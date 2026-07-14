"""Conversion of PDF documents into Markdown."""

from pathlib import Path


class EmptyConversionError(RuntimeError):
    """Raised when a conversion succeeds but extracts no usable text.

    Docling reports SUCCESS for scanned PDFs with no text layer, returning only
    image placeholders. Technically correct, practically useless: the caller must
    be able to tell "it finished" apart from "the result is worth having".
    """


def validate_pdf_path(pdf_path: str | Path) -> Path:
    """Validate that the given path points to an existing PDF file."""
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
    """
    return bool(getattr(document, "texts", None) or getattr(document, "tables", None))


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    output_directory: str | Path,
) -> Path:
    """Convert a PDF document into a Markdown file.

    Raises:
        FileNotFoundError: If the source file does not exist.
        ValueError: If the source file is not a PDF.
        EmptyConversionError: If no text could be extracted.
    """
    # Imported here, not at module level, so that importing this module stays
    # cheap: unit tests and the user interface must not pay Docling's import cost.
    from docling.document_converter import DocumentConverter

    source_path = validate_pdf_path(pdf_path)
    destination = create_output_directory(output_directory)

    conversion_result = DocumentConverter().convert(source_path)
    document = conversion_result.document

    if not has_extractable_content(document):
        raise EmptyConversionError(
            f"No se pudo extraer texto de {source_path.name}. "
            "El documento parece ser escaneado o contener solo imágenes."
        )

    markdown_path = build_output_path(source_path, destination)
    markdown_path.write_text(document.export_to_markdown(), encoding="utf-8")

    return markdown_path
