"""
SubscriptIQ AI Revenue Intelligence Module.

Provides autonomous financial intelligence, predictive analytics, and revenue protection:
- Revenue Leakage Detection (6 distinct risk vectors)
- Intelligent Invoice Auditing (deterministic line-item and tax recalculation)
- Statistical Revenue Forecasting (NumPy & Pandas 6-month forward projections)
- Customer Churn Risk Prediction (telemetry-based risk scoring)
- Multi-factor Business Financial Health Index (0-100 composite scoring)
"""

from backend.services.intelligence.leakage_detector import (
    LeakageAlertResult,
    detect_revenue_leakage,
    detect_unbilled_subscriptions,
    detect_duplicate_invoices,
    detect_expired_discounts,
    detect_overdue_invoices,
    detect_missing_renewals,
    detect_payment_reconciliation_gaps,
)
from backend.services.intelligence.invoice_auditor import (
    AuditResult,
    audit_invoice,
    audit_invoices_batch,
)
from backend.services.intelligence.forecasting_service import (
    ForecastResult,
    forecast_revenue,
    generate_forecast_from_invoices,
)
from backend.services.intelligence.churn_service import (
    ChurnRiskAssessment,
    assess_customer_churn_risk,
    assess_cohort_churn_risk,
    summarize_churn_risks,
)
from backend.services.intelligence.health_score_service import (
    HealthScoreResult,
    calculate_business_health_score,
)

__all__ = [
    # Leakage Detection
    "LeakageAlertResult",
    "detect_revenue_leakage",
    "detect_unbilled_subscriptions",
    "detect_duplicate_invoices",
    "detect_expired_discounts",
    "detect_overdue_invoices",
    "detect_missing_renewals",
    "detect_payment_reconciliation_gaps",
    # Invoice Auditing
    "AuditResult",
    "audit_invoice",
    "audit_invoices_batch",
    # Forecasting
    "ForecastResult",
    "forecast_revenue",
    "generate_forecast_from_invoices",
    # Churn Prediction
    "ChurnRiskAssessment",
    "assess_customer_churn_risk",
    "assess_cohort_churn_risk",
    "summarize_churn_risks",
    # Business Health Score
    "HealthScoreResult",
    "calculate_business_health_score",
]
