"""
SQLAlchemy Revenue Intelligence & Protection Models for SubscriptIQ.

Stores insights, anomaly detections, and business health scores produced by:
- AI Revenue Leakage Detector.
- Intelligent Invoice Auditor.
- Smart Collections Assistant.
"""

from decimal import Decimal
from sqlalchemy import (
    Column,
    Date,
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


class RevenueLeakageAlert(Base):
    """
    Automated anomaly and revenue leakage alert entity.

    Attributes:
        id: Primary key identifier.
        leakage_type: Category of detected revenue risk
            ('duplicate_billing_attempt', 'expired_discount_applied',
             'billing_discrepancy', 'overdue_uncollected',
             'missing_renewal_invoice', 'unbilled_active_subscription').
        severity: Priority level ('low', 'medium', 'high', 'critical').
        estimated_loss: Quantified at-risk revenue amount.
        subscription_id: Associated subscription reference (Member 2 model).
        invoice_id: Associated invoice reference (Member 3 model).
        customer_id: Associated customer reference (Member 2 model).
        description: Diagnostic explanation of the leakage risk.
        recommended_action: Suggested remediation workflow.
        status: Resolution lifecycle ('open', 'investigating', 'resolved', 'dismissed').
        detected_at: Timestamp when risk was identified.
        resolved_at: Timestamp when issue was resolved or dismissed.
    """
    __tablename__ = "revenue_leakage_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    leakage_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, default="medium", index=True)
    estimated_loss = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    # Future Foreign Keys to Member 2 models:
    subscription_id = Column(Integer, nullable=True, index=True)
    customer_id = Column(Integer, nullable=True, index=True)

    # Intra-package relationship to Member 3 Invoice
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)

    description = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="open", index=True)

    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice = relationship("Invoice")

    def __repr__(self) -> str:
        return f"<RevenueLeakageAlert(id={self.id}, type='{self.leakage_type}', loss={self.estimated_loss}, status='{self.status}')>"


class BusinessHealthSnapshot(Base):
    """
    Daily / periodic multi-factor business financial health snapshot.

    Attributes:
        id: Primary key identifier.
        snapshot_date: Calculation date.
        mrr: Total Monthly Recurring Revenue.
        arr: Annual Recurring Revenue run-rate.
        active_subscriptions_count: Total active subscriber count.
        total_outstanding_amount: Uncollected accounts receivable.
        overdue_invoices_count: Number of overdue invoices.
        health_score: Composite 0-100 financial health index.
        created_at: Snapshot creation timestamp.
    """
    __tablename__ = "business_health_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, unique=True, index=True, nullable=False)

    mrr = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    arr = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    active_subscriptions_count = Column(Integer, nullable=False, default=0)
    total_outstanding_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    overdue_invoices_count = Column(Integer, nullable=False, default=0)
    health_score = Column(Numeric(5, 2), nullable=False, default=Decimal("100.00"))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<BusinessHealthSnapshot(date={self.snapshot_date}, score={self.health_score}, mrr={self.mrr})>"
