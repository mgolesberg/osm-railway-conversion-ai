import json
import os
from config import (
    get_railways_ways_updated_paths,
    get_railways_ways_missing_path,
    get_railways_ways_valid_paths,
    validate_configuration,
    print_configuration,
)


def has_valid_coordinates(feature):
    """
    Check if a feature has valid, real coordinates.

    Args:
        feature (dict): GeoJSON feature

    Returns:
        bool: True if feature has valid coordinates, False otherwise
    """
    geometry = feature.get("geometry", {})
    coordinates = geometry.get("coordinates", [])

    if not coordinates:
        return False

    geometry_type = geometry.get("type", "")

    if geometry_type == "Point":
        # Check if coordinates are [0, 0] or empty
        if len(coordinates) != 2:
            return False
        return not (coordinates[0] == 0 and coordinates[1] == 0)

    elif geometry_type == "LineString":
        # Check if we have at least 2 points and they're not all [0, 0]
        if len(coordinates) < 2:
            return False
        # Check if all coordinates are [0, 0]
        valid_points = 0
        for coord in coordinates:
            if len(coord) == 2 and not (coord[0] == 0 and coord[1] == 0):
                valid_points += 1
        return valid_points > 0

    elif geometry_type == "Polygon":
        # Check polygon coordinates
        if not coordinates or len(coordinates) == 0:
            return False
        # Check the exterior ring
        exterior_ring = coordinates[0]
        if len(exterior_ring) < 3:
            return False
        valid_points = 0
        for coord in exterior_ring:
            if len(coord) == 2 and not (coord[0] == 0 and coord[1] == 0):
                valid_points += 1
        return valid_points > 0

    # For other geometry types, assume they're valid if they have coordinates
    return True


def extract_missing_coordinates(input_files, output_file):
    """
    Extract features with missing coordinates from multiple input files.

    Args:
        input_files (list): List of input GeoJSON file paths
        output_file (str): Path to output file for missing coordinates
    """
    missing_features = []
    total_processed = 0
    missing_count = 0

    print(f"Checking {len(input_files)} files for missing coordinates...")

    for input_file in input_files:
        if not os.path.exists(input_file):
            print(f"Warning: {input_file} not found, skipping...")
            continue

        print(f"Processing {input_file}...")

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            file_missing = 0
            for feature in data.get("features", []):
                total_processed += 1

                if not has_valid_coordinates(feature):
                    # Add source file information to properties
                    feature["properties"]["source_file"] = os.path.basename(input_file)
                    feature["properties"]["missing_coordinates"] = True

                    missing_features.append(feature)
                    file_missing += 1
                    missing_count += 1

            print(f"  Found {file_missing} features with missing coordinates")

        except Exception as e:
            print(f"Error processing {input_file}: {e}")

    # Create output GeoJSON
    output_data = {
        "type": "FeatureCollection",
        "features": missing_features,
        "metadata": {
            "description": "Railway ways with missing or invalid coordinates",
            "total_features": len(missing_features),
            "source_files": [
                os.path.basename(f) for f in input_files if os.path.exists(f)
            ],
            "extraction_criteria": "Features with [0,0] coordinates, empty coordinates, or invalid geometry",
        },
    }

    # Write output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n=== SUMMARY ===")
    print(f"Total features processed: {total_processed}")
    print(f"Features with missing coordinates: {missing_count}")
    print(f"Percentage missing: {(missing_count/total_processed*100):.1f}%")
    print(f"Output written to: {output_file}")

    return missing_count, total_processed


def create_valid_coordinates_files(input_files, output_files=None):
    """
    Create new files containing only features with valid coordinates.

    Args:
        input_files (list): List of input GeoJSON file paths
        output_files (list): List of output file paths (optional)
    """
    print(f"\nCreating files with valid coordinates only...")

    for i, input_file in enumerate(input_files):
        if not os.path.exists(input_file):
            continue

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            valid_features = []
            for feature in data.get("features", []):
                if has_valid_coordinates(feature):
                    valid_features.append(feature)

            # Use provided output file or create default
            if output_files and i < len(output_files):
                output_file = output_files[i]
            else:
                output_file = f"railways_ways_valid_{i+1}.geojson"

            output_data = {"type": "FeatureCollection", "features": valid_features}

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output_data, f, ensure_ascii=False, separators=(",", ":"))

            original_count = len(data.get("features", []))
            valid_count = len(valid_features)
            print(
                f"  {output_file}: {valid_count}/{original_count} features ({valid_count/original_count*100:.1f}% valid)"
            )

        except Exception as e:
            print(f"Error processing {input_file}: {e}")


def main():
    """
    Main function to extract missing coordinates from updated railway ways files using configuration.
    """
    # Print configuration and validate
    print_configuration()

    if not validate_configuration():
        return

    # Get file paths from configuration
    input_files = get_railways_ways_updated_paths()
    missing_output = get_railways_ways_missing_path()
    valid_outputs = get_railways_ways_valid_paths()

    print(f"Input files: {input_files}")
    print(f"Missing coordinates output: {missing_output}")
    print(f"Valid coordinates outputs: {valid_outputs}")
    print("=" * 60)

    # Extract missing coordinates
    missing_count, total_count = extract_missing_coordinates(
        input_files, missing_output
    )

    # Optionally create "clean" files with only valid coordinates
    if missing_count > 0:
        create_valid_coordinates_files(input_files, valid_outputs)
        print(f"\nClean files (valid coordinates only) created in country directory")


if __name__ == "__main__":
    main()
