"""
Split GSD-PLC Standard Details PDF into individual pages,
naming each file based on the DRAWING TITLE in the title block.
Duplicate titles get suffixed _001, _002, etc.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

import pdfplumber
from pypdf import PdfReader, PdfWriter

PDF_PATH = r"E:\Somersham\Bellway Standard Details\GSD-PLC Standard Details-3.5.pdf"
OUTPUT_DIR = r"E:\Somersham\Bellway Standard Details\Split Pages"


def sanitize(name: str) -> str:
    """Remove characters illegal in Windows filenames and trim."""
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name[:150]  # Keep filenames reasonable


def extract_drawing_title(page) -> str:
    """
    Extract the drawing title from the title block.
    The title block is in the right column (x0 > ~950).
    'DRAWING TITLE' label marks the start row.
    'Drawn' marks the end row.
    All words between those rows (in the right column) form the title.
    """
    words = page.extract_words(extra_attrs=['size'])

    # Find 'DRAWING' and 'TITLE' label in right column
    label_top = None
    for w in words:
        if w['text'] == 'DRAWING' and w['x0'] > 700:
            label_top = w['top']
            break

    if label_top is None:
        return ""

    # Find 'Drawn' below the label in right column
    drawn_top = None
    for w in words:
        if w['text'] == 'Drawn' and w['x0'] > 700 and w['top'] > label_top:
            drawn_top = w['top']
            break

    if drawn_top is None:
        drawn_top = label_top + 80  # fallback

    # Collect title words: right column, between label_top and drawn_top
    right_x_min = 970  # title block content x threshold
    title_words = [
        w for w in words
        if w['x0'] >= right_x_min
        and w['top'] > label_top
        and w['top'] < drawn_top - 2  # small margin
    ]

    if not title_words:
        return ""

    # Group words into lines by proximity in top coordinate
    title_words.sort(key=lambda w: (round(w['top'] / 4) * 4, w['x0']))
    lines = []
    current_line = []
    current_top = None
    tolerance = 6

    for w in title_words:
        if current_top is None or abs(w['top'] - current_top) <= tolerance:
            current_line.append(w['text'])
            current_top = w['top']
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [w['text']]
            current_top = w['top']
    if current_line:
        lines.append(' '.join(current_line))

    return ' '.join(lines)


def main():
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Reading: {PDF_PATH}")
    reader = PdfReader(PDF_PATH)
    total = len(reader.pages)
    print(f"Total pages: {total}")

    # Pass 1: extract all titles
    print("Extracting titles...")
    titles = []
    with pdfplumber.open(PDF_PATH) as pdf:
        for i, page in enumerate(pdf.pages):
            title = extract_drawing_title(page)
            if not title:
                # Fallback: use page number
                title = f"Page_{i+1:03d}"
            titles.append(title)
            if (i + 1) % 20 == 0:
                print(f"  Scanned {i+1}/{total} pages...")

    # Pass 2: count duplicates and build final filenames
    count = defaultdict(int)
    occurrence = defaultdict(int)
    for t in titles:
        count[t] += 1

    filenames = []
    for t in titles:
        if count[t] > 1:
            occurrence[t] += 1
            filenames.append(f"{sanitize(t)}_{occurrence[t]:03d}.pdf")
        else:
            filenames.append(f"{sanitize(t)}.pdf")

    # Pass 3: write individual PDFs
    print("Writing individual page PDFs...")
    for i, filename in enumerate(filenames):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        out_file = output_path / filename
        with open(out_file, 'wb') as f:
            writer.write(f)
        print(f"  [{i+1:3d}/{total}] {filename}")

    print(f"\nDone! {total} files written to:")
    print(f"  {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
