"""Tkinter user interface for the PDF to Markdown converter."""

import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, ttk

from pdf2md.converter import EmptyConversionError, convert_pdf_to_markdown

WINDOW_TITLE = "PDF a Markdown"
WINDOW_SIZE = "620x300"
POLL_INTERVAL_MS = 100


@dataclass(frozen=True)
class ConversionOutcome:
    """The result of a conversion, as handed back from the worker thread.

    Exactly one of `markdown_path` or `error` is set. Passing the exception
    object rather than a formatted string keeps the presentation decision in the
    interface, where it belongs.
    """

    markdown_path: Path | None = None
    error: Exception | None = None


def _run_conversion(
    pdf_path: Path,
    output_directory: Path,
    outbox: "queue.Queue[ConversionOutcome]",
) -> None:
    """Convert a document and post the outcome to the queue.

    Runs in a worker thread. It must never touch a Tkinter widget: Tkinter is
    not thread-safe, and doing so causes rare, unreproducible crashes. The queue
    is the only channel back to the interface.
    """
    try:
        markdown_path = convert_pdf_to_markdown(pdf_path, output_directory)
    except Exception as error:  # noqa: BLE001
        # Every exception is captured, including unexpected ones. An exception
        # escaping a worker thread dies in silence: the thread ends, and the
        # interface waits for a result that will never arrive.
        outbox.put(ConversionOutcome(error=error))
    else:
        outbox.put(ConversionOutcome(markdown_path=markdown_path))


class ConverterWindow(ttk.Frame):
    """Main application window."""

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root, padding=16)
        self.root = root
        self.pdf_path: Path | None = None
        self.output_directory: Path | None = None
        self.outbox: queue.Queue[ConversionOutcome] = queue.Queue()

        self.pdf_label = ttk.Label(self, text="Ningún PDF seleccionado")
        self.output_label = ttk.Label(self, text="Ninguna carpeta seleccionada")
        self.status_label = ttk.Label(self, text="", wraplength=560, justify="left")
        self.select_pdf_button = ttk.Button(
            self, text="Seleccionar PDF", command=self.on_select_pdf
        )
        self.select_output_button = ttk.Button(
            self, text="Carpeta de destino", command=self.on_select_output
        )
        self.convert_button = ttk.Button(
            self, text="Convertir", command=self.on_convert, state=tk.DISABLED
        )

        self._build_layout()

    def _build_layout(self) -> None:
        """Place the widgets in the window."""
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(1, weight=1)

        self.select_pdf_button.grid(row=0, column=0, sticky="w", pady=4)
        self.pdf_label.grid(row=0, column=1, sticky="w", padx=12)

        self.select_output_button.grid(row=1, column=0, sticky="w", pady=4)
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
        """Start the conversion in a worker thread and begin polling for it."""
        if self.pdf_path is None or self.output_directory is None:
            return

        self._set_busy(busy=True)
        self.status_label.config(
            text="Convirtiendo... Los documentos escaneados pueden tardar un minuto."
        )

        worker = threading.Thread(
            target=_run_conversion,
            args=(self.pdf_path, self.output_directory, self.outbox),
            # A daemon thread does not keep the process alive. Without this,
            # closing the window mid-conversion would leave Python hanging until
            # the conversion finished.
            daemon=True,
        )
        worker.start()

        self.root.after(POLL_INTERVAL_MS, self._poll_outbox)

    def _poll_outbox(self) -> None:
        """Check for a finished conversion, and reschedule if there is none.

        Runs in the main thread, driven by Tkinter's own event loop, which is
        what makes it safe to touch widgets from here.
        """
        try:
            outcome = self.outbox.get_nowait()
        except queue.Empty:
            self.root.after(POLL_INTERVAL_MS, self._poll_outbox)
            return

        self._show_outcome(outcome)
        self._set_busy(busy=False)

    def _show_outcome(self, outcome: ConversionOutcome) -> None:
        """Report a finished conversion to the user."""
        if outcome.markdown_path is not None:
            self.status_label.config(text=f"Creado: {outcome.markdown_path.name}")
            return

        error = outcome.error

        if isinstance(error, EmptyConversionError):
            # Its message is already a complete sentence aimed at the user.
            self.status_label.config(text=str(error))
        elif isinstance(error, FileNotFoundError | ValueError):
            self.status_label.config(text=f"Error: {error}")
        else:
            self.status_label.config(text=f"La conversión ha fallado: {error}")

    def _set_busy(self, *, busy: bool) -> None:
        """Lock the interface while a conversion is running."""
        self.root.config(cursor="watch" if busy else "")

        state = tk.DISABLED if busy else tk.NORMAL
        self.select_pdf_button.config(state=state)
        self.select_output_button.config(state=state)

        if busy:
            self.convert_button.config(state=tk.DISABLED)
        else:
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
