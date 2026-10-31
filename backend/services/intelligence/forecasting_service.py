"""
AI Revenue Forecasting Engine for SubscriptIQ.

Uses NumPy and Pandas to analyze historical monthly recurring revenue and project
forward-looking trajectories for the next 6 months.

Features:
- Generates data contracts compatible with frontend charts (RevenueInsights.tsx).
- Computes trend slope via linear regression (numpy.polyfit).
- Calculates predicted MRR, projected growth rates, and statistical confidence scores.
- Handles sparse / zero data gracefully with heuristic baselines.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from backend.services.finance.money_utils import to_decimal


@dataclass
class ForecastResult:
    """Consolidated revenue projection result."""
    forecast_data: List[Dict[str, Any]]
    current_mrr: float
    predicted_mrr: float
    growth_rate_pct: float
    confidence_score: float
    historical_months_count: int
    forecast_months_count: int
    trend_direction: str
    methodology: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert forecast result to dictionary matching frontend contracts."""
        return {
            "forecast_data": self.forecast_data,
            "current_mrr": round(self.current_mrr, 2),
            "predicted_mrr": round(self.predicted_mrr, 2),
            "growth_rate_pct": round(self.growth_rate_pct, 2),
            "confidence_score": round(self.confidence_score, 2),
            "historical_months_count": self.historical_months_count,
            "forecast_months_count": self.forecast_months_count,
            "trend_direction": self.trend_direction,
            "methodology": self.methodology,
        }


def _advance_month(year: int, month: int, delta: int) -> Tuple[int, int]:
    """Advance year and month by delta months."""
    total_months = year * 12 + (month - 1) + delta
    new_year = total_months // 12
    new_month = (total_months % 12) + 1
    return new_year, new_month


def _format_month(year: int, month: int) -> str:
    """Format year and month as YYYY-MM string."""
    return f"{year:04d}-{month:02d}"


def forecast_revenue(
    historical_monthly_revenue: Union[List[Dict[str, Any]], Dict[str, float]],
    months_ahead: int = 6,
    known_current_mrr: Optional[float] = None,
) -> ForecastResult:
    """
    Projects monthly recurring revenue for `months_ahead` periods.

    Parameters:
        historical_monthly_revenue:
            List of dicts: [{'month': '2026-01', 'revenue': 10000.0}, ...]
            OR dict mapping month to revenue: {'2026-01': 10000.0, '2026-02': 11000.0}
        months_ahead: Number of future months to forecast (default 6).
        known_current_mrr: Optional verified current MRR to anchor the forecast.

    Returns:
        ForecastResult with historical actuals, projected points, and metrics.
    """
    # 1. Parse historical data into a clean sorted pandas Series
    records: Dict[str, float] = {}
    if isinstance(historical_monthly_revenue, dict):
        for k, v in historical_monthly_revenue.items():
            records[str(k)[:7]] = float(v)
    elif isinstance(historical_monthly_revenue, list):
        for item in historical_monthly_revenue:
            m = item.get("month") or item.get("date") or item.get("period")
            rev = item.get("revenue") or item.get("mrr") or item.get("amount") or 0.0
            if m:
                records[str(m)[:7]] = float(rev)

    if not records and known_current_mrr is not None and known_current_mrr > 0:
        # Create single synthetic baseline point for current month
        today = date.today()
        records[_format_month(today.year, today.month)] = float(known_current_mrr)

    # Sort months chronologically
    sorted_months = sorted(records.keys())
    hist_count = len(sorted_months)

    # 2. Case: Completely Empty Data
    if hist_count == 0:
        today = date.today()
        empty_points = []
        for i in range(months_ahead):
            y, m = _advance_month(today.year, today.month, i + 1)
            empty_points.append({"month": _format_month(y, m), "actual": None, "forecast": 0.0})
        return ForecastResult(
            forecast_data=empty_points,
            current_mrr=0.0,
            predicted_mrr=0.0,
            growth_rate_pct=0.0,
            confidence_score=0.0,
            historical_months_count=0,
            forecast_months_count=months_ahead,
            trend_direction="stable",
            methodology="insufficient_data",
        )

    # Prepare DataFrame
    df = pd.DataFrame([{"month": m, "revenue": max(0.0, records[m])} for m in sorted_months])
    revenues = df["revenue"].to_numpy(dtype=float)

    # Determine last month anchor
    last_month_str = sorted_months[-1]
    last_year = int(last_month_str[:4])
    last_month_num = int(last_month_str[5:7])

    current_mrr = known_current_mrr if known_current_mrr is not None else float(revenues[-1])

    # 3. Model Fitting & Projection
    forecast_points: List[float] = []
    confidence: float = 0.5
    methodology: str = "linear_regression"

    if hist_count == 1:
        # Single point baseline: project constant with slight conservative dampening
        methodology = "single_point_baseline"
        confidence = 0.35
        growth_rate_pct = 0.0
        forecast_points = [current_mrr] * months_ahead
    elif hist_count == 2:
        # Two points: simple linear rate of change
        methodology = "two_point_extrapolation"
        rev_prev, rev_curr = revenues[0], revenues[1]
        step = (rev_curr - rev_prev) * 0.8  # 20% dampening on forward trend
        growth_rate_pct = ((rev_curr - rev_prev) / rev_prev * 100.0) if rev_prev > 0 else 0.0
        confidence = 0.55
        for step_idx in range(1, months_ahead + 1):
            val = max(0.0, current_mrr + step * step_idx)
            forecast_points.append(val)
    else:
        # 3+ points: Weighted Linear Trend Regression via NumPy
        methodology = "weighted_linear_regression"
        x = np.arange(hist_count, dtype=float)
        y = revenues

        # Exponential recency weights: recent months weigh significantly more than older ones
        weights = np.exp(np.linspace(0.5, 1.5, hist_count))
        slope, intercept = np.polyfit(x, y, 1, w=weights)

        # Baseline monthly growth percentage
        mean_rev = np.mean(y) if np.mean(y) > 0 else 1.0
        growth_rate_pct = (slope / mean_rev) * 100.0

        # Confidence based on variance / R-squared
        fitted_y = slope * x + intercept
        ss_res = np.sum((y - fitted_y) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.8
        r_squared = max(0.0, min(1.0, float(r_squared)))

        # Confidence scales with sample size and fit quality
        sample_factor = min(1.0, hist_count / 10.0)
        confidence = min(0.95, max(0.40, (r_squared * 0.6) + (sample_factor * 0.35)))

        # Project forward with trend dampening (0.97 factor per month)
        dampening = 0.97
        cumulative_slope = slope
        last_val = current_mrr
        for step_idx in range(1, months_ahead + 1):
            cumulative_slope *= dampening
            projected = max(0.0, last_val + cumulative_slope)
            forecast_points.append(projected)
            last_val = projected

    # 4. Assemble Unified forecast_data
    # Historical points: actual filled, forecast is None
    # Transition point: last actual month also starts the forecast curve
    # Future points: actual is None, forecast filled
    unified_data: List[Dict[str, Any]] = []

    for idx, m_str in enumerate(sorted_months):
        act_val = round(float(revenues[idx]), 2)
        if idx == hist_count - 1:
            # Overlap point connects the two curves cleanly on SVG / Recharts
            unified_data.append({
                "month": m_str,
                "actual": act_val,
                "forecast": act_val,
            })
        else:
            unified_data.append({
                "month": m_str,
                "actual": act_val,
                "forecast": None,
            })

    for step_idx, f_val in enumerate(forecast_points, start=1):
        fy, fm = _advance_month(last_year, last_month_num, step_idx)
        unified_data.append({
            "month": _format_month(fy, fm),
            "actual": None,
            "forecast": round(float(f_val), 2),
        })

    predicted_mrr = forecast_points[-1] if forecast_points else current_mrr
    total_change = predicted_mrr - current_mrr
    if abs(total_change) < 0.01:
        trend_direction = "stable"
    elif total_change > 0:
        trend_direction = "positive"
    else:
        trend_direction = "negative"

    overall_growth_pct = ((predicted_mrr - current_mrr) / current_mrr * 100.0) if current_mrr > 0 else 0.0

    return ForecastResult(
        forecast_data=unified_data,
        current_mrr=current_mrr,
        predicted_mrr=predicted_mrr,
        growth_rate_pct=overall_growth_pct,
        confidence_score=confidence,
        historical_months_count=hist_count,
        forecast_months_count=months_ahead,
        trend_direction=trend_direction,
        methodology=methodology,
    )


def generate_forecast_from_invoices(
    invoices: List[Any],
    months_ahead: int = 6,
    known_current_mrr: Optional[float] = None,
) -> ForecastResult:
    """
    Extracts monthly revenue aggregates from invoices and computes the 6-month forecast.
    """
    monthly_rev: Dict[str, float] = {}
    for inv in invoices:
        status = getattr(inv, "status", None) if not isinstance(inv, dict) else inv.get("status")
        if status in ("cancelled", "void"):
            continue

        raw_date = getattr(inv, "issue_date", None) if not isinstance(inv, dict) else inv.get("issue_date")
        if not raw_date:
            raw_date = getattr(inv, "billing_period_start", None) if not isinstance(inv, dict) else inv.get("billing_period_start")

        amt = getattr(inv, "total_amount", 0) if not isinstance(inv, dict) else inv.get("total_amount", 0)
        d_str = str(raw_date)[:7] if raw_date else None
        if d_str and len(d_str) == 7:
            monthly_rev[d_str] = monthly_rev.get(d_str, 0.0) + float(to_decimal(amt))

    return forecast_revenue(monthly_rev, months_ahead=months_ahead, known_current_mrr=known_current_mrr)
