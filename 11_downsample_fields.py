#!/usr/bin/env python3
"""
Advanced downsample script for China railways data.
Takes railways_ways_downsampled_simple.geojson and applies advanced processing:
- Field coverage analysis and filtering
- Coordinate precision rounding
- Name field language filtering
- Property field exclusion
"""

import json
import os
import re

# import math  # REMOVED: No longer needed without parallel detection
from typing import Dict, List, Any

# Configuration
COUNTRY_DIR = "china"
INPUT_FILE = "railways_ways_downsampled_simple_algorithm.geojson"
OUTPUT_FILE = "railways_ways_downsampled_advanced.geojson"

# # Railway types to keep (only rail)
# KEEP_RAILWAY_TYPES = {"rail"}

# # Usage types to keep
# KEEP_USAGE_TYPES = {"main", "branch", "military", "freight"}

# Fields to exclude
EXCLUDED_FIELDS = {
    "osm_id",
    "osm_type",
    "node_ids",
    "gauge",
    "electrified",
    "voltage",
    "maxspeed",
    "alt_name",
    "old_name",
    "wikipedia",
    "was_names",
    "operator",
    "maxspeed_designed",
    "public_transport",
    "node_count",
    "frequency",
}

# Languages to keep for name fields (English and Chinese)
KEEP_LANGUAGES = {"en", "zh", "zh-Hans", "zh-Hant"}

# Parallel track detection parameters (REMOVED)
# PARALLEL_TOLERANCE_METERS = 50  # Max distance between parallel tracks
# MIN_TRACK_LENGTH_METERS = 100  # Min track length for parallel detection
# PARALLEL_ANGLE_TOLERANCE_DEGREES = 15  # Max angle difference for parallel tracks


def is_chinese_text(text: str) -> bool:
    """Check if text contains Chinese characters."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def is_english_text(text: str) -> bool:
    """Check if text contains only English characters."""
    return bool(re.match(r"^[a-zA-Z\s\-\.]+$", text))


def round_coordinates(geometry: Dict[str, Any], precision: int = 4) -> Dict[str, Any]:
    """
    Round coordinates in geometry to specified decimal places.
    """
    if geometry.get("type") == "LineString":
        coords = geometry.get("coordinates", [])
        rounded_coords = [
            [round(coord[0], precision), round(coord[1], precision)] for coord in coords
        ]
        return {"type": "LineString", "coordinates": rounded_coords}
    elif geometry.get("type") == "MultiLineString":
        coords = geometry.get("coordinates", [])
        rounded_coords = [
            [[round(coord[0], precision), round(coord[1], precision)] for coord in line]
            for line in coords
        ]
        return {"type": "MultiLineString", "coordinates": rounded_coords}
    else:
        return geometry


def should_keep_name_field(field_name: str, field_value: str) -> bool:
    """
    Determine if a name field should be kept based on language.
    Keep fields that are:
    - Generic 'name' field
    - English names (name:en)
    - Chinese names (name:zh, name:zh-Hans, name:zh-Hant)
    """
    if field_name == "name":
        return True

    if field_name.startswith("name:"):
        lang = field_name.split(":", 1)[1]
        if lang in KEEP_LANGUAGES:
            return True

    return False


# Note: Usage filtering is already done in the simple downsampled file


def filter_properties(
    properties: Dict[str, Any], field_coverage: Dict[str, float]
) -> Dict[str, Any]:
    """
    Filter properties dictionary to remove unwanted fields.
    Note: Usage filtering is already done in the simple downsampled file.
    """
    filtered_props = {}

    # Filter out excluded fields
    for key, value in properties.items():
        if key in EXCLUDED_FIELDS:
            continue

        # Skip fields with less than 20% coverage
        if key in field_coverage and field_coverage[key] < 0.20:
            continue

        # Handle name fields specially
        if key.startswith("name"):
            if should_keep_name_field(key, str(value)):
                filtered_props[key] = value
        else:
            filtered_props[key] = value

    return filtered_props


def calculate_field_coverage(input_file: str) -> Dict[str, float]:
    """
    Calculate field coverage from the simple downsampled file to determine which fields to keep.
    """
    print("Calculating field coverage from simple downsampled file...")

    field_counts = {}
    total_features = 0

    print(f"  Processing file: {os.path.basename(input_file)}")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    total_features = len(features)

    print(f"    Analyzing {total_features:,} features...")

    for i, feature in enumerate(features):
        # Progress tracking for large files
        if i % 5000 == 0 or i == total_features - 1:
            progress = ((i + 1) / total_features) * 100
            print(f"      Progress: {progress:.1f}% ({i+1:,}/{total_features:,})")

        properties = feature.get("properties", {})

        # Count all fields (since usage filtering already done in simple version)
        for key in properties.keys():
            field_counts[key] = field_counts.get(key, 0) + 1

    # Calculate coverage percentages
    field_coverage = {}
    for field, count in field_counts.items():
        coverage = count / total_features
        field_coverage[field] = coverage

    print(f"Analyzed {total_features:,} features from simple downsampled file")
    print(f"Found {len(field_counts)} unique fields")

    # Show fields that will be removed due to low coverage
    low_coverage_fields = [f for f, c in field_coverage.items() if c < 0.20]
    print(
        f"Fields with <20% coverage ({len(low_coverage_fields)}): "
        f"{sorted(low_coverage_fields)}"
    )

    return field_coverage


def process_geojson_file(
    file_path: str, field_coverage: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Process the simple downsampled GeoJSON file and return filtered features.
    Note: Coordinate rounding is now done as the final step.
    """
    print(f"Processing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    total_features = len(features)
    filtered_features = []

    print(f"  Applying advanced filtering to {total_features:,} features...")

    for i, feature in enumerate(features):
        # Progress tracking for large files
        if i % 1000 == 0 or i == total_features - 1:
            progress = ((i + 1) / total_features) * 100
            print(f"    Progress: {progress:.1f}% ({i+1:,}/{total_features:,})")

        properties = feature.get("properties", {})

        # Filter properties (field filtering) - usage filtering already done
        filtered_props = filter_properties(properties, field_coverage)

        filtered_feature = {
            "type": "Feature",
            "geometry": feature.get("geometry"),  # Keep original coordinates
            "properties": filtered_props,
        }
        filtered_features.append(filtered_feature)

    print(f"  Processed {len(filtered_features):,} features")
    return filtered_features


def apply_advanced_processing():
    """
    Main function to apply advanced processing to the simple downsampled file:
    - Field coverage analysis and filtering
    - Coordinate precision rounding
    - Name field language filtering
    - Property field exclusion
    """
    print("Starting ADVANCED processing on simple downsampled file...")
    print("=" * 60)

    # Check if china directory exists
    if not os.path.exists(COUNTRY_DIR):
        print(f"Error: Directory '{COUNTRY_DIR}' not found!")
        return

    # Check if simple downsampled file exists
    input_path = os.path.join(COUNTRY_DIR, INPUT_FILE)
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found!")
        print(
            "Please run 7_downsample_simple.py first to create the simple downsampled file."
        )
        return

    print(f"Found input file: {INPUT_FILE}")

    # Calculate field coverage first
    print("\nStep 1/4: Calculating field coverage...")
    field_coverage = calculate_field_coverage(input_path)

    # Process the file
    print(f"\nStep 2/4: Processing file...")
    all_features = process_geojson_file(input_path, field_coverage)

    # Count original features for statistics
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    total_original_features = len(data.get("features", []))

    # Round coordinates as final step
    print("\nStep 3/4: Rounding coordinates...")
    print(f"Rounding coordinates for {len(all_features):,} features...")

    for i, feature in enumerate(all_features):
        if i % 1000 == 0 or i == len(all_features) - 1:
            progress = ((i + 1) / len(all_features)) * 100
            print(f"  Progress: {progress:.1f}% ({i+1:,}/{len(all_features):,})")

        # Round coordinates
        feature["geometry"] = round_coordinates(feature.get("geometry"))

    print("✓ Coordinates rounded successfully!")

    # Create output GeoJSON
    print("\nStep 4/4: Creating output file...")
    output_data = {"type": "FeatureCollection", "features": all_features}

    # Write output file
    output_path = os.path.join(COUNTRY_DIR, OUTPUT_FILE)
    print(f"Writing output to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, separators=(",", ":"))

    print("✓ Output file created successfully!")

    # Print statistics
    print("\n" + "=" * 60)
    print("ADVANCED PROCESSING STATISTICS")
    print("=" * 60)
    print(f"Input features (from simple): {total_original_features:,}")
    print(f"Output features (after advanced processing): {len(all_features):,}")
    print("No features removed - only field filtering and coordinate rounding applied")

    # Show filtering criteria
    # print(f"Railway types kept: {KEEP_RAILWAY_TYPES}")
    # print(f"Usage types kept (must have usage field): {KEEP_USAGE_TYPES}")
    print("Service types removed: crossover, connector")
    print("Coordinate precision: 4 decimal places")
    print(
        "Advanced features: Field coverage analysis, name filtering, property exclusion"
    )

    # Show field filtering statistics
    high_coverage_fields = [f for f, c in field_coverage.items() if c >= 0.20]
    low_coverage_fields = [f for f, c in field_coverage.items() if c < 0.20]
    print(f"Fields kept (≥20% coverage): {len(high_coverage_fields)}")
    print(f"Fields removed (<20% coverage): {len(low_coverage_fields)}")

    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print("=" * 60)

    # Print some examples of filtered features
    print("\nSample of processed features:")
    for i, feature in enumerate(all_features[:3]):
        props = feature.get("properties", {})
        railway_type = props.get("railway", "unknown")
        usage_type = props.get("usage", "unknown")
        name = props.get("name", "unnamed")
        print(
            f"  {i+1}. Railway: {railway_type}, Usage: {usage_type}, " f"Name: {name}"
        )


if __name__ == "__main__":
    apply_advanced_processing()
