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
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageTk


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


def safe_file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return -1


def pick_largest_pdf(pdfs: list[Path]) -> Path | None:
    if not pdfs:
        return None
    return max(pdfs, key=lambda p: (safe_file_size(p), p.name.lower()))


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
SPLASH_MP4 = _res("splash.mp4")
APP_WORD = "PDFrr"
APP_BRAND = f"<{APP_WORD}>"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_BRAND)
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
        self._split_target = pick_largest_pdf(self._pdfs)
        if self._split_target:
            self._use_titles  = detect_uses_titles(self._split_target)
            self._titles_auto = True

        self._merge_files  = list(self._pdfs)

        self._left_frame = None
        self._right_frame = None
        self._toggle_left = None
        self._toggle_right = None
        self._top_tab_btn = None
        self._mode_anim_after = None
        self._progress_anim_after = None
        self._progress_value = 0.0
        self._progress_target = 0.0

        self._splash_after = None
        self._splash_done_after = None
        self._splash_reader = None
        self._splash_video_label = None
        self._splash_photo = None
        self._splash_frame_size = (384, 216)
        self._splash_corner_radius = 26
        self._splash_delay_ms = 33
        self._splash_active = False

        self._build_splash()

    # ── core helpers ──────────────────────────────────────────────────────────

    def _clear(self):
        for handle_name in (
            "_mode_anim_after",
            "_progress_anim_after",
            "_splash_after",
            "_splash_done_after",
        ):
            handle = getattr(self, handle_name, None)
            if handle is not None:
                try:
                    self.after_cancel(handle)
                except Exception:
                    pass
                setattr(self, handle_name, None)
        self._close_splash_reader()
        self._splash_active = False
        self._splash_video_label = None
        self._splash_photo = None
        self._toggle_left = None
        self._toggle_right = None
        self._top_tab_btn = None
        self._left_frame = None
        self._right_frame = None
        for w in self.winfo_children():
            w.destroy()

    def _on_close(self):
        self._clear()
        try:
            self.destroy()
        except tk.TclError:
            pass

    def _current_split_pdf(self) -> Path | None:
        if self._split_target in self._pdfs:
            return self._split_target
        self._split_target = pick_largest_pdf(self._pdfs)
        return self._split_target

    def _refresh(self):
        self._pdfs         = scan_folder(self._folder)
        self._merge_files  = list(self._pdfs)
        self._split_target = pick_largest_pdf(self._pdfs)
        self._mode         = "merge" if len(self._pdfs) >= 2 else "split"
        if self._split_target:
            self._use_titles  = detect_uses_titles(self._split_target)
            self._titles_auto = True
        self._build_home()

    # ── Splash ────────────────────────────────────────────────────────────────

    def _build_splash(self):
        self._clear()
        self._splash_active = True

        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.pack(fill="both", expand=True)

        title = ctk.CTkFrame(body, fg_color="transparent")
        title.place(relx=0.5, rely=0.18, anchor="center")
        ctk.CTkLabel(title, text="<",
                     font=("Segoe UI", 40, "bold"), text_color=CYAN).pack(side="left")
        ctk.CTkLabel(title, text=APP_WORD,
                     font=("Segoe UI", 40, "bold"), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(title, text=">",
                     font=("Segoe UI", 40, "bold"), text_color=CYAN).pack(side="left")

        shell = ctk.CTkFrame(
            body,
            width=430,
            height=248,
            corner_radius=44,
            fg_color=PANEL,
            border_width=1,
            border_color=BORDER,
        )
        shell.place(relx=0.5, rely=0.5, anchor="center")
        shell.pack_propagate(False)

        inner = ctk.CTkFrame(
            shell,
            width=406,
            height=224,
            corner_radius=36,
            fg_color=CARD,
            border_width=1,
            border_color=CYAN_DIM,
        )
        inner.place(relx=0.5, rely=0.5, anchor="center")
        inner.pack_propagate(False)

        self._splash_video_label = tk.Label(
            inner,
            bg=CARD,
            bd=0,
            highlightthickness=0,
        )
        self._splash_video_label.place(relx=0.5, rely=0.5, anchor="center")

        playing = self._start_splash_video()
        if not playing:
            self._set_splash_fallback()

        ctk.CTkLabel(
            body,
            text="Loading workspace…",
            font=("Segoe UI", 12),
            text_color=SUBTEXT,
        ).place(relx=0.5, rely=0.80, anchor="center")

        self._splash_done_after = self.after(2400, self._end_splash)

    def _end_splash(self):
        self._splash_done_after = None
        self._build_home()

    def _start_splash_video(self) -> bool:
        if self._splash_video_label is None or not SPLASH_MP4.exists():
            return False

        try:
            import imageio.v2 as imageio
            self._splash_reader = imageio.get_reader(str(SPLASH_MP4), format="ffmpeg")
            meta = self._splash_reader.get_meta_data()
            fps = float(meta.get("fps", 30) or 30)
            self._splash_delay_ms = max(20, min(60, int(round(1000 / fps))))
        except Exception:
            self._close_splash_reader()
            return False

        self._draw_splash_frame()
        return True

    def _draw_splash_frame(self):
        if not self._splash_active or self._splash_video_label is None:
            return

        frame = None
        if self._splash_reader is not None:
            try:
                frame = self._splash_reader.get_next_data()
            except Exception:
                self._restart_splash_video()
                if self._splash_reader is not None:
                    try:
                        frame = self._splash_reader.get_next_data()
                    except Exception:
                        frame = None

        if frame is None:
            self._splash_after = self.after(60, self._draw_splash_frame)
            return

        try:
            image = self._rounded_frame_from_array(frame)
            self._splash_photo = ImageTk.PhotoImage(image)
            self._splash_video_label.configure(image=self._splash_photo, text="")
            self._splash_video_label.image = self._splash_photo
        except tk.TclError:
            self._splash_after = None
            return

        self._splash_after = self.after(self._splash_delay_ms, self._draw_splash_frame)

    def _restart_splash_video(self):
        self._close_splash_reader()
        try:
            import imageio.v2 as imageio
            self._splash_reader = imageio.get_reader(str(SPLASH_MP4), format="ffmpeg")
        except Exception:
            self._splash_reader = None

    def _close_splash_reader(self):
        if self._splash_reader is None:
            return
        try:
            self._splash_reader.close()
        except Exception:
            pass
        self._splash_reader = None

    def _set_splash_fallback(self):
        if self._splash_video_label is None:
            return

        try:
            base = Image.open(str(LOGO_PNG)).convert("RGB") if LOGO_PNG.exists() else None
            if base is None:
                return
            fitted = ImageOps.fit(
                base,
                self._splash_frame_size,
                method=Image.Resampling.LANCZOS
            ).filter(ImageFilter.GaussianBlur(0.5))
            image = self._round_image(fitted, self._splash_corner_radius)
            self._splash_photo = ImageTk.PhotoImage(image)
            self._splash_video_label.configure(image=self._splash_photo, text="")
            self._splash_video_label.image = self._splash_photo
        except Exception:
            self._splash_video_label.configure(
                text=APP_BRAND,
                fg=CYAN,
                bg=CARD,
                font=("Segoe UI", 26, "bold"),
            )

    def _rounded_frame_from_array(self, frame):
        image = Image.fromarray(frame).convert("RGB")
        fitted = ImageOps.fit(
            image,
            self._splash_frame_size,
            method=Image.Resampling.LANCZOS
        )
        smoothed = fitted.filter(ImageFilter.GaussianBlur(0.35))
        return self._round_image(smoothed, self._splash_corner_radius)

    # ── HOME ──────────────────────────────────────────────────────────────────

    def _build_home(self):
        self._clear()

        # ── Header bar ──
        bar = ctk.CTkFrame(self, fg_color=self._blend_hex(BG, CARD, 0.18), height=58, corner_radius=0)
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

        # App name  <PDFrr>  with styled brackets
        name_f = ctk.CTkFrame(bar, fg_color="transparent")
        name_f.place(x=56, rely=0.5, anchor="w")
        ctk.CTkLabel(name_f, text="<", font=("Segoe UI", 18, "bold"),
                     text_color=CYAN).pack(side="left")
        ctk.CTkLabel(name_f, text=APP_WORD, font=("Segoe UI", 18, "bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkLabel(name_f, text=">", font=("Segoe UI", 18, "bold"),
                     text_color=CYAN).pack(side="left")

        # Workspace chip (less URL/browser-like than full path text)
        folder_name = self._folder.name or str(self._folder)
        chip = ctk.CTkFrame(
            bar,
            fg_color=self._blend_hex(CARD, BG, 0.22),
            height=28,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        chip.place(relx=1.0, x=-48, rely=0.5, anchor="e")
        ctk.CTkLabel(
            chip,
            text=f"{self._trunc(folder_name, 16)}  ·  {len(self._pdfs)} PDF{'s' if len(self._pdfs) != 1 else ''}",
            font=("Segoe UI", 9),
            text_color=SUBTEXT,
        ).pack(padx=10, pady=3)

        # Mode-aware top tab for selection/options
        self._top_tab_btn = ctk.CTkButton(
            bar,
            text="",
            width=128,
            height=30,
            corner_radius=14,
            fg_color=self._blend_hex(BG, CARD, 0.12),
            hover_color=self._blend_hex(BG, CARD, 0.28),
            text_color=CYAN,
            border_width=1,
            border_color=self._blend_hex(CYAN, BORDER, 0.65),
            font=("Segoe UI", 10, "bold"),
            command=self._edit_split,
        )
        self._top_tab_btn.place(relx=0.55, rely=0.5, anchor="center")
        self._attach_hover_effect(
            self._top_tab_btn,
            base_width=128,
            base_height=30,
            base_rely=0.5,
            hover_width=136,
            hover_height=33,
            hover_rely=0.494,
            border_base=self._blend_hex(CYAN, BORDER, 0.65),
            border_hover=CYAN,
        )
        self._update_top_tab()

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
            body, corner_radius=28,
            fg_color=SPLIT_BG if self._mode == "split" else DIM2,
            border_width=1,
            border_color=self._blend_hex(CYAN if self._mode == "split" else BORDER, BORDER, 0.55),
        )
        self._left_frame.place(relx=0.02, rely=0.5, relwidth=0.46, relheight=0.96, anchor="w")

        self._right_frame = ctk.CTkFrame(
            body, corner_radius=28,
            fg_color=MERGE_BG if self._mode == "merge" else DIM2,
            border_width=1,
            border_color=self._blend_hex(AMBER if self._mode == "merge" else BORDER, BORDER, 0.55),
        )
        self._right_frame.place(relx=0.52, rely=0.5, relwidth=0.46, relheight=0.96, anchor="w")

        # Soft centre seam glow
        ctk.CTkFrame(
            body,
            fg_color=self._blend_hex(BORDER, BG, 0.25),
            width=14,
            corner_radius=7,
        ).place(relx=0.5, rely=0.5, relheight=0.72, anchor="center")

        # ── Centre toggle  < | > ──
        tog_outer = ctk.CTkFrame(
            body,
            fg_color=self._blend_hex(CARD, BG, 0.34),
            width=84,
            height=42,
            corner_radius=21,
            border_width=1,
            border_color=self._blend_hex(BORDER, BG, 0.2),
        )
        tog_outer.place(relx=0.5, rely=0.5, anchor="center")
        tog_outer.pack_propagate(False)

        tog = ctk.CTkFrame(
            tog_outer,
            fg_color=self._blend_hex(BG, CARD, 0.15),
            width=74,
            height=34,
            corner_radius=17,
            border_width=1,
            border_color=self._blend_hex(CYAN if self._mode == "split" else AMBER, BORDER, 0.75),
        )
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

        self._attach_hover_effect(
            tog,
            base_width=74,
            base_height=34,
            base_rely=0.5,
            hover_width=80,
            hover_height=38,
            hover_rely=0.494,
            border_base=self._blend_hex(CYAN if self._mode == "split" else AMBER, BORDER, 0.75),
            border_hover=CYAN if self._mode == "split" else AMBER,
            bind_events=False,
        )

        # Make whole toggle clickable
        for w in [tog_outer, tog, tog_inner, lt, div, rt]:
            w.bind("<Button-1>", lambda e: self._toggle_mode())
            w.bind("<Enter>",    lambda e: self._set_hover_target(tog, 1.0))
            w.bind("<Leave>",    lambda e: self._set_hover_target(tog, 0.0))
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
        single = self._current_split_pdf()
        page_count = None
        if single:
            try:
                page_count = get_page_count(single)
            except Exception:
                pass

        panel = ctk.CTkFrame(
            parent,
            fg_color=self._blend_hex(SPLIT_BG if active else DIM2, CARD, 0.35),
            corner_radius=24,
            border_width=1,
            border_color=self._blend_hex(CYAN if active else BORDER, BORDER, 0.45),
        )
        panel.place(relx=0.5, rely=0.5, relwidth=0.88, relheight=0.92, anchor="center")

        ac = CYAN if active else "#55707D"
        tc = TEXT if active else "#5E7280"
        sc = CYAN if active else "#4A5D68"
        ic = self._blend_hex(CYAN_DIM, BG, 0.12) if active else self._blend_hex(DIM2, BG, 0.28)

        # ── < label ──
        ctk.CTkLabel(panel, text="<",
                     font=("Segoe UI", 34, "bold"), text_color=ac,
                     ).place(relx=0.5, rely=0.09, anchor="center")

        ctk.CTkLabel(panel, text=self._tracked_text("SPLIT"),
                     font=("Segoe UI", 10, "bold"), text_color=sc,
                     ).place(relx=0.5, rely=0.17, anchor="center")

        if active:
            ctk.CTkFrame(
                panel,
                fg_color=self._blend_hex(CYAN_DIM, CYAN, 0.18),
                width=102,
                height=102,
                corner_radius=30,
            ).place(relx=0.5, rely=0.30, anchor="center")

        # Icon box
        ico_f = ctk.CTkFrame(
            panel,
            fg_color=ic,
            width=64,
            height=64,
            corner_radius=16,
            border_width=1,
            border_color=self._blend_hex(CYAN, BORDER, 0.55) if active else BORDER,
        )
        ico_f.place(relx=0.5, rely=0.30, anchor="center")
        ctk.CTkLabel(ico_f, text="✂",
                     font=("Segoe UI Emoji", 26),
                     text_color=ac).place(relx=0.5, rely=0.5, anchor="center")

        if single:
            ctk.CTkLabel(panel, text=self._trunc(single.name, 22),
                         font=("Segoe UI", 12, "bold"), text_color=tc,
                         ).place(relx=0.5, rely=0.46, anchor="center")

            detail = f"→  {page_count} files" if page_count else "→  ? files"
            ctk.CTkLabel(panel, text=detail,
                         font=("Segoe UI", 10), text_color=sc,
                         ).place(relx=0.5, rely=0.54, anchor="center")

            tag = ("Drawing Titles" if self._use_titles else "Sequential")
            if self._titles_auto:
                tag += "  (auto)"
            ctk.CTkLabel(panel, text=tag,
                         font=("Segoe UI", 9), text_color=sc,
                         ).place(relx=0.5, rely=0.61, anchor="center")

            if len(self._pdfs) > 1 and single == pick_largest_pdf(self._pdfs):
                ctk.CTkLabel(
                    panel,
                    text="Default: largest PDF by size",
                    font=("Segoe UI", 9),
                    text_color=self._blend_hex(CYAN, SUBTEXT, 0.35),
                ).place(relx=0.5, rely=0.66, anchor="center")
        else:
            ctk.CTkLabel(panel, text="No PDF found",
                         font=("Segoe UI", 11), text_color=tc,
                         ).place(relx=0.5, rely=0.50, anchor="center")

        if active and single:
            go_btn = ctk.CTkButton(
                panel, text="GO",
                font=("Segoe UI", 16, "bold"),
                height=44, width=132, corner_radius=14,
                fg_color=CYAN, hover_color=CYAN_HOV, text_color="#001A18",
                border_width=1, border_color=self._blend_hex(CYAN, BORDER, 0.6),
                command=self._run_split,
            )
            go_btn.place(relx=0.5, rely=0.75, anchor="center")
            self._attach_hover_effect(
                go_btn,
                base_width=132,
                base_height=44,
                base_rely=0.75,
                hover_width=154,
                hover_height=54,
                hover_rely=0.736,
                border_base=self._blend_hex(CYAN, BORDER, 0.6),
                border_hover=CYAN,
            )

            ctk.CTkLabel(
                panel,
                text="Use top tab to select pages/options",
                font=("Segoe UI", 9, "bold"),
                text_color=self._blend_hex(CYAN, SUBTEXT, 0.38),
            ).place(relx=0.5, rely=0.88, anchor="center")

        elif active:
            browse_btn = ctk.CTkButton(
                panel, text="Browse…",
                font=("Segoe UI", 12), height=36, width=120, corner_radius=10,
                fg_color=DIM, hover_color=CARD_HOV, text_color=CYAN,
                command=self._pick_split_pdf,
            )
            browse_btn.place(relx=0.5, rely=0.75, anchor="center")
            self._attach_hover_effect(
                browse_btn,
                base_width=120,
                base_height=36,
                base_rely=0.75,
                hover_width=126,
                hover_height=39,
                hover_rely=0.744,
            )

    # ── Merge half ────────────────────────────────────────────────────────────

    def _draw_merge_half(self, parent, active: bool):
        count = len(self._merge_files)
        panel = ctk.CTkFrame(
            parent,
            fg_color=self._blend_hex(MERGE_BG if active else DIM2, CARD, 0.35),
            corner_radius=24,
            border_width=1,
            border_color=self._blend_hex(AMBER if active else BORDER, BORDER, 0.45),
        )
        panel.place(relx=0.5, rely=0.5, relwidth=0.88, relheight=0.92, anchor="center")

        ac = AMBER if active else "#6B6A62"
        tc = TEXT if active else "#726A60"
        sc = AMBER if active else "#5E584E"
        ic = self._blend_hex(AMBER_DIM, BG, 0.12) if active else self._blend_hex(DIM2, BG, 0.28)

        ctk.CTkLabel(panel, text=">",
                     font=("Segoe UI", 34, "bold"), text_color=ac,
                     ).place(relx=0.5, rely=0.09, anchor="center")

        ctk.CTkLabel(panel, text=self._tracked_text("MERGE"),
                     font=("Segoe UI", 10, "bold"), text_color=sc,
                     ).place(relx=0.5, rely=0.17, anchor="center")

        if active:
            ctk.CTkFrame(
                panel,
                fg_color=self._blend_hex(AMBER_DIM, AMBER, 0.18),
                width=102,
                height=102,
                corner_radius=30,
            ).place(relx=0.5, rely=0.30, anchor="center")

        ico_f = ctk.CTkFrame(
            panel,
            fg_color=ic,
            width=64,
            height=64,
            corner_radius=16,
            border_width=1,
            border_color=self._blend_hex(AMBER, BORDER, 0.55) if active else BORDER,
        )
        ico_f.place(relx=0.5, rely=0.30, anchor="center")
        ctk.CTkLabel(ico_f, text="⊞",
                     font=("Segoe UI Emoji", 26),
                     text_color=ac).place(relx=0.5, rely=0.5, anchor="center")

        if count >= 2:
            ctk.CTkLabel(panel, text=f"{count} PDFs",
                         font=("Segoe UI", 12, "bold"), text_color=tc,
                         ).place(relx=0.5, rely=0.46, anchor="center")
            ctk.CTkLabel(panel, text="→  merged.pdf",
                         font=("Segoe UI", 10), text_color=sc,
                         ).place(relx=0.5, rely=0.54, anchor="center")
        elif count == 1:
            ctk.CTkLabel(panel, text="Need 2+ PDFs",
                         font=("Segoe UI", 11), text_color=tc,
                         ).place(relx=0.5, rely=0.50, anchor="center")
        else:
            ctk.CTkLabel(panel, text="No PDFs found",
                         font=("Segoe UI", 11), text_color=tc,
                         ).place(relx=0.5, rely=0.50, anchor="center")

        if active and count >= 2:
            go_btn = ctk.CTkButton(
                panel, text="GO",
                font=("Segoe UI", 16, "bold"),
                height=44, width=132, corner_radius=14,
                fg_color=AMBER, hover_color=AMBER_HOV, text_color="#1A0E00",
                border_width=1, border_color=self._blend_hex(AMBER, BORDER, 0.6),
                command=self._run_merge,
            )
            go_btn.place(relx=0.5, rely=0.75, anchor="center")
            self._attach_hover_effect(
                go_btn,
                base_width=132,
                base_height=44,
                base_rely=0.75,
                hover_width=154,
                hover_height=54,
                hover_rely=0.736,
                border_base=self._blend_hex(AMBER, BORDER, 0.6),
                border_hover=AMBER,
            )

            ctk.CTkLabel(
                panel,
                text="Use top tab to select file order",
                font=("Segoe UI", 9, "bold"),
                text_color=self._blend_hex(AMBER, SUBTEXT, 0.38),
            ).place(relx=0.5, rely=0.88, anchor="center")

    # ── Toggle ────────────────────────────────────────────────────────────────

    def _toggle_mode(self):
        old_mode = self._mode
        self._mode = "merge" if self._mode == "split" else "split"
        self._set_toggle_colors()
        self._update_top_tab()
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

    def _update_top_tab(self):
        if self._top_tab_btn is None:
            return
        if self._mode == "split":
            accent = CYAN
            self._top_tab_btn.configure(
                text="Select Pages",
                text_color=accent,
                command=self._edit_split,
                border_color=self._blend_hex(accent, BORDER, 0.65),
            )
        else:
            accent = AMBER
            self._top_tab_btn.configure(
                text="Select Files",
                text_color=accent,
                command=self._edit_merge,
                border_color=self._blend_hex(accent, BORDER, 0.65),
            )
        hover_fx = getattr(self._top_tab_btn, "_hover_fx", None)
        if hover_fx:
            hover_fx["border_base"] = self._blend_hex(accent, BORDER, 0.65)
            hover_fx["border_hover"] = accent

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
        left_border_from = self._blend_hex(CYAN if from_mode == "split" else BORDER, BORDER, 0.55)
        left_border_to = self._blend_hex(CYAN if to_mode == "split" else BORDER, BORDER, 0.55)
        right_border_from = self._blend_hex(AMBER if from_mode == "merge" else BORDER, BORDER, 0.55)
        right_border_to = self._blend_hex(AMBER if to_mode == "merge" else BORDER, BORDER, 0.55)
        steps = 8
        delay_ms = 16

        def step(i: int = 0):
            t = i / steps
            self._left_frame.configure(
                fg_color=self._blend_hex(left_from, left_to, t),
                border_color=self._blend_hex(left_border_from, left_border_to, t),
            )
            self._right_frame.configure(
                fg_color=self._blend_hex(right_from, right_to, t),
                border_color=self._blend_hex(right_border_from, right_border_to, t),
            )
            if i < steps:
                self._mode_anim_after = self.after(delay_ms, lambda: step(i + 1))
            else:
                self._mode_anim_after = None
                self._populate_halves()

        step()

    def _attach_hover_effect(
        self,
        widget,
        *,
        base_width: int,
        base_height: int,
        base_rely: float,
        hover_width: int,
        hover_height: int,
        hover_rely: float,
        border_base: str | None = None,
        border_hover: str | None = None,
        bind_events: bool = True,
    ):
        widget._hover_fx = {
            "value": 0.0,
            "target": 0.0,
            "after": None,
            "base_width": base_width,
            "base_height": base_height,
            "base_rely": base_rely,
            "hover_width": hover_width,
            "hover_height": hover_height,
            "hover_rely": hover_rely,
            "border_base": border_base,
            "border_hover": border_hover,
        }
        if border_base and border_hover:
            try:
                widget.configure(border_color=border_base)
            except tk.TclError:
                return
        if bind_events:
            widget.bind("<Enter>", lambda e, w=widget: self._set_hover_target(w, 1.0), add="+")
            widget.bind("<Leave>", lambda e, w=widget: self._set_hover_target(w, 0.0), add="+")

    def _set_hover_target(self, widget, target: float):
        hover_fx = getattr(widget, "_hover_fx", None)
        if hover_fx is None:
            return
        hover_fx["target"] = max(0.0, min(1.0, target))
        if hover_fx["after"] is None:
            self._step_hover_effect(widget)

    def _step_hover_effect(self, widget):
        hover_fx = getattr(widget, "_hover_fx", None)
        if hover_fx is None:
            return

        value = hover_fx["value"]
        target = hover_fx["target"]
        value += (target - value) * 0.35
        if abs(target - value) < 0.01:
            value = target
        hover_fx["value"] = value

        width = round(hover_fx["base_width"] + (hover_fx["hover_width"] - hover_fx["base_width"]) * value)
        height = round(hover_fx["base_height"] + (hover_fx["hover_height"] - hover_fx["base_height"]) * value)
        rely = hover_fx["base_rely"] + (hover_fx["hover_rely"] - hover_fx["base_rely"]) * value

        try:
            widget.configure(width=width, height=height)
            widget.place_configure(rely=rely)
            if hover_fx["border_base"] and hover_fx["border_hover"]:
                widget.configure(
                    border_color=self._blend_hex(
                        hover_fx["border_base"],
                        hover_fx["border_hover"],
                        value,
                    )
                )
        except tk.TclError:
            hover_fx["after"] = None
            return

        if value == target:
            hover_fx["after"] = None
            return
        hover_fx["after"] = self.after(16, lambda: self._step_hover_effect(widget))

    # ── Edit dialogs ──────────────────────────────────────────────────────────

    def _edit_split(self):
        multi = len(self._pdfs) > 1
        w = 420
        h = 560 if multi else 410
        d = ctk.CTkToplevel(self)
        d.title(f"{APP_BRAND} — Split Options")
        d.geometry(f"{w}x{h}")
        d.configure(fg_color=BG)
        d.transient(self)
        d.grab_set()
        d.resizable(False, False)

        try:
            if LOGO_ICO.exists():
                d.iconbitmap(str(LOGO_ICO))
        except Exception:
            pass

        self.update_idletasks()
        x = self.winfo_x() + max(12, (self.winfo_width() - w) // 2)
        y = self.winfo_y() + max(28, (self.winfo_height() - h) // 2)
        d.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkLabel(d, text="Split Options",
                     font=("Segoe UI", 16, "bold"), text_color=TEXT).pack(pady=(16, 8))

        content = ctk.CTkScrollableFrame(
            d,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=CARD_HOV,
            scrollbar_button_hover_color=DIM,
        )
        content.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        if multi:
            ctk.CTkLabel(content, text="Which PDF to split?",
                         font=("Segoe UI", 10), text_color=SUBTEXT).pack(anchor="w", padx=24)
            cur = self._current_split_pdf() or self._pdfs[0]
            pdf_var = tk.StringVar(value=str(cur))
            sf = ctk.CTkScrollableFrame(content, fg_color=CARD, corner_radius=10, height=210)
            sf.pack(fill="x", padx=24, pady=(4, 14))
            ordered = sorted(self._pdfs, key=lambda p: (-safe_file_size(p), p.name.lower()))
            for p in ordered:
                label = f"{self._trunc(p.name, 26)}  ·  {self._fmt_size(safe_file_size(p))}"
                ctk.CTkRadioButton(
                    sf, text=label,
                    variable=pdf_var, value=str(p),
                    font=("Segoe UI", 11), text_color=TEXT,
                    radiobutton_width=16, radiobutton_height=16,
                    fg_color=CYAN, border_color=BORDER,
                ).pack(anchor="w", pady=2, padx=6)
            ctk.CTkLabel(content, text="Auto default uses the largest PDF in this folder.",
                         font=("Segoe UI", 9), text_color=SUBTEXT).pack(anchor="w", padx=24, pady=(0, 14))

        ctk.CTkLabel(content, text="File naming",
                     font=("Segoe UI", 10), text_color=SUBTEXT).pack(anchor="w", padx=24)
        name_var = tk.StringVar(value="titles" if self._use_titles else "seq")

        for val, lbl in [("seq", "Sequential (doc_01.pdf, doc_02.pdf…)"),
                         ("titles", "Drawing titles (from title block)")]:
            ctk.CTkRadioButton(
                content, text=lbl, variable=name_var, value=val,
                font=("Segoe UI", 11), text_color=TEXT,
                radiobutton_width=16, radiobutton_height=16,
                fg_color=CYAN, border_color=BORDER,
            ).pack(anchor="w", padx=24, pady=3)

        def apply():
            if multi:
                self._split_target = Path(pdf_var.get())
            else:
                self._split_target = self._current_split_pdf()
            self._use_titles  = (name_var.get() == "titles")
            self._titles_auto = False
            d.destroy()
            self._populate_halves()

        actions = ctk.CTkFrame(d, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(
            actions, text="Cancel", height=38, width=120, corner_radius=10,
            fg_color=DIM2, hover_color=DIM, text_color=TEXT,
            font=("Segoe UI", 12, "bold"),
            command=d.destroy,
        ).pack(side="left")
        ctk.CTkButton(
            actions, text="Apply", height=38, corner_radius=10,
            fg_color=CYAN, hover_color=CYAN_HOV, text_color="#001A18",
            font=("Segoe UI", 13, "bold"),
            command=apply,
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _edit_merge(self):
        if not self._pdfs:
            return
        d = ctk.CTkToplevel(self)
        d.title(f"{APP_BRAND} — Merge Order")
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
            self._split_target = Path(p)
            self._mode         = "split"
            self._use_titles   = detect_uses_titles(self._pdfs[0])
            self._titles_auto  = True
            self._build_home()

    # ── Run ───────────────────────────────────────────────────────────────────

    def _run_split(self):
        if not self._pdfs:
            return
        pdf = self._current_split_pdf()
        if pdf is None:
            return
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
        ctk.CTkLabel(name_f, text=APP_WORD, font=("Segoe UI", 18, "bold"),
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
    def _round_image(image: Image.Image, radius: int) -> Image.Image:
        rgba = image.convert("RGBA")
        w, h = rgba.size
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
        rgba.putalpha(mask)
        return rgba

    @staticmethod
    def _fmt_size(size_bytes: int) -> str:
        if size_bytes < 0:
            return "?"
        units = ["B", "KB", "MB", "GB"]
        value = float(size_bytes)
        idx = 0
        while value >= 1024 and idx < len(units) - 1:
            value /= 1024
            idx += 1
        return f"{value:.1f} {units[idx]}" if idx > 0 else f"{int(value)} B"

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
