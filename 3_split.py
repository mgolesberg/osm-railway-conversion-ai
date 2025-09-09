import json
import math
from config import (
    get_railways_ways_path,
    get_railways_ways_split_paths,
    NUM_SPLITS,
    validate_configuration,
    print_configuration,
)


def split_geojson(input_file, num_files=6, output_files=None):
    """
    Split a large GeoJSON file into multiple smaller files.

    Args:
        input_file (str): Path to the input GeoJSON file
        num_files (int): Number of output files to create
        output_files (list): Optional list of output file paths
    """

    # Read the original GeoJSON file
    print(f"Reading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data["features"]
    total_features = len(features)

    print(f"Total features: {total_features}")

    # Calculate features per file
    features_per_file = math.ceil(total_features / num_files)
    print(f"Features per file: ~{features_per_file}")

    # Split and write files
    for i in range(num_files):
        start_idx = i * features_per_file
        end_idx = min((i + 1) * features_per_file, total_features)

        # Skip if no features left
        if start_idx >= total_features:
            break

        # Use provided output file path or create default
        if output_files and i < len(output_files):
            output_file = output_files[i]
        else:
            # Fallback: create output filename
            base_name = input_file.replace(".geojson", "")
            output_file = f"{base_name}_{i+1}.geojson"

        # Create new GeoJSON structure
        output_data = {
            "type": "FeatureCollection",
            "features": features[start_idx:end_idx],
        }

        # Write the file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, separators=(",", ":"))

        actual_features = len(output_data["features"])
        print(f"Created {output_file} with {actual_features} features")

    print("Split complete!")


def main():
    """
    Main function to split railways_ways.geojson using configuration
    """
    # Print configuration and validate
    print_configuration()

    if not validate_configuration():
        return

    input_file = get_railways_ways_path()
    output_files = get_railways_ways_split_paths()

    print(f"Input file: {input_file}")
    print(f"Number of splits: {NUM_SPLITS}")
    print(f"Output files: {output_files}")
    print("=" * 60)

    try:
        split_geojson(input_file, NUM_SPLITS, output_files)
        print(f"\n✅ Split completed successfully!")
        print(f"   Created {NUM_SPLITS} split files in country directory")
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_file}")
        print("Please run the ways converter first to create railways_ways.geojson")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
