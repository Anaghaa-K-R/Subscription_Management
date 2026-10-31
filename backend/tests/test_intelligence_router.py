"""
Unit and Integration Tests for AI Revenue Intelligence FastAPI Endpoints.

Tests:
1. GET  /api/ai/forecast       - Predictive time-series forecasting & empty state handling
2. GET  /api/ai/leakage-alerts - 6-vector anomaly detection & database duplicate prevention
3. GET  /api/ai/health-score   - Composite business score, letter grade & snapshot persistence
4. GET  /api/ai/churn-risk     - Cohort churn risk scoring, filtering & customer 404 handling
5. POST /api/ai/audit-invoice  - Single & batch mathematical invoice integrity verification
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend.models import (
    Customer,
    Product,
    Subscription,
    Invoice,
    InvoiceItem,
    Payment,
    Discount,
    TaxRule,
    RevenueLeakageAlert,
    BusinessHealthSnapshot,
)


@pytest.fixture(name="db_session")
def fixture_db_session():
    """Provides an isolated, in-memory SQLite database per test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(name="client")
def fixture_client(db_session):
    """Provides a FastAPI test client wired to the isolated in-memory DB."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def make_sub(
    customer_id: int,
    plan_id: int,
    subscription_number: str = "SUB-01",
    status: str = "active",
    unit_price: Decimal = Decimal("100.00"),
    quantity: int = 1,
    start_date: Optional[date] = None,
    current_period_start: Optional[date] = None,
    current_period_end: Optional[date] = None,
    next_billing_date: Optional[date] = None,
    auto_renew: bool = True,
    billing_interval: str = "monthly",
) -> Subscription:
    """Helper to create Subscription with all non-nullable date columns populated."""
    s_date = start_date or (date.today() - timedelta(days=60))
    p_start = current_period_start or date.today()
    p_end = current_period_end or (date.today() + timedelta(days=30))
    n_date = next_billing_date or (date.today() + timedelta(days=30))
    return Subscription(
        subscription_number=subscription_number,
        customer_id=customer_id,
        plan_id=plan_id,
        status=status,
        unit_price=unit_price,
        quantity=quantity,
        billing_interval=billing_interval,
        start_date=s_date,
        current_period_start=p_start,
        current_period_end=p_end,
        next_billing_date=n_date,
        auto_renew=auto_renew,
    )


# ==============================================================================
# 1. REVENUE FORECASTING ENDPOINT
# ==============================================================================

class TestForecastEndpoint:
    def test_forecast_empty_database_returns_safe_defaults(self, client):
        response = client.get("/api/ai/forecast?months_ahead=6")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["current_mrr"] == 0.0
        assert data["predicted_mrr"] == 0.0
        assert data["confidence_score"] == 0.0
        assert len(data["forecast_data"]) == 6
        assert all(p["actual"] is None for p in data["forecast_data"])

    def test_forecast_with_historical_invoices(self, client, db_session):
        cust = Customer(name="Acme Corp", email="billing@acme.com")
        prod = Product(name="Cloud Plan", price=Decimal("1000.00"), billing_interval="monthly")
        db_session.add_all([cust, prod])
        db_session.commit()

        sub = make_sub(cust.id, prod.id, "SUB-FC-01", unit_price=Decimal("1000.00"))
        db_session.add(sub)
        db_session.commit()

        # Seed 3 sequential months of paid invoices
        inv1 = Invoice(
            invoice_number="INV-2026-08",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date(2026, 8, 1),
            billing_period_end=date(2026, 8, 31),
            issue_date=date(2026, 8, 1),
            due_date=date(2026, 8, 15),
            subtotal=Decimal("5000.00"),
            total_amount=Decimal("5000.00"),
            amount_paid=Decimal("5000.00"),
            amount_due=Decimal("0.00"),
            status="paid",
        )
        inv2 = Invoice(
            invoice_number="INV-2026-09",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date(2026, 9, 1),
            billing_period_end=date(2026, 9, 30),
            issue_date=date(2026, 9, 1),
            due_date=date(2026, 9, 15),
            subtotal=Decimal("6000.00"),
            total_amount=Decimal("6000.00"),
            amount_paid=Decimal("6000.00"),
            amount_due=Decimal("0.00"),
            status="paid",
        )
        inv3 = Invoice(
            invoice_number="INV-2026-10",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date(2026, 10, 1),
            billing_period_end=date(2026, 10, 31),
            issue_date=date(2026, 10, 1),
            due_date=date(2026, 10, 15),
            subtotal=Decimal("7000.00"),
            total_amount=Decimal("7000.00"),
            amount_paid=Decimal("7000.00"),
            amount_due=Decimal("0.00"),
            status="paid",
        )
        db_session.add_all([inv1, inv2, inv3])
        db_session.commit()

        response = client.get("/api/ai/forecast?months_ahead=6")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["historical_months_count"] == 3
        assert data["current_mrr"] == 7000.0
        assert data["predicted_mrr"] > 7000.0
        assert data["growth_rate_pct"] > 0
        assert data["trend_direction"] == "positive"
        assert len(data["forecast_data"]) == 9


# ==============================================================================
# 2. REVENUE LEAKAGE ALERTS ENDPOINT
# ==============================================================================

class TestLeakageAlertsEndpoint:
    def test_leakage_empty_database_returns_no_alerts(self, client):
        response = client.get("/api/ai/leakage-alerts")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["total_alerts"] == 0
        assert data["total_estimated_loss"] == 0.0
        assert data["alerts"] == []

    def test_leakage_detection_and_duplicate_prevention(self, client, db_session):
        cust = Customer(name="Overdue Client", email="overdue@client.com")
        prod = Product(name="Enterprise", price=Decimal("250.00"), billing_interval="monthly")
        db_session.add_all([cust, prod])
        db_session.commit()

        sub = make_sub(cust.id, prod.id, "SUB-LK-01", unit_price=Decimal("250.00"))
        db_session.add(sub)
        db_session.commit()

        # Seed an overdue unpaid invoice
        overdue_inv = Invoice(
            invoice_number="INV-OVERDUE-99",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date.today() - timedelta(days=60),
            billing_period_end=date.today() - timedelta(days=31),
            issue_date=date.today() - timedelta(days=60),
            due_date=date.today() - timedelta(days=45),  # 45 days overdue
            subtotal=Decimal("250.00"),
            total_amount=Decimal("250.00"),
            amount_paid=Decimal("0.00"),
            amount_due=Decimal("250.00"),
            status="overdue",
        )
        db_session.add(overdue_inv)
        db_session.commit()

        # First Call: Alert detected and persisted
        resp1 = client.get("/api/ai/leakage-alerts")
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["total_alerts"] >= 1
        assert any(a["leakage_type"] == "overdue_uncollected" for a in data1["alerts"])

        initial_count = db_session.query(RevenueLeakageAlert).count()
        assert initial_count >= 1

        # Second Call: Should NOT create duplicate rows in the database
        resp2 = client.get("/api/ai/leakage-alerts")
        assert resp2.status_code == 200
        second_count = db_session.query(RevenueLeakageAlert).count()
        assert second_count == initial_count

    def test_status_filtering(self, client, db_session):
        alert_open = RevenueLeakageAlert(
            leakage_type="unbilled_active_subscription",
            severity="high",
            estimated_loss=Decimal("150.00"),
            description="Open anomaly",
            status="open",
        )
        alert_resolved = RevenueLeakageAlert(
            leakage_type="duplicate_billing_attempt",
            severity="critical",
            estimated_loss=Decimal("200.00"),
            description="Resolved anomaly",
            status="resolved",
        )
        db_session.add_all([alert_open, alert_resolved])
        db_session.commit()

        resp_open = client.get("/api/ai/leakage-alerts?status_filter=open")
        data_open = resp_open.json()
        assert all(a["status"] == "open" for a in data_open["alerts"])

        resp_res = client.get("/api/ai/leakage-alerts?status_filter=resolved")
        data_res = resp_res.json()
        assert all(a["status"] == "resolved" for a in data_res["alerts"])


# ==============================================================================
# 3. BUSINESS HEALTH SCORE ENDPOINT
# ==============================================================================

class TestHealthScoreEndpoint:
    def test_health_score_empty_database_runs_safely(self, client):
        response = client.get("/api/ai/health-score")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "health_score" in data
        assert "grade" in data
        assert "key_metrics" in data
        assert "insights" in data
        assert "recommendations" in data
        assert len(data["key_metrics"]) == 4

    def test_health_score_snapshot_persistence(self, client, db_session):
        cust = Customer(name="Big Client", email="big@client.com")
        prod = Product(name="Enterprise", price=Decimal("1000.00"), billing_interval="monthly")
        db_session.add_all([cust, prod])
        db_session.commit()

        sub = make_sub(cust.id, prod.id, "SUB-HEALTH-01", unit_price=Decimal("1000.00"), quantity=5)
        db_session.add(sub)
        db_session.commit()

        inv = Invoice(
            invoice_number="INV-HEALTH-01",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date.today() - timedelta(days=30),
            billing_period_end=date.today(),
            issue_date=date.today() - timedelta(days=30),
            due_date=date.today() - timedelta(days=15),
            subtotal=Decimal("5000.00"),
            total_amount=Decimal("5000.00"),
            amount_paid=Decimal("5000.00"),
            amount_due=Decimal("0.00"),
            status="paid",
        )
        db_session.add(inv)
        db_session.commit()

        pay = Payment(
            payment_reference="PAY-HEALTH-01",
            invoice_id=inv.id,
            customer_id=cust.id,
            amount=Decimal("5000.00"),
            payment_method="credit_card",
            status="successful",
            payment_date=date.today(),
        )
        db_session.add(pay)
        db_session.commit()

        response = client.get("/api/ai/health-score")
        assert response.status_code == 200
        data = response.json()
        assert data["mrr"] == 5000.0
        assert data["arr"] == 60000.0
        assert data["health_score"] >= 80.0

        # Verify today's snapshot was written to database
        snap = db_session.query(BusinessHealthSnapshot).filter(
            BusinessHealthSnapshot.snapshot_date == date.today()
        ).first()
        assert snap is not None
        assert snap.mrr == Decimal("5000.00")

        # Second call updates the snapshot without unique constraint crash
        resp2 = client.get("/api/ai/health-score")
        assert resp2.status_code == 200


# ==============================================================================
# 4. CUSTOMER CHURN RISK ENDPOINT
# ==============================================================================

class TestChurnRiskEndpoint:
    def test_churn_empty_database_returns_empty_summary(self, client):
        response = client.get("/api/ai/churn-risk")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["summary"]["total_customers"] == 0
        assert data["assessments"] == []

    def test_cohort_and_individual_churn_risk(self, client, db_session):
        c1 = Customer(name="Reliable Corp", email="c1@corp.com")
        c2 = Customer(name="Churning LLC", email="c2@llc.com")
        prod = Product(name="Basic", price=Decimal("50.00"), billing_interval="monthly")
        db_session.add_all([c1, c2, prod])
        db_session.commit()

        # Reliable sub
        sub1 = make_sub(
            c1.id,
            prod.id,
            "SUB-CHURN-01",
            unit_price=Decimal("50.00"),
            start_date=date.today() - timedelta(days=365),
            auto_renew=True,
        )
        # Churning sub
        sub2 = make_sub(
            c2.id,
            prod.id,
            "SUB-CHURN-02",
            unit_price=Decimal("50.00"),
            status="past_due",
            auto_renew=False,
            start_date=date.today() - timedelta(days=15),
        )
        db_session.add_all([sub1, sub2])
        db_session.commit()

        # Invoice for c2
        inv2 = Invoice(
            invoice_number="INV-CHURN-02",
            subscription_id=sub2.id,
            customer_id=c2.id,
            billing_period_start=date.today() - timedelta(days=30),
            billing_period_end=date.today(),
            issue_date=date.today() - timedelta(days=30),
            due_date=date.today() - timedelta(days=15),
            subtotal=Decimal("50.00"),
            total_amount=Decimal("50.00"),
            amount_paid=Decimal("0.00"),
            amount_due=Decimal("50.00"),
            status="overdue",
        )
        db_session.add(inv2)
        db_session.commit()

        # Failed payments on c2
        p1 = Payment(
            payment_reference="PAY-FAIL-1",
            invoice_id=inv2.id,
            customer_id=c2.id,
            amount=Decimal("50.00"),
            payment_method="credit_card",
            status="failed",
            payment_date=date.today(),
        )
        p2 = Payment(
            payment_reference="PAY-FAIL-2",
            invoice_id=inv2.id,
            customer_id=c2.id,
            amount=Decimal("50.00"),
            payment_method="credit_card",
            status="failed",
            payment_date=date.today(),
        )
        db_session.add_all([p1, p2])
        db_session.commit()

        # Cohort query
        resp_cohort = client.get("/api/ai/churn-risk")
        assert resp_cohort.status_code == 200
        cohort_data = resp_cohort.json()
        assert cohort_data["summary"]["total_customers"] == 2
        # C2 should be ranked highest risk first
        assert cohort_data["assessments"][0]["customer_id"] == c2.id

        # Specific customer query
        resp_single = client.get(f"/api/ai/churn-risk?customer_id={c2.id}")
        assert resp_single.status_code == 200
        single_data = resp_single.json()
        assert single_data["assessment"]["customer_id"] == c2.id
        assert single_data["assessment"]["risk_score"] > 50.0
        assert "recommended_action" in single_data["assessment"]

    def test_invalid_customer_id_returns_404(self, client):
        response = client.get("/api/ai/churn-risk?customer_id=99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ==============================================================================
# 5. INVOICE AUDITOR ENDPOINT
# ==============================================================================

class TestInvoiceAuditorEndpoint:
    def test_audit_invalid_invoice_id_returns_404(self, client):
        response = client.post("/api/ai/audit-invoice", json={"invoice_id": 99999})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_audit_single_valid_invoice(self, client, db_session):
        cust = Customer(name="Valid Client", email="valid@client.com")
        prod = Product(name="Pro Plan", price=Decimal("100.00"), billing_interval="monthly")
        db_session.add_all([cust, prod])
        db_session.commit()

        sub = make_sub(cust.id, prod.id, "SUB-AUDIT-01", unit_price=Decimal("100.00"), quantity=2)
        db_session.add(sub)
        db_session.commit()

        # Perfect invoice: subtotal=200, discount=20, tax=18, total=198
        inv = Invoice(
            invoice_number="INV-AUDIT-PERFECT",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date(2026, 11, 1),
            billing_period_end=date(2026, 11, 30),
            issue_date=date(2026, 11, 1),
            due_date=date(2026, 11, 15),
            subtotal=Decimal("200.00"),
            discount_amount=Decimal("20.00"),
            tax_amount=Decimal("18.00"),
            total_amount=Decimal("198.00"),
            amount_paid=Decimal("198.00"),
            amount_due=Decimal("0.00"),
            status="paid",
            is_audited=False,
        )
        db_session.add(inv)
        db_session.commit()

        # Add line item
        item = InvoiceItem(
            invoice_id=inv.id,
            description="Seats (x2)",
            quantity=2,
            unit_price=Decimal("100.00"),
            total_price=Decimal("200.00"),
        )
        db_session.add(item)
        db_session.commit()

        # Audit via POST
        response = client.post("/api/ai/audit-invoice", json={"invoice_id": inv.id, "update_model": True})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["audit"]["is_valid"] is True
        assert data["audit"]["discrepancy_amount"] == 0.0

        # Verify model was updated in DB
        db_session.refresh(inv)
        assert inv.is_audited is True
        assert inv.audit_discrepancy_notes is None

    def test_audit_discrepant_invoice_flags_error(self, client, db_session):
        cust = Customer(name="Error Client", email="err@client.com")
        prod = Product(name="Pro", price=Decimal("100.00"))
        db_session.add_all([cust, prod])
        db_session.commit()

        sub = make_sub(cust.id, prod.id, "SUB-AUDIT-02", unit_price=Decimal("100.00"))
        db_session.add(sub)
        db_session.commit()

        # Subtotal says 100, but total says 300 with 0 tax and 0 discount
        bad_inv = Invoice(
            invoice_number="INV-AUDIT-BAD",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date(2026, 11, 1),
            billing_period_end=date(2026, 11, 30),
            issue_date=date(2026, 11, 1),
            due_date=date(2026, 11, 15),
            subtotal=Decimal("100.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("300.00"),  # Error!
            amount_paid=Decimal("0.00"),
            amount_due=Decimal("300.00"),
            status="issued",
            is_audited=False,
        )
        db_session.add(bad_inv)
        db_session.commit()

        item = InvoiceItem(
            invoice_id=bad_inv.id,
            description="Unit",
            quantity=1,
            unit_price=Decimal("100.00"),
            total_price=Decimal("100.00"),
        )
        db_session.add(item)
        db_session.commit()

        response = client.post(f"/api/ai/audit-invoice?invoice_id={bad_inv.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["audit"]["is_valid"] is False
        assert data["audit"]["discrepancy_amount"] > 0
        assert len(data["audit"]["discrepancies"]) >= 1

        db_session.refresh(bad_inv)
        assert bad_inv.is_audited is False
        assert bad_inv.audit_discrepancy_notes is not None

    def test_batch_audit_all_invoices(self, client, db_session):
        # Empty DB batch
        resp_empty = client.post("/api/ai/audit-invoice")
        assert resp_empty.status_code == 200
        assert resp_empty.json()["audited_count"] == 0

        # Seed an invoice
        cust = Customer(name="Batch Customer", email="batch@cust.com")
        prod = Product(name="Batch Plan", price=Decimal("50.00"))
        db_session.add_all([cust, prod])
        db_session.commit()

        sub = make_sub(cust.id, prod.id, "SUB-BATCH", unit_price=Decimal("50.00"))
        db_session.add(sub)
        db_session.commit()

        inv = Invoice(
            invoice_number="INV-BATCH-01",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date(2026, 11, 1),
            billing_period_end=date(2026, 11, 30),
            issue_date=date(2026, 11, 1),
            due_date=date(2026, 11, 15),
            subtotal=Decimal("50.00"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("50.00"),
            amount_paid=Decimal("50.00"),
            amount_due=Decimal("0.00"),
            status="paid",
        )
        db_session.add(inv)
        db_session.commit()

        resp_batch = client.post("/api/ai/audit-invoice", json={"update_model": True})
        assert resp_batch.status_code == 200
        data = resp_batch.json()
        assert data["audited_count"] == 1
        assert data["valid_count"] == 1
        assert data["discrepancy_count"] == 0
