# FinTabPDF-Gen

A synthetic financial table **PDF** dataset generator, extended from [SynFinTabs](https://ethanbradley.co.uk/research/synfintabs) by Bradley et al. (2026).

The key extension over the original is **PDF output with a native text layer** and **dual-coordinate ground truth** (screen pixels + PDF points), making it directly compatible with PDF extraction tools such as Camelot and pdfplumber — no OCR required.

---

## What It Generates

Each sample consists of:

| File | Description |
|---|---|
| `pdf/<id>.pdf` | A4 PDF with native text layer (rendered via headless Chrome) |
| `html/<id>.html` | Intermediate HTML (kept for debugging) |
| `annotations.json` | Ground-truth annotations for all samples |

### Ground Truth Format

```json
{
  "id": "HF61dtR6l0L",
  "theme": 2,
  "page_width_pts": 595.5,
  "page_height_pts": 842.25,

  "bbox":     [0, 0, 657, 601],
  "bbox_pdf": [0.0, 391.5, 492.75, 842.25],

  "rows": [
    {
      "bbox":     [0, 0, 657, 27],
      "bbox_pdf": [0.0, 815.25, 492.75, 842.25],
      "cells": [
        {
          "bbox":     [0, 0, 263, 27],
          "bbox_pdf": [0.0, 815.25, 197.25, 842.25],
          "text": "Fixed assets",
          "words": [
            {"bbox": [...], "bbox_pdf": [...], "text": "Fixed"},
            {"bbox": [...], "bbox_pdf": [...], "text": "assets"}
          ]
        }
      ]
    }
  ],

  "question": "What is the value of Fixed assets for 2022?",
  "answer": "6,428",
  "answerKeys": {"row": "Fixed assets", "col": "2022"}
}
```

**Coordinate systems:**
- `bbox` — screen pixels, top-left origin, y-down
- `bbox_pdf` — PDF points (1 pt = 1/72 inch), bottom-left origin, y-up

Every table, row, cell, and word has both coordinate representations.

---


## Installation

```bash
pip install selenium nltk htmltree nanoid numpy tqdm
python -c "import nltk; nltk.download('words')"
```

Chrome must be installed (used headless for rendering and PDF export).

---

## Usage

```bash
# Generate 100 samples (default output: ./output/FinTab_PDF/)
python generate.py --count 100

# Custom output directory and dataset name
python generate.py --count 1000 --output D:/datasets --name train

# Separate train / test splits
python generate.py --count 800 --output ./data --name train
python generate.py --count 200 --output ./data --name test
```

Speed: ~2–3 seconds per sample.

---

## Using with pdfplumber

```python
import pdfplumber

with pdfplumber.open("output/FinTab_PDF/pdf/HF61dtR6l0L.pdf") as pdf:
    words = pdf.pages[0].extract_words()
    # Each word: {'text': ..., 'x0': ..., 'y0': ..., 'x1': ..., 'y1': ...}
    # pdfplumber uses top-left origin; compare against bbox_pdf with y-flip:
    # pdf_y0 = page_height - pdfplumber_y1
```

---

## Project Structure

```
FinTabPDF/
├── FinTabPDF/
│   ├── config.py               # DatasetConfig dataclass
│   ├── generator_table.py      # Randomised table data structure
│   ├── generator_theme.py      # 6 CSS visual themes
│   ├── generator_document.py   # HTML rendering (+ @media print injection)
│   ├── generator_pdf.py        # Chrome CDP Page.printToPDF
│   ├── generator_annotation.py # DOM bbox reading + coordinate conversion
│   └── generator_dataset.py    # Orchestration pipeline
├── generate.py                 # CLI entry point
├── requirements.txt
└── README.md
```

---

## Citation

This project is built on top of **SynFinTabs** by Bradley et al. If you use this software, please cite the original work:

```bibtex
@inproceedings{bradley2026synfintabs,
    title        = {Syn{F}in{T}abs: A Dataset of Synthetic Financial Tables for Information and Table Extraction},
    author       = {Bradley, Ethan and Roman, Muhammad and Rafferty, Karen and Devereux, Barry},
    year         = 2026,
    month        = jan,
    booktitle    = {Document Analysis and Recognition -- ICDAR 2025 Workshops},
    publisher    = {Springer Nature Switzerland},
    address      = {Cham},
    pages        = {85--100},
    doi          = {10.1007/978-3-032-09371-4_6},
    isbn         = {978-3-032-09371-4},
    editor       = {Jin, Lianwen and Zanibbi, Richard and Eglin, Veronique},
    abstract     = {Table extraction from document images is a challenging AI problem,
                    and labelled data for many content domains is difficult to come by.
                    Existing table extraction datasets often focus on scientific tables
                    due to the vast amount of academic articles that are readily available,
                    along with their source code. However, there are significant layout
                    and typographical differences between tables found across scientific,
                    financial, and other domains. Current datasets often lack the words,
                    and their positions, contained within the tables, instead relying on
                    unreliable OCR to extract these features for training modern machine
                    learning models on natural language processing tasks. Therefore, there
                    is a need for a more general method of obtaining labelled data. We
                    present SynFinTabs, a large-scale, labelled dataset of synthetic
                    financial tables. Our hope is that our method of generating these
                    synthetic tables is transferable to other domains. To demonstrate the
                    effectiveness of our dataset in training models to extract information
                    from table images, we create FinTabQA, a layout large language model
                    trained on an extractive question-answering task. We test our model
                    using real-world financial tables and compare it to a state-of-the-art
                    generative model and discuss the results. We make the dataset, model,
                    and dataset generation code publicly available
                    (https://ethanbradley.co.uk/research/synfintabs).}
}
```

Original code: [https://github.com/ethanbradley/synfintabgen](https://github.com/ethanbradley/synfintabgen)  
Original dataset: [https://ethanbradley.co.uk/research/synfintabs](https://ethanbradley.co.uk/research/synfintabs)
