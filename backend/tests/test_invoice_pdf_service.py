"""
Unit Tests for Professional PDF Invoice Generator (backend/services/billing/invoice_pdf_service.py).
"""

import io
import os
import tempfile
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import pytest

from backend.services.billing.invoice_pdf_service import (
    BusinessInfo,
    CustomerInfo,
    InvoiceData,
    InvoiceItemData,
    TaxBreakdownItem,
    format_currency,
    generate_invoice_pdf,
    validate_invoice_data,
)


@pytest.fixture
def sample_customer() -> CustomerInfo:
    return CustomerInfo(
        name="Sarah Jenkins",
        email="sarah.jenkins@acmecorp.com",
        company_name="Acme Global Corporation",
        billing_address="456 Tech Parkway, Suite 200, Austin, TX 78701",
        tax_id="US-TX-998877",
        customer_id=104,
    )


@pytest.fixture
def sample_invoice_data(sample_customer: CustomerInfo) -> InvoiceData:
    issue = date(2026, 11, 1)
    due = date(2026, 11, 16)
    period_start = date(2026, 11, 1)
    period_end = date(2026, 11, 30)

    # 2 items:
    # Item 1: 1 * 100.00 - 10.00 = 90.00
    # Item 2: 2 * 25.00  - 0.00  = 50.00
    # Subtotal: 150.00
    # Item Discounts: 10.00
    # Invoice Discount: 20.00
    # Total Discount: 30.00
    # Taxable: 150.00 - 30.00 = 120.00
    # Tax: 18% on 120.00 = 21.60
    # Total Amount: 120.00 + 21.60 = 141.60
    # Amount Paid: 50.00
    # Amount Due: 91.60
    items = [
        InvoiceItemData(
            description="Pro Subscription Plan (Monthly)",
            quantity=Decimal("1.00"),
            unit_price=Decimal("100.00"),
            discount_amount=Decimal("10.00"),
            line_total=Decimal("90.00"),
        ),
        InvoiceItemData(
            description="Additional Team Member Seats",
            quantity=Decimal("2.00"),
            unit_price=Decimal("25.00"),
            discount_amount=Decimal("0.00"),
            line_total=Decimal("50.00"),
        ),
    ]

    taxes = [
        TaxBreakdownItem(name="State Tax", rate_percentage=Decimal("18.00"), tax_amount=Decimal("21.60"))
    ]

    return InvoiceData(
        invoice_number="INV-2026-001042",
        issue_date=issue,
        due_date=due,
        status="partially_paid",
        currency="USD",
        billing_period_start=period_start,
        billing_period_end=period_end,
        customer=sample_customer,
        business=BusinessInfo(),
        items=items,
        subtotal=Decimal("150.00"),
        item_discounts=Decimal("10.00"),
        invoice_discount=Decimal("20.00"),
        total_discount=Decimal("30.00"),
        taxable_amount=Decimal("120.00"),
        tax_amount=Decimal("21.60"),
        tax_breakdown=taxes,
        total_amount=Decimal("141.60"),
        amount_paid=Decimal("50.00"),
        amount_due=Decimal("91.60"),
        notes="Net 15 payment terms. Thank you for choosing SubscriptIQ.",
        payment_instructions="Wire transfer to SubscriptIQ Silicon Valley Bank. Account: 987654321.",
    )


class TestInvoicePDFGeneration:
    def test_successful_pdf_file_generation(self, sample_invoice_data: InvoiceData):
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_pdf = Path(tmp_dir) / "test_invoice.pdf"
            result_path = generate_invoice_pdf(sample_invoice_data, output_destination=target_pdf)

            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 1000

            # Verify PDF magic bytes
            with open(result_path, "rb") as f:
                header = f.read(5)
                assert header == b"%PDF-"

    def test_bytes_io_buffer_generation(self, sample_invoice_data: InvoiceData):
        buf = io.BytesIO()
        result = generate_invoice_pdf(sample_invoice_data, output_destination=buf)

        assert result == "buffer"
        buf.seek(0)
        content = buf.read()
        assert len(content) > 1000
        assert content.startswith(b"%PDF-")

    @pytest.mark.parametrize("status", ["draft", "issued", "paid", "partially_paid", "overdue", "void", "cancelled"])
    def test_all_invoice_statuses(self, sample_invoice_data: InvoiceData, status: str):
        sample_invoice_data.status = status
        with tempfile.TemporaryDirectory() as tmp_dir:
            target_pdf = Path(tmp_dir) / f"invoice_{status}.pdf"
            path = generate_invoice_pdf(sample_invoice_data, output_destination=target_pdf)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 1000

    def test_missing_optional_customer_fields(self, sample_invoice_data: InvoiceData):
        minimal_customer = CustomerInfo(
            name="John Doe",
            email="john.doe@example.com",
            company_name=None,
            billing_address=None,
            tax_id=None,
            customer_id=None,
        )
        sample_invoice_data.customer = minimal_customer

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_pdf = Path(tmp_dir) / "minimal_customer.pdf"
            path = generate_invoice_pdf(sample_invoice_data, output_destination=target_pdf)
            assert os.path.exists(path)
            assert os.path.getsize(path) > 1000

    def test_multi_page_long_invoice(self, sample_invoice_data: InvoiceData):
        # Create 45 line items to force multi-page rendering
        long_items = []
        total_subtotal = Decimal("0.00")
        for i in range(1, 46):
            price = Decimal("10.00")
            qty = Decimal("1.00")
            item_total = price * qty
            total_subtotal += item_total
            long_items.append(
                InvoiceItemData(
                    description=f"Automated Enterprise Feature Line Item #{i}",
                    quantity=qty,
                    unit_price=price,
                    discount_amount=Decimal("0.00"),
                    line_total=item_total,
                )
            )

        sample_invoice_data.items = long_items
        sample_invoice_data.subtotal = total_subtotal
        sample_invoice_data.item_discounts = Decimal("0.00")
        sample_invoice_data.invoice_discount = Decimal("0.00")
        sample_invoice_data.total_discount = Decimal("0.00")
        sample_invoice_data.taxable_amount = total_subtotal
        sample_invoice_data.tax_amount = Decimal("0.00")
        sample_invoice_data.tax_breakdown = []
        sample_invoice_data.total_amount = total_subtotal
        sample_invoice_data.amount_paid = Decimal("0.00")
        sample_invoice_data.amount_due = total_subtotal

        with tempfile.TemporaryDirectory() as tmp_dir:
            target_pdf = Path(tmp_dir) / "multipage_invoice.pdf"
            path = generate_invoice_pdf(sample_invoice_data, output_destination=target_pdf)
            assert os.path.exists(path)
            # Long invoice will be significantly larger in file size
            assert os.path.getsize(path) > 5000

    def test_default_storage_fallback(self, sample_invoice_data: InvoiceData):
        # When output_destination is None, generates into backend/storage/invoices/
        path_str = generate_invoice_pdf(sample_invoice_data, output_destination=None)
        assert os.path.exists(path_str)
        assert path_str.endswith(".pdf")
        assert "storage" in path_str
        # Clean up generated file
        os.remove(path_str)


class TestCurrencyFormatting:
    def test_common_currencies(self):
        assert format_currency("1234.50", "USD") == "$1,234.50"
        assert format_currency("99.99", "EUR") == "€99.99"
        assert format_currency("500", "GBP") == "£500.00"
        assert format_currency("25000.75", "INR") == "₹25,000.75"
        assert format_currency("100.00", "CAD") == "CA$100.00"
        assert format_currency("50.00", "XYZ") == "XYZ 50.00"

    def test_zero_amount(self):
        assert format_currency(Decimal("0.00"), "USD") == "$0.00"


class TestInvoiceValidation:
    def test_missing_invoice_number_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.invoice_number = ""
        with pytest.raises(ValueError, match="Invoice number is required"):
            validate_invoice_data(sample_invoice_data)

    def test_invalid_status_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.status = "unknown_status"
        with pytest.raises(ValueError, match="Invalid invoice status"):
            validate_invoice_data(sample_invoice_data)

    def test_due_date_before_issue_date_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.due_date = sample_invoice_data.issue_date - timedelta(days=1)
        with pytest.raises(ValueError, match="due_date .* cannot be earlier than issue_date"):
            validate_invoice_data(sample_invoice_data)

    def test_billing_period_invalid_range_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.billing_period_start = date(2026, 11, 30)
        sample_invoice_data.billing_period_end = date(2026, 11, 1)
        with pytest.raises(ValueError, match="billing_period_end .* cannot be earlier"):
            validate_invoice_data(sample_invoice_data)

    def test_empty_customer_name_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.customer.name = "   "
        with pytest.raises(ValueError, match="Customer name is required"):
            validate_invoice_data(sample_invoice_data)

    def test_invalid_customer_email_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.customer.email = "not_an_email"
        with pytest.raises(ValueError, match="Valid customer email is required"):
            validate_invoice_data(sample_invoice_data)

    def test_empty_items_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.items = []
        with pytest.raises(ValueError, match="must contain at least one line item"):
            validate_invoice_data(sample_invoice_data)

    def test_negative_item_quantity_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.items[0].quantity = Decimal("-1.00")
        with pytest.raises(ValueError, match="quantity must be positive"):
            validate_invoice_data(sample_invoice_data)

    def test_subtotal_mismatch_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.subtotal = Decimal("9999.00")
        with pytest.raises(ValueError, match="Invoice subtotal mismatch"):
            validate_invoice_data(sample_invoice_data)

    def test_total_mismatch_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.total_amount = Decimal("5000.00")
        with pytest.raises(ValueError, match="Invoice total mismatch"):
            validate_invoice_data(sample_invoice_data)

    def test_amount_due_mismatch_raises_value_error(self, sample_invoice_data: InvoiceData):
        sample_invoice_data.amount_due = Decimal("0.00")  # Should be 91.60
        with pytest.raises(ValueError, match="Amount due mismatch"):
            validate_invoice_data(sample_invoice_data)
