"""
AI Customer Churn Prediction Engine for SubscriptIQ.

Analyzes customer behavioral and financial telemetry to evaluate retention hazard:
1. Payment failure velocity (declines and card friction).
2. Delinquent overdue invoice aging.
3. Subscription auto-renew toggle cancellation signals.
4. Customer lifecycle tenure hazard curves.

Outputs a calibrated 0-100 risk score, risk tier classification, and automated retention playbooks.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from backend.services.finance.money_utils import to_decimal


@dataclass
class ChurnRiskAssessment:
    """Standardized customer churn and retention hazard assessment."""
    customer_id: int
    customer_name: str
    risk_score: float
    risk_category: str
    risk_factors: List[str]
    recommended_action: str
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert assessment to dictionary."""
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "risk_score": round(self.risk_score, 1),
            "risk_category": self.risk_category,
            "risk_factors": self.risk_factors,
            "recommended_action": self.recommended_action,
            "metrics": self.metrics,
        }


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to retrieve attribute from ORM model or dictionary."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _to_date(val: Any) -> Optional[date]:
    """Helper to convert string/datetime to date."""
    if val is None:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        try:
            return date.fromisoformat(val[:10])
        except ValueError:
            return None
    return None


def assess_customer_churn_risk(
    customer: Any,
    subscriptions: Optional[List[Any]] = None,
    invoices: Optional[List[Any]] = None,
    payments: Optional[List[Any]] = None,
    as_of_date: Optional[date] = None,
) -> ChurnRiskAssessment:
    """
    Evaluates individual subscriber risk profile across multi-factor telemetry.
    """
    as_of = as_of_date or date.today()
    cust_id = int(_get_val(customer, "id", 0))
    cust_name = str(_get_val(customer, "name") or _get_val(customer, "company_name") or f"Customer #{cust_id}")

    # Fall back to ORM relationships if lists not explicitly passed
    cust_subs = subscriptions if subscriptions is not None else _get_val(customer, "subscriptions", [])
    cust_invs = invoices if invoices is not None else _get_val(customer, "invoices", [])
    cust_pays = payments if payments is not None else _get_val(customer, "payments", [])

    # Filter to this customer if broad arrays passed
    my_subs = [s for s in cust_subs if int(_get_val(s, "customer_id", cust_id)) == cust_id]
    my_invs = [i for i in cust_invs if int(_get_val(i, "customer_id", cust_id)) == cust_id]
    my_pays = [p for p in cust_pays if int(_get_val(p, "customer_id", cust_id)) == cust_id]

    score = 0.0
    risk_factors: List[str] = []

    # 1. Failed Payment Analysis (Weight: 35 pts)
    # Consider failures within last 60 days
    sixty_days_ago = as_of - timedelta(days=60)
    recent_failed_payments = 0
    total_failed_payments = 0
    for p in my_pays:
        st = _get_val(p, "status", "")
        if st == "failed":
            total_failed_payments += 1
            p_date = _to_date(_get_val(p, "payment_date")) or _to_date(_get_val(p, "created_at"))
            if not p_date or p_date >= sixty_days_ago:
                recent_failed_payments += 1

    if recent_failed_payments >= 3:
        score += 35.0
        risk_factors.append(f"Severe payment failure velocity: {recent_failed_payments} failed transactions in last 60 days")
    elif recent_failed_payments == 2:
        score += 25.0
        risk_factors.append("Multiple failed payment attempts (2) indicate imminent involuntary churn")
    elif recent_failed_payments == 1:
        score += 15.0
        risk_factors.append("Recent failed transaction (1) indicates card expiration or processing friction")
    elif total_failed_payments > 0:
        score += 5.0
        risk_factors.append("Historical payment decline recorded on file")

    # 2. Overdue Invoices Analysis (Weight: 30 pts)
    overdue_count = 0
    max_days_overdue = 0
    total_overdue_balance = Decimal("0.00")

    for inv in my_invs:
        inv_status = _get_val(inv, "status", "")
        if inv_status in ("paid", "cancelled", "void"):
            continue
        due_d = _to_date(_get_val(inv, "due_date"))
        amount_due = to_decimal(_get_val(inv, "amount_due", 0))

        if due_d and due_d < as_of and amount_due > Decimal("0.00"):
            overdue_count += 1
            days = (as_of - due_d).days
            if days > max_days_overdue:
                max_days_overdue = days
            total_overdue_balance += amount_due

    if max_days_overdue > 30:
        score += 30.0
        risk_factors.append(f"Critical overdue invoice aging ({max_days_overdue} days overdue, balance: {total_overdue_balance})")
    elif max_days_overdue > 14:
        score += 20.0
        risk_factors.append(f"Moderately overdue invoices ({max_days_overdue} days, balance: {total_overdue_balance})")
    elif overdue_count > 0:
        score += 10.0
        risk_factors.append(f"{overdue_count} invoice(s) recently past due date")

    # 3. Auto-Renew Status Analysis (Weight: 20 pts)
    active_subs = [s for s in my_subs if _get_val(s, "status") in ("active", "past_due")]
    has_disabled_autorenew = False
    for sub in active_subs:
        auto_renew = _get_val(sub, "auto_renew", True)
        if auto_renew is False:
            has_disabled_autorenew = True
            break

    if has_disabled_autorenew:
        score += 20.0
        risk_factors.append("Active subscription has auto-renew toggle disabled, indicating voluntary cancellation intent")

    # 4. Subscription Tenure Hazard (Weight: 15 pts)
    # Early customers (<30-90 days) have highest churn hazard; >180 days have loyal baseline
    min_tenure_days = 9999
    if my_subs:
        for s in my_subs:
            start_d = _to_date(_get_val(s, "start_date")) or _to_date(_get_val(s, "created_at"))
            if start_d:
                tenure = max(0, (as_of - start_d).days)
                if tenure < min_tenure_days:
                    min_tenure_days = tenure
    else:
        # Check customer profile created_at
        c_created = _to_date(_get_val(customer, "created_at"))
        if c_created:
            min_tenure_days = max(0, (as_of - c_created).days)
        else:
            min_tenure_days = 30

    if min_tenure_days < 30:
        score += 15.0
        risk_factors.append("Early onboarding phase (<30 days tenure): vulnerable to initial adoption drop-off")
    elif min_tenure_days < 90:
        score += 10.0
        risk_factors.append("Trial / early adoption phase (30-90 days tenure)")
    elif min_tenure_days < 180:
        score += 5.0

    # Ensure bounded 0.0 to 100.0
    final_score = min(100.0, max(0.0, score))

    # Determine risk category & recommended playbook
    if final_score >= 75.0:
        risk_category = "critical"
        recommended_action = (
            "Immediate high-priority intervention: Contact customer directly, resolve billing method decline, "
            "and consider issuing a 15% retention credit before cycle termination."
        )
    elif final_score >= 50.0:
        risk_category = "high"
        recommended_action = (
            "Escalate to customer success manager: Send proactive payment update link and schedule a satisfaction check-in."
        )
    elif final_score >= 25.0:
        risk_category = "medium"
        recommended_action = (
            "Automated nurture: Dispatch friendly upcoming renewal reminder and verify card expiration details."
        )
    else:
        risk_category = "low"
        recommended_action = "Healthy subscriber: Standard automated recurring operations."

    if not risk_factors:
        risk_factors.append("Consistent payment track record with active auto-renewing subscriptions")

    return ChurnRiskAssessment(
        customer_id=cust_id,
        customer_name=cust_name,
        risk_score=final_score,
        risk_category=risk_category,
        risk_factors=risk_factors,
        recommended_action=recommended_action,
        metrics={
            "failed_payments_recent": recent_failed_payments,
            "failed_payments_total": total_failed_payments,
            "overdue_invoices_count": overdue_count,
            "max_days_overdue": max_days_overdue,
            "total_overdue_balance": float(total_overdue_balance),
            "auto_renew_disabled": has_disabled_autorenew,
            "tenure_days": min_tenure_days if min_tenure_days != 9999 else 0,
        },
    )


def assess_cohort_churn_risk(
    customers: List[Any],
    subscriptions: Optional[List[Any]] = None,
    invoices: Optional[List[Any]] = None,
    payments: Optional[List[Any]] = None,
    as_of_date: Optional[date] = None,
) -> List[ChurnRiskAssessment]:
    """
    Evaluates churn risk across a portfolio or cohort of customers.
    """
    results: List[ChurnRiskAssessment] = []
    for c in customers:
        results.append(
            assess_customer_churn_risk(
                customer=c,
                subscriptions=subscriptions,
                invoices=invoices,
                payments=payments,
                as_of_date=as_of_date,
            )
        )
    # Sort descending by risk score (highest risk first)
    results.sort(key=lambda r: r.risk_score, reverse=True)
    return results


def summarize_churn_risks(assessments: List[ChurnRiskAssessment]) -> Dict[str, Any]:
    """
    Produces aggregate telemetry across customer churn assessments.
    """
    total = len(assessments)
    if total == 0:
        return {
            "total_customers": 0,
            "average_risk_score": 0.0,
            "category_counts": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            "high_risk_count": 0,
            "at_risk_customer_ids": [],
        }

    counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    sum_score = 0.0
    high_risk_ids = []

    for a in assessments:
        counts[a.risk_category] = counts.get(a.risk_category, 0) + 1
        sum_score += a.risk_score
        if a.risk_category in ("high", "critical"):
            high_risk_ids.append(a.customer_id)

    return {
        "total_customers": total,
        "average_risk_score": round(sum_score / total, 1),
        "category_counts": counts,
        "high_risk_count": counts["high"] + counts["critical"],
        "at_risk_customer_ids": high_risk_ids,
    }
