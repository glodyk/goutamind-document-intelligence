"""Regenerate the synthetic golden example in ``examples/golden_claim/``.

Usage (from the repository root)::

    python -m scripts.make_synthetic_bundle

Writes the synthetic PDF, its JSON bundle and its inspection report. All
content is invented (see tests/fixtures/synthetic_bundle.py), so these files
are safe to commit. The ingestion timestamp is fixed so the output is
reproducible.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from pipeline.report import render_inspection
from pipeline.run import process_pdf
from pipeline.serialize import to_json_dict
from tests.fixtures.synthetic_bundle import synthetic_bundle_pdf

OUT = Path(__file__).resolve().parents[1] / "examples" / "golden_claim"
FIXED_NOW = datetime(2025, 1, 1, tzinfo=UTC)


def main() -> None:
    pdf = OUT / "synthetic_claim_bundle.pdf"
    pdf.write_bytes(synthetic_bundle_pdf())
    bundle = process_pdf(pdf, now=FIXED_NOW)
    (OUT / "synthetic_claim_bundle.bundle.json").write_text(
        json.dumps(to_json_dict(bundle), indent=2, ensure_ascii=False) + "\n", "utf-8"
    )
    (OUT / "synthetic_claim_bundle.inspection.txt").write_text(render_inspection(bundle), "utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
