# PDFRR — `<PDF>`

## Project Overview

**`<PDF>`** (PDFRR) is a portable PDF split & merge utility for Windows. Drop it next to PDFs, run, one click. Smart enough to auto-detect drawing title blocks.

| Item | Value |
|------|-------|
| Type | Desktop App (Python → Electron migration pending) |
| Current Stack | Python 3, customtkinter, pdfplumber, pypdf, PyInstaller |
| Repo | github.com/Kepners/pdfrr |
| Distribution | Standalone `.exe` (PyInstaller) |
| Monetization | TBD |

---

## Key Files

| File | Purpose |
|------|---------|
| [pdf_tool/app.py](pdf_tool/app.py) | Main Python app — UI + PDF logic |
| [pdf_tool/logo.png](pdf_tool/logo.png) | App icon (dark navy + teal-cyan `<>` brackets) |
| [pdf_tool/mockup.html](pdf_tool/mockup.html) | UI mockup (phone-frame design concept) |
| [split_pdf.py](split_pdf.py) | Standalone split script (no UI) |

---

## Design System: Dark Navy + Teal-Cyan

| Name | Hex | Usage |
|------|-----|-------|
| Deep Navy | `#0D1218` | App background |
| Panel | `#111820` | Panel surfaces |
| Card | `#161E28` | Card backgrounds |
| Teal Cyan | `#0CEEDE` | Primary accent (split, CTAs) |
| Amber | `#F59E0B` | Secondary accent (merge) |
| Text | `#E8F0F8` | Near-white body text |
| Subtext | `#5A7080` | Secondary text |
| Border | `#1E2D38` | Borders / separators |

```css
:root {
  --bg: #0D1218;
  --cyan: #0CEEDE;
  --amber: #F59E0B;
  --text: #E8F0F8;
  --border: #1E2D38;
}
```

---

## Current Features

- **Split**: One PDF → individual pages (sequential numbering or drawing title extraction)
- **Merge**: Multiple PDFs → single merged file (drag-to-reorder, include/exclude toggle)
- **Auto-mode**: Detects 2+ PDFs → defaults to Merge; 1 PDF → defaults to Split
- **Title detection**: Reads engineering drawing title blocks from PDF content
- **Portable**: Drop EXE next to PDFs and run — no install needed

---

## Architecture

```
pdf_tool/
├── app.py          # Full app: UI (customtkinter) + PDF logic (pdfplumber, pypdf)
├── logo.png        # App icon (source)
├── logo.ico        # App icon (Windows)
├── mockup.html     # Design concept mockup
└── PDF Tool.spec   # PyInstaller build spec
```

**Build command:**
```bash
cd pdf_tool
pyinstaller "PDF Tool.spec"
# Output: dist/PDF Tool.exe (portable, no install)
```

---

## MCP Note
> Per user preference (2026-03-04): configure all MCP servers using Docker going forward.

---

*Created: 2026-03-04*
