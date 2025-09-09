#!/usr/bin/env python3
"""
Convert OSM PBF to GeoJSON - Railway features only, with progress tracking
Requires: pip install osmium-tool geojson
"""

import osmium
import geojson
import json
import time
from collections import defaultdict
from config import (
    get_input_path,
    get_railways_ways_path,
    PROGRESS_INTERVAL,
    validate_configuration,
    print_configuration,
)


class SimpleRailwayExtractor(osmium.SimpleHandler):
    """Extract railway ways without coordinates - just IDs and tags"""

    def __init__(self, progress_interval=50000):
        osmium.SimpleHandler.__init__(self)
        self.progress_interval = progress_interval

        # Progress tracking
        self.processed_count = 0
        self.railway_ways_count = 0
        self.start_time = time.time()

        # Store railway way data
        self.railway_ways = []

        print("Starting simple railway ways extraction...")
        print("(No coordinates - just way IDs, tags, and node lists)")
        print(f"Progress will be reported every {progress_interval:,} features")
        print("=" * 60)

    def _print_progress(self, feature_type=""):
        """Print processing progress"""
        elapsed = time.time() - self.start_time
        rate = self.processed_count / elapsed if elapsed > 0 else 0

        print(
            f"Processed: {self.processed_count:,} | "
            f"Railway ways: {self.railway_ways_count:,} | "
            f"Rate: {rate:.0f}/sec | "
            f"Time: {elapsed:.1f}s | "
            f"Type: {feature_type}"
        )

    def _is_railway(self, tags):
        """Check if feature has railway-related tags"""
        for tag in tags:
            key = tag.k.lower()
            value = tag.v.lower()

            # Main railway tags
            if key == "railway":
                return True

            # Public transport stations
            if key == "public_transport" and "station" in value:
                return True

            # Additional railway-related tags
            if (
                "railway" in key
                or "railway" in value
                or "railroad" in key
                or "railroad" in value
                or key == "train"
                or value == "train"
            ):
                return True

        return False

    # def node(self, n):
    #     """Skip all nodes - we don't need them"""
    #     self.processed_count += 1

    #     if self.processed_count % self.progress_interval == 0:
    #         self._print_progress("nodes")

    def way(self, w):
        """Extract railway ways with tags and node IDs only"""
        self.processed_count += 1

        if self.processed_count % self.progress_interval == 0:
            self._print_progress("ways")

        # Only process railway ways
        if len(w.tags) > 0 and self._is_railway(w.tags):
            self.railway_ways_count += 1

            # Create simple feature with no geometry - just properties
            properties = {
                "osm_id": w.id,
                "osm_type": "way",
                "node_count": len(w.nodes),
                "node_ids": [
                    int(node.ref) for node in w.nodes
                ],  # Convert NodeRef to int
            }

            # Add all OSM tags
            for tag in w.tags:
                properties[tag.k] = tag.v

            # Create a "fake" point geometry at (0,0) since GeoJSON requires geometry
            # You can ignore the coordinates - the real data is in the properties
            feature = geojson.Feature(
                geometry=geojson.Point([0, 0]),  # Placeholder geometry
                properties=properties,
            )

            self.railway_ways.append(feature)

            # Show first few ways
            if self.railway_ways_count <= 3:
                railway_type = properties.get("railway", "unknown")
                print(f"    ✓ Way {w.id}: {railway_type}, {len(w.nodes)} nodes")

    def relation(self, r):
        """Skip relations"""
        self.processed_count += 1

        if self.processed_count % self.progress_interval == 0:
            self._print_progress("relations")


def extract_railway_ways(input_pbf, output_geojson, progress_interval=50000):
    """
    Extract railway ways from OSM PBF - no coordinates, just way data

    Args:
        input_pbf: Path to input .osm.pbf file
        output_geojson: Path to output .geojson file
        progress_interval: How often to print progress
    """
    print(f"Extracting railway ways from {input_pbf}")
    print(f"Output will be saved to: {output_geojson}")
    print("-" * 60)

    try:
        # Create extractor and process file
        extractor = SimpleRailwayExtractor(progress_interval)
        extractor.apply_file(input_pbf)

        # Print final statistics
        elapsed = time.time() - extractor.start_time
        total_features = len(extractor.railway_ways)

        print("\n" + "=" * 60)
        print("EXTRACTION COMPLETE!")
        print("=" * 60)
        print(f"Processing time: {elapsed:.1f} seconds")
        print(f"Total features processed: {extractor.processed_count:,}")
        print(f"Railway ways found: {extractor.railway_ways_count:,}")
        print(f"Railway ways saved: {total_features:,}")
        print(f"Processing rate: {extractor.processed_count/elapsed:.0f} features/sec")

        if total_features > 0:
            # Create GeoJSON FeatureCollection
            print(f"\nCreating GeoJSON FeatureCollection...")
            feature_collection = geojson.FeatureCollection(extractor.railway_ways)

            # Write to file
            print(f"Writing to {output_geojson}...")
            with open(output_geojson, "w", encoding="utf-8") as f:
                geojson.dump(feature_collection, f, indent=2, ensure_ascii=False)

            print(
                f"✅ Successfully saved {total_features:,} railway ways to {output_geojson}"
            )

            # Show sample of what was found
            print(f"\nSample railway types found:")
            railway_types = defaultdict(int)

            for feature in extractor.railway_ways[:1000]:  # Sample first 1000
                railway_value = feature["properties"].get("railway", "other")
                railway_types[railway_value] += 1

            for rail_type, count in sorted(
                railway_types.items(), key=lambda x: x[1], reverse=True
            )[:15]:
                print(f"  {rail_type}: {count:,}")

            # Show structure of first feature
            if extractor.railway_ways:
                print(f"\nSample feature structure:")
                sample = extractor.railway_ways[0]["properties"]
                print(f"  OSM ID: {sample['osm_id']}")
                print(f"  Railway type: {sample.get('railway', 'N/A')}")
                print(f"  Node count: {sample['node_count']}")
                print(f"  First few node IDs: {sample['node_ids'][:5]}")
                print(f"  All tags: {list(sample.keys())}")

        else:
            print("⚠️  No railway ways found in the input file!")

        return extractor

    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_pbf}")
        return None
    except Exception as e:
        print(f"ERROR during extraction: {e}")
        import traceback

        traceback.print_exc()
        return None


def debug_run():
    """
    Run extraction with the configured variables from config.py
    """
    # Print configuration and validate
    print_configuration()

    if not validate_configuration():
        return

    input_path = get_input_path()
    output_path = get_railways_ways_path()

    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Progress interval: {PROGRESS_INTERVAL:,} features")
    print("=" * 60)

    try:
        extractor = extract_railway_ways(input_path, output_path, PROGRESS_INTERVAL)

        if extractor and extractor.railway_ways:
            print(f"\n🚂 Railway extraction completed successfully!")
            print(f"   Output: {output_path}")
            print(f"   Contains: Way IDs, tags, and node ID lists")
            print(f"   Note: No coordinates included - geometry is placeholder")

    except FileNotFoundError:
        print(f"ERROR: File not found: {input_path}")
        print("Please update the INPUT_PBF_FILENAME variable in config.py")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Command line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract OSM railway ways (no coordinates)"
    )
    parser.add_argument("input", help="Input .osm.pbf file")
    parser.add_argument("output", help="Output .geojson file")
    parser.add_argument(
        "--progress",
        "-p",
        type=int,
        default=50000,
        help="Progress interval (default: 50000)",
    )

    args = parser.parse_args()

    extract_railway_ways(args.input, args.output, args.progress)


# =============================================================================
# FOR DEBUGGING: Run this directly in your IDE or debugging terminal
# =============================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        main()  # Use command line interface
    else:
        debug_run()  # Use debugging configuration
