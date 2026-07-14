# 0001 — OCR as a fallback, not a default

## Context

Docling's `do_ocr` is enabled by default, but it decides per page whether OCR is
warranted, using `bitmap_area_threshold`. Scanned documents that do not clear
that threshold are silently skipped, producing a Markdown file containing only
image placeholders while reporting SUCCESS.

`force_full_page_ocr` overrides that decision. The question was whether to
enable it always.

## Measurements

| Document | Mode | Time | Text items | Quality |
|---|---|---|---|---|
| Scanned | default | 3.2 s | 0 | Empty |
| Scanned | forced OCR | 15.3 s | 442 | Usable |
| Text-based | default | 8.3 s | 984 | Exact |
| Text-based | forced OCR | 63.2 s | 962 | Degraded |

Forcing OCR on a document that already has a text layer is 8x slower, extracts
*less* content, and corrupts it: accents are dropped, characters are misread,
and the OCR engine's Chinese-oriented models occasionally emit full-width
punctuation. The embedded text layer is ground truth; OCR is an estimate.

## Decision

Convert without forcing OCR. If the resulting document contains no text and no
tables, convert again with `force_full_page_ocr = True`.

## Consequences

- Text-based PDFs keep their exact content and their 8 second conversion.
- Scanned PDFs cost roughly 19 seconds (a failed 3 s attempt plus a 15 s OCR
  pass) instead of silently producing nothing.
- Worst-case latency rises to ~20 seconds, which makes moving the conversion off
  the UI thread a requirement rather than a refinement.
- OCR quality for Spanish is mediocre. Evaluating alternative OCR engines is
  tracked separately.

## Alternatives rejected

- **Always force OCR.** Rejected: slower and less accurate on the common case.
- **Never OCR.** Rejected: scanned documents are a real use case, and the
  current behaviour silently fails on them.
- **Tune `bitmap_area_threshold`.** Rejected for now: it replaces one heuristic
  with another. Checking the actual output is a direct measure of the thing we
  care about.