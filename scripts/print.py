import os
import platform

WINDOWS = platform.system() == "Windows"

if WINDOWS:
    import win32print
    import win32api
    import win32con

def get_installed_printers():
    if not WINDOWS:
        return []

    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = win32print.EnumPrinters(flags)
    return [p[2] for p in printers]


def _print_pdf_windows(file_path, printer_name, orientation="landscape",
                       print_quality="medium", color=True):
    if not WINDOWS:
        raise RuntimeError("Printing is only supported on Windows.")

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    h_printer = win32print.OpenPrinter(printer_name)
    try:
        properties = win32print.GetPrinter(h_printer, 2)
        devmode = properties["pDevMode"]

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

        properties["pDevMode"] = devmode
        win32print.SetPrinter(h_printer, 2, properties, 0)

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


def print_selected_formats(output_files, printer_settings):
    if not WINDOWS:
        raise RuntimeError("Printing is only supported on Windows.")

    if not output_files:
        return

    formats_order = ["A0", "A2", "A3", "A4"]

    for fmt in formats_order:
        pdf_path = output_files.get(fmt)
        settings = printer_settings.get(fmt)

        if not pdf_path or not settings:
            continue

        printer_name = settings.get("printer_name")
        if not printer_name or printer_name.startswith("["):
            continue

        orientation = settings.get("orientation", "landscape")
        quality = settings.get("print_quality", "medium")
        color = settings.get("color", True)

        _print_pdf_windows(
            file_path=pdf_path,
            printer_name=printer_name,
            orientation=orientation,
            print_quality=quality,
            color=color,
        )

