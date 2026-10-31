# SubscriptIQ: Financial Analytics Engine

The `analytics_service` provides high-precision, database-independent revenue intelligence, recurring subscription metrics, payment health analytics, and time-series financial trends.

---

## 1. Core Analytics Metrics

| Metric | Business Definition | Formula / Logic |
| :--- | :--- | :--- |
| **Monthly Recurring Revenue (MRR)** | Normalized predictable monthly subscription revenue from all active customers. | Weekly: `((Price * Qty - Disc) * 52) / 12`<br>Monthly: `Price * Qty - Disc`<br>Yearly: `(Price * Qty - Disc) / 12` |
| **Annual Recurring Revenue (ARR)** | Annualized run-rate of recurring subscription contracts. | `ARR = MRR * 12` |
| **Revenue Growth** | Period-over-period percentage growth in recognized revenue. | `((Current - Previous) / Previous) * 100`<br>*(Safely handles zero prior baseline)* |
| **Payment Success Rate** | Ratio of completed transactions vs total payment attempts. | `(Successful Payments / Total Payments) * 100` |
| **Accounts Receivable Aging** | Classification of overdue invoice balances across standard aging cohorts. | Buckets: `Current`, `1-30 Days`, `31-60 Days`, `61-90 Days`, `90+ Days` |
| **Subscription Churn Rate** | Percentage of customer cancellations relative to the subscriber base. | `(Cancelled / (Active + Cancelled)) * 100` |
| **Average Revenue Per User (ARPU)** | Average recurring revenue generated per active subscription. | `MRR / Active Subscriptions` |
| **Monthly Revenue Trends** | Time-series monthly revenue and Month-over-Month (MoM) growth rates. | Chronologically aggregated by `YYYY-MM` with MoM percentage change. |

---

## 2. Input Data Structures

The engine accepts either Python dataclasses (`SubscriptionRecord`, `InvoiceRecord`, `PaymentRecord`) or plain Python dictionaries.

```python
from datetime import date
from decimal import Decimal
from backend.services.finance.analytics_service import (
    SubscriptionRecord,
    InvoiceRecord,
    PaymentRecord,
)

# 1. Subscription Contracts
subscriptions = [
    SubscriptionRecord(
        id=1,
        customer_id=101,
        unit_price=Decimal("100.00"),
        quantity=1,
        billing_interval="monthly",
        status="active",
        discount_amount=Decimal("10.00"),
    ),
    SubscriptionRecord(
        id=2,
        customer_id=102,
        unit_price=Decimal("1200.00"),
        quantity=1,
        billing_interval="yearly",
        status="active",
    ),
    SubscriptionRecord(
        id=3,
        customer_id=103,
        unit_price=Decimal("25.00"),
        quantity=2,
        billing_interval="weekly",
        status="active",
    ),
]

# 2. Invoices (for Accounts Receivable & Aging)
invoices = [
    InvoiceRecord(
        id=1001,
        customer_id=101,
        total_amount=Decimal("90.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("90.00"),
        status="issued",
        due_date=date(2026, 11, 20),
    ),
    InvoiceRecord(
        id=1002,
        customer_id=102,
        total_amount=Decimal("1200.00"),
        amount_paid=Decimal("0.00"),
        amount_due=Decimal("1200.00"),
        status="overdue",
        due_date=date(2026, 10, 15),
    ),
]

# 3. Payments (for Settlement & Cashflow Analytics)
payments = [
    PaymentRecord(
        id=501,
        amount=Decimal("90.00"),
        status="successful",
        payment_date=date(2026, 11, 1),
    ),
    PaymentRecord(
        id=502,
        amount=Decimal("1200.00"),
        status="failed",
        payment_date=date(2026, 11, 2),
    ),
]
```

---

## 3. Example Usage

```python
from backend.services.finance.analytics_service import (
    calculate_mrr,
    calculate_arr,
    calculate_outstanding_revenue,
    calculate_payment_analytics,
    calculate_subscription_analytics,
    calculate_monthly_revenue_trends,
    calculate_comprehensive_analytics,
)

# A. Calculate MRR & ARR
mrr_summary = calculate_mrr(subscriptions)
print(f"Total MRR: ${mrr_summary.total_mrr}")
# Total MRR: $406.67 (Monthly: $90.00 + Yearly: $100.00 + Weekly: $216.67)

arr = calculate_arr(mrr_summary)
print(f"Annual Run-Rate (ARR): ${arr}")
# Annual Run-Rate (ARR): $4,880.04

# B. Accounts Receivable Aging
ar_summary = calculate_outstanding_revenue(invoices, evaluation_date=date(2026, 11, 1))
print(f"Total Outstanding: ${ar_summary.total_outstanding}")
print(f"Overdue (1-30 Days): ${ar_summary.aging_buckets.days_1_to_30}")

# C. Consolidated Executive Dashboard Payload
dashboard = calculate_comprehensive_analytics(subscriptions, invoices, payments)
```

---

## 4. FastAPI Integration Blueprint

When Member 2 completes database session management, the analytics service plugs into FastAPI endpoints with zero database refactoring:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_user
from backend.models import Subscription, Invoice, Payment
from backend.services.finance.analytics_service import (
    calculate_comprehensive_analytics,
    SubscriptionRecord,
    InvoiceRecord,
    PaymentRecord,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["Financial Analytics"])

@router.get("/dashboard")
def get_executive_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # 1. Query raw records from DB
    subs_db = db.query(Subscription).all()
    invs_db = db.query(Invoice).all()
    pays_db = db.query(Payment).all()

    # 2. Map ORM models to lightweight analytics records
    subs = [
        SubscriptionRecord(
            id=s.id,
            customer_id=s.customer_id,
            unit_price=s.unit_price,
            quantity=s.quantity,
            billing_interval=s.billing_interval,
            status=s.status,
            discount_amount=getattr(s, "discount_amount", 0),
        )
        for s in subs_db
    ]

    invs = [
        InvoiceRecord(
            id=i.id,
            customer_id=i.customer_id,
            total_amount=i.total_amount,
            amount_paid=i.amount_paid,
            amount_due=i.amount_due,
            status=i.status,
            due_date=i.due_date,
        )
        for i in invs_db
    ]

    pays = [
        PaymentRecord(
            id=p.id,
            amount=p.amount,
            status=p.status,
            payment_date=p.payment_date,
        )
        for p in pays_db
    ]

    # 3. Compute analytics deterministically
    analytics = calculate_comprehensive_analytics(subs, invs, pays)
    return analytics
```

---

## 5. Frontend Visual Dashboard Consumption (Recharts)

The output format is directly tailored for React chart libraries such as **Recharts**:

### Monthly Revenue Trend Chart:
```tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

function RevenueTrendChart({ data }: { data: MonthlyTrendPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <XAxis dataKey="month" stroke="#64748B" />
        <YAxis stroke="#64748B" />
        <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
        <Line type="monotone" dataKey="revenue" stroke="#007BA7" strokeWidth={2} dot />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### Aging Buckets Bar Chart:
```tsx
const agingData = [
  { bucket: 'Current', amount: dashboard.outstanding_revenue.aging_buckets.current_not_due },
  { bucket: '1-30 Days', amount: dashboard.outstanding_revenue.aging_buckets.days_1_to_30 },
  { bucket: '31-60 Days', amount: dashboard.outstanding_revenue.aging_buckets.days_31_to_60 },
  { bucket: '61-90 Days', amount: dashboard.outstanding_revenue.aging_buckets.days_61_to_90 },
  { bucket: '90+ Days', amount: dashboard.outstanding_revenue.aging_buckets.days_90_plus },
];
```
