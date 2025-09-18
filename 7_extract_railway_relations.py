#!/usr/bin/env python3
"""
Extract railway relationships from OSM PBF file
Requires: pip install osmium-tool geojson

This script extracts all railway-related relations from an OSM PBF file,
including route relations, network relations, and other railway-related
organizational structures.
"""

import osmium
import geojson
import time
from collections import defaultdict
from config import (
    get_input_path,
    get_railways_relations_path,
    PROGRESS_INTERVAL,
    validate_configuration,
    print_configuration,
)


class RailwayRelationsExtractor(osmium.SimpleHandler):
    """Extract railway relations from OSM PBF file"""

    def __init__(self, progress_interval=50000):
        osmium.SimpleHandler.__init__(self)
        self.progress_interval = progress_interval

        # Progress tracking
        self.processed_count = 0
        self.railway_relations_count = 0
        self.start_time = time.time()

        # Store railway relations
        self.railway_relations = []

        print("Starting railway relations extraction...")
        print(f"Progress will be reported every {progress_interval:,} features")
        print("=" * 60)

    def _print_progress(self, feature_type=""):
        """Print processing progress"""
        elapsed = time.time() - self.start_time
        rate = self.processed_count / elapsed if elapsed > 0 else 0

        print(
            f"Processed: {self.processed_count:,} | "
            f"Railway relations: {self.railway_relations_count:,} | "
            f"Rate: {rate:.0f}/sec | "
            f"Time: {elapsed:.1f}s | "
            f"Type: {feature_type}"
        )

    def _is_railway_relation(self, tags):
        """Check if relation has railway-related tags"""
        for tag in tags:
            key = tag.k.lower()
            value = tag.v.lower()

            # Main railway relation types
            if key == "type" and value in [
                "route",
                "network",
                "multipolygon",
                "boundary",
                "site",
            ]:
                # Check if it's railway-related
                for other_tag in tags:
                    other_key = other_tag.k.lower()
                    other_value = other_tag.v.lower()

                    if (
                        (other_key == "route" and "rail" in other_value)
                        or (other_key == "railway")
                        or (other_key == "public_transport" and "rail" in other_value)
                        or ("railway" in other_key)
                        or ("railway" in other_value)
                        or ("railroad" in other_key)
                        or ("railroad" in other_value)
                    ):
                        return True

            # Direct railway tags
            if key == "railway":
                return True

            # Public transport railway
            if key == "public_transport" and "rail" in value:
                return True

            # Railway-related keywords
            if (
                "railway" in key
                or "railway" in value
                or "railroad" in key
                or "railroad" in value
                or "train" in key
                or "train" in value
            ):
                return True

        return False

    def _create_feature_properties(self, osm_id, osm_type, tags, members):
        """Create GeoJSON properties from OSM relation data"""
        properties = {
            "osm_id": osm_id,
            "osm_type": osm_type,
            "member_count": len(members),
        }

        # Add all tags as properties
        for tag in tags:
            properties[tag.k] = tag.v

        # Add member information
        member_types = defaultdict(int)
        member_roles = defaultdict(int)

        for member in members:
            member_types[member.type] += 1
            member_roles[member.role] += 1

        properties["member_types"] = dict(member_types)
        properties["member_roles"] = dict(member_roles)
        properties["member_ids"] = [int(member.ref) for member in members]

        return properties

    def relation(self, r):
        """Process OSM relations"""
        self.processed_count += 1

        if self.processed_count % self.progress_interval == 0:
            self._print_progress("relations")

        # Only process railway relations
        if len(r.tags) > 0 and self._is_railway_relation(r.tags):
            self.railway_relations_count += 1

            properties = self._create_feature_properties(
                r.id, "relation", r.tags, r.members
            )

            # Create a placeholder point geometry since GeoJSON requires geometry
            # The real data is in the properties
            feature = geojson.Feature(
                geometry=geojson.Point([0, 0]),  # Placeholder geometry
                properties=properties,
            )

            self.railway_relations.append(feature)

            # Show first few relations
            if self.railway_relations_count <= 3:
                relation_type = properties.get("type", "unknown")
                route_type = properties.get("route", "unknown")
                print(
                    f"    ✓ Relation {r.id}: {relation_type}, "
                    f"route={route_type}, {len(r.members)} members"
                )


def extract_railway_relations(input_pbf, output_geojson, progress_interval=50000):
    """
    Extract railway relations from OSM PBF file

    Args:
        input_pbf: Path to input .osm.pbf file
        output_geojson: Path to output .geojson file
        progress_interval: How often to print progress
    """
    print(f"Extracting railway relations from {input_pbf}")
    print(f"Output will be saved to: {output_geojson}")
    print("-" * 60)

    try:
        # Create extractor and process file
        extractor = RailwayRelationsExtractor(progress_interval)
        extractor.apply_file(input_pbf)

        # Print final statistics
        elapsed = time.time() - extractor.start_time
        total_features = len(extractor.railway_relations)

        print("\n" + "=" * 60)
        print("EXTRACTION COMPLETE!")
        print("=" * 60)
        print(f"Processing time: {elapsed:.1f} seconds")
        print(f"Total features processed: {extractor.processed_count:,}")
        print(f"Railway relations found: {extractor.railway_relations_count:,}")
        print(f"Railway relations saved: {total_features:,}")
        print(
            f"Processing rate: " f"{extractor.processed_count/elapsed:.0f} features/sec"
        )

        if total_features > 0:
            # Create GeoJSON FeatureCollection
            print("\nCreating GeoJSON FeatureCollection...")
            feature_collection = geojson.FeatureCollection(extractor.railway_relations)

            # Write to file
            print(f"Writing to {output_geojson}...")
            with open(output_geojson, "w", encoding="utf-8") as f:
                geojson.dump(feature_collection, f, indent=2, ensure_ascii=False)

            print(
                f"✅ Successfully saved {total_features:,} railway relations "
                f"to {output_geojson}"
            )

            # Show sample of what was found
            print("\nSample relation types found:")
            relation_types = defaultdict(int)
            route_types = defaultdict(int)
            railway_types = defaultdict(int)

            for feature in extractor.railway_relations[:1000]:
                props = feature["properties"]

                relation_type = props.get("type", "other")
                relation_types[relation_type] += 1

                route_type = props.get("route", "other")
                route_types[route_type] += 1

                railway_type = props.get("railway", "other")
                railway_types[railway_type] += 1

            print("  Relation Types:")
            for rel_type, count in sorted(
                relation_types.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"    {rel_type}: {count:,}")

            print("  Route Types:")
            for route_type, count in sorted(
                route_types.items(), key=lambda x: x[1], reverse=True
            )[:10]:
                print(f"    {route_type}: {count:,}")

            print("  Railway Types:")
            for rail_type, count in sorted(
                railway_types.items(), key=lambda x: x[1], reverse=True
            )[:10]:
                print(f"    {rail_type}: {count:,}")

            # Show structure of first feature
            if extractor.railway_relations:
                print("\nSample relation structure:")
                sample = extractor.railway_relations[0]["properties"]
                print(f"  OSM ID: {sample['osm_id']}")
                print(f"  Type: {sample.get('type', 'N/A')}")
                print(f"  Route: {sample.get('route', 'N/A')}")
                print(f"  Member count: {sample['member_count']}")
                print(f"  Member types: {sample['member_types']}")
                print(f"  Member roles: {sample['member_roles']}")
                print(f"  First few member IDs: {sample['member_ids'][:5]}")

        else:
            print("⚠️  No railway relations found in the input file!")

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
    output_path = get_railways_relations_path()

    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")
    print(f"Progress interval: {PROGRESS_INTERVAL:,} features")
    print("=" * 60)

    try:
        extractor = extract_railway_relations(
            input_path, output_path, PROGRESS_INTERVAL
        )

        if extractor and extractor.railway_relations:
            print("\n🚂 Railway relations extraction completed successfully!")
            print(f"   Output: {output_path}")
            print("   Contains: Relation IDs, tags, member information")
            print("   Note: No coordinates included - geometry is placeholder")

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

    parser = argparse.ArgumentParser(description="Extract OSM railway relations")
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

    extract_railway_relations(args.input, args.output, args.progress)


# =============================================================================
# FOR DEBUGGING: Run this directly in your IDE or debugging terminal
# =============================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        main()  # Use command line interface
    else:
        debug_run()  # Use debugging configuration
