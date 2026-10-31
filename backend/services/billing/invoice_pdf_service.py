"""
Professional PDF Invoice Generator for SubscriptIQ.

Uses ReportLab to generate enterprise-grade SaaS invoices with:
- SubscriptIQ corporate branding and styling.
- Comprehensive customer and billing information.
- Itemized line items table with multi-page automatic wrapping.
- Precision Decimal financial summary (subtotal, discounts, taxes, balance due).
- Dynamic status badges (DRAFT, ISSUED, PARTIALLY_PAID, PAID, OVERDUE, VOID).
- Multi-page page numbering ("Page X of Y") via NumberedCanvas.
- Strict financial validation before rendering.
"""

import os
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from backend.services.finance.money_utils import (
    ZERO_MONEY,
    MoneyType,
    round_money,
    to_decimal,
)


# ==============================================================================
# DATA STRUCTURES
# ==============================================================================

@dataclass
class BusinessInfo:
    """SubscriptIQ Business/Issuer Information."""
    name: str = "SubscriptIQ Technologies Inc."
    tagline: str = "AI-Powered Subscription & Recurring Revenue Management"
    email: str = "billing@subscriptiq.io"
    phone: str = "+1 (800) 555-SUBS"
    website: str = "https://subscriptiq.io"
    address_line1: str = "100 Innovation Way, Suite 400"
    city_state_zip: str = "San Francisco, CA 94105"
    country: str = "United States"
    tax_id: Optional[str] = "US-EIN-98-7654321"


@dataclass
class CustomerInfo:
    """Customer Billing Profile."""
    name: str
    email: str
    company_name: Optional[str] = None
    billing_address: Optional[str] = None
    tax_id: Optional[str] = None
    customer_id: Optional[Union[int, str]] = None


@dataclass
class InvoiceItemData:
    """Single itemized line item on the invoice."""
    description: str
    quantity: MoneyType
    unit_price: MoneyType
    discount_amount: MoneyType = Decimal("0.00")
    line_total: Optional[MoneyType] = None


@dataclass
class TaxBreakdownItem:
    """Itemized tax detail."""
    name: str
    rate_percentage: MoneyType
    tax_amount: MoneyType


@dataclass
class InvoiceData:
    """Comprehensive input payload for PDF Invoice generation."""
    invoice_number: str
    issue_date: date
    due_date: date
    status: str
    currency: str = "USD"
    billing_period_start: Optional[date] = None
    billing_period_end: Optional[date] = None
    customer: CustomerInfo = None  # type: ignore
    business: BusinessInfo = field(default_factory=BusinessInfo)
    items: List[InvoiceItemData] = field(default_factory=list)
    subtotal: MoneyType = Decimal("0.00")
    item_discounts: MoneyType = Decimal("0.00")
    invoice_discount: MoneyType = Decimal("0.00")
    total_discount: MoneyType = Decimal("0.00")
    taxable_amount: MoneyType = Decimal("0.00")
    tax_amount: MoneyType = Decimal("0.00")
    tax_breakdown: List[TaxBreakdownItem] = field(default_factory=list)
    total_amount: MoneyType = Decimal("0.00")
    amount_paid: MoneyType = Decimal("0.00")
    amount_due: MoneyType = Decimal("0.00")
    notes: Optional[str] = None
    payment_instructions: Optional[str] = None


# ==============================================================================
# CURRENCY & NUMBER FORMATTING
# ==============================================================================

CURRENCY_SYMBOLS: Dict[str, str] = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "INR": "₹",
    "CAD": "CA$",
    "AUD": "AU$",
    "JPY": "¥",
    "SGD": "SG$",
}


def format_currency(amount: MoneyType, currency: str = "USD") -> str:
    """
    Format a Decimal monetary value with standard thousand-separators and currency symbol.

    Examples:
        format_currency(1234.5, "USD") -> "$1,234.50"
        format_currency(2500, "INR")   -> "₹2,500.00"
        format_currency(100, "XYZ")    -> "XYZ 100.00"
    """
    dec = round_money(amount)
    curr_upper = currency.upper().strip()
    formatted_num = f"{dec:,.2f}"

    if curr_upper in CURRENCY_SYMBOLS:
        return f"{CURRENCY_SYMBOLS[curr_upper]}{formatted_num}"
    return f"{curr_upper} {formatted_num}"


# ==============================================================================
# VALIDATION ENGINE
# ==============================================================================

VALID_STATUSES = {
    "draft",
    "issued",
    "partially_paid",
    "paid",
    "overdue",
    "cancelled",
    "void",
}


def validate_invoice_data(data: InvoiceData) -> None:
    """
    Strictly validate invoice data integrity before rendering.

    Raises:
        ValueError: If any required field is missing, dates are invalid,
                    or financial totals fail mathematical invariants.
    """
    # 1. Invoice Identification
    if not data.invoice_number or not str(data.invoice_number).strip():
        raise ValueError("Invoice number is required.")

    status_clean = str(data.status).lower().strip()
    if status_clean not in VALID_STATUSES:
        raise ValueError(
            f"Invalid invoice status: '{data.status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}."
        )

    # 2. Date Validations
    if not isinstance(data.issue_date, date):
        raise ValueError(f"issue_date must be a datetime.date instance, got {type(data.issue_date)}")
    if not isinstance(data.due_date, date):
        raise ValueError(f"due_date must be a datetime.date instance, got {type(data.due_date)}")
    if data.due_date < data.issue_date:
        raise ValueError(
            f"due_date ({data.due_date}) cannot be earlier than issue_date ({data.issue_date})."
        )

    if data.billing_period_start and data.billing_period_end:
        if data.billing_period_end < data.billing_period_start:
            raise ValueError(
                f"billing_period_end ({data.billing_period_end}) cannot be earlier than "
                f"billing_period_start ({data.billing_period_start})."
            )

    # 3. Customer Validations
    if not data.customer:
        raise ValueError("Customer information is required.")
    if not data.customer.name or not str(data.customer.name).strip():
        raise ValueError("Customer name is required.")
    if not data.customer.email or "@" not in str(data.customer.email):
        raise ValueError(f"Valid customer email is required, got '{getattr(data.customer, 'email', None)}'.")

    # 4. Item Validations
    if not data.items:
        raise ValueError("Invoice must contain at least one line item.")

    computed_subtotal = ZERO_MONEY
    computed_item_discounts = ZERO_MONEY

    for idx, item in enumerate(data.items, start=1):
        if not item.description or not str(item.description).strip():
            raise ValueError(f"Item #{idx} has an empty description.")

        qty = to_decimal(item.quantity)
        price = to_decimal(item.unit_price)
        disc = to_decimal(item.discount_amount)

        if qty <= 0:
            raise ValueError(f"Item #{idx} ('{item.description}') quantity must be positive, got {qty}.")
        if price < 0:
            raise ValueError(f"Item #{idx} ('{item.description}') unit price cannot be negative, got {price}.")
        if disc < 0:
            raise ValueError(f"Item #{idx} ('{item.description}') discount cannot be negative, got {disc}.")

        expected_line_total = round_money((qty * price) - disc)
        if item.line_total is not None:
            actual_line_total = round_money(item.line_total)
            if actual_line_total != expected_line_total:
                raise ValueError(
                    f"Item #{idx} line_total mismatch: expected {expected_line_total}, got {actual_line_total}."
                )

        computed_subtotal += round_money(qty * price)
        computed_item_discounts += round_money(disc)

    # 5. Financial Invariants
    subtotal = round_money(data.subtotal)
    if subtotal != computed_subtotal:
        raise ValueError(
            f"Invoice subtotal mismatch: items sum to {computed_subtotal}, but subtotal is {subtotal}."
        )

    item_discounts = round_money(data.item_discounts)
    if item_discounts != computed_item_discounts:
        raise ValueError(
            f"Item discounts mismatch: items discounts sum to {computed_item_discounts}, "
            f"but item_discounts is {item_discounts}."
        )

    invoice_discount = round_money(data.invoice_discount)
    total_discount = round_money(data.total_discount)
    expected_total_discount = item_discounts + invoice_discount
    if total_discount != expected_total_discount:
        raise ValueError(
            f"Total discount mismatch: expected {expected_total_discount}, got {total_discount}."
        )

    taxable_amount = round_money(data.taxable_amount)
    expected_taxable = max(ZERO_MONEY, subtotal - total_discount)
    if taxable_amount != expected_taxable:
        raise ValueError(
            f"Taxable amount mismatch: expected {expected_taxable}, got {taxable_amount}."
        )

    tax_amount = round_money(data.tax_amount)
    if tax_amount < 0:
        raise ValueError(f"Tax amount cannot be negative: {tax_amount}")

    total_amount = round_money(data.total_amount)
    expected_total = taxable_amount + tax_amount
    if total_amount != expected_total:
        raise ValueError(
            f"Invoice total mismatch: taxable ({taxable_amount}) + tax ({tax_amount}) = "
            f"{expected_total}, but total_amount is {total_amount}."
        )

    amount_paid = round_money(data.amount_paid)
    if amount_paid < 0:
        raise ValueError(f"amount_paid cannot be negative: {amount_paid}")

    amount_due = round_money(data.amount_due)
    expected_due = max(ZERO_MONEY, total_amount - amount_paid)
    if amount_due != expected_due:
        raise ValueError(
            f"Amount due mismatch: total ({total_amount}) - paid ({amount_paid}) = "
            f"{expected_due}, but amount_due is {amount_due}."
        )


# ==============================================================================
# NUMBERED CANVAS (MULTI-PAGE PAGE NUMBERING & FOOTER)
# ==============================================================================

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass ReportLab Canvas that computes total page count dynamically
    and renders 'Page X of Y' alongside the corporate footer on every page.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count: int) -> None:
        """Draw clean separator and pagination on page bottom."""
        page_width, _ = A4
        left_margin = 36
        right_margin = page_width - 36
        footer_y = 28

        self.saveState()

        # Divider line
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(left_margin, footer_y + 12, right_margin, footer_y + 12)

        # Brand tagline left
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(
            left_margin,
            footer_y,
            "SubscriptIQ — Manage Recurring Revenue. Predict Growth. Prevent Leakage.",
        )

        # Page numbering right
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(right_margin, footer_y, page_text)

        self.restoreState()


# ==============================================================================
# PDF BUILDER ENGINE
# ==============================================================================

STATUS_COLORS: Dict[str, Dict[str, str]] = {
    "paid": {"bg": "#DCFCE7", "text": "#166534", "border": "#86EFAC"},
    "partially_paid": {"bg": "#FEF3C7", "text": "#92400E", "border": "#FDE68A"},
    "overdue": {"bg": "#FEE2E2", "text": "#991B1B", "border": "#FCA5A5"},
    "issued": {"bg": "#DBEAFE", "text": "#1E40AF", "border": "#93C5FD"},
    "draft": {"bg": "#F1F5F9", "text": "#475569", "border": "#CBD5E1"},
    "cancelled": {"bg": "#F3F4F6", "text": "#6B7280", "border": "#D1D5DB"},
    "void": {"bg": "#F3F4F6", "text": "#6B7280", "border": "#D1D5DB"},
}


def _create_styles() -> Dict[str, ParagraphStyle]:
    """Initialize robust paragraph styles for invoice elements."""
    base_sheet = getSampleStyleSheet()

    styles = {
        "BrandTitle": ParagraphStyle(
            "BrandTitle",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=colors.HexColor("#0A0A0C"),
        ),
        "BrandTagline": ParagraphStyle(
            "BrandTagline",
            parent=base_sheet["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#007BA7"),
        ),
        "CompanyDetails": ParagraphStyle(
            "CompanyDetails",
            parent=base_sheet["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
        ),
        "InvoiceTitle": ParagraphStyle(
            "InvoiceTitle",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=25,
            alignment=2,  # Right aligned
            textColor=colors.HexColor("#0A0A0C"),
        ),
        "InvoiceMetaRight": ParagraphStyle(
            "InvoiceMetaRight",
            parent=base_sheet["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#334155"),
        ),
        "SectionHeader": ParagraphStyle(
            "SectionHeader",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B"),
        ),
        "CustomerName": ParagraphStyle(
            "CustomerName",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
        ),
        "CustomerDetails": ParagraphStyle(
            "CustomerDetails",
            parent=base_sheet["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#475569"),
        ),
        "TableHeader": ParagraphStyle(
            "TableHeader",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
        ),
        "TableHeaderRight": ParagraphStyle(
            "TableHeaderRight",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            alignment=2,
            textColor=colors.white,
        ),
        "TableHeaderCenter": ParagraphStyle(
            "TableHeaderCenter",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            alignment=1,
            textColor=colors.white,
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            parent=base_sheet["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1E293B"),
        ),
        "TableCellRight": ParagraphStyle(
            "TableCellRight",
            parent=base_sheet["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#1E293B"),
        ),
        "TableCellCenter": ParagraphStyle(
            "TableCellCenter",
            parent=base_sheet["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            alignment=1,
            textColor=colors.HexColor("#1E293B"),
        ),
        "SummaryLabel": ParagraphStyle(
            "SummaryLabel",
            parent=base_sheet["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#475569"),
        ),
        "SummaryValue": ParagraphStyle(
            "SummaryValue",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#0F172A"),
        ),
        "TotalLabel": ParagraphStyle(
            "TotalLabel",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=2,
            textColor=colors.HexColor("#0A0A0C"),
        ),
        "TotalValue": ParagraphStyle(
            "TotalValue",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            alignment=2,
            textColor=colors.HexColor("#007BA7"),
        ),
        "DueLabel": ParagraphStyle(
            "DueLabel",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            alignment=2,
            textColor=colors.HexColor("#0A0A0C"),
        ),
        "DueValue": ParagraphStyle(
            "DueValue",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=2,
            textColor=colors.HexColor("#DC2626"),  # Highlighted red
        ),
        "PaidLabel": ParagraphStyle(
            "PaidLabel",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#166534"),  # Green
        ),
        "PaidValue": ParagraphStyle(
            "PaidValue",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            alignment=2,
            textColor=colors.HexColor("#166534"),
        ),
        "NotesHeading": ParagraphStyle(
            "NotesHeading",
            parent=base_sheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B"),
        ),
        "NotesBody": ParagraphStyle(
            "NotesBody",
            parent=base_sheet["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
        ),
    }

    return styles


def generate_invoice_pdf(
    invoice_data: InvoiceData,
    output_destination: Optional[Union[str, Path, BinaryIO]] = None,
) -> str:
    """
    Generate an enterprise-grade PDF invoice from structured InvoiceData.

    Parameters:
        invoice_data: Fully populated and verified InvoiceData object.
        output_destination: Filepath (str/Path) or BytesIO/Binary buffer.
                            If None, defaults to `backend/storage/invoices/<invoice_number>.pdf`.

    Returns:
        String path of the generated PDF file (or 'buffer' if a stream was provided).

    Raises:
        ValueError: If invoice_data fails validation.
    """
    # 1. Strict Validation
    validate_invoice_data(invoice_data)

    # 2. Determine Output Destination
    target_path_str = ""
    target_dest: Any = output_destination

    if target_dest is None:
        storage_dir = Path("backend") / "storage" / "invoices"
        storage_dir.mkdir(parents=True, exist_ok=True)
        safe_num = invoice_data.invoice_number.replace("/", "_").replace("\\", "_")
        target_path = storage_dir / f"{safe_num}.pdf"
        target_dest = str(target_path)
        target_path_str = str(target_path.resolve())
    elif isinstance(target_dest, (str, Path)):
        p = Path(target_dest)
        p.parent.mkdir(parents=True, exist_ok=True)
        target_dest = str(p)
        target_path_str = str(p.resolve())
    else:
        target_path_str = "buffer"

    # 3. Document Template Setup (A4 Page: 595.27 x 841.89 pt)
    # Margins: 36 pt (0.5 inch). Printable width: 523.27 pt
    printable_width = 523.27
    doc = SimpleDocTemplate(
        target_dest,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=46,  # Leave room for NumberedCanvas footer
    )

    styles = _create_styles()
    story: List[Any] = []

    # ==========================================================================
    # HEADER: BRANDING & INVOICE META
    # ==========================================================================
    b = invoice_data.business
    status_key = invoice_data.status.lower().strip()
    status_palette = STATUS_COLORS.get(status_key, STATUS_COLORS["draft"])

    # Left: Brand Details
    brand_content = [
        Paragraph(b.name, styles["BrandTitle"]),
        Paragraph(b.tagline, styles["BrandTagline"]),
        Spacer(1, 4),
        Paragraph(f"{b.address_line1}, {b.city_state_zip}, {b.country}", styles["CompanyDetails"]),
        Paragraph(f"Email: {b.email} | Phone: {b.phone}", styles["CompanyDetails"]),
        Paragraph(f"Tax / VAT ID: {b.tax_id or 'N/A'}", styles["CompanyDetails"]),
    ]

    # Right: Invoice Title & Meta Table
    period_str = ""
    if invoice_data.billing_period_start and invoice_data.billing_period_end:
        period_str = f"{invoice_data.billing_period_start} to {invoice_data.billing_period_end}"

    # Status Badge cell
    status_badge_html = (
        f'<font color="{status_palette["text"]}">'
        f'<b>&nbsp;{invoice_data.status.upper().replace("_", " ")}&nbsp;</b>'
        f'</font>'
    )
    status_badge = Paragraph(status_badge_html, styles["TableCellCenter"])
    status_badge_table = Table([[status_badge]], colWidths=[90])
    status_badge_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(status_palette["bg"])),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(status_palette["border"])),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ])
    )

    meta_rows = [
        [Paragraph("INVOICE", styles["InvoiceTitle"]), ""],
        [Paragraph(f"<b>Invoice #:</b> {invoice_data.invoice_number}", styles["InvoiceMetaRight"]), ""],
        [status_badge_table, ""],
        [Paragraph(f"<b>Issue Date:</b> {invoice_data.issue_date}", styles["InvoiceMetaRight"]), ""],
        [Paragraph(f"<b>Due Date:</b> {invoice_data.due_date}", styles["InvoiceMetaRight"]), ""],
    ]
    if period_str:
        meta_rows.append(
            [Paragraph(f"<b>Billing Period:</b> {period_str}", styles["InvoiceMetaRight"]), ""]
        )

    # Header Master Table: Left (320 pt), Right (203 pt) -> 523 pt total
    header_table = Table(
        [
            [brand_content, Table(meta_rows, colWidths=[203, 0])]
        ],
        colWidths=[320, 203],
    )
    header_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    story.append(header_table)
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0"), spaceAfter=12))

    # ==========================================================================
    # BILLED TO & PAYMENT SUMMARY BOX
    # ==========================================================================
    c = invoice_data.customer
    customer_lines = [
        Paragraph("BILLED TO", styles["SectionHeader"]),
        Paragraph(c.name, styles["CustomerName"]),
    ]
    if c.company_name:
        customer_lines.append(Paragraph(c.company_name, styles["CustomerDetails"]))
    if c.billing_address:
        customer_lines.append(Paragraph(c.billing_address, styles["CustomerDetails"]))
    customer_lines.append(Paragraph(f"Email: {c.email}", styles["CustomerDetails"]))
    if c.tax_id:
        customer_lines.append(Paragraph(f"Tax / VAT ID: {c.tax_id}", styles["CustomerDetails"]))
    if c.customer_id:
        customer_lines.append(Paragraph(f"Customer ID: #{c.customer_id}", styles["CustomerDetails"]))

    # Summary Snapshot box (Right side)
    currency = invoice_data.currency
    balance_due_str = format_currency(invoice_data.amount_due, currency)
    total_str = format_currency(invoice_data.total_amount, currency)

    summary_box_data = [
        [Paragraph("Total Amount:", styles["SummaryLabel"]), Paragraph(total_str, styles["SummaryValue"])],
        [
            Paragraph("Amount Paid:", styles["SummaryLabel"]),
            Paragraph(format_currency(invoice_data.amount_paid, currency), styles["PaidValue"]),
        ],
        [Paragraph("Balance Due:", styles["DueLabel"]), Paragraph(balance_due_str, styles["DueValue"])],
    ]
    summary_box_table = Table(summary_box_data, colWidths=[90, 103])
    summary_box_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )

    billed_to_table = Table(
        [[customer_lines, summary_box_table]],
        colWidths=[320, 203],
    )
    billed_to_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )
    story.append(billed_to_table)
    story.append(Spacer(1, 14))

    # ==========================================================================
    # ITEMIZED BILLING TABLE
    # Total Width: 25 + 248 + 45 + 65 + 65 + 75 = 523 pt
    # ==========================================================================
    item_table_data = [
        [
            Paragraph("#", styles["TableHeaderCenter"]),
            Paragraph("Description", styles["TableHeader"]),
            Paragraph("Qty", styles["TableHeaderCenter"]),
            Paragraph("Unit Price", styles["TableHeaderRight"]),
            Paragraph("Discount", styles["TableHeaderRight"]),
            Paragraph("Amount", styles["TableHeaderRight"]),
        ]
    ]

    for idx, item in enumerate(invoice_data.items, start=1):
        qty_str = f"{to_decimal(item.quantity):.2f}".rstrip("0").rstrip(".")
        unit_str = format_currency(item.unit_price, currency)
        disc_str = format_currency(item.discount_amount, currency) if to_decimal(item.discount_amount) > 0 else "-"
        expected_line_total = (to_decimal(item.quantity) * to_decimal(item.unit_price)) - to_decimal(item.discount_amount)
        amount_str = format_currency(item.line_total if item.line_total is not None else expected_line_total, currency)

        item_table_data.append([
            Paragraph(str(idx), styles["TableCellCenter"]),
            Paragraph(item.description, styles["TableCell"]),
            Paragraph(qty_str, styles["TableCellCenter"]),
            Paragraph(unit_str, styles["TableCellRight"]),
            Paragraph(disc_str, styles["TableCellRight"]),
            Paragraph(amount_str, styles["TableCellRight"]),
        ])

    items_table = Table(
        item_table_data,
        colWidths=[25, 248, 45, 65, 65, 75],
        repeatRows=1,  # Repeats header on every page for multi-page invoices!
    )
    table_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),  # Dark Navy Slate Header
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]

    # Alternate row shading
    for r in range(1, len(item_table_data)):
        if r % 2 == 0:
            table_styles.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#F8FAFC")))

    items_table.setStyle(TableStyle(table_styles))
    story.append(items_table)
    story.append(Spacer(1, 12))

    # ==========================================================================
    # FINANCIAL SUMMARY & NOTES (KeepTogether prevents orphan total block)
    # Total Width: 270 (Notes) + 253 (Summary) = 523 pt
    # ==========================================================================
    notes_elements = []
    if invoice_data.notes:
        notes_elements.append(Paragraph("NOTES", styles["NotesHeading"]))
        notes_elements.append(Paragraph(invoice_data.notes, styles["NotesBody"]))
        notes_elements.append(Spacer(1, 6))

    payment_info = (
        invoice_data.payment_instructions
        or f"Please submit payments to {b.name}. Direct inquiries to {b.email}."
    )
    notes_elements.append(Paragraph("PAYMENT INSTRUCTIONS", styles["NotesHeading"]))
    notes_elements.append(Paragraph(payment_info, styles["NotesBody"]))

    # Financial Breakdown Rows
    summary_rows = [
        [
            Paragraph("Subtotal:", styles["SummaryLabel"]),
            Paragraph(format_currency(invoice_data.subtotal, currency), styles["SummaryValue"]),
        ]
    ]

    if to_decimal(invoice_data.item_discounts) > 0:
        summary_rows.append([
            Paragraph("Item Discounts:", styles["SummaryLabel"]),
            Paragraph(f"-{format_currency(invoice_data.item_discounts, currency)}", styles["SummaryValue"]),
        ])

    if to_decimal(invoice_data.invoice_discount) > 0:
        summary_rows.append([
            Paragraph("Invoice Discount:", styles["SummaryLabel"]),
            Paragraph(f"-{format_currency(invoice_data.invoice_discount, currency)}", styles["SummaryValue"]),
        ])

    if to_decimal(invoice_data.total_discount) > 0:
        summary_rows.append([
            Paragraph("Taxable Subtotal:", styles["SummaryLabel"]),
            Paragraph(format_currency(invoice_data.taxable_amount, currency), styles["SummaryValue"]),
        ])

    # Tax Breakdown Rows
    if invoice_data.tax_breakdown:
        for t_item in invoice_data.tax_breakdown:
            label = f"{t_item.name} ({to_decimal(t_item.rate_percentage):.2f}%):"
            summary_rows.append([
                Paragraph(label, styles["SummaryLabel"]),
                Paragraph(format_currency(t_item.tax_amount, currency), styles["SummaryValue"]),
            ])
    elif to_decimal(invoice_data.tax_amount) > 0:
        summary_rows.append([
            Paragraph("Tax:", styles["SummaryLabel"]),
            Paragraph(format_currency(invoice_data.tax_amount, currency), styles["SummaryValue"]),
        ])
    else:
        summary_rows.append([
            Paragraph("Tax:", styles["SummaryLabel"]),
            Paragraph(format_currency(ZERO_MONEY, currency), styles["SummaryValue"]),
        ])

    # Total Amount Highlight Row
    summary_rows.append([
        Paragraph("Total Amount:", styles["TotalLabel"]),
        Paragraph(format_currency(invoice_data.total_amount, currency), styles["TotalValue"]),
    ])

    # Payment Status Details
    if to_decimal(invoice_data.amount_paid) > 0:
        summary_rows.append([
            Paragraph("Amount Paid:", styles["PaidLabel"]),
            Paragraph(f"-{format_currency(invoice_data.amount_paid, currency)}", styles["PaidValue"]),
        ])

    summary_rows.append([
        Paragraph("Amount Due:", styles["DueLabel"]),
        Paragraph(format_currency(invoice_data.amount_due, currency), styles["DueValue"]),
    ])

    summary_table = Table(summary_rows, colWidths=[140, 113])
    summary_table_styles = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        # Highlight Total Amount row
        ("LINEBELOW", (0, -3), (1, -3), 1, colors.HexColor("#007BA7")),
        ("LINEABOVE", (0, -3), (1, -3), 1, colors.HexColor("#007BA7")),
    ]
    summary_table.setStyle(TableStyle(summary_table_styles))

    bottom_section_table = Table(
        [[notes_elements, summary_table]],
        colWidths=[270, 253],
    )
    bottom_section_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ])
    )

    story.append(KeepTogether(bottom_section_table))

    # 4. Build Document using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)

    return target_path_str
