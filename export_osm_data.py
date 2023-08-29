import logging
import zipfile

import geopandas as gpd
import requests

ZIP_FILE = "hamburg.zip"
GEOFABRIK_SHP_URL = "http://download.geofabrik.de/europe/germany/hamburg-latest-free.shp.zip"
TEMP_DIR = "./data/temp/"
ZIP_FILE_PATH = f"{TEMP_DIR}/{ZIP_FILE}"
EXTRACT_DIR = f"{TEMP_DIR}/hamburg"

logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s][export_osm_data] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)


# Download and extract the latest osm data (zip) from "http://download.geofabrik.de/europe/germany/hamburg-latest-free.shp.zip" 
def download_latest_osm_data_set():
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
def convert_shp_file(name: str, query:str, output:str):
    name = name + ".shp"
    output = output + ".geojson"

    logging.info(f"Converting '{name}' -> '{output}'")
    shp_file_path = f"{EXTRACT_DIR}/{name}"

    # get content of shp file
    gdf = gpd.read_file(shp_file_path)

    # filter features where column "fclass" equals the query
    filtered_data = gdf[gdf["fclass"] == query]
    output_geojson_path = f"./data/generated/osm/{output}"
    
    # Save to geojson
    filtered_data.to_file(output_geojson_path, driver='GeoJSON')


def main():
    download_latest_osm_data_set()
    convert_shp_file("gis_osm_traffic_free_1", "parking_bicycle", "bicycle_parking")
    convert_shp_file("gis_osm_traffic_a_free_1", "parking_bicycle", "bicycle_parking_polygon")
    convert_shp_file("gis_osm_pois_free_1", "bicycle_rental", "bicycle_rental")
    convert_shp_file("gis_osm_pois_free_1", "bicycle_shop", "bicycle_shop")
    convert_shp_file("gis_osm_pois_a_free_1", "bicycle_rental", "bicycle_rental_polygon")
    convert_shp_file("gis_osm_pois_a_free_1", "bicycle_shop", "bicycle_shop_polygon")
    logging.info("Done.")
   

if __name__ == "__main__":
    main()