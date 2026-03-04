# PDFRR — Specification

## Overview
Portable PDF split & merge utility. Drop the EXE next to PDFs, run it, use it. No install, no config, no cloud.

## Current Status
**Phase 1 COMPLETE** — Python/customtkinter desktop app (PyInstaller EXE)

---

## Core Goals
- [x] Split multi-page PDF into individual pages
- [x] Merge multiple PDFs into one
- [x] Auto-detect mode (merge if 2+ PDFs present, split if 1)
- [x] Engineering drawing title extraction (reads title blocks)
- [x] Drag-to-reorder merge list
- [x] Portable EXE — zero install

## Phase 2 Goals (TBD)
- [ ] Electron rebuild (web tech, easier to extend + distribute)
- [ ] Drag-and-drop file support
- [ ] Page range selection for splits
- [ ] PDF preview thumbnails
- [ ] Monetization (one-time purchase?)
- [ ] Auto-update mechanism

---

## Target Users
- Engineers dealing with large multi-page drawing PDFs
- Office workers merging scanned documents
- Anyone who needs quick split/merge without Adobe

## Key UX Principles
- **Zero friction**: App opens in the right mode automatically
- **No config file**: Everything is inferred from what's in the folder
- **Dark UI**: Matches the dark, professional aesthetic of the logo

---

## Technical Requirements (Phase 1 — Current)
- Python 3.10+
- customtkinter, pdfplumber, pypdf, Pillow
- PyInstaller (single EXE output)
- Windows 10+ target

## Technical Requirements (Phase 2 — Electron)
- Electron + Node.js
- pdf-lib or pdfjs for PDF manipulation
- Vite + React (or vanilla JS for minimal footprint)
- electron-builder for distribution

---

## Design System
See `CLAUDE.md` for full color palette.

Primary: `#0CEEDE` teal-cyan (split/CTAs)
Accent: `#F59E0B` amber (merge)
Background: `#0D1218` deep navy

---

*Status: Phase 1 Complete — Phase 2 Planning*
*Last Updated: 2026-03-04*
