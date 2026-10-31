"""
SubscriptIQ Database Models Registry.

Exports all SQLAlchemy declarative entities and status enums for SubscriptIQ:
- Core entities: User, Customer, Product, Subscription
- Financial operations: TaxRule, Discount, Invoice, InvoiceItem, Payment
- AI Revenue Intelligence: RevenueLeakageAlert, BusinessHealthSnapshot
"""

from backend.database import Base
from backend.models.user import User, PasswordResetToken
from backend.models.customer import Customer
from backend.models.product import Product
from backend.models.subscription import Subscription
from backend.models.tax import TaxRule
from backend.models.discount import Discount
from backend.models.invoice import Invoice, InvoiceItem
from backend.models.payment import Payment
from backend.models.intelligence import RevenueLeakageAlert, BusinessHealthSnapshot

# Standard Status Enums & Tuples
CUSTOMER_STATUSES = (
    "active",
    "inactive",
    "archived",
)

PRODUCT_STATUSES = (
    "active",
    "archived",
    "draft",
)

SUBSCRIPTION_STATUSES = (
    "draft",
    "active",
    "past_due",
    "paused",
    "cancelled",
    "expired",
)

BILLING_INTERVALS = (
    "weekly",
    "monthly",
    "quarterly",
    "yearly",
)

INVOICE_STATUSES = (
    "draft",
    "issued",
    "partially_paid",
    "paid",
    "overdue",
    "cancelled",
    "void",
)

PAYMENT_STATUSES = (
    "pending",
    "successful",
    "failed",
    "refunded",
)

LEAKAGE_TYPES = (
    "duplicate_billing_attempt",
    "expired_discount_applied",
    "billing_discrepancy",
    "overdue_uncollected",
    "missing_renewal_invoice",
    "unbilled_active_subscription",
)

SEVERITY_LEVELS = (
    "low",
    "medium",
    "high",
    "critical",
)

__all__ = [
    "Base",
    "User",
    "PasswordResetToken",
    "Customer",
    "Product",
    "Subscription",
    "TaxRule",
    "Discount",
    "Invoice",
    "InvoiceItem",
    "Payment",
    "RevenueLeakageAlert",
    "BusinessHealthSnapshot",
    "CUSTOMER_STATUSES",
    "PRODUCT_STATUSES",
    "SUBSCRIPTION_STATUSES",
    "BILLING_INTERVALS",
    "INVOICE_STATUSES",
    "PAYMENT_STATUSES",
    "LEAKAGE_TYPES",
    "SEVERITY_LEVELS",
]
