"""
PDF layout factory — fpdf2 based.

Generates three layout types:
  workbook      — alternating source/blank-space line buffers for handwritten entries
  note_sheet    — note-taking margin layout with fixed structural borders
  declension    — empty tabular grids for case inflection practice

Paper size: A4 (default) or Letter, configured via config.toml.
Margins: 20 mm default (10–40 mm range).
DPI: 300 for any rasterised elements.
FreeSerif font bundled for macron/diacritic support.
Output served as in-memory bytes; no file written to disk.
"""
from __future__ import annotations

import io
from pathlib import Path

from fpdf import FPDF

FONTS_DIR = Path(__file__).parent.parent / "static" / "fonts"
FREESERIF_PATH = FONTS_DIR / "FreeSerif.ttf"
DEJAVUSANS_PATH = FONTS_DIR / "DejaVuSans.ttf"

# A4 and Letter dimensions in mm
PAPER_SIZES: dict[str, tuple[float, float]] = {
    "A4": (210.0, 297.0),
    "Letter": (215.9, 279.4),
}

# Case names for declension matrix columns
# Macron → ASCII transliteration used when no TTF font is available
_MACRON_TRANSLITERATE = str.maketrans(
    "āēīōūĀĒĪŌŪ",
    "aeiouAEIOU",
)

LATIN_CASES = ("Nominative", "Genitive", "Dative", "Accusative", "Ablative", "Vocative")
NUMBERS = ("Singular", "Plural")

# Height in mm allocated per handwriting space line
HANDWRITE_LINE_HEIGHT = 15.0
# Height in mm for a printed source line
SOURCE_LINE_HEIGHT = 8.0


class PdfFactory:
    def __init__(
        self,
        paper_size: str = "A4",
        margin_mm: int = 20,
    ) -> None:
        if paper_size not in PAPER_SIZES:
            paper_size = "A4"
        w, h = PAPER_SIZES[paper_size]
        self._w = w
        self._h = h
        self._margin = float(margin_mm)
        self._paper_size = paper_size

    def _make_pdf(self) -> FPDF:
        pdf = FPDF(orientation="P", unit="mm", format=(self._w, self._h))
        pdf.set_margins(self._margin, self._margin, self._margin)
        pdf.set_auto_page_break(auto=True, margin=self._margin)

        # Register FreeSerif if available (macron/diacritic support)
        if FREESERIF_PATH.exists():
            pdf.add_font("FreeSerif", "", str(FREESERIF_PATH))
            pdf.add_font("FreeSerif", "B", str(FREESERIF_PATH))
            self._latin_font = "FreeSerif"
        elif DEJAVUSANS_PATH.exists():
            pdf.add_font("DejaVuSans", "", str(DEJAVUSANS_PATH))
            self._latin_font = "DejaVuSans"
        else:
            self._latin_font = "Helvetica"  # fallback; macrons transliterated to ASCII

        return pdf

    def _safe_text(self, text: str) -> str:
        """When using a core font, transliterate macron chars to ASCII equivalents."""
        if self._latin_font == "Helvetica":
            return text.translate(_MACRON_TRANSLITERATE)
        return text

    def generate(self, content_type: str = "workbook", text: str = "") -> bytes:
        """
        Generate a PDF and return raw bytes.
        No file is written to disk.
        """
        if content_type == "workbook":
            return self._generate_workbook(text)
        elif content_type == "note_sheet":
            return self._generate_note_sheet(text)
        elif content_type == "declension":
            return self._generate_declension(text)
        else:
            return self._generate_workbook(text)

    def _generate_workbook(self, text: str) -> bytes:
        """Alternating line buffers: source line then blank handwriting space."""
        pdf = self._make_pdf()
        pdf.add_page()

        # Title
        pdf.set_font(self._latin_font if self._latin_font != "Helvetica" else "Helvetica", size=14)
        pdf.cell(0, 10, "Latin Translation Workbook", ln=True, align="C")
        pdf.ln(5)

        lines = [l.strip() for l in text.split("\n") if l.strip()] or ["(No source text provided)"]
        usable_w = self._w - 2 * self._margin

        pdf.set_font(self._latin_font if self._latin_font != "Helvetica" else "Helvetica", size=10)
        for i, line in enumerate(lines, 1):
            # Printed source line
            pdf.set_fill_color(240, 240, 240)
            pdf.multi_cell(usable_w, SOURCE_LINE_HEIGHT, self._safe_text(f"{i}. {line}"), fill=True, ln=True)

            # Blank handwriting space — dotted baseline
            y_start = pdf.get_y()
            x_left = self._margin
            x_right = self._w - self._margin
            pdf.set_draw_color(180, 180, 180)
            for line_offset in range(1, 3):
                y = y_start + line_offset * (HANDWRITE_LINE_HEIGHT / 2)
                pdf.dashed_line(x_left, y, x_right, y, dash_length=2, space_length=2)
            pdf.ln(HANDWRITE_LINE_HEIGHT)

        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    def _generate_note_sheet(self, text: str) -> bytes:
        """Note-taking margin layout: wide left column, narrow right note margin."""
        pdf = self._make_pdf()
        pdf.add_page()

        usable_w = self._w - 2 * self._margin
        note_col_w = usable_w * 0.25
        text_col_w = usable_w * 0.70
        gap = usable_w * 0.05

        pdf.set_font(self._latin_font if self._latin_font != "Helvetica" else "Helvetica", size=14)
        pdf.cell(0, 10, "Latin Study Note Sheet", ln=True, align="C")
        pdf.ln(3)

        # Column headers
        pdf.set_font(self._latin_font if self._latin_font != "Helvetica" else "Helvetica", size=9)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(text_col_w, 7, "Text / Translation", border=1, fill=True)
        pdf.cell(gap, 7, "", border=0)
        pdf.cell(note_col_w, 7, "Notes", border=1, fill=True, ln=True)
        pdf.ln(2)

        lines = [l.strip() for l in text.split("\n") if l.strip()] or ["(No source text provided)"]
        pdf.set_font(self._latin_font if self._latin_font != "Helvetica" else "Helvetica", size=10)

        for line in lines:
            row_h = 14.0
            pdf.multi_cell(text_col_w, row_h, line, border=1)
            # Reset X to draw note cell beside the text cell
            y_after = pdf.get_y()
            pdf.set_xy(self._margin + text_col_w + gap, y_after - row_h)
            pdf.cell(note_col_w, row_h, "", border=1, ln=True)

        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()

    def _generate_declension(self, text: str) -> bytes:
        """Empty declension matrix grid for manual case inflection practice."""
        pdf = self._make_pdf()
        pdf.add_page()

        usable_w = self._w - 2 * self._margin

        pdf.set_font(self._latin_font if self._latin_font != "Helvetica" else "Helvetica", size=14)
        pdf.cell(0, 10, "Latin Declension Practice", ln=True, align="C")
        pdf.ln(2)

        if text:
            pdf.set_font(self._latin_font if self._latin_font != "Helvetica" else "Helvetica", size=10)
            pdf.multi_cell(usable_w, 8, f"Vocabulary focus: {text}", ln=True)
            pdf.ln(3)

        # Column widths
        label_w = usable_w * 0.18
        case_w = (usable_w - label_w) / len(LATIN_CASES)
        row_h = 10.0

        pdf.set_font(self._latin_font if self._latin_font != "Helvetica" else "Helvetica", size=8)
        pdf.set_fill_color(220, 220, 220)

        # Header row
        pdf.cell(label_w, row_h, "", border=1, fill=True)
        for case in LATIN_CASES:
            pdf.cell(case_w, row_h, case, border=1, fill=True, align="C")
        pdf.ln()

        # Data rows (Singular / Plural — blank for manual entry)
        pdf.set_fill_color(255, 255, 255)
        for number in NUMBERS:
            pdf.cell(label_w, row_h, number, border=1, fill=True)
            for _ in LATIN_CASES:
                pdf.cell(case_w, row_h, "", border=1)
            pdf.ln()

        buf = io.BytesIO()
        pdf.output(buf)
        return buf.getvalue()
