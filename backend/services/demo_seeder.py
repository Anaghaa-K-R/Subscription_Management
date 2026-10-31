"""
SubscriptIQ Demo Data Seeder.

Populates realistic, enterprise-grade subscription, customer, billing, and payment records
to enable full demonstration of:
- Dashboard executive financial telemetry
- Customer directory and subscriptions management
- Invoices with PDF downloads and audit trails
- Real-time AI Revenue Leakage alerts
- 6-Month forward forecasting using historical invoice cashflows
- Customer Churn Risk scoring and playbooks
- Multi-factor Business Health Scoring (A+ to F)
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, Any

from sqlalchemy.orm import Session

from backend.database import Base, engine
from backend.models import (
    Customer,
    Product,
    Subscription,
    Invoice,
    InvoiceItem,
    Payment,
    Discount,
    TaxRule,
)


def seed_demo_data_if_empty(db: Session, force: bool = False) -> Dict[str, Any]:
    """
    Seeds realistic demo data if the customer table is empty or force=True.
    Returns summary of seeded records.
    """
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    existing_cust_count = db.query(Customer).count()
    if existing_cust_count > 0 and not force:
        return {"status": "skipped", "message": f"Database already contains {existing_cust_count} customers."}

    today = date.today()

    # 1. Products / Plans
    p_starter = Product(
        name="Starter Cloud",
        description="For growing teams scaling automated billing",
        price=Decimal("49.00"),
        billing_interval="monthly",
        currency="USD",
        status="active",
    )
    p_pro = Product(
        name="Pro Growth",
        description="Full recurring revenue analytics and AI insights",
        price=Decimal("199.00"),
        billing_interval="monthly",
        currency="USD",
        status="active",
    )
    p_enterprise = Product(
        name="Enterprise AI",
        description="Dedicated SLA, audit intelligence and custom dunning",
        price=Decimal("999.00"),
        billing_interval="monthly",
        currency="USD",
        status="active",
    )
    db.add_all([p_starter, p_pro, p_enterprise])
    db.commit()

    # 2. Customers
    c_stripe = Customer(
        name="Stripe Technologies",
        email="billing@stripe.demo",
        company_name="Stripe Inc.",
        billing_address="510 Townsend St, San Francisco, CA 94103",
        currency="USD",
        status="active",
        is_tax_exempt=False,
    )
    c_acme = Customer(
        name="Acme Corporation",
        email="finance@acme.demo",
        company_name="Acme Global Ltd.",
        billing_address="120 Innovation Way, Austin, TX 78701",
        currency="USD",
        status="active",
        is_tax_exempt=False,
    )
    c_nexa = Customer(
        name="Nexa Analytics",
        email="admin@nexa.demo",
        company_name="Nexa Systems",
        billing_address="88 Silicon Blvd, Seattle, WA 98101",
        currency="USD",
        status="active",
        is_tax_exempt=False,
    )
    c_techflow = Customer(
        name="TechFlow Inc",
        email="billing@techflow.demo",
        company_name="TechFlow LLC",
        billing_address="44 Tech Plaza, Boston, MA 02110",
        currency="USD",
        status="active",
        is_tax_exempt=False,
    )
    c_quantum = Customer(
        name="Quantum Dynamics",
        email="ap@quantum.demo",
        company_name="Quantum Dyn Corp",
        billing_address="900 Quantum Rd, Boulder, CO 80301",
        currency="USD",
        status="active",
        is_tax_exempt=False,
    )
    db.add_all([c_stripe, c_acme, c_nexa, c_techflow, c_quantum])
    db.commit()

    # 3. Subscriptions
    # Stripe: Enterprise plan, long tenure, healthy
    sub_stripe = Subscription(
        subscription_number="SUB-2026-0001",
        customer_id=c_stripe.id,
        plan_id=p_enterprise.id,
        status="active",
        billing_interval="monthly",
        unit_price=Decimal("999.00"),
        quantity=1,
        currency="USD",
        start_date=today - timedelta(days=365),
        current_period_start=today.replace(day=1),
        current_period_end=(today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
        next_billing_date=(today.replace(day=1) + timedelta(days=32)).replace(day=1),
        auto_renew=True,
    )
    # Acme: 2 Pro seats, active
    sub_acme = Subscription(
        subscription_number="SUB-2026-0002",
        customer_id=c_acme.id,
        plan_id=p_pro.id,
        status="active",
        billing_interval="monthly",
        unit_price=Decimal("199.00"),
        quantity=2,
        currency="USD",
        start_date=today - timedelta(days=180),
        current_period_start=today.replace(day=1),
        current_period_end=(today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
        next_billing_date=(today.replace(day=1) + timedelta(days=32)).replace(day=1),
        auto_renew=True,
    )
    # Nexa: 1 Pro seat, active
    sub_nexa = Subscription(
        subscription_number="SUB-2026-0003",
        customer_id=c_nexa.id,
        plan_id=p_pro.id,
        status="active",
        billing_interval="monthly",
        unit_price=Decimal("199.00"),
        quantity=1,
        currency="USD",
        start_date=today - timedelta(days=90),
        current_period_start=today.replace(day=1),
        current_period_end=(today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
        next_billing_date=(today.replace(day=1) + timedelta(days=32)).replace(day=1),
        auto_renew=True,
    )
    # TechFlow: 1 Starter seat, recent trial
    sub_techflow = Subscription(
        subscription_number="SUB-2026-0004",
        customer_id=c_techflow.id,
        plan_id=p_starter.id,
        status="active",
        billing_interval="monthly",
        unit_price=Decimal("49.00"),
        quantity=1,
        currency="USD",
        start_date=today - timedelta(days=10),
        current_period_start=today - timedelta(days=10),
        current_period_end=today + timedelta(days=20),
        next_billing_date=today + timedelta(days=20),
        auto_renew=True,
    )
    # Quantum: 1 Pro seat, past_due, auto_renew FALSE (churn vector!)
    sub_quantum = Subscription(
        subscription_number="SUB-2026-0005",
        customer_id=c_quantum.id,
        plan_id=p_pro.id,
        status="past_due",
        billing_interval="monthly",
        unit_price=Decimal("199.00"),
        quantity=1,
        currency="USD",
        start_date=today - timedelta(days=25),
        current_period_start=today - timedelta(days=25),
        current_period_end=today + timedelta(days=5),
        next_billing_date=today + timedelta(days=5),
        auto_renew=False,
    )
    # Missing renewal anomaly: Active sub with current_period_end in past and auto_renew=True
    sub_unbilled = Subscription(
        subscription_number="SUB-2026-0006",
        customer_id=c_nexa.id,
        plan_id=p_starter.id,
        status="active",
        billing_interval="monthly",
        unit_price=Decimal("49.00"),
        quantity=1,
        currency="USD",
        start_date=today - timedelta(days=60),
        current_period_start=today - timedelta(days=60),
        current_period_end=today - timedelta(days=5),  # 5 days ago!
        next_billing_date=today - timedelta(days=5),
        auto_renew=True,
    )
    db.add_all([sub_stripe, sub_acme, sub_nexa, sub_techflow, sub_quantum, sub_unbilled])
    db.commit()

    # 4. Invoices & Historical Months for Forecasting
    # Seed historical monthly paid invoices (May through October 2026)
    history_months = [
        ("INV-HIST-05", date(2026, 5, 1), Decimal("1450.00")),
        ("INV-HIST-06", date(2026, 6, 1), Decimal("1620.00")),
        ("INV-HIST-07", date(2026, 7, 1), Decimal("1810.00")),
        ("INV-HIST-08", date(2026, 8, 1), Decimal("2050.00")),
        ("INV-HIST-09", date(2026, 9, 1), Decimal("2380.00")),
    ]
    for inv_num, issue_d, amt in history_months:
        h_inv = Invoice(
            invoice_number=inv_num,
            subscription_id=sub_stripe.id,
            customer_id=c_stripe.id,
            currency="USD",
            billing_period_start=issue_d,
            billing_period_end=issue_d + timedelta(days=29),
            issue_date=issue_d,
            due_date=issue_d + timedelta(days=15),
            subtotal=amt,
            total_amount=amt,
            amount_paid=amt,
            amount_due=Decimal("0.00"),
            status="paid",
            is_audited=True,
        )
        db.add(h_inv)
        db.commit()

    # Active Month Invoices
    # 1. Stripe (Paid $999.00)
    inv_stripe = Invoice(
        invoice_number="INV-2026-0001",
        subscription_id=sub_stripe.id,
        customer_id=c_stripe.id,
        currency="USD",
        billing_period_start=today.replace(day=1),
        billing_period_end=(today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
        issue_date=today.replace(day=1),
        due_date=today.replace(day=1) + timedelta(days=15),
        subtotal=Decimal("999.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("999.00"),
        amount_paid=Decimal("999.00"),
        amount_due=Decimal("0.00"),
        status="paid",
        is_audited=True,
    )
    db.add(inv_stripe)
    db.commit()

    item_stripe = InvoiceItem(
        invoice_id=inv_stripe.id,
        description="Enterprise AI Platform (Monthly)",
        quantity=1,
        unit_price=Decimal("999.00"),
        total_price=Decimal("999.00"),
    )
    db.add(item_stripe)

    pay_stripe = Payment(
        payment_reference="PAY-2026-0001",
        invoice_id=inv_stripe.id,
        customer_id=c_stripe.id,
        currency="USD",
        amount=Decimal("999.00"),
        payment_method="credit_card",
        status="successful",
        payment_date=today.replace(day=1) + timedelta(days=1),
    )
    db.add(pay_stripe)

    # 2. Acme ($398.00, Paid)
    inv_acme = Invoice(
        invoice_number="INV-2026-0002",
        subscription_id=sub_acme.id,
        customer_id=c_acme.id,
        currency="USD",
        billing_period_start=today.replace(day=1),
        billing_period_end=(today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
        issue_date=today.replace(day=1),
        due_date=today.replace(day=1) + timedelta(days=15),
        subtotal=Decimal("398.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("398.00"),
        amount_paid=Decimal("398.00"),
        amount_due=Decimal("0.00"),
        status="paid",
        is_audited=True,
    )
    db.add(inv_acme)
    db.commit()

    item_acme = InvoiceItem(
        invoice_id=inv_acme.id,
        description="Pro Growth License (x2 Seats)",
        quantity=2,
        unit_price=Decimal("199.00"),
        total_price=Decimal("398.00"),
    )
    db.add(item_acme)

    pay_acme = Payment(
        payment_reference="PAY-2026-0002",
        invoice_id=inv_acme.id,
        customer_id=c_acme.id,
        currency="USD",
        amount=Decimal("398.00"),
        payment_method="bank_transfer",
        status="successful",
        payment_date=today.replace(day=1) + timedelta(days=2),
    )
    db.add(pay_acme)

    # 3. Nexa ($199.00, Issued / Pending)
    inv_nexa = Invoice(
        invoice_number="INV-2026-0003",
        subscription_id=sub_nexa.id,
        customer_id=c_nexa.id,
        currency="USD",
        billing_period_start=today.replace(day=1),
        billing_period_end=(today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
        issue_date=today.replace(day=1),
        due_date=today + timedelta(days=10),
        subtotal=Decimal("199.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("199.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("199.00"),
        status="issued",
        is_audited=False,
    )
    db.add(inv_nexa)
    db.commit()

    item_nexa = InvoiceItem(
        invoice_id=inv_nexa.id,
        description="Pro Growth License (Monthly)",
        quantity=1,
        unit_price=Decimal("199.00"),
        total_price=Decimal("199.00"),
    )
    db.add(item_nexa)

    # 4. Quantum: OVERDUE invoice + FAILED payment (revenue leakage + churn vector!)
    inv_quantum = Invoice(
        invoice_number="INV-2026-0004",
        subscription_id=sub_quantum.id,
        customer_id=c_quantum.id,
        currency="USD",
        billing_period_start=today - timedelta(days=50),
        billing_period_end=today - timedelta(days=21),
        issue_date=today - timedelta(days=50),
        due_date=today - timedelta(days=35),  # 35 days overdue!
        subtotal=Decimal("199.00"),
        discount_amount=Decimal("0.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("199.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("199.00"),
        status="overdue",
        is_audited=False,
    )
    db.add(inv_quantum)
    db.commit()

    item_quantum = InvoiceItem(
        invoice_id=inv_quantum.id,
        description="Pro Growth License (Unpaid Renewal)",
        quantity=1,
        unit_price=Decimal("199.00"),
        total_price=Decimal("199.00"),
    )
    db.add(item_quantum)

    pay_quantum_fail1 = Payment(
        payment_reference="PAY-2026-0004-F1",
        invoice_id=inv_quantum.id,
        customer_id=c_quantum.id,
        currency="USD",
        amount=Decimal("199.00"),
        payment_method="credit_card",
        status="failed",
        payment_date=today - timedelta(days=34),
    )
    pay_quantum_fail2 = Payment(
        payment_reference="PAY-2026-0004-F2",
        invoice_id=inv_quantum.id,
        customer_id=c_quantum.id,
        currency="USD",
        amount=Decimal("199.00"),
        payment_method="credit_card",
        status="failed",
        payment_date=today - timedelta(days=30),
    )
    db.add_all([pay_quantum_fail1, pay_quantum_fail2])
    db.commit()

    return {
        "status": "success",
        "customers_seeded": 5,
        "subscriptions_seeded": 6,
        "invoices_seeded": 9,
        "payments_seeded": 4,
    }
