import datetime
import json
import math
import time
import arcpy
import requests
from setup import *

base_url = "https://www.gis-idmz.nrw.de/arcgis/rest/services/stba/unfallstatistik/MapServer/100/query?"

spatial_reference_in = 25832
spatial_reference_out = 25832

total_max_x = 606885.400445
total_max_y = 5957071.658003
total_min_x = 526588.190788
total_min_y = 5913195.599347

parts_x = 15
parts_y = 10

increase_x = (total_max_x - total_min_x) / parts_x
increase_y = (total_max_y - total_min_y) / parts_y

min_year = 2016

# current year
max_year = datetime.date.today().year

sleep_time = 1

mapping_accidents = {
    "Unfall mit Leichtverletzten": 1,
    "Unfall mit Schwerverletzten": 2,
    "Unfall mit Getöteten": 3
}

mapping_roads = {
    "primary": 1.2,
    "motorway": 1,
    "secondary": 1.5,
    "default": 2
}

buffer_radius_analysis = 5
buffer_radius_decision = 30
threshold = 6

file_total_accidents = "\\data\\generated\\accidents\\accidents_total.geojson"
file_boundary = "\\data\\boundary\\hamburg_boundary.geojson"
file_roads = "\\data\\open-street-map\\gis_osm_roads_free_1.shp"


def set_dresden_properties():
    global file_roads, file_boundary, total_max_x, total_max_y, total_min_x, total_min_y, increase_x, increase_y, parts_x, parts_y, file_total_accidents

    file_boundary = "\\data\\boundary\\dresden_boundary.geojson"
    file_roads = "\\data\\open-street-map-dresden\\gis_osm_roads_free_1.shp"
    file_total_accidents = "\\data\\generated\\accidents\\accidents_total_dresden.geojson"
    total_max_x = 843024
    total_max_y = 5673292
    total_min_x = 820516
    total_min_y = 5657921

    parts_x = 5
    parts_y = 4

    increase_x = (total_max_x - total_min_x) / parts_x
    increase_y = (total_max_y - total_min_y) / parts_y


def generate_url(options, current_year):
    return base_url + "f=json&geometry=%7B%22spatialReference%22%3A%7B%22wkid%22%3A" + str(spatial_reference_in) + \
           "%7D%2C%22xmin%22%3A" + str(options["x_min"]) + \
           "%2C%22ymin%22%3A" + str(options["y_min"]) + \
           "%2C%22xmax%22%3A" + str(options["x_max"]) + \
           "3%2C%22ymax%22%3A" + str(options["y_max"]) + \
           "%7D&outFields=OBJECTID%2CUnfallkategorie%2C" \
           "PKW%2CFu%C3%9Fg%C3%A4nger%2C" \
           "Kraftrad%2CRad%2CGKFZ%2C" \
           "Sonstige&" \
           "spatialRel=esriSpatialRelContains&where=UJAHR%20%3D%20" \
           + str(current_year) + \
           "&geometryType=esriGeometryEnvelope&inSR=25832&outSR=25832"


def generate_urls(current_year):
    current_urls = []

    for x in range(0, parts_x):
        for y in range(0, parts_y):
            current_urls.append(generate_url({
                "x_min": total_min_x + increase_x * x,
                "y_min": total_min_y + increase_y * y,
                "x_max": total_min_x + increase_x * (x + 1),
                "y_max": total_min_y + increase_y * (y + 1)
            }, current_year))
    return current_urls


def convert_seconds_to_string(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%d:%02d:%02d" % (hour, minutes, seconds)


def get_accidents():
    total_geojson = None
    total_features = {}
    count = 0

    all_urls = {}
    for year in range(min_year, max_year):
        all_urls[year] = generate_urls(year)

    for year in range(min_year, max_year):
        log("Start downloading year: " + str(year))

        responses = []
        for url in all_urls[year]:
            if count % 10 == 0:
                log("Step " + str(int(count / 10)) + "/" + str(
                    int(parts_y * parts_x * (max_year - min_year) / 10)) + ": " + convert_seconds_to_string(
                    ((parts_y * parts_x * (max_year - min_year)) - count) * sleep_time))
            r = requests.get(url=url)
            result_json = r.json()
            responses.append(result_json)
            time.sleep(sleep_time)
            count += 1

        dict_features = {}

        for response in responses:
            for feature in response["features"]:
                if feature["attributes"]["Rad"] == 0:
                    continue
                feature["attributes"]["Jahr"] = year
                feature["attributes"]["OBJECTID"] = str(feature["attributes"]["OBJECTID"]) + "_" + str(year)
                feature["attributes"]["Unfallkategorie"] = mapping_accidents[feature["attributes"]["Unfallkategorie"]]

                dict_features[feature["attributes"]["OBJECTID"]] = feature
                total_features[feature["attributes"]["OBJECTID"]] = feature

        if total_geojson is None:
            total_geojson = responses[0]
            for i in range(0, len(total_geojson["fields"])):
                if total_geojson["fields"][i]["name"] == "Unfallkategorie":
                    total_geojson["fields"][i]["type"] = "esriFieldTypeSmallInteger"

        geojson = responses[0]
        geojson["features"] = []
        for i in range(0, len(geojson["fields"])):
            if geojson["fields"][i]["name"] == "Unfallkategorie":
                geojson["fields"][i]["type"] = "esriFieldTypeSmallInteger"

        for key, value in dict_features.items():
            geojson["features"].append(value)

        with open("data/generated/accidents/accidents_" + str(year) + ".geojson", "w") as file:
            log("Saving ...")
            json.dump(geojson, file)

    for key, value in total_features.items():
        total_geojson["features"].append(value)

    with open("data/generated/accidents/accidents_total.geojson", "w") as file:
        json.dump(total_geojson, file)


def create_buffer(feature_name, output_feature_name, distance):
    log("Creating buffer around " + feature_name + " to " + output_feature_name)
    arcpy.analysis.Buffer(feature_name,
                          get_data_base_path(output_feature_name),
                          str(distance) + " Meters", "FULL", "ROUND", "NONE", None, "PLANAR")


def dissolve_features(feature_name, output_feature_name):
    log("Dissolving " + feature_name + " to " + output_feature_name)
    arcpy.management.Dissolve(feature_name, get_data_base_path(output_feature_name), None, None, "SINGLE_PART",
                              "DISSOLVE_LINES", '')


def spatial_join(target_feature, join_feature, output_feature):
    log("Joining " + target_feature + " and " + join_feature + " to " + output_feature)
    arcpy.analysis.SpatialJoin(target_feature, join_feature,
                               get_data_base_path(output_feature),
                               "JOIN_ONE_TO_ONE", "KEEP_ALL",
                               'Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,accidents_dissolved,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,accidents_dissolved,Shape_Area,-1,-1;Unfallkategorie "Unfallkategorie" true true false 2 Short 0 0,Sum,#,accidents,Unfallkategorie,-1,-1;PKW "PKW" true true false 2 Short 0 0,Sum,#,accidents,PKW,-1,-1;Fußgänger "Fußgänger" true true false 2 Short 0 0,Sum,#,accidents,Fußgänger,-1,-1;Kraftrad "Kraftrad" true true false 2 Short 0 0,Sum,#,accidents,Kraftrad,-1,-1;Rad "Rad" true true false 2 Short 0 0,Sum,#,accidents,Rad,-1,-1;GKFZ "GKFZ" true true false 2 Short 0 0,Sum,#,accidents,GKFZ,-1,-1;Sonstige "Sonstige" true true false 2 Short 0 0,Sum,#,accidents,Sonstige,-1,-1',
                               "INTERSECT", None, '')


def import_shp_file(local_file, feature_name, condition):
    log("Importing " + local_file + " to " + feature_name + "(" + condition + ")")
    arcpy.conversion.ExportFeatures(
        get_local_file_path(local_file),
        get_data_base_path(feature_name), condition,
        "NOT_USE_ALIAS",
        'osm_id "osm_id" true true false 12 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',osm_id,0,12;code "code" true true false 4 Short 0 4,First,#,' + get_local_file_path(
            local_file) + ',code,-1,-1;fclass "fclass" true true false 28 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',fclass,0,28;name "name" true true false 100 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',name,0,100;ref "ref" true true false 20 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',ref,0,20;oneway "oneway" true true false 1 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',oneway,0,1;maxspeed "maxspeed" true true false 3 Short 0 3,First,#,' + get_local_file_path(
            local_file) + ',maxspeed,-1,-1;layer "layer" true true false 12 Double 0 12,First,#,' + get_local_file_path(
            local_file) + ',layer,-1,-1;bridge "bridge" true true false 1 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',bridge,0,1;tunnel "tunnel" true true false 1 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',tunnel,0,1',
        None)


def add_field_to_table(feature, field_name):
    arcpy.management.AddField(get_data_base_path(feature), field_name, "FLOAT", None, None, None, '', "NULLABLE",
                              "NON_REQUIRED", '')


def count_road_types(target_feature, join_feature, output_feature):
    log("Counting road types of " + join_feature)
    arcpy.analysis.SpatialJoin(target_feature, join_feature,
                               get_data_base_path(output_feature),
                               "JOIN_ONE_TO_ONE", "KEEP_ALL",
                               join_feature + '_count "Join_Count" true true false 4 Long 0 0,First,#,accidents_dissolved_joined,Join_Count,-1,-1;TARGET_FID "TARGET_FID" true true false 4 Long 0 0,First,#,accidents_dissolved_joined,TARGET_FID,-1,-1;Unfallkategorie "Unfallkategorie" true true false 50 Text 0 0,First,#,accidents_dissolved_joined,Unfallkategorie,0,50;PKW "PKW" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,PKW,-1,-1;Fußgänger "Fußgänger" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,Fußgänger,-1,-1;Kraftrad "Kraftrad" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,Kraftrad,-1,-1;Rad "Rad" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,Rad,-1,-1;GKFZ "GKFZ" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,GKFZ,-1,-1;Sonstige "Sonstige" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,Sonstige,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,accidents_dissolved_joined,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,accidents_dissolved_joined,Shape_Area,-1,-1;osm_id "osm_id" true true false 12 Text 0 0,First,#,roads_primary,osm_id,0,12;code "code" true true false 2 Short 0 0,First,#,roads_primary,code,-1,-1;fclass "fclass" true true false 28 Text 0 0,First,#,roads_primary,fclass,0,28;name "name" true true false 100 Text 0 0,First,#,roads_primary,name,0,100;ref "ref" true true false 20 Text 0 0,First,#,roads_primary,ref,0,20;oneway "oneway" true true false 1 Text 0 0,First,#,roads_primary,oneway,0,1;maxspeed "maxspeed" true true false 2 Short 0 0,First,#,roads_primary,maxspeed,-1,-1;layer "layer" true true false 8 Double 0 0,First,#,roads_primary,layer,-1,-1;bridge "bridge" true true false 1 Text 0 0,First,#,roads_primary,bridge,0,1;tunnel "tunnel" true true false 1 Text 0 0,First,#,roads_primary,tunnel,0,1;Shape_Length_1 "Shape_Length" false true true 8 Double 0 0,First,#,roads_primary,Shape_Length,-1,-1',
                               "INTERSECT", None, '')


def calculate_score_of_roads(feature, field_name):
    log("Calculating score of road")
    arcpy.management.CalculateField(feature, field_name, "Reclass(!fclass!)", "PYTHON3", """def Reclass(arg):
        if arg is "primary" or arg is "primary_link":
            return """ + str(mapping_roads["primary"]) + """
        elif arg is "secondary" or arg is "secondary_link":
            return """ + str(mapping_roads["secondary"]) + """
        return """ + str(mapping_roads["motorway"]) + """
    """, "TEXT", "NO_ENFORCE_DOMAINS")


def calculate_score_of_vulnerability(feature, field_name):
    log("Calculating score of vulnerability")
    arcpy.management.CalculateField(feature, field_name,
                                    "!Unfallkategorie! / !Join_Count!", "PYTHON3", '',
                                    "TEXT", "NO_ENFORCE_DOMAINS")


def calculate_score_of_amount(feature, field_name):
    log("Calculating score of amount")
    arcpy.management.CalculateField(feature, field_name,
                                    "!Join_Count!", "PYTHON3", '',
                                    "TEXT", "NO_ENFORCE_DOMAINS")


def spatial_join_roads_and_accidents(target_feature, join_feature, output_feature):
    log("Spatial join roads and accidents")
    arcpy.analysis.SpatialJoin(target_feature, join_feature,
                               get_data_base_path(output_feature),
                               "JOIN_ONE_TO_ONE", "KEEP_ALL",
                               'Join_Count "Join_Count" true true false 4 Long 0 0,First,#,accidents_dissolved_joined,Join_Count,-1,-1;TARGET_FID "TARGET_FID" true true false 4 Long 0 0,First,#,accidents_dissolved_joined,TARGET_FID,-1,-1;Unfallkategorie "Unfallkategorie" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,Unfallkategorie,-1,-1;PKW "PKW" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,PKW,-1,-1;Fußgänger "Fußgänger" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,Fußgänger,-1,-1;Kraftrad "Kraftrad" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,Kraftrad,-1,-1;Rad "Rad" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,Rad,-1,-1;GKFZ "GKFZ" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,GKFZ,-1,-1;Sonstige "Sonstige" true true false 2 Short 0 0,First,#,accidents_dissolved_joined,Sonstige,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,accidents_dissolved_joined,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,accidents_dissolved_joined,Shape_Area,-1,-1;score_vulnerability "score_vulnerability" true true false 4 Float 0 0,First,#,accidents_dissolved_joined,score_vulnerability,-1,-1;score_amount "score_amount" true true false 4 Float 0 0,First,#,accidents_dissolved_joined,score_amount,-1,-1;osm_id "osm_id" true true false 12 Text 0 0,First,#,roads,osm_id,0,12;code "code" true true false 2 Short 0 0,First,#,roads,code,-1,-1;fclass "fclass" true true false 28 Text 0 0,First,#,roads,fclass,0,28;name "name" true true false 100 Text 0 0,First,#,roads,name,0,100;score_road "score" true true false 4 Float 0 0,Max,#,roads,score,-1,-1',
                               "INTERSECT", None, '')


def calculate_missing_scores_of_road(feature, field_name):
    log("Calculating max value of " + feature + "/" + field_name)
    arcpy.management.CalculateField(feature, field_name, "Reclass(!" + field_name + "!)", "PYTHON3", """def Reclass(arg):
        if arg is None:
            return """ + str(mapping_roads["default"]) + """
        return arg
        """, "FLOAT", "NO_ENFORCE_DOMAINS")


def calculate_score_of_area(feature, field_name):
    max_area = buffer_radius_analysis * math.pi
    arcpy.management.CalculateField(feature, field_name, "Reclass(!SHAPE_AREA!, !score_amount!)", "PYTHON3", """def Reclass(arg, score_amount):
            score = """ + str(max_area) + """ - (arg / score_amount)
            return score if score > 0 else 0""", "FLOAT", "NO_ENFORCE_DOMAINS")


def get_max_value_of_field(feature, field):
    max_value_of_field = 0
    with arcpy.da.SearchCursor(get_data_base_path(feature), [field]) as cursor:
        for row in cursor:
            if row[0] > max_value_of_field:
                max_value_of_field = row[0]
    return max_value_of_field


def calculate_total_score(feature, field_name):
    arcpy.management.CalculateField(feature, field_name,
                                    "Reclass(!score_road!, !score_area!, !score_vulnerability!, !score_amount!)",
                                    "PYTHON3", """def Reclass(road, area, vulnerability, amount):
                return road * area * vulnerability""", "FLOAT", "NO_ENFORCE_DOMAINS")


def clip_to_boundary(feature_accidents, boundary, output):
    log("Map accidents to boundary")
    arcpy.analysis.Intersect(feature_accidents + " #;" + boundary + " #",
                             get_data_base_path(output),
                             "ALL", None, "INPUT")


def normalize_total_score(feature, field_name):
    max_score = get_max_value_of_field(feature, field_name)
    log("Max score: " + str(max_score))
    arcpy.management.CalculateField(feature, field_name, "Reclass(!" + field_name + "!)", "PYTHON3", """def Reclass(arg):
            return arg / """ + str(max_score) + """""", "FLOAT", "NO_ENFORCE_DOMAINS")


def get_accident_black_spots(feature, output_feature):
    log("Get accident black spots")
    arcpy.conversion.ExportFeatures(feature,
                                    get_data_base_path(output_feature),
                                    "total_score > " + str(threshold), "NOT_USE_ALIAS",
                                    'Join_Count "Join_Count" true true false 4 Long 0 0,First,#,accidents_with_all_scores,Join_Count,-1,-1;TARGET_FID "TARGET_FID" true true false 4 Long 0 0,First,#,accidents_with_all_scores,TARGET_FID,-1,-1;Join_Count_1 "Join_Count" true true false 4 Long 0 0,First,#,accidents_with_all_scores,Join_Count_1,-1,-1;TARGET_FID_1 "TARGET_FID" true true false 4 Long 0 0,First,#,accidents_with_all_scores,TARGET_FID_1,-1,-1;Unfallkategorie "Unfallkategorie" true true false 2 Short 0 0,First,#,accidents_with_all_scores,Unfallkategorie,-1,-1;PKW "PKW" true true false 2 Short 0 0,First,#,accidents_with_all_scores,PKW,-1,-1;Fußgänger "Fußgänger" true true false 2 Short 0 0,First,#,accidents_with_all_scores,Fußgänger,-1,-1;Kraftrad "Kraftrad" true true false 2 Short 0 0,First,#,accidents_with_all_scores,Kraftrad,-1,-1;Rad "Rad" true true false 2 Short 0 0,First,#,accidents_with_all_scores,Rad,-1,-1;GKFZ "GKFZ" true true false 2 Short 0 0,First,#,accidents_with_all_scores,GKFZ,-1,-1;Sonstige "Sonstige" true true false 2 Short 0 0,First,#,accidents_with_all_scores,Sonstige,-1,-1;score_vulnerability "score_vulnerability" true true false 4 Float 0 0,First,#,accidents_with_all_scores,score_vulnerability,-1,-1;score_amount "score_amount" true true false 4 Float 0 0,First,#,accidents_with_all_scores,score_amount,-1,-1;osm_id "osm_id" true true false 12 Text 0 0,First,#,accidents_with_all_scores,osm_id,0,12;code "code" true true false 2 Short 0 0,First,#,accidents_with_all_scores,code,-1,-1;fclass "fclass" true true false 28 Text 0 0,First,#,accidents_with_all_scores,fclass,0,28;name "name" true true false 100 Text 0 0,First,#,accidents_with_all_scores,name,0,100;score_road "score" true true false 4 Float 0 0,First,#,accidents_with_all_scores,score_road,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0,First,#,accidents_with_all_scores,Shape_Length,-1,-1;Shape_Area "Shape_Area" false true true 8 Double 0 0,First,#,accidents_with_all_scores,Shape_Area,-1,-1;score_area "score_area" true true false 4 Float 0 0,First,#,accidents_with_all_scores,score_area,-1,-1;total_score "total_score" true true false 4 Float 0 0,First,#,accidents_with_all_scores,total_score,-1,-1',
                                    None)


def calculate_center_point(feature, output_feature):
    add_field_to_table(feature, "x")
    add_field_to_table(feature, "y")
    arcpy.management.CalculateGeometryAttributes(feature, "x INSIDE_X;y INSIDE_Y", '', '', None,
                                                 "SAME_AS_INPUT")

    point_feature_table_name = feature + "_exported_table"
    arcpy.conversion.ExportTable(feature,
                                 get_data_base_path(point_feature_table_name),
                                 '', "NOT_USE_ALIAS",
                                 'Join_Count "Join_Count" true true false 4 Long 0 0,First,#,accident_black_spots_decision,Join_Count,-1,-1;TARGET_FID "TARGET_FID" true true false 4 Long 0 0,First,#,accident_black_spots_decision,TARGET_FID,-1,-1;Join_Count_1 "Join_Count" true true false 4 Long 0 0,First,#,accident_black_spots_decision,Join_Count_1,-1,-1;TARGET_FID_1 "TARGET_FID" true true false 4 Long 0 0,First,#,accident_black_spots_decision,TARGET_FID_1,-1,-1;Unfallkategorie "Unfallkategorie" true true false 2 Short 0 0,First,#,accident_black_spots_decision,Unfallkategorie,-1,-1;PKW "PKW" true true false 2 Short 0 0,First,#,accident_black_spots_decision,PKW,-1,-1;Fußgänger "Fußgänger" true true false 2 Short 0 0,First,#,accident_black_spots_decision,Fußgänger,-1,-1;Kraftrad "Kraftrad" true true false 2 Short 0 0,First,#,accident_black_spots_decision,Kraftrad,-1,-1;Rad "Rad" true true false 2 Short 0 0,First,#,accident_black_spots_decision,Rad,-1,-1;GKFZ "GKFZ" true true false 2 Short 0 0,First,#,accident_black_spots_decision,GKFZ,-1,-1;Sonstige "Sonstige" true true false 2 Short 0 0,First,#,accident_black_spots_decision,Sonstige,-1,-1;score_vulnerability "score_vulnerability" true true false 4 Float 0 0,First,#,accident_black_spots_decision,score_vulnerability,-1,-1;score_amount "score_amount" true true false 4 Float 0 0,First,#,accident_black_spots_decision,score_amount,-1,-1;osm_id "osm_id" true true false 12 Text 0 0,First,#,accident_black_spots_decision,osm_id,0,12;code "code" true true false 2 Short 0 0,First,#,accident_black_spots_decision,code,-1,-1;fclass "fclass" true true false 28 Text 0 0,First,#,accident_black_spots_decision,fclass,0,28;name "name" true true false 100 Text 0 0,First,#,accident_black_spots_decision,name,0,100;score_road "score" true true false 4 Float 0 0,First,#,accident_black_spots_decision,score_road,-1,-1;score_area "score_area" true true false 4 Float 0 0,First,#,accident_black_spots_decision,score_area,-1,-1;total_score "total_score" true true false 4 Float 0 0,First,#,accident_black_spots_decision,total_score,-1,-1;x "x" true true false 4 Float 0 0,First,#,accident_black_spots_decision,x,-1,-1;y "y" true true false 4 Float 0 0,First,#,accident_black_spots_decision,y,-1,-1',
                                 None)
    arcpy.management.XYTableToPoint(point_feature_table_name,
                                    get_data_base_path(output_feature),
                                    "x", "y", None,
                                    'PROJCS["ETRS_1989_UTM_Zone_32N",GEOGCS["GCS_ETRS_1989",DATUM["D_ETRS_1989",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",9.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]];-5120900 -9998100 450445547.391054;-100000 10000;-100000 10000;0.001;0.001;0.001;IsHighPrecision')


def export(feature, file_name):
    log("Saving " + file_name + "... ")
    arcpy.conversion.FeaturesToJSON(feature,
                                    get_local_file_path(file_name),
                                    "NOT_FORMATTED", "NO_Z_VALUES", "NO_M_VALUES", "GEOJSON", "WGS84",
                                    "USE_FIELD_NAME")


def main():
    init_arcpy()

    # Dresden
    # set_dresden_properties()
    # use this function to update the data sets
    # get_accidents()

    clear_database()

    # convert geojson to geo feature
    import_geojson(file_total_accidents, "accidents", "POINT")
    import_geojson(file_boundary, "boundary", "POLYGON")

    clip_to_boundary("accidents", "boundary", "accidents_mapped")

    # make buffer around all accidents
    create_buffer("accidents_mapped", "accidents_buffer_10m", buffer_radius_analysis)

    # dissolve accidents buffers to merge overlapping buffers
    dissolve_features("accidents_buffer_10m", "accidents_dissolved")
    spatial_join("accidents_dissolved", "accidents", "accidents_dissolved_joined")

    add_field_to_table("accidents_dissolved_joined", "score_vulnerability")
    calculate_score_of_vulnerability("accidents_dissolved_joined", "score_vulnerability")

    add_field_to_table("accidents_dissolved_joined", "score_amount")
    calculate_score_of_amount("accidents_dissolved_joined", "score_amount")

    import_shp_file(file_roads, "roads",
                    "fclass = 'motorway' Or fclass = 'motorway_link' Or fclass = 'primary' Or fclass = 'primary_link' Or fclass = 'secondary' Or fclass = 'secondary_link'")

    add_field_to_table("roads", "score")
    calculate_score_of_roads("roads", "score")

    spatial_join_roads_and_accidents("accidents_dissolved_joined", "roads", "accidents_with_all_scores")
    calculate_missing_scores_of_road("accidents_with_all_scores", "score_road")

    add_field_to_table("accidents_with_all_scores", "score_area")
    calculate_score_of_area("accidents_with_all_scores", "score_area")

    add_field_to_table("accidents_with_all_scores", "total_score")
    calculate_total_score("accidents_with_all_scores", "total_score")

    #normalize_total_score("accidents_with_all_scores", "total_score")
    get_accident_black_spots("accidents_with_all_scores", "accident_black_spots_decision")

    calculate_center_point("accident_black_spots_decision", "accident_black_spots_points")
    create_buffer("accident_black_spots_points", "accident_black_spots", buffer_radius_decision)

    export("accident_black_spots", "\\data\\generated\\accidents\\accident_black_spots.geojson")


if __name__ == "__main__":
    main()
