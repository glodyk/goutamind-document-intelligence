"""Human-readable inspection report for one processed bundle.

This is a developer view for checking whether the layers connect; it is not
a user-facing format. With ``show_source_text=False`` the copied source text
(evidence text and document titles) is left out, so the report can be shared
more safely. Fact values and dates are still shown.
"""

from collections import Counter

from app.bundle import ClaimDocumentBundle
from app.temporal import TemporalValue

TEXT_PREVIEW = 70


def _tv(tv: TemporalValue) -> str:
    value = tv.value or "?"
    extra = f", {tv.ambiguity}" if tv.ambiguity else ""
    return f'{value} ({tv.precision}{extra}, raw "{tv.raw_text}")'


def _preview(text: str | None) -> str:
    if text is None:
        return ""
    text = " ".join(text.split())
    return text if len(text) <= TEXT_PREVIEW else text[: TEXT_PREVIEW - 1] + "…"


def page_assignment_lines(bundle: ClaimDocumentBundle, show_source_text: bool = True) -> list[str]:
    """Why each page sits where it does (ADR-REQ-001): page -> document -> basis -> evidence."""
    membership = {ref.page_id: (d, ref) for d in bundle.documents for ref in d.page_refs}
    evidence = {e.evidence_id: e for e in bundle.evidence}
    lines = ["Page assignment:"]
    for source in bundle.source_files:
        for page in source.pages:
            lines.append(f"  Page {page.page_number}")
            if page.page_id not in membership:
                lines.append("    Document: NONE")
                lines.append(f"    Reason: {page.page_kind}")
                continue
            document, ref = membership[page.page_id]
            lines.append(f"    Document: {document.document_id}")
            lines.append(f"    Type: {document.document_type}")
            lines.append(f"    Basis: {ref.basis}")
            lines.append(f"    Evidence: {ref.evidence_ref}")
            cited = evidence[ref.evidence_ref].source_text
            if show_source_text and cited:
                lines.append(f'    Cited: "{_preview(cited)}"')
    return lines


def render_page_assignment(bundle: ClaimDocumentBundle, show_source_text: bool = True) -> str:
    return "\n".join(page_assignment_lines(bundle, show_source_text)) + "\n"


def render_inspection(bundle: ClaimDocumentBundle, show_source_text: bool = True) -> str:
    out: list[str] = []
    add = out.append
    page_doc = {ref.page_id: d.document_id for d in bundle.documents for ref in d.page_refs}
    pages = bundle.pages
    evidence = {e.evidence_id: e for e in bundle.evidence}

    for source in bundle.source_files:
        add(f"SourceFile: {source.source_reference} ({source.source_file_id})")
        add(f"  status: {source.ingestion_status}   media_type: {source.media_type}")
        add(f"  digest: {source.content_digest[:23]}…   ingested_at: {source.ingested_at}")
        add(f"  pages: {source.page_count if source.page_count is not None else 'UNKNOWN'}")
        if source.error:
            add(f"  error: {source.error}")
        add("")
        add("Pages:")
        for page in source.pages:
            target = page_doc.get(page.page_id, "(no document)")
            add(
                f"  p{page.page_number:<3} {page.page_kind:<8} {page.modality:<12} "
                f"{page.extraction_method:<11} text={page.text_status:<13} "
                f"lines={len(page.text_lines):<3} images={page.image_count:<2} -> {target}"
            )
        add("")

    add("Documents:")
    for n, document in enumerate(bundle.documents, start=1):
        roles = ",".join(document.document_role) or "-"
        add(f"  {n}. {document.document_type}  ({document.document_id})")
        add(f"     pages: {document.page_range}   roles: {roles}   basis: {document.boundary_basis}")
        bases = ", ".join(f"p{ref.page_number}={ref.basis}" for ref in document.page_refs)
        add(f"     page basis: {bases}")
        if document.page_counters:
            add(f"     printed page counters: {', '.join(document.page_counters)}")
        if show_source_text and document.document_title:
            add(f'     title: "{_preview(document.document_title)}"')
        add(f"     completeness_status: {document.completeness_status}")
        sections = ", ".join(f"{s.section_type}[{len(s.chunks)}]" for s in document.sections)
        add(f"     sections[chunks]: {sections or '(none: no text)'}")
        for tv in document.dates:
            label = f' label="{tv.source_label}"' if tv.source_label else ""
            add(f"     date {tv.date_role:<12} {_tv(tv)}{label}")
    add("")

    out.extend(page_assignment_lines(bundle, show_source_text))
    add("")

    add("Evidence:")
    for ev in bundle.evidence:
        text = f'  "{_preview(ev.source_text)}"' if show_source_text and ev.source_text else ""
        add(
            f"  {ev.evidence_id} -> page {ev.page_number} ({ev.source_file_id}) "
            f"{ev.document_id or '-'} {ev.content_kind} {ev.extraction_method} "
            f"[{ev.purpose}]{text}"
        )
    add("")

    add("Facts:")
    for fact in bundle.facts:
        chain = []
        for ref in fact.evidence_refs:
            ev = evidence[ref]
            chain.append(f"{ref} -> page {pages[ev.page_id].page_number} -> {ev.source_file_id}")
        label = f' label="{fact.source_label}"' if fact.source_label else ""
        system = f" system={fact.coding_system}" if fact.coding_system else ""
        add(
            f"  {fact.fact_id} {fact.fact_type} {fact.attribute}={fact.value!r} "
            f"[{fact.availability_status}, {fact.provenance}]{label}{system} "
            f"({fact.document_id}) -> {'; '.join(chain)}"
        )
    add("")

    add("Events:")
    for event in bundle.events:
        add(
            f"  {event.event_id} {event.event_type} {_tv(event.temporal_value)} "
            f"pathway={event.care_pathway} stage={event.care_stage} ({event.document_id}) "
            f"-> {', '.join(event.evidence_refs)}"
        )
    add("")

    add("Summary:")
    types = Counter(str(d.document_type) for d in bundle.documents)
    add(f"  documents: {len(bundle.documents)}  " + ", ".join(f"{k}={v}" for k, v in sorted(types.items())))
    add(f"  pages without document: {[p.page_number for p in bundle.unassigned_pages()]}")
    fact_types = Counter(str(f.fact_type) for f in bundle.facts)
    add(f"  facts: {len(bundle.facts)}  " + ", ".join(f"{k}={v}" for k, v in sorted(fact_types.items())))
    add(f"  events: {len(bundle.events)}   evidence: {len(bundle.evidence)}")
    return "\n".join(out) + "\n"
