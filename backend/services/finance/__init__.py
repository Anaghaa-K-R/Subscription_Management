"""
Finance Services Module - SubscriptIQ.

Includes:
- money_utils: High-precision Decimal monetary operations.
- tax_service: Deterministic tax engine with breakdown and exemption support.
- discount_service: Pure validation and application of discounts/coupons.
"""

from .money_utils import (
    to_decimal,
    round_money,
    money_add,
    money_sub,
    money_mul,
    money_div,
    calculate_percentage,
    ZERO_MONEY,
    MONEY_QUANTIZATION,
)
from .tax_service import (
    TaxRuleInput,
    TaxItemBreakdown,
    TaxCalculationResult,
    calculate_tax,
)
from .discount_service import (
    DiscountRuleInput,
    DiscountApplicationResult,
    validate_and_apply_discount,
)
from .analytics_service import (
    SubscriptionRecord,
    InvoiceRecord,
    PaymentRecord,
    MRRBreakdown,
    RevenueGrowthResult,
    PaymentAnalyticsResult,
    AgingBuckets,
    OutstandingRevenueResult,
    SubscriptionAnalyticsResult,
    MonthlyTrendPoint,
    ComprehensiveFinancialAnalytics,
    calculate_mrr,
    calculate_arr,
    calculate_revenue_growth,
    calculate_payment_analytics,
    calculate_outstanding_revenue,
    calculate_subscription_analytics,
    calculate_monthly_revenue_trends,
    calculate_comprehensive_analytics,
)

__all__ = [
    "to_decimal",
    "round_money",
    "money_add",
    "money_sub",
    "money_mul",
    "money_div",
    "calculate_percentage",
    "ZERO_MONEY",
    "MONEY_QUANTIZATION",
    "TaxRuleInput",
    "TaxItemBreakdown",
    "TaxCalculationResult",
    "calculate_tax",
    "DiscountRuleInput",
    "DiscountApplicationResult",
    "validate_and_apply_discount",
    "SubscriptionRecord",
    "InvoiceRecord",
    "PaymentRecord",
    "MRRBreakdown",
    "RevenueGrowthResult",
    "PaymentAnalyticsResult",
    "AgingBuckets",
    "OutstandingRevenueResult",
    "SubscriptionAnalyticsResult",
    "MonthlyTrendPoint",
    "ComprehensiveFinancialAnalytics",
    "calculate_mrr",
    "calculate_arr",
    "calculate_revenue_growth",
    "calculate_payment_analytics",
    "calculate_outstanding_revenue",
    "calculate_subscription_analytics",
    "calculate_monthly_revenue_trends",
    "calculate_comprehensive_analytics",
]

