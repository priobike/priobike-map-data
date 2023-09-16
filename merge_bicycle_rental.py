import geopandas as gpd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import logging

STADTRAD_PREFIX = "StadtRAD"
MATCHING_SCORE_THRESHOLD = 80
MAX_MAPPING_DISTANCE_IN_M = 50

def get_osm_entry_by_name(osm, name, match_list):
    query = osm[osm['name'] == name]

    if not query.empty:
        return query
    
    best_match, score = process.extractOne(str(name), match_list, scorer=fuzz.ratio)
    if score < MATCHING_SCORE_THRESHOLD:
        return None
    
    best_match_query = osm[osm['name'] == best_match]
    if best_match_query.empty:
        logging.warning(f"It should find one ... {name, best_match}")
        return None
        
    
    return best_match_query

def edit_osm_entry(query, osm, name, id):
    osm.loc[osm['osm_id'] == query.iloc[0]['osm_id'],"name"] = f"{STADTRAD_PREFIX} {name}"
    osm.loc[osm['osm_id'] == query.iloc[0]['osm_id'],"is_stadtrad"] = True
    osm.loc[osm['osm_id'] == query.iloc[0]['osm_id'],"stadtrad_id"] = id


def map_perfect_matches(wfs, osm):
    matched_stadt_rad_stations = []

    logging.info("Looking for identical matches.")
    for index, stadt_rad_row in wfs.iterrows():
        stadt_rad_station_name = stadt_rad_row["name"]
        stadt_rad_station_id = stadt_rad_row["id"]

        query = osm[osm['name'] == stadt_rad_station_name]

        if query.empty:
            continue

        if query.shape[0] > 1:
            logging.warning(f"Found multiple osm entries for '{stadt_rad_station_name}'.")

        matched_stadt_rad_stations.append(index)
        edit_osm_entry(query=query, osm=osm, name=stadt_rad_station_name, id=stadt_rad_station_id)
        
    
    for index_to_delete in matched_stadt_rad_stations:
        wfs = wfs.drop(index_to_delete)
    logging.info(f"Matched {len(matched_stadt_rad_stations)} StadtRAD stations. {wfs.shape[0]} stations left.")
        
    return wfs

def map_levenshtein_matches(wfs, osm):
    matched_stadt_rad_stations = []

    osm_names = [str(name) for name in osm['name'].tolist()]

    logging.info(f"Looking via Levenshtein distance with threshold score {MATCHING_SCORE_THRESHOLD}")
    for index, stadt_rad_row in wfs.iterrows():
        stadt_rad_station_name = stadt_rad_row["name"]
        stadt_rad_station_id = stadt_rad_row["id"]

        best_match, score = process.extractOne(str(stadt_rad_station_name), osm_names, scorer=fuzz.ratio)
        if score < MATCHING_SCORE_THRESHOLD:
            continue

        query = osm[osm['name'] == best_match]

        if query.empty:
            logging.warning(f"Found {best_match} a second time while looking for {stadt_rad_station_name}")
            continue

        if query.shape[0] > 1:
            logging.warning(f"Found multiple osm entries for '{stadt_rad_station_name}'.")

        matched_stadt_rad_stations.append(index)
        edit_osm_entry(query=query, osm=osm, name=stadt_rad_station_name, id=stadt_rad_station_id)

    for index_to_delete in matched_stadt_rad_stations:
        wfs = wfs.drop(index_to_delete)
    logging.info(f"Matched {len(matched_stadt_rad_stations)} StadtRAD stations. {wfs.shape[0]} stations left.")
    
    return wfs


def create_buffer(feature, distance):
    logging.info(f"Creating buffer with radius {distance}")
    buffered_gdf = feature.copy()
    buffered_gdf['geometry'] = feature.buffer(distance)
    return buffered_gdf

def map_spatial_relation(wfs, osm):
    matched_stadt_rad_stations = []

    logging.info("Looking for spatial relation.")
    projected_wfs = wfs.to_crs("EPSG:32632")
    buffered_wfs = create_buffer(projected_wfs, MAX_MAPPING_DISTANCE_IN_M)
    buffered_wfs_epsg_4326 = buffered_wfs.to_crs("EPSG:4326")

    for index, buffer_row in buffered_wfs_epsg_4326.iterrows():
        stadt_rad_station_name = buffer_row["name"]
        stadt_rad_station_id = buffer_row["id"]
        osm_within_buffer = osm[osm.within(buffer_row['geometry'])]

        if osm_within_buffer.empty:
            continue

        if osm_within_buffer.shape[0] > 1:
            logging.warning(f"Found multiple osm entries for '{stadt_rad_station_name}'.")
        matched_stadt_rad_stations.append(index)
        edit_osm_entry(query=osm_within_buffer, osm=osm, name=stadt_rad_station_name, id=stadt_rad_station_id)
    

    for index_to_delete in matched_stadt_rad_stations:
        wfs = wfs.drop(index_to_delete)

    logging.info(f"Matched {len(matched_stadt_rad_stations)} StadtRAD stations. {wfs.shape[0]} stations left.")
    return wfs

def add_missing_rental_stations(wfs, osm):
    logging.info(f"Adding {wfs.shape[0]} StadtRAD stations to OSM.")

    for index, buffer_row in wfs.iterrows():
        osm_entry = {
            "name": buffer_row["name"],
            "is_stadtrad": True,
            "stadtrad_id": buffer_row["id"],
            "osm_name": "",
            "geometry": buffer_row["geometry"],
            "code": 2566,
            "fclass": "bicycle_rental"

        }
        osm = osm._append(osm_entry, ignore_index=True)

    return osm

def map_wfs_to_osm(wfs, osm):

    # Store the original osm name in a new column
    # this is used for debugging purposes
    osm['osm_name'] = osm['name']

    # initialize a new column "is_stadtrad" or type boolean
    # the value will be True if the osm entry was mapped to a StadtRAD station
    osm['is_stadtrad'] = [False] * len(osm)

    # initialize a new column "stadtrad_id"
    # the value of this column will be the 
    osm['stadtrad_id'] = [None] * len(osm)

    remaining_wfs_stations = map_perfect_matches(wfs, osm)
    remaining_wfs_stations = map_levenshtein_matches(remaining_wfs_stations, osm)
    remaining_wfs_stations = map_spatial_relation(remaining_wfs_stations, osm)
    
    osm = add_missing_rental_stations(remaining_wfs_stations,osm)

    return osm


def main():

    # OSM rental stations
    osm_bicycle_points = gpd.read_file("./data/generated/osm/bicycle_rental_original_osm.geojson")

    # StadtRAD WFS rental stations
    wfs_bicycle_points = gpd.read_file("./data/generated/wfs/stadt_rad.geojson")

    mapped_dataset = map_wfs_to_osm(wfs=wfs_bicycle_points, osm=osm_bicycle_points)
    mapped_dataset.to_file("./data/generated/osm/bicycle_rental.geojson", driver='GeoJSON')

if __name__ == "__main__":
    main()