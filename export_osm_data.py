import logging
import zipfile

import geopandas as gpd
import requests
import pandas as pd

ZIP_FILE = "hamburg.zip"
GEOFABRIK_SHP_URL = "http://download.geofabrik.de/europe/germany/hamburg-latest-free.shp.zip"
TEMP_DIR = "./data/temp/"
ZIP_FILE_PATH = f"{TEMP_DIR}/{ZIP_FILE}"
EXTRACT_DIR = f"{TEMP_DIR}/hamburg"

def download_latest_osm_data_set():
    """
    Download and extract the latest OSM data (zip) from the specified `GEOFABRIK_SHP_URL`.
    """
    # Download file
    logging.info(f"Downloading 'hamburg-latest-free.shp.zip' from '{GEOFABRIK_SHP_URL}' ...")
    response = requests.get(GEOFABRIK_SHP_URL)
    response.raise_for_status()

    # write response to file
    with open(f"{TEMP_DIR}/{ZIP_FILE}", "wb") as file:
        file.write(response.content)

    logging.info(f"Done. Saved in '{ZIP_FILE_PATH}'.")
    logging.info("Extracting .zip file ...")
    # Extract zip file
    with zipfile.ZipFile(ZIP_FILE_PATH, 'r') as zip_file:
        zip_file.extractall(EXTRACT_DIR)
    logging.info(f"Done. Extracted files to '{EXTRACT_DIR}'.")
   

# Read .shp file, filter feature based on "query" and save it to geojson
def read_shp_file(name: str, query:str):
    name = name + ".shp"

    logging.info(f"Reading '{name}'.")
    shp_file_path = f"{EXTRACT_DIR}/{name}"

    # get content of shp file
    gdf = gpd.read_file(shp_file_path)

    # filter features where column "fclass" equals the query
    return gdf[gdf["fclass"] == query]

def merge_points_and_polygons(points, polygons):
    bicycle_rental_polygons_centroids = get_centroids(polygons)
    gdf = gpd.GeoDataFrame( pd.concat([points,bicycle_rental_polygons_centroids], ignore_index=True) )
    gdf.crs = points.crs
    return gdf
    
def save(feature, output):
    output = output + ".geojson"
    output_geojson_path = f"./data/generated/osm/{output}"
    feature.to_file(output_geojson_path, driver='GeoJSON') 
    
def save_v2(feature, output):
    # Add unique IDs to each entry
    feature['id'] = [output + "-" + str(i) for i in range(0, len(feature))]
    output = output + "_v2.geojson"
    output_geojson_path = f"./data/generated/osm/{output}"
    feature.to_file(output_geojson_path, driver='GeoJSON') 

def get_centroids(feature):
    centroid_geometries = []
    for idx, polygon_row in feature.iterrows():
        centroid = polygon_row['geometry'].centroid
        centroid_geometries.append(centroid)
    points_gdf = gpd.GeoDataFrame(geometry=centroid_geometries, crs=feature.crs)
    # copy content of original data
    for col in feature.columns:
        if col != 'geometry':
            points_gdf[col] = feature[col].values
    return points_gdf


def main():
    download_latest_osm_data_set()

    bicycle_parking_points = read_shp_file("gis_osm_traffic_free_1", "parking_bicycle")
    bicycle_parking_polygons = read_shp_file("gis_osm_traffic_a_free_1", "parking_bicycle")
    merged_bicycle_parking = merge_points_and_polygons(bicycle_parking_points, bicycle_parking_polygons)
    save(merged_bicycle_parking, "bicycle_parking")
    save_v2(merged_bicycle_parking, "bicycle_parking")

    bicycle_rental_points = read_shp_file("gis_osm_pois_free_1", "bicycle_rental")
    bicycle_rental_polygons = read_shp_file("gis_osm_pois_a_free_1", "bicycle_rental")
    merged_bicycle_rental = merge_points_and_polygons(bicycle_rental_points, bicycle_rental_polygons)
    save(merged_bicycle_rental, "bicycle_rental_original_osm")
    # V2 is not necessary for this dataset because we only use this in subsequent steps but not in the app

    bicycle_shop_points = read_shp_file("gis_osm_pois_free_1", "bicycle_shop")
    bicycle_shop_polygons = read_shp_file("gis_osm_pois_a_free_1", "bicycle_shop")
    merged_bicycle_shop = merge_points_and_polygons(bicycle_shop_points, bicycle_shop_polygons)
    save(merged_bicycle_shop, "bicycle_shop")
    save_v2(merged_bicycle_shop, "bicycle_shop")

    logging.info("Done.")
   

if __name__ == "__main__":
    main()