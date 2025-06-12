import geopandas as gpd
import pandas as pd

def generate_regions_geojson(dept_geojson_path, mapping_csv_path, output_path):
    """
    Generate a GeoJSON file with region geometries by merging departments based on a mapping table.

    Parameters:
    - dept_geojson_path (str): Path to the input GeoJSON file containing department geometries.
    - mapping_csv_path (str): Path to the CSV file mapping department codes to region names.
    - output_path (str): Path where the resulting regions GeoJSON will be saved.

    Returns:
    - str: Path to the saved GeoJSON file containing regions.
    """
    # Read GeoJSON departments
    depts = gpd.read_file(dept_geojson_path)

    # Convert dept code to string with leading zeros (e.g., '01', '02', etc.)
    depts['code'] = depts['code'].astype(str).str.zfill(2)

    # Read mapping table 
    mapping = pd.read_csv(mapping_csv_path)
    mapping['num_dep'] = mapping['num_dep'].astype(str).str.zfill(2)

    # Merge data to add region name
    depts = depts.merge(mapping, left_on="code", right_on="num_dep")

    # Dissolve departments by region name
    regions = depts.dissolve(by="region_name", as_index=False)

    # Save to GeoJSON
    regions.to_file(output_path, driver="GeoJSON")

    return output_path

def get_region_shapes(geojson_path):
    """
    Load region shapes from a GeoJSON file.

    Parameters:
    - geojson_path (str): Path to the GeoJSON file containing region geometries.

    Returns:
    - dict: A dictionary mapping region names to their corresponding Shapely geometries.
    """
    gdf = gpd.read_file(geojson_path)
    shapes = {row['region_name']: row['geometry'] for _, row in gdf.iterrows()}
    return shapes
