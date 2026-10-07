"""Opaque identifiers (DATA_MODEL 4).

Identifiers are sequential within one processing run, so the same input
always yields the same ids. They carry no business meaning.
"""

import hashlib
from collections import defaultdict


class IdFactory:
    """Hands out ``<prefix>-<NNN>`` ids, one counter per prefix."""

    def __init__(self) -> None:
        self._counters: defaultdict[str, int] = defaultdict(int)

    def next(self, prefix: str) -> str:
        self._counters[prefix] += 1
        return f"{prefix}-{self._counters[prefix]:03d}"


def content_digest(data: bytes) -> str:
    """SHA-256 of the file bytes, used for SourceFile identity and duplicate detection."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def source_file_id_for(digest: str) -> str:
    """Stable SourceFile id derived from the content digest.

    The same bytes always get the same id, across runs and machines. The
    digest prefix is opaque: it says nothing about the claim or patient.
    """
    return "file-" + digest.removeprefix("sha256:")[:12]
