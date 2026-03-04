"""
<PDF> — AnglePDF
Portable folder-aware PDF split & merge utility.
Drop next to PDFs, run, one click.
"""

import re
import sys
import threading
from pathlib import Path
from collections import defaultdict
from tkinter import filedialog
import tkinter as tk
import customtkinter as ctk


# ── Brand palette (from logo) ─────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG          = "#0D1218"   # deep navy — logo background
PANEL       = "#111820"   # slightly lighter panel
CARD        = "#161E28"   # card surfaces
CARD_HOV    = "#1C2430"
CYAN        = "#0CEEDE"   # logo primary — bright teal-cyan
CYAN_HOV    = "#0ACCC0"
CYAN_DIM    = "#0A2A28"   # dark tint of cyan for inactive icon bg
AMBER       = "#F59E0B"   # merge accent — warm contrast to cyan
AMBER_HOV   = "#D97706"
AMBER_DIM   = "#2A1E08"
SPLIT_BG    = "#0A1E1C"   # active split half
MERGE_BG    = "#1A1208"   # active merge half
TEXT        = "#E8F0F8"   # near-white
SUBTEXT     = "#5A7080"
DIM         = "#1A2030"
DIM2        = "#0F1520"
BORDER      = "#1E2D38"


# ── Folder helpers ────────────────────────────────────────────────────────────
def get_app_folder() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(sys.argv[0]).resolve().parent


def scan_folder(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir()
                  if p.is_file() and p.suffix.lower() == '.pdf')


# ── PDF logic ─────────────────────────────────────────────────────────────────
def sanitize(name: str) -> str:
    name = name.strip()
    name = re.sub(r'[\\/:*?"<>|]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name[:150]


def extract_drawing_title(page) -> str:
    try:
        words = page.extract_words(extra_attrs=['size'])
        label_top = None
        for w in words:
            if w['text'] == 'DRAWING' and w['x0'] > 700:
                label_top = w['top']
                break
        if label_top is None:
            return ""
        drawn_top = None
        for w in words:
            if w['text'] == 'Drawn' and w['x0'] > 700 and w['top'] > label_top:
                drawn_top = w['top']
                break
        if drawn_top is None:
            drawn_top = label_top + 80
        title_words = [w for w in words
                       if w['x0'] >= 970 and w['top'] > label_top
                       and w['top'] < drawn_top - 2]
        if not title_words:
            return ""
        title_words.sort(key=lambda w: (round(w['top'] / 4) * 4, w['x0']))
        lines, current_line, current_top = [], [], None
        for w in title_words:
            if current_top is None or abs(w['top'] - current_top) <= 6:
                current_line.append(w['text'])
                current_top = w['top']
            else:
                lines.append(' '.join(current_line))
                current_line = [w['text']]
                current_top = w['top']
        if current_line:
            lines.append(' '.join(current_line))
        return ' '.join(lines)
    except Exception:
        return ""


def get_page_count(pdf_path: Path) -> int:
    from pypdf import PdfReader
    return len(PdfReader(str(pdf_path)).pages)


def detect_uses_titles(pdf_path: Path) -> bool:
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages[:3]:
                if extract_drawing_title(page):
                    return True
        return False
    except Exception:
        return False


def do_split(pdf_path: Path, output_dir: Path, use_titles: bool,
             progress_cb, status_cb):
    import pdfplumber
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(pdf_path))
    total = len(reader.pages)
    stem = pdf_path.stem
    status_cb(f"Reading {total} pages…")

    if use_titles:
        titles = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                title = extract_drawing_title(page)
                titles.append(title if title else f"Page_{i+1:03d}")
                progress_cb((i + 1) / (total * 2))
                status_cb(f"Scanning {i+1}/{total}…")
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
        half = 0.5
    else:
        digits = len(str(total))
        filenames = [f"{stem}_{str(i+1).zfill(digits)}.pdf" for i in range(total)]
        half = 0.0

    output_dir.mkdir(parents=True, exist_ok=True)
    for i, filename in enumerate(filenames):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        with open(output_dir / filename, 'wb') as f:
            writer.write(f)
        progress_cb(half + (i + 1) / (total * (2 if use_titles else 1)))
        status_cb(f"Saving {i+1}/{total}  {filename[:45]}…")

    status_cb(f"Done! {total} files → {output_dir.name}/")
    progress_cb(1.0)


def do_merge(pdf_paths: list, output_file: Path, progress_cb, status_cb):
    from pypdf import PdfWriter
    writer = PdfWriter()
    total = len(pdf_paths)
    status_cb(f"Merging {total} files…")
    for i, p in enumerate(pdf_paths):
        writer.append(str(p))
        progress_cb((i + 1) / total)
        status_cb(f"Adding {i+1}/{total}  {p.name[:45]}…")
    with open(output_file, 'wb') as f:
        writer.write(f)
    status_cb(f"Done!  →  {output_file.name}")
    progress_cb(1.0)


# ── App ───────────────────────────────────────────────────────────────────────
def _res(name: str) -> Path:
    """Resolve bundled resource path — works both frozen and as script."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / name
    return Path(__file__).parent / name

LOGO_ICO = _res("logo.ico")
LOGO_PNG = _res("logo.png")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("<PDF>")
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        # Set window icon
        try:
            if LOGO_ICO.exists():
                self.iconbitmap(str(LOGO_ICO))
        except Exception:
            pass

        self._folder = get_app_folder()
        self._pdfs   = scan_folder(self._folder)
        self._mode   = "merge" if len(self._pdfs) >= 2 else "split"

        self._use_titles  = False
        self._titles_auto = False
        if self._pdfs:
            self._use_titles  = detect_uses_titles(self._pdfs[0])
            self._titles_auto = True

        self._merge_files  = list(self._pdfs)
        self._split_target = None

        self._left_frame = None
        self._right_frame = None
        self._toggle_left = None
        self._toggle_right = None
        self._mode_anim_after = None
        self._progress_anim_after = None
        self._progress_value = 0.0
        self._progress_target = 0.0

        self._build_home()

    # ── core helpers ──────────────────────────────────────────────────────────

    def _clear(self):
        for handle_name in ("_mode_anim_after", "_progress_anim_after"):
            handle = getattr(self, handle_name, None)
            if handle is not None:
                try:
                    self.after_cancel(handle)
                except Exception:
                    pass
                setattr(self, handle_name, None)
        self._toggle_left = None
        self._toggle_right = None
        self._left_frame = None
        self._right_frame = None
        for w in self.winfo_children():
            w.destroy()

    def _refresh(self):
        self._pdfs         = scan_folder(self._folder)
        self._merge_files  = list(self._pdfs)
        self._split_target = None
        self._mode         = "merge" if len(self._pdfs) >= 2 else "split"
        if self._pdfs:
            self._use_titles  = detect_uses_titles(self._pdfs[0])
            self._titles_auto = True
        self._build_home()

    # ── HOME ──────────────────────────────────────────────────────────────────

    def _build_home(self):
        self._clear()

        # ── Header bar ──
        bar = ctk.CTkFrame(self, fg_color=BG, height=54, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo image
        try:
            if LOGO_PNG.exists():
                from PIL import Image
                img = ctk.CTkImage(
                    light_image=Image.open(str(LOGO_PNG)),
                    dark_image=Image.open(str(LOGO_PNG)),
                    size=(32, 32)
                )
                ctk.CTkLabel(bar, image=img, text="").place(x=14, rely=0.5, anchor="w")
        except Exception:
            # fallback text badge
            badge = ctk.CTkFrame(bar, fg_color=CYAN_DIM, width=32, height=32, corner_radius=8)
            badge.place(x=14, rely=0.5, anchor="w")
            ctk.CTkLabel(badge, text="<>", font=("JetBrains Mono", 11, "bold"),
                         text_color=CYAN).place(relx=0.5, rely=0.5, anchor="center")

        # App name  <PDF>  with styled brackets
        name_f = ctk.CTkFrame(bar, fg_color="transparent")
        name_f.place(x=56, rely=0.5, anchor="w")
        ctk.CTkLabel(name_f, text="<", font=("Segoe UI", 18, "bold"),
                     text_color=CYAN).pack(side="left")
        ctk.CTkLabel(name_f, text="PDF", font=("Segoe UI", 18, "bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkLabel(name_f, text=">", font=("Segoe UI", 18, "bold"),
                     text_color=CYAN).pack(side="left")

        # Folder path
        folder_str = str(self._folder)
        if len(folder_str) > 38:
            folder_str = "…" + folder_str[-36:]
        ctk.CTkLabel(bar, text=folder_str,
                     font=("Segoe UI", 9), text_color=SUBTEXT
                     ).place(relx=1.0, x=-46, rely=0.5, anchor="e")

        # Refresh
        ctk.CTkButton(
            bar, text="⟳", width=30, height=30, corner_radius=8,
            font=("Segoe UI", 15), fg_color="transparent",
            hover_color=DIM, text_color=SUBTEXT,
            command=self._refresh,
        ).place(relx=1.0, x=-12, rely=0.5, anchor="e")

        # ── Thin separator ──
        sep = ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0)
        sep.pack(fill="x")

        # ── Body ──
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True)

        self._left_frame = ctk.CTkFrame(
            body, corner_radius=0,
            fg_color=SPLIT_BG if self._mode == "split" else DIM2)
        self._left_frame.place(relx=0, rely=0, relwidth=0.5, relheight=1.0)

        self._right_frame = ctk.CTkFrame(
            body, corner_radius=0,
            fg_color=MERGE_BG if self._mode == "merge" else DIM2)
        self._right_frame.place(relx=0.5, rely=0, relwidth=0.5, relheight=1.0)

        # Thin centre divider line
        ctk.CTkFrame(body, fg_color=BORDER, width=1, corner_radius=0
                     ).place(relx=0.5, rely=0, relwidth=0, relheight=1.0,
                             anchor="n", x=0)

        # ── Centre toggle  < | > ──
        tog = ctk.CTkFrame(body, fg_color=BG, width=64, height=32,
                           corner_radius=16, border_width=1, border_color=BORDER)
        tog.place(relx=0.5, rely=0.5, anchor="center")
        tog.pack_propagate(False)

        tog_inner = ctk.CTkFrame(tog, fg_color="transparent")
        tog_inner.place(relx=0.5, rely=0.5, anchor="center")

        lt = ctk.CTkLabel(tog_inner, text="<",
                          font=("Segoe UI", 13, "bold"),
                          text_color=CYAN if self._mode == "split" else SUBTEXT)
        lt.pack(side="left", padx=(4, 0))

        div = ctk.CTkLabel(tog_inner, text="|",
                           font=("Segoe UI", 11),
                           text_color=BORDER)
        div.pack(side="left", padx=3)

        rt = ctk.CTkLabel(tog_inner, text=">",
                          font=("Segoe UI", 13, "bold"),
                          text_color=AMBER if self._mode == "merge" else SUBTEXT)
        rt.pack(side="left", padx=(0, 4))

        self._toggle_left = lt
        self._toggle_right = rt

        # Make whole toggle clickable
        for w in [tog, tog_inner, lt, div, rt]:
            w.bind("<Button-1>", lambda e: self._toggle_mode())
            w.bind("<Enter>",    lambda e: tog.configure(border_color=CYAN))
            w.bind("<Leave>",    lambda e: tog.configure(border_color=BORDER))
            w.configure(cursor="hand2")

        self._populate_halves()

    def _populate_halves(self):
        for w in self._left_frame.winfo_children():
            w.destroy()
        for w in self._right_frame.winfo_children():
            w.destroy()
        self._draw_split_half(self._left_frame,  active=(self._mode == "split"))
        self._draw_merge_half(self._right_frame, active=(self._mode == "merge"))

    # ── Split half ────────────────────────────────────────────────────────────

    def _draw_split_half(self, parent, active: bool):
        single = self._split_target or (self._pdfs[0] if self._pdfs else None)
        page_count = None
        if single:
            try:
                page_count = get_page_count(single)
            except Exception:
                pass

        ac  = CYAN    if active else SUBTEXT
        tc  = TEXT    if active else DIM
        sc  = CYAN    if active else DIM
        ic  = CYAN_DIM if active else DIM2

        # ── < label ──
        ctk.CTkLabel(parent, text="<",
                     font=("Segoe UI", 28, "bold"), text_color=ac,
                     ).place(relx=0.5, rely=0.09, anchor="center")

        ctk.CTkLabel(parent, text=self._tracked_text("SPLIT"),
                     font=("Segoe UI", 8, "bold"), text_color=sc,
                     ).place(relx=0.5, rely=0.17, anchor="center")

        # Icon box
        ico_f = ctk.CTkFrame(parent, fg_color=ic, width=56, height=56, corner_radius=14)
        ico_f.place(relx=0.5, rely=0.30, anchor="center")
        ctk.CTkLabel(ico_f, text="✂",
                     font=("Segoe UI Emoji", 24),
                     text_color=ac).place(relx=0.5, rely=0.5, anchor="center")

        if single:
            ctk.CTkLabel(parent, text=self._trunc(single.name, 17),
                         font=("Segoe UI", 11, "bold"), text_color=tc,
                         ).place(relx=0.5, rely=0.46, anchor="center")

            detail = f"→  {page_count} files" if page_count else "→  ? files"
            ctk.CTkLabel(parent, text=detail,
                         font=("Segoe UI", 10), text_color=sc,
                         ).place(relx=0.5, rely=0.54, anchor="center")

            tag = ("📐 Titles" if self._use_titles else "🔢 Sequential")
            if self._titles_auto:
                tag += "  (auto)"
            ctk.CTkLabel(parent, text=tag,
                         font=("Segoe UI", 9), text_color=sc,
                         ).place(relx=0.5, rely=0.61, anchor="center")
        else:
            ctk.CTkLabel(parent, text="No PDF found",
                         font=("Segoe UI", 11), text_color=tc,
                         ).place(relx=0.5, rely=0.50, anchor="center")

        if active and single:
            ctk.CTkButton(
                parent, text="GO",
                font=("Segoe UI", 16, "bold"),
                height=42, width=120, corner_radius=12,
                fg_color=CYAN, hover_color=CYAN_HOV, text_color="#001A18",
                command=self._run_split,
            ).place(relx=0.5, rely=0.75, anchor="center")

            label = "Change  /  Edit" if len(self._pdfs) > 1 else "Edit"
            ctk.CTkButton(
                parent, text=label,
                font=("Segoe UI", 10), height=24, width=110, corner_radius=6,
                fg_color="transparent", hover_color=DIM, text_color=sc,
                command=self._edit_split,
            ).place(relx=0.5, rely=0.87, anchor="center")

        elif active:
            ctk.CTkButton(
                parent, text="Browse…",
                font=("Segoe UI", 12), height=36, width=120, corner_radius=10,
                fg_color=DIM, hover_color=CARD_HOV, text_color=CYAN,
                command=self._pick_split_pdf,
            ).place(relx=0.5, rely=0.75, anchor="center")

    # ── Merge half ────────────────────────────────────────────────────────────

    def _draw_merge_half(self, parent, active: bool):
        count = len(self._merge_files)
        ac = AMBER   if active else SUBTEXT
        tc = TEXT    if active else DIM
        sc = AMBER   if active else DIM
        ic = AMBER_DIM if active else DIM2

        ctk.CTkLabel(parent, text=">",
                     font=("Segoe UI", 28, "bold"), text_color=ac,
                     ).place(relx=0.5, rely=0.09, anchor="center")

        ctk.CTkLabel(parent, text=self._tracked_text("MERGE"),
                     font=("Segoe UI", 8, "bold"), text_color=sc,
                     ).place(relx=0.5, rely=0.17, anchor="center")

        ico_f = ctk.CTkFrame(parent, fg_color=ic, width=56, height=56, corner_radius=14)
        ico_f.place(relx=0.5, rely=0.30, anchor="center")
        ctk.CTkLabel(ico_f, text="⊞",
                     font=("Segoe UI Emoji", 24),
                     text_color=ac).place(relx=0.5, rely=0.5, anchor="center")

        if count >= 2:
            ctk.CTkLabel(parent, text=f"{count} PDFs",
                         font=("Segoe UI", 11, "bold"), text_color=tc,
                         ).place(relx=0.5, rely=0.46, anchor="center")
            ctk.CTkLabel(parent, text="→  merged.pdf",
                         font=("Segoe UI", 10), text_color=sc,
                         ).place(relx=0.5, rely=0.54, anchor="center")
        elif count == 1:
            ctk.CTkLabel(parent, text="Need 2+ PDFs",
                         font=("Segoe UI", 11), text_color=tc,
                         ).place(relx=0.5, rely=0.50, anchor="center")
        else:
            ctk.CTkLabel(parent, text="No PDFs found",
                         font=("Segoe UI", 11), text_color=tc,
                         ).place(relx=0.5, rely=0.50, anchor="center")

        if active and count >= 2:
            ctk.CTkButton(
                parent, text="GO",
                font=("Segoe UI", 16, "bold"),
                height=42, width=120, corner_radius=12,
                fg_color=AMBER, hover_color=AMBER_HOV, text_color="#1A0E00",
                command=self._run_merge,
            ).place(relx=0.5, rely=0.75, anchor="center")

            ctk.CTkButton(
                parent, text="Edit",
                font=("Segoe UI", 10), height=24, width=110, corner_radius=6,
                fg_color="transparent", hover_color=DIM, text_color=sc,
                command=self._edit_merge,
            ).place(relx=0.5, rely=0.87, anchor="center")

    # ── Toggle ────────────────────────────────────────────────────────────────

    def _toggle_mode(self):
        old_mode = self._mode
        self._mode = "merge" if self._mode == "split" else "split"
        self._set_toggle_colors()
        self._animate_mode_panels(old_mode, self._mode)

    def _set_toggle_colors(self):
        if self._toggle_left is not None:
            self._toggle_left.configure(
                text_color=CYAN if self._mode == "split" else SUBTEXT
            )
        if self._toggle_right is not None:
            self._toggle_right.configure(
                text_color=AMBER if self._mode == "merge" else SUBTEXT
            )

    def _animate_mode_panels(self, from_mode: str, to_mode: str):
        if self._left_frame is None or self._right_frame is None:
            self._populate_halves()
            return

        if self._mode_anim_after is not None:
            try:
                self.after_cancel(self._mode_anim_after)
            except Exception:
                pass
            self._mode_anim_after = None

        left_from = SPLIT_BG if from_mode == "split" else DIM2
        left_to = SPLIT_BG if to_mode == "split" else DIM2
        right_from = MERGE_BG if from_mode == "merge" else DIM2
        right_to = MERGE_BG if to_mode == "merge" else DIM2
        steps = 8
        delay_ms = 16

        def step(i: int = 0):
            t = i / steps
            self._left_frame.configure(
                fg_color=self._blend_hex(left_from, left_to, t)
            )
            self._right_frame.configure(
                fg_color=self._blend_hex(right_from, right_to, t)
            )
            if i < steps:
                self._mode_anim_after = self.after(delay_ms, lambda: step(i + 1))
            else:
                self._mode_anim_after = None
                self._populate_halves()

        step()

    # ── Edit dialogs ──────────────────────────────────────────────────────────

    def _edit_split(self):
        multi = len(self._pdfs) > 1
        h = 310 if multi else 210
        d = ctk.CTkToplevel(self)
        d.title("<PDF> — Split Options")
        d.geometry(f"360x{h}")
        d.configure(fg_color=BG)
        d.grab_set()
        d.resizable(False, False)

        try:
            if LOGO_ICO.exists():
                d.iconbitmap(str(LOGO_ICO))
        except Exception:
            pass

        ctk.CTkLabel(d, text="Split Options",
                     font=("Segoe UI", 15, "bold"), text_color=TEXT).pack(pady=(18, 12))

        if multi:
            ctk.CTkLabel(d, text="Which PDF?",
                         font=("Segoe UI", 10), text_color=SUBTEXT).pack(anchor="w", padx=24)
            cur = self._split_target or self._pdfs[0]
            pdf_var = tk.StringVar(value=str(cur))
            sf = ctk.CTkScrollableFrame(d, fg_color=CARD, corner_radius=8, height=90)
            sf.pack(fill="x", padx=24, pady=(4, 14))
            for p in self._pdfs:
                ctk.CTkRadioButton(
                    sf, text=p.name[:34],
                    variable=pdf_var, value=str(p),
                    font=("Segoe UI", 11), text_color=TEXT,
                    radiobutton_width=16, radiobutton_height=16,
                    fg_color=CYAN, border_color=BORDER,
                ).pack(anchor="w", pady=2, padx=6)

        ctk.CTkLabel(d, text="File naming",
                     font=("Segoe UI", 10), text_color=SUBTEXT).pack(anchor="w", padx=24)
        name_var = tk.StringVar(value="titles" if self._use_titles else "seq")

        for val, lbl in [("seq", "🔢  Sequential  (doc_01.pdf, doc_02.pdf…)"),
                         ("titles", "📐  Drawing titles  (reads title block)")]:
            ctk.CTkRadioButton(
                d, text=lbl, variable=name_var, value=val,
                font=("Segoe UI", 11), text_color=TEXT,
                radiobutton_width=16, radiobutton_height=16,
                fg_color=CYAN, border_color=BORDER,
            ).pack(anchor="w", padx=24, pady=3)

        def apply():
            if multi:
                self._split_target = Path(pdf_var.get())
                self._use_titles   = detect_uses_titles(self._split_target)
                self._titles_auto  = True
            self._use_titles  = (name_var.get() == "titles")
            self._titles_auto = False
            d.destroy()
            self._populate_halves()

        ctk.CTkButton(
            d, text="Apply", height=38, corner_radius=10,
            fg_color=CYAN, hover_color=CYAN_HOV, text_color="#001A18",
            font=("Segoe UI", 13, "bold"),
            command=apply,
        ).pack(pady=(14, 0), padx=24, fill="x")

    def _edit_merge(self):
        if not self._pdfs:
            return
        d = ctk.CTkToplevel(self)
        d.title("<PDF> — Merge Order")
        d.geometry("400x500")
        d.configure(fg_color=BG)
        d.grab_set()
        d.resizable(False, False)

        try:
            if LOGO_ICO.exists():
                d.iconbitmap(str(LOGO_ICO))
        except Exception:
            pass

        ctk.CTkLabel(d, text="Order & Select",
                     font=("Segoe UI", 15, "bold"), text_color=TEXT).pack(pady=(18, 4))
        ctk.CTkLabel(d, text="↑ ↓ reorder   ·   uncheck to exclude",
                     font=("Segoe UI", 10), text_color=SUBTEXT).pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(d, fg_color=CARD, corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        items: list[tuple[Path, tk.BooleanVar]] = [
            (p, tk.BooleanVar(value=(p in self._merge_files)))
            for p in self._pdfs
        ]

        def render():
            for w in scroll.winfo_children():
                w.destroy()
            for idx, (p, var) in enumerate(items):
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=2, padx=4)

                ctk.CTkLabel(row, text=f"{idx+1}",
                             font=("Segoe UI", 10, "bold"), text_color=SUBTEXT,
                             width=20).pack(side="left")

                for arrow, delta, enabled in [("↑", -1, idx > 0),
                                               ("↓", +1, idx < len(items) - 1)]:
                    ctk.CTkButton(
                        row, text=arrow, width=26, height=26, corner_radius=6,
                        font=("Segoe UI", 12, "bold"),
                        fg_color=CARD_HOV, hover_color=DIM,
                        text_color=CYAN if enabled else DIM,
                        state="normal" if enabled else "disabled",
                        command=lambda i=idx, d=delta: (
                            items.__setitem__(slice(i, i+2), [items[i+d], items[i]])
                            if d == -1 else
                            items.__setitem__(slice(i, i+2), [items[i+1], items[i]])
                        ) or render(),
                    ).pack(side="left", padx=(0, 2))

                ctk.CTkCheckBox(
                    row, text=p.name[:30],
                    variable=var,
                    font=("Segoe UI", 11), text_color=TEXT,
                    checkbox_width=18, checkbox_height=18,
                    border_color=AMBER, checkmark_color=BG, fg_color=AMBER,
                ).pack(side="left", padx=(6, 0), fill="x", expand=True)

        render()

        def apply():
            self._merge_files = [p for p, v in items if v.get()]
            d.destroy()
            self._populate_halves()

        ctk.CTkButton(
            d, text="Apply", height=38, corner_radius=10,
            fg_color=AMBER, hover_color=AMBER_HOV, text_color="#1A0E00",
            font=("Segoe UI", 13, "bold"),
            command=apply,
        ).pack(pady=8, padx=16, fill="x")

    # ── Pick manually ─────────────────────────────────────────────────────────

    def _pick_split_pdf(self):
        p = filedialog.askopenfilename(
            title="Select PDF to split",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if p:
            self._pdfs         = [Path(p)]
            self._merge_files  = []
            self._split_target = None
            self._mode         = "split"
            self._use_titles   = detect_uses_titles(self._pdfs[0])
            self._titles_auto  = True
            self._build_home()

    # ── Run ───────────────────────────────────────────────────────────────────

    def _run_split(self):
        if not self._pdfs:
            return
        pdf = self._split_target or self._pdfs[0]
        out_dir = self._folder / pdf.stem
        self._build_progress("Splitting", CYAN)

        def run():
            try:
                do_split(pdf, out_dir, self._use_titles,
                         self._set_progress_threadsafe,
                         self._set_status_threadsafe)
            except Exception as e:
                self._set_status_threadsafe(f"Error: {e}")
            finally:
                self._run_on_ui(self._finish)

        threading.Thread(target=run, daemon=True).start()

    def _run_merge(self):
        if len(self._merge_files) < 2:
            return
        out_file = self._folder / "merged.pdf"
        i = 1
        while out_file.exists():
            out_file = self._folder / f"merged_{i}.pdf"
            i += 1
        self._build_progress("Merging", AMBER)

        def run():
            try:
                do_merge(self._merge_files, out_file,
                         self._set_progress_threadsafe,
                         self._set_status_threadsafe)
            except Exception as e:
                self._set_status_threadsafe(f"Error: {e}")
            finally:
                self._run_on_ui(self._finish)

        threading.Thread(target=run, daemon=True).start()

    def _run_on_ui(self, fn, *args):
        try:
            self.after(0, lambda: fn(*args))
        except tk.TclError:
            pass

    def _set_progress_threadsafe(self, v):
        self._run_on_ui(self._set_progress, v)

    def _set_status_threadsafe(self, msg):
        self._run_on_ui(self._set_status, msg)

    # ── Progress ──────────────────────────────────────────────────────────────

    def _build_progress(self, verb: str, color: str):
        self._clear()

        # Header stays
        bar = ctk.CTkFrame(self, fg_color=BG, height=54, corner_radius=0)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        try:
            if LOGO_PNG.exists():
                from PIL import Image
                img = ctk.CTkImage(
                    light_image=Image.open(str(LOGO_PNG)),
                    dark_image=Image.open(str(LOGO_PNG)),
                    size=(32, 32)
                )
                ctk.CTkLabel(bar, image=img, text="").place(x=14, rely=0.5, anchor="w")
        except Exception:
            pass
        name_f = ctk.CTkFrame(bar, fg_color="transparent")
        name_f.place(x=56, rely=0.5, anchor="w")
        ctk.CTkLabel(name_f, text="<", font=("Segoe UI", 18, "bold"),
                     text_color=CYAN).pack(side="left")
        ctk.CTkLabel(name_f, text="PDF", font=("Segoe UI", 18, "bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkLabel(name_f, text=">", font=("Segoe UI", 18, "bold"),
                     text_color=CYAN).pack(side="left")

        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        # Content
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True, padx=44)

        ctk.CTkLabel(body, text=verb + "…",
                     font=("Segoe UI", 22, "bold"), text_color=color,
                     ).pack(pady=(52, 8))

        self._status_var = tk.StringVar(value="Starting…")
        ctk.CTkLabel(body, textvariable=self._status_var,
                     font=("Segoe UI", 11), text_color=SUBTEXT,
                     wraplength=400).pack(pady=(0, 32))

        self._progress = ctk.CTkProgressBar(
            body, height=6, corner_radius=3,
            progress_color=color, fg_color=DIM2
        )
        self._progress_value = 0.0
        self._progress_target = 0.0
        self._progress.set(0)
        self._progress.pack(fill="x")

        self._pct_var = tk.StringVar(value="0%")
        ctk.CTkLabel(body, textvariable=self._pct_var,
                     font=("Segoe UI", 11), text_color=color,
                     ).pack(anchor="e", pady=(6, 0))

        self._done_btn = ctk.CTkButton(
            body, text="Back",
            font=("Segoe UI", 14), height=44, corner_radius=10,
            fg_color=DIM2, hover_color=DIM,
            text_color=SUBTEXT, command=self._refresh, state="disabled",
        )
        self._done_btn.pack(pady=40, fill="x")

    def _set_progress(self, v):
        if not hasattr(self, "_progress"):
            return
        try:
            target = max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return
        self._progress_target = target
        if self._progress_anim_after is None:
            self._animate_progress()

    def _animate_progress(self):
        delta = self._progress_target - self._progress_value
        if abs(delta) < 0.004:
            self._progress_value = self._progress_target
        else:
            self._progress_value += delta * 0.3

        try:
            self._progress.set(self._progress_value)
            self._pct_var.set(f"{int(self._progress_value * 100)}%")
            self.update_idletasks()
        except tk.TclError:
            self._progress_anim_after = None
            return

        if abs(self._progress_target - self._progress_value) <= 0.001:
            self._progress_anim_after = None
            return
        self._progress_anim_after = self.after(16, self._animate_progress)

    def _set_status(self, msg):
        try:
            self._status_var.set(msg)
            self.update_idletasks()
        except tk.TclError:
            pass

    def _finish(self):
        try:
            self._done_btn.configure(
                state="normal",
                text="← Done",
                text_color=TEXT,
                fg_color=CYAN_DIM,
                hover_color=DIM,
            )
        except tk.TclError:
            pass

    # ── utils ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _tracked_text(word: str) -> str:
        return " ".join(word)

    @staticmethod
    def _blend_hex(color_a: str, color_b: str, t: float) -> str:
        t = max(0.0, min(1.0, t))
        a = color_a.lstrip("#")
        b = color_b.lstrip("#")
        ar, ag, ab = (int(a[i:i+2], 16) for i in (0, 2, 4))
        br, bg, bb = (int(b[i:i+2], 16) for i in (0, 2, 4))
        rr = round(ar + (br - ar) * t)
        rg = round(ag + (bg - ag) * t)
        rb = round(ab + (bb - ab) * t)
        return f"#{rr:02X}{rg:02X}{rb:02X}"

    @staticmethod
    def _trunc(s: str, n: int) -> str:
        return s if len(s) <= n else s[:n - 1] + "…"


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
