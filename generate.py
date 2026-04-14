"""
generate.py — CLI entry point for FinTabPDF

Usage:
    python generate.py --count 100
    python generate.py --count 1000 --output ./my_dataset --name train
"""

import argparse
import sys
from pathlib import Path

# Allow running from the project root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from FinTabPDF import DatasetConfig, DatasetGenerator


def main():
    ap = argparse.ArgumentParser(
        description="Generate a synthetic financial-table PDF dataset.")
    ap.add_argument("--count",  type=int,  default=100,
                    help="Number of tables to generate (default: 100)")
    ap.add_argument("--output", type=str,  default="./output",
                    help="Root output directory (default: ./output)")
    ap.add_argument("--name",   type=str,  default="fintabpdf",
                    help="Dataset sub-directory name (default: fintabpdf)")
    args = ap.parse_args()

    config = DatasetConfig(
        output_dir=args.output,
        dataset_name=args.name,
    )

    with DatasetGenerator(config) as gen:
        gen.generate(args.count)


if __name__ == "__main__":
    main()
