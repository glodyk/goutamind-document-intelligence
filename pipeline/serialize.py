"""Plain-JSON view of a bundle (not yet a JSON Schema; see DATA_MODEL 45)."""

from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any

from app.bundle import ClaimDocumentBundle


def _plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: _plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def to_json_dict(bundle: ClaimDocumentBundle) -> dict[str, Any]:
    data = _plain(bundle)
    for document, raw in zip(bundle.documents, data["documents"], strict=True):
        raw["page_range"] = document.page_range  # derived convenience field
    # Not produced by this slice; present so the top-level shape matches DATA_MODEL 45.
    data.update(canonical_claim=None, source_discrepancies=[], timeline=[], narrative=None, intelligence=[])
    return data
