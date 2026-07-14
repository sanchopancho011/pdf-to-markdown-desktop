"""Conversion of PDF documents into Markdown."""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Evaluated by the type checker, never at runtime. This keeps the lazy
    # import intact while still giving mypy the real type.
    from docling_core.types.doc.document import DoclingDocument


class EmptyConversionError(RuntimeError):
    """Raised when a conversion succeeds but extracts no usable text.

    Docling reports SUCCESS for scanned PDFs with no text layer, returning a
    document made only of image placeholders. Technically correct, practically
    useless: the caller must be able to tell "it finished" apart from "the
    result is worth having".
    """


def validate_pdf_path(pdf_path: str | Path) -> Path:
    """Validate that the given path points to an existing PDF file.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the path is not a file, or is not a PDF.
    """
    source_path = Path(pdf_path)

    if not source_path.exists():
        raise FileNotFoundError(f"File does not exist: {source_path}")

    if not source_path.is_file():
        raise ValueError(f"Path is not a file: {source_path}")

    if source_path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {source_path}")

    return source_path


def create_output_directory(output_directory: str | Path) -> Path:
    """Create the output directory if needed and return it."""
    destination = Path(output_directory)
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def build_output_path(source_path: Path, destination: Path) -> Path:
    """Return the Markdown path corresponding to a source PDF."""
    return destination / f"{source_path.stem}.md"


def has_extractable_content(document: object) -> bool:
    """Return whether a converted document contains any text or tables.

    A scanned PDF yields a document made only of pictures. Docling considers
    that a successful conversion; the user, holding an empty Markdown file,
    does not.

    Takes `object` rather than `DoclingDocument` on purpose: duck typing keeps
    this testable with a stub, so the empty-document case is covered without
    loading the machine learning stack.
    """
    return bool(getattr(document, "texts", None) or getattr(document, "tables", None))


def _convert_document(source_path: Path, *, force_ocr: bool) -> "DoclingDocument":
    """Run Docling over a PDF, optionally forcing full-page OCR.

    EasyOCR with Spanish is used instead of Docling's default engine, which is
    RapidOCR with Chinese-oriented models: it drops accents, runs words together
    and occasionally emits full-width punctuation. See
    docs/decisions/0002-ocr-engine.md
    """
    # Imported here, not at module level, so that importing this module stays
    # cheap: unit tests and the user interface must not pay Docling's import cost.
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    ocr_options = EasyOcrOptions(lang=["es"])
    ocr_options.force_full_page_ocr = force_ocr

    options = PdfPipelineOptions()
    options.do_ocr = True
    options.ocr_options = ocr_options

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )

    return converter.convert(source_path).document


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    output_directory: str | Path,
) -> Path:
    """Convert a PDF document into a Markdown file.

    OCR is a fallback, not a default: forcing it on a document that already
    carries a text layer is roughly eight times slower and produces worse text,
    because it replaces exact embedded characters with a visual guess. See
    docs/decisions/0001-ocr-fallback.md

    Args:
        pdf_path: Path to the source PDF document.
        output_directory: Directory where the Markdown file will be written.

    Returns:
        The path of the generated Markdown file.

    Raises:
        FileNotFoundError: If the source file does not exist.
        ValueError: If the source file is not a PDF.
        EmptyConversionError: If no text could be extracted, with or without OCR.
    """
    source_path = validate_pdf_path(pdf_path)
    destination = create_output_directory(output_directory)

    # First pass: trust the document's own text layer. It is ground truth.
    document = _convert_document(source_path, force_ocr=False)

    if not has_extractable_content(document):
        # Nothing came out: the document is scanned. OCR is the only option
        # left, and an imperfect transcription beats an empty file.
        document = _convert_document(source_path, force_ocr=True)

    if not has_extractable_content(document):
        raise EmptyConversionError(
            f"No se pudo extraer texto de {source_path.name}, ni siquiera con OCR. "
            "El documento puede estar vacío, dañado o ser ilegible."
        )

    markdown_path = build_output_path(source_path, destination)
    markdown_path.write_text(document.export_to_markdown(), encoding="utf-8")

    return markdown_path
