"""
Discount Calculation & Validation Engine for SubscriptIQ.

Provides pure, deterministic discount validation and application supporting:
- Percentage-based discounts (e.g. 20.00 means 20%).
- Fixed-amount discounts (e.g. $50.00 off).
- Maximum discount cap for percentage discounts.
- Minimum purchase amount and minimum quantity gating.
- Time-based eligibility (start date and end date).
- Global usage limit enforcement.
- Safe rejection handling without modifying persistent state.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional
from .money_utils import (
    to_decimal,
    round_money,
    calculate_percentage,
    ZERO_MONEY,
    MoneyType,
)


@dataclass(frozen=True)
class DiscountRuleInput:
    """
    Data input representation for a discount rule/coupon.

    Attributes:
        code: Unique promotion code (e.g. 'LAUNCH20').
        discount_type: 'percentage' or 'fixed_amount'.
        value: Numeric value (e.g. 20.00 for 20% or 50.00 for $50.00).
        currency: Optional ISO-4217 currency code (required for fixed_amount).
        min_purchase_amount: Minimum subtotal required to qualify.
        min_quantity: Minimum quantity of items/seats required to qualify.
        max_discount_amount: Maximum allowed discount ceiling for percentage discounts.
        start_date: Inclusive start date of promotion.
        end_date: Inclusive end date of promotion.
        max_uses: Maximum total redemptions permitted (None = unlimited).
        current_uses: Current redemption counter.
        is_active: Whether discount code is active.
        applicable_plan_id: Optional plan restriction.
    """
    code: str
    discount_type: str
    value: MoneyType
    currency: Optional[str] = None
    min_purchase_amount: MoneyType = Decimal("0.00")
    min_quantity: int = 1
    max_discount_amount: Optional[MoneyType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_uses: Optional[int] = None
    current_uses: int = 0
    is_active: bool = True
    applicable_plan_id: Optional[int] = None


@dataclass(frozen=True)
class DiscountApplicationResult:
    """
    Output result from evaluating and applying a discount rule.
    """
    is_valid: bool
    discount_code: str
    discount_type: str
    discount_amount: Decimal
    net_amount: Decimal
    rejection_reason: Optional[str] = None


def validate_and_apply_discount(
    base_amount: MoneyType,
    discount_rule: Optional[DiscountRuleInput],
    quantity: int = 1,
    evaluation_date: Optional[date] = None,
    plan_id: Optional[int] = None,
) -> DiscountApplicationResult:
    """
    Validate and apply a discount rule to a base monetary amount.

    Guarantees:
    - Never discounts more than base_amount (net_amount is never negative).
    - Preserves monetary rounding using ROUND_HALF_UP.
    - If discount is rejected, discount_amount is 0.00, net_amount equals base_amount,
      and a descriptive rejection_reason is returned.

    Parameters:
        base_amount: The pre-discount subtotal amount.
        discount_rule: Discount configuration to evaluate, or None.
        quantity: Item quantity or seat count being purchased.
        evaluation_date: Date to check against start_date/end_date (defaults to today).
        plan_id: Plan ID being purchased, to verify plan-specific discounts.

    Returns:
        DiscountApplicationResult with validity status and calculated amounts.

    Raises:
        ValueError: If base_amount or quantity are negative.
    """
    dec_base = to_decimal(base_amount)
    if dec_base < 0:
        raise ValueError(f"Base amount cannot be negative: {dec_base}")
    if quantity < 0:
        raise ValueError(f"Quantity cannot be negative: {quantity}")

    rounded_base = round_money(dec_base)

    # 1. No discount supplied
    if discount_rule is None:
        return DiscountApplicationResult(
            is_valid=True,
            discount_code="NONE",
            discount_type="none",
            discount_amount=ZERO_MONEY,
            net_amount=rounded_base,
            rejection_reason=None,
        )

    code = discount_rule.code.strip()
    d_type = discount_rule.discount_type.lower()
    curr_date = evaluation_date or date.today()

    def reject(reason: str) -> DiscountApplicationResult:
        return DiscountApplicationResult(
            is_valid=False,
            discount_code=code,
            discount_type=d_type,
            discount_amount=ZERO_MONEY,
            net_amount=rounded_base,
            rejection_reason=reason,
        )

    # 2. Validation Checks
    if not discount_rule.is_active:
        return reject("Discount code is inactive.")

    if discount_rule.start_date is not None and curr_date < discount_rule.start_date:
        return reject(f"Discount code has not started yet (starts {discount_rule.start_date}).")

    if discount_rule.end_date is not None and curr_date > discount_rule.end_date:
        return reject(f"Discount code expired on {discount_rule.end_date}.")

    if discount_rule.max_uses is not None and discount_rule.current_uses >= discount_rule.max_uses:
        return reject("Discount code has reached its maximum redemption limit.")

    if quantity < discount_rule.min_quantity:
        return reject(
            f"Minimum quantity requirement not met. Required: {discount_rule.min_quantity}, provided: {quantity}."
        )

    min_purchase = to_decimal(discount_rule.min_purchase_amount)
    if rounded_base < min_purchase:
        return reject(
            f"Minimum purchase amount not met. Required: {round_money(min_purchase)}, subtotal: {rounded_base}."
        )

    if discount_rule.applicable_plan_id is not None:
        if plan_id is None or plan_id != discount_rule.applicable_plan_id:
            return reject("Discount code is not applicable to the selected subscription plan.")

    # 3. Calculation of Discount Amount
    discount_val = to_decimal(discount_rule.value)
    if discount_val < 0:
        return reject("Discount value cannot be negative.")

    if d_type == "percentage":
        raw_discount = calculate_percentage(rounded_base, discount_val)
        # Apply cap if max_discount_amount is defined
        if discount_rule.max_discount_amount is not None:
            max_cap = to_decimal(discount_rule.max_discount_amount)
            if raw_discount > max_cap:
                raw_discount = round_money(max_cap)
        discount_amount = min(raw_discount, rounded_base)

    elif d_type == "fixed_amount":
        fixed_discount = round_money(discount_val)
        discount_amount = min(fixed_discount, rounded_base)

    else:
        return reject(f"Invalid discount_type: '{discount_rule.discount_type}'. Use 'percentage' or 'fixed_amount'.")

    net_amount = round_money(rounded_base - discount_amount)

    return DiscountApplicationResult(
        is_valid=True,
        discount_code=code,
        discount_type=d_type,
        discount_amount=discount_amount,
        net_amount=net_amount,
        rejection_reason=None,
    )
