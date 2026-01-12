import os
import platform

WINDOWS = platform.system() == "Windows"
if WINDOWS:
    import win32print
    import win32api
    import win32con
else:
    win32print = None
    win32api = None
    win32con = None


def _print_pdf_windows(file_path, printer_name, orientation="landscape",
                       print_quality="medium", color=True):
    """
    Druckt eine einzelne PDF-Datei auf einen angegebenen Drucker (Windows).

    Hinweis:
    Wenn SetPrinter keine Rechte hat (Fehler 5), wird der Fehler ignoriert
    und trotzdem gedruckt – dann gelten die Standard-Druckereinstellungen.
    """
    if not WINDOWS:
        raise RuntimeError("Printing is only supported on Windows.")

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    h_printer = win32print.OpenPrinter(printer_name)
    try:
        props = win32print.GetPrinter(h_printer, 2)
        devmode = props["pDevMode"]

        try:
            if orientation == "landscape":
                devmode.Orientation = win32con.DMORIENT_LANDSCAPE
            else:
                devmode.Orientation = win32con.DMORIENT_PORTRAIT

            quality_map = {
                "draft": win32con.DMRES_DRAFT,
                "medium": win32con.DMRES_MEDIUM,
                "high": win32con.DMRES_HIGH,
            }
            devmode.PrintQuality = quality_map.get(print_quality, win32con.DMRES_MEDIUM)

            devmode.Color = win32con.DMCOLOR_COLOR if color else win32con.DMCOLOR_MONOCHROME

            props["pDevMode"] = devmode

            win32print.SetPrinter(h_printer, 2, props, 0)
        except Exception as e:
            pass

    finally:
        win32print.ClosePrinter(h_printer)

    win32api.ShellExecute(
        0,
        "printto",
        file_path,
        f'"{printer_name}"',
        ".",
        0
    )


def get_installed_printers():
    """
    Gibt eine Liste der installierten Druckernamen zurück.
    """
    if not WINDOWS:
        return []

    try:
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        printers = win32print.EnumPrinters(flags)
        return sorted([p[2] for p in printers if len(p) > 2])
    except Exception:
        return []


def print_selected_formats(output_files, printer_settings):
    """
    Druckt die generierten PDFs basierend auf den Einstellungen.

    output_files: Dictionary { "A0": "/path/to/a0.pdf", "A4": ... }
    printer_settings: Dictionary { "A0": { "printer_name": "...", "orientation": ... }, ... }
    """
    if not WINDOWS:
        raise RuntimeError("Printing is only supported on Windows.")

    for fmt, file_path in output_files.items():
        if fmt not in printer_settings:
            continue

        settings = printer_settings[fmt]
        printer_name = settings.get("printer_name")
        if not printer_name:
            continue

        _print_pdf_windows(
            file_path=file_path,
            printer_name=printer_name,
            orientation=settings.get("orientation", "landscape"),
            print_quality=settings.get("print_quality", "medium"),
            color=settings.get("color", True)
        )

