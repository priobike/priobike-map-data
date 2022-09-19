from setup import *


def main():
    init_arcpy()
    clear_database()
    import_geojson("\\data\\generated\\accidents\\accidents_total.geojson", "accidents", "POINT")
    import_geojson("\\data\\generated\\accidents\\accident_black_spots.geojson", "accidents_black_spots", "POLYGON")
    import_geojson("\\data\\generated\\accidents\\accident_black_spots_dresden.geojson", "accidents_black_spots_dresden", "POLYGON")
    import_geojson("\\data\\generated\\accidents\\accident_total_dresden.geojson", "accidents_black_spots_dresden", "POLYGON")
    import_geojson("\\data\\generated\\osm\\bicycle_parking.geojson", "osm_bicycle_parking", "POINT")
    import_geojson("\\data\\generated\\osm\\bicycle_rental.geojson", "osm_bicycle_rental", "POINT")
    import_geojson("\\data\\generated\\osm\\bicycle_shop.geojson", "osm_bicycle_shop", "POINT")
    import_geojson("\\data\\generated\\osm\\bicycle_parking_polygon.geojson", "osm_bicycle_parking_polygon", "POLYGON")
    import_geojson("\\data\\generated\\osm\\bicycle_rental_polygon.geojson", "osm_bicycle_rental_polygon", "POLYGON")
    import_geojson("\\data\\generated\\osm\\bicycle_shop_polygon.geojson", "osm_bicycle_shop_polygon", "POLYGON")

    import_geojson("\\data\\generated\\wfs\\bike_count.geojson", "wfs_bike_count", "POINT")
    import_geojson("\\data\\generated\\wfs\\bike_and_ride.geojson", "wfs_bike_and_ride", "POINT")
    import_geojson("\\data\\generated\\wfs\\bike_air_station.geojson", "wfs_bike_air_station", "POINT")
    import_geojson("\\data\\generated\\wfs\\construction_sides.geojson", "wfs_construction_sides", "POINT")
    import_geojson("\\data\\generated\\wfs\\stadt_rad.geojson", "wfs_stadt_rad", "POINT")
    import_geojson("\\data\\generated\\wfs\\traffic.geojson", "wfs_traffic", "POLYLINE")



if __name__ == "__main__":
    main()
