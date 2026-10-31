"""
Tax Calculation Engine for SubscriptIQ.

Provides pure, deterministic tax calculations supporting:
- Percentage-based tax rules (e.g. 18.00 means 18%).
- Fixed-amount taxes (e.g. $5.00 flat surcharge).
- Tax-exempt customer status (resulting in $0.00 tax).
- Compound and standard tax sequencing.
- Itemized tax breakdown for auditing and reporting.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Union
from .money_utils import (
    to_decimal,
    round_money,
    calculate_percentage,
    ZERO_MONEY,
    MoneyType,
)


@dataclass(frozen=True)
class TaxRuleInput:
    """
    Data input representation for a tax rule.

    Attributes:
        name: Identifier or title for the tax (e.g. 'GST 18%', 'Standard VAT').
        rate_percentage: Numeric rate (e.g. 18.00 means 18%; for fixed_amount, the flat value).
        tax_type: 'percentage' or 'fixed_amount'.
        country: Optional geographical jurisdiction.
        state_province: Optional regional jurisdiction.
        is_active: Whether this rule is currently applied.
        is_compound: Whether this tax applies on top of previous taxes.
    """
    name: str
    rate_percentage: MoneyType
    tax_type: str = "percentage"
    country: Optional[str] = None
    state_province: Optional[str] = None
    is_active: bool = True
    is_compound: bool = False


@dataclass(frozen=True)
class TaxItemBreakdown:
    """
    Itemized breakdown of a single applied tax rule.
    """
    rule_name: str
    tax_type: str
    rate_percentage: Decimal
    taxable_base_amount: Decimal
    tax_amount: Decimal


@dataclass(frozen=True)
class TaxCalculationResult:
    """
    Comprehensive output of a tax calculation.
    """
    taxable_base_amount: Decimal
    total_tax_amount: Decimal
    is_tax_exempt: bool
    breakdowns: List[TaxItemBreakdown] = field(default_factory=list)


def calculate_tax(
    taxable_amount: MoneyType,
    tax_rules: Union[TaxRuleInput, List[TaxRuleInput], None] = None,
    is_tax_exempt: bool = False,
) -> TaxCalculationResult:
    """
    Calculate taxes on a taxable amount (typically subtotal after discounts).

    Consistent Convention:
    For percentage taxes, rate_percentage represents the literal percent.
    Example: rate_percentage=18.00 means 18%.

    Parameters:
        taxable_amount: The base monetary value to be taxed.
        tax_rules: Single TaxRuleInput, list of TaxRuleInputs, or None.
        is_tax_exempt: If True, all taxes evaluate to 0.00.

    Returns:
        TaxCalculationResult with total tax and itemized breakdowns.

    Raises:
        ValueError: If taxable_amount is negative.
    """
    dec_taxable = to_decimal(taxable_amount)
    if dec_taxable < 0:
        raise ValueError(f"Taxable amount cannot be negative: {dec_taxable}")

    rounded_taxable = round_money(dec_taxable)

    # 1. Handle Tax Exemption
    if is_tax_exempt:
        return TaxCalculationResult(
            taxable_base_amount=rounded_taxable,
            total_tax_amount=ZERO_MONEY,
            is_tax_exempt=True,
            breakdowns=[],
        )

    # 2. Normalize Tax Rules
    rules_list: List[TaxRuleInput] = []
    if tax_rules is not None:
        if isinstance(tax_rules, TaxRuleInput):
            rules_list = [tax_rules]
        else:
            rules_list = list(tax_rules)

    active_rules = [r for r in rules_list if r.is_active]

    if not active_rules or rounded_taxable == 0:
        return TaxCalculationResult(
            taxable_base_amount=rounded_taxable,
            total_tax_amount=ZERO_MONEY,
            is_tax_exempt=False,
            breakdowns=[],
        )

    breakdowns: List[TaxItemBreakdown] = []
    total_tax = ZERO_MONEY

    # Separate standard rules from compound rules
    standard_rules = [r for r in active_rules if not r.is_compound]
    compound_rules = [r for r in active_rules if r.is_compound]

    # 3. Calculate Standard Taxes
    for rule in standard_rules:
        rate = to_decimal(rule.rate_percentage)
        if rule.tax_type == "percentage":
            tax_for_rule = calculate_percentage(rounded_taxable, rate)
        elif rule.tax_type == "fixed_amount":
            tax_for_rule = round_money(rate)
        else:
            raise ValueError(f"Unsupported tax_type: '{rule.tax_type}'. Use 'percentage' or 'fixed_amount'.")

        breakdowns.append(
            TaxItemBreakdown(
                rule_name=rule.name,
                tax_type=rule.tax_type,
                rate_percentage=round_money(rate, places=2),
                taxable_base_amount=rounded_taxable,
                tax_amount=tax_for_rule,
            )
        )
        total_tax += tax_for_rule

    # 4. Calculate Compound Taxes (Base includes previously accrued taxes)
    compound_base = rounded_taxable + total_tax
    for rule in compound_rules:
        rate = to_decimal(rule.rate_percentage)
        if rule.tax_type == "percentage":
            tax_for_rule = calculate_percentage(compound_base, rate)
        elif rule.tax_type == "fixed_amount":
            tax_for_rule = round_money(rate)
        else:
            raise ValueError(f"Unsupported tax_type: '{rule.tax_type}'. Use 'percentage' or 'fixed_amount'.")

        breakdowns.append(
            TaxItemBreakdown(
                rule_name=rule.name,
                tax_type=rule.tax_type,
                rate_percentage=round_money(rate, places=2),
                taxable_base_amount=round_money(compound_base),
                tax_amount=tax_for_rule,
            )
        )
        total_tax += tax_for_rule
        compound_base += tax_for_rule

    return TaxCalculationResult(
        taxable_base_amount=rounded_taxable,
        total_tax_amount=round_money(total_tax),
        is_tax_exempt=False,
        breakdowns=breakdowns,
    )
