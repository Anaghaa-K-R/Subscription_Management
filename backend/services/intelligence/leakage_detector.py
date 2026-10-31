"""
AI Revenue Leakage Detector for SubscriptIQ.

Scans subscriptions, invoices, discounts, and payment ledgers to detect:
1. Unbilled active subscriptions (billing cycle started/elapsed without an invoice).
2. Duplicate billing attempts (multiple invoices covering identical periods).
3. Expired discounts improperly deducted from recurring revenue.
4. Overdue unpaid invoices requiring collection / dunning intervention.
5. Missing renewal invoices for active auto-renewing subscriptions.
6. Payment reconciliation discrepancies (payments sum != invoice amount_paid).

Quantifies estimated financial loss and produces actionable remediation workflows.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.models.intelligence import RevenueLeakageAlert
from backend.services.finance.money_utils import (
    money_add,
    money_sub,
    money_mul,
    round_money,
    to_decimal,
)


@dataclass
class LeakageAlertResult:
    """Standardized revenue leakage diagnostic result."""
    leakage_type: str
    severity: str
    estimated_loss: Decimal
    description: str
    recommended_action: str
    subscription_id: Optional[int] = None
    invoice_id: Optional[int] = None
    customer_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_alert_model(self) -> RevenueLeakageAlert:
        """Converts this result into a persistent SQLAlchemy RevenueLeakageAlert model."""
        return RevenueLeakageAlert(
            leakage_type=self.leakage_type,
            severity=self.severity,
            estimated_loss=self.estimated_loss,
            subscription_id=self.subscription_id,
            invoice_id=self.invoice_id,
            customer_id=self.customer_id,
            description=self.description,
            recommended_action=self.recommended_action,
            status="open",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Converts result to JSON-serializable dictionary."""
        return {
            "leakage_type": self.leakage_type,
            "severity": self.severity,
            "estimated_loss": float(self.estimated_loss),
            "subscription_id": self.subscription_id,
            "invoice_id": self.invoice_id,
            "customer_id": self.customer_id,
            "description": self.description,
            "recommended_action": self.recommended_action,
            "metadata": self.metadata,
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


def detect_unbilled_subscriptions(
    subscriptions: List[Any],
    invoices: List[Any],
    as_of_date: Optional[date] = None,
) -> List[LeakageAlertResult]:
    """
    Detect active subscriptions that are due for billing but have no invoice.
    """
    as_of = as_of_date or date.today()
    alerts: List[LeakageAlertResult] = []

    # Map existing invoices by subscription_id to their billing periods
    billed_periods: Set[Tuple[int, date, date]] = set()
    for inv in invoices:
        sub_id = _get_val(inv, "subscription_id")
        p_start = _to_date(_get_val(inv, "billing_period_start"))
        p_end = _to_date(_get_val(inv, "billing_period_end"))
        status = _get_val(inv, "status", "")
        if sub_id and p_start and p_end and status not in ("cancelled", "void"):
            billed_periods.add((sub_id, p_start, p_end))

    for sub in subscriptions:
        status = _get_val(sub, "status", "")
        if status not in ("active", "past_due"):
            continue

        sub_id = _get_val(sub, "id")
        sub_num = _get_val(sub, "subscription_number", f"SUB-{sub_id}")
        cust_id = _get_val(sub, "customer_id")
        next_billing = _to_date(_get_val(sub, "next_billing_date"))
        period_start = _to_date(_get_val(sub, "current_period_start"))
        period_end = _to_date(_get_val(sub, "current_period_end"))
        unit_price = to_decimal(_get_val(sub, "unit_price", 0))
        quantity = Decimal(str(_get_val(sub, "quantity", 1)))
        loss = round_money(money_mul(unit_price, quantity))

        if next_billing and next_billing <= as_of:
            # Check if an invoice covers the current cycle
            cycle_key = (sub_id, period_start, period_end) if (period_start and period_end) else None
            if not cycle_key or cycle_key not in billed_periods:
                days_overdue = (as_of - next_billing).days
                severity = "critical" if days_overdue > 14 else ("high" if days_overdue > 3 else "medium")
                alerts.append(
                    LeakageAlertResult(
                        leakage_type="unbilled_active_subscription",
                        severity=severity,
                        estimated_loss=loss,
                        subscription_id=sub_id,
                        customer_id=cust_id,
                        description=(
                            f"Active subscription {sub_num} reached next billing date ({next_billing}) "
                            f"{days_overdue} days ago, but no recurring invoice was generated."
                        ),
                        recommended_action=(
                            f"Trigger billing cycle run for subscription {sub_num} to generate the missing invoice."
                        ),
                        metadata={"days_overdue": days_overdue, "next_billing_date": str(next_billing)},
                    )
                )

    return alerts


def detect_duplicate_invoices(invoices: List[Any]) -> List[LeakageAlertResult]:
    """
    Detect multiple non-void invoices generated for the same subscription & billing period.
    """
    alerts: List[LeakageAlertResult] = []
    # Group by (subscription_id, period_start, period_end)
    period_invoices: Dict[Tuple[int, date, date], List[Any]] = {}

    for inv in invoices:
        status = _get_val(inv, "status", "")
        if status in ("cancelled", "void"):
            continue
        sub_id = _get_val(inv, "subscription_id")
        p_start = _to_date(_get_val(inv, "billing_period_start"))
        p_end = _to_date(_get_val(inv, "billing_period_end"))
        if sub_id and p_start and p_end:
            key = (sub_id, p_start, p_end)
            period_invoices.setdefault(key, []).append(inv)

    for (sub_id, p_start, p_end), inv_list in period_invoices.items():
        if len(inv_list) > 1:
            # First invoice is legitimate, duplicates represent duplicate billing / refund risk
            duplicates = inv_list[1:]
            total_dup_loss = Decimal("0.00")
            dup_numbers = []
            for d in duplicates:
                total_dup_loss = money_add(total_dup_loss, to_decimal(_get_val(d, "total_amount", 0)))
                dup_numbers.append(_get_val(d, "invoice_number", f"INV-{_get_val(d, 'id')}"))

            primary_inv = inv_list[0]
            cust_id = _get_val(primary_inv, "customer_id")
            alerts.append(
                LeakageAlertResult(
                    leakage_type="duplicate_billing_attempt",
                    severity="critical",
                    estimated_loss=round_money(total_dup_loss),
                    subscription_id=sub_id,
                    invoice_id=_get_val(duplicates[0], "id"),
                    customer_id=cust_id,
                    description=(
                        f"Detected {len(inv_list)} duplicate invoices for subscription ID {sub_id} "
                        f"over billing period {p_start} to {p_end}. Duplicate invoices: {', '.join(dup_numbers)}."
                    ),
                    recommended_action=(
                        f"Immediately void or cancel duplicate invoice(s) {', '.join(dup_numbers)} "
                        "to prevent double-charging or merchant chargeback disputes."
                    ),
                    metadata={"duplicate_invoice_numbers": dup_numbers, "billing_period": f"{p_start} to {p_end}"},
                )
            )

    return alerts


def detect_expired_discounts(
    invoices: List[Any],
    discounts: Optional[List[Any]] = None,
) -> List[LeakageAlertResult]:
    """
    Detect invoices that applied discounts past their validity window or max redemption limit.
    """
    alerts: List[LeakageAlertResult] = []
    discount_lookup: Dict[Any, Any] = {}
    if discounts:
        for d in discounts:
            d_id = _get_val(d, "id")
            d_code = _get_val(d, "code")
            if d_id is not None:
                discount_lookup[d_id] = d
            if d_code:
                discount_lookup[d_code] = d

    for inv in invoices:
        discount_amount = to_decimal(_get_val(inv, "discount_amount", 0))
        if discount_amount <= Decimal("0.00"):
            continue

        inv_id = _get_val(inv, "id")
        inv_num = _get_val(inv, "invoice_number", f"INV-{inv_id}")
        cust_id = _get_val(inv, "customer_id")
        sub_id = _get_val(inv, "subscription_id")
        issue_date = _to_date(_get_val(inv, "issue_date"))
        disc_id = _get_val(inv, "discount_id")
        disc_obj = discount_lookup.get(disc_id) if disc_id else _get_val(inv, "discount")

        if disc_obj and issue_date:
            end_date = _to_date(_get_val(disc_obj, "end_date"))
            code = _get_val(disc_obj, "code", "UNKNOWN")
            is_active = _get_val(disc_obj, "is_active", True)
            redemption_count = int(_get_val(disc_obj, "redemption_count", 0) or 0)
            max_redemptions = _get_val(disc_obj, "max_redemptions")

            is_expired = end_date and issue_date > end_date
            is_exhausted = max_redemptions is not None and redemption_count > int(max_redemptions)

            if is_expired or not is_active or is_exhausted:
                reason = "expired" if is_expired else ("deactivated" if not is_active else "exhausted limit")
                alerts.append(
                    LeakageAlertResult(
                        leakage_type="expired_discount_applied",
                        severity="medium",
                        estimated_loss=round_money(discount_amount),
                        subscription_id=sub_id,
                        invoice_id=inv_id,
                        customer_id=cust_id,
                        description=(
                            f"Invoice {inv_num} applied a {reason} discount '{code}' (ID {disc_id}), "
                            f"resulting in unearned deduction of {discount_amount}."
                        ),
                        recommended_action=(
                            f"Revoke coupon '{code}' from customer subscription and update future renewal cycles."
                        ),
                        metadata={"discount_code": code, "discount_amount": float(discount_amount), "reason": reason},
                    )
                )

    return alerts


def detect_overdue_invoices(
    invoices: List[Any],
    as_of_date: Optional[date] = None,
    grace_period_days: int = 7,
) -> List[LeakageAlertResult]:
    """
    Detect outstanding overdue invoices with uncollected balances.
    """
    as_of = as_of_date or date.today()
    alerts: List[LeakageAlertResult] = []

    for inv in invoices:
        status = _get_val(inv, "status", "")
        if status in ("cancelled", "void", "paid"):
            continue

        due_date = _to_date(_get_val(inv, "due_date"))
        amount_due = to_decimal(_get_val(inv, "amount_due", 0))

        if due_date and due_date < as_of and amount_due > Decimal("0.00"):
            days_overdue = (as_of - due_date).days
            if days_overdue >= grace_period_days:
                inv_id = _get_val(inv, "id")
                inv_num = _get_val(inv, "invoice_number", f"INV-{inv_id}")
                cust_id = _get_val(inv, "customer_id")
                sub_id = _get_val(inv, "subscription_id")

                severity = "critical" if days_overdue > 30 else ("high" if days_overdue > 14 else "medium")
                alerts.append(
                    LeakageAlertResult(
                        leakage_type="overdue_uncollected",
                        severity=severity,
                        estimated_loss=round_money(amount_due),
                        subscription_id=sub_id,
                        invoice_id=inv_id,
                        customer_id=cust_id,
                        description=(
                            f"Invoice {inv_num} is past due by {days_overdue} days with an uncollected balance of {amount_due}."
                        ),
                        recommended_action=(
                            f"Trigger automated dunning reminder or smart collections outreach for invoice {inv_num}."
                        ),
                        metadata={"days_overdue": days_overdue, "amount_due": float(amount_due), "due_date": str(due_date)},
                    )
                )

    return alerts


def detect_missing_renewals(
    subscriptions: List[Any],
    as_of_date: Optional[date] = None,
) -> List[LeakageAlertResult]:
    """
    Detect auto-renewing subscriptions that passed period end without renewal progression.
    """
    as_of = as_of_date or date.today()
    alerts: List[LeakageAlertResult] = []

    for sub in subscriptions:
        status = _get_val(sub, "status", "")
        auto_renew = _get_val(sub, "auto_renew", True)
        if status != "active" or not auto_renew:
            continue

        period_end = _to_date(_get_val(sub, "current_period_end"))
        if period_end and period_end < as_of:
            days_past = (as_of - period_end).days
            sub_id = _get_val(sub, "id")
            sub_num = _get_val(sub, "subscription_number", f"SUB-{sub_id}")
            cust_id = _get_val(sub, "customer_id")
            unit_price = to_decimal(_get_val(sub, "unit_price", 0))
            quantity = Decimal(str(_get_val(sub, "quantity", 1)))
            loss = round_money(money_mul(unit_price, quantity))

            severity = "critical" if days_past > 14 else ("high" if days_past > 3 else "medium")
            alerts.append(
                LeakageAlertResult(
                    leakage_type="missing_renewal_invoice",
                    severity=severity,
                    estimated_loss=loss,
                    subscription_id=sub_id,
                    customer_id=cust_id,
                    description=(
                        f"Subscription {sub_num} current period ended on {period_end} ({days_past} days ago), "
                        "but renewal cycle has not advanced."
                    ),
                    recommended_action=(
                        f"Advance subscription {sub_num} cycle to the next active period and generate renewal invoice."
                    ),
                    metadata={"days_past_renewal": days_past, "period_end": str(period_end)},
                )
            )

    return alerts


def detect_payment_reconciliation_gaps(
    invoices: List[Any],
    payments: Optional[List[Any]] = None,
) -> List[LeakageAlertResult]:
    """
    Detect discrepancies between recorded invoice amounts and ledger payment receipts.
    """
    alerts: List[LeakageAlertResult] = []

    # Map successful payments by invoice_id
    successful_payments_by_inv: Dict[int, Decimal] = {}
    if payments:
        for p in payments:
            status = _get_val(p, "status", "")
            if status == "successful":
                inv_id = _get_val(p, "invoice_id")
                amt = to_decimal(_get_val(p, "amount", 0))
                if inv_id is not None:
                    successful_payments_by_inv[inv_id] = money_add(
                        successful_payments_by_inv.get(inv_id, Decimal("0.00")),
                        amt,
                    )

    for inv in invoices:
        inv_id = _get_val(inv, "id")
        inv_num = _get_val(inv, "invoice_number", f"INV-{inv_id}")
        cust_id = _get_val(inv, "customer_id")
        sub_id = _get_val(inv, "subscription_id")

        total_amount = to_decimal(_get_val(inv, "total_amount", 0))
        amount_paid = to_decimal(_get_val(inv, "amount_paid", 0))
        amount_due = to_decimal(_get_val(inv, "amount_due", 0))

        # 1. Internal arithmetic check: total_amount must equal amount_paid + amount_due
        expected_balance = money_add(amount_paid, amount_due)
        balance_gap = abs(money_sub(total_amount, expected_balance))
        if balance_gap > Decimal("0.01"):
            alerts.append(
                LeakageAlertResult(
                    leakage_type="billing_discrepancy",
                    severity="high",
                    estimated_loss=round_money(balance_gap),
                    subscription_id=sub_id,
                    invoice_id=inv_id,
                    customer_id=cust_id,
                    description=(
                        f"Invoice {inv_num} arithmetic discrepancy: total amount ({total_amount}) "
                        f"does not match amount paid ({amount_paid}) + amount due ({amount_due})."
                    ),
                    recommended_action=(
                        f"Recalculate and update ledger balances for invoice {inv_num}."
                    ),
                    metadata={"balance_gap": float(balance_gap), "total_amount": float(total_amount)},
                )
            )

        # 2. External payment receipts check: if payments list is provided
        if payments and inv_id in successful_payments_by_inv:
            recorded_total_paid = successful_payments_by_inv[inv_id]
            payment_gap = abs(money_sub(amount_paid, recorded_total_paid))
            if payment_gap > Decimal("0.01"):
                alerts.append(
                    LeakageAlertResult(
                        leakage_type="billing_discrepancy",
                        severity="high",
                        estimated_loss=round_money(payment_gap),
                        subscription_id=sub_id,
                        invoice_id=inv_id,
                        customer_id=cust_id,
                        description=(
                            f"Invoice {inv_num} payment reconciliation mismatch: invoice states amount paid is {amount_paid}, "
                            f"but recorded successful transactions sum to {recorded_total_paid}."
                        ),
                        recommended_action=(
                            f"Audit payment gateway receipts and adjust invoice {inv_num} amount_paid balance."
                        ),
                        metadata={"payment_gap": float(payment_gap), "recorded_paid": float(recorded_total_paid)},
                    )
                )

    return alerts


def detect_revenue_leakage(
    subscriptions: Optional[List[Any]] = None,
    invoices: Optional[List[Any]] = None,
    payments: Optional[List[Any]] = None,
    discounts: Optional[List[Any]] = None,
    as_of_date: Optional[date] = None,
) -> List[LeakageAlertResult]:
    """
    Comprehensive revenue leakage scan across all vectors.
    """
    subs = subscriptions or []
    invs = invoices or []
    pays = payments or []
    discs = discounts or []

    all_alerts: List[LeakageAlertResult] = []
    all_alerts.extend(detect_unbilled_subscriptions(subs, invs, as_of_date))
    all_alerts.extend(detect_duplicate_invoices(invs))
    all_alerts.extend(detect_expired_discounts(invs, discs))
    all_alerts.extend(detect_overdue_invoices(invs, as_of_date))
    all_alerts.extend(detect_missing_renewals(subs, as_of_date))
    all_alerts.extend(detect_payment_reconciliation_gaps(invs, pays))

    return all_alerts
