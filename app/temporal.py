"""Temporal Value parsing (DATA_MODEL 17, 17A, 17B).

Rules implemented here:

- ``value`` is never more precise than the source (no invented day or time);
- ``raw_text`` always keeps the date exactly as written;
- numeric day/month order is only resolved when it is unambiguous
  (one part > 12) or when the caller passes an explicit ``numeric_order``
  (the "documented adapter configuration" of 17A). Otherwise the value is
  left empty, precision is ``UNKNOWN`` and the ambiguity is recorded.
"""

import re
from dataclasses import dataclass
from typing import Literal

from app.vocabulary import DateRole, TemporalPrecision

NumericOrder = Literal["DMY", "MDY"]

MONTHS: dict[str, int] = {
    # Indonesian
    "januari": 1,
    "februari": 2,
    "pebruari": 2,
    "maret": 3,
    "april": 4,
    "mei": 5,
    "juni": 6,
    "juli": 7,
    "agustus": 8,
    "september": 9,
    "oktober": 10,
    "nopember": 11,
    "november": 11,
    "desember": 12,
    # English
    "january": 1,
    "february": 2,
    "march": 3,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "october": 10,
    "december": 12,
    # Abbreviations (shared)
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "agu": 8,
    "agt": 8,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "okt": 10,
    "oct": 10,
    "nov": 11,
    "des": 12,
    "dec": 12,
}

_MONTH_NAMES = "|".join(sorted(MONTHS, key=len, reverse=True))
_TIME = r"(?:[ ,T]+(?:jam\s*)?(?P<h>\d{1,2})[:.](?P<mi>\d{2})(?::(?P<s>\d{2}))?)?"
_TZ = r"(?:\s*(?P<tz>WIB|WITA|WIT)\b)?"

ISO_DATE = re.compile(r"\b(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})" + _TIME + _TZ)
NUMERIC_DATE = re.compile(r"\b(?P<a>\d{1,2})[/-](?P<b>\d{1,2})[/-](?P<y>\d{4})\b" + _TIME + _TZ)
NAMED_DATE = re.compile(
    r"\b(?P<d>\d{1,2})\s+(?P<mon>" + _MONTH_NAMES + r")\.?\s+(?P<y>\d{4})\b" + _TIME + _TZ,
    re.IGNORECASE,
)
MONTH_YEAR = re.compile(r"\b(?P<mon>" + _MONTH_NAMES + r")\s+(?P<y>\d{4})\b", re.IGNORECASE)


@dataclass(slots=True)
class TemporalValue:
    """DATA_MODEL 17A Temporal Value."""

    value: str | None
    precision: TemporalPrecision
    raw_text: str
    date_role: DateRole = DateRole.UNKNOWN
    timezone: str | None = None
    ambiguity: str | None = None  # IMPLEMENTATION: why the value was not resolved
    source_label: str | None = None  # IMPLEMENTATION: label printed before the date


@dataclass(slots=True)
class DateMatch:
    start: int
    end: int
    temporal: TemporalValue


def _valid(y: int, m: int, d: int) -> bool:
    return 1 <= m <= 12 and 1 <= d <= 31 and 1900 <= y <= 2100


def _build(
    raw: str,
    y: int,
    m: int,
    d: int,
    groups: dict[str, str | None],
) -> TemporalValue | None:
    if not _valid(y, m, d):
        return None
    tz = groups.get("tz")
    if groups.get("h") is not None:
        h, mi = int(groups["h"] or 0), int(groups["mi"] or 0)
        if h > 23 or mi > 59:
            return None
        value = f"{y:04d}-{m:02d}-{d:02d}T{h:02d}:{mi:02d}"
        if groups.get("s") is not None:
            value += f":{int(groups['s'] or 0):02d}"
        return TemporalValue(value, TemporalPrecision.EXACT_DATETIME, raw, timezone=tz)
    return TemporalValue(f"{y:04d}-{m:02d}-{d:02d}", TemporalPrecision.DATE, raw, timezone=tz)


def _resolve_numeric(a: int, b: int, order: NumericOrder | None) -> tuple[int, int] | str:
    """Return (month, day) or a reason string when the order cannot be decided."""
    if a > 12 and b <= 12:
        return b, a
    if b > 12 and a <= 12:
        return a, b
    if a == b:
        return a, b
    if order == "DMY":
        return b, a
    if order == "MDY":
        return a, b
    return "AMBIGUOUS_DAY_MONTH_ORDER"


def find_dates(text: str, numeric_order: NumericOrder | None = None) -> list[DateMatch]:
    """Find every date-like expression in ``text``, left to right, non-overlapping."""
    found: list[DateMatch] = []
    taken: list[tuple[int, int]] = []

    def overlaps(s: int, e: int) -> bool:
        return any(s < te and e > ts for ts, te in taken)

    for match in ISO_DATE.finditer(text):
        tv = _build(
            match.group(0).strip(), int(match["y"]), int(match["m"]), int(match["d"]), match.groupdict()
        )
        if tv:
            found.append(DateMatch(match.start(), match.end(), tv))
            taken.append(match.span())

    for match in NUMERIC_DATE.finditer(text):
        if overlaps(*match.span()):
            continue
        raw = match.group(0).strip()
        resolved = _resolve_numeric(int(match["a"]), int(match["b"]), numeric_order)
        numeric: TemporalValue | None
        if isinstance(resolved, str):
            numeric = TemporalValue(None, TemporalPrecision.UNKNOWN, raw, ambiguity=resolved)
        else:
            numeric = _build(raw, int(match["y"]), resolved[0], resolved[1], match.groupdict())
        if numeric:
            found.append(DateMatch(match.start(), match.end(), numeric))
            taken.append(match.span())

    for match in NAMED_DATE.finditer(text):
        if overlaps(*match.span()):
            continue
        month = MONTHS[match["mon"].lower()]
        tv = _build(match.group(0).strip(), int(match["y"]), month, int(match["d"]), match.groupdict())
        if tv:
            found.append(DateMatch(match.start(), match.end(), tv))
            taken.append(match.span())

    for match in MONTH_YEAR.finditer(text):
        if overlaps(*match.span()):
            continue
        month, year = MONTHS[match["mon"].lower()], int(match["y"])
        if 1900 <= year <= 2100:
            tv = TemporalValue(f"{year:04d}-{month:02d}", TemporalPrecision.MONTH, match.group(0))
            found.append(DateMatch(match.start(), match.end(), tv))
            taken.append(match.span())

    return sorted(found, key=lambda dm: dm.start)
