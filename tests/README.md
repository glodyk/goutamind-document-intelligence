# Tests

```bash
python -m pytest            # everything
python -m pytest tests/unit # fast, no PDF files involved
```

| Folder | What |
|---|---|
| `unit/` | Temporal parsing, title/marker/counter rules, section headings, fact patterns, PDF reader edge cases (blank, image-only, broken, password-protected). |
| `integration/` | Whole pipeline on the synthetic bundle: every layer, the Fact -> Evidence -> Page -> SourceFile chain, CLI output, and a check that `examples/golden_claim/` is up to date. |
| `fixtures/` | `synthetic_pdf.py` writes small PDFs with no extra dependency; `synthetic_bundle.py` is the invented 16-page claim bundle used by the tests and the golden example. |

`integration/test_private_samples.py` runs structural checks on real PDFs in
`samples_private/` (or `$GOUTAMIND_PRIVATE_SAMPLES`). It is skipped when there
are none, never asserts on content, and its test ids do not contain file
names.

No fixture may contain real patient data. Add new cases to
`tests/fixtures/synthetic_bundle.py` with invented values, then run
`python -m scripts.make_synthetic_bundle` to refresh the golden example.
