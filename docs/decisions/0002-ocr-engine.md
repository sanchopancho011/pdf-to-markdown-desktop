# 0002 — EasyOCR with Spanish instead of the default engine

## Context

Docling defaults to RapidOCR with PP-OCRv4 models, trained primarily on Chinese.
Applied to Spanish tax documents it dropped accents, ran words together, and
emitted full-width CJK punctuation. `ocr_options.lang` defaults to an empty
list, so no language is ever declared.

## Measurements

Same scanned PDF, full-page OCR forced:

| Engine | Time | Text items | Sample output |
|---|---|---|---|
| RapidOCR (default) | 15.3 s | 442 | `ENTIDADESENREGIMENDEATRIBUCIONDERENTAS` |
| EasyOCR (`lang=["es"]`) | 33.8 s | 413 | `ENTIDADES EN RÉGIMEN DE ATRIBUCIÓN DE RENTAS.` |

EasyOCR reports *fewer* text items while producing *more* usable text: RapidOCR
was fragmenting words, inflating the count with noise. Item count is not a
quality metric.

## Decision

Use `EasyOcrOptions(lang=["es"])`.

## Consequences

- Scanned documents become readable rather than merely non-empty.
- OCR takes roughly twice as long. Combined with the fallback in ADR 0001, the
  worst case is ~37 s, which makes background threading mandatory.
- `easyocr` is an additional runtime dependency that downloads its own models on
  first use, adding to the packaging problem tracked in the PyInstaller spike.
- Output is still imperfect (`FISICAS` for `FÍSICAS`). Users must be told when a
  result came from OCR.

## Alternatives rejected

- **Tesseract.** Likely the best Spanish accuracy, but it is a native binary that
  must be installed separately and bundled into the Windows executable. The
  distribution cost outweighs the marginal gain over EasyOCR.
- **Tuning RapidOCR's language.** `RapidOcrOptions()` requests an ONNX backend
  that is not installed, and its models are not built for Spanish regardless.