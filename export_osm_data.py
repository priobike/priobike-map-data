from setup import *


def convert_osm_to_geojson(local_file, feature_name, query, geo_json_file_name):
    log("Converting " + local_file + " to " + geo_json_file_name)
    arcpy.conversion.ExportFeatures(
        get_local_file_path(local_file),
        get_data_base_path(feature_name),
        query, "NOT_USE_ALIAS",
        'osm_id "osm_id" true true false 12 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',osm_id,0,12;' + 'code "code" true true false 4 Short 0 4,First,#,' + get_local_file_path(
            local_file) + ',code,-1,-1;' + 'fclass "fclass" true true false 28 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',fclass,0,28;' + 'name "name" true true false 100 Text 0 0,First,#,' + get_local_file_path(
            local_file) + ',name,0,100',
        None)
    arcpy.conversion.FeaturesToJSON(feature_name,
                                    get_local_file_path(geo_json_file_name),
                                    "NOT_FORMATTED", "NO_Z_VALUES", "NO_M_VALUES", "GEOJSON", "KEEP_INPUT_SR",
                                    "USE_FIELD_NAME")


def main():
    init_arcpy()
    clear_database()
    convert_osm_to_geojson("\\data\\open-street-map\\gis_osm_traffic_free_1.shp", "parking_bicycle",
                           "fclass = 'parking_bicycle'", "data\\generated\\osm\\bicycle_parking.geojson")
    convert_osm_to_geojson("\\data\\open-street-map\\gis_osm_traffic_a_free_1.shp", "parking_bicycle_a",
                           "fclass = 'parking_bicycle'", "data\\generated\\osm\\bicycle_parking_polygon.geojson")
    convert_osm_to_geojson("\\data\\open-street-map\\gis_osm_pois_free_1.shp", "rental_bicycle",
                           "fclass = 'bicycle_rental'", "data\\generated\\osm\\bicycle_rental.geojson")
    convert_osm_to_geojson("\\data\\open-street-map\\gis_osm_pois_free_1.shp", "shop_bicycle",
                           "fclass = 'bicycle_shop'", "data\\generated\\osm\\bicycle_shop.geojson")
    convert_osm_to_geojson("\\data\\open-street-map\\gis_osm_pois_a_free_1.shp", "rental_bicycle_a",
                           "fclass = 'bicycle_shop'", "data\\generated\\osm\\bicycle_rental_polygon.geojson")
    convert_osm_to_geojson("\\data\\open-street-map\\gis_osm_pois_a_free_1.shp", "shop_bicycle_a",
                           "fclass = 'bicycle_shop'", "data\\generated\\osm\\bicycle_shop_polygon.geojson")


if __name__ == "__main__":
    main()
