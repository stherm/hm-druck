import os
import platform

WINDOWS = platform.system() == "Windows"
if WINDOWS:
    import win32print
    import win32api
    import win32con


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

