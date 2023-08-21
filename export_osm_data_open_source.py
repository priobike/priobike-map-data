import requests
import zipfile
import geopandas as gpd

ZIP_FILE = "hamburg.zip"
GEOFABRIK_SHP_URL = f"http://download.geofabrik.de/europe/germany/hamburg-latest-free.shp.zip"
TEMP_DIR = f"./data/temp/"
ZIP_FILE_PATH = f"{TEMP_DIR}/{ZIP_FILE}"
EXTRACT_DIR = f"{TEMP_DIR}/hamburg"

def download_latest_osm_data_set():
    response = requests.get(GEOFABRIK_SHP_URL)
    print("Downloading geofabrik zip file.")
    if response.status_code == 200:
        with open(f"{TEMP_DIR}/{ZIP_FILE}", "wb") as file:
            file.write(response.content)
        print("Success.")
        print("Extracting zip file.")
        with zipfile.ZipFile(ZIP_FILE_PATH, 'r') as zip_file:
            zip_file.extractall(EXTRACT_DIR)
        print("Success")
    else:
        raise Exception("Failed to download zip file.")


def read_shp_file(name, query, output):
    print(f"Reading '{name}' -> '{output}'")
    shp_file_path = f"{EXTRACT_DIR}/{name}"
    gdf = gpd.read_file(shp_file_path)
    filtered_data = gdf[gdf["fclass"] == query]
    output_geojson_path = f"./data/generated/osm_os/{output}"
    print("Saving file.")
    filtered_data.to_file(output_geojson_path, driver='GeoJSON')


def main():
    download_latest_osm_data_set()
    read_shp_file("gis_osm_traffic_free_1.shp", "parking_bicycle", "bicycle_parking.geojson")
    read_shp_file("gis_osm_traffic_a_free_1.shp", "parking_bicycle", "bicycle_parking_polygon.geojson")
    read_shp_file("gis_osm_pois_free_1.shp", "bicycle_rental", "bicycle_rental.geojson")
    read_shp_file("gis_osm_pois_free_1.shp", "bicycle_shop", "bicycle_shop.geojson")
    read_shp_file("gis_osm_pois_a_free_1.shp", "bicycle_rental", "bicycle_rental_polygon.geojson")
    read_shp_file("gis_osm_pois_a_free_1.shp", "bicycle_shop", "bicycle_shop_polygon.geojson")
   

if __name__ == "__main__":
    main()