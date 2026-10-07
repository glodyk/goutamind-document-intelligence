"""Attach a date role to each date found on a line (DATA_MODEL 17B).

The role comes only from a label printed just before the date on the same
line. No label, or an unlisted one, gives ``UNKNOWN``. Birth dates are
recognised so they can be *skipped*: this slice does not copy them into
document metadata (personal data, ADR-08).
"""

from dataclasses import replace

from app.document.models import Document
from app.document.rules import DATE_LABEL_WINDOW, DATE_LABELS
from app.extraction.models import Page
from app.temporal import NumericOrder, TemporalValue, find_dates
from app.vocabulary import DateRole


def labelled_dates(text: str, numeric_order: NumericOrder | None = None) -> list[TemporalValue]:
    results: list[TemporalValue] = []
    previous_end = 0
    for match in find_dates(text, numeric_order):
        window = text[max(previous_end, match.start - DATE_LABEL_WINDOW) : match.start]
        role = DateRole.UNKNOWN
        best = -1
        for pattern, label_role in DATE_LABELS:
            for label in pattern.finditer(window):
                if label.start() > best:  # the label closest to the date wins
                    best, role = label.start(), label_role
        previous_end = match.end
        if role is DateRole.BIRTH:
            continue
        results.append(replace(match.temporal, date_role=role))
    return results


def collect_document_dates(
    document: Document, pages: dict[str, Page], numeric_order: NumericOrder | None = None
) -> None:
    for ref in document.page_refs:
        for element in pages[ref.page_id].text_lines:
            document.dates.extend(labelled_dates(element.text or "", numeric_order))
