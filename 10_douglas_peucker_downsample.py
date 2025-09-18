#!/usr/bin/env python3
"""
Douglas-Peucker algorithm downsample script for railways_guangzhou dataset.
Uses Shapely's simplify method with a 250m tolerance to reduce coordinate
density while preserving the essential shape of railway lines.
"""

import json
import os
from typing import Dict, Any
from shapely.geometry import LineString
import pyproj

# Configuration
INPUT_FILE = "china/railways_combined_polylines.geojson"
OUTPUT_FILE = "china/railways_ways_downsampled_simple_algorithm.geojson"
TOLERANCE_METERS = 500  # Douglas-Peucker tolerance in meters

# Coordinate system for distance calculations (WGS84)
WGS84 = pyproj.CRS("EPSG:4326")
# Use a projected coordinate system for accurate distance calculations
# Using UTM Zone 49N (covers Guangzhou area)
UTM_PROJECTION = pyproj.CRS("EPSG:32649")  # UTM Zone 49N


def transform_coordinates(geometry_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform coordinates from WGS84 to UTM for accurate distance calculations.
    """
    if geometry_dict.get("type") == "LineString":
        coords = geometry_dict.get("coordinates", [])

        # Create transformer from WGS84 to UTM
        transformer = pyproj.Transformer.from_crs(WGS84, UTM_PROJECTION, always_xy=True)

        # Transform coordinates
        transformed_coords = []
        for coord in coords:
            lon, lat = coord[0], coord[1]
            x, y = transformer.transform(lon, lat)
            transformed_coords.append([x, y])

        return {"type": "LineString", "coordinates": transformed_coords}
    elif geometry_dict.get("type") == "MultiLineString":
        coords = geometry_dict.get("coordinates", [])

        # Create transformer from WGS84 to UTM
        transformer = pyproj.Transformer.from_crs(WGS84, UTM_PROJECTION, always_xy=True)

        # Transform coordinates for each line
        transformed_coords = []
        for line in coords:
            transformed_line = []
            for coord in line:
                lon, lat = coord[0], coord[1]
                x, y = transformer.transform(lon, lat)
                transformed_line.append([x, y])
            transformed_coords.append(transformed_line)

        return {"type": "MultiLineString", "coordinates": transformed_coords}
    else:
        return geometry_dict


def transform_coordinates_back(geometry_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform coordinates back from UTM to WGS84 for output.
    """
    if geometry_dict.get("type") == "LineString":
        coords = geometry_dict.get("coordinates", [])

        # Create transformer from UTM to WGS84
        transformer = pyproj.Transformer.from_crs(UTM_PROJECTION, WGS84, always_xy=True)

        # Transform coordinates back
        transformed_coords = []
        for coord in coords:
            x, y = coord[0], coord[1]
            lon, lat = transformer.transform(x, y)
            transformed_coords.append([lon, lat])

        return {"type": "LineString", "coordinates": transformed_coords}
    elif geometry_dict.get("type") == "MultiLineString":
        coords = geometry_dict.get("coordinates", [])

        # Create transformer from UTM to WGS84
        transformer = pyproj.Transformer.from_crs(UTM_PROJECTION, WGS84, always_xy=True)

        # Transform coordinates back for each line
        transformed_coords = []
        for line in coords:
            transformed_line = []
            for coord in line:
                x, y = coord[0], coord[1]
                lon, lat = transformer.transform(x, y)
                transformed_line.append([lon, lat])
            transformed_coords.append(transformed_line)

        return {"type": "MultiLineString", "coordinates": transformed_coords}
    else:
        return geometry_dict


def simplify_geometry(
    geometry_dict: Dict[str, Any], tolerance_meters: float
) -> Dict[str, Any]:
    """
    Apply Douglas-Peucker simplification to a geometry.
    """
    if geometry_dict.get("type") == "LineString":
        coords = geometry_dict.get("coordinates", [])

        # Skip if less than 3 points (can't simplify)
        if len(coords) < 3:
            return geometry_dict

        # Create LineString and simplify
        line = LineString(coords)
        simplified_line = line.simplify(tolerance_meters, preserve_topology=True)

        # Convert back to coordinate list
        if simplified_line.is_empty:
            return geometry_dict

        simplified_coords = list(simplified_line.coords)

        return {"type": "LineString", "coordinates": simplified_coords}

    elif geometry_dict.get("type") == "MultiLineString":
        coords = geometry_dict.get("coordinates", [])
        simplified_coords = []

        for line_coords in coords:
            if len(line_coords) < 3:
                simplified_coords.append(line_coords)
                continue

            # Create LineString and simplify
            line = LineString(line_coords)
            simplified_line = line.simplify(tolerance_meters, preserve_topology=True)

            if simplified_line.is_empty:
                simplified_coords.append(line_coords)
            else:
                simplified_coords.append(list(simplified_line.coords))

        return {"type": "MultiLineString", "coordinates": simplified_coords}

    else:
        return geometry_dict


def process_feature(feature: Dict[str, Any], tolerance_meters: float) -> Dict[str, Any]:
    """
    Process a single feature by applying Douglas-Peucker simplification.
    """
    geometry = feature.get("geometry", {})
    properties = feature.get("properties", {})

    # Transform to UTM for accurate distance calculations
    utm_geometry = transform_coordinates(geometry)

    # Apply Douglas-Peucker simplification
    simplified_utm_geometry = simplify_geometry(utm_geometry, tolerance_meters)

    # Transform back to WGS84
    simplified_geometry = transform_coordinates_back(simplified_utm_geometry)

    return {
        "type": "Feature",
        "geometry": simplified_geometry,
        "properties": properties,
    }


def downsample_railways():
    """
    Main function to downsample the railways_guangzhou dataset using
    Douglas-Peucker algorithm.
    """
    print("Starting Douglas-Peucker downsample process...")
    print("=" * 60)
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Tolerance: {TOLERANCE_METERS} meters")
    print("=" * 60)

    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found!")
        return

    # Load the GeoJSON data
    print(f"Loading data from {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    total_features = len(features)
    print(f"Loaded {total_features:,} features")

    # Process features
    print("\nProcessing features with Douglas-Peucker algorithm...")
    processed_features = []
    original_coord_count = 0
    simplified_coord_count = 0

    for i, feature in enumerate(features):
        # Progress tracking
        if i % 1000 == 0 or i == total_features - 1:
            progress = ((i + 1) / total_features) * 100
            print(f"  Progress: {progress:.1f}% ({i+1:,}/{total_features:,})")

        # Count original coordinates
        geometry = feature.get("geometry", {})
        if geometry.get("type") == "LineString":
            original_coord_count += len(geometry.get("coordinates", []))
        elif geometry.get("type") == "MultiLineString":
            for line_coords in geometry.get("coordinates", []):
                original_coord_count += len(line_coords)

        # Process feature
        processed_feature = process_feature(feature, TOLERANCE_METERS)
        processed_features.append(processed_feature)

        # Count simplified coordinates
        simplified_geometry = processed_feature.get("geometry", {})
        if simplified_geometry.get("type") == "LineString":
            simplified_coord_count += len(simplified_geometry.get("coordinates", []))
        elif simplified_geometry.get("type") == "MultiLineString":
            for line_coords in simplified_geometry.get("coordinates", []):
                simplified_coord_count += len(line_coords)

    # Create output GeoJSON
    print("\nCreating output file...")
    output_data = {"type": "FeatureCollection", "features": processed_features}

    # Write output file
    print(f"Writing output to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, separators=(",", ":"))

    print("✓ Output file created successfully!")

    # Print statistics
    print("\n" + "=" * 60)
    print("DOUGLAS-PEUCKER DOWNSAMPLE STATISTICS")
    print("=" * 60)
    print(f"Input features: {total_features:,}")
    print(f"Output features: {len(processed_features):,}")
    print(f"Original coordinates: {original_coord_count:,}")
    print(f"Simplified coordinates: {simplified_coord_count:,}")

    if original_coord_count > 0:
        reduction_pct = (
            (original_coord_count - simplified_coord_count) / original_coord_count * 100
        )
        print(f"Coordinate reduction: {reduction_pct:.1f}%")

    print(f"Tolerance: {TOLERANCE_METERS} meters")
    print("Algorithm: Douglas-Peucker with topology preservation")
    print("Coordinate system: UTM Zone 49N for distance calculations")
    print(f"Input file: {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print("=" * 60)

    # Print some examples
    print("\nSample of processed features:")
    for i, feature in enumerate(processed_features[:3]):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        name = props.get("name", "unnamed")
        railway_type = props.get("railway", "unknown")
        usage = props.get("usage", "unknown")

        coord_count = 0
        if geometry.get("type") == "LineString":
            coord_count = len(geometry.get("coordinates", []))
        elif geometry.get("type") == "MultiLineString":
            for line_coords in geometry.get("coordinates", []):
                coord_count += len(line_coords)

        print(
            f"  {i+1}. {name} ({railway_type}, {usage}) - " f"{coord_count} coordinates"
        )


if __name__ == "__main__":
    downsample_railways()
