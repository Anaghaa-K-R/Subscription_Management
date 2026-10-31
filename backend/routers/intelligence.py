"""
FastAPI Router for AI Revenue Intelligence in SubscriptIQ.

Exposes RESTful endpoints for:
- GET  /api/ai/forecast       - Predictive 6-month revenue forecasting (NumPy/Pandas)
- GET  /api/ai/leakage-alerts - 6-vector automated revenue leakage detection & deduplication
- GET  /api/ai/health-score   - Composite 0-100 executive business health index & recommendations
- GET  /api/ai/churn-risk     - Multi-factor customer churn risk scoring & retention playbooks
- POST /api/ai/audit-invoice  - Mathematical and regulatory invoice integrity verification
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

try:
    from backend.database import get_db
    from backend.models import (
        Customer,
        Subscription,
        Invoice,
        InvoiceItem,
        Payment,
        Discount,
        TaxRule,
        RevenueLeakageAlert,
        BusinessHealthSnapshot,
    )
    from backend.services.intelligence import (
        forecast_revenue,
        generate_forecast_from_invoices,
        detect_revenue_leakage,
        assess_customer_churn_risk,
        assess_cohort_churn_risk,
        summarize_churn_risks,
        audit_invoice,
        calculate_business_health_score,
    )
    from backend.services.finance.money_utils import to_decimal
except ImportError:
    from database import get_db
    from models import (
        Customer,
        Subscription,
        Invoice,
        InvoiceItem,
        Payment,
        Discount,
        TaxRule,
        RevenueLeakageAlert,
        BusinessHealthSnapshot,
    )
    from services.intelligence import (
        forecast_revenue,
        generate_forecast_from_invoices,
        detect_revenue_leakage,
        assess_customer_churn_risk,
        assess_cohort_churn_risk,
        summarize_churn_risks,
        audit_invoice,
        calculate_business_health_score,
    )
    from services.finance.money_utils import to_decimal


router = APIRouter(prefix="/api/ai", tags=["AI Revenue Intelligence"])


class AuditInvoiceRequest(BaseModel):
    """Payload for auditing a specific invoice or triggering a batch audit."""
    invoice_id: Optional[int] = Field(None, description="Optional ID of specific invoice to audit")
    update_model: bool = Field(True, description="Persist audit verification status to database")


@router.get("/forecast", summary="6-Month Revenue Forecast")
def get_revenue_forecast(
    months_ahead: int = Query(6, ge=1, le=24, description="Number of future months to forecast"),
    db: Session = Depends(get_db),
):
    """
    Computes time-series revenue forecasts using historical invoice revenue.
    Gracefully handles empty or single-point historical data.
    """
    invoices = db.query(Invoice).all()
    if not invoices:
        result = forecast_revenue([], months_ahead=months_ahead)
    else:
        result = generate_forecast_from_invoices(invoices, months_ahead=months_ahead)

    return {
        "status": "success",
        **result.to_dict(),
    }


@router.get("/leakage-alerts", summary="Active Revenue Leakage Anomaly Alerts")
def get_leakage_alerts(
    status_filter: Optional[str] = Query(None, description="Optional filter by alert status ('open', 'resolved', 'dismissed')"),
    auto_detect: bool = Query(True, description="Run detection and persist newly found alerts"),
    db: Session = Depends(get_db),
):
    """
    Detects and returns revenue leakage anomalies across 6 vectors:
    unbilled subscriptions, duplicate invoices, expired discounts,
    overdue uncollected balances, missing renewals, and reconciliation gaps.
    Prevents duplicate alert creation in the database.
    """
    if auto_detect:
        subscriptions = db.query(Subscription).all()
        invoices = db.query(Invoice).all()
        payments = db.query(Payment).all()
        discounts = db.query(Discount).all()

        detected = detect_revenue_leakage(
            subscriptions=subscriptions,
            invoices=invoices,
            payments=payments,
            discounts=discounts,
            as_of_date=date.today(),
        )

        # Retrieve existing open alerts to prevent duplication
        existing_alerts = (
            db.query(RevenueLeakageAlert)
            .filter(RevenueLeakageAlert.status.in_(["open", "investigating"]))
            .all()
        )
        existing_keys = {
            (a.leakage_type, a.subscription_id, a.invoice_id, a.customer_id)
            for a in existing_alerts
        }

        new_count = 0
        for alert_res in detected:
            key = (
                alert_res.leakage_type,
                alert_res.subscription_id,
                alert_res.invoice_id,
                alert_res.customer_id,
            )
            if key not in existing_keys:
                alert_model = alert_res.to_alert_model()
                db.add(alert_model)
                existing_keys.add(key)
                new_count += 1

        if new_count > 0:
            db.commit()

    query = db.query(RevenueLeakageAlert)
    if status_filter:
        query = query.filter(RevenueLeakageAlert.status == status_filter)

    alerts = query.order_by(RevenueLeakageAlert.detected_at.desc()).all()
    open_loss = sum(
        (to_decimal(a.estimated_loss) for a in alerts if a.status in ("open", "investigating")),
        Decimal("0.00"),
    )

    return {
        "status": "success",
        "total_alerts": len(alerts),
        "total_estimated_loss": float(open_loss),
        "alerts": [
            {
                "id": a.id,
                "leakage_type": a.leakage_type,
                "severity": a.severity,
                "estimated_loss": float(a.estimated_loss),
                "subscription_id": a.subscription_id,
                "invoice_id": a.invoice_id,
                "customer_id": a.customer_id,
                "description": a.description,
                "recommended_action": a.recommended_action,
                "status": a.status,
                "detected_at": a.detected_at.isoformat() if a.detected_at else None,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            }
            for a in alerts
        ],
    }


@router.get("/health-score", summary="Executive Business Health Score (0-100)")
def get_business_health_score(
    db: Session = Depends(get_db),
):
    """
    Computes an executive 0-100 business health score from operational telemetry:
    payment success rate, overdue receivables, subscriber churn, and MRR growth.
    Records or updates today's snapshot in business_health_snapshots.
    """
    subscriptions = db.query(Subscription).all()
    invoices = db.query(Invoice).all()
    payments = db.query(Payment).all()

    today = date.today()
    prev_snapshot = (
        db.query(BusinessHealthSnapshot)
        .filter(BusinessHealthSnapshot.snapshot_date < today)
        .order_by(BusinessHealthSnapshot.snapshot_date.desc())
        .first()
    )
    previous_mrr = prev_snapshot.mrr if prev_snapshot else None

    result = calculate_business_health_score(
        subscriptions=subscriptions,
        invoices=invoices,
        payments=payments,
        previous_mrr=previous_mrr,
        as_of_date=today,
    )

    today_snapshot = (
        db.query(BusinessHealthSnapshot)
        .filter(BusinessHealthSnapshot.snapshot_date == today)
        .first()
    )
    if today_snapshot:
        today_snapshot.mrr = result.mrr
        today_snapshot.arr = result.arr
        today_snapshot.active_subscriptions_count = result.active_subscriptions_count
        today_snapshot.total_outstanding_amount = result.total_outstanding_amount
        today_snapshot.overdue_invoices_count = result.overdue_invoices_count
        today_snapshot.health_score = to_decimal(result.health_score)
    else:
        new_snap = result.to_snapshot_model(snapshot_date=today)
        db.add(new_snap)
    db.commit()

    return {
        "status": "success",
        **result.to_dict(),
    }


@router.get("/churn-risk", summary="Customer Churn Risk Scoring & Playbooks")
def get_churn_risk(
    customer_id: Optional[int] = Query(None, description="Optional ID to inspect a specific customer"),
    risk_category: Optional[str] = Query(None, description="Filter cohort by category ('low', 'medium', 'high', 'critical')"),
    db: Session = Depends(get_db),
):
    """
    Assesses customer churn risk (0-100) based on failed payments, overdue invoices,
    disabled auto-renew, and contract tenure. Returns targeted retention action playbooks.
    """
    subscriptions = db.query(Subscription).all()
    invoices = db.query(Invoice).all()
    payments = db.query(Payment).all()

    if customer_id is not None:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID {customer_id} not found.",
            )
        cust_subs = [s for s in subscriptions if s.customer_id == customer_id]
        cust_invs = [i for i in invoices if i.customer_id == customer_id]
        cust_pays = [p for p in payments if p.customer_id == customer_id]

        assessment = assess_customer_churn_risk(
            customer=customer,
            subscriptions=cust_subs,
            invoices=cust_invs,
            payments=cust_pays,
            as_of_date=date.today(),
        )
        return {
            "status": "success",
            "assessment": assessment.to_dict(),
        }

    customers = db.query(Customer).all()
    if not customers:
        return {
            "status": "success",
            "summary": {
                "total_customers": 0,
                "average_risk_score": 0.0,
                "risk_distribution": {"low": 0, "medium": 0, "high": 0, "critical": 0},
                "high_risk_customers_count": 0,
            },
            "assessments": [],
        }

    cohort = assess_cohort_churn_risk(
        customers=customers,
        subscriptions=subscriptions,
        invoices=invoices,
        payments=payments,
        as_of_date=date.today(),
    )
    summary = summarize_churn_risks(cohort)

    if risk_category:
        cohort = [c for c in cohort if c.risk_category == risk_category.lower().strip()]

    return {
        "status": "success",
        "summary": summary,
        "assessments": [c.to_dict() for c in cohort],
    }


@router.post("/audit-invoice", summary="Intelligent Invoice Arithmetic & Compliance Audit")
def post_audit_invoice(
    payload: Optional[AuditInvoiceRequest] = None,
    invoice_id: Optional[int] = Query(None, description="Optional ID passed via query param"),
    db: Session = Depends(get_db),
):
    """
    Recalculates invoice line-item math, taxes, and discounts using InvoiceCalculator.
    Detects subtotal, discount, tax, and grand total discrepancies, and rejects negative amounts.
    """
    target_id = None
    update_model = True
    if payload is not None:
        target_id = payload.invoice_id
        update_model = payload.update_model
    if target_id is None and invoice_id is not None:
        target_id = invoice_id

    if target_id is not None:
        invoice = (
            db.query(Invoice)
            .options(
                joinedload(Invoice.items),
                joinedload(Invoice.tax_rule),
                joinedload(Invoice.discount),
                joinedload(Invoice.customer),
            )
            .filter(Invoice.id == target_id)
            .first()
        )
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice with ID {target_id} not found.",
            )

        is_exempt = invoice.customer.is_tax_exempt if invoice.customer else False
        audit_res = audit_invoice(
            invoice=invoice,
            items=invoice.items,
            tax_rules=[invoice.tax_rule] if invoice.tax_rule else None,
            discount_obj=invoice.discount,
            is_tax_exempt=is_exempt,
            update_model=update_model,
        )

        if update_model:
            db.commit()
            db.refresh(invoice)

        return {
            "status": "success",
            "audit": audit_res.to_dict(),
        }

    # Batch audit of all invoices
    invoices = (
        db.query(Invoice)
        .options(
            joinedload(Invoice.items),
            joinedload(Invoice.tax_rule),
            joinedload(Invoice.discount),
            joinedload(Invoice.customer),
        )
        .all()
    )

    if not invoices:
        return {
            "status": "success",
            "message": "No invoices available in the system.",
            "audited_count": 0,
            "valid_count": 0,
            "discrepancy_count": 0,
            "results": [],
        }

    results = []
    valid_count = 0
    discrepancy_count = 0

    for inv in invoices:
        is_exempt = inv.customer.is_tax_exempt if inv.customer else False
        res = audit_invoice(
            invoice=inv,
            items=inv.items,
            tax_rules=[inv.tax_rule] if inv.tax_rule else None,
            discount_obj=inv.discount,
            is_tax_exempt=is_exempt,
            update_model=update_model,
        )
        if res.is_valid:
            valid_count += 1
        else:
            discrepancy_count += 1
        results.append(res.to_dict())

    if update_model:
        db.commit()

    return {
        "status": "success",
        "audited_count": len(results),
        "valid_count": valid_count,
        "discrepancy_count": discrepancy_count,
        "results": results,
    }
