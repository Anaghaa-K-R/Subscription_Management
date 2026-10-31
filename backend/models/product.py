"""
SQLAlchemy Product / Plan Model for SubscriptIQ.

Represents subscription plans, tiers, and add-on products available for recurring billing.
"""

from decimal import Decimal
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

try:
    from backend.database import Base
except ModuleNotFoundError:
    from database import Base


class Product(Base):
    """
    Product or Subscription Plan entity.

    Attributes:
        id: Primary key identifier.
        name: Product or plan tier name (e.g., 'Starter Plan', 'Enterprise Tier').
        description: Marketing or feature details.
        price: Base recurring price (Numeric(12, 2)).
        billing_interval: Cadence ('weekly', 'monthly', 'quarterly', 'yearly').
        currency: Pricing ISO currency code (default 'USD').
        status: Availability status ('active', 'archived', 'draft').
        created_at: Audit creation timestamp.
        updated_at: Modification timestamp.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    billing_interval = Column(String(20), nullable=False, default="monthly")
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(20), nullable=False, default="active", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")
    invoice_items = relationship("InvoiceItem", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', price={self.price}, interval='{self.billing_interval}')>"
