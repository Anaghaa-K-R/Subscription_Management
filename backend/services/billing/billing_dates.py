"""
Billing Dates & Recurring Cycle Scheduler for SubscriptIQ.

Provides robust, anchor-preserving calendar math for subscription recurring schedules:
- Weekly: Adds 7 days strictly.
- Monthly: Advances 1 calendar month, preserving subscription anchor day across
  varying month lengths (e.g. Jan 31 -> Feb 28 -> Mar 31).
- Yearly: Advances 1 calendar year, safely handling Feb 29 leap-year edge cases.
- Billing period calculation: Returns (period_start, period_end) where
  period_end is the day immediately prior to next_billing_date.
"""

import calendar
from datetime import date, timedelta
from enum import Enum
from typing import Optional, Tuple, Union


class BillingInterval(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


def get_days_in_month(year: int, month: int) -> int:
    """
    Return the total number of days in the specified month and year.
    Accurately accounts for leap years in February (29 days vs 28 days).
    """
    return calendar.monthrange(year, month)[1]


def calculate_next_billing_date(
    current_date: date,
    interval: Union[str, BillingInterval],
    anchor_day: Optional[int] = None,
) -> date:
    """
    Calculate the next recurring billing date given a current date and billing interval.

    Anchor Day Preservation:
    If a subscription is anchored on day 31, recurring monthly billing will
    temporarily clamp to the last day of shorter months (e.g., Feb 28/29, Apr 30),
    but restore to the 31st for 31-day months (e.g. Mar 31, May 31).

    Parameters:
        current_date: The base date of the current cycle.
        interval: 'weekly', 'monthly', or 'yearly'.
        anchor_day: The intended day-of-month (1-31). If None, defaults to current_date.day.

    Returns:
        Next scheduled billing date.

    Raises:
        ValueError: If interval is unsupported or anchor_day is out of 1-31 range.
    """
    if not isinstance(current_date, date):
        raise ValueError(f"current_date must be a datetime.date instance, got {type(current_date)}")

    raw_interval = interval.value if isinstance(interval, BillingInterval) else str(interval).lower().strip()

    if anchor_day is not None and not (1 <= anchor_day <= 31):
        raise ValueError(f"anchor_day must be between 1 and 31 inclusive, got {anchor_day}")

    target_anchor = anchor_day if anchor_day is not None else current_date.day

    if raw_interval == "weekly":
        return current_date + timedelta(days=7)

    elif raw_interval == "monthly":
        year = current_date.year
        month = current_date.month

        # Advance one month
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1

        days_in_target_month = get_days_in_month(next_year, next_month)
        # Clamp to the maximum available days in the target month
        day = min(target_anchor, days_in_target_month)
        return date(next_year, next_month, day)

    elif raw_interval == "yearly":
        next_year = current_date.year + 1
        target_month = current_date.month
        days_in_target_month = get_days_in_month(next_year, target_month)
        # Handles leap-year edge cases (e.g., Feb 29 -> Feb 28 on non-leap year)
        day = min(target_anchor, days_in_target_month)
        return date(next_year, target_month, day)

    else:
        raise ValueError(
            f"Unsupported billing interval: '{interval}'. Must be 'weekly', 'monthly', or 'yearly'."
        )


def calculate_billing_period(
    period_start: date,
    interval: Union[str, BillingInterval],
    anchor_day: Optional[int] = None,
) -> Tuple[date, date]:
    """
    Calculate the start and inclusive end date of a billing cycle.

    By standard SaaS convention:
    period_end is the calendar day immediately preceding the next billing date.

    Example (Monthly):
    - period_start: 2026-01-01
    - next_billing_date: 2026-02-01
    - returned: (2026-01-01, 2026-01-31)

    Example (Weekly):
    - period_start: 2026-01-01
    - next_billing_date: 2026-01-08
    - returned: (2026-01-01, 2026-01-07)

    Returns:
        Tuple of (period_start, period_end)
    """
    next_billing = calculate_next_billing_date(period_start, interval, anchor_day=anchor_day)
    period_end = next_billing - timedelta(days=1)
    return (period_start, period_end)


def is_billing_due(next_billing_date: Optional[date], evaluation_date: Optional[date] = None) -> bool:
    """
    Determine if a subscription is due for recurring invoice generation.

    Parameters:
        next_billing_date: The subscription's next scheduled billing date.
        evaluation_date: Date to evaluate against (defaults to today).

    Returns:
        True if evaluation_date >= next_billing_date. False if next_billing_date is None.
    """
    if next_billing_date is None:
        return False
    eval_date = evaluation_date or date.today()
    return eval_date >= next_billing_date
