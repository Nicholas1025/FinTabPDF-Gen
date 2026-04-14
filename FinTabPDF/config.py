from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatasetConfig:
    """
    Configuration for FinTabPDF dataset generation.

    Attributes:
        output_dir    : Root directory where datasets are written.
        dataset_name  : Sub-directory name for this dataset.
        window_width  : Chrome window width in pixels (A4 at 96 DPI = 794).
        window_height : Chrome window height in pixels (A4 at 96 DPI = 1123).

    The PDF page dimensions (in points) are derived automatically:
        page_width_pts  = window_width  * 72 / 96  ≈ 595.5
        page_height_pts = window_height * 72 / 96  ≈ 842.25
    """

    output_dir:    str = "./output"
    dataset_name:  str = "fintabpdf"

    # A4 at 96 DPI — must match _PAGE_W_PX / _PAGE_H_PX in generator_annotation.py
    window_width:  int = 794
    window_height: int = 1123
