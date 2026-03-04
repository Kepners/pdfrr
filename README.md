# `<PDF>` — PDFRR

> PDF split & merge utility. Drop it next to your PDFs, run it, done.

---

## What it does

- **Split** — One multi-page PDF → individual page files
- **Merge** — Multiple PDFs → one merged file (reorderable)
- **Smart auto-mode** — 2+ PDFs in folder = merge mode; 1 PDF = split mode
- **Drawing titles** — Auto-extracts engineering drawing title block text for file names

## Dev Setup

```bash
cd pdf_tool
pip install customtkinter pdfplumber pypdf Pillow pyinstaller
python app.py
```

## Build

```bash
cd pdf_tool
pyinstaller "PDF Tool.spec"
# → dist/PDF Tool.exe
```

---

*Built with Python + customtkinter*
