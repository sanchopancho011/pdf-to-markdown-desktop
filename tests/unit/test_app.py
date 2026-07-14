"""Unit tests for the user interface module.

Tkinter widgets are not instantiated here: creating a real window requires a
display, which continuous integration runners do not have. These tests cover
what can be verified without one.
"""

import sys


def test_importing_app_does_not_import_docling() -> None:
    """The lazy import must survive the user interface layer."""
    import pdf2md.app  # noqa: F401

    assert "docling" not in sys.modules, (
        "Importing the interface pulled in Docling. Keep the import inside "
        "convert_pdf_to_markdown."
    )


def test_app_handles_empty_conversion_error() -> None:
    """The interface must import the error it claims to handle.

    Cheap, but it catches a real mistake: renaming or removing the exception in
    converter.py while leaving a dangling `except` clause behind.
    """
    from pdf2md.app import EmptyConversionError

    assert issubclass(EmptyConversionError, Exception)
