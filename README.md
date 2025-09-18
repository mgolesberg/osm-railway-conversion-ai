# Railroad Extraction from OpenStreetMaps

## Experimenting with AI

This was my experiment using generative AI to understand and process a large amount of data in a format I had never used before.
Specifically, this was my first time using the .pbf file type from [OpenStreetMap](https://www.openstreetmap.org/) (OSM).
I worked with a chatbot to understand how the data was structured and write code to extract, transform, and load the data.

### Code Provenance

All of the modules in this project were written by Claude Sonnet 4 or Cursor's Agent. The only changes I made are formatting the files with Black.
I directed the AI with all the features I needed. It took several iterations.

### Time Savings

It took me 4 hours from downloading the files to having processed several hundred megabytes of useful data from over a gigabyte of downloaded data. I do not have a comparison for working with a similar dataset without AI, but I was pleased with the workflow as a way to experiment with new data types.

## Problem Definition

Given a large package of OpenStreetMap data, such as an entire country from

[Geofabrik Downloads](https://download.geofabrik.de/)

extract all railways data and process it into a GeoJSON format. I focused on vector data of points (called Nodes by OSM) and polylines (called Ways by OSM).

## Results

1.3 GB of raw Chinese OSM data became 100 MB of railway points data (Nodes) and 263 MB of railway polyline data (Ways).

859 MB of raw Czech Republic data became 29 MB of railway points data and 71 MB of railway polyline data.

**Downsampling Achievement**: The Chinese railway polyline data was successfully downsampled from 263 MB to 3.87 MB (98.5% reduction) while preserving essential railway network information through usage filtering, Douglas-Peucker algorithm simplification, and field optimization.

I am not including the raw data here nor the Chinese Railways Nodes file because they are too large for GitHub.

## Visualizations

![Czech Republic Railway Network](czech-railways-ways.png "Output of extracting the Czech railways lines/ways")

![Czech Republic Railway Parts](czech-railways-6-parts.png "Czech Railway lines/ways plotted on a map with the 6 part split")

## Module Overview (AI wrote the rest of this README about how to use the files)

This project consists of 11 sequential modules designed to extract, process, and optimize railway data from OpenStreetMap PBF files. The modules are intentionally separated to provide checkpoints for computers with lower processing power or when working with particularly large datasets. Each module can be run independently after its prerequisites are met.

The workflow is divided into two main phases:

- **Basic Extraction (Modules 1-5)**: Core railway data extraction and coordinate assignment
- **Advanced Processing (Modules 6-11)**: Downsampling, optimization, and field filtering for production-ready datasets

### Module 1: `1_osm_converter_nodes.py`

**Purpose**: Extracts railway nodes (points) from OSM PBF files and converts them to GeoJSON format.

**What it does**:

- Parses the entire OSM PBF file to identify railway-related nodes
- Identifies nodes with railway tags (railway=\*, public_transport=station, etc.)
- Caches all node coordinates for use in later modules
- Outputs `railways_nodes.geojson` containing railway point features

**Input**: OSM PBF file (e.g., `country.osm.pbf`)
**Output**: `railways_nodes.geojson`

### Module 2: `2_osm_converter_ways_without_coordinates.py`

**Purpose**: Extracts railway ways (lines/paths) from OSM PBF files without coordinates, storing only way IDs, tags, and node references.

**What it does**:

- Processes railway ways from the OSM PBF file
- Extracts way properties and node ID lists (but not coordinates)
- Creates placeholder geometry at (0,0) since GeoJSON requires geometry
- Outputs `railways_ways.geojson` with way data and node references

**Input**: OSM PBF file (e.g., `country.osm.pbf`)
**Output**: `railways_ways.geojson`

### Module 3: `3_split.py`

**Purpose**: Splits large railway ways files into smaller, manageable chunks for processing.

**What it does**:

- Takes the large `railways_ways.geojson` file
- Divides it into 6 smaller files (`railways_ways_1.geojson` through `railways_ways_6.geojson`)
- Enables parallel processing and reduces memory requirements

**Input**: `railways_ways.geojson`
**Output**: `railways_ways_1.geojson`, `railways_ways_2.geojson`, ..., `railways_ways_6.geojson`

### Module 4: `4_assign_coordinates_to_ways.py`

**Purpose**: Assigns real coordinates to railway ways by looking up node coordinates from the original PBF file.

**What it does**:

- Collects all unique node IDs from the split ways files
- Extracts coordinates for these specific nodes from the original PBF file
- Updates each way's geometry with actual LineString or Point coordinates
- Outputs updated files (`railways_ways_1_updated.geojson`, etc.)

**Input**: Split ways files + original OSM PBF file
**Output**: `railways_ways_1_updated.geojson`, `railways_ways_2_updated.geojson`, etc.

### Module 5: `5_segment_missing_coordinates.py` _(Optional)_

**Purpose**: Identifies and separates ways that still have missing or invalid coordinates after step 4.

**What it does**:

- Analyzes all updated ways files for features with missing coordinates
- Creates a separate file (`railways_ways_missing_coordinates.geojson`) containing problematic features
- Creates clean files (`railways_ways_valid_1.geojson`, etc.) with only valid coordinates
- **Note**: This module is only necessary if there are missing nodes after step 4

**Input**: Updated ways files from step 4
**Output**:

- `railways_ways_missing_coordinates.geojson` (problematic features)
- `railways_ways_valid_1.geojson`, `railways_ways_valid_2.geojson`, etc. (clean data)

### Module 6: `6_downsample_usage.py`

**Purpose**: Simple downsample script that combines railway ways files and filters by usage type.

**What it does**:

- Combines all `railways_ways_*_updated.geojson` files into a single dataset
- Filters railways to keep only main, branch, military, and freight usage types
- Removes crossover and connector service types
- Preserves all properties while reducing dataset size significantly

**Input**: `railways_ways_1_updated.geojson` through `railways_ways_6_updated.geojson`
**Output**: `railways_ways_downsampled_simple.geojson`

### Module 7: `7_extract_railway_relations.py`

**Purpose**: Extracts railway relationships from OSM PBF files.

**What it does**:

- Processes OSM relations to find railway-related organizational structures
- Identifies route relations, network relations, and other railway groupings
- Extracts member information and relationship metadata
- Creates placeholder geometry since relations don't have direct coordinates

**Input**: OSM PBF file (e.g., `country.osm.pbf`)
**Output**: `railways_relations.geojson`

### Module 8: `8_combine_railway_polylines.py`

**Purpose**: Combines railway polylines for each railway relationship into single polylines.

**What it does**:

- Reads railway relations and their member way IDs
- Combines all polylines belonging to each relation using line merging
- Processes standalone railway ways not part of any relation
- Creates comprehensive railway network with both relation-based and standalone polylines

**Input**: `railways_relations.geojson` + `railways_ways_downsampled_simple.geojson`
**Output**: `railways_combined_polylines.geojson`

### Module 9: `9_flatten_geojson.py`

**Purpose**: Flattens GeoJSON files by removing unnecessary whitespace for size optimization.

**What it does**:

- Removes indentation and extra whitespace from GeoJSON files
- Significantly reduces file size while preserving JSON structure
- Useful for final output optimization before distribution

**Input**: Any GeoJSON file
**Output**: Flattened version of the same file

### Module 10: `10_douglas_peucker_downsample.py`

**Purpose**: Applies Douglas-Peucker algorithm to reduce coordinate density while preserving railway line shapes.

**What it does**:

- Uses Shapely's simplify method with configurable tolerance (500m default)
- Transforms coordinates to UTM projection for accurate distance calculations
- Preserves topology while reducing coordinate count
- Maintains essential railway line geometry with fewer points

**Input**: `railways_combined_polylines.geojson`
**Output**: `railways_ways_downsampled_simple_algorithm.geojson`

### Module 11: `11_downsample_fields.py`

**Purpose**: Advanced field filtering and coordinate precision optimization.

**What it does**:

- Analyzes field coverage and removes fields with less than 20% coverage
- Filters name fields to keep only English and Chinese variants
- Rounds coordinates to 4 decimal places for size optimization
- Removes technical fields like OSM IDs, gauge, voltage, etc.

**Input**: `railways_ways_downsampled_simple_algorithm.geojson`
**Output**: `railways_ways_downsampled_advanced.geojson`

### Optional Module: `prettify.py`

**Purpose**: Formats GeoJSON files with proper indentation for human readability.

**What it does**:

- Adds whitespace and indentation to GeoJSON files
- Makes files easier to read and debug
- **Warning**: Significantly increases file size and memory usage due to added whitespace
- **Note**: This module is not necessary for data processing and should only be used for debugging or final presentation

**Input**: Any GeoJSON file
**Output**: Prettified version of the same file

## Usage Workflow

### Basic Railway Extraction (Modules 1-5)

0. **Gather Raw Data**: Download the raw data and set `config.py`
1. **Run Module 1**: Extract railway nodes
2. **Run Module 2**: Extract railway ways (without coordinates)
3. **Run Module 3**: Split ways file into manageable chunks
4. **Run Module 4**: Assign coordinates to ways
5. **Run Module 5**: _(Only if needed)_ Clean up missing coordinates

### Advanced Processing and Downsampling (Modules 6-11)

6. **Run Module 6**: Simple usage-based downsample
7. **Run Module 7**: Extract railway relations
8. **Run Module 8**: Combine railway polylines
9. **Run Module 9**: _(Optional)_ Flatten GeoJSON for size optimization
10. **Run Module 10**: Douglas-Peucker algorithm downsample
11. **Run Module 11**: Advanced field filtering and precision optimization

### Optional Utilities

12. **Run prettify.py**: _(Optional)_ Format files for readability at the cost of increased file size

## Configuration

All modules use `config.py` for file paths and settings. Update the configuration file to specify your input PBF file and output directory before running any modules.
