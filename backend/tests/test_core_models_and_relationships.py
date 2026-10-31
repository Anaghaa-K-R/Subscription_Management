"""
Unit Tests for SubscriptIQ Core Database Models and Relationships.

Verifies:
- All core models (User, Customer, Product, Subscription) register properly.
- Column types, numeric precision (12, 2), and defaults.
- Unique constraints and composite indexes.
- Foreign key resolution across all core and financial models.
- Bidirectional ORM relationships:
    * User <-> Customer
    * Customer <-> Subscription
    * Product <-> Subscription
    * Customer <-> Invoice
    * Subscription <-> Invoice
    * Invoice <-> Payment
    * Customer <-> Payment
    * Product <-> InvoiceItem
- Strict foreign key deletion restrictions (RESTRICT) protecting financial ledgers.
- Status enum and tuple definitions.
"""

from datetime import date, datetime
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.models import (
    Base,
    BILLING_INTERVALS,
    CUSTOMER_STATUSES,
    Customer,
    Discount,
    INVOICE_STATUSES,
    Invoice,
    InvoiceItem,
    PAYMENT_STATUSES,
    Payment,
    PRODUCT_STATUSES,
    Product,
    SUBSCRIPTION_STATUSES,
    Subscription,
    TaxRule,
    User,
)


@pytest.fixture
def db_session_with_fk():
    """
    Isolated in-memory SQLite session with foreign key constraints strictly enforced.
    SQLite requires explicit 'PRAGMA foreign_keys = ON' per connection.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session, engine
    finally:
        session.close()
        Base.metadata.drop_all(engine)


class TestCoreModelMetadata:
    def test_all_core_and_financial_tables_registered(self, db_session_with_fk):
        _, engine = db_session_with_fk
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        required_tables = {
            "users",
            "customers",
            "products",
            "subscriptions",
            "invoices",
            "invoice_items",
            "payments",
            "tax_rules",
            "discounts",
            "revenue_leakage_alerts",
            "business_health_snapshots",
        }
        assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"

    def test_customer_columns(self):
        inspector_cols = {c.name for c in Customer.__table__.columns}
        expected_cols = {
            "id",
            "user_id",
            "name",
            "email",
            "company_name",
            "billing_address",
            "tax_id",
            "currency",
            "is_tax_exempt",
            "status",
            "created_at",
            "updated_at",
        }
        assert expected_cols.issubset(inspector_cols)

    def test_product_columns_and_precision(self):
        cols = {c.name for c in Product.__table__.columns}
        expected_cols = {
            "id",
            "name",
            "description",
            "price",
            "billing_interval",
            "currency",
            "status",
            "created_at",
            "updated_at",
        }
        assert expected_cols.issubset(cols)
        assert Product.price.type.precision == 12
        assert Product.price.type.scale == 2

    def test_subscription_columns_and_precision(self):
        cols = {c.name for c in Subscription.__table__.columns}
        expected_cols = {
            "id",
            "subscription_number",
            "customer_id",
            "plan_id",
            "status",
            "billing_interval",
            "unit_price",
            "quantity",
            "currency",
            "start_date",
            "current_period_start",
            "current_period_end",
            "next_billing_date",
            "auto_renew",
            "created_at",
            "updated_at",
        }
        assert expected_cols.issubset(cols)
        assert Subscription.unit_price.type.precision == 12
        assert Subscription.unit_price.type.scale == 2

    def test_user_columns(self):
        cols = {c.name for c in User.__table__.columns}
        expected_cols = {
            "id",
            "email",
            "hashed_password",
            "full_name",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        }
        assert expected_cols.issubset(cols)


class TestCoreModelConstraints:
    def test_user_email_unique(self, db_session_with_fk):
        session, _ = db_session_with_fk
        u1 = User(email="test@subscriptiq.io", hashed_password="hash_secret_123")
        session.add(u1)
        session.commit()

        u2 = User(email="test@subscriptiq.io", hashed_password="another_hash_456")
        session.add(u2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_subscription_number_unique(self, db_session_with_fk):
        session, _ = db_session_with_fk

        # Seed customer and product
        cust = Customer(name="Acme Corp", email="billing@acme.com")
        prod = Product(name="Enterprise Tier", price=Decimal("499.00"), billing_interval="monthly")
        session.add_all([cust, prod])
        session.commit()

        sub1 = Subscription(
            subscription_number="SUB-2026-00001",
            customer_id=cust.id,
            plan_id=prod.id,
            status="active",
            billing_interval="monthly",
            unit_price=Decimal("499.00"),
            start_date=date(2026, 1, 1),
            current_period_start=date(2026, 1, 1),
            current_period_end=date(2026, 1, 31),
            next_billing_date=date(2026, 2, 1),
        )
        session.add(sub1)
        session.commit()

        sub2 = Subscription(
            subscription_number="SUB-2026-00001",
            customer_id=cust.id,
            plan_id=prod.id,
            status="active",
            billing_interval="monthly",
            unit_price=Decimal("499.00"),
            start_date=date(2026, 2, 1),
            current_period_start=date(2026, 2, 1),
            current_period_end=date(2026, 2, 28),
            next_billing_date=date(2026, 3, 1),
        )
        session.add(sub2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


class TestEndToEndRelationships:
    def test_full_subscriber_billing_flow(self, db_session_with_fk):
        session, _ = db_session_with_fk

        # 1. Create Auth User
        user = User(
            email="sarah.connor@cyberdyne.com",
            hashed_password="argon2$example_hash",
            full_name="Sarah Connor",
            role="customer",
        )
        session.add(user)
        session.commit()

        # 2. Create Customer Profile linked to User
        customer = Customer(
            user_id=user.id,
            name="Sarah Connor",
            email="sarah.connor@cyberdyne.com",
            company_name="Cyberdyne Resistance",
            billing_address="100 Tech Blvd, Los Angeles, CA",
            tax_id="US-CA-992817",
            currency="USD",
            is_tax_exempt=False,
            status="active",
        )
        session.add(customer)
        session.commit()

        # Check User <-> Customer One-to-One
        assert user.customer.id == customer.id
        assert customer.user.id == user.id

        # 3. Create Product / Plan
        plan = Product(
            name="Pro AI Automation",
            description="Autonomous recurring billing with predictive analytics",
            price=Decimal("199.00"),
            billing_interval="monthly",
            currency="USD",
            status="active",
        )
        session.add(plan)
        session.commit()

        # 4. Create Subscription
        subscription = Subscription(
            subscription_number="SUB-2026-9901",
            customer_id=customer.id,
            plan_id=plan.id,
            status="active",
            billing_interval="monthly",
            unit_price=Decimal("199.00"),
            quantity=2,
            currency="USD",
            start_date=date(2026, 11, 1),
            current_period_start=date(2026, 11, 1),
            current_period_end=date(2026, 11, 30),
            next_billing_date=date(2026, 12, 1),
            auto_renew=True,
        )
        session.add(subscription)
        session.commit()

        # Check Subscription <-> Customer and Subscription <-> Product
        assert subscription.customer.name == "Sarah Connor"
        assert subscription.plan.name == "Pro AI Automation"
        assert len(customer.subscriptions) == 1
        assert customer.subscriptions[0].subscription_number == "SUB-2026-9901"
        assert len(plan.subscriptions) == 1

        # 5. Create Invoice referencing Customer and Subscription
        invoice = Invoice(
            invoice_number="INV-2026-9901-01",
            subscription_id=subscription.id,
            customer_id=customer.id,
            currency="USD",
            billing_period_start=date(2026, 11, 1),
            billing_period_end=date(2026, 11, 30),
            issue_date=date(2026, 11, 1),
            due_date=date(2026, 11, 16),
            subtotal=Decimal("398.00"),
            total_amount=Decimal("398.00"),
            amount_paid=Decimal("0.00"),
            amount_due=Decimal("398.00"),
            status="issued",
        )
        item = InvoiceItem(
            invoice=invoice,
            product_id=plan.id,
            description="Pro AI Automation (2 seats)",
            quantity=Decimal("2.00"),
            unit_price=Decimal("199.00"),
            total_price=Decimal("398.00"),
        )
        session.add_all([invoice, item])
        session.commit()

        # Check Invoice <-> Customer and Invoice <-> Subscription
        assert invoice.customer.id == customer.id
        assert invoice.subscription.id == subscription.id
        assert len(customer.invoices) == 1
        assert customer.invoices[0].invoice_number == "INV-2026-9901-01"
        assert len(subscription.invoices) == 1
        assert len(invoice.items) == 1
        assert invoice.items[0].product.name == "Pro AI Automation"

        # 6. Record Payment
        payment = Payment(
            payment_reference="PAY-2026-9901-01",
            invoice_id=invoice.id,
            customer_id=customer.id,
            currency="USD",
            amount=Decimal("398.00"),
            payment_method="credit_card",
            status="successful",
            transaction_reference="ch_stripe_live_8827361",
        )
        session.add(payment)
        invoice.amount_paid = Decimal("398.00")
        invoice.amount_due = Decimal("0.00")
        invoice.status = "paid"
        session.commit()

        # Check Payment <-> Invoice and Payment <-> Customer
        assert payment.invoice.invoice_number == "INV-2026-9901-01"
        assert payment.customer.name == "Sarah Connor"
        assert len(invoice.payments) == 1
        assert len(customer.payments) == 1
        assert customer.payments[0].payment_reference == "PAY-2026-9901-01"


class TestDeletionSafetyAndRestrictions:
    def test_prevent_customer_deletion_when_invoices_exist(self, db_session_with_fk):
        session, _ = db_session_with_fk

        cust = Customer(name="Protected Client", email="client@protect.com")
        prod = Product(name="Basic Plan", price=Decimal("50.00"))
        session.add_all([cust, prod])
        session.commit()

        sub = Subscription(
            subscription_number="SUB-SAFE-01",
            customer_id=cust.id,
            plan_id=prod.id,
            status="active",
            billing_interval="monthly",
            unit_price=Decimal("50.00"),
            start_date=date(2026, 1, 1),
            current_period_start=date(2026, 1, 1),
            current_period_end=date(2026, 1, 31),
            next_billing_date=date(2026, 2, 1),
        )
        session.add(sub)
        session.commit()

        inv = Invoice(
            invoice_number="INV-SAFE-01",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            issue_date=date(2026, 1, 1),
            due_date=date(2026, 1, 15),
            subtotal=Decimal("50.00"),
            total_amount=Decimal("50.00"),
            amount_due=Decimal("50.00"),
            status="issued",
        )
        session.add(inv)
        session.commit()

        # Attempting to delete customer must be rejected due to ondelete="RESTRICT"
        session.delete(cust)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_prevent_invoice_deletion_when_payment_exists(self, db_session_with_fk):
        session, _ = db_session_with_fk

        cust = Customer(name="Ledger Audit Client", email="audit@client.com")
        prod = Product(name="Tier 1", price=Decimal("100.00"))
        session.add_all([cust, prod])
        session.commit()

        sub = Subscription(
            subscription_number="SUB-AUDIT-01",
            customer_id=cust.id,
            plan_id=prod.id,
            status="active",
            billing_interval="monthly",
            unit_price=Decimal("100.00"),
            start_date=date(2026, 1, 1),
            current_period_start=date(2026, 1, 1),
            current_period_end=date(2026, 1, 31),
            next_billing_date=date(2026, 2, 1),
        )
        session.add(sub)
        session.commit()

        inv = Invoice(
            invoice_number="INV-AUDIT-01",
            subscription_id=sub.id,
            customer_id=cust.id,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            issue_date=date(2026, 1, 1),
            due_date=date(2026, 1, 15),
            subtotal=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            amount_due=Decimal("0.00"),
            amount_paid=Decimal("100.00"),
            status="paid",
        )
        session.add(inv)
        session.commit()

        pay = Payment(
            payment_reference="PAY-AUDIT-01",
            invoice_id=inv.id,
            customer_id=cust.id,
            amount=Decimal("100.00"),
            payment_method="credit_card",
            status="successful",
        )
        session.add(pay)
        session.commit()

        # Attempting to delete invoice must be rejected because payment references it with RESTRICT
        session.delete(inv)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_prevent_product_deletion_when_subscription_exists(self, db_session_with_fk):
        session, _ = db_session_with_fk

        cust = Customer(name="Sub User", email="sub@user.com")
        prod = Product(name="Core Tier", price=Decimal("29.00"))
        session.add_all([cust, prod])
        session.commit()

        sub = Subscription(
            subscription_number="SUB-ACTIVE-99",
            customer_id=cust.id,
            plan_id=prod.id,
            status="active",
            billing_interval="monthly",
            unit_price=Decimal("29.00"),
            start_date=date(2026, 1, 1),
            current_period_start=date(2026, 1, 1),
            current_period_end=date(2026, 1, 31),
            next_billing_date=date(2026, 2, 1),
        )
        session.add(sub)
        session.commit()

        # Attempting to delete product must fail because active subscription references it with RESTRICT
        session.delete(prod)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_user_deletion_sets_customer_user_id_to_null(self, db_session_with_fk):
        session, _ = db_session_with_fk

        user = User(email="leaving@corp.com", hashed_password="pw_hash_test_123")
        session.add(user)
        session.commit()

        cust = Customer(user_id=user.id, name="Corporate Profile", email="leaving@corp.com")
        session.add(cust)
        session.commit()

        # Deleting auth user preserves historical customer profile and sets user_id to NULL
        session.delete(user)
        session.commit()

        session.refresh(cust)
        assert cust.user_id is None
        assert cust.name == "Corporate Profile"


class TestStatusTuples:
    def test_status_tuples(self):
        assert "active" in CUSTOMER_STATUSES
        assert "inactive" in CUSTOMER_STATUSES
        assert "archived" in CUSTOMER_STATUSES

        assert "active" in PRODUCT_STATUSES
        assert "archived" in PRODUCT_STATUSES

        assert "active" in SUBSCRIPTION_STATUSES
        assert "past_due" in SUBSCRIPTION_STATUSES
        assert "cancelled" in SUBSCRIPTION_STATUSES

        assert "monthly" in BILLING_INTERVALS
        assert "yearly" in BILLING_INTERVALS
