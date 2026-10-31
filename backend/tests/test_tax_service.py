"""
Unit Tests for Tax Calculation Engine (backend/services/finance/tax_service.py).
"""

import pytest
from decimal import Decimal
from backend.services.finance.tax_service import (
    TaxRuleInput,
    calculate_tax,
)


class TestTaxService:
    def test_single_percentage_tax(self):
        rule = TaxRuleInput(name="GST 18%", rate_percentage="18.00", tax_type="percentage")
        res = calculate_tax(taxable_amount="100.00", tax_rules=rule)

        assert res.total_tax_amount == Decimal("18.00")
        assert res.is_tax_exempt is False
        assert len(res.breakdowns) == 1
        assert res.breakdowns[0].rule_name == "GST 18%"
        assert res.breakdowns[0].tax_amount == Decimal("18.00")

    def test_fixed_amount_tax(self):
        rule = TaxRuleInput(name="Regulatory Surcharge", rate_percentage="5.00", tax_type="fixed_amount")
        res = calculate_tax(taxable_amount="100.00", tax_rules=rule)

        assert res.total_tax_amount == Decimal("5.00")
        assert len(res.breakdowns) == 1
        assert res.breakdowns[0].tax_amount == Decimal("5.00")

    def test_tax_exempt_customer(self):
        rule = TaxRuleInput(name="VAT 20%", rate_percentage="20.00", tax_type="percentage")
        res = calculate_tax(taxable_amount="250.00", tax_rules=rule, is_tax_exempt=True)

        assert res.total_tax_amount == Decimal("0.00")
        assert res.is_tax_exempt is True
        assert len(res.breakdowns) == 0

    def test_zero_taxable_amount(self):
        rule = TaxRuleInput(name="GST 18%", rate_percentage="18.00", tax_type="percentage")
        res = calculate_tax(taxable_amount="0.00", tax_rules=rule)

        assert res.total_tax_amount == Decimal("0.00")
        assert len(res.breakdowns) == 0

    def test_negative_taxable_amount_raises_value_error(self):
        rule = TaxRuleInput(name="GST 18%", rate_percentage="18.00")
        with pytest.raises(ValueError, match="Taxable amount cannot be negative"):
            calculate_tax(taxable_amount="-50.00", tax_rules=rule)

    def test_multiple_standard_taxes(self):
        rule1 = TaxRuleInput(name="State Tax 6%", rate_percentage="6.00")
        rule2 = TaxRuleInput(name="City Tax 2%", rate_percentage="2.00")
        res = calculate_tax(taxable_amount="100.00", tax_rules=[rule1, rule2])

        assert res.total_tax_amount == Decimal("8.00")
        assert len(res.breakdowns) == 2
        assert res.breakdowns[0].tax_amount == Decimal("6.00")
        assert res.breakdowns[1].tax_amount == Decimal("2.00")

    def test_compound_tax(self):
        standard = TaxRuleInput(name="Duty 10%", rate_percentage="10.00", is_compound=False)
        compound = TaxRuleInput(name="Surcharge 5%", rate_percentage="5.00", is_compound=True)
        # Base: 100.00
        # Standard: 10% of 100 = 10.00
        # Compound base: 100 + 10 = 110.00
        # Compound tax: 5% of 110.00 = 5.50
        # Total tax: 15.50
        res = calculate_tax(taxable_amount="100.00", tax_rules=[standard, compound])

        assert res.total_tax_amount == Decimal("15.50")
        assert res.breakdowns[0].tax_amount == Decimal("10.00")
        assert res.breakdowns[1].tax_amount == Decimal("5.50")

    def test_inactive_rule_skipped(self):
        active_rule = TaxRuleInput(name="Active Tax 10%", rate_percentage="10.00", is_active=True)
        inactive_rule = TaxRuleInput(name="Old Tax 5%", rate_percentage="5.00", is_active=False)
        res = calculate_tax(taxable_amount="100.00", tax_rules=[active_rule, inactive_rule])

        assert res.total_tax_amount == Decimal("10.00")
        assert len(res.breakdowns) == 1

    def test_tax_rounding_edge_case(self):
        # 8.875% on 49.99 = 4.4366125 -> rounds to 4.44
        rule = TaxRuleInput(name="NY Sales Tax", rate_percentage="8.875")
        res = calculate_tax(taxable_amount="49.99", tax_rules=rule)

        assert res.total_tax_amount == Decimal("4.44")
