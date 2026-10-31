"""
Unit Tests for Discount Calculation & Validation Engine (backend/services/finance/discount_service.py).
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from backend.services.finance.discount_service import (
    DiscountRuleInput,
    validate_and_apply_discount,
)


class TestDiscountService:
    def test_none_discount_returns_full_amount(self):
        res = validate_and_apply_discount(base_amount="150.00", discount_rule=None)
        assert res.is_valid is True
        assert res.discount_amount == Decimal("0.00")
        assert res.net_amount == Decimal("150.00")

    def test_standard_percentage_discount(self):
        rule = DiscountRuleInput(code="SAVE20", discount_type="percentage", value="20.00")
        res = validate_and_apply_discount(base_amount="100.00", discount_rule=rule)

        assert res.is_valid is True
        assert res.discount_amount == Decimal("20.00")
        assert res.net_amount == Decimal("80.00")

    def test_standard_fixed_discount(self):
        rule = DiscountRuleInput(code="FLAT25", discount_type="fixed_amount", value="25.00")
        res = validate_and_apply_discount(base_amount="100.00", discount_rule=rule)

        assert res.is_valid is True
        assert res.discount_amount == Decimal("25.00")
        assert res.net_amount == Decimal("75.00")

    def test_fixed_discount_capped_at_base_amount(self):
        # Discount of $150 on an invoice of $100 cannot produce negative net amount
        rule = DiscountRuleInput(code="SUPER150", discount_type="fixed_amount", value="150.00")
        res = validate_and_apply_discount(base_amount="100.00", discount_rule=rule)

        assert res.is_valid is True
        assert res.discount_amount == Decimal("100.00")
        assert res.net_amount == Decimal("0.00")

    def test_percentage_discount_cap(self):
        # 50% of 1000 = 500, but capped at 100
        rule = DiscountRuleInput(
            code="HALFOFFCAP",
            discount_type="percentage",
            value="50.00",
            max_discount_amount="100.00",
        )
        res = validate_and_apply_discount(base_amount="1000.00", discount_rule=rule)

        assert res.is_valid is True
        assert res.discount_amount == Decimal("100.00")
        assert res.net_amount == Decimal("900.00")

    def test_minimum_purchase_amount_not_met(self):
        rule = DiscountRuleInput(
            code="BIGSPENDER",
            discount_type="percentage",
            value="15.00",
            min_purchase_amount="200.00",
        )
        res = validate_and_apply_discount(base_amount="150.00", discount_rule=rule)

        assert res.is_valid is False
        assert res.discount_amount == Decimal("0.00")
        assert res.net_amount == Decimal("150.00")
        assert "Minimum purchase amount not met" in res.rejection_reason

    def test_minimum_quantity_condition(self):
        rule = DiscountRuleInput(
            code="TEAM5",
            discount_type="percentage",
            value="10.00",
            min_quantity=5,
        )
        # Quantity 3 fails
        res_fail = validate_and_apply_discount(base_amount="300.00", discount_rule=rule, quantity=3)
        assert res_fail.is_valid is False
        assert "Minimum quantity requirement not met" in res_fail.rejection_reason

        # Quantity 5 passes
        res_pass = validate_and_apply_discount(base_amount="500.00", discount_rule=rule, quantity=5)
        assert res_pass.is_valid is True
        assert res_pass.discount_amount == Decimal("50.00")

    def test_expired_discount(self):
        yesterday = date.today() - timedelta(days=1)
        two_days_ago = date.today() - timedelta(days=2)
        rule = DiscountRuleInput(
            code="EXPIRED",
            discount_type="percentage",
            value="20.00",
            start_date=two_days_ago,
            end_date=yesterday,
        )
        res = validate_and_apply_discount(base_amount="100.00", discount_rule=rule)

        assert res.is_valid is False
        assert "expired" in res.rejection_reason.lower()

    def test_future_start_date_discount(self):
        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)
        rule = DiscountRuleInput(
            code="FUTURE",
            discount_type="percentage",
            value="20.00",
            start_date=tomorrow,
            end_date=next_week,
        )
        res = validate_and_apply_discount(base_amount="100.00", discount_rule=rule)

        assert res.is_valid is False
        assert "not started yet" in res.rejection_reason.lower()

    def test_max_redemption_uses_exceeded(self):
        rule = DiscountRuleInput(
            code="LIMITED",
            discount_type="percentage",
            value="20.00",
            max_uses=10,
            current_uses=10,
        )
        res = validate_and_apply_discount(base_amount="100.00", discount_rule=rule)

        assert res.is_valid is False
        assert "maximum redemption limit" in res.rejection_reason.lower()

    def test_inactive_discount(self):
        rule = DiscountRuleInput(
            code="DEACTIVATED",
            discount_type="percentage",
            value="20.00",
            is_active=False,
        )
        res = validate_and_apply_discount(base_amount="100.00", discount_rule=rule)

        assert res.is_valid is False
        assert "inactive" in res.rejection_reason.lower()

    def test_plan_specific_discount(self):
        rule = DiscountRuleInput(
            code="ENTERPRISEONLY",
            discount_type="percentage",
            value="30.00",
            applicable_plan_id=99,
        )
        # Mismatched plan
        res_mismatch = validate_and_apply_discount(base_amount="100.00", discount_rule=rule, plan_id=10)
        assert res_mismatch.is_valid is False
        assert "not applicable" in res_mismatch.rejection_reason.lower()

        # Matched plan
        res_match = validate_and_apply_discount(base_amount="100.00", discount_rule=rule, plan_id=99)
        assert res_match.is_valid is True
        assert res_match.discount_amount == Decimal("30.00")

    def test_negative_base_amount_raises_value_error(self):
        rule = DiscountRuleInput(code="TEST", discount_type="percentage", value="10.00")
        with pytest.raises(ValueError, match="Base amount cannot be negative"):
            validate_and_apply_discount(base_amount="-50.00", discount_rule=rule)
