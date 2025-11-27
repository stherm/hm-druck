import os
from PyPDF2 import PdfReader, PdfWriter, PageObject, Transformation

MM_PER_POINT = 0.352778  # mm/point

A_SIZES_MM = {
    "A0": (841, 1189),
    "A1": (594, 841),
    "A2": (420, 594),
    "A3": (297, 420),
    "A4": (210, 297),
    "A5": (148, 210),
    "A6": (105, 148),
    "A7": (74, 105),
    "A8": (52, 74),
}


def get_page_size_mm(page):
    box = page.mediabox
    width_pt = float(box.upper_right[0]) - float(box.lower_left[0])
    height_pt = float(box.upper_right[1]) - float(box.lower_left[1])
    width_mm = width_pt * MM_PER_POINT
    height_mm = height_pt * MM_PER_POINT
    return width_mm, height_mm


def classify_page_size(width_mm, height_mm, tolerance=5):
    for size, (w_mm, h_mm) in A_SIZES_MM.items():
        if (abs(width_mm - w_mm) < tolerance and abs(height_mm - h_mm) < tolerance) or \
           (abs(width_mm - h_mm) < tolerance and abs(height_mm - w_mm) < tolerance):
            return size
    return "other"


def collect_pages_by_size(pdf_directory):
    pdf_files = sorted(
        f for f in os.listdir(pdf_directory) if f.lower().endswith(".pdf")
    )

    pages_by_size = {
        size: [] for size in ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "other"]
    }

    for filename in pdf_files:
        path = os.path.join(pdf_directory, filename)
        reader = PdfReader(path)
        for page_index, page in enumerate(reader.pages):
            width_mm, height_mm = get_page_size_mm(page)
            size = classify_page_size(width_mm, height_mm)
            pages_by_size[size].append(
                {"path": path, "page_index": page_index}
            )

    return pages_by_size



def add_single_pages(writer, entries):
    by_path = {}
    for info in entries:
        by_path.setdefault(info["path"], []).append(info["page_index"])

    for path, indices in by_path.items():
        reader = PdfReader(path)
        for idx in indices:
            writer.add_page(reader.pages[idx])


def merge_two_pages_side_by_side(page_left, page_right):
    page_width = float(page_left.mediabox.width)
    page_height = float(page_left.mediabox.height)

    merged = PageObject.create_blank_page(width=page_width * 2, height=page_height)

    merged.merge_page(page_right)
    merged.add_transformation(Transformation().translate(tx=page_width, ty=0))
    merged.merge_page(page_left)

    return merged


def add_two_up_pages(writer, entries):
    for i in range(0, len(entries), 2):
        info_left = entries[i]
        info_right = entries[i + 1] if i + 1 < len(entries) else None

        reader_left = PdfReader(info_left["path"])
        page_left = reader_left.pages[info_left["page_index"]]

        if info_right is not None:
            reader_right = PdfReader(info_right["path"])
            page_right = reader_right.pages[info_right["page_index"]]
            merged = merge_two_pages_side_by_side(page_left, page_right)
        else:
            page_width = float(page_left.mediabox.width)
            page_height = float(page_left.mediabox.height)
            merged = PageObject.create_blank_page(width=page_width * 2, height=page_height)
            merged.merge_page(page_left)

        writer.add_page(merged)


def write_imposed_pdfs(pages_by_size, output_directory):
    os.makedirs(output_directory, exist_ok=True)

    output_files = {}

    a0_writer = PdfWriter()
    a0_single = pages_by_size.get("A0", []) or []
    a1_two_up = pages_by_size.get("A1", []) or []

    if a0_single:
        add_single_pages(a0_writer, a0_single)
    if a1_two_up:
        add_two_up_pages(a0_writer, a1_two_up)

    if len(a0_writer.pages) > 0:
        a0_path = os.path.join(output_directory, "A0_output.pdf")
        with open(a0_path, "wb") as f:
            a0_writer.write(f)
        output_files["A0"] = a0_path

    a2_writer = PdfWriter()
    a2_single = pages_by_size.get("A2", []) or []
    a3_all = pages_by_size.get("A3", []) or []

    if a2_single:
        add_single_pages(a2_writer, a2_single)

    pair_count = (len(a3_all) // 2) * 2
    a3_pairs = a3_all[:pair_count]
    a3_leftover = a3_all[pair_count:]

    if a3_pairs:
        add_two_up_pages(a2_writer, a3_pairs)

    if len(a2_writer.pages) > 0:
        a2_path = os.path.join(output_directory, "A2_output.pdf")
        with open(a2_path, "wb") as f:
            a2_writer.write(f)
        output_files["A2"] = a2_path

    if a3_leftover:
        a3_writer = PdfWriter()
        add_single_pages(a3_writer, a3_leftover)
        if len(a3_writer.pages) > 0:
            a3_path = os.path.join(output_directory, "A3_output.pdf")
            with open(a3_path, "wb") as f:
                a3_writer.write(f)
            output_files["A3"] = a3_path

    a4_writer = PdfWriter()
    a4_single = pages_by_size.get("A4", []) or []
    a5_two_up = pages_by_size.get("A5", []) or []

    if a4_single:
        add_single_pages(a4_writer, a4_single)
    if a5_two_up:
        add_two_up_pages(a4_writer, a5_two_up)

    if len(a4_writer.pages) > 0:
        a4_path = os.path.join(output_directory, "A4_output.pdf")
        with open(a4_path, "wb") as f:
            a4_writer.write(f)
        output_files["A4"] = a4_path

    return output_files
