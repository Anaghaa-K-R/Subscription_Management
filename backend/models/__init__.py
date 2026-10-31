"""
SubscriptIQ Database Models Registry.

Exports all SQLAlchemy declarative entities and status enums for Member 3
financial operations and AI revenue protection.
"""

from backend.database import Base
from backend.models.tax import TaxRule
from backend.models.discount import Discount
from backend.models.invoice import Invoice, InvoiceItem
from backend.models.payment import Payment
from backend.models.intelligence import RevenueLeakageAlert, BusinessHealthSnapshot

# Standard Status Enums & Tuples
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
    "TaxRule",
    "Discount",
    "Invoice",
    "InvoiceItem",
    "Payment",
    "RevenueLeakageAlert",
    "BusinessHealthSnapshot",
    "INVOICE_STATUSES",
    "PAYMENT_STATUSES",
    "LEAKAGE_TYPES",
    "SEVERITY_LEVELS",
]
