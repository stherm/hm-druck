<p align="center">
  <img src="assets/logo.png" alt="HM-Druck Logo" width="180">
</p>

# HM-Druck – PDF Sorting & Printing Tool

A utility for:
- sorting PDF pages by size (A0–A5),
- generating imposed 2-up sheets  
  (A1 → A0, A3 → A2, A5 → A4),
- creating output PDFs per target format,
- optionally printing them to selected Windows printers,
- offering a modern GUI with persistent settings.

Sorting works on all platforms.  
**Printing is Windows-only** (via pywin32).

---

## ✨ Features

### ✔ PDF Sorting (Cross-Platform)
- Processes all PDFs in a source directory.
- Detects the size of **each page individually**.
- Classifies pages into A-formats using millimeter geometry.
- Generates:
  - `A0_output.pdf`
  - `A2_output.pdf`
  - `A3_output.pdf` (for leftover single A3 pages)
  - `A4_output.pdf`

### ✔ Automatic 2-Up Imposition
- A1 → A0  
- A3 → A2  
- A5 → A4  
- Odd number of pages → last page is placed alone (half sheet).

### ✔ Modern GUI
- Tkinter-based, styled with a modern layout.
- Separate printer dropdowns for:
  - A0  
  - A2  
  - A3  
  - A4  
- Source / target directory selectors.
- Toggleable log window with color-coded messages (INFO / WARN / ERROR).
- “Sort only” or “Sort & print”.

### ✔ Persistent Configuration
Automatically stored:

- selected printers,
- last source path,
- last target path.

Config file location:

| Platform | Path |
|----------|------------------------------|
| Windows  | `%APPDATA%/hm-druck/config.json` |
| Linux/macOS | `~/.config/hm-druck/config.json` |

No admin rights required.

---

## 📁 Project Structure

```
hm-druck/
  main.py                  – Application entrypoint

  scripts/
    gui.py                 – Tkinter GUI (modern layout, printer selection)
    sort.py                – PDF parsing & 2-up imposition (A1→A0, A3→A2, ...)
    print.py               – Windows printing backend (pywin32)
    config.py              – persistent configuration (APPDATA / ~/.config)
    generate_test_pdfs.py  – creates random test PDFs in test/input/

  assets/
    hm-druck.ico           – application icon for Windows EXE

  test/
    input/                 – auto-generated test PDFs
    output/                – generated final PDF files (A0/A2/A3/A4)

  requirements.txt         – Python dependencies (used by GitHub CI)
  flake.nix                – Nix development environment
  README.md
````

---

## 🧪 Test PDFs

A helper script allows generating random PDFs in A-formats (A0–A5):

```bash
python scripts/generate_test_pdfs.py
````

Output is written to:

```
./test/input/
```

Each PDF will contain:

* its A-format,
* and a page number in the corner (for verification).

---

## 🛠 Development on NixOS

Enter the reproducible devshell:

```bash
nix develop
```

This provides:

* Python 3
* PyPDF2 / pypdf
* Tkinter
* PyInstaller
* ReportLab (for test PDFs)

Useful for working on Linux even if printing is Windows-only.

---

## 🏗 Building the EXE (Windows)

You can build the Windows executable in **two ways**:

---

### **Option A — Manual PyInstaller Build (from nix develop)**

Prepare an icon (recommended: 256×256 `.ico`) at:

```
assets/hm-druck.ico
```

Then run:

```powershell
pyinstaller --onefile --windowed --name "HM-Druck" --icon "assets/hm-druck.ico" main.py
```

The EXE will appear in:

```
dist/HM-Druck.exe
```

---

### **Option B — Nix Build (icon included automatically)**

The `flake.nix` defines a buildable package:

```bash
nix build .#hm-druck
```

This runs PyInstaller internally with:

* `--icon assets/hm-druck.ico`
* `--onefile`
* `--windowed`
* `--name HM-Druck`

Result:

```
./result/bin/HM-Druck.exe
```

> Note:
> EXE output only works on a Windows Nix environment.
> On Linux it still performs the build, but the binary is not executable.

---

## 🖼 Icon Handling

* Windows requires `.ico` format for EXE icons.
* You may design your icon in **SVG**, but PyInstaller needs a `.ico`.
* Using **a single 256×256 icon** is sufficient — Windows will scale it.

Place the icon here:

```
assets/hm-druck.ico
```

---

## 🚀 Running the Program

Sorting only:

```bash
python main.py
```

Or simply double-click the EXE on Windows.

---

## 📌 Known limitations

* Printing is supported on **Windows only**.
* Complex PDF transformations (rotations, mixed orientations)
  are simplified and may be improved in later versions.
