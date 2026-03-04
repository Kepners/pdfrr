# PDFRR — Architecture

## Current Architecture (Phase 1 — Python)

```
PDFRR/
├── pdf_tool/
│   ├── app.py              # Main app (UI + PDF logic combined)
│   │   ├── Brand palette   # Color constants (BG, CYAN, AMBER, etc.)
│   │   ├── Folder helpers  # get_app_folder(), scan_folder()
│   │   ├── PDF logic       # do_split(), do_merge(), extract_drawing_title()
│   │   └── App class       # customtkinter UI
│   ├── logo.png / .ico     # App icons
│   ├── mockup.html         # UI design mockup (phone-frame concept)
│   └── PDF Tool.spec       # PyInstaller build config
└── split_pdf.py            # Standalone headless split script
```

### PDF Processing Stack
```
Input PDF
    │
    ├─→ pdfplumber ──→ extract_drawing_title()  (reads title block text)
    │
    └─→ pypdf ────────→ PdfReader / PdfWriter   (split/merge pages)
```

### Build Pipeline
```
python app.py                  # Dev run
pyinstaller "PDF Tool.spec"    # Build
    └─→ dist/PDF Tool.exe      # Portable output (no install)
```

---

## Planned Architecture (Phase 2 — Electron)

```
pdfrr/
├── electron/
│   ├── main.js              # Main process: file system, PDF operations
│   ├── preload.js           # IPC bridge
│   └── pdf-worker.js        # PDF processing (Node worker thread)
├── src/
│   ├── App.jsx              # Main UI
│   ├── SplitPanel.jsx       # Split half
│   ├── MergePanel.jsx       # Merge half
│   └── styles.css           # Brand styles
├── assets/
│   └── logo.png / .ico
└── package.json
```

### Phase 2 PDF Stack Options
| Library | Pros | Cons |
|---------|------|------|
| `pdf-lib` | Pure JS, fast, full control | No text extraction |
| `pdfjs-dist` | Mozilla, text extraction | Larger bundle |
| `node-poppler` | Battle-tested | Native binary dependency |

---

## Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Portable EXE | Yes | Core requirement — drop-and-run |
| Combined UI+logic | Phase 1: Yes | Simplicity for MVP |
| Dark theme only | Yes | Target users are engineers |
| Phone-frame mockup | Design concept | May ship as mobile app too |

---

*Last Updated: 2026-03-04*
