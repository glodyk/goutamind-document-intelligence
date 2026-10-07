"""Claim Document Bundle (DATA_MODEL 5): the processing boundary of one run.

Only the layers built by the vertical slice are present. Canonical claim,
timeline, narrative and intelligence are not produced yet.
"""

from dataclasses import dataclass, field

from app.document.models import Document
from app.evidence.models import Event, Evidence, Fact
from app.extraction.models import Page, SourceFile


@dataclass(slots=True)
class ClaimDocumentBundle:
    bundle_id: str
    schema_version: str
    extraction_version: str
    source_files: list[SourceFile] = field(default_factory=list)
    documents: list[Document] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)

    @property
    def pages(self) -> dict[str, Page]:
        return {p.page_id: p for f in self.source_files for p in f.pages}

    def unassigned_pages(self) -> list[Page]:
        """Pages that belong to no Document (blank pages, by design)."""
        assigned = {ref.page_id for d in self.documents for ref in d.page_refs}
        return [p for p in self.pages.values() if p.page_id not in assigned]
