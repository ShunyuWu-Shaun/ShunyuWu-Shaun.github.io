#!/usr/bin/env python3
"""Render one verified figure rectangle from an original paper PDF."""

import argparse
from pathlib import Path

import fitz


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--page", type=int, required=True, help="One-based PDF page")
    parser.add_argument("--clip", type=float, nargs=4, required=True,
                        metavar=("X0", "Y0", "X1", "Y1"))
    parser.add_argument("--scale", type=float, default=4)
    args = parser.parse_args()

    with fitz.open(args.source) as document:
        page = document[args.page - 1]
        rectangle = fitz.Rect(args.clip)
        if rectangle.is_empty or not page.rect.contains(rectangle):
            raise ValueError("The selected figure must lie within the PDF page.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image = page.get_pixmap(matrix=fitz.Matrix(args.scale, args.scale),
                               clip=rectangle, alpha=False)
        image.save(args.output)
        print(f"{args.output.name}: {image.width} x {image.height}")


if __name__ == "__main__":
    main()
