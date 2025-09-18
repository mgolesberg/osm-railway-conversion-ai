#!/usr/bin/env python3
"""
Script to flatten GeoJSON files by removing unnecessary whitespace
while preserving the JSON structure for better size comparison.
"""

import json
import os
from pathlib import Path


def flatten_geojson(input_file: str, output_file: str = None) -> None:
    """
    Flatten a GeoJSON file by removing unnecessary whitespace.

    Args:
        input_file: Path to the input GeoJSON file
        output_file: Path to the output flattened file (optional)
    """
    if output_file is None:
        # Create output filename by adding '_flattened' before the extension
        input_path = Path(input_file)
        output_file = (
            input_path.parent / f"{input_path.stem}_flattened{input_path.suffix}"
        )

    print(f"Reading {input_file}...")

    # Read the original file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Get original file size
    original_size = os.path.getsize(input_file)

    print(
        f"Original file size: {original_size:,} bytes ({original_size / 1024 / 1024:.2f} MB)"
    )

    # Write flattened version
    print(f"Writing flattened version to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)

    # Get new file size
    new_size = os.path.getsize(output_file)

    print(f"Flattened file size: {new_size:,} bytes ({new_size / 1024 / 1024:.2f} MB)")
    print(
        f"Size reduction: {original_size - new_size:,} bytes ({((original_size - new_size) / original_size) * 100:.1f}% smaller)"
    )


if __name__ == "__main__":
    # Flatten the railways combined polylines file
    input_file = "china/railways_combined_polylines.geojson"

    if os.path.exists(input_file):
        flatten_geojson(input_file)
    else:
        print(f"Error: File {input_file} not found!")
