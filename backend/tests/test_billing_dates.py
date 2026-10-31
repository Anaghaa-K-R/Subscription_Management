"""
Unit Tests for Billing Dates Engine (backend/services/billing/billing_dates.py).
"""

import pytest
from datetime import date
from backend.services.billing.billing_dates import (
    calculate_next_billing_date,
    calculate_billing_period,
    is_billing_due,
    get_days_in_month,
    BillingInterval,
)


class TestBillingDates:
    def test_days_in_month(self):
        # Normal February
        assert get_days_in_month(2026, 2) == 28
        # Leap year February
        assert get_days_in_month(2024, 2) == 29
        # April has 30 days
        assert get_days_in_month(2026, 4) == 30
        # July has 31 days
        assert get_days_in_month(2026, 7) == 31

    def test_weekly_billing(self):
        start = date(2026, 1, 1)
        next_date = calculate_next_billing_date(start, interval="weekly")
        assert next_date == date(2026, 1, 8)

    def test_monthly_billing_standard(self):
        start = date(2026, 1, 15)
        next_date = calculate_next_billing_date(start, interval=BillingInterval.MONTHLY)
        assert next_date == date(2026, 2, 15)

    def test_monthly_year_rollover(self):
        start = date(2026, 12, 15)
        next_date = calculate_next_billing_date(start, interval="monthly")
        assert next_date == date(2027, 1, 15)

    def test_month_end_anchor_preservation_non_leap_year(self):
        """
        Critical recurring billing requirement:
        A subscriber starting Jan 31 must bill Feb 28, then Mar 31, then Apr 30!
        """
        # Cycle 1: Jan 31 -> Feb 28 (non-leap year 2026)
        jan_31 = date(2026, 1, 31)
        feb_due = calculate_next_billing_date(jan_31, interval="monthly", anchor_day=31)
        assert feb_due == date(2026, 2, 28)

        # Cycle 2: From Feb 28 back to Mar 31
        mar_due = calculate_next_billing_date(feb_due, interval="monthly", anchor_day=31)
        assert mar_due == date(2026, 3, 31)

        # Cycle 3: From Mar 31 to Apr 30
        apr_due = calculate_next_billing_date(mar_due, interval="monthly", anchor_day=31)
        assert apr_due == date(2026, 4, 30)

        # Cycle 4: From Apr 30 to May 31
        may_due = calculate_next_billing_date(apr_due, interval="monthly", anchor_day=31)
        assert may_due == date(2026, 5, 31)

    def test_month_end_anchor_preservation_leap_year(self):
        # In 2024 (leap year), Jan 31 -> Feb 29
        jan_31_2024 = date(2024, 1, 31)
        feb_due = calculate_next_billing_date(jan_31_2024, interval="monthly", anchor_day=31)
        assert feb_due == date(2024, 2, 29)

        # From Feb 29 to Mar 31
        mar_due = calculate_next_billing_date(feb_due, interval="monthly", anchor_day=31)
        assert mar_due == date(2024, 3, 31)

    def test_yearly_billing_standard(self):
        start = date(2026, 5, 20)
        next_date = calculate_next_billing_date(start, interval=BillingInterval.YEARLY)
        assert next_date == date(2027, 5, 20)

    def test_yearly_leap_year_rollover(self):
        # Feb 29 on leap year (2024) -> Feb 28 next year (2025)
        leap_day = date(2024, 2, 29)
        next_date = calculate_next_billing_date(leap_day, interval="yearly")
        assert next_date == date(2025, 2, 28)

    def test_calculate_billing_period_monthly(self):
        period_start = date(2026, 1, 1)
        p_start, p_end = calculate_billing_period(period_start, interval="monthly")
        assert p_start == date(2026, 1, 1)
        assert p_end == date(2026, 1, 31)

    def test_calculate_billing_period_weekly(self):
        period_start = date(2026, 1, 1)
        p_start, p_end = calculate_billing_period(period_start, interval="weekly")
        assert p_start == date(2026, 1, 1)
        assert p_end == date(2026, 1, 7)

    def test_calculate_billing_period_yearly(self):
        period_start = date(2026, 1, 1)
        p_start, p_end = calculate_billing_period(period_start, interval="yearly")
        assert p_start == date(2026, 1, 1)
        assert p_end == date(2026, 12, 31)

    def test_is_billing_due(self):
        target = date(2026, 5, 1)

        # Due when evaluation date equals or exceeds target
        assert is_billing_due(target, evaluation_date=date(2026, 5, 1)) is True
        assert is_billing_due(target, evaluation_date=date(2026, 5, 2)) is True

        # Not due when evaluation date is in the past
        assert is_billing_due(target, evaluation_date=date(2026, 4, 30)) is False

        # Not due if target is None
        assert is_billing_due(None) is False

    def test_invalid_interval_raises_error(self):
        with pytest.raises(ValueError, match="Unsupported billing interval"):
            calculate_next_billing_date(date(2026, 1, 1), interval="bi-weekly")

    def test_invalid_anchor_day_raises_error(self):
        with pytest.raises(ValueError, match="anchor_day must be between 1 and 31"):
            calculate_next_billing_date(date(2026, 1, 1), interval="monthly", anchor_day=32)
