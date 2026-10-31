"""
AI Intelligent Invoice Auditor for SubscriptIQ.

Performs mathematical and financial integrity verification on recurring invoices:
- Validates line-item math (quantity * unit_price).
- Recalculates expected subtotal, discounts, and taxes using InvoiceCalculator.
- Flags penny rounding drift and major arithmetic anomalies.
- Rejects negative unit rates, negative quantities, or illegal balances.
- Sets `is_audited=True` and records diagnostic discrepancy notes on ORM models.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from backend.services.billing.invoice_calculator import (
    LineItemInput,
    InvoiceCalculationResult,
    calculate_invoice,
)
from backend.services.finance.discount_service import DiscountRuleInput
from backend.services.finance.tax_service import TaxRuleInput
from backend.services.finance.money_utils import (
    money_add,
    money_sub,
    round_money,
    to_decimal,
)


@dataclass
class AuditResult:
    """Diagnostic outcome of an automated invoice audit."""
    is_valid: bool
    invoice_number: str
    invoice_id: Optional[int] = None
    discrepancy_amount: Decimal = Decimal("0.00")
    discrepancies: List[str] = field(default_factory=list)
    expected_subtotal: Decimal = Decimal("0.00")
    actual_subtotal: Decimal = Decimal("0.00")
    expected_discount: Decimal = Decimal("0.00")
    actual_discount: Decimal = Decimal("0.00")
    expected_tax: Decimal = Decimal("0.00")
    actual_tax: Decimal = Decimal("0.00")
    expected_total: Decimal = Decimal("0.00")
    actual_total: Decimal = Decimal("0.00")
    expected_amount_due: Decimal = Decimal("0.00")
    actual_amount_due: Decimal = Decimal("0.00")
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "invoice_number": self.invoice_number,
            "invoice_id": self.invoice_id,
            "discrepancy_amount": float(self.discrepancy_amount),
            "discrepancies": self.discrepancies,
            "expected_subtotal": float(self.expected_subtotal),
            "actual_subtotal": float(self.actual_subtotal),
            "expected_discount": float(self.expected_discount),
            "actual_discount": float(self.actual_discount),
            "expected_tax": float(self.expected_tax),
            "actual_tax": float(self.actual_tax),
            "expected_total": float(self.expected_total),
            "actual_total": float(self.actual_total),
            "expected_amount_due": float(self.expected_amount_due),
            "actual_amount_due": float(self.actual_amount_due),
            "notes": self.notes,
        }


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Helper to retrieve attribute from ORM model or dictionary."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def audit_invoice(
    invoice: Any,
    items: Optional[List[Any]] = None,
    tax_rules: Optional[List[Any]] = None,
    discount_obj: Optional[Any] = None,
    is_tax_exempt: bool = False,
    update_model: bool = True,
) -> AuditResult:
    """
    Audits a single invoice against independent recalculation.

    Parameters:
        invoice: Invoice ORM instance or dictionary.
        items: Optional explicit list of line items (falls back to invoice.items).
        tax_rules: Optional tax rules applied.
        discount_obj: Optional discount coupon metadata.
        is_tax_exempt: If customer is exempt from tax.
        update_model: If True and invoice is an ORM model, sets is_audited & audit_discrepancy_notes.

    Returns:
        AuditResult with boolean validity status and detailed diagnostic notes.
    """
    inv_id = _get_val(invoice, "id")
    inv_num = _get_val(invoice, "invoice_number", f"INV-{inv_id}")

    actual_subtotal = to_decimal(_get_val(invoice, "subtotal", 0))
    actual_discount = to_decimal(_get_val(invoice, "discount_amount", 0))
    actual_tax = to_decimal(_get_val(invoice, "tax_amount", 0))
    actual_total = to_decimal(_get_val(invoice, "total_amount", 0))
    actual_paid = to_decimal(_get_val(invoice, "amount_paid", 0))
    actual_due = to_decimal(_get_val(invoice, "amount_due", 0))

    discrepancies: List[str] = []
    total_discrepancy_loss = Decimal("0.00")

    # 1. Negative Value Check
    if actual_subtotal < Decimal("0.00"):
        discrepancies.append(f"Subtotal cannot be negative (found {actual_subtotal})")
    if actual_total < Decimal("0.00"):
        discrepancies.append(f"Total amount cannot be negative (found {actual_total})")
    if actual_due < Decimal("0.00"):
        discrepancies.append(f"Amount due cannot be negative (found {actual_due})")
    if actual_paid < Decimal("0.00"):
        discrepancies.append(f"Amount paid cannot be negative (found {actual_paid})")

    # 2. Extract line items
    raw_items = items if items is not None else _get_val(invoice, "items", [])
    calculation_items: List[LineItemInput] = []

    sum_item_gross = Decimal("0.00")
    for idx, item in enumerate(raw_items, start=1):
        desc = _get_val(item, "description", f"Item #{idx}")
        qty = to_decimal(_get_val(item, "quantity", 1))
        unit_price = to_decimal(_get_val(item, "unit_price", 0))
        item_discount = to_decimal(_get_val(item, "discount_amount", 0))
        item_tax = to_decimal(_get_val(item, "tax_amount", 0))

        if qty < Decimal("0.00"):
            discrepancies.append(f"Line item #{idx} ('{desc}') has negative quantity: {qty}")
        if unit_price < Decimal("0.00"):
            discrepancies.append(f"Line item #{idx} ('{desc}') has negative unit price: {unit_price}")

        sum_item_gross = money_add(sum_item_gross, round_money(qty * unit_price))
        calculation_items.append(
            LineItemInput(
                description=desc,
                unit_price=unit_price,
                quantity=qty,
                discount_amount=item_discount,
            )
        )

    # 3. Item Gross vs Subtotal Check
    if calculation_items and abs(money_sub(sum_item_gross, actual_subtotal)) > Decimal("0.01"):
        diff = abs(money_sub(sum_item_gross, actual_subtotal))
        discrepancies.append(
            f"Line items gross sum ({sum_item_gross}) does not match invoice subtotal ({actual_subtotal}), diff={diff}"
        )
        total_discrepancy_loss = money_add(total_discrepancy_loss, diff)

    # 4. Independent Recalculation via calculate_invoice
    expected_subtotal = actual_subtotal
    expected_discount = actual_discount
    expected_tax = actual_tax
    expected_total = actual_total
    expected_due = actual_due

    if calculation_items:
        # Check discount rule input
        disc_input: Optional[DiscountRuleInput] = None
        disc = discount_obj if discount_obj is not None else _get_val(invoice, "discount")
        if disc:
            disc_code = _get_val(disc, "code", "DISCOUNT")
            disc_type = _get_val(disc, "discount_type", "percentage")
            if disc_type == "fixed":
                disc_type = "fixed_amount"
            disc_val = to_decimal(_get_val(disc, "value", 0))
            disc_input = DiscountRuleInput(
                code=disc_code,
                discount_type=disc_type,
                value=disc_val,
                is_active=_get_val(disc, "is_active", True),
            )
        elif actual_discount > Decimal("0.00"):
            # If no discount rule object is attached, use recorded discount amount as fixed rule
            disc_input = DiscountRuleInput(
                code="RECORDED_DISCOUNT",
                discount_type="fixed_amount",
                value=actual_discount,
                is_active=True,
            )

        # Check tax rule input
        raw_tax_rules = tax_rules or []
        if not raw_tax_rules:
            single_tax_rule = _get_val(invoice, "tax_rule")
            if single_tax_rule:
                raw_tax_rules = [single_tax_rule]

        tax_inputs: List[TaxRuleInput] = []
        for tr in raw_tax_rules:
            if isinstance(tr, TaxRuleInput):
                tax_inputs.append(tr)
            else:
                tax_inputs.append(
                    TaxRuleInput(
                        name=_get_val(tr, "name", "Tax"),
                        rate_percentage=to_decimal(_get_val(tr, "rate_percentage", 0)),
                        tax_type=_get_val(tr, "tax_type", "percentage"),
                        is_compound=_get_val(tr, "is_compound", False),
                        is_active=_get_val(tr, "is_active", True),
                    )
                )

        if not tax_inputs and actual_tax > Decimal("0.00") and not is_tax_exempt:
            tax_rate = _get_val(invoice, "tax_rate_applied")
            if tax_rate is not None and to_decimal(tax_rate) > Decimal("0.00"):
                tax_inputs.append(
                    TaxRuleInput(
                        name="Recorded Tax",
                        rate_percentage=to_decimal(tax_rate),
                        tax_type="percentage",
                    )
                )
            else:
                tax_inputs.append(
                    TaxRuleInput(
                        name="Recorded Tax",
                        rate_percentage=actual_tax,
                        tax_type="fixed_amount",
                    )
                )

        try:
            calc_result = calculate_invoice(
                items=calculation_items,
                invoice_discount=disc_input,
                tax_rules=tax_inputs if tax_inputs else None,
                is_tax_exempt=is_tax_exempt,
            )

            expected_subtotal = calc_result.subtotal
            expected_discount = calc_result.total_discount_amount
            expected_tax = calc_result.tax_amount
            expected_total = calc_result.total_amount
            expected_due = max(Decimal("0.00"), money_sub(expected_total, actual_paid))

            # Check Subtotal Discrepancy
            sub_diff = abs(money_sub(calc_result.subtotal, actual_subtotal))
            if sub_diff > Decimal("0.01"):
                discrepancies.append(
                    f"Subtotal discrepancy: calculated {calc_result.subtotal} != recorded {actual_subtotal}"
                )
                total_discrepancy_loss = money_add(total_discrepancy_loss, sub_diff)

            # Check Total Discrepancy
            total_diff = abs(money_sub(calc_result.total_amount, actual_total))
            if total_diff > Decimal("0.01"):
                discrepancies.append(
                    f"Grand total discrepancy: calculated {calc_result.total_amount} != recorded {actual_total}"
                )
                total_discrepancy_loss = money_add(total_discrepancy_loss, total_diff)

            # Check Amount Due Discrepancy
            due_diff = abs(money_sub(expected_due, actual_due))
            if due_diff > Decimal("0.01"):
                discrepancies.append(
                    f"Amount due discrepancy: calculated {expected_due} != recorded {actual_due}"
                )
                total_discrepancy_loss = money_add(total_discrepancy_loss, due_diff)

        except Exception as e:
            discrepancies.append(f"Calculation engine exception: {str(e)}")

    # 5. Internal consistency fallback (subtotal - discount + tax == total)
    internal_expected_total = round_money(money_add(money_sub(actual_subtotal, actual_discount), actual_tax))
    if abs(money_sub(internal_expected_total, actual_total)) > Decimal("0.01"):
        diff = abs(money_sub(internal_expected_total, actual_total))
        discrepancies.append(
            f"Arithmetic ledger error: subtotal ({actual_subtotal}) - discount ({actual_discount}) + tax ({actual_tax}) = {internal_expected_total}, but total is {actual_total}"
        )
        total_discrepancy_loss = money_add(total_discrepancy_loss, diff)

    is_valid = len(discrepancies) == 0
    notes = "; ".join(discrepancies) if discrepancies else "Invoice verified: all arithmetic and tax schedules balance."

    # Update ORM model attributes if requested and available
    if update_model and hasattr(invoice, "is_audited"):
        invoice.is_audited = is_valid
        if hasattr(invoice, "audit_discrepancy_notes"):
            invoice.audit_discrepancy_notes = notes if not is_valid else None

    return AuditResult(
        is_valid=is_valid,
        invoice_number=inv_num,
        invoice_id=inv_id,
        discrepancy_amount=round_money(total_discrepancy_loss),
        discrepancies=discrepancies,
        expected_subtotal=expected_subtotal,
        actual_subtotal=actual_subtotal,
        expected_discount=expected_discount,
        actual_discount=actual_discount,
        expected_tax=expected_tax,
        actual_tax=actual_tax,
        expected_total=expected_total,
        actual_total=actual_total,
        expected_amount_due=expected_due,
        actual_amount_due=actual_due,
        notes=notes,
    )


def audit_invoices_batch(
    invoices: List[Any],
    tax_rules_map: Optional[Dict[int, Any]] = None,
    discounts_map: Optional[Dict[int, Any]] = None,
) -> List[AuditResult]:
    """
    Audits a batch of invoices, resolving foreign references where provided.
    """
    t_map = tax_rules_map or {}
    d_map = discounts_map or {}
    results = []
    for inv in invoices:
        tax_id = _get_val(inv, "tax_rule_id")
        disc_id = _get_val(inv, "discount_id")
        t_rules = [t_map[tax_id]] if tax_id in t_map else None
        d_obj = d_map.get(disc_id)
        results.append(audit_invoice(inv, tax_rules=t_rules, discount_obj=d_obj))
    return results
