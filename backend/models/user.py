"""
SQLAlchemy User Model for SubscriptIQ.

Core user entity for authentication and role-based access control,
coordinated with Member 2's authentication architecture.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    """
    User entity for authentication and system access.

    Attributes:
        id: Primary key identifier.
        email: Unique user email address (login credential).
        hashed_password: Salted password hash.
        full_name: User display/contact name.
        role: Access control role ('admin', 'finance_manager', 'customer').
        is_active: Account status flag.
        created_at: Audit registration timestamp.
        updated_at: Account modification timestamp.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="customer")
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="user", uselist=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
