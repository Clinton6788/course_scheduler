"""Dated course/session pricing.

Pricing is read from a CSV (see ``config.settings.PRICING_PATH``) where each
row is a price tier that becomes effective on its ``Begin Date`` and stays in
effect until the next (later) row's begin date. To change prices, add a new row
with a new begin date -- existing rows are left untouched so historical sessions
keep their original pricing.

A session's cost is resolved against the session's *start date*: the applicable
tier is the latest one whose begin date is on or before that start date. A new
tier therefore never affects a session that has already started before its
begin date -- it only applies to sessions that start on or after it.
"""
from __future__ import annotations
import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import settings


# Accepted header variants -> canonical column name. Headers are matched
# case-insensitively after stripping whitespace.
_COLUMN_MAP = {
    "begin date": [
        "begin date", "begindate", "begin-date", "begin_date",
        "start date", "effective date", "effective", "date",
    ],
    "cost per session": [
        "cost per session", "costpersession", "cost-per-session",
        "cost_per_session", "session cost", "per session",
    ],
    "cost per course": [
        "cost per course", "costpercourse", "cost-per-course",
        "cost_per_course", "course cost", "per course",
    ],
    "cost per ch undergrad": [
        "cost per ch undergrad", "cost-per-ch-undergrad",
        "cost_per_ch_undergrad", "ch undergrad", "undergrad ch", "undergrad",
    ],
    "cost per ch grad": [
        "cost per ch grad", "cost-per-ch-grad", "cost_per_ch_grad",
        "ch grad", "grad ch", "grad",
    ],
    "alumni savings percent": [
        "alumni savings percent", "alumni-savings-percent",
        "alumni_savings_percent", "alumni savings %", "alumni percent",
        "alumni savings", "alumni",
    ],
}


@dataclass(frozen=True)
class PriceTier:
    """A set of costs effective on/after ``begin_date``."""
    begin_date: dt.date
    cost_per_session: float
    cost_per_course: float          # Flat additional cost per course (outside cost/ch)
    cost_per_ch_undergrad: float
    cost_per_ch_grad: float
    alumni_savings_percent: float   # Whole percentage (e.g. 20 for 20%); grad only


# Loaded tiers, sorted ascending by begin_date. Cached after first load.
_CACHE: list[PriceTier] | None = None


def _resolve_path() -> Path:
    path = Path(settings.PRICING_PATH)
    if not getattr(settings, "PRICING_PATH_ABS", False):
        path = Path.cwd() / path
    return path


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map any recognized header variant to its canonical column name."""
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower()
        for std_name, variants in _COLUMN_MAP.items():
            if key in variants:
                rename[col] = std_name
                break
    return df.rename(columns=rename)


def _parse_date(val) -> dt.date:
    if isinstance(val, dt.datetime):
        return val.date()
    if isinstance(val, dt.date):
        return val
    ts = pd.to_datetime(val, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Unparseable Begin Date in pricing file: {val!r}")
    return ts.date()


def load_pricing(force_reload: bool = False) -> list[PriceTier]:
    """Load and cache all price tiers, sorted ascending by begin date."""
    global _CACHE
    if _CACHE is not None and not force_reload:
        return _CACHE

    path = _resolve_path()
    if not path.exists():
        raise FileNotFoundError(f"Pricing file not found: {path}")

    df = _normalize_columns(pd.read_csv(path))

    missing = [c for c in _COLUMN_MAP if c not in df.columns]
    if missing:
        raise ValueError(
            f"Pricing file {path} is missing required columns: {missing}"
        )

    tiers = []
    for _, row in df.iterrows():
        tiers.append(PriceTier(
            begin_date=_parse_date(row["begin date"]),
            cost_per_session=float(row["cost per session"]),
            cost_per_course=float(row["cost per course"]),
            cost_per_ch_undergrad=float(row["cost per ch undergrad"]),
            cost_per_ch_grad=float(row["cost per ch grad"]),
            alumni_savings_percent=float(row["alumni savings percent"]),
        ))

    if not tiers:
        raise ValueError(f"No pricing rows found in {path}")

    tiers.sort(key=lambda t: t.begin_date)

    seen = set()
    for t in tiers:
        if t.begin_date in seen:
            raise ValueError(
                f"Duplicate Begin Date {t.begin_date} in pricing file {path}"
            )
        seen.add(t.begin_date)

    _CACHE = tiers
    return tiers


def get_pricing(date: dt.date) -> PriceTier:
    """Return the price tier in effect on ``date``.

    The applicable tier is the latest one whose ``begin_date`` is on or before
    ``date``. Raises if ``date`` precedes the earliest tier.
    """
    tiers = load_pricing()
    applicable = None
    for t in tiers:
        if t.begin_date <= date:
            applicable = t
        else:
            break  # tiers are sorted ascending; no later tier can apply
    if applicable is None:
        raise ValueError(
            f"No pricing tier effective on or before {date}. Earliest pricing "
            f"begins {tiers[0].begin_date}. Add an earlier row to "
            f"'{settings.PRICING_PATH}'."
        )
    return applicable
