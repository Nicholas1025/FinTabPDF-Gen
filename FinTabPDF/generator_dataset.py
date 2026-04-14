import sys
from pathlib import Path

from nanoid import non_secure_generate as nanoid
import numpy as np
from selenium import webdriver
from tqdm import trange

from FinTabPDF.config import DatasetConfig
from FinTabPDF.generator_annotation import AnnotationGenerator
from FinTabPDF.generator_document import DocumentGenerator
from FinTabPDF.generator_pdf import PDFGenerator
from FinTabPDF.generator_table import TableGenerator
from FinTabPDF.generator_theme import ThemeGenerator


class DatasetGenerator():
    """
    Orchestrates synthetic PDF financial-table dataset generation.

    Pipeline per sample:
      1. TableGenerator   → randomised table data structure
      2. ThemeGenerator   → CSS theme dict
      3. DocumentGenerator → HTML file (with @media print CSS)
      4. PDFGenerator     → PDF file via Chrome CDP Page.printToPDF
      5. AnnotationGenerator → reads DOM bboxes, stores dual coords
    """

    if sys.platform == "win32":
        _no_pad_char = "#"
    else:
        _no_pad_char = "-"

    _eoy_formats       = ("%Y", f"%{_no_pad_char}d.%{_no_pad_char}m.%y")
    _note_column_names = ("Note", "Notes")
    _empty_values      = ("", "-")
    _font_sizes        = ("x-small", "small", "smaller", "medium", "large", "larger")
    _border_styles     = ("solid", "double")
    _typefaces         = (
        "Lato", "DejaVu Serif", "Latin Modern Roman",
        "TeX Gyre Bonum", "Nimbus Sans", "Utopia",
    )
    _doc_id_len        = 11
    _doc_id_alphabet   = ("0123456789abcdefghijklmnopqrstuvwxyz"
                          "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    _theme_indices      = range(6)
    _theme_probs        = (0.4, 0.12, 0.12, 0.12, 0.12, 0.12)

    def __init__(self, config: DatasetConfig = None) -> None:
        self._config = config or DatasetConfig()

        base       = Path(self._config.output_dir).resolve() / self._config.dataset_name
        self._html_dir  = base / "html"
        self._pdf_dir   = base / "pdf"
        self._ann_path  = base / "annotations.json"

        self._driver = self._build_driver()

        self._table_gen  = TableGenerator()
        self._theme_gen  = ThemeGenerator()
        self._doc_gen    = DocumentGenerator(str(self._html_dir))
        self._pdf_gen    = PDFGenerator(str(self._pdf_dir), self._driver)
        self._ann_gen    = AnnotationGenerator(str(self._ann_path), self._driver)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(self, count: int) -> None:
        """Generate `count` synthetic PDF tables with annotations."""
        self._mkdir()
        print(f"Generating {count} samples → {self._pdf_dir}")

        for _ in trange(count):
            doc_id  = nanoid(self._doc_id_alphabet, self._doc_id_len)
            params  = self._random_params()
            table   = self._table_gen(params)
            t_idx   = int(np.random.choice(self._theme_indices,
                                           p=self._theme_probs))
            theme   = self._theme_gen(t_idx, params)

            # 1. Render HTML (also navigates Chrome to the file)
            html_path = self._doc_gen(doc_id, table, theme)

            # 2. Print HTML → PDF via Chrome CDP
            self._pdf_gen(doc_id, html_path)

            # 3. Annotate — Chrome is still on the HTML page, so DOM is live
            self._ann_gen(doc_id, t_idx, table, params)

        self._ann_gen.write_to_file()
        print(f"\nDone. Annotations → {self._ann_path}")

    def close(self) -> None:
        """Quit the Chrome driver."""
        try:
            self._driver.quit()
        except Exception:
            pass

    # Allow use as context manager
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _mkdir(self) -> None:
        self._html_dir.mkdir(parents=True, exist_ok=True)
        self._pdf_dir.mkdir(parents=True, exist_ok=True)

    def _build_driver(self) -> webdriver.Chrome:
        opts = webdriver.ChromeOptions()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        # A4 at 96 DPI: 794 × 1123 px — matches coordinate conversion in generator_annotation.py
        opts.add_argument(
            f"--window-size={self._config.window_width},{self._config.window_height}")
        return webdriver.Chrome(options=opts)

    def _random_params(self) -> dict:
        return {
            'num_sections':          np.random.randint(2, 5),
            'numbered_sections':     np.random.rand() > .5,
            'uppercase_sections':    np.random.rand() > .7,
            'note_column':           np.random.rand() > .7,
            'note_column_name':      np.random.choice(self._note_column_names),
            'double_column':         np.random.rand() > .8,
            'max_value':             int(np.random.choice((1e3, 1e4, 1e5, 1e6, 1e7))),
            'thousand_factor':       np.random.rand() > .5,
            'eoy_format':            np.random.choice(self._eoy_formats),
            'no_value':              np.random.choice(self._empty_values, p=(0.8, 0.2)),
            'bracket_negatives':     np.random.rand() > .5,
            'typeface':              np.random.choice(self._typefaces),
            'font_size':             np.random.choice(self._font_sizes),
            'line_height':           np.random.choice((1, 1.25, 1.5), p=(0.7, 0.2, 0.1)),
            'border':                np.random.rand() > .9,
            'total_row':             np.random.rand() > .7,
            'total_border_style':    np.random.choice(self._border_styles, p=(0.8, 0.2)),
            'total_border_width':    np.random.randint(1, 4),
            'double_header_centered': np.random.rand() > .4,
            'current_year_bold':     np.random.rand() > .8,
            'note_column_bold':      np.random.rand() > .5,
            'note_column_min_width': np.random.randint(35, 80),
            'column_min_width':      np.random.randint(55, 250),
            'row_header_max_width':  np.random.randint(300, 372),
        }
