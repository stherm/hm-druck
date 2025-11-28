import os
import platform
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from .sort import collect_pages_by_size, write_imposed_pdfs
from .config import load_config, save_config

WINDOWS = platform.system() == "Windows"

print_module = None
if WINDOWS:
    try:
        from . import print as print_module
    except Exception as e:
        print("Could not import print module:", e)
        print_module = None


class PdfSortPrintGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("HM – PDF sortieren & drucken")

        # Konfiguration laden
        self.config = load_config()

        self.root.geometry("900x520")
        self.root.minsize(800, 420)

        self._configure_style()
        self._build_layout()
        self._center_window()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------------------------------------
    # Styling / Layout
    # ---------------------------------------------------------

    def _configure_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Main.TFrame", background="#f5f5f7")
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background="#f5f5f7")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#555555", background="#f5f5f7")
        style.configure("TLabel", font=("Segoe UI", 10), background="#f5f5f7")
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("Status.TLabel", font=("Segoe UI", 9), background="#e5e5e7")

    def _build_layout(self):
        self.root.configure(bg="#f5f5f7")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Header
        header_frame = ttk.Frame(self.root, style="Main.TFrame")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))

        header_label = ttk.Label(header_frame, text="PDF sortieren & drucken", style="Header.TLabel")
        header_label.grid(row=0, column=0, sticky="w")

        subheader_label = ttk.Label(
            header_frame,
            text="PDF-Seiten nach Format sortieren, 2-up montieren (A1→A0, A3→A2, A5→A4) und optional drucken.",
            style="SubHeader.TLabel",
        )
        subheader_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Hauptbereich
        main_frame = ttk.Frame(self.root, style="Main.TFrame")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=8)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        self._build_left_printer_panel(main_frame)
        self._build_right_job_panel(main_frame)

        # Statusleiste
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=2, column=0, sticky="ew")
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Bereit.")
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style="Status.TLabel",
            anchor="w",
            padding=(10, 3),
        )
        status_label.grid(row=0, column=0, sticky="ew")

        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=160)
        self.progress.grid(row=0, column=1, padx=(0, 10), pady=4, sticky="e")

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = int((sw - w) / 2)
        y = int((sh - h) / 3)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ---------------------------------------------------------
    # Linkes Panel: Drucker
    # ---------------------------------------------------------

    def _build_left_printer_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Drucker (A0 / A2 / A3 / A4)")
        frame.grid(row=0, column=0, padx=(0, 8), pady=4, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        self.printer_values = self._load_printer_values()
        self.printer_combos = {}

        cfg_printers = self.config.get("printers") or {}

        row = 0
        for fmt in ["A0", "A2", "A3", "A4"]:
            ttk.Label(frame, text=f"{fmt}-Drucker:").grid(
                row=row, column=0, padx=6, pady=6, sticky="w"
            )
            combo = ttk.Combobox(
                frame,
                values=self.printer_values,
                state="readonly",
                width=32,
            )
            combo.grid(row=row, column=1, padx=6, pady=6, sticky="ew")

            saved = cfg_printers.get(fmt)
            if saved and saved in self.printer_values:
                combo.set(saved)
            elif self.printer_values:
                combo.current(0)

            self.printer_combos[fmt] = combo
            row += 1

        info_text = ""
        if not WINDOWS or print_module is None:
            info_text = "Drucken ist nur unter Windows mit eingerichtetem Drucker verfügbar."
        elif self.printer_values and self.printer_values[0].startswith("["):
            info_text = self.printer_values[0]

        if info_text:
            info_label = ttk.Label(
                frame,
                text=info_text,
                style="SubHeader.TLabel",
                wraplength=260,
            )
            info_label.grid(row=row, column=0, columnspan=2, padx=6, pady=(4, 2), sticky="w")

    def _load_printer_values(self):
        if WINDOWS and print_module is not None:
            try:
                printers = print_module.get_installed_printers()
                if not printers:
                    return ["[Keine Drucker gefunden]"]
                return printers
            except Exception as e:
                print("Error getting printers:", e)
                return ["[Fehler beim Laden der Drucker]"]
        else:
            return ["[Windows-Drucker nicht verfügbar]"]

    # ---------------------------------------------------------
    # Rechtes Panel: Job-Einstellungen
    # ---------------------------------------------------------

    def _build_right_job_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Auftragseinstellungen")
        frame.grid(row=0, column=1, padx=(8, 0), pady=4, sticky="nsew")
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(3, weight=1)

        last_source = self.config.get("last_source", "")
        last_target = self.config.get("last_target", "")

        ttk.Label(frame, text="Quellordner:").grid(
            row=0, column=0, padx=6, pady=(8, 4), sticky="w"
        )
        self.source_var = tk.StringVar(value=last_source)
        entry_source = ttk.Entry(frame, textvariable=self.source_var)
        entry_source.grid(row=0, column=1, padx=6, pady=(8, 4), sticky="ew")
        btn_source = ttk.Button(frame, text="Durchsuchen…", command=self.browse_source)
        btn_source.grid(row=0, column=2, padx=6, pady=(8, 4))

        ttk.Label(frame, text="Zielordner:").grid(
            row=1, column=0, padx=6, pady=4, sticky="w"
        )
        self.target_var = tk.StringVar(value=last_target)
        entry_target = ttk.Entry(frame, textvariable=self.target_var)
        entry_target.grid(row=1, column=1, padx=6, pady=4, sticky="ew")
        btn_target = ttk.Button(frame, text="Durchsuchen…", command=self.browse_target)
        btn_target.grid(row=1, column=2, padx=6, pady=4)

        # Log-Toggle
        self.log_visible = False
        self.log_toggle_btn = ttk.Button(
            frame,
            text="Log anzeigen ▾",
            command=self._toggle_log,
        )
        self.log_toggle_btn.grid(row=2, column=1, columnspan=2,
                                 padx=6, pady=(6, 2), sticky="e")

        # Log Widgets (anfangs versteckt)
        self.log_label = ttk.Label(frame, text="Protokoll:")

        self.log_text = scrolledtext.ScrolledText(
            frame,
            height=9,
            wrap="word",
            state="disabled",
            font=("Segoe UI", 9),
        )
        self.log_text.tag_configure("INFO", foreground="#1f6feb")
        self.log_text.tag_configure("ERROR", foreground="#d73a49")
        self.log_text.tag_configure("WARN", foreground="#b08800")

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=(8, 8), sticky="e")
        btn_frame.columnconfigure(0, weight=1)

        btn_sort = ttk.Button(btn_frame, text="Nur sortieren", command=self.on_sort_only_clicked)
        btn_sort.grid(row=0, column=0, padx=(0, 8))

        btn_print = ttk.Button(
            btn_frame,
            text="Sortieren & drucken",
            style="Accent.TButton",
            command=self.on_print_clicked,
        )
        btn_print.grid(row=0, column=1)

        if not WINDOWS or print_module is None:
            btn_print.state(["disabled"])

        self._log("Bereit.")

    # ---------------------------------------------------------
    # Log-Handling
    # ---------------------------------------------------------

    def _show_log_widgets(self):
        if not self.log_visible:
            self.log_label.grid(row=3, column=0, padx=6, pady=(4, 2), sticky="nw")
            self.log_text.grid(row=3, column=1, columnspan=2,
                               padx=6, pady=(4, 4), sticky="nsew")
            self.log_visible = True
            self.log_toggle_btn.config(text="Log ausblenden ▴")

    def _hide_log_widgets(self):
        if self.log_visible:
            self.log_label.grid_remove()
            self.log_text.grid_remove()
            self.log_visible = False
            self.log_toggle_btn.config(text="Log anzeigen ▾")

    def _toggle_log(self):
        if self.log_visible:
            self._hide_log_widgets()
        else:
            self._show_log_widgets()

    # ---------------------------------------------------------
    # Datei-Dialoge
    # ---------------------------------------------------------

    def browse_source(self):
        path = filedialog.askdirectory(title="Quellordner auswählen")
        if path:
            self.source_var.set(path)
            self._log(f"Quellordner gesetzt: {path}")

    def browse_target(self):
        path = filedialog.askdirectory(title="Zielordner auswählen")
        if path:
            self.target_var.set(path)
            self._log(f"Zielordner gesetzt: {path}")

    # ---------------------------------------------------------
    # Nur sortieren
    # ---------------------------------------------------------

    def on_sort_only_clicked(self):
        source, target = self._validate_paths()
        if not source:
            return

        self._set_status("Seiten werden sortiert und montiert …")
        self._log(f"Starte »Nur sortieren« von '{source}' nach '{target}'")
        self._start_progress()
        self.root.update_idletasks()

        try:
            pages_by_size = collect_pages_by_size(source)
            self._log("Seiten nach Format gesammelt.")
            output_files = write_imposed_pdfs(pages_by_size, target)
            self._log(f"Ausgabe-PDFs erstellt: {output_files}")
        except Exception as e:
            self._stop_progress()
            self._set_status("Fehler beim Sortieren.")
            self._log(f"Fehler beim Erstellen der Ausgabe-PDFs: {e}", level="ERROR")
            messagebox.showerror("Fehler", f"Fehler beim Erstellen der Ausgabe-PDFs:\n{e}")
            return

        self._stop_progress()

        if not output_files:
            self._set_status("Keine Seiten zu verarbeiten.")
            self._log("Keine Seiten gefunden, die verarbeitet werden können.", level="WARN")
            messagebox.showinfo("Info", "Keine Seiten gefunden, die verarbeitet werden können.")
            return

        self._save_current_config()

        self._set_status("Sortieren abgeschlossen (kein Druck).")
        self._log("Sortieren erfolgreich abgeschlossen (kein Druck).")
        messagebox.showinfo(
            "Nur sortieren",
            "Ausgabe-PDFs wurden erfolgreich erstellt.\nEs wurde nichts gedruckt."
        )

    # ---------------------------------------------------------
    # Sortieren & Drucken
    # ---------------------------------------------------------

    def on_print_clicked(self):
        source, target = self._validate_paths()
        if not source:
            return

        self._set_status("Seiten werden sortiert und montiert …")
        self._log(f"Starte »Sortieren & drucken« von '{source}' nach '{target}'")
        self._start_progress()
        self.root.update_idletasks()

        try:
            pages_by_size = collect_pages_by_size(source)
            self._log("Seiten nach Format gesammelt.")
            output_files = write_imposed_pdfs(pages_by_size, target)
            self._log(f"Ausgabe-PDFs erstellt: {output_files}")
        except Exception as e:
            self._stop_progress()
            self._set_status("Fehler beim Sortieren.")
            self._log(f"Fehler beim Erstellen der Ausgabe-PDFs: {e}", level="ERROR")
            messagebox.showerror("Fehler", f"Fehler beim Erstellen der Ausgabe-PDFs:\n{e}")
            return

        if not output_files:
            self._stop_progress()
            self._set_status("Keine Seiten zu verarbeiten.")
            self._log("Keine Seiten gefunden, die verarbeitet werden können.", level="WARN")
            messagebox.showinfo("Info", "Keine Seiten gefunden, die verarbeitet werden können.")
            return

        printer_settings = self._build_printer_settings()
        self._log(f"Drucker-Einstellungen: {printer_settings}")

        if WINDOWS and print_module is not None and printer_settings:
            self._set_status("Druckaufträge werden gesendet …")
            self.root.update_idletasks()
            try:
                print_module.print_selected_formats(output_files, printer_settings)
                self._set_status("Druckaufträge gesendet.")
                self._log("Druckaufträge erfolgreich gesendet.")
                messagebox.showinfo("Fertig", "Ausgabe-PDFs wurden erstellt und an die Drucker gesendet.")
            except Exception as e:
                self._set_status("Fehler beim Drucken.")
                self._log(f"Fehler beim Drucken: {e}", level="ERROR")
                messagebox.showerror("Fehler", f"Fehler beim Drucken:\n{e}")
        else:
            self._set_status("Sortieren abgeschlossen (Druck nicht verfügbar).")
            self._log("Drucken auf diesem System nicht verfügbar.", level="WARN")
            messagebox.showinfo(
                "Info",
                "Ausgabe-PDFs wurden erfolgreich erstellt.\n"
                "Drucken ist nur unter Windows mit eingerichtetem Drucker verfügbar."
            )

        self._stop_progress()
        self._save_current_config()

    # ---------------------------------------------------------
    # Konfiguration speichern / Fenster schließen
    # ---------------------------------------------------------

    def _save_current_config(self):
        printers = {}
        for fmt, combo in self.printer_combos.items():
            val = combo.get()
            if val and not val.startswith("["):
                printers[fmt] = val

        cfg = {
            "printers": printers,
            "last_source": self.source_var.get().strip(),
            "last_target": self.target_var.get().strip(),
        }
        save_config(cfg)

    def _on_close(self):
        try:
            self._save_current_config()
        finally:
            self.root.destroy()

    # ---------------------------------------------------------
    # Hilfsfunktionen
    # ---------------------------------------------------------

    def _validate_paths(self):
        source = self.source_var.get().strip()
        target = self.target_var.get().strip()

        if not source or not os.path.isdir(source):
            messagebox.showerror("Fehler", "Bitte einen gültigen Quellordner auswählen.")
            return None, None
        if not target:
            messagebox.showerror("Fehler", "Bitte einen Zielordner auswählen.")
            return None, None

        return source, target

    def _build_printer_settings(self):
        """
        Liest die Combobox-Werte aus und baut daraus das printer_settings-Dict
        für A0, A2, A3, A4. Einträge mit Platzhalter-Text werden ignoriert.
        """
        settings = {}
        for fmt in ["A0", "A2", "A3", "A4"]:
            combo = self.printer_combos[fmt]
            value = combo.get()
            if not value or value.startswith("["):
                continue

            settings[fmt] = {
                "printer_name": value,
                "orientation": "landscape",
                "print_quality": "medium",
                "color": True,
            }

        return settings

    def _set_status(self, text: str):
        self.status_var.set(text)

    def _start_progress(self):
        try:
            self.progress.start(10)
        except tk.TclError:
            pass

    def _stop_progress(self):
        try:
            self.progress.stop()
        except tk.TclError:
            pass

    def _log(self, message: str, level: str = "INFO"):
        level = level.upper()
        if level not in ("INFO", "ERROR", "WARN"):
            level = "INFO"

        if not hasattr(self, "log_text"):
            return

        prefix = f"[{level}] "
        self.log_text.configure(state="normal")
        self.log_text.insert("end", prefix + message + "\n", level)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


def main():
    root = tk.Tk()
    PdfSortPrintGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

