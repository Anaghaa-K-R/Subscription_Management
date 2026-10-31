"""
Unit Tests for Financial SQLAlchemy Models (backend/models/).

Uses an isolated, in-memory SQLite database to verify:
- Complete DDL table metadata creation without foreign-key deadlocks.
- Monetary Numeric(12, 2) column specifications.
- Unique constraints and indexes.
- ORM relationships (Invoice <-> InvoiceItem, Invoice <-> Payment, TaxRule, Discount).
- Cascade deletion behavior.
- Revenue intelligence and leakage alert persistence.
"""

from datetime import date, datetime
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.models import (
    Base,
    BusinessHealthSnapshot,
    Discount,
    INVOICE_STATUSES,
    Invoice,
    InvoiceItem,
    LEAKAGE_TYPES,
    PAYMENT_STATUSES,
    Payment,
    RevenueLeakageAlert,
    SEVERITY_LEVELS,
    TaxRule,
)


@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite engine and session for model testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session, engine
    finally:
        session.close()
        Base.metadata.drop_all(engine)


class TestFinancialModelMetadata:
    def test_tables_successfully_created(self, db_session):
        _, engine = db_session
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())

        expected_tables = {
            "tax_rules",
            "discounts",
            "invoices",
            "invoice_items",
            "payments",
            "revenue_leakage_alerts",
            "business_health_snapshots",
        }
        assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"

    def test_monetary_column_definitions(self):
        # Invoices
        assert Invoice.subtotal.type.precision == 12
        assert Invoice.subtotal.type.scale == 2
        assert Invoice.total_amount.type.precision == 12
        assert Invoice.total_amount.type.scale == 2
        assert Invoice.amount_due.type.precision == 12
        assert Invoice.amount_due.type.scale == 2

        # Payments
        assert Payment.amount.type.precision == 12
        assert Payment.amount.type.scale == 2

        # InvoiceItem
        assert InvoiceItem.unit_price.type.precision == 12
        assert InvoiceItem.unit_price.type.scale == 2
        assert InvoiceItem.total_price.type.precision == 12
        assert InvoiceItem.total_price.type.scale == 2

        # Discount & Tax
        assert Discount.value.type.precision == 12
        assert Discount.value.type.scale == 2
        assert TaxRule.rate_percentage.type.precision == 5
        assert TaxRule.rate_percentage.type.scale == 2

    def test_unique_constraints_and_indexes(self, db_session):
        _, engine = db_session
        inspector = inspect(engine)

        # Invoices unique constraint on invoice_number
        inv_indexes = {idx["name"]: idx for idx in inspector.get_indexes("invoices")}
        assert any("invoice_number" in idx["column_names"] and idx["unique"] for idx in inv_indexes.values())

        # Check composite unique constraint for duplicate billing prevention
        unique_constraints = inspector.get_unique_constraints("invoices")
        constraint_names = {uc["name"] for uc in unique_constraints}
        assert "uq_invoice_subscription_period" in constraint_names


class TestModelCRUDAndRelationships:
    def test_invoice_with_items_and_payment_workflow(self, db_session):
        session, _ = db_session

        # 1. Create TaxRule & Discount
        tax = TaxRule(name="GST 18%", rate_percentage=Decimal("18.00"), tax_type="percentage", country="India")
        discount = Discount(
            code="EARLYBIRD10",
            discount_type="percentage",
            value=Decimal("10.00"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        session.add_all([tax, discount])
        session.commit()

        # 2. Create Invoice
        invoice = Invoice(
            invoice_number="INV-2026-000001",
            subscription_id=42,  # Contract reference to Member 2 Subscription
            customer_id=10,      # Contract reference to Member 2 Customer
            currency="USD",
            billing_period_start=date(2026, 11, 1),
            billing_period_end=date(2026, 11, 30),
            issue_date=date(2026, 11, 1),
            due_date=date(2026, 11, 16),
            subtotal=Decimal("100.00"),
            discount_amount=Decimal("10.00"),
            discount=discount,
            tax_amount=Decimal("16.20"),
            tax_rule=tax,
            tax_rate_applied=Decimal("18.00"),
            total_amount=Decimal("106.20"),
            amount_paid=Decimal("50.00"),
            amount_due=Decimal("56.20"),
            status="partially_paid",
        )

        # Add line item
        item = InvoiceItem(
            description="Pro Subscription Plan",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("10.00"),
            tax_amount=Decimal("16.20"),
            total_price=Decimal("106.20"),
        )
        invoice.items.append(item)

        # Add payment
        payment = Payment(
            payment_reference="PAY-2026-000001",
            customer_id=10,
            currency="USD",
            amount=Decimal("50.00"),
            payment_method="credit_card",
            status="successful",
            transaction_reference="txn_stripe_987654",
        )
        invoice.payments.append(payment)

        session.add(invoice)
        session.commit()

        # 3. Query back and verify ORM navigation
        fetched_inv = session.query(Invoice).filter_by(invoice_number="INV-2026-000001").first()
        assert fetched_inv is not None
        assert fetched_inv.total_amount == Decimal("106.20")
        assert len(fetched_inv.items) == 1
        assert fetched_inv.items[0].description == "Pro Subscription Plan"
        assert len(fetched_inv.payments) == 1
        assert fetched_inv.payments[0].payment_reference == "PAY-2026-000001"
        assert fetched_inv.tax_rule.name == "GST 18%"
        assert fetched_inv.discount.code == "EARLYBIRD10"

        # Back-populates check
        assert fetched_inv.items[0].invoice.id == fetched_inv.id
        assert fetched_inv.payments[0].invoice.id == fetched_inv.id

    def test_duplicate_invoice_prevention_constraint(self, db_session):
        session, _ = db_session

        inv1 = Invoice(
            invoice_number="INV-DUP-01",
            subscription_id=99,
            customer_id=5,
            billing_period_start=date(2026, 11, 1),
            billing_period_end=date(2026, 11, 30),
            issue_date=date(2026, 11, 1),
            due_date=date(2026, 11, 16),
            subtotal=Decimal("50.00"),
            total_amount=Decimal("50.00"),
            amount_due=Decimal("50.00"),
            status="issued",
        )
        session.add(inv1)
        session.commit()

        # Attempt to insert identical subscription_id and billing period
        inv2 = Invoice(
            invoice_number="INV-DUP-02",
            subscription_id=99,
            customer_id=5,
            billing_period_start=date(2026, 11, 1),
            billing_period_end=date(2026, 11, 30),
            issue_date=date(2026, 11, 1),
            due_date=date(2026, 11, 16),
            subtotal=Decimal("50.00"),
            total_amount=Decimal("50.00"),
            amount_due=Decimal("50.00"),
            status="issued",
        )
        session.add(inv2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_cascade_delete_invoice_items(self, db_session):
        session, _ = db_session

        inv = Invoice(
            invoice_number="INV-CASCADE-01",
            subscription_id=1,
            customer_id=1,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            issue_date=date(2026, 1, 1),
            due_date=date(2026, 1, 16),
            subtotal=Decimal("20.00"),
            total_amount=Decimal("20.00"),
            amount_due=Decimal("20.00"),
        )
        item = InvoiceItem(description="Disposable Item", quantity=1, unit_price=20, total_price=20)
        inv.items.append(item)
        session.add(inv)
        session.commit()

        # Delete invoice and verify child items are removed
        session.delete(inv)
        session.commit()
        remaining_items = session.query(InvoiceItem).filter_by(description="Disposable Item").all()
        assert len(remaining_items) == 0


class TestRevenueLeakageAlertModel:
    def test_create_leakage_alert(self, db_session):
        session, _ = db_session

        alert = RevenueLeakageAlert(
            leakage_type="duplicate_billing_attempt",
            severity="critical",
            estimated_loss=Decimal("199.00"),
            subscription_id=77,
            customer_id=23,
            description="Detected duplicate renewal attempt for period 2026-11-01 to 2026-11-30.",
            recommended_action="Cancel duplicate queue job and notify finance team.",
            status="open",
        )
        session.add(alert)
        session.commit()

        fetched = session.query(RevenueLeakageAlert).filter_by(subscription_id=77).first()
        assert fetched is not None
        assert fetched.estimated_loss == Decimal("199.00")
        assert fetched.severity == "critical"
        assert fetched.status == "open"

    def test_business_health_snapshot(self, db_session):
        session, _ = db_session

        snapshot = BusinessHealthSnapshot(
            snapshot_date=date(2026, 11, 1),
            mrr=Decimal("45000.00"),
            arr=Decimal("540000.00"),
            active_subscriptions_count=210,
            total_outstanding_amount=Decimal("3500.00"),
            overdue_invoices_count=4,
            health_score=Decimal("94.50"),
        )
        session.add(snapshot)
        session.commit()

        fetched = session.query(BusinessHealthSnapshot).filter_by(snapshot_date=date(2026, 11, 1)).first()
        assert fetched is not None
        assert fetched.health_score == Decimal("94.50")
        assert fetched.mrr == Decimal("45000.00")


class TestStatusConstants:
    def test_invoice_statuses(self):
        assert "draft" in INVOICE_STATUSES
        assert "issued" in INVOICE_STATUSES
        assert "partially_paid" in INVOICE_STATUSES
        assert "paid" in INVOICE_STATUSES
        assert "overdue" in INVOICE_STATUSES
        assert "cancelled" in INVOICE_STATUSES
        assert "void" in INVOICE_STATUSES

    def test_payment_statuses(self):
        assert "pending" in PAYMENT_STATUSES
        assert "successful" in PAYMENT_STATUSES
        assert "failed" in PAYMENT_STATUSES
        assert "refunded" in PAYMENT_STATUSES

    def test_leakage_types_and_severities(self):
        assert "duplicate_billing_attempt" in LEAKAGE_TYPES
        assert "critical" in SEVERITY_LEVELS
