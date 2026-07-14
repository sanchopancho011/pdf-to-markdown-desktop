"""Unit tests for the user interface module.

Tkinter widgets are not instantiated here: creating a real window requires a
display, which continuous integration runners do not have. These tests cover
what can be verified without one.
"""

import queue
import sys
from pathlib import Path

from pdf2md.app import ConversionOutcome, _run_conversion


def test_importing_app_does_not_import_docling() -> None:
    """The lazy import must survive the user interface layer."""
    import pdf2md.app  # noqa: F401

    assert "docling" not in sys.modules, (
        "Importing the interface pulled in Docling. Keep the import inside "
        "convert_pdf_to_markdown."
    )


def test_worker_reports_errors_instead_of_dying_silently(tmp_path: Path) -> None:
    """An exception escaping a worker thread would leave the UI waiting forever.

    Uses a missing file to provoke a real failure without invoking Docling.
    """
    outbox: queue.Queue[ConversionOutcome] = queue.Queue()

    _run_conversion(tmp_path / "missing.pdf", tmp_path, outbox)

    outcome = outbox.get_nowait()
    assert outcome.markdown_path is None
    assert isinstance(outcome.error, FileNotFoundError)


def test_conversion_outcome_carries_the_exception_not_a_string() -> None:
    """The worker reports what happened; the interface decides how to say it."""
    error = ValueError("File is not a PDF")

    outcome = ConversionOutcome(error=error)

    assert outcome.error is error
