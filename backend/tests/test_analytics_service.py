"""
Unit Tests for Financial Analytics Engine (backend/services/finance/analytics_service.py).
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import pytest

from backend.services.finance.analytics_service import (
    AgingBuckets,
    ComprehensiveFinancialAnalytics,
    InvoiceRecord,
    MonthlyTrendPoint,
    MRRBreakdown,
    PaymentAnalyticsResult,
    PaymentRecord,
    RevenueGrowthResult,
    SubscriptionAnalyticsResult,
    SubscriptionRecord,
    calculate_arr,
    calculate_comprehensive_analytics,
    calculate_monthly_revenue_trends,
    calculate_mrr,
    calculate_outstanding_revenue,
    calculate_payment_analytics,
    calculate_revenue_growth,
    calculate_subscription_analytics,
)


# ==============================================================================
# MRR & ARR TESTS
# ==============================================================================

class TestMRRCalculation:
    def test_monthly_billing_standard(self):
        subs = [
            SubscriptionRecord(id=1, customer_id=10, unit_price="100.00", quantity=1, billing_interval="monthly"),
            SubscriptionRecord(id=2, customer_id=11, unit_price="50.00", quantity=2, billing_interval="monthly"),
        ]
        res = calculate_mrr(subs)
        assert res.total_mrr == Decimal("200.00")
        assert res.active_subscriptions_count == 2
        assert res.monthly_contributed_mrr == Decimal("200.00")

    def test_weekly_billing_normalization(self):
        # $25.00/week -> (25 * 52) / 12 = 1300 / 12 = 108.33
        subs = [
            SubscriptionRecord(id=1, customer_id=10, unit_price="25.00", quantity=1, billing_interval="weekly"),
        ]
        res = calculate_mrr(subs)
        assert res.total_mrr == Decimal("108.33")
        assert res.weekly_contributed_mrr == Decimal("108.33")

    def test_yearly_billing_normalization(self):
        # $1200.00/year -> 1200 / 12 = 100.00
        subs = [
            SubscriptionRecord(id=1, customer_id=10, unit_price="1200.00", quantity=1, billing_interval="yearly"),
        ]
        res = calculate_mrr(subs)
        assert res.total_mrr == Decimal("100.00")
        assert res.yearly_contributed_mrr == Decimal("100.00")

    def test_mixed_frequency_and_discounts(self):
        # Sub 1: Monthly $100 with $20 discount = $80.00
        # Sub 2: Weekly $10 (no discount) -> (10 * 52) / 12 = $43.33
        # Sub 3: Yearly $2400 (no discount) -> 2400 / 12 = $200.00
        subs = [
            SubscriptionRecord(id=1, customer_id=1, unit_price="100.00", discount_amount="20.00", billing_interval="monthly"),
            SubscriptionRecord(id=2, customer_id=2, unit_price="10.00", billing_interval="weekly"),
            SubscriptionRecord(id=3, customer_id=3, unit_price="2400.00", billing_interval="yearly"),
        ]
        res = calculate_mrr(subs)
        # Expected: 80.00 + 43.33 + 200.00 = 323.33
        assert res.total_mrr == Decimal("323.33")
        assert res.active_subscriptions_count == 3
        assert res.total_discounts_deducted == Decimal("20.00")

    def test_status_filtering_excludes_inactive(self):
        subs = [
            SubscriptionRecord(id=1, customer_id=1, unit_price="100.00", status="active"),
            SubscriptionRecord(id=2, customer_id=2, unit_price="100.00", status="cancelled"),
            SubscriptionRecord(id=3, customer_id=3, unit_price="100.00", status="paused"),
            SubscriptionRecord(id=4, customer_id=4, unit_price="100.00", status="draft"),
            SubscriptionRecord(id=5, customer_id=5, unit_price="100.00", status="closed"),
        ]
        res = calculate_mrr(subs)
        assert res.total_mrr == Decimal("100.00")
        assert res.active_subscriptions_count == 1

    def test_discount_exceeding_unit_price_is_capped_at_zero(self):
        subs = [
            SubscriptionRecord(id=1, customer_id=1, unit_price="50.00", discount_amount="80.00"),
        ]
        res = calculate_mrr(subs)
        assert res.total_mrr == Decimal("0.00")

    def test_empty_subscriptions_returns_zero(self):
        res = calculate_mrr([])
        assert res.total_mrr == Decimal("0.00")
        assert res.active_subscriptions_count == 0

    def test_raw_dict_input_compatibility(self):
        subs_dict = [
            {"id": "s1", "customer_id": "c1", "unit_price": 75.00, "quantity": 1, "billing_interval": "monthly", "status": "active"},
        ]
        res = calculate_mrr(subs_dict)
        assert res.total_mrr == Decimal("75.00")
        assert res.active_subscriptions_count == 1


class TestARRCalculation:
    def test_arr_from_mrr_breakdown(self):
        mrr = MRRBreakdown(
            total_mrr=Decimal("1000.00"),
            active_subscriptions_count=10,
            weekly_contributed_mrr=Decimal("0.00"),
            monthly_contributed_mrr=Decimal("1000.00"),
            yearly_contributed_mrr=Decimal("0.00"),
            total_discounts_deducted=Decimal("0.00"),
        )
        assert calculate_arr(mrr) == Decimal("12000.00")

    def test_arr_from_direct_subscription_list(self):
        subs = [
            SubscriptionRecord(id=1, customer_id=1, unit_price="250.00", billing_interval="monthly"),
        ]
        # MRR = 250 -> ARR = 3000
        assert calculate_arr(subs) == Decimal("3000.00")


# ==============================================================================
# REVENUE GROWTH TESTS
# ==============================================================================

class TestRevenueGrowth:
    def test_positive_growth(self):
        res = calculate_revenue_growth(current_period_revenue="1500.00", previous_period_revenue="1000.00")
        assert res.net_change == Decimal("500.00")
        assert res.growth_rate_percentage == Decimal("50.00")
        assert res.is_growth_positive is True

    def test_negative_growth(self):
        res = calculate_revenue_growth(current_period_revenue="750.00", previous_period_revenue="1000.00")
        assert res.net_change == Decimal("-250.00")
        assert res.growth_rate_percentage == Decimal("-25.00")
        assert res.is_growth_positive is False

    def test_zero_change(self):
        res = calculate_revenue_growth(current_period_revenue="1000.00", previous_period_revenue="1000.00")
        assert res.net_change == Decimal("0.00")
        assert res.growth_rate_percentage == Decimal("0.00")
        assert res.is_growth_positive is True

    def test_zero_previous_revenue_with_positive_current(self):
        res = calculate_revenue_growth(current_period_revenue="500.00", previous_period_revenue="0.00")
        assert res.net_change == Decimal("500.00")
        assert res.growth_rate_percentage == Decimal("100.00")
        assert res.is_growth_positive is True

    def test_both_zero_revenue(self):
        res = calculate_revenue_growth(current_period_revenue="0.00", previous_period_revenue="0.00")
        assert res.net_change == Decimal("0.00")
        assert res.growth_rate_percentage == Decimal("0.00")


# ==============================================================================
# PAYMENT ANALYTICS TESTS
# ==============================================================================

class TestPaymentAnalytics:
    def test_payment_analytics_breakdown(self):
        payments = [
            PaymentRecord(id=1, amount="100.00", status="successful"),
            PaymentRecord(id=2, amount="200.00", status="successful"),
            PaymentRecord(id=3, amount="50.00", status="pending"),
            PaymentRecord(id=4, amount="150.00", status="failed"),
            PaymentRecord(id=5, amount="25.00", status="refunded"),
        ]
        res = calculate_payment_analytics(payments)

        assert res.total_volume == Decimal("525.00")
        assert res.successful_volume == Decimal("300.00")
        assert res.pending_volume == Decimal("50.00")
        assert res.failed_volume == Decimal("150.00")
        assert res.refunded_volume == Decimal("25.00")

        assert res.total_count == 5
        assert res.successful_count == 2
        assert res.pending_count == 1
        assert res.failed_count == 1
        assert res.refunded_count == 1

        # 2 / 5 = 40.00%
        assert res.success_rate_percentage == Decimal("40.00")
        # 1 / 5 = 20.00%
        assert res.failure_rate_percentage == Decimal("20.00")

    def test_empty_payments_returns_zero(self):
        res = calculate_payment_analytics([])
        assert res.total_volume == Decimal("0.00")
        assert res.total_count == 0
        assert res.success_rate_percentage == Decimal("0.00")


# ==============================================================================
# OUTSTANDING REVENUE & AGING TESTS
# ==============================================================================

class TestOutstandingRevenue:
    def test_aging_and_due_classification(self):
        eval_date = date(2026, 11, 15)

        invoices = [
            # 1. Current / Not overdue (due in 5 days): $100
            InvoiceRecord(id=1, customer_id=1, total_amount="100.00", amount_due="100.00", status="issued", due_date=date(2026, 11, 20)),
            # 2. Overdue 10 days (due Nov 5): $200 (in 1-30 bucket)
            InvoiceRecord(id=2, customer_id=2, total_amount="200.00", amount_due="200.00", status="issued", due_date=date(2026, 11, 5)),
            # 3. Overdue 40 days (due Oct 6): $300 (in 31-60 bucket)
            InvoiceRecord(id=3, customer_id=3, total_amount="300.00", amount_due="300.00", status="overdue", due_date=date(2026, 10, 6)),
            # 4. Overdue 75 days (due Sept 1): $400 (in 61-90 bucket)
            InvoiceRecord(id=4, customer_id=4, total_amount="400.00", amount_due="400.00", status="overdue", due_date=date(2026, 9, 1)),
            # 5. Overdue 100 days (due Aug 7): $500 (in 90+ bucket)
            InvoiceRecord(id=5, customer_id=5, total_amount="500.00", amount_due="500.00", status="overdue", due_date=date(2026, 8, 7)),
            # 6. Fully Paid invoice: should be completely ignored
            InvoiceRecord(id=6, customer_id=6, total_amount="150.00", amount_paid="150.00", amount_due="0.00", status="paid", due_date=date(2026, 10, 1)),
            # 7. Cancelled invoice: should be ignored
            InvoiceRecord(id=7, customer_id=7, total_amount="500.00", amount_due="500.00", status="cancelled", due_date=date(2026, 10, 1)),
        ]

        res = calculate_outstanding_revenue(invoices, evaluation_date=eval_date)

        # Expected: 100 (current) + 200 + 300 + 400 + 500 (overdue) = 1500.00
        assert res.total_outstanding == Decimal("1500.00")
        assert res.current_due_amount == Decimal("100.00")
        assert res.overdue_amount == Decimal("1400.00")

        assert res.current_invoices_count == 1
        assert res.overdue_invoices_count == 4
        assert res.total_unpaid_invoices_count == 5

        # Check aging cohorts
        assert res.aging_buckets.current_not_due == Decimal("100.00")
        assert res.aging_buckets.days_1_to_30 == Decimal("200.00")
        assert res.aging_buckets.days_31_to_60 == Decimal("300.00")
        assert res.aging_buckets.days_61_to_90 == Decimal("400.00")
        assert res.aging_buckets.days_90_plus == Decimal("500.00")

    def test_empty_invoices_returns_zero(self):
        res = calculate_outstanding_revenue([])
        assert res.total_outstanding == Decimal("0.00")
        assert res.total_unpaid_invoices_count == 0


# ==============================================================================
# SUBSCRIPTION ANALYTICS & CHURN TESTS
# ==============================================================================

class TestSubscriptionAnalytics:
    def test_counts_and_churn_rate(self):
        subs = [
            SubscriptionRecord(id=1, customer_id=1, unit_price="100.00", status="active"),
            SubscriptionRecord(id=2, customer_id=2, unit_price="100.00", status="active"),
            SubscriptionRecord(id=3, customer_id=3, unit_price="100.00", status="active"),
            SubscriptionRecord(id=4, customer_id=4, unit_price="100.00", status="active"),
            SubscriptionRecord(id=5, customer_id=5, unit_price="100.00", status="cancelled"),
            SubscriptionRecord(id=6, customer_id=6, unit_price="100.00", status="paused"),
            SubscriptionRecord(id=7, customer_id=7, unit_price="100.00", status="draft"),
        ]
        res = calculate_subscription_analytics(subs)

        assert res.active_count == 4
        assert res.cancelled_count == 1
        assert res.paused_count == 1
        assert res.draft_count == 1
        assert res.total_count == 7

        # Churn rate: 1 cancelled / (4 active + 1 cancelled) = 1 / 5 = 20.00%
        assert res.churn_rate_percentage == Decimal("20.00")

        # ARPU: MRR ($400) / 4 active = $100.00
        assert res.arpu == Decimal("100.00")

    def test_zero_subscriptions_returns_zero_metrics(self):
        res = calculate_subscription_analytics([])
        assert res.active_count == 0
        assert res.churn_rate_percentage == Decimal("0.00")
        assert res.arpu == Decimal("0.00")


# ==============================================================================
# MONTHLY REVENUE TRENDS TESTS
# ==============================================================================

class TestMonthlyRevenueTrends:
    def test_chronological_grouping_and_mom_growth(self):
        payments = [
            PaymentRecord(id=1, amount="1000.00", status="successful", payment_date=date(2026, 1, 15)),
            PaymentRecord(id=2, amount="500.00", status="successful", payment_date=date(2026, 1, 20)),
            # Jan total = 1500.00

            PaymentRecord(id=3, amount="2000.00", status="successful", payment_date=date(2026, 2, 10)),
            # Feb total = 2000.00 -> MoM: (2000 - 1500) / 1500 = +33.33%

            PaymentRecord(id=4, amount="1800.00", status="successful", payment_date=date(2026, 3, 5)),
            # Mar total = 1800.00 -> MoM: (1800 - 2000) / 2000 = -10.00%

            # Failed payment in Feb should be ignored
            PaymentRecord(id=5, amount="500.00", status="failed", payment_date=date(2026, 2, 12)),
        ]

        trends = calculate_monthly_revenue_trends(payments)

        assert len(trends) == 3

        # Month 1: Jan
        assert trends[0].month == "2026-01"
        assert trends[0].revenue == Decimal("1500.00")
        assert trends[0].transaction_count == 2
        assert trends[0].growth_rate_mom is None

        # Month 2: Feb
        assert trends[1].month == "2026-02"
        assert trends[1].revenue == Decimal("2000.00")
        assert trends[1].transaction_count == 1
        assert trends[1].growth_rate_mom == Decimal("33.33")

        # Month 3: Mar
        assert trends[2].month == "2026-03"
        assert trends[2].revenue == Decimal("1800.00")
        assert trends[2].transaction_count == 1
        assert trends[2].growth_rate_mom == Decimal("-10.00")

    def test_empty_records_returns_empty_trends(self):
        assert calculate_monthly_revenue_trends([]) == []


# ==============================================================================
# COMPREHENSIVE ANALYTICS AGGREGATOR TEST
# ==============================================================================

class TestComprehensiveAnalytics:
    def test_unified_aggregation(self):
        subs = [SubscriptionRecord(id=1, customer_id=1, unit_price="100.00", billing_interval="monthly")]
        invs = [InvoiceRecord(id=1, customer_id=1, total_amount="100.00", amount_due="100.00", status="issued", due_date=date(2026, 12, 1))]
        pays = [PaymentRecord(id=1, amount="100.00", status="successful", payment_date=date(2026, 11, 1))]

        res = calculate_comprehensive_analytics(subscriptions=subs, invoices=invs, payments=pays)

        assert isinstance(res, ComprehensiveFinancialAnalytics)
        assert res.mrr_summary.total_mrr == Decimal("100.00")
        assert res.arr == Decimal("1200.00")
        assert res.payment_analytics.successful_volume == Decimal("100.00")
        assert res.outstanding_revenue.total_outstanding == Decimal("100.00")
        assert res.subscription_analytics.active_count == 1
        assert len(res.monthly_trends) == 1
