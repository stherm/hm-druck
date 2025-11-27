import os
import random

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A0, A1, A2, A3, A4, A5


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
INPUT_DIR = os.path.join(BASE_DIR, "test", "input")

PAGE_SIZES = {
    "A0": A0,
    "A1": A1,
    "A2": A2,
    "A3": A3,
    "A4": A4,
    "A5": A5,
}

def ensure_dirs():
    os.makedirs(INPUT_DIR, exist_ok=True)

def create_test_pdfs():
    ensure_dirs()
    print(f"Writing test PDFs to: {INPUT_DIR}")

    for fmt, pagesize in PAGE_SIZES.items():
        count = random.randint(1, 9)
        print(f"  - {fmt}: generating {count} file(s)")

        for i in range(1, count + 1):
            filename = f"{fmt}_{i}.pdf"
            path = os.path.join(INPUT_DIR, filename)

            c = canvas.Canvas(path, pagesize=pagesize)
            width, height = pagesize

            c.setFont("Helvetica-Bold", height / 20)
            c.drawCentredString(width / 2, height / 2, fmt)

            c.setFont("Helvetica", 12)
            label = f"{fmt} #{i}"
            margin = 20
            text_width = c.stringWidth(label, "Helvetica", 12)
            c.drawString(width - text_width - margin, margin, label)

            c.showPage()
            c.save()

    print("Done.")

if __name__ == "__main__":
    create_test_pdfs()

