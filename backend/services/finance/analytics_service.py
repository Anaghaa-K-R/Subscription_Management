"""
Financial Analytics Engine for SubscriptIQ.

Provides pure, database-independent financial business intelligence and reporting:
1. Monthly Recurring Revenue (MRR) with multi-frequency normalization (weekly, monthly, yearly).
2. Annual Recurring Revenue (ARR).
3. Revenue Growth (Period-over-Period) with safe zero-baseline handling.
4. Payment Analytics (Success rate, failed volume, pending reconciliation).
5. Outstanding Revenue & Aging Analysis (Current vs Overdue aging cohorts: 1-30, 31-60, 61-90, 90+ days).
6. Subscription Lifecycle & Churn Metrics (Active, cancelled, churn rate, ARPU).
7. Monthly Revenue Trends (Structured for frontend visual dashboards like Recharts).

All calculations strictly use Python's Decimal with ROUND_HALF_UP to preserve
currency precision.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from backend.services.finance.money_utils import (
    ONE_HUNDRED,
    ZERO_MONEY,
    MoneyType,
    money_add,
    money_div,
    money_mul,
    money_sub,
    round_money,
    to_decimal,
)


# ==============================================================================
# INPUT DATA STRUCTURES (Dataclasses accepting dicts or typed objects)
# ==============================================================================

@dataclass
class SubscriptionRecord:
    """Represents a subscription contract for analytical aggregation."""
    id: Union[int, str]
    customer_id: Union[int, str]
    unit_price: MoneyType
    quantity: int = 1
    billing_interval: str = "monthly"  # "weekly", "monthly", "yearly"
    status: str = "active"             # "active", "cancelled", "paused", "draft", "closed"
    discount_amount: MoneyType = Decimal("0.00")
    start_date: Optional[date] = None
    cancellation_date: Optional[date] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubscriptionRecord":
        return cls(
            id=data.get("id", ""),
            customer_id=data.get("customer_id", ""),
            unit_price=data.get("unit_price", Decimal("0.00")),
            quantity=int(data.get("quantity", 1)),
            billing_interval=str(data.get("billing_interval", "monthly")),
            status=str(data.get("status", "active")),
            discount_amount=data.get("discount_amount", Decimal("0.00")),
            start_date=data.get("start_date"),
            cancellation_date=data.get("cancellation_date"),
        )


@dataclass
class InvoiceRecord:
    """Represents an invoice for outstanding balance and revenue aging analysis."""
    id: Union[int, str]
    customer_id: Union[int, str]
    total_amount: MoneyType
    amount_paid: MoneyType = Decimal("0.00")
    amount_due: Optional[MoneyType] = None
    status: str = "issued"  # "draft", "issued", "partially_paid", "paid", "overdue", "cancelled", "void"
    issue_date: Optional[date] = None
    due_date: Optional[date] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvoiceRecord":
        return cls(
            id=data.get("id", ""),
            customer_id=data.get("customer_id", ""),
            total_amount=data.get("total_amount", Decimal("0.00")),
            amount_paid=data.get("amount_paid", Decimal("0.00")),
            amount_due=data.get("amount_due"),
            status=str(data.get("status", "issued")),
            issue_date=data.get("issue_date"),
            due_date=data.get("due_date"),
        )


@dataclass
class PaymentRecord:
    """Represents a payment transaction for success rate and cashflow tracking."""
    id: Union[int, str]
    amount: MoneyType
    status: str = "successful"  # "successful", "pending", "failed", "refunded"
    payment_date: Optional[Union[date, datetime]] = None
    payment_method: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PaymentRecord":
        return cls(
            id=data.get("id", ""),
            amount=data.get("amount", Decimal("0.00")),
            status=str(data.get("status", "successful")),
            payment_date=data.get("payment_date"),
            payment_method=data.get("payment_method"),
        )


# ==============================================================================
# OUTPUT ANALYTICAL RESULTS
# ==============================================================================

@dataclass(frozen=True)
class MRRBreakdown:
    """Monthly Recurring Revenue analytical summary."""
    total_mrr: Decimal
    active_subscriptions_count: int
    weekly_contributed_mrr: Decimal
    monthly_contributed_mrr: Decimal
    yearly_contributed_mrr: Decimal
    total_discounts_deducted: Decimal


@dataclass(frozen=True)
class RevenueGrowthResult:
    """Period-over-period revenue growth comparison."""
    current_period_revenue: Decimal
    previous_period_revenue: Decimal
    net_change: Decimal
    growth_rate_percentage: Decimal
    is_growth_positive: bool


@dataclass(frozen=True)
class PaymentAnalyticsResult:
    """Comprehensive payment settlement health."""
    total_volume: Decimal
    successful_volume: Decimal
    pending_volume: Decimal
    failed_volume: Decimal
    refunded_volume: Decimal
    successful_count: int
    pending_count: int
    failed_count: int
    refunded_count: int
    total_count: int
    success_rate_percentage: Decimal
    failure_rate_percentage: Decimal


@dataclass(frozen=True)
class AgingBuckets:
    """Aging breakdown for overdue accounts receivable."""
    current_not_due: Decimal = Decimal("0.00")
    days_1_to_30: Decimal = Decimal("0.00")
    days_31_to_60: Decimal = Decimal("0.00")
    days_61_to_90: Decimal = Decimal("0.00")
    days_90_plus: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class OutstandingRevenueResult:
    """Accounts receivable and overdue analysis."""
    total_outstanding: Decimal
    overdue_amount: Decimal
    current_due_amount: Decimal
    overdue_invoices_count: int
    current_invoices_count: int
    total_unpaid_invoices_count: int
    aging_buckets: AgingBuckets = field(default_factory=AgingBuckets)


@dataclass(frozen=True)
class SubscriptionAnalyticsResult:
    """Subscription lifecycle counts, churn rate, and ARPU."""
    active_count: int
    cancelled_count: int
    paused_count: int
    draft_count: int
    total_count: int
    churn_rate_percentage: Decimal
    arpu: Decimal  # Average Revenue Per User/Subscription (MRR / active_count)


@dataclass(frozen=True)
class MonthlyTrendPoint:
    """Single point in a time-series monthly revenue trend."""
    month: str  # "YYYY-MM"
    revenue: Decimal
    transaction_count: int
    growth_rate_mom: Optional[Decimal] = None


@dataclass(frozen=True)
class ComprehensiveFinancialAnalytics:
    """Unified executive financial dashboard payload."""
    mrr_summary: MRRBreakdown
    arr: Decimal
    payment_analytics: PaymentAnalyticsResult
    outstanding_revenue: OutstandingRevenueResult
    subscription_analytics: SubscriptionAnalyticsResult
    monthly_trends: List[MonthlyTrendPoint]


# ==============================================================================
# NORMALIZATION HELPERS
# ==============================================================================

WEEKS_IN_YEAR = Decimal("52")
MONTHS_IN_YEAR = Decimal("12")


def _normalize_subscription(sub: Union[SubscriptionRecord, Dict[str, Any]]) -> SubscriptionRecord:
    """Ensure subscription record is standardized."""
    if isinstance(sub, dict):
        return SubscriptionRecord.from_dict(sub)
    return sub


def _normalize_invoice(inv: Union[InvoiceRecord, Dict[str, Any]]) -> InvoiceRecord:
    """Ensure invoice record is standardized."""
    if isinstance(inv, dict):
        return InvoiceRecord.from_dict(inv)
    return inv


def _normalize_payment(pay: Union[PaymentRecord, Dict[str, Any]]) -> PaymentRecord:
    """Ensure payment record is standardized."""
    if isinstance(pay, dict):
        return PaymentRecord.from_dict(pay)
    return pay


# ==============================================================================
# CORE ANALYTICAL FUNCTIONS
# ==============================================================================

def calculate_mrr(
    subscriptions: List[Union[SubscriptionRecord, Dict[str, Any]]],
    active_statuses: Optional[List[str]] = None,
) -> MRRBreakdown:
    """
    Calculate Monthly Recurring Revenue (MRR) normalized across billing frequencies.

    Frequency Normalization Formulas:
    - Monthly: (unit_price * quantity) - discount
    - Weekly:  [((unit_price * quantity) - discount) * 52] / 12
    - Yearly:  [((unit_price * quantity) - discount)] / 12

    Filtering Rules:
    - Excludes non-active subscriptions (cancelled, draft, paused, closed).
    - Capped at >= 0.00 (discounts cannot make recurring revenue negative).

    Parameters:
        subscriptions: List of subscription records or dicts.
        active_statuses: Allowed status strings (default: ['active']).

    Returns:
        MRRBreakdown with total MRR and frequency contributions.
    """
    valid_statuses = [s.lower().strip() for s in (active_statuses or ["active"])]

    total_mrr = ZERO_MONEY
    weekly_mrr = ZERO_MONEY
    monthly_mrr = ZERO_MONEY
    yearly_mrr = ZERO_MONEY
    total_discounts = ZERO_MONEY
    active_count = 0

    for raw_sub in subscriptions:
        sub = _normalize_subscription(raw_sub)
        status = str(sub.status).lower().strip()

        if status not in valid_statuses:
            continue

        price = to_decimal(sub.unit_price)
        qty = to_decimal(sub.quantity)
        disc = to_decimal(sub.discount_amount)

        if price < 0 or qty <= 0 or disc < 0:
            continue

        gross_recurring = price * qty
        net_recurring = max(ZERO_MONEY, gross_recurring - disc)
        interval = str(sub.billing_interval).lower().strip()

        if interval == "weekly":
            # (Weekly * 52) / 12
            normalized = (net_recurring * WEEKS_IN_YEAR) / MONTHS_IN_YEAR
            normalized_disc = (disc * WEEKS_IN_YEAR) / MONTHS_IN_YEAR
            weekly_mrr += normalized

        elif interval == "yearly":
            # Yearly / 12
            normalized = net_recurring / MONTHS_IN_YEAR
            normalized_disc = disc / MONTHS_IN_YEAR
            yearly_mrr += normalized

        else:
            # Default is monthly
            normalized = net_recurring
            normalized_disc = disc
            monthly_mrr += normalized

        total_mrr += normalized
        total_discounts += normalized_disc
        active_count += 1

    return MRRBreakdown(
        total_mrr=round_money(total_mrr),
        active_subscriptions_count=active_count,
        weekly_contributed_mrr=round_money(weekly_mrr),
        monthly_contributed_mrr=round_money(monthly_mrr),
        yearly_contributed_mrr=round_money(yearly_mrr),
        total_discounts_deducted=round_money(total_discounts),
    )


def calculate_arr(
    subscriptions_or_mrr: Union[List[Union[SubscriptionRecord, Dict[str, Any]]], MRRBreakdown, MoneyType]
) -> Decimal:
    """
    Calculate Annual Recurring Revenue (ARR) from normalized MRR.

    Formula:
        ARR = MRR * 12

    Parameters:
        subscriptions_or_mrr: List of subscriptions, MRRBreakdown, or direct MRR amount.

    Returns:
        Annual Recurring Revenue as Decimal rounded to 2 places.
    """
    if isinstance(subscriptions_or_mrr, MRRBreakdown):
        mrr_val = subscriptions_or_mrr.total_mrr
    elif isinstance(subscriptions_or_mrr, (list, tuple)):
        mrr_val = calculate_mrr(subscriptions_or_mrr).total_mrr
    else:
        mrr_val = to_decimal(subscriptions_or_mrr)

    return round_money(mrr_val * MONTHS_IN_YEAR)


def calculate_revenue_growth(
    current_period_revenue: MoneyType,
    previous_period_revenue: MoneyType,
) -> RevenueGrowthResult:
    """
    Calculate period-over-period percentage revenue growth safely.

    Formula:
        Growth % = ((Current - Previous) / Previous) * 100

    Zero-Baseline Handling:
    - If previous == 0 and current > 0: +100.00% growth.
    - If previous == 0 and current == 0: 0.00% growth.
    - If previous == 0 and current < 0: -100.00% growth.

    Returns:
        RevenueGrowthResult with net change and growth percentage.
    """
    curr = round_money(to_decimal(current_period_revenue))
    prev = round_money(to_decimal(previous_period_revenue))
    net_change = curr - prev

    if prev == 0:
        if curr > 0:
            growth_rate = Decimal("100.00")
        elif curr < 0:
            growth_rate = Decimal("-100.00")
        else:
            growth_rate = ZERO_MONEY
    else:
        growth_rate = round_money((net_change / abs(prev)) * ONE_HUNDRED)

    return RevenueGrowthResult(
        current_period_revenue=curr,
        previous_period_revenue=prev,
        net_change=net_change,
        growth_rate_percentage=growth_rate,
        is_growth_positive=(net_change >= 0),
    )


def calculate_payment_analytics(
    payments: List[Union[PaymentRecord, Dict[str, Any]]]
) -> PaymentAnalyticsResult:
    """
    Analyze payment transaction volume, completion rates, and failure statistics.

    Parameters:
        payments: List of PaymentRecord objects or dictionaries.

    Returns:
        PaymentAnalyticsResult with status counts, volumes, and success rate.
    """
    success_vol = ZERO_MONEY
    pending_vol = ZERO_MONEY
    failed_vol = ZERO_MONEY
    refunded_vol = ZERO_MONEY

    success_cnt = 0
    pending_cnt = 0
    failed_cnt = 0
    refunded_cnt = 0

    for raw_p in payments:
        p = _normalize_payment(raw_p)
        status = str(p.status).lower().strip()
        amt = round_money(to_decimal(p.amount))

        if amt < 0:
            continue

        if status == "successful":
            success_vol += amt
            success_cnt += 1
        elif status == "pending":
            pending_vol += amt
            pending_cnt += 1
        elif status == "failed":
            failed_vol += amt
            failed_cnt += 1
        elif status == "refunded":
            refunded_vol += amt
            refunded_cnt += 1

    total_cnt = success_cnt + pending_cnt + failed_cnt + refunded_cnt
    total_vol = success_vol + pending_vol + failed_vol + refunded_vol

    if total_cnt > 0:
        success_rate = round_money((Decimal(success_cnt) / Decimal(total_cnt)) * ONE_HUNDRED)
        failure_rate = round_money((Decimal(failed_cnt) / Decimal(total_cnt)) * ONE_HUNDRED)
    else:
        success_rate = ZERO_MONEY
        failure_rate = ZERO_MONEY

    return PaymentAnalyticsResult(
        total_volume=total_vol,
        successful_volume=success_vol,
        pending_volume=pending_vol,
        failed_volume=failed_vol,
        refunded_volume=refunded_vol,
        successful_count=success_cnt,
        pending_count=pending_cnt,
        failed_count=failed_cnt,
        refunded_count=refunded_cnt,
        total_count=total_cnt,
        success_rate_percentage=success_rate,
        failure_rate_percentage=failure_rate,
    )


def calculate_outstanding_revenue(
    invoices: List[Union[InvoiceRecord, Dict[str, Any]]],
    evaluation_date: Optional[date] = None,
) -> OutstandingRevenueResult:
    """
    Calculate accounts receivable, separating current vs overdue balances and
    classifying into standard aging cohorts (1-30, 31-60, 61-90, 90+ days).

    Excluded Statuses: 'paid', 'cancelled', 'void', 'draft'.
    Active Unpaid Statuses: 'issued', 'partially_paid', 'overdue'.

    Parameters:
        invoices: List of InvoiceRecord objects or dictionaries.
        evaluation_date: Base reference date (defaults to date.today()).

    Returns:
        OutstandingRevenueResult with total outstanding, overdue, and aging cohorts.
    """
    eval_date = evaluation_date or date.today()
    unpaid_statuses = {"issued", "partially_paid", "overdue"}

    total_outstanding = ZERO_MONEY
    overdue_amount = ZERO_MONEY
    current_due_amount = ZERO_MONEY

    overdue_count = 0
    current_count = 0

    bucket_current = ZERO_MONEY
    bucket_1_30 = ZERO_MONEY
    bucket_31_60 = ZERO_MONEY
    bucket_61_90 = ZERO_MONEY
    bucket_90_plus = ZERO_MONEY

    for raw_inv in invoices:
        inv = _normalize_invoice(raw_inv)
        status = str(inv.status).lower().strip()

        if status not in unpaid_statuses:
            continue

        tot = to_decimal(inv.total_amount)
        paid = to_decimal(inv.amount_paid)

        if inv.amount_due is not None:
            due = to_decimal(inv.amount_due)
        else:
            due = max(ZERO_MONEY, tot - paid)

        due = round_money(due)
        if due <= 0:
            continue

        total_outstanding += due

        # Check due date
        due_d = inv.due_date
        if due_d is not None and due_d < eval_date:
            # Overdue
            overdue_amount += due
            overdue_count += 1
            days_overdue = (eval_date - due_d).days

            if days_overdue <= 30:
                bucket_1_30 += due
            elif days_overdue <= 60:
                bucket_31_60 += due
            elif days_overdue <= 90:
                bucket_61_90 += due
            else:
                bucket_90_plus += due
        else:
            # Current / Not Yet Due
            current_due_amount += due
            current_count += 1
            bucket_current += due

    aging = AgingBuckets(
        current_not_due=bucket_current,
        days_1_to_30=bucket_1_30,
        days_31_to_60=bucket_31_60,
        days_61_to_90=bucket_61_90,
        days_90_plus=bucket_90_plus,
    )

    return OutstandingRevenueResult(
        total_outstanding=total_outstanding,
        overdue_amount=overdue_amount,
        current_due_amount=current_due_amount,
        overdue_invoices_count=overdue_count,
        current_invoices_count=current_count,
        total_unpaid_invoices_count=overdue_count + current_count,
        aging_buckets=aging,
    )


def calculate_subscription_analytics(
    subscriptions: List[Union[SubscriptionRecord, Dict[str, Any]]],
    mrr_override: Optional[Decimal] = None,
) -> SubscriptionAnalyticsResult:
    """
    Calculate customer subscription counts, churn rate, and ARPU.

    Churn Rate Formula:
        (Cancelled / (Active + Cancelled)) * 100

    ARPU (Average Revenue Per Unit/Subscription):
        MRR / Active Subscriptions

    Parameters:
        subscriptions: List of SubscriptionRecord objects or dicts.
        mrr_override: Pre-computed MRR if already available.

    Returns:
        SubscriptionAnalyticsResult.
    """
    active_cnt = 0
    cancelled_cnt = 0
    paused_cnt = 0
    draft_cnt = 0
    total_cnt = 0

    for raw_sub in subscriptions:
        sub = _normalize_subscription(raw_sub)
        status = str(sub.status).lower().strip()
        total_cnt += 1

        if status == "active":
            active_cnt += 1
        elif status in ("cancelled", "closed"):
            cancelled_cnt += 1
        elif status == "paused":
            paused_cnt += 1
        elif status in ("draft", "quotation"):
            draft_cnt += 1

    # Churn rate
    denominator = active_cnt + cancelled_cnt
    if denominator > 0:
        churn_rate = round_money((Decimal(cancelled_cnt) / Decimal(denominator)) * ONE_HUNDRED)
    else:
        churn_rate = ZERO_MONEY

    # ARPU
    mrr_val = mrr_override if mrr_override is not None else calculate_mrr(subscriptions).total_mrr
    if active_cnt > 0:
        arpu = round_money(mrr_val / Decimal(active_cnt))
    else:
        arpu = ZERO_MONEY

    return SubscriptionAnalyticsResult(
        active_count=active_cnt,
        cancelled_count=cancelled_cnt,
        paused_count=paused_cnt,
        draft_count=draft_cnt,
        total_count=total_cnt,
        churn_rate_percentage=churn_rate,
        arpu=arpu,
    )


def calculate_monthly_revenue_trends(
    records: List[Union[PaymentRecord, InvoiceRecord, Dict[str, Any]]],
    date_field: str = "date",
    amount_field: str = "amount",
) -> List[MonthlyTrendPoint]:
    """
    Group financial transactions chronologically by month (YYYY-MM) and calculate
    month-over-month (MoM) revenue growth trends for dashboard visual charts.

    Parameters:
        records: List of payment or invoice objects/dicts.
        date_field: Property/key containing transaction date.
        amount_field: Property/key containing monetary value.

    Returns:
        List of MonthlyTrendPoint objects sorted chronologically.
    """
    monthly_data: Dict[str, Dict[str, Any]] = {}

    for raw_r in records:
        # Extract object or dict attribute
        if isinstance(raw_r, dict):
            d_val = raw_r.get(date_field) or raw_r.get("payment_date") or raw_r.get("issue_date")
            amt_val = raw_r.get(amount_field) or raw_r.get("amount") or raw_r.get("total_amount", 0)
            status_val = raw_r.get("status", "successful")
        else:
            d_val = getattr(raw_r, date_field, None) or getattr(raw_r, "payment_date", None) or getattr(raw_r, "issue_date", None)
            amt_val = getattr(raw_r, amount_field, None) or getattr(raw_r, "amount", None) or getattr(raw_r, "total_amount", 0)
            status_val = getattr(raw_r, "status", "successful")

        # Skip failed, void, or cancelled records
        if str(status_val).lower().strip() in ("failed", "cancelled", "void"):
            continue

        if d_val is None:
            continue

        if isinstance(d_val, datetime):
            d_obj = d_val.date()
        elif isinstance(d_val, date):
            d_obj = d_val
        elif isinstance(d_val, str):
            try:
                d_obj = datetime.fromisoformat(d_val.split("T")[0]).date()
            except ValueError:
                continue
        else:
            continue

        month_key = f"{d_obj.year:04d}-{d_obj.month:02d}"
        amt = round_money(to_decimal(amt_val))

        if month_key not in monthly_data:
            monthly_data[month_key] = {"revenue": ZERO_MONEY, "count": 0}

        monthly_data[month_key]["revenue"] += amt
        monthly_data[month_key]["count"] += 1

    # Sort chronologically by month key
    sorted_months = sorted(monthly_data.keys())
    trend_points: List[MonthlyTrendPoint] = []
    prev_rev: Optional[Decimal] = None

    for m in sorted_months:
        rev = monthly_data[m]["revenue"]
        cnt = monthly_data[m]["count"]

        if prev_rev is not None:
            growth_calc = calculate_revenue_growth(rev, prev_rev)
            mom = growth_calc.growth_rate_percentage
        else:
            mom = None

        trend_points.append(
            MonthlyTrendPoint(
                month=m,
                revenue=round_money(rev),
                transaction_count=cnt,
                growth_rate_mom=mom,
            )
        )
        prev_rev = rev

    return trend_points


def calculate_comprehensive_analytics(
    subscriptions: List[Union[SubscriptionRecord, Dict[str, Any]]],
    invoices: List[Union[InvoiceRecord, Dict[str, Any]]],
    payments: List[Union[PaymentRecord, Dict[str, Any]]],
    evaluation_date: Optional[date] = None,
) -> ComprehensiveFinancialAnalytics:
    """
    Produce a complete, consolidated executive financial intelligence summary in one call.
    """
    mrr_res = calculate_mrr(subscriptions)
    arr_res = calculate_arr(mrr_res)
    pay_res = calculate_payment_analytics(payments)
    out_res = calculate_outstanding_revenue(invoices, evaluation_date=evaluation_date)
    sub_res = calculate_subscription_analytics(subscriptions, mrr_override=mrr_res.total_mrr)
    trend_res = calculate_monthly_revenue_trends(payments)

    return ComprehensiveFinancialAnalytics(
        mrr_summary=mrr_res,
        arr=arr_res,
        payment_analytics=pay_res,
        outstanding_revenue=out_res,
        subscription_analytics=sub_res,
        monthly_trends=trend_res,
    )
