"""
Unit Tests for SubscriptIQ AI Revenue Intelligence Module.

Covers:
1. Revenue Leakage Detector (6 leakage vectors, severity classifications, loss quantifications).
2. Intelligent Invoice Auditor (recalculation, discrepancies, negative checks, ORM model updates).
3. Statistical Revenue Forecaster (NumPy/Pandas trend fits, frontend contracts, sparse data handling).
4. Customer Churn Predictor (payment failures, overdue aging, auto-renew signals, cohort summaries).
5. Business Health Score (composite 0-100 index, grade mapping, snapshot conversions).
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import pytest

from backend.models.intelligence import RevenueLeakageAlert, BusinessHealthSnapshot
from backend.services.intelligence import (
    # Leakage
    detect_revenue_leakage,
    detect_unbilled_subscriptions,
    detect_duplicate_invoices,
    detect_expired_discounts,
    detect_overdue_invoices,
    detect_missing_renewals,
    detect_payment_reconciliation_gaps,
    # Auditor
    audit_invoice,
    audit_invoices_batch,
    # Forecaster
    forecast_revenue,
    generate_forecast_from_invoices,
    # Churn
    assess_customer_churn_risk,
    assess_cohort_churn_risk,
    summarize_churn_risks,
    # Health Score
    calculate_business_health_score,
)


# ==============================================================================
# 1. REVENUE LEAKAGE DETECTOR TESTS
# ==============================================================================

class TestRevenueLeakageDetector:
    def test_unbilled_active_subscriptions(self):
        sub = {
            "id": 101,
            "subscription_number": "SUB-101",
            "customer_id": 1,
            "status": "active",
            "unit_price": Decimal("99.00"),
            "quantity": 2,
            "current_period_start": date(2026, 11, 1),
            "current_period_end": date(2026, 11, 30),
            "next_billing_date": date(2026, 11, 1),
        }
        # Invoices empty -> unbilled
        alerts = detect_unbilled_subscriptions([sub], invoices=[], as_of_date=date(2026, 11, 5))
        assert len(alerts) == 1
        a = alerts[0]
        assert a.leakage_type == "unbilled_active_subscription"
        assert a.estimated_loss == Decimal("198.00")
        assert a.subscription_id == 101
        assert "SUB-101" in a.description

    def test_duplicate_invoices_detected(self):
        inv1 = {
            "id": 1,
            "invoice_number": "INV-001",
            "subscription_id": 50,
            "customer_id": 5,
            "billing_period_start": date(2026, 11, 1),
            "billing_period_end": date(2026, 11, 30),
            "total_amount": Decimal("100.00"),
            "status": "issued",
        }
        inv2 = {
            "id": 2,
            "invoice_number": "INV-002",
            "subscription_id": 50,
            "customer_id": 5,
            "billing_period_start": date(2026, 11, 1),
            "billing_period_end": date(2026, 11, 30),
            "total_amount": Decimal("100.00"),
            "status": "issued",
        }
        alerts = detect_duplicate_invoices([inv1, inv2])
        assert len(alerts) == 1
        a = alerts[0]
        assert a.leakage_type == "duplicate_billing_attempt"
        assert a.severity == "critical"
        assert a.estimated_loss == Decimal("100.00")
        assert "INV-002" in a.description

    def test_expired_discounts_detected(self):
        inv = {
            "id": 10,
            "invoice_number": "INV-DISC-01",
            "customer_id": 7,
            "subscription_id": 3,
            "issue_date": date(2026, 11, 15),
            "discount_id": 99,
            "discount_amount": Decimal("25.00"),
        }
        discount = {
            "id": 99,
            "code": "BLACKFRIDAY",
            "end_date": date(2026, 10, 31),  # Expired before invoice issue date
            "is_active": True,
        }
        alerts = detect_expired_discounts([inv], discounts=[discount])
        assert len(alerts) == 1
        a = alerts[0]
        assert a.leakage_type == "expired_discount_applied"
        assert a.estimated_loss == Decimal("25.00")
        assert "BLACKFRIDAY" in a.description

    def test_overdue_uncollected_invoices(self):
        inv = {
            "id": 20,
            "invoice_number": "INV-OVERDUE-01",
            "customer_id": 12,
            "subscription_id": 4,
            "due_date": date(2026, 10, 1),
            "amount_due": Decimal("500.00"),
            "status": "overdue",
        }
        # As of Nov 10, 2026 -> 40 days overdue -> critical
        alerts = detect_overdue_invoices([inv], as_of_date=date(2026, 11, 10))
        assert len(alerts) == 1
        a = alerts[0]
        assert a.leakage_type == "overdue_uncollected"
        assert a.severity == "critical"
        assert a.estimated_loss == Decimal("500.00")

    def test_missing_renewal_invoices(self):
        sub = {
            "id": 77,
            "subscription_number": "SUB-RENEW-01",
            "customer_id": 2,
            "status": "active",
            "auto_renew": True,
            "current_period_end": date(2026, 10, 31),
            "unit_price": Decimal("150.00"),
            "quantity": 1,
        }
        alerts = detect_missing_renewals([sub], as_of_date=date(2026, 11, 5))
        assert len(alerts) == 1
        a = alerts[0]
        assert a.leakage_type == "missing_renewal_invoice"
        assert a.estimated_loss == Decimal("150.00")

    def test_payment_reconciliation_gap(self):
        inv = {
            "id": 30,
            "invoice_number": "INV-RECON-01",
            "total_amount": Decimal("100.00"),
            "amount_paid": Decimal("100.00"),
            "amount_due": Decimal("0.00"),
        }
        # Only one payment of 60.00 exists in gateway
        payment = {
            "id": 1,
            "invoice_id": 30,
            "amount": Decimal("60.00"),
            "status": "successful",
        }
        alerts = detect_payment_reconciliation_gaps([inv], payments=[payment])
        assert len(alerts) == 1
        a = alerts[0]
        assert a.leakage_type == "billing_discrepancy"
        assert a.estimated_loss == Decimal("40.00")

    def test_full_detector_orchestration_and_model_conversion(self):
        alerts = detect_revenue_leakage(
            subscriptions=[],
            invoices=[],
            payments=[],
            discounts=[],
        )
        assert alerts == []

        # Test model conversion
        alert_res = detect_unbilled_subscriptions(
            subscriptions=[{
                "id": 1,
                "subscription_number": "SUB-1",
                "customer_id": 1,
                "status": "active",
                "unit_price": Decimal("10.00"),
                "quantity": 1,
                "next_billing_date": date(2026, 1, 1),
            }],
            invoices=[],
            as_of_date=date(2026, 1, 10),
        )[0]
        model = alert_res.to_alert_model()
        assert isinstance(model, RevenueLeakageAlert)
        assert model.leakage_type == "unbilled_active_subscription"
        assert model.estimated_loss == Decimal("10.00")


# ==============================================================================
# 2. INVOICE AUDITOR TESTS
# ==============================================================================

class TestInvoiceAuditor:
    def test_valid_invoice_audit_passes(self):
        invoice = {
            "id": 1,
            "invoice_number": "INV-PERFECT-01",
            "subtotal": Decimal("200.00"),
            "discount_amount": Decimal("20.00"),
            "tax_amount": Decimal("18.00"),
            "total_amount": Decimal("198.00"),
            "amount_paid": Decimal("198.00"),
            "amount_due": Decimal("0.00"),
            "items": [
                {"description": "Pro Tier", "quantity": Decimal("2.00"), "unit_price": Decimal("100.00")},
            ],
        }
        res = audit_invoice(invoice)
        assert res.is_valid is True
        assert res.discrepancy_amount == Decimal("0.00")
        assert len(res.discrepancies) == 0

    def test_negative_amounts_rejected(self):
        invoice = {
            "id": 2,
            "invoice_number": "INV-NEG-01",
            "subtotal": Decimal("-50.00"),
            "total_amount": Decimal("-50.00"),
            "amount_due": Decimal("-50.00"),
            "amount_paid": Decimal("0.00"),
            "items": [
                {"description": "Faulty", "quantity": Decimal("-1.00"), "unit_price": Decimal("50.00")},
            ],
        }
        res = audit_invoice(invoice)
        assert res.is_valid is False
        assert any("negative" in d.lower() for d in res.discrepancies)

    def test_subtotal_mismatch_detected(self):
        invoice = {
            "id": 3,
            "invoice_number": "INV-MISMATCH-01",
            "subtotal": Decimal("150.00"),  # Actual recorded subtotal is 150
            "total_amount": Decimal("150.00"),
            "amount_paid": Decimal("0.00"),
            "amount_due": Decimal("150.00"),
            "items": [
                {"description": "Item A", "quantity": Decimal("1.00"), "unit_price": Decimal("100.00")},  # Sum is 100
            ],
        }
        res = audit_invoice(invoice)
        assert res.is_valid is False
        assert res.discrepancy_amount > Decimal("0.00")
        assert any("subtotal" in d.lower() for d in res.discrepancies)

    def test_arithmetic_balance_gap_detected(self):
        invoice = {
            "id": 4,
            "invoice_number": "INV-ARITH-01",
            "subtotal": Decimal("100.00"),
            "discount_amount": Decimal("10.00"),
            "tax_amount": Decimal("10.00"),
            "total_amount": Decimal("150.00"),  # Should be 100 - 10 + 10 = 100
            "amount_paid": Decimal("0.00"),
            "amount_due": Decimal("150.00"),
            "items": [],
        }
        res = audit_invoice(invoice)
        assert res.is_valid is False
        assert any("arithmetic" in d.lower() for d in res.discrepancies)

    def test_batch_auditing(self):
        invoices = [
            {"id": 1, "invoice_number": "A", "subtotal": Decimal("50"), "total_amount": Decimal("50"), "amount_due": Decimal("50"), "amount_paid": Decimal("0"), "items": []},
            {"id": 2, "invoice_number": "B", "subtotal": Decimal("-10"), "total_amount": Decimal("-10"), "amount_due": Decimal("0"), "amount_paid": Decimal("0"), "items": []},
        ]
        results = audit_invoices_batch(invoices)
        assert len(results) == 2
        assert results[0].is_valid is True
        assert results[1].is_valid is False


# ==============================================================================
# 3. REVENUE FORECASTING ENGINE TESTS
# ==============================================================================

class TestRevenueForecasting:
    def test_forecast_with_standard_historical_trend(self):
        history = [
            {"month": "2026-01", "revenue": 10000.0},
            {"month": "2026-02", "revenue": 12000.0},
            {"month": "2026-03", "revenue": 14000.0},
            {"month": "2026-04", "revenue": 16000.0},
        ]
        res = forecast_revenue(history, months_ahead=6)
        assert res.historical_months_count == 4
        assert res.forecast_months_count == 6
        assert res.current_mrr == 16000.0
        assert res.predicted_mrr > 16000.0
        assert res.growth_rate_pct > 0.0
        assert res.confidence_score > 0.70
        assert res.trend_direction == "positive"
        # Total data points = 4 historical + 6 forecast = 10
        assert len(res.forecast_data) == 10

    def test_forecast_single_point_baseline(self):
        history = [{"month": "2026-10", "revenue": 5000.0}]
        res = forecast_revenue(history, months_ahead=6)
        assert res.historical_months_count == 1
        assert res.current_mrr == 5000.0
        assert res.predicted_mrr == 5000.0
        assert res.confidence_score == 0.35
        assert res.methodology == "single_point_baseline"

    def test_forecast_two_points(self):
        history = [
            {"month": "2026-09", "revenue": 1000.0},
            {"month": "2026-10", "revenue": 1200.0},
        ]
        res = forecast_revenue(history, months_ahead=3)
        assert res.historical_months_count == 2
        assert res.current_mrr == 1200.0
        assert res.predicted_mrr > 1200.0

    def test_forecast_empty_data_handled_gracefully(self):
        res = forecast_revenue([], months_ahead=6)
        assert res.historical_months_count == 0
        assert res.current_mrr == 0.0
        assert res.predicted_mrr == 0.0
        assert res.confidence_score == 0.0
        assert len(res.forecast_data) == 6

    def test_forecast_from_invoices(self):
        invs = [
            {"issue_date": "2026-08-15", "total_amount": Decimal("2000.00"), "status": "paid"},
            {"issue_date": "2026-09-15", "total_amount": Decimal("2500.00"), "status": "paid"},
            {"issue_date": "2026-10-15", "total_amount": Decimal("3000.00"), "status": "paid"},
        ]
        res = generate_forecast_from_invoices(invs, months_ahead=6)
        assert res.historical_months_count == 3
        assert res.current_mrr == 3000.0
        assert res.predicted_mrr > 3000.0


# ==============================================================================
# 4. CUSTOMER CHURN PREDICTOR TESTS
# ==============================================================================

class TestCustomerChurnPredictor:
    def test_low_risk_healthy_customer(self):
        customer = {"id": 1, "name": "Stripe Inc", "created_at": date(2025, 1, 1)}
        subs = [{
            "customer_id": 1,
            "status": "active",
            "auto_renew": True,
            "start_date": date(2025, 1, 1),
        }]
        pays = [{"customer_id": 1, "status": "successful"}]
        invs = [{"customer_id": 1, "status": "paid", "amount_due": Decimal("0.00")}]

        res = assess_customer_churn_risk(
            customer=customer,
            subscriptions=subs,
            invoices=invs,
            payments=pays,
            as_of_date=date(2026, 11, 1),
        )
        assert res.risk_category == "low"
        assert res.risk_score < 25.0

    def test_critical_risk_due_to_failed_payments_and_overdue_invoices(self):
        customer = {"id": 2, "name": "At-Risk LLC"}
        subs = [{
            "customer_id": 2,
            "status": "past_due",
            "auto_renew": False,  # 20 pts
            "start_date": date(2026, 10, 15),  # Early onboarding <30 days -> 15 pts
        }]
        pays = [
            {"customer_id": 2, "status": "failed", "payment_date": date(2026, 10, 20)},
            {"customer_id": 2, "status": "failed", "payment_date": date(2026, 10, 25)},
            {"customer_id": 2, "status": "failed", "payment_date": date(2026, 10, 30)},  # 3 failures -> 35 pts
        ]
        invs = [{
            "customer_id": 2,
            "status": "overdue",
            "due_date": date(2026, 9, 15),  # >30 days overdue -> 30 pts
            "amount_due": Decimal("450.00"),
        }]

        res = assess_customer_churn_risk(
            customer=customer,
            subscriptions=subs,
            invoices=invs,
            payments=pays,
            as_of_date=date(2026, 11, 1),
        )
        # Expected score: 35 + 30 + 20 + 15 = 100 (critical)
        assert res.risk_category == "critical"
        assert res.risk_score >= 90.0
        assert len(res.risk_factors) >= 4

    def test_cohort_churn_risk_ranking(self):
        c1 = {"id": 1, "name": "Healthy"}
        c2 = {"id": 2, "name": "Unhealthy"}
        subs = [
            {"customer_id": 1, "status": "active", "auto_renew": True, "start_date": date(2025, 1, 1)},
            {"customer_id": 2, "status": "past_due", "auto_renew": False, "start_date": date(2026, 10, 20)},
        ]
        cohort = assess_cohort_churn_risk([c1, c2], subscriptions=subs, as_of_date=date(2026, 11, 1))
        assert len(cohort) == 2
        # Highest risk first
        assert cohort[0].customer_id == 2
        assert cohort[1].customer_id == 1

        summary = summarize_churn_risks(cohort)
        assert summary["total_customers"] == 2
        assert summary["average_risk_score"] > 0


# ==============================================================================
# 5. BUSINESS HEALTH SCORE TESTS
# ==============================================================================

class TestBusinessHealthScore:
    def test_optimal_healthy_business(self):
        subs = [
            {"id": 1, "status": "active", "billing_interval": "monthly", "unit_price": Decimal("500.00"), "quantity": 10},
        ]
        pays = [
            {"amount": Decimal("5000.00"), "status": "successful"} for _ in range(10)
        ]
        invs = [
            {"status": "paid", "amount_due": Decimal("0.00"), "due_date": date(2026, 10, 1)}
        ]

        res = calculate_business_health_score(
            subscriptions=subs,
            invoices=invs,
            payments=pays,
            previous_mrr=Decimal("4500.00"),  # Positive growth from 4500 -> 5000
            as_of_date=date(2026, 11, 1),
        )
        assert res.health_score >= 90.0
        assert res.grade in ("A", "A+")
        assert res.mrr == Decimal("5000.00")
        assert res.arr == Decimal("60000.00")
        assert len(res.key_metrics) == 4
        assert len(res.insights) == 3

    def test_delinquent_business_lower_score(self):
        subs = [
            {"id": 1, "status": "cancelled", "billing_interval": "monthly", "unit_price": Decimal("100.00"), "quantity": 1},
        ]
        pays = [
            {"amount": Decimal("100.00"), "status": "failed"},
        ]
        invs = [
            {"status": "overdue", "amount_due": Decimal("500.00"), "due_date": date(2026, 9, 1)}
        ]

        res = calculate_business_health_score(
            subscriptions=subs,
            invoices=invs,
            payments=pays,
            as_of_date=date(2026, 11, 1),
        )
        assert res.health_score < 70.0
        assert res.grade in ("C", "D", "F")
        assert any(r["priority"] == "High" for r in res.recommendations)

    def test_snapshot_model_conversion(self):
        res = calculate_business_health_score(
            subscriptions=[{"status": "active", "billing_interval": "monthly", "unit_price": Decimal("200.00"), "quantity": 1}],
            as_of_date=date(2026, 11, 1),
        )
        snapshot = res.to_snapshot_model(snapshot_date=date(2026, 11, 1))
        assert isinstance(snapshot, BusinessHealthSnapshot)
        assert snapshot.mrr == Decimal("200.00")
        assert snapshot.health_score > Decimal("0.00")
