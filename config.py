#!/usr/bin/env python3
"""
Global configuration file for OSM conversion pipeline
Contains all constants and settings used across the conversion scripts
"""

import os
import re

# =============================================================================
# GLOBAL CONFIGURATION CONSTANTS
# =============================================================================

# Input file configuration
INPUT_PBF_FILENAME = "czech-republic-250908.osm.pbf"

# Processing configuration
NUM_SPLITS = 6  # Number of files to split railways_ways into
PROGRESS_INTERVAL = 50000  # Print progress every N features

# Output directory configuration
# All output files will be placed in a country-specific subdirectory
BASE_OUTPUT_DIR = os.getcwd()  # Use current working directory as base

# =============================================================================
# DERIVED CONFIGURATION (automatically calculated)
# =============================================================================


def get_country_name(pbf_filename):
    """
    Extract country name from PBF filename.

    Args:
        pbf_filename (str): PBF filename (e.g., "czech-republic-250908.osm.pbf")

    Returns:
        str: Country name (e.g., "czech-republic")
    """
    # Remove .osm.pbf extension
    base_name = pbf_filename.replace(".osm.pbf", "")

    # Extract country name (everything before the last dash followed by numbers)
    # Pattern: country-name-YYYYMMDD -> country-name
    match = re.match(r"^(.+)-(\d{6,8})$", base_name)
    if match:
        return match.group(1)

    # Fallback: use the entire base name if pattern doesn't match
    return base_name


def get_output_directory():
    """
    Get the output directory for the current country.

    Returns:
        str: Path to country-specific output directory
    """
    country_name = get_country_name(INPUT_PBF_FILENAME)
    output_dir = os.path.join(BASE_OUTPUT_DIR, country_name)
    return output_dir


def get_input_path():
    """
    Get the full path to the input PBF file.

    Returns:
        str: Full path to input PBF file
    """
    return os.path.join(BASE_OUTPUT_DIR, INPUT_PBF_FILENAME)


# =============================================================================
# OUTPUT FILE PATHS (automatically generated)
# =============================================================================


def get_railways_nodes_path():
    """Get path for railways nodes output file"""
    return os.path.join(get_output_directory(), "railways_nodes.geojson")


def get_railways_ways_path():
    """Get path for railways ways output file"""
    return os.path.join(get_output_directory(), "railways_ways.geojson")


def get_railways_ways_missing_path():
    """Get path for railways ways missing coordinates file"""
    return os.path.join(
        get_output_directory(), "railways_ways_missing_coordinates.geojson"
    )


def get_railways_ways_split_paths():
    """Get paths for split railways ways files"""
    output_dir = get_output_directory()
    return [
        os.path.join(output_dir, f"railways_ways_{i}.geojson")
        for i in range(1, NUM_SPLITS + 1)
    ]


def get_railways_ways_updated_paths():
    """Get paths for updated railways ways files (with coordinates)"""
    output_dir = get_output_directory()
    return [
        os.path.join(output_dir, f"railways_ways_{i}_updated.geojson")
        for i in range(1, NUM_SPLITS + 1)
    ]


def get_railways_ways_valid_paths():
    """Get paths for railways ways files with valid coordinates only"""
    output_dir = get_output_directory()
    return [
        os.path.join(output_dir, f"railways_ways_valid_{i}.geojson")
        for i in range(1, NUM_SPLITS + 1)
    ]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def ensure_output_directory():
    """
    Create the output directory if it doesn't exist.

    Returns:
        str: Path to the created/existing output directory
    """
    output_dir = get_output_directory()
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def print_configuration():
    """Print current configuration for debugging"""
    print("=" * 60)
    print("OSM CONVERSION CONFIGURATION")
    print("=" * 60)
    print(f"Input PBF file: {INPUT_PBF_FILENAME}")
    print(f"Country name: {get_country_name(INPUT_PBF_FILENAME)}")
    print(f"Base output directory: {BASE_OUTPUT_DIR}")
    print(f"Output directory: {get_output_directory()}")
    print(f"Number of splits: {NUM_SPLITS}")
    print(f"Progress interval: {PROGRESS_INTERVAL:,}")
    print("=" * 60)


# =============================================================================
# MAIN CONFIGURATION VALIDATION
# =============================================================================


def validate_configuration():
    """
    Validate the current configuration and check if input file exists.

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    input_path = get_input_path()

    if not os.path.exists(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        print(f"Please update INPUT_PBF_FILENAME in config.py")
        return False

    # Ensure output directory exists
    ensure_output_directory()

    return True


if __name__ == "__main__":
    # Print configuration when run directly
    print_configuration()
    validate_configuration()
