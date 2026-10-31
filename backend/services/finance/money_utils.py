"""
Money Utilities Module for SubscriptIQ.

Strictly provides Decimal-based financial operations using the ROUND_HALF_UP
quantization strategy. Floats are never used internally to guarantee zero
floating-point precision loss across billing and invoicing calculations.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union, Iterable, Optional

# Standard financial quantization constants
MONEY_QUANTIZATION = Decimal("0.01")
RATE_QUANTIZATION = Decimal("0.0001")
ZERO_MONEY = Decimal("0.00")
ONE_HUNDRED = Decimal("100.00")

MoneyType = Union[Decimal, int, str, float]


def to_decimal(value: Optional[MoneyType]) -> Decimal:
    """
    Safely convert an integer, string, float, or Decimal into a high-precision Decimal.

    Parameters:
        value: The numerical input to convert.

    Returns:
        Decimal representation of the input.

    Raises:
        ValueError: If value is None or cannot be parsed as a valid numerical Decimal.
    """
    if value is None:
        raise ValueError("Cannot convert None to Decimal.")

    if isinstance(value, Decimal):
        return value

    if isinstance(value, float):
        # Convert via str to prevent binary floating-point representation artifacts
        return Decimal(str(value))

    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, TypeError, AttributeError) as exc:
        raise ValueError(f"Invalid monetary value: '{value}'") from exc


def round_money(amount: MoneyType, places: int = 2) -> Decimal:
    """
    Round a monetary amount to the specified number of decimal places using ROUND_HALF_UP.

    Standard financial rounding:
    - 2.555 -> 2.56
    - 2.554 -> 2.55

    Parameters:
        amount: The monetary value to round.
        places: Number of decimal places (default is 2).

    Returns:
        Quantized Decimal.
    """
    dec_val = to_decimal(amount)
    quantizer = Decimal(10) ** -places
    return dec_val.quantize(quantizer, rounding=ROUND_HALF_UP)


def money_add(*amounts: MoneyType) -> Decimal:
    """
    Safely compute the sum of one or more monetary amounts, rounded to 2 decimal places.

    Returns:
        Decimal sum quantized to 2 decimal places.
    """
    if not amounts:
        return ZERO_MONEY

    total = sum((to_decimal(a) for a in amounts), Decimal("0.00"))
    return round_money(total)


def money_sub(minuend: MoneyType, subtrahend: MoneyType) -> Decimal:
    """
    Safely compute (minuend - subtrahend) rounded to 2 decimal places.

    Parameters:
        minuend: Base value.
        subtrahend: Value to subtract.

    Returns:
        Difference as Decimal rounded to 2 decimal places.
    """
    diff = to_decimal(minuend) - to_decimal(subtrahend)
    return round_money(diff)


def money_mul(amount: MoneyType, factor: MoneyType, round_result: bool = True) -> Decimal:
    """
    Safely compute (amount * factor).

    Parameters:
        amount: Base monetary value.
        factor: Multiplier (e.g. quantity or tax factor).
        round_result: If True, round result to 2 decimal places.

    Returns:
        Product as Decimal.
    """
    product = to_decimal(amount) * to_decimal(factor)
    return round_money(product) if round_result else product


def money_div(amount: MoneyType, divisor: MoneyType, round_result: bool = True) -> Decimal:
    """
    Safely compute (amount / divisor).

    Parameters:
        amount: Numerator.
        divisor: Denominator.
        round_result: If True, round result to 2 decimal places.

    Returns:
        Quotient as Decimal.

    Raises:
        ZeroDivisionError: If divisor equals zero.
    """
    dec_div = to_decimal(divisor)
    if dec_div == 0:
        raise ZeroDivisionError("Monetary division by zero.")

    quotient = to_decimal(amount) / dec_div
    return round_money(quotient) if round_result else quotient


def calculate_percentage(
    base_amount: MoneyType,
    percentage_rate: MoneyType,
    round_result: bool = True,
) -> Decimal:
    """
    Calculate the percentage value of a base amount.

    Consistent Convention:
    percentage_rate represents the human-readable percentage.
    For example:
    - 18.00 means 18% (18 / 100)
    - 5.50 means 5.5% (5.5 / 100)

    Formula:
        (base_amount * percentage_rate) / 100

    Parameters:
        base_amount: The base value (e.g. subtotal).
        percentage_rate: The rate in percentage points (e.g. 18.00).
        round_result: If True, quantizes to 2 decimal places using ROUND_HALF_UP.

    Returns:
        Calculated percentage amount as Decimal.
    """
    dec_base = to_decimal(base_amount)
    dec_rate = to_decimal(percentage_rate)

    raw_val = (dec_base * dec_rate) / ONE_HUNDRED
    return round_money(raw_val) if round_result else raw_val


def is_zero(amount: MoneyType) -> bool:
    """Check if the monetary amount is equal to zero."""
    return to_decimal(amount) == 0


def is_positive(amount: MoneyType) -> bool:
    """Check if the monetary amount is strictly positive (> 0)."""
    return to_decimal(amount) > 0


def is_negative(amount: MoneyType) -> bool:
    """Check if the monetary amount is strictly negative (< 0)."""
    return to_decimal(amount) < 0
