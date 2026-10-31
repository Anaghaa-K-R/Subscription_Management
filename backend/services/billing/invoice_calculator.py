"""
Invoice Calculation Engine for SubscriptIQ.

Orchestrates line items, discounts, and taxes to produce an auditable,
deterministic invoice total. All arithmetic uses high-precision Decimal with
ROUND_HALF_UP quantization.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional, Union

from backend.services.finance.money_utils import (
    to_decimal,
    round_money,
    money_add,
    money_sub,
    money_mul,
    ZERO_MONEY,
    MoneyType,
)
from backend.services.finance.tax_service import (
    TaxRuleInput,
    TaxCalculationResult,
    TaxItemBreakdown,
    calculate_tax,
)
from backend.services.finance.discount_service import (
    DiscountRuleInput,
    DiscountApplicationResult,
    validate_and_apply_discount,
)


@dataclass(frozen=True)
class LineItemInput:
    """
    Input specification for an invoice line item.

    Attributes:
        description: Line item name or description.
        unit_price: Price per unit.
        quantity: Number of units (default: 1).
        discount_amount: Item-level discount (default: 0.00).
    """
    description: str
    unit_price: MoneyType
    quantity: MoneyType = 1
    discount_amount: MoneyType = Decimal("0.00")


@dataclass(frozen=True)
class LineItemCalculation:
    """
    Detailed calculated result for a single line item.
    """
    description: str
    unit_price: Decimal
    quantity: Decimal
    gross_amount: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    total_price: Decimal


@dataclass(frozen=True)
class InvoiceCalculationResult:
    """
    Comprehensive financial calculation result for an entire invoice.

    Mathematical Invariant:
        subtotal - total_discount_amount + tax_amount == total_amount
    """
    currency: str
    items: List[LineItemCalculation]
    subtotal: Decimal
    total_item_discounts: Decimal
    invoice_discount_amount: Decimal
    total_discount_amount: Decimal
    taxable_subtotal: Decimal
    tax_amount: Decimal
    tax_breakdowns: List[TaxItemBreakdown]
    total_amount: Decimal
    is_tax_exempt: bool
    is_audited_valid: bool
    discount_result: Optional[DiscountApplicationResult] = None
    audit_notes: Optional[str] = None


def calculate_invoice(
    items: List[LineItemInput],
    currency: str = "USD",
    invoice_discount: Optional[DiscountRuleInput] = None,
    tax_rules: Union[TaxRuleInput, List[TaxRuleInput], None] = None,
    is_tax_exempt: bool = False,
    evaluation_date: Optional[date] = None,
    plan_id: Optional[int] = None,
) -> InvoiceCalculationResult:
    """
    Calculate an entire invoice breakdown:
    1. Line item gross = quantity * unit_price
    2. Line item taxable = gross - line item discount
    3. Invoice subtotal = sum of line item gross amounts
    4. Item discounts = sum of line item discount amounts
    5. Invoice-level discount = evaluated against pre-discount subtotal
    6. Taxable subtotal = subtotal - total discounts (capped at >= 0)
    7. Taxes = computed on taxable subtotal (or 0 if tax-exempt)
    8. Total amount = taxable subtotal + tax amount
    9. Internal audit = validates that line item math matches total.

    Parameters:
        items: List of LineItemInput objects (must not be empty).
        currency: ISO-4217 currency code (default: 'USD').
        invoice_discount: Optional invoice-level discount configuration.
        tax_rules: Tax rule or list of tax rules to apply.
        is_tax_exempt: If True, bypasses tax rules and sets tax to $0.00.
        evaluation_date: Date used to validate discount validity (default: today).
        plan_id: Plan ID to validate discount applicability.

    Returns:
        InvoiceCalculationResult with itemized and aggregate monetary values.

    Raises:
        ValueError: If items list is empty or line item has negative price/quantity.
    """
    if not items:
        raise ValueError("Cannot calculate invoice with empty line items.")

    calculated_items: List[LineItemCalculation] = []
    subtotal = ZERO_MONEY
    total_item_discounts = ZERO_MONEY
    total_quantity = 0

    # 1. Process Line Items
    for item in items:
        unit_price = to_decimal(item.unit_price)
        quantity = to_decimal(item.quantity)

        if unit_price < 0:
            raise ValueError(f"Line item '{item.description}' cannot have a negative unit price: {unit_price}")
        if quantity < 0:
            raise ValueError(f"Line item '{item.description}' cannot have a negative quantity: {quantity}")

        gross = money_mul(unit_price, quantity)
        item_discount = round_money(to_decimal(item.discount_amount))

        # Item discount cannot exceed gross
        item_discount = min(item_discount, gross)
        taxable = money_sub(gross, item_discount)

        calc_item = LineItemCalculation(
            description=item.description,
            unit_price=round_money(unit_price),
            quantity=round_money(quantity, places=2),
            gross_amount=gross,
            discount_amount=item_discount,
            taxable_amount=taxable,
            total_price=taxable,  # Base item total before invoice-level tax
        )
        calculated_items.append(calc_item)

        subtotal += gross
        total_item_discounts += item_discount
        total_quantity += int(quantity)

    subtotal = round_money(subtotal)
    total_item_discounts = round_money(total_item_discounts)

    # 2. Apply Invoice-Level Discount
    base_for_invoice_discount = max(ZERO_MONEY, subtotal - total_item_discounts)
    discount_res: Optional[DiscountApplicationResult] = None
    invoice_discount_amount = ZERO_MONEY

    if invoice_discount is not None:
        discount_res = validate_and_apply_discount(
            base_amount=base_for_invoice_discount,
            discount_rule=invoice_discount,
            quantity=total_quantity,
            evaluation_date=evaluation_date,
            plan_id=plan_id,
        )
        if discount_res.is_valid:
            invoice_discount_amount = discount_res.discount_amount

    total_discount_amount = round_money(total_item_discounts + invoice_discount_amount)
    taxable_subtotal = max(ZERO_MONEY, round_money(subtotal - total_discount_amount))

    # 3. Calculate Taxes
    tax_res: TaxCalculationResult = calculate_tax(
        taxable_amount=taxable_subtotal,
        tax_rules=tax_rules,
        is_tax_exempt=is_tax_exempt,
    )
    tax_amount = tax_res.total_tax_amount

    # 4. Final Invoice Total
    total_amount = round_money(taxable_subtotal + tax_amount)

    # 5. Independent Mathematical Audit
    expected_total = round_money(subtotal - total_discount_amount + tax_amount)
    is_audited_valid = (expected_total == total_amount) and (total_amount >= 0)
    audit_notes = None if is_audited_valid else f"Audit discrepancy: computed {total_amount} != expected {expected_total}"

    return InvoiceCalculationResult(
        currency=currency.upper(),
        items=calculated_items,
        subtotal=subtotal,
        total_item_discounts=total_item_discounts,
        invoice_discount_amount=invoice_discount_amount,
        total_discount_amount=total_discount_amount,
        taxable_subtotal=taxable_subtotal,
        tax_amount=tax_amount,
        tax_breakdowns=tax_res.breakdowns,
        total_amount=total_amount,
        is_tax_exempt=is_tax_exempt,
        is_audited_valid=is_audited_valid,
        discount_result=discount_res,
        audit_notes=audit_notes,
    )
