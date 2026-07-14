"""Tkinter user interface for the PDF to Markdown converter."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from pdf2md.converter import EmptyConversionError, convert_pdf_to_markdown

WINDOW_TITLE = "PDF a Markdown"
WINDOW_SIZE = "620x280"


class ConverterWindow(ttk.Frame):
    """Main application window."""

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=16)
        self.root = root
        self.pdf_path: Path | None = None
        self.output_directory: Path | None = None

        self.pdf_label = ttk.Label(self, text="Ningún PDF seleccionado")
        self.output_label = ttk.Label(self, text="Ninguna carpeta seleccionada")
        self.status_label = ttk.Label(self, text="", wraplength=560, justify="left")
        self.convert_button = ttk.Button(
            self,
            text="Convertir",
            command=self.on_convert,
            state=tk.DISABLED,
        )

        self._build_layout()

    def _build_layout(self) -> None:
        """Place the widgets in the window."""
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(1, weight=1)

        ttk.Button(self, text="Seleccionar PDF", command=self.on_select_pdf).grid(
            row=0, column=0, sticky="w", pady=4
        )
        self.pdf_label.grid(row=0, column=1, sticky="w", padx=12)

        ttk.Button(self, text="Carpeta de destino", command=self.on_select_output).grid(
            row=1, column=0, sticky="w", pady=4
        )
        self.output_label.grid(row=1, column=1, sticky="w", padx=12)

        self.convert_button.grid(row=2, column=0, sticky="w", pady=16)
        self.status_label.grid(row=3, column=0, columnspan=2, sticky="w")

    def on_select_pdf(self) -> None:
        """Ask the user for a PDF file."""
        selected = filedialog.askopenfilename(
            title="Seleccionar documento PDF",
            filetypes=[("Documentos PDF", "*.pdf")],
        )
        if not selected:
            return

        self.pdf_path = Path(selected)
        self.pdf_label.config(text=self.pdf_path.name)
        self.status_label.config(text="")
        self._refresh_convert_button()

    def on_select_output(self) -> None:
        """Ask the user for an output directory."""
        selected = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if not selected:
            return

        self.output_directory = Path(selected)
        self.output_label.config(text=str(self.output_directory))
        self.status_label.config(text="")
        self._refresh_convert_button()

    def _refresh_convert_button(self) -> None:
        """Enable the convert button only when both paths are selected."""
        ready = self.pdf_path is not None and self.output_directory is not None
        self.convert_button.config(state=tk.NORMAL if ready else tk.DISABLED)

    def on_convert(self) -> None:
        """Run the conversion and report the outcome.

        This blocks the event loop. Moving the conversion to a background thread
        is handled in a follow-up issue.
        """
        if self.pdf_path is None or self.output_directory is None:
            return

        self.convert_button.config(state=tk.DISABLED)
        self.status_label.config(text="Convirtiendo...")
        self.root.update_idletasks()

        try:
            markdown_path = convert_pdf_to_markdown(
                self.pdf_path, self.output_directory
            )
        except EmptyConversionError as error:
            self.status_label.config(text=str(error))
        except (FileNotFoundError, ValueError) as error:
            self.status_label.config(text=f"Error: {error}")
        except Exception as error:  # noqa: BLE001
            # Last resort: Docling can fail in ways we do not control, and the
            # application must report it instead of closing in the user's face.
            self.status_label.config(text=f"La conversión ha fallado: {error}")
        else:
            self.status_label.config(text=f"Creado: {markdown_path.name}")
        finally:
            self._refresh_convert_button()


def main() -> None:
    """Start the application."""
    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry(WINDOW_SIZE)
    root.columnconfigure(0, weight=1)

    ConverterWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
