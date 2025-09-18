#!/usr/bin/env python3
"""
Simple downsample script for China railways data.
Combines railways_ways_1-6_updated.geojson files and filters by usage only.
"""

import json
import os
from typing import Dict, List, Any

# Configuration
COUNTRY_DIR = "china"
OUTPUT_FILE = "railways_ways_downsampled_simple.geojson"

# Railway types to keep (only rail)
KEEP_RAILWAY_TYPES = {"rail"}

# Usage types to keep
KEEP_USAGE_TYPES = {"main", "branch", "military", "freight"}


def filter_by_usage(properties: Dict[str, Any]) -> bool:
    """
    Filter function to check if a feature should be kept based on
    railway type and usage.
    """
    # Check if railway type should be kept (only rail)
    railway_type = properties.get("railway", "")
    if railway_type not in KEEP_RAILWAY_TYPES:
        return False

    # Check if usage type should be kept
    usage_type = properties.get("usage", "")
    if not usage_type or usage_type not in KEEP_USAGE_TYPES:
        return False

    # Remove anything with service IN ('crossover', 'connector')
    service_type = properties.get("service", "")
    if service_type in ("crossover", "connector"):
        return False

    return True


def process_geojson_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Process a single GeoJSON file and return filtered features.
    """
    print(f"Processing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    total_features = len(features)
    filtered_features = []

    print(f"  Filtering {total_features:,} features...")

    for i, feature in enumerate(features):
        # Progress tracking for large files
        if i % 1000 == 0 or i == total_features - 1:
            progress = ((i + 1) / total_features) * 100
            print(f"    Progress: {progress:.1f}% ({i+1:,}/{total_features:,})")

        properties = feature.get("properties", {})

        # Filter by usage
        if filter_by_usage(properties):
            filtered_feature = {
                "type": "Feature",
                "geometry": feature.get("geometry"),
                "properties": properties,  # Keep all properties
            }
            filtered_features.append(filtered_feature)

    print(f"  Kept {len(filtered_features):,} features out of {total_features:,}")
    return filtered_features


def combine_and_downsample():
    """
    Main function to combine all railways_ways files and filter by usage.
    """
    print("Starting simple downsample process for China railways data...")
    print("=" * 60)

    # Check if china directory exists
    if not os.path.exists(COUNTRY_DIR):
        print(f"Error: Directory '{COUNTRY_DIR}' not found!")
        return

    # Find all railways_ways_*_updated.geojson files
    input_files = []
    for i in range(1, 7):  # Files 1-6
        file_path = os.path.join(COUNTRY_DIR, f"railways_ways_{i}_updated.geojson")
        if os.path.exists(file_path):
            input_files.append(file_path)
        else:
            print(f"Warning: File {file_path} not found!")

    if not input_files:
        print("Error: No input files found!")
        return

    print(f"Found {len(input_files)} input files to process")

    # Process all files
    print(f"\nProcessing {len(input_files)} files...")
    all_features = []
    total_original_features = 0

    for file_idx, file_path in enumerate(input_files):
        print(
            f"\nProcessing file {file_idx + 1}/{len(input_files)}: {os.path.basename(file_path)}"
        )
        features = process_geojson_file(file_path)
        all_features.extend(features)

        # Count original features for statistics
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        total_original_features += len(data.get("features", []))

    # Create output GeoJSON
    print("\nCreating output file...")
    output_data = {"type": "FeatureCollection", "features": all_features}

    # Write output file
    output_path = os.path.join(COUNTRY_DIR, OUTPUT_FILE)
    print(f"Writing output to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, separators=(",", ":"))

    print("✓ Output file created successfully!")

    # Print statistics
    print("\n" + "=" * 60)
    print("SIMPLE DOWNSAMPLE STATISTICS")
    print("=" * 60)
    print(f"Original features: {total_original_features:,}")
    print(f"After usage filtering: {len(all_features):,}")
    reduction_pct = (
        (total_original_features - len(all_features)) / total_original_features * 100
    )
    print(f"Total reduction: {reduction_pct:.1f}%")

    # Show filtering criteria
    print(f"Railway types kept: {KEEP_RAILWAY_TYPES}")
    print(f"Usage types kept (must have usage field): {KEEP_USAGE_TYPES}")
    print("Service types removed: crossover, connector")
    print("All properties preserved (no field filtering)")

    print(f"Output file: {output_path}")
    print("=" * 60)

    # Print some examples of filtered features
    print("\nSample of filtered features:")
    for i, feature in enumerate(all_features[:3]):
        props = feature.get("properties", {})
        railway_type = props.get("railway", "unknown")
        usage_type = props.get("usage", "unknown")
        name = props.get("name", "unnamed")
        print(
            f"  {i+1}. Railway: {railway_type}, Usage: {usage_type}, " f"Name: {name}"
        )


if __name__ == "__main__":
    combine_and_downsample()
