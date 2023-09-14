import geopandas as gpd
import sys
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s][generate_accident_hot_spots] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)

MAPPING_ROADS = {
    "primary": .7,
    "motorway": 0.5,
    "secondary": .85,
    "default": 1
}

ANALYSIS_BUFFER_RADIUS = 5


def read_geojson_file(file):
    logging.info(f"Reading file '{file}'")
    gdf = gpd.read_file(file)
    return gdf


def clip_to_boundary(boundary, accidents):
    logging.info("Clip accidents to boundary.")
    return accidents[accidents.geometry.within(boundary.unary_union)]


def create_buffer(feature, distance):
    logging.info(f"Creating buffer with radius {distance}")
    buffered_gdf = feature.copy()
    buffered_gdf['geometry'] = feature.buffer(distance)
    return buffered_gdf


def save(feature, file):
    feature.to_file(f"./data/generated/accidents/{file}", driver='GeoJSON') 


def merge_overlapping_buffers(feature):
    logging.info("Merging overlapping buffers.")

    unioned_geometry = feature.geometry.unary_union
    individual_polygons = unioned_geometry.geoms
    features = [{'geometry': geom, 'id': idx} for idx, geom in enumerate(individual_polygons)]
    return gpd.GeoDataFrame(features, crs=feature.crs)


def spatial_join_accidents_and_buffer(accidents, buffer):
    count_list = []
    unfallkategorie_sum_list = []

    for index, merged_buffer in buffer.iterrows():
        points_inside_buffer = accidents[accidents.geometry.within(merged_buffer['geometry'])]
        point_count = len(points_inside_buffer)
        unfallkategorie_sum = points_inside_buffer["Unfallkategorie"].sum()
        count_list.append(point_count)
        unfallkategorie_sum_list.append(unfallkategorie_sum)

    buffer['count'] = count_list
    buffer['Unfallkategorie_Sum'] = unfallkategorie_sum_list


def calculate_score_amount(feature):
    logging.info("Calculating score of amount.")
    feature['score_amount'] = feature['count']


def calculate_score_of_area(feature):
    logging.info("Calculating score of area.")
    max_area = ANALYSIS_BUFFER_RADIUS ** 2 *  3.1415926535
    feature['area'] = feature.geometry.area
    score_area = []
    for index, merged_buffer in feature.iterrows():
        score = (max_area - (merged_buffer["area"] / merged_buffer["count"])) / max_area
        if score < 0:
            score = 0
        score_area.append(score)
    feature["score_area"] = score_area


def calculate_score_of_vulnerability(feature):
    logging.info("Calculating score of vulnerability.")

    score_vulnerability = []
    for index, merged_buffer in feature.iterrows():
        score = merged_buffer["Unfallkategorie_Sum"] / merged_buffer["count"] / 3
        score_vulnerability.append(score)
    feature["score_vulnerability"] = score_vulnerability


def filter_roads(roads):
    logging.info("Filtering roads.")
    filtered_road_types = ["motorway_link", "motorway", "primary", "primary_link", "secondary", "secondary_link"]
    filtered_data = roads[roads["fclass"].isin(filtered_road_types)]
    
    scores = []

    for index, merged_buffer in filtered_data.iterrows():
        fclass = merged_buffer["fclass"]
        if fclass == "motorway_link" or fclass == "motorway":
            scores.append(MAPPING_ROADS["motorway"])
        elif fclass == "primary_link" or fclass == "primary":
            scores.append(MAPPING_ROADS["primary"])
        else:
            scores.append(MAPPING_ROADS["secondary"])

    filtered_data["score"] = scores
    return filtered_data


def spatial_join_roads_and_buffer(roads, buffer):
    logging.info("Calculating score of roads.")
    highest_scores = {}

    roads_with_buffer = roads.copy()
    roads_with_buffer['geometry'] = roads_with_buffer['geometry'].buffer(5)


    for index, merged_buffer in buffer.iterrows():
        buffer_geometry = merged_buffer['geometry']

        intersecting_lines = roads_with_buffer[roads_with_buffer.geometry.intersects(buffer_geometry)]

        if intersecting_lines.empty:
            highest_score = MAPPING_ROADS["default"]
        else:
            highest_score = intersecting_lines['score'].max()

        highest_scores[index] = highest_score

    buffer['score_road'] = buffer.index.map(highest_scores)


def calculate_total_score(features):
    scores = []
    for index, feature in features.iterrows():
        score_vulnerability = feature["score_vulnerability"]
        score_area = feature["score_area"]
        score_road = feature["score_road"]
        score_amount = feature["score_amount"]
        scores.append(score_road * score_area * score_vulnerability * score_amount)
    features["score_total"] = scores

def get_centroids(feature):
    logging.info("Calculating centroids.")
    # Create an empty list to hold the centroid point geometries
    centroid_geometries = []

    # Iterate over the rows of the GeoDataFrame
    for idx, polygon_row in feature.iterrows():
        # Calculate the centroid of the polygon
        centroid = polygon_row['geometry'].centroid

        # Store the centroid geometry in the list
        centroid_geometries.append(centroid)

    # Create a new GeoDataFrame with the centroid geometries
    points_gdf = gpd.GeoDataFrame(geometry=centroid_geometries, crs=feature.crs)

    # Copy attributes from the original GeoDataFrame
    for col in feature.columns:
        if col != 'geometry':
            points_gdf[col] = feature[col].values

    return points_gdf


def main():
    amount_of_spots = 30
    if len(sys.argv) > 0 and sys.argv[0].isdigit():
        amount_of_spots = int(sys.argv[0])    
        
    boundary = read_geojson_file("./data/boundary/hamburg_boundary.geojson")
    boundary = boundary.to_crs(epsg=25832)

    accidents = read_geojson_file("./data/generated/accidents/accidents_total.geojson")

    # select all accidents inside the boundaries of hamburg
    clipped_accidents = clip_to_boundary(boundary, accidents)

    # create a buffer around every accident
    buffer_accidents = create_buffer(clipped_accidents, ANALYSIS_BUFFER_RADIUS)

    # merge all overlapping buffer
    merged_buffer_accidents = merge_overlapping_buffers(buffer_accidents)

    spatial_join_accidents_and_buffer(accidents, merged_buffer_accidents)

    roads = read_geojson_file("./data/temp/hamburg/gis_osm_roads_free_1.shp")
    roads = filter_roads(roads)
    roads = roads.to_crs("EPSG:25832")
    
    spatial_join_roads_and_buffer(roads, merged_buffer_accidents)    
    calculate_score_amount(merged_buffer_accidents)
    calculate_score_of_vulnerability(merged_buffer_accidents)
    calculate_score_of_area(merged_buffer_accidents)

    calculate_total_score(merged_buffer_accidents)

    top_rows = merged_buffer_accidents.nlargest(amount_of_spots, "score_total")

    centroids = get_centroids(top_rows)
    centroids = centroids.to_crs("EPSG:4326")

    logging.info(f"Saving '{amount_of_spots}' spots.")

    save(centroids, "accident_hot_spots.geojson")


if __name__ == "__main__":
    main()