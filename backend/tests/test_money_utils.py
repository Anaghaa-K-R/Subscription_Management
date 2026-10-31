"""
Unit Tests for Money Utilities Module (backend/services/finance/money_utils.py).
"""

import pytest
from decimal import Decimal
from backend.services.finance.money_utils import (
    to_decimal,
    round_money,
    money_add,
    money_sub,
    money_mul,
    money_div,
    calculate_percentage,
    is_zero,
    is_positive,
    is_negative,
    ZERO_MONEY,
)


class TestToDecimal:
    def test_decimal_input_preserved(self):
        val = Decimal("199.99")
        assert to_decimal(val) == val

    def test_integer_conversion(self):
        assert to_decimal(50) == Decimal("50")

    def test_string_conversion(self):
        assert to_decimal("  45.67  ") == Decimal("45.67")

    def test_float_conversion_avoids_binary_artifact(self):
        # 0.1 in float is 0.10000000000000000555...
        result = to_decimal(0.1)
        assert result == Decimal("0.1")

    def test_none_raises_value_error(self):
        with pytest.raises(ValueError, match="Cannot convert None to Decimal"):
            to_decimal(None)

    def test_invalid_string_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid monetary value"):
            to_decimal("invalid_amount")


class TestRoundMoney:
    def test_round_half_up_positive(self):
        # 2.555 rounds up to 2.56 in ROUND_HALF_UP
        assert round_money("2.555") == Decimal("2.56")
        assert round_money("2.554") == Decimal("2.55")
        assert round_money("2.5551") == Decimal("2.56")

    def test_round_half_up_zero(self):
        assert round_money("0.0000") == Decimal("0.00")

    def test_round_custom_places(self):
        assert round_money("1.23456", places=4) == Decimal("1.2346")


class TestMoneyAdd:
    def test_empty_arguments_returns_zero(self):
        assert money_add() == ZERO_MONEY

    def test_multiple_amounts_addition(self):
        result = money_add("10.50", 20, Decimal("5.25"))
        assert result == Decimal("35.75")

    def test_mixed_signs(self):
        result = money_add("100.00", "-40.00", "-15.50")
        assert result == Decimal("44.50")


class TestMoneySub:
    def test_positive_difference(self):
        assert money_sub("100.00", "45.25") == Decimal("54.75")

    def test_negative_difference(self):
        assert money_sub("45.25", "100.00") == Decimal("-54.75")

    def test_zero_difference(self):
        assert money_sub("50.00", 50) == Decimal("0.00")


class TestMoneyMul:
    def test_standard_multiplication(self):
        assert money_mul("19.99", 3) == Decimal("59.97")

    def test_fractional_factor(self):
        assert money_mul("100.00", "0.155") == Decimal("15.50")

    def test_zero_multiplication(self):
        assert money_mul("100.00", 0) == Decimal("0.00")


class TestMoneyDiv:
    def test_standard_division(self):
        assert money_div("100.00", 3) == Decimal("33.33")

    def test_division_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError):
            money_div("100.00", 0)


class TestCalculatePercentage:
    def test_percentage_18_percent(self):
        # 18.00 means 18%
        assert calculate_percentage("100.00", "18.00") == Decimal("18.00")

    def test_percentage_partial_rate(self):
        # 15.5% of 250.00 = 38.75
        assert calculate_percentage("250.00", "15.5") == Decimal("38.75")

    def test_percentage_rounding_edge_case(self):
        # 33.33 * 7.25 / 100 = 2.416425 -> 2.42
        assert calculate_percentage("33.33", "7.25") == Decimal("2.42")

    def test_percentage_zero_rate(self):
        assert calculate_percentage("100.00", "0.00") == Decimal("0.00")

    def test_percentage_zero_base(self):
        assert calculate_percentage("0.00", "18.00") == Decimal("0.00")


class TestComparisonHelpers:
    def test_is_zero(self):
        assert is_zero("0.00") is True
        assert is_zero(0) is True
        assert is_zero("0.01") is False

    def test_is_positive(self):
        assert is_positive("0.01") is True
        assert is_positive("0.00") is False
        assert is_positive("-10.00") is False

    def test_is_negative(self):
        assert is_negative("-0.01") is True
        assert is_negative("0.00") is False
        assert is_negative("10.00") is False
