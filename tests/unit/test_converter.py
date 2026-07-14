"""Unit tests for the converter module.

These tests must never trigger a real Docling conversion.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from pdf2md.converter import (
    build_output_path,
    create_output_directory,
    has_extractable_content,
    validate_pdf_path,
)


def test_validate_pdf_path_accepts_existing_pdf(tmp_path: Path) -> None:
    pdf_path = tmp_path / "document.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    assert validate_pdf_path(pdf_path) == pdf_path


def test_validate_pdf_path_accepts_uppercase_extension(tmp_path: Path) -> None:
    pdf_path = tmp_path / "document.PDF"
    pdf_path.write_bytes(b"%PDF-1.4")

    assert validate_pdf_path(pdf_path) == pdf_path


def test_validate_pdf_path_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        validate_pdf_path(tmp_path / "missing.pdf")


def test_validate_pdf_path_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a file"):
        validate_pdf_path(tmp_path)


def test_validate_pdf_path_rejects_non_pdf_file(tmp_path: Path) -> None:
    text_file = tmp_path / "document.txt"
    text_file.write_text("Not a PDF", encoding="utf-8")

    with pytest.raises(ValueError, match="not a PDF"):
        validate_pdf_path(text_file)


def test_create_output_directory_creates_missing_directory(tmp_path: Path) -> None:
    output_directory = tmp_path / "results"

    result = create_output_directory(output_directory)

    assert result == output_directory
    assert output_directory.is_dir()


def test_create_output_directory_accepts_existing_directory(tmp_path: Path) -> None:
    assert create_output_directory(tmp_path) == tmp_path


def test_build_output_path_replaces_extension(tmp_path: Path) -> None:
    source_path = tmp_path / "report.pdf"
    destination = tmp_path / "out"

    assert build_output_path(source_path, destination) == destination / "report.md"


def test_scanned_document_has_no_extractable_content() -> None:
    """A scanned PDF yields pictures only. Docling calls that a success."""
    scanned = SimpleNamespace(texts=[], tables=[], pictures=["page1", "page2"])

    assert has_extractable_content(scanned) is False


def test_document_with_text_has_extractable_content() -> None:
    document = SimpleNamespace(texts=["heading"], tables=[], pictures=[])

    assert has_extractable_content(document) is True


def test_document_with_only_tables_has_extractable_content() -> None:
    """A document made entirely of tables is still worth keeping."""
    document = SimpleNamespace(texts=[], tables=["table"], pictures=[])

    assert has_extractable_content(document) is True


def test_importing_converter_does_not_import_docling() -> None:
    """Docling must be imported lazily, inside the conversion function.

    Importing it at module level would force every unit test and the user
    interface to load the machine learning stack. This test guards that
    decision: if it fails, someone moved the import to the top of the module.

    Note: this relies on `addopts = "-m 'not slow'"` in pyproject.toml, which
    keeps the integration tests, the only ones that import Docling, out of this
    session.
    """
    assert "pdf2md.converter" in sys.modules

    assert "docling" not in sys.modules, (
        "Docling was imported at module level. Keep the import inside "
        "convert_pdf_to_markdown so unit tests stay fast."
    )
