"""
Unit Tests for Invoice Calculation Engine (backend/services/billing/invoice_calculator.py).
"""

import pytest
from decimal import Decimal
from backend.services.billing.invoice_calculator import (
    LineItemInput,
    calculate_invoice,
)
from backend.services.finance.tax_service import TaxRuleInput
from backend.services.finance.discount_service import DiscountRuleInput


class TestInvoiceCalculator:
    def test_single_item_no_tax_no_discount(self):
        items = [LineItemInput(description="Standard SaaS", unit_price="99.00", quantity=1)]
        res = calculate_invoice(items=items, currency="USD")

        assert res.subtotal == Decimal("99.00")
        assert res.total_discount_amount == Decimal("0.00")
        assert res.tax_amount == Decimal("0.00")
        assert res.total_amount == Decimal("99.00")
        assert res.is_audited_valid is True
        assert len(res.items) == 1

    def test_multi_item_with_quantities(self):
        items = [
            LineItemInput(description="User Seats", unit_price="10.00", quantity=5),     # 50.00
            LineItemInput(description="Storage 100GB", unit_price="15.50", quantity=2), # 31.00
        ]
        res = calculate_invoice(items=items, currency="USD")

        assert res.subtotal == Decimal("81.00")
        assert res.total_amount == Decimal("81.00")
        assert res.is_audited_valid is True

    def test_item_level_discount(self):
        items = [
            LineItemInput(
                description="Custom Domain",
                unit_price="50.00",
                quantity=1,
                discount_amount="10.00",
            )
        ]
        res = calculate_invoice(items=items)

        assert res.subtotal == Decimal("50.00")
        assert res.total_item_discounts == Decimal("10.00")
        assert res.total_discount_amount == Decimal("10.00")
        assert res.total_amount == Decimal("40.00")
        assert res.is_audited_valid is True

    def test_invoice_level_percentage_discount_and_tax(self):
        """
        Subtotal: 100.00
        Discount: 20% = 20.00
        Taxable: 80.00
        Tax: 18% of 80.00 = 14.40
        Total: 80.00 + 14.40 = 94.40
        """
        items = [LineItemInput(description="Pro Plan", unit_price="100.00", quantity=1)]
        discount = DiscountRuleInput(code="SAVE20", discount_type="percentage", value="20.00")
        tax = TaxRuleInput(name="GST 18%", rate_percentage="18.00")

        res = calculate_invoice(
            items=items,
            invoice_discount=discount,
            tax_rules=tax,
        )

        assert res.subtotal == Decimal("100.00")
        assert res.invoice_discount_amount == Decimal("20.00")
        assert res.total_discount_amount == Decimal("20.00")
        assert res.taxable_subtotal == Decimal("80.00")
        assert res.tax_amount == Decimal("14.40")
        assert res.total_amount == Decimal("94.40")
        assert res.is_audited_valid is True

    def test_tax_exemption_overrides_tax_rules(self):
        items = [LineItemInput(description="Enterprise Plan", unit_price="500.00", quantity=1)]
        tax = TaxRuleInput(name="VAT 20%", rate_percentage="20.00")

        res = calculate_invoice(
            items=items,
            tax_rules=tax,
            is_tax_exempt=True,
        )

        assert res.subtotal == Decimal("500.00")
        assert res.tax_amount == Decimal("0.00")
        assert res.total_amount == Decimal("500.00")
        assert res.is_tax_exempt is True
        assert res.is_audited_valid is True

    def test_combined_item_discount_and_invoice_discount(self):
        # Item 1: $100 with $10 discount -> $90
        # Item 2: $50 with $0 discount -> $50
        # Subtotal: $150
        # Item discounts: $10
        # Base for invoice discount: $140
        # Invoice discount: 10% on $140 = $14
        # Total discounts: $10 + $14 = $24
        # Taxable: $150 - $24 = $126
        items = [
            LineItemInput(description="Item 1", unit_price="100.00", discount_amount="10.00"),
            LineItemInput(description="Item 2", unit_price="50.00"),
        ]
        discount = DiscountRuleInput(code="EXTRA10", discount_type="percentage", value="10.00")

        res = calculate_invoice(items=items, invoice_discount=discount)

        assert res.subtotal == Decimal("150.00")
        assert res.total_item_discounts == Decimal("10.00")
        assert res.invoice_discount_amount == Decimal("14.00")
        assert res.total_discount_amount == Decimal("24.00")
        assert res.total_amount == Decimal("126.00")
        assert res.is_audited_valid is True

    def test_full_discount_free_invoice(self):
        # 100% discount
        items = [LineItemInput(description="Trial Month", unit_price="30.00")]
        discount = DiscountRuleInput(code="100OFF", discount_type="percentage", value="100.00")
        tax = TaxRuleInput(name="Sales Tax 10%", rate_percentage="10.00")

        res = calculate_invoice(items=items, invoice_discount=discount, tax_rules=tax)

        assert res.subtotal == Decimal("30.00")
        assert res.total_discount_amount == Decimal("30.00")
        assert res.taxable_subtotal == Decimal("0.00")
        assert res.tax_amount == Decimal("0.00")
        assert res.total_amount == Decimal("0.00")
        assert res.is_audited_valid is True

    def test_zero_price_line_item(self):
        items = [LineItemInput(description="Free Onboarding Tier", unit_price="0.00")]
        res = calculate_invoice(items=items)

        assert res.subtotal == Decimal("0.00")
        assert res.total_amount == Decimal("0.00")
        assert res.is_audited_valid is True

    def test_empty_line_items_raises_value_error(self):
        with pytest.raises(ValueError, match="Cannot calculate invoice with empty line items"):
            calculate_invoice(items=[])

    def test_negative_unit_price_raises_value_error(self):
        items = [LineItemInput(description="Bad Item", unit_price="-10.00")]
        with pytest.raises(ValueError, match="cannot have a negative unit price"):
            calculate_invoice(items=items)

    def test_negative_quantity_raises_value_error(self):
        items = [LineItemInput(description="Bad Quantity", unit_price="10.00", quantity=-1)]
        with pytest.raises(ValueError, match="cannot have a negative quantity"):
            calculate_invoice(items=items)
