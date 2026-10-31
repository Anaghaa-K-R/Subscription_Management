"""
SQLAlchemy Subscription Model for SubscriptIQ.

Core recurring contract entity managing customer lifecycle, renewal schedules,
unit pricing, and billing intervals.
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
    func,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Subscription(Base):
    """
    Subscription recurring contract entity.

    Attributes:
        id: Primary key identifier.
        subscription_number: Unique business reference (e.g., 'SUB-2026-00001').
        customer_id: Foreign key to subscriber Customer.
        plan_id: Foreign key to Product/Plan.
        status: Lifecycle status ('draft', 'active', 'past_due', 'paused', 'cancelled', 'expired').
        billing_interval: Cadence ('weekly', 'monthly', 'quarterly', 'yearly').
        unit_price: Rate per unit/seat billed per period (Numeric(12, 2)).
        quantity: Seat or unit multiplier.
        currency: ISO currency code.
        start_date: Contract commencement date.
        current_period_start: Start of active billing cycle.
        current_period_end: End of active billing cycle.
        next_billing_date: Timestamp date for upcoming renewal invoice generation.
        auto_renew: Flag indicating automatic cycle advancement.
        created_at: Audit registration timestamp.
        updated_at: Modification timestamp.
    """
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_number = Column(String(64), unique=True, index=True, nullable=False)

    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)

    status = Column(String(20), nullable=False, default="active", index=True)
    billing_interval = Column(String(20), nullable=False, default="monthly")
    unit_price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    quantity = Column(Integer, nullable=False, default=1)
    currency = Column(String(3), nullable=False, default="USD")

    start_date = Column(Date, nullable=False)
    current_period_start = Column(Date, nullable=False)
    current_period_end = Column(Date, nullable=False)
    next_billing_date = Column(Date, nullable=False, index=True)
    auto_renew = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_subscriptions_status_next_billing", "status", "next_billing_date"),
    )

    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Product", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, number='{self.subscription_number}', status='{self.status}', plan_id={self.plan_id})>"
