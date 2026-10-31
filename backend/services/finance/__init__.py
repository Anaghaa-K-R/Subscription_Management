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
]
