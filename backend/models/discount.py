"""
SQLAlchemy Discount Model for SubscriptIQ.

Stores promotional discounts, coupons, and subscription pricing concessions with:
- Percentage-based or fixed-amount discounts.
- Minimum purchase and quantity gating.
- Expiration and redemption usage limits.
"""

from decimal import Decimal
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from backend.database import Base


class Discount(Base):
    """
    Discount rule entity governing invoice & subscription deductions.

    Attributes:
        id: Primary key identifier.
        code: Unique promotional coupon code (e.g., 'SAVE20').
        discount_type: 'percentage' or 'fixed_amount'.
        value: Numeric discount amount or percentage value.
        currency: ISO-4217 currency code (required for fixed_amount discounts).
        min_purchase_amount: Minimum invoice subtotal required to qualify.
        min_quantity: Minimum item or seat count required to qualify.
        max_discount_amount: Maximum discount ceiling for percentage discounts.
        start_date: Promotion start date.
        end_date: Promotion expiration date.
        max_uses: Maximum allowed global redemptions (None = unlimited).
        current_uses: Current redemption counter.
        is_active: Whether discount code is active.
        applicable_plan_id: Plan restriction (Future FK to plans.id).
        created_at: Audit creation timestamp.
        updated_at: Modification timestamp.
    """
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    discount_type = Column(String(20), nullable=False)  # 'percentage' or 'fixed_amount'
    value = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=True)

    min_purchase_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    min_quantity = Column(Integer, nullable=False, default=1)
    max_discount_amount = Column(Numeric(12, 2), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    max_uses = Column(Integer, nullable=True)
    current_uses = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Note: Customer/Plan models owned by Member 2.
    # Future relationship: applicable_plan = relationship("Plan")
    applicable_plan_id = Column(Integer, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    invoices = relationship("Invoice", back_populates="discount")

    def __repr__(self) -> str:
        return f"<Discount(id={self.id}, code='{self.code}', type='{self.discount_type}', value={self.value})>"
