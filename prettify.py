import json
import os
import glob


def prettify_geojson_file(input_file, output_file=None):
    """
    Prettify a GeoJSON file by formatting it with proper indentation.

    Args:
        input_file (str): Path to input GeoJSON file
        output_file (str): Path to output file (if None, overwrites input)
    """
    if not os.path.exists(input_file):
        print(f"Warning: {input_file} not found, skipping...")
        return False

    try:
        # Read the file
        print(f"Prettifying {input_file}...")
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Write back with pretty formatting
        output_path = output_file if output_file else input_file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, separators=(",", ": "))

        # Get file size info
        file_size = os.path.getsize(output_path)
        feature_count = len(data.get("features", []))

        print(f"  ✓ {output_path}")
        print(f"    Features: {feature_count:,}")
        print(f"    Size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

        return True

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}")
        return False
    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return False


def prettify_railways_valid_files():
    """
    Prettify all railways_ways_valid_*.geojson files.
    """
    # Find all valid railways files
    pattern = "railways_ways_valid_*.geojson"
    files = glob.glob(pattern)

    if not files:
        print(f"No files found matching pattern: {pattern}")
        print("Looking for individual files...")

        # Try individual files
        files = []
        for i in range(1, 7):
            filename = f"railways_ways_{i}_updated.geojson"
            if os.path.exists(filename):
                files.append(filename)

    if not files:
        print("No railways_ways_valid_*.geojson files found!")
        print("Make sure you've run the coordinate extraction script first.")
        return

    print(f"Found {len(files)} files to prettify:")
    for file in sorted(files):
        print(f"  - {file}")

    print("\nPrettifying files...")
    print("=" * 50)

    success_count = 0
    total_features = 0
    total_size = 0

    for file in sorted(files):
        if prettify_geojson_file(file):
            success_count += 1

            # Add to totals
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                total_features += len(data.get("features", []))
                total_size += os.path.getsize(file)
            except:
                pass
        print()

    print("=" * 50)
    print(f"SUMMARY:")
    print(f"Files processed: {success_count}/{len(files)}")
    print(f"Total features: {total_features:,}")
    print(f"Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")

    if success_count == len(files):
        print("✓ All files successfully prettified!")
    else:
        print(f"⚠ {len(files) - success_count} files had errors")


def prettify_specific_files(file_list):
    """
    Prettify a specific list of files.

    Args:
        file_list (list): List of file paths to prettify
    """
    print(f"Prettifying {len(file_list)} specified files...")
    print("=" * 50)

    success_count = 0
    for file in file_list:
        if prettify_geojson_file(file):
            success_count += 1
        print()

    print("=" * 50)
    print(f"Files processed: {success_count}/{len(file_list)}")


def main():
    """
    Main function - prettify all valid railways files.
    """
    print("GeoJSON Prettifier")
    print("=" * 50)

    # Option to prettify specific files or all valid files
    import sys

    if len(sys.argv) > 1:
        # Prettify specific files passed as arguments
        file_list = sys.argv[1:]
        prettify_specific_files(file_list)
    else:
        # Prettify all railways_ways_valid_*.geojson files
        prettify_railways_valid_files()


if __name__ == "__main__":
    main()
