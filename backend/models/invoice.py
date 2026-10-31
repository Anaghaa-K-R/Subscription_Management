"""
SQLAlchemy Invoice & InvoiceItem Models for SubscriptIQ.

The central financial ledger for recurring billing, providing:
- Guaranteed database-level duplicate billing protection.
- High-precision Decimal monetary accounting.
- Multi-state lifecycle tracking (draft, issued, partially_paid, paid, overdue, cancelled, void).
- Automated auditing validation status.
- Strict cascade and audit compliance.
"""

from decimal import Decimal
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Invoice(Base):
    """
    Central Invoice ledger entity.

    Attributes:
        id: Primary key identifier.
        invoice_number: Unique business invoice number (e.g., 'INV-2026-00001').
        subscription_id: Foreign reference to subscription (Member 2 model).
        customer_id: Foreign reference to customer (Member 2 model).
        currency: ISO-4217 currency code (e.g., 'USD', 'INR').
        billing_period_start: Start date of billed recurring window.
        billing_period_end: End date of billed recurring window.
        issue_date: Date the invoice was generated and issued.
        due_date: Date payment is due before becoming overdue.
        subtotal: Sum of item gross totals before discounts and taxes.
        discount_amount: Cumulative discount deductions.
        discount_id: Nullable foreign key to applied Discount coupon.
        tax_amount: Cumulative tax additions.
        tax_rule_id: Nullable foreign key to primary applied TaxRule.
        tax_rate_applied: Percentage tax rate applied at generation time.
        total_amount: Final invoice total (subtotal - discount + tax).
        amount_paid: Cumulative recorded successful payments.
        amount_due: Remaining outstanding balance (total_amount - amount_paid).
        status: Lifecycle status ('draft', 'issued', 'partially_paid', 'paid', 'overdue', 'cancelled', 'void').
        pdf_path: Local or cloud storage path of the ReportLab generated PDF.
        is_audited: Verified by AI Invoice Auditor.
        audit_discrepancy_notes: Explanation of detected arithmetic discrepancies.
        notes: Customer notes or terms.
        created_at: Audit creation timestamp.
        updated_at: Modification timestamp.
    """
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(64), unique=True, index=True, nullable=False)

    # --------------------------------------------------------------------------
    # MEMBER 2 FOREIGN KEY INTEGRATION CONTRACT:
    # Customer and Subscription models are owned by Member 2.
    # To permit independent metadata creation and migration before Member 2's
    # models are finalized, these are indexed Integer columns with the target
    # foreign keys documented for activation:
    #
    # Future Foreign Keys:
    #   customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    #   subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="RESTRICT"), nullable=False, index=True)
    #
    # Future Relationships:
    #   customer = relationship("Customer", back_populates="invoices")
    #   subscription = relationship("Subscription", back_populates="invoices")
    # --------------------------------------------------------------------------
    subscription_id = Column(Integer, nullable=False, index=True)
    customer_id = Column(Integer, nullable=False, index=True)

    currency = Column(String(3), nullable=False, default="USD")
    billing_period_start = Column(Date, nullable=False, index=True)
    billing_period_end = Column(Date, nullable=False, index=True)
    issue_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=False, index=True)

    # Monetary Fields (Strictly Numeric 12, 2)
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    discount_id = Column(Integer, ForeignKey("discounts.id", ondelete="SET NULL"), nullable=True, index=True)

    tax_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tax_rule_id = Column(Integer, ForeignKey("tax_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    tax_rate_applied = Column(Numeric(5, 2), nullable=True)

    total_amount = Column(Numeric(12, 2), nullable=False)
    amount_paid = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    amount_due = Column(Numeric(12, 2), nullable=False)

    # Status: 'draft', 'issued', 'partially_paid', 'paid', 'overdue', 'cancelled', 'void'
    status = Column(String(20), nullable=False, default="draft", index=True)

    pdf_path = Column(String(500), nullable=True)
    is_audited = Column(Boolean, nullable=False, default=False)
    audit_discrepancy_notes = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Database-level Constraints & Composite Indexes
    __table_args__ = (
        # RULE 9 & 10: Prevent duplicate billing cycles at the database engine level
        UniqueConstraint(
            "subscription_id",
            "billing_period_start",
            "billing_period_end",
            name="uq_invoice_subscription_period",
        ),
        # High-performance index for overdue invoice detection
        Index("ix_invoices_due_date_status", "due_date", "status"),
        # High-performance index for customer portal invoice history
        Index("ix_invoices_customer_status", "customer_id", "status"),
    )

    # Intra-Package Relationships
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    tax_rule = relationship("TaxRule", back_populates="invoices")
    discount = relationship("Discount", back_populates="invoices")

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total={self.total_amount}, status='{self.status}')>"


class InvoiceItem(Base):
    """
    Itemized line item on an invoice.

    Attributes:
        id: Primary key identifier.
        invoice_id: Cascade foreign key to parent Invoice.
        product_id: Optional reference to product (Member 2 model).
        description: Line item name or detail.
        quantity: Billed units or seat count.
        unit_price: Unit rate.
        discount_amount: Line-level discount deduction.
        tax_amount: Line-level tax portion.
        total_price: Net line total (quantity * unit_price - discount + tax).
        created_at: Audit creation timestamp.
    """
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)

    # Future Foreign Key:
    #   product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(Integer, nullable=True, index=True)

    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False, default=Decimal("1.00"))
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tax_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total_price = Column(Numeric(12, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")

    def __repr__(self) -> str:
        return f"<InvoiceItem(id={self.id}, invoice_id={self.invoice_id}, desc='{self.description}', total={self.total_price})>"
