import geopandas as gpd
import logging

from shapely.geometry import Point
from pyogrio import read_dataframe

# amount of hot spots that will be exported with this script
HOT_SPOTS_AMOUNT_EXPORT = 30

# spatial distance between accidents to belong to the same cluster in m
CLUSTER_THRESHOLD = 15

# buffer size around a road to map roads to clusters in m
ROAD_THRESHOLD = 20

# "bigger" streets have more traffic. That means an accident is more likely to happen
# so if there is the same amount of accidents on a smaller street that spot is more dangerous
# score of a road with the fclass "primary" or "primary_link"
SCORE_ROAD_PRIMARY = 0.8
# score of a road with the fclass "secondary"
SCORE_ROAD_SECONDARY = 0.9
# scpre of all the other roads
SCORE_ROAD_OTHERS = 1

# Score for accidents with "UKATEGORIE" == 1 (deadly)
SCORE_ACCIDENT_DEADLY = 1
# Score for accidents with "UKATEGORIE" == 2 (major injuries)
SCORE_ACCIDENT_MAJOR = 0.85
# Score for accidents with "UKATEGORIE" == 3 (minor injuries)
SCORE_ACCIDENT_MINOR = 0.6

class DistanceMatrix:

    def __init__(self, bounding_box, accidents):
        self.bounding_box = bounding_box
        self.spatial_width = bounding_box[2] - bounding_box[0] # long
        self.spatial_height = bounding_box[3] - bounding_box[1] # lat

        self.width = int(self.spatial_width / ( 2 * CLUSTER_THRESHOLD))
        self.height = int(self.spatial_height / ( 2 * CLUSTER_THRESHOLD))
        self.content = [[[] for i in range(0, self.width)] for j in range(0, self.height)]

        self.load(accidents)

    def load(self, accidents):       
        self.step_width = self.spatial_width / self.width
        self.step_height = self.spatial_height / self.height

        for accident in accidents:
            width = int((accident.longitude - self.bounding_box[0]) / self.step_width)
            height = int((accident.latitude - self.bounding_box[1]) / self.step_height)
            
            if height == self.height:
                height -= 1
            if width == self.width:
                width -= 1
            accident.set_matrix_coordinates(width=width, height=height)
            self.content[height][width].append(accident)

    def get(self, height, width):
        if width - 1 < 0 or width + 1 >= self.width:
            return None
        if height - 1 < 0 or height + 1 >= self.height:
            return None
        return self.content[height][width]

    def get_points_close_to(self, position):
        
        width_index = int((position.y - self.bounding_box[0]) / self.step_width)
        height_index = int((position.x - self.bounding_box[1]) / self.step_height)

        potential_partners = []
        coordinates_to_look = [
            [height_index-1, width_index-1],
            [height_index-1, width_index],
            [height_index-1, width_index+1],
            [height_index, width_index-1],
            [height_index, width_index],
            [height_index, width_index+1],
            [height_index+1, width_index-1],
            [height_index+1, width_index],
            [height_index+1, width_index+1]
        ]

        for coords in coordinates_to_look:
            result = self.get(coords[0], coords[1])
            if result is not None:
                potential_partners += result

        return potential_partners

    def remove(self, accident):
        self.content[accident.matrix_height][accident.matrix_width].remove(accident)


class Cluster:

    def __init__(self, point, id) -> None:
        self.points = [point]
        self.center = point.get_position()
        self.id = id
        self.score = 0
        self.road = SCORE_ROAD_OTHERS

    def add(self, point):
        self.points.append(point)
        point_coordinate = point.get_position()
        center_difference_x = self.center[0] - point_coordinate[0]
        center_difference_y = self.center[1] - point_coordinate[1]
        factor = 1 / len(self.points)
        self.center[0] -= center_difference_x * factor
        self.center[1] -= center_difference_y * factor

    def get_center(self):
        return Point(self.center[0], self.center[1]) 
    

    def temp_geojson(self):
        point = Point(self.center[1], self.center[0])
        coords = (self.points[0].matrix_height, self.points[0].matrix_width)

        return {
            "geometry": point,
            "id": self.id,
            "size": len(self.points),
            "coords": str(coords),
        }

    def to_geojson(self):
        geojson = self.temp_geojson()
        geojson["score"] = self.score
        geojson["score_amount"]= self.score_amount
        geojson["score_vulnerability"]= self.score_vulnerability
        geojson["score_road"]= self.score_road
        return geojson

    def calculcate_vulnerability_score(self): 
        score_vulnerability = 0
        for accident in self.points:
            score_vulnerability += accident.get_vulnerability_score()
        
        max_vulnerability = SCORE_ACCIDENT_DEADLY * len(self.points)
        if max_vulnerability == 0:
            raise ValueError("No accidents found.")

        score_vulnerability /= max_vulnerability
        return score_vulnerability

    def calculate_road_score(self):
        return self.road
    
    def calculate_score(self):
        self.score_amount = len(self.points)
        self.score_vulnerability = self.calculcate_vulnerability_score()
        self.score_road = self.calculate_road_score()
        self.score = self.score_amount * self.score_vulnerability * self.score_road        

   
class Accident:

    def __init__(self, accident) -> None:
        self.year = accident["UJAHR"]
        self.month = accident["UMONAT"]
        self.hour = accident["USTUNDE"]
        self.weekday = accident["UWOCHENTAG"]
        self.latitude = accident["geometry"].y
        self.longitude = accident["geometry"].x
        self.vulnerability = accident["UKATEGORIE"]
        self.point = Point(self.latitude, self.longitude)
     
    def set_matrix_coordinates(self, width: int, height: int):
        self.matrix_width = width
        self.matrix_height = height

    def get_position(self):
        return [self.latitude, self.longitude]

    def get_vulnerability_score(self):
        if self.vulnerability == "1":
            return SCORE_ACCIDENT_DEADLY
        if self.vulnerability == "2":
            return SCORE_ACCIDENT_MAJOR
        return SCORE_ACCIDENT_MINOR
    
    def calculate_distance_to_current_center(self, center: Point):
        self.current_distance = self.point.distance(center)


class ClusterManager:

    def __init__(self,accidents_gdf) -> None:
        self.clusters = []

        accidents_gdf = accidents_gdf.to_crs("EPSG:31467")
        accidents = []
        for index, accident in accidents_gdf.iterrows():
            accidents.append(Accident(accident))

        if len(accidents) == 0:
            raise ValueError("No Accidents found.")
        
        self.matrix = DistanceMatrix(accidents_gdf.total_bounds, accidents)
        
        self.clusters.append(Cluster(accidents[0], 0))
        accidents = accidents[1:]

        while len(accidents) > 0:                
            accidents = self.sort_accidents_by_distance(accidents, self.clusters[-1].get_center())
            current_accident = accidents.pop(0)
            self.matrix.remove(current_accident)

            if current_accident.current_distance < CLUSTER_THRESHOLD:
                self.clusters[-1].add(current_accident)
            else:
                self.clusters.append(Cluster(current_accident, len(self.clusters)))       

    def sort_accidents_by_distance(self, accidents, center):
        for accident in accidents:
            accident.current_distance = 1000 * CLUSTER_THRESHOLD
        
        points_potential = self.matrix.get_points_close_to(center)
        for accident in points_potential:
            accident.calculate_distance_to_current_center(center)

        return sorted(accidents, key=lambda accident: accident.current_distance)

    def merge_roads(self, roads):
        clusters_gdf = self.temp_export()
        clusters_gdf['geometry'] = clusters_gdf['geometry'].buffer(ROAD_THRESHOLD)
        roads['geometry'] = roads['geometry'].buffer(ROAD_THRESHOLD)
       
        for index, cluster in clusters_gdf.iterrows():
            buffer_geometry = cluster['geometry']

            intersecting_lines = roads[roads.geometry.intersects(buffer_geometry)]
            highest_score = SCORE_ROAD_OTHERS if intersecting_lines.empty else intersecting_lines['score'].max()

            self.clusters[cluster["id"]].road = highest_score            

    def calculate_scores(self):
        for cluster in self.clusters:
            cluster.calculate_score()

    def temp_export(self):
        jsons = []
        for cluster in self.clusters:
            jsons.append(cluster.temp_geojson())
        
        point_geometries = [cluster["geometry"] for cluster in jsons]
        gdf = gpd.GeoDataFrame(jsons, geometry=point_geometries)
        gdf.crs = "EPSG:31467"
        return gdf


    def export(self):
        jsons = []
        print(len(self.clusters))
        for cluster in self.clusters:
            jsons.append(cluster.to_geojson())
        
        point_geometries = [cluster["geometry"] for cluster in jsons]
        gdf = gpd.GeoDataFrame(jsons, geometry=point_geometries)
        gdf.crs = "EPSG:31467"
        gdf = gdf.to_crs("EPSG:4326")
        sorted_gdf = gdf.sort_values(by='score', ascending=False)
        top_30_rows = sorted_gdf.head(30)
        return top_30_rows


def read_roads():
    roads = read_dataframe("./data/temp/hamburg/gis_osm_roads_free_1.shp")
    
    filtered_road_types = ["primary", "primary_link", "secondary", "secondary_link"]
    logging.info("Filter roads.")
    roads = roads[roads["fclass"].isin(filtered_road_types)]
    scores = []

    for index, road in roads.iterrows():
        fclass = road["fclass"]
        if fclass == "primary_link" or fclass == "primary":
            scores.append(SCORE_ROAD_PRIMARY)
        else:
            scores.append(SCORE_ROAD_SECONDARY)

    roads["score"] = scores
    logging.info("Converting roads geometry to EPSG:31467")
    roads = roads.to_crs("EPSG:31467")
    return roads 


def main():
    logging.info("Reading accidents_total.geojson")
    accidents = read_dataframe("./data/generated/accidents/accidents_total.geojson")

    logging.info("Create clusters of accidents.")
    cluster_manager = ClusterManager(accidents)
    
    logging.info("Reading roads .shp file from OSM.")
    roads = read_roads()
    logging.info("Merging roads with clusters.")
    cluster_manager.merge_roads(roads)

    logging.info("Calculate Score of clusters.")
    cluster_manager.calculate_scores()

    logging.info("Export cluster.")
    accident_hotspots = cluster_manager.export()
    accident_hotspots.to_file("./data/generated/accidents/accident_hot_spots.geojson")


if __name__ == "__main__":
    main()