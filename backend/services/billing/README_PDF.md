# SubscriptIQ: Professional PDF Invoice Generator

The `invoice_pdf_service` is an enterprise-grade, ReportLab-powered document generation engine designed for SubscriptIQ. It converts structured billing data into publication-ready, multi-page financial PDFs.

---

## 1. Key Capabilities

* **Modern SaaS Layout:** Styled using SubscriptIQ's corporate palette (Dark Navy `#0F172A`, Cerulean Blue `#007BA7`, Slate borders).
* **Automatic Multi-Page Handling:** Seamlessly flows item tables across multiple pages without clipping, overlapping, or orphan totals blocks (`KeepTogether` & `NumberedCanvas`).
* **Dynamic Status Badging:** Renders styled badges for `DRAFT`, `ISSUED`, `PAID`, `PARTIALLY_PAID`, `OVERDUE`, `VOID`, and `CANCELLED`.
* **Strict Financial Validation:** Refuses to generate PDFs if subtotal, discounts, taxable amounts, or taxes fail mathematical invariant checks.
* **Dual Output Modes:** Supports saving directly to disk or streaming binary PDF buffers (`io.BytesIO`) for fast HTTP streaming.

---

## 2. Required Input Structure

All amounts strictly use `Decimal` with `ROUND_HALF_UP` quantization (`0.01`).

```python
from datetime import date
from decimal import Decimal
from backend.services.billing.invoice_pdf_service import (
    BusinessInfo,
    CustomerInfo,
    InvoiceItemData,
    TaxBreakdownItem,
    InvoiceData,
    generate_invoice_pdf,
)

# 1. Define customer
customer = CustomerInfo(
    name="Jane Doe",
    email="jane.doe@example.com",
    company_name="Acme Solutions Ltd",
    billing_address="123 Innovation Boulevard, Suite 500, Austin, TX 78701",
    tax_id="US-TX-998877",
    customer_id=101,
)

# 2. Define line items
items = [
    InvoiceItemData(
        description="Enterprise Subscription Plan (Monthly)",
        quantity=Decimal("1.00"),
        unit_price=Decimal("199.00"),
        discount_amount=Decimal("0.00"),
        line_total=Decimal("199.00"),
    ),
    InvoiceItemData(
        description="Dedicated Support Add-on",
        quantity=Decimal("1.00"),
        unit_price=Decimal("50.00"),
        discount_amount=Decimal("10.00"),
        line_total=Decimal("40.00"),
    ),
]

# 3. Assemble invoice payload
invoice = InvoiceData(
    invoice_number="INV-2026-000101",
    issue_date=date(2026, 11, 1),
    due_date=date(2026, 11, 16),
    status="issued",
    currency="USD",
    billing_period_start=date(2026, 11, 1),
    billing_period_end=date(2026, 11, 30),
    customer=customer,
    business=BusinessInfo(),  # Defaults to SubscriptIQ corporate details
    items=items,
    subtotal=Decimal("249.00"),
    item_discounts=Decimal("10.00"),
    invoice_discount=Decimal("0.00"),
    total_discount=Decimal("10.00"),
    taxable_amount=Decimal("239.00"),
    tax_amount=Decimal("43.02"),
    tax_breakdown=[
        TaxBreakdownItem(name="State Tax", rate_percentage=Decimal("18.00"), tax_amount=Decimal("43.02"))
    ],
    total_amount=Decimal("282.02"),
    amount_paid=Decimal("0.00"),
    amount_due=Decimal("282.02"),
    notes="Net 15 payment terms. Thank you for your business.",
    payment_instructions="ACH transfer to SubscriptIQ. Routing: 121000358, Account: 9876543210.",
)
```

---

## 3. How to Generate an Invoice PDF

### Option A: Save to File
```python
# Saves to specified destination or defaults to backend/storage/invoices/<invoice_number>.pdf
file_path = generate_invoice_pdf(invoice, output_destination="invoices/INV-2026-000101.pdf")
print("Saved to:", file_path)
```

### Option B: Stream via Buffer (for Web APIs)
```python
import io

pdf_buffer = io.BytesIO()
generate_invoice_pdf(invoice, output_destination=pdf_buffer)
pdf_bytes = pdf_buffer.getvalue()
```

---

## 4. Default Storage Location

When `output_destination` is omitted or set to `None`, files are automatically persisted to:
```text
backend/storage/invoices/<invoice_number>.pdf
```
Directories are created automatically if they do not exist.

---

## 5. FastAPI Integration Blueprint

When Member 2 completes the core API routes, the service plugs into a FastAPI endpoint with zero modifications:

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_user
from backend.services.billing.invoice_pdf_service import generate_invoice_pdf
import io

router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])

@router.get("/{invoice_id}/download")
def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # Security: Verify tenant/user ownership
    if invoice.customer.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Map SQLAlchemy model to InvoiceData
    invoice_payload = map_db_model_to_invoice_data(invoice)
    
    # Generate in-memory PDF
    buf = io.BytesIO()
    generate_invoice_pdf(invoice_payload, output_destination=buf)
    
    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"'
        },
    )
```
