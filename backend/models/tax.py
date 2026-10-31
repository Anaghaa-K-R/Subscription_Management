"""
SQLAlchemy TaxRule Model for SubscriptIQ.

Stores regional, national, and category-level tax configurations with:
- High-precision percentage rates or fixed-amount tax fees.
- Compound tax sequencing support.
- Geographical jurisdiction metadata.
"""

from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from backend.database import Base


class TaxRule(Base):
    """
    Tax rule entity governing invoice tax calculations.

    Attributes:
        id: Primary key identifier.
        name: User-facing tax name (e.g., 'GST 18%', 'Standard VAT', 'State Tax').
        rate_percentage: Numeric tax percentage (e.g., 18.00 represents 18.00%).
        tax_type: 'percentage' or 'fixed_amount'.
        country: Country jurisdiction code or name.
        state_province: Optional state/provincial jurisdiction.
        is_active: Whether this tax rule is actively applied.
        is_compound: Whether tax is applied on top of other applied taxes.
        created_at: Audit creation timestamp.
        updated_at: Modification timestamp.
    """
    __tablename__ = "tax_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    rate_percentage = Column(Numeric(5, 2), nullable=False)
    tax_type = Column(String(20), nullable=False, default="percentage")
    country = Column(String(100), nullable=False)
    state_province = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_compound = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    invoices = relationship("Invoice", back_populates="tax_rule")

    def __repr__(self) -> str:
        return f"<TaxRule(id={self.id}, name='{self.name}', rate={self.rate_percentage}%, active={self.is_active})>"
