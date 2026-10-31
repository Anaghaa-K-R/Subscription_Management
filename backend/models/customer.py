"""
SQLAlchemy Customer Model for SubscriptIQ.

Core customer billing profile representing business and individual subscribers.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

try:
    from backend.database import Base
except ModuleNotFoundError:
    from database import Base


class Customer(Base):
    """
    Customer billing entity.

    Attributes:
        id: Primary key identifier.
        user_id: Optional reference to auth user account.
        name: Customer contact/display name.
        email: Customer billing notification email address.
        company_name: Organization/enterprise legal entity name.
        billing_address: Full physical billing address for invoicing and tax jurisdiction.
        tax_id: Registered tax identification number (e.g. VAT/GSTIN).
        currency: Primary settlement currency (default 'USD').
        is_tax_exempt: Exemption flag bypassing automated tax calculation.
        status: Customer lifecycle state ('active', 'inactive', 'archived').
        created_at: Audit registration timestamp.
        updated_at: Account modification timestamp.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    billing_address = Column(Text, nullable=True)
    tax_id = Column(String(64), nullable=True)
    currency = Column(String(3), nullable=False, default="USD")
    is_tax_exempt = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="active", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="customer")
    subscriptions = relationship("Subscription", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")

    def __repr__(self) -> str:
        return f"<Customer(id={self.id}, name='{self.name}', email='{self.email}', status='{self.status}')>"
