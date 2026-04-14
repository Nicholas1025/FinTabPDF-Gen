import json
from typing import List, Tuple

import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By


# ---------------------------------------------------------------------------
# A4 page dimensions used for coordinate conversion
# Chrome window is sized to A4 at 96 DPI: 794 × 1123 px
# PDF page is A4 at 72 pt/inch:           595.28 × 841.89 pt
# ---------------------------------------------------------------------------
_PAGE_W_PX: int   = 794
_PAGE_H_PX: int   = 1123
_SCALE: float     = 72.0 / 96          # 0.75  (pixels → PDF points)
_PAGE_W_PTS: float = round(_PAGE_W_PX * _SCALE, 3)   # 595.5
_PAGE_H_PTS: float = round(_PAGE_H_PX * _SCALE, 3)   # 842.25


def _px_to_pdf(x0: float, y0: float, x1: float, y1: float) -> List[float]:
    """
    Convert a screen-pixel bbox (top-left origin, y-down) to PDF points
    (bottom-left origin, y-up).

    Args:
        x0, y0 : top-left corner in screen pixels
        x1, y1 : bottom-right corner in screen pixels

    Returns:
        [pdf_x0, pdf_y0, pdf_x1, pdf_y1] in PDF points
        where y=0 is the BOTTOM of the page.
    """
    return [
        round(x0 * _SCALE, 3),
        round((_PAGE_H_PX - y1) * _SCALE, 3),   # y1 is screen-bottom → pdf-bottom
        round(x1 * _SCALE, 3),
        round((_PAGE_H_PX - y0) * _SCALE, 3),   # y0 is screen-top   → pdf-top
    ]


class AnnotationGenerator():
    """
    Reads DOM bounding boxes via Selenium and builds per-table annotations.

    Each annotation contains:
      bbox     : pixel coords   [x0, y0, x1, y1]  (top-left origin)
      bbox_pdf : PDF pt coords  [x0, y0, x1, y1]  (bottom-left origin)

    Call write_to_file() once at the end to persist annotations.json.
    """

    _empty_values = ("", "-")

    def __init__(self,
                 annotations_file_path: str,
                 driver: webdriver.Chrome) -> None:
        self._annotations_file_path = annotations_file_path
        self._driver  = driver
        self._tables  = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def __call__(self,
                 doc_id: str,
                 theme_idx: int,
                 table: List[List[dict]],
                 params: dict) -> None:
        table_dict = self._create_table_dict(doc_id, theme_idx, table, params)
        self._tables.append(table_dict)

    def write_to_file(self) -> None:
        with open(self._annotations_file_path, "w", encoding="utf-8") as f:
            json.dump(self._tables, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _create_table_dict(self, doc_id, theme_idx, table, params):
        rows = []

        for i, row in enumerate(table):
            cells = []

            for j, cell in enumerate(row):
                words = []
                for k, word in enumerate(cell['content'].split()):
                    px, pdf = self._get_dual_bbox(f"t0:r{i}:c{j}:w{k}")
                    words.append({'bbox': px, 'bbox_pdf': pdf, 'text': word})

                px, pdf = self._get_dual_bbox(f"t0:r{i}:c{j}")
                cells.append({
                    'bbox':     px,
                    'bbox_pdf': pdf,
                    'text':     cell['content'],
                    'words':    words,
                })

            px, pdf = self._get_dual_bbox(f"t0:r{i}")
            rows.append({'bbox': px, 'bbox_pdf': pdf, 'cells': cells})

        question, answer, ans_row_key, ans_col_key = self._create_q_and_a(
            table, params)

        px_tbl, pdf_tbl = self._get_dual_bbox("t0")
        return {
            'id':               doc_id,
            'theme':            theme_idx,
            'page_width_pts':   _PAGE_W_PTS,
            'page_height_pts':  _PAGE_H_PTS,
            'bbox':             px_tbl,
            'bbox_pdf':         pdf_tbl,
            'rows':             rows,
            'question':         question,
            'answer':           answer,
            'answerKeys':       {'row': ans_row_key, 'col': ans_col_key},
        }

    def _get_dual_bbox(self, element_id: str) -> Tuple[List, List]:
        """Return (pixel_bbox, pdf_bbox) for the DOM element with given ID."""
        rect = self._driver.find_element(By.ID, element_id).rect
        x0 = rect['x'];         y0 = rect['y']
        x1 = x0 + rect['width']; y1 = y0 + rect['height']
        px  = [int(x0), int(y0), int(x1), int(y1)]
        pdf = _px_to_pdf(x0, y0, x1, y1)
        return px, pdf

    def _create_q_and_a(self, table, params):
        row_count   = len(table)
        ans_row_idx = np.random.randint(0, row_count)

        # Skip rows that aren't data rows with a row-scope header
        while (table[ans_row_idx][0]['type'] == "DATA"
               or table[ans_row_idx][0].get('scope') == "col"):
            ans_row_idx = (ans_row_idx + 1) % row_count

        ans_row_key = table[ans_row_idx][0]['content']

        col_start = 2 if params['note_column'] else 1
        col_end   = col_start + 3 if params['double_column'] else col_start + 1
        ans_col_idx = np.random.randint(col_start, col_end + 1)
        answer = table[ans_row_idx][ans_col_idx]['content']

        for _ in range(len(table[ans_row_idx])):
            if answer not in self._empty_values:
                break
            ans_col_idx = col_start if ans_col_idx == col_end else ans_col_idx + 1
            answer = table[ans_row_idx][ans_col_idx]['content']

        ans_col_key_idx = ans_col_idx
        if params['double_column']:
            ans_col_key_idx = int(
                col_start + np.floor((ans_col_idx - col_start) / 2))

        ans_col_key = table[0][ans_col_key_idx]['content']
        question    = f"What is the value of {ans_row_key} for {ans_col_key}?"

        return question, answer, ans_row_key, ans_col_key
