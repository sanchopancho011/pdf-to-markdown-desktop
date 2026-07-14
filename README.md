# PDF to Markdown Desktop

[![CI](https://github.com/sanchopancho011/pdf-to-markdown-desktop/actions/workflows/ci.yml/badge.svg)](https://github.com/sanchopancho011/pdf-to-markdown-desktop/actions/workflows/ci.yml)

A Windows desktop application that converts PDF documents into structured
Markdown using [Docling](https://github.com/docling-project/docling).

## Why

Copying text out of a PDF destroys its structure: headings collapse, tables
break, lists lose their nesting. This application preserves that structure by
converting the document into clean Markdown, ready to be used in notes,
documentation or version control.

## Status

Under active development. See the [issues](../../issues) and
[milestones](../../milestones) for the current roadmap.

## Requirements

- Windows
- Python 3.12 or later

## Installation

```powershell
git clone https://github.com/sanchopancho011/pdf-to-markdown-desktop.git
cd pdf-to-markdown-desktop
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Development

```powershell
python -m pip install -r requirements-dev.txt
python -m pip install -e .

ruff format .        # Format the code
ruff check .         # Lint
mypy src             # Static type checks
pytest tests/unit    # Fast unit tests
pytest -m slow       # Real conversion tests (slow)
```

## Architecture

Docling is imported lazily inside `convert_pdf_to_markdown`. This keeps module
imports cheap, allows unit tests to run without the machine learning stack, and
lets continuous integration stay under two minutes.

Tests are split accordingly:

| Suite | Location | Docling required | Runs in CI |
|---|---|---|---|
| Unit | `tests/unit` | No | Every push and pull request |
| Integration | `tests/integration` | Yes | Windows workflow only |

## License

MIT. See [LICENSE](LICENSE).