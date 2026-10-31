"""
SQLAlchemy Payment Model for SubscriptIQ.

Records payment transactions against invoices with:
- Partial payment reconciliation.
- Multi-status lifecycle (pending, successful, failed, refunded).
- High-precision Numeric(12, 2) amounts.
- Transaction and receipt references.
"""

from decimal import Decimal
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Payment(Base):
    """
    Payment transaction record.

    Attributes:
        id: Primary key identifier.
        payment_reference: Unique business transaction number (e.g., 'PAY-2026-00001').
        invoice_id: Foreign key to the target Invoice.
        customer_id: Foreign reference to paying customer (Member 2 model).
        currency: ISO-4217 currency code.
        amount: Transaction monetary amount.
        payment_method: Payment rail ('credit_card', 'bank_transfer', 'upi', 'cash', 'simulated_gateway').
        status: Transaction status ('pending', 'successful', 'failed', 'refunded').
        transaction_reference: Gateway payment ID or bank UTR number.
        payment_date: Timestamp transaction was executed.
        receipt_number: Generated customer receipt number.
        failure_reason: Error message if payment was declined or failed.
        notes: Audit notes.
        created_at: Audit creation timestamp.
        updated_at: Modification timestamp.
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_reference = Column(String(64), unique=True, index=True, nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True)

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)

    currency = Column(String(3), nullable=False, default="USD")
    amount = Column(Numeric(12, 2), nullable=False)
    payment_method = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)

    transaction_reference = Column(String(128), nullable=True, index=True)
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    receipt_number = Column(String(64), nullable=True)
    failure_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, ref='{self.payment_reference}', amount={self.amount}, status='{self.status}')>"
