#!/usr/bin/env python3
"""
Filter railway nodes to keep only main railway stations.
Excludes tram, subway, stops, halts, and other non-main railway infrastructure.
"""

import json
import sys
from pathlib import Path

def is_main_railway_station_only(feature):
    """
    Check if a feature represents a main railway station only.
    Excludes tram, subway, stops, halts, and other non-main railway elements.
    """
    props = feature.get('properties', {})
    
    # Get railway type
    railway_type = props.get('railway', '')
    
    # Check for tram or subway indicators
    if any(indicator in props for indicator in ['tram', 'subway', 'light_rail']):
        return False
    
    # Check if it's explicitly marked as tram or subway
    if railway_type in ['tram_stop', 'tram_level_crossing', 'tram_crossing']:
        return False
    
    # Check public transport type
    public_transport = props.get('public_transport', '')
    if public_transport in ['tram_stop', 'subway_station']:
        return False
    
    # Only keep main railway stations (exclude stops and halts)
    if railway_type == 'station':
        return True
    
    return False

def filter_railway_nodes(input_file, output_file):
    """
    Filter railway nodes to keep only main railway stations.
    """
    print(f"Reading {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Original features: {len(data['features'])}")
    
    # Filter features
    filtered_features = []
    excluded_count = 0
    
    for feature in data['features']:
        if is_main_railway_station_only(feature):
            filtered_features.append(feature)
        else:
            excluded_count += 1
    
    # Create new GeoJSON structure
    filtered_data = {
        "type": "FeatureCollection",
        "features": filtered_features
    }
    
    print(f"Filtered features: {len(filtered_features)}")
    print(f"Excluded features: {excluded_count}")
    
    # Write filtered data
    print(f"Writing filtered data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, separators=(',', ':'))
    
    print("Filtering complete!")
    
    # Print some statistics about the filtered data
    railway_types = {}
    public_transport_types = {}
    named_features = 0
    
    for feature in filtered_features:
        props = feature.get('properties', {})
        
        # Count railway types
        railway_type = props.get('railway', 'unknown')
        railway_types[railway_type] = railway_types.get(railway_type, 0) + 1
        
        # Count public transport types
        pt_type = props.get('public_transport', 'none')
        public_transport_types[pt_type] = public_transport_types.get(pt_type, 0) + 1
        
        # Count named features
        if 'name' in props:
            named_features += 1
    
    print(f"\nFiltered data statistics:")
    print(f"Railway types in filtered data:")
    for rt, count in sorted(railway_types.items()):
        print(f"  {rt}: {count}")
    
    print(f"\nPublic transport types in filtered data:")
    for pt, count in sorted(public_transport_types.items()):
        print(f"  {pt}: {count}")
    
    print(f"\nNamed features: {named_features}")

def main():
    """Main function to run the filtering script."""
    input_file = "china/railways_nodes.geojson"
    output_file = "china/railways_nodes_main_only.geojson"
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: Input file {input_file} not found!")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        filter_railway_nodes(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
