import json
import osmium
from config import (
    get_input_path,
    get_railways_ways_split_paths,
    get_railways_ways_updated_paths,
    validate_configuration,
    print_configuration,
)


class NodeCoordinateExtractor(osmium.SimpleHandler):
    """Extract coordinates for specific node IDs from OSM PBF file"""

    def __init__(self, required_node_ids):
        osmium.SimpleHandler.__init__(self)
        self.required_node_ids = required_node_ids
        self.node_coords = {}
        self.found_count = 0

    def node(self, n):
        """Process OSM nodes and extract coordinates for required IDs"""
        if n.id in self.required_node_ids and n.location.valid():
            self.node_coords[n.id] = [n.location.lon, n.location.lat]
            self.found_count += 1


def collect_all_node_ids(ways_files):
    """
    Collect all unique node IDs from railways_ways_x.geojson files.

    Args:
        ways_files (list): List of ways file paths

    Returns:
        set: Set of unique node IDs referenced in ways files
    """
    print("Collecting all node IDs from railways_ways files...")

    all_node_ids = set()

    for ways_file in ways_files:
        try:
            with open(ways_file, "r", encoding="utf-8") as f:
                ways_data = json.load(f)

            for feature in ways_data["features"]:
                node_ids = feature["properties"].get("node_ids", [])
                all_node_ids.update(node_ids)

        except FileNotFoundError:
            print(f"Warning: {ways_file} not found, skipping...")
        except Exception as e:
            print(f"Error reading {ways_file}: {e}")

    print(f"Collected {len(all_node_ids)} unique node IDs")
    return all_node_ids


def load_specific_node_coordinates(pbf_file, required_node_ids):
    """
    Load coordinates for specific node IDs from OSM PBF file.

    Args:
        pbf_file (str): Path to the OSM PBF file
        required_node_ids (set): Set of node IDs to load coordinates for

    Returns:
        dict: Dictionary mapping node osm_id to coordinates
    """
    print(
        f"Loading coordinates for {len(required_node_ids)} specific nodes "
        f"from {pbf_file}..."
    )

    # Create extractor and process PBF file
    extractor = NodeCoordinateExtractor(required_node_ids)
    extractor.apply_file(pbf_file)

    print(
        f"Found coordinates for {extractor.found_count} out of "
        f"{len(required_node_ids)} requested nodes"
    )

    if extractor.found_count < len(required_node_ids):
        missing_count = len(required_node_ids) - extractor.found_count
        print(f"Warning: {missing_count} node IDs not found in PBF file")

    return extractor.node_coords


def update_way_coordinates(ways_file, node_coords, output_file):
    """
    Update coordinates in a ways file using node coordinate lookup.

    Args:
        ways_file (str): Path to input ways file
        node_coords (dict): Dictionary mapping node IDs to coordinates
        output_file (str): Path to output file
    """
    print(f"Processing {ways_file}...")

    with open(ways_file, "r", encoding="utf-8") as f:
        ways_data = json.load(f)

    updated_features = []
    missing_nodes = set()

    for feature in ways_data["features"]:
        # Get the node IDs for this way
        node_ids = feature["properties"].get("node_ids", [])

        if not node_ids:
            # If no node_ids, keep original coordinates
            updated_features.append(feature)
            continue

        # Collect coordinates for all nodes in this way
        way_coordinates = []
        for node_id in node_ids:
            if node_id in node_coords:
                way_coordinates.append(node_coords[node_id])
            else:
                missing_nodes.add(node_id)

        # Update the feature based on number of coordinates
        if len(way_coordinates) == 0:
            # No valid coordinates found, keep original
            updated_features.append(feature)
        elif len(way_coordinates) == 1:
            # Single point
            feature["geometry"] = {"type": "Point", "coordinates": way_coordinates[0]}
            updated_features.append(feature)
        else:
            # Multiple points - create LineString
            feature["geometry"] = {"type": "LineString", "coordinates": way_coordinates}
            updated_features.append(feature)

    # Create updated GeoJSON
    updated_data = {"type": "FeatureCollection", "features": updated_features}

    # Write updated file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"Updated {len(updated_features)} features in {output_file}")
    if missing_nodes:
        print(f"Warning: {len(missing_nodes)} node IDs not found in " f"nodes file")

    return len(missing_nodes)


def main():
    """
    Main function to process all railway ways files using configuration.
    """
    # Print configuration and validate
    print_configuration()

    if not validate_configuration():
        return

    # Get file paths from configuration
    input_pbf = get_input_path()
    ways_files = get_railways_ways_split_paths()
    updated_files = get_railways_ways_updated_paths()

    print(f"Input PBF file: {input_pbf}")
    print(f"Ways files: {ways_files}")
    print(f"Output files: {updated_files}")
    print("=" * 60)

    # Step 1: Collect all unique node IDs from ways files
    required_node_ids = collect_all_node_ids(ways_files)

    # Step 2: Load coordinates for only the required nodes from PBF file
    node_coords = load_specific_node_coordinates(input_pbf, required_node_ids)

    # Step 3: Process each ways file
    total_missing = 0
    for i in range(len(ways_files)):
        input_file = ways_files[i]
        output_file = updated_files[i]

        try:
            missing_count = update_way_coordinates(input_file, node_coords, output_file)
            total_missing += missing_count
        except FileNotFoundError:
            print(f"Warning: {input_file} not found, skipping...")
        except Exception as e:
            print(f"Error processing {input_file}: {e}")

    print("\nProcessing complete!")
    print(f"Total missing node references: {total_missing}")
    if total_missing > 0:
        print(
            "This is normal - some ways may reference nodes outside the "
            "railways_nodes.geojson dataset"
        )


if __name__ == "__main__":
    main()
