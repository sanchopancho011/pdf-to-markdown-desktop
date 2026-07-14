"""Conversion of PDF documents into Markdown."""

from pathlib import Path


def validate_pdf_path(pdf_path: str | Path) -> Path:
    """Validate that the given path points to an existing PDF file.

    Args:
        pdf_path: Path to the PDF document.

    Returns:
        The validated path.

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


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    output_directory: str | Path,
) -> Path:
    """Convert a PDF document into a Markdown file.

    Args:
        pdf_path: Path to the source PDF document.
        output_directory: Directory where the Markdown file will be written.

    Returns:
        The path of the generated Markdown file.
    """
    # Imported here, not at module level, so that importing this module stays
    # cheap: unit tests and the user interface must not pay Docling's import cost.
    from docling.document_converter import DocumentConverter

    source_path = validate_pdf_path(pdf_path)
    destination = create_output_directory(output_directory)

    converter = DocumentConverter()
    conversion_result = converter.convert(source_path)
    markdown_text = conversion_result.document.export_to_markdown()

    markdown_path = build_output_path(source_path, destination)
    markdown_path.write_text(markdown_text, encoding="utf-8")

    return markdown_path
