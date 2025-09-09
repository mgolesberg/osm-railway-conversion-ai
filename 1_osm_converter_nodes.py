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
    get_railways_nodes_path,
    PROGRESS_INTERVAL,
    validate_configuration,
    print_configuration,
)


class RailwayConverter(osmium.SimpleHandler):
    """Convert OSM railway features to GeoJSON with progress tracking"""

    def __init__(self, progress_interval=50000):
        osmium.SimpleHandler.__init__(self)
        self.progress_interval = progress_interval

        # Progress tracking
        self.processed_count = 0
        self.railway_nodes_count = 0
        self.railway_ways_count = 0
        self.start_time = time.time()

        # Store railway features
        self.railway_features = []
        self.node_cache = {}  # Cache node locations for way processing

        print("Starting railway conversion...")
        print(f"Progress will be reported every {progress_interval:,} features")
        print("=" * 60)

    def _print_progress(self, feature_type=""):
        """Print processing progress"""
        elapsed = time.time() - self.start_time
        rate = self.processed_count / elapsed if elapsed > 0 else 0

        print(
            f"Processed: {self.processed_count:,} | "
            f"Railway nodes: {self.railway_nodes_count:,} | "
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

    def _create_feature_properties(self, osm_id, osm_type, tags):
        """Create GeoJSON properties from OSM tags"""
        properties = {"osm_id": osm_id, "osm_type": osm_type}

        # Add all tags as properties
        for tag in tags:
            properties[tag.k] = tag.v

        return properties

    def node(self, n):
        """Process OSM nodes"""
        self.processed_count += 1

        if self.processed_count % self.progress_interval == 0:
            self._print_progress("nodes")

        # Always cache node location for way processing
        if n.location.valid():
            self.node_cache[n.id] = [n.location.lon, n.location.lat]

        # Only create features for railway nodes with tags
        if len(n.tags) > 0 and self._is_railway(n.tags) and n.location.valid():
            self.railway_nodes_count += 1

            properties = self._create_feature_properties(n.id, "node", n.tags)

            feature = geojson.Feature(
                geometry=geojson.Point([n.location.lon, n.location.lat]),
                properties=properties,
            )

            self.railway_features.append(feature)


def convert_railways_to_geojson(input_pbf, output_geojson, progress_interval=50000):
    """
    Convert railway features from OSM PBF to GeoJSON

    Args:
        input_pbf: Path to input .osm.pbf file
        output_geojson: Path to output .geojson file
        progress_interval: How often to print progress
    """
    print(f"Converting railway features from {input_pbf}")
    print(f"Output will be saved to: {output_geojson}")
    print("-" * 60)

    try:
        # Create converter and process file
        converter = RailwayConverter(progress_interval)
        converter.apply_file(input_pbf)

        # Print final statistics
        elapsed = time.time() - converter.start_time
        total_railway_features = len(converter.railway_features)

        print("\n" + "=" * 60)
        print("CONVERSION COMPLETE!")
        print("=" * 60)
        print(f"Processing time: {elapsed:.1f} seconds")
        print(f"Total features processed: {converter.processed_count:,}")
        print(f"Railway nodes found: {converter.railway_nodes_count:,}")
        print(f"Railway ways found: {converter.railway_ways_count:,}")
        print(f"Total railway features in GeoJSON: {total_railway_features:,}")
        print(f"Processing rate: {converter.processed_count/elapsed:.0f} features/sec")
        print(f"Cached nodes: {len(converter.node_cache):,}")

        if total_railway_features > 0:
            # Create GeoJSON FeatureCollection
            print(f"\nCreating GeoJSON FeatureCollection...")
            feature_collection = geojson.FeatureCollection(converter.railway_features)

            # Write to file
            print(f"Writing to {output_geojson}...")
            with open(output_geojson, "w", encoding="utf-8") as f:
                geojson.dump(feature_collection, f, indent=2, ensure_ascii=False)

            print(
                f"✓ Successfully saved {total_railway_features:,} railway features to {output_geojson}"
            )

            # Show sample of what was found
            print(f"\nSample of railway feature types found:")
            feature_types = defaultdict(int)
            railway_types = defaultdict(int)

            for feature in converter.railway_features[:1000]:  # Sample first 1000
                osm_type = feature["properties"].get("osm_type", "unknown")
                feature_types[osm_type] += 1

                railway_value = feature["properties"].get("railway", "other")
                railway_types[railway_value] += 1

            print("  OSM Types:")
            for osm_type, count in sorted(feature_types.items()):
                print(f"    {osm_type}: {count:,}")

            print("  Railway Types (sample):")
            for rail_type, count in sorted(
                railway_types.items(), key=lambda x: x[1], reverse=True
            )[:10]:
                print(f"    {rail_type}: {count:,}")

        else:
            print("⚠️  No railway features found in the input file!")
            print("   The file might not contain railway data.")

        return converter

    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_pbf}")
        return None
    except Exception as e:
        print(f"ERROR during conversion: {e}")
        import traceback

        traceback.print_exc()
        return None


def debug_run():
    """
    Run conversion with the configured variables from config.py
    """
    # Print configuration and validate
    print_configuration()

    if not validate_configuration():
        return

    input_path = get_input_path()
    output_path = get_railways_nodes_path()

    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Progress interval: {PROGRESS_INTERVAL:,} features")
    print("=" * 60)

    try:
        converter = convert_railways_to_geojson(
            input_path, output_path, PROGRESS_INTERVAL
        )

        if converter:
            print(f"\n🚂 Railway conversion completed successfully!")
            print(f"   Output: {output_path}")

    except FileNotFoundError:
        print(f"ERROR: File not found: {input_path}")
        print("Please update the INPUT_PBF_FILENAME variable in config.py")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_run()  # Use debugging configuration
