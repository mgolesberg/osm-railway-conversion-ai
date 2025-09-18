#!/usr/bin/env python3
"""
Combine railway polylines for each railway relationship

This script reads railway relations and railway ways, then combines all polylines
belonging to each railway relationship into a single polyline.

Input files:
- china/railways_relations.geojson: Contains railway relationships with member_ids
- china/railways_guangzhou.geojson: Contains railway ways (LineString geometries)

Output:
- china/railways_combined_polylines.geojson: Combined polylines for each relationship
"""

import geojson
import json
from collections import defaultdict
from shapely.geometry import LineString, MultiLineString
from shapely.ops import linemerge
import time


def load_geojson_file(filepath):
    """Load a GeoJSON file and return the feature collection"""
    print(f"Loading {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        data = geojson.load(f)
    print(f"Loaded {len(data['features'])} features")
    return data


def create_way_lookup(ways_data):
    """Create a lookup dictionary from OSM ID to way geometry and properties"""
    print("Creating way lookup dictionary...")
    way_lookup = {}

    for feature in ways_data["features"]:
        osm_id = feature["properties"]["osm_id"]
        geometry = feature["geometry"]
        properties = feature["properties"]

        way_lookup[osm_id] = {"geometry": geometry, "properties": properties}

    print(f"Created lookup for {len(way_lookup)} ways")
    return way_lookup


def combine_polylines_for_relation(relation, way_lookup):
    """
    Combine all polylines belonging to a railway relation into a single polyline

    Args:
        relation: GeoJSON feature representing a railway relation
        way_lookup: Dictionary mapping OSM ID to way data

    Returns:
        Combined geometry (MultiLineString or LineString) or None if no ways found
    """
    member_ids = relation["properties"].get("member_ids", [])

    if not member_ids:
        return None

    # Collect all LineString geometries for this relation
    line_strings = []

    for member_id in member_ids:
        if member_id in way_lookup:
            way_data = way_lookup[member_id]
            geometry = way_data["geometry"]

            # Only process LineString geometries
            if geometry["type"] == "LineString":
                coords = geometry["coordinates"]
                if len(coords) >= 2:  # Valid LineString needs at least 2 points
                    line_strings.append(LineString(coords))

    if not line_strings:
        return None

    # Try to merge connected LineStrings
    try:
        merged = linemerge(line_strings)

        # Convert back to GeoJSON geometry
        if merged.geom_type == "LineString":
            return geojson.LineString(list(merged.coords))
        elif merged.geom_type == "MultiLineString":
            return geojson.MultiLineString([list(line.coords) for line in merged.geoms])
        else:
            # Fallback: return as MultiLineString
            return geojson.MultiLineString([list(line.coords) for line in line_strings])

    except Exception as e:
        print(
            f"Warning: Could not merge lines for relation {relation['properties']['osm_id']}: {e}"
        )
        # Fallback: return as MultiLineString
        return geojson.MultiLineString([list(line.coords) for line in line_strings])


def process_railway_relations(relations_data, way_lookup):
    """
    Process all railway relations and combine their polylines

    Args:
        relations_data: GeoJSON FeatureCollection of railway relations
        way_lookup: Dictionary mapping OSM ID to way data

    Returns:
        Tuple of (combined_features, used_way_ids)
    """
    print("Processing railway relations...")
    combined_features = []
    used_way_ids = set()
    processed_count = 0
    successful_count = 0

    for relation in relations_data["features"]:
        processed_count += 1

        if processed_count % 100 == 0:
            print(
                f"Processed {processed_count}/{len(relations_data['features'])} relations"
            )

        # Combine polylines for this relation
        combined_geometry = combine_polylines_for_relation(relation, way_lookup)

        if combined_geometry is not None:
            # Track which ways were used in this relation
            member_ids = relation["properties"].get("member_ids", [])
            for member_id in member_ids:
                if member_id in way_lookup:
                    used_way_ids.add(member_id)

            # Create new feature with combined geometry
            new_properties = relation["properties"].copy()
            new_properties["combined_way_count"] = len(member_ids)
            new_properties["geometry_type"] = combined_geometry["type"]
            new_properties["source"] = "relation"

            combined_feature = geojson.Feature(
                geometry=combined_geometry, properties=new_properties
            )

            combined_features.append(combined_feature)
            successful_count += 1

    print(
        f"Successfully combined polylines for {successful_count}/{processed_count} relations"
    )
    print(f"Used {len(used_way_ids)} ways in relations")
    return combined_features, used_way_ids


def process_standalone_ways(way_lookup, used_way_ids):
    """
    Process railway ways that are not part of any relation

    Args:
        way_lookup: Dictionary mapping OSM ID to way data
        used_way_ids: Set of way IDs that are already used in relations

    Returns:
        List of GeoJSON features for standalone ways
    """
    print("Processing standalone railway ways...")
    standalone_features = []

    for osm_id, way_data in way_lookup.items():
        if osm_id not in used_way_ids:
            geometry = way_data["geometry"]
            properties = way_data["properties"].copy()

            # Only process LineString geometries
            if geometry["type"] == "LineString":
                coords = geometry["coordinates"]
                if len(coords) >= 2:  # Valid LineString needs at least 2 points
                    # Add metadata to indicate this is a standalone way
                    properties["source"] = "standalone_way"
                    properties["geometry_type"] = "LineString"
                    properties["combined_way_count"] = 1

                    standalone_feature = geojson.Feature(
                        geometry=geometry, properties=properties
                    )

                    standalone_features.append(standalone_feature)

    print(f"Found {len(standalone_features)} standalone railway ways")
    return standalone_features


def main():
    """Main function to combine railway polylines"""
    print("=" * 60)
    print("RAILWAY POLYLINE COMBINER")
    print("=" * 60)

    start_time = time.time()

    # Load input files
    relations_file = "china/railways_relations.geojson"
    ways_file = "china/railways_ways_downsampled_simple.geojson"
    output_file = "china/railways_combined_polylines.geojson"

    try:
        # Load railway relations
        relations_data = load_geojson_file(relations_file)

        # Load railway ways
        ways_data = load_geojson_file(ways_file)

        # Create way lookup
        way_lookup = create_way_lookup(ways_data)

        # Process relations and combine polylines
        combined_features, used_way_ids = process_railway_relations(
            relations_data, way_lookup
        )

        # Process standalone railway ways
        standalone_features = process_standalone_ways(way_lookup, used_way_ids)

        # Combine all features
        all_features = combined_features + standalone_features

        # Create output GeoJSON
        output_collection = geojson.FeatureCollection(all_features)

        # Write to file
        print(f"\nWriting combined polylines to {output_file}...")
        with open(output_file, "w", encoding="utf-8") as f:
            geojson.dump(output_collection, f, ensure_ascii=False)

        # Print summary
        elapsed_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("COMBINATION COMPLETE!")
        print("=" * 60)
        print(f"Processing time: {elapsed_time:.1f} seconds")
        print(f"Input relations: {len(relations_data['features'])}")
        print(f"Input ways: {len(ways_data['features'])}")
        print(f"Combined relation polylines: {len(combined_features)}")
        print(f"Standalone railway ways: {len(standalone_features)}")
        print(f"Total output features: {len(all_features)}")
        print(f"Output file: {output_file}")

        # Show sample of results
        if all_features:
            print("\nSample features:")

            # Show sample combined polyline
            if combined_features:
                print("\nSample combined polyline (from relation):")
                sample = combined_features[0]
                props = sample["properties"]
                geom = sample["geometry"]

                print(f"  Relation ID: {props['osm_id']}")
                print(f"  Name: {props.get('name', 'N/A')}")
                print(f"  Source: {props['source']}")
                print(f"  Geometry type: {geom['type']}")
                print(f"  Combined ways: {props['combined_way_count']}")

                if geom["type"] == "LineString":
                    print(f"  Coordinate count: {len(geom['coordinates'])}")
                elif geom["type"] == "MultiLineString":
                    print(f"  Line count: {len(geom['coordinates'])}")
                    total_coords = sum(len(line) for line in geom["coordinates"])
                    print(f"  Total coordinates: {total_coords}")

            # Show sample standalone way
            if standalone_features:
                print("\nSample standalone railway way:")
                sample = standalone_features[0]
                props = sample["properties"]
                geom = sample["geometry"]

                print(f"  Way ID: {props['osm_id']}")
                print(f"  Name: {props.get('name', 'N/A')}")
                print(f"  Source: {props['source']}")
                print(f"  Geometry type: {geom['type']}")
                print(f"  Coordinate count: {len(geom['coordinates'])}")

    except FileNotFoundError as e:
        print(f"ERROR: File not found: {e}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
