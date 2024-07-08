# priobike-map-data

The scripts in this repository can be used to download map data relevant for cyclists in Hamburg. This contains bicycle stands, rental stations, repair stations, air pump stations, velo routes, the current traffic density, construction sites, and accident spots. 

For some datasets, additional processing is performed to obtain meaningful data. For example, the accident spots from the Unfallatlas dataset are clustered to find hotspots and warn users.

To provide this data as map overlays to users of the PrioBike app, it is packaged into a NGINX image which can be deployed as a stateless web service.

[Learn more about PrioBike](https://github.com/priobike)

## Quickstart

The easiest way to run a web service with the processed data is to use the contained `Dockerfile`:

```
docker build -t priobike-map-data . && docker run -p 80:80 --rm priobike-map-data
```

## API and CLI

### `main.py`

This script executes all the following scripts in the correct order. All possible data is updated with this script.

### `export_osm_data.py`

This script downloads the latest OpenStreetMap data for the city of Hamburg (provided by [Geofabrik](http://download.geofabrik.de/europe/germany/hamburg-latest-free.shp.zip)). These are then filtered based on the values of the `fclass` attribute and saved in a `geojson` file. In these datasets, some features are stored as point data and others as polygons. The datasets contain different features.

- Bicycle stands (point data): `gis_osm_traffic_free_1.shp` → `bicycle_parking.geojson` (`fclass=parking_bicycle`)
- Bicycle stands (polygon data): `gis_osm_traffic_a_free_1.shp` → `bicycle_parking_polygon.geojson` (`fclass=parking_bicycle`)
- Bicycle rental stations (point data): `gis_osm_pois_free_1` → `bicycle_rental` (`fclass=bicycle_rental`)
- Bicycle rental stations (polygon data): `gis_osm_pois_a_free_1` → `bicycle_rental_polygon` (`fclass=bicycle_rental`)
- Bicycle shops/workshops (point data): `gis_osm_pois_free_1` → `bicycle_shop` (`fclass=bicycle_shop`)
- Bicycle shops/workshops (polygon data): `gis_osm_pois_a_free_1` → `bicycle_shop_polygon` (`fclass=bicycle_shop`)

### `export_wfs_data.py`

This script downloads data from various Web Feature Services ([WFS](https://en.wikipedia.org/wiki/Web_Feature_Service)) of the city of Hamburg and saves them in a `geojson` file. The following WFS are used:

#### 1. HH_WFS_Bike_und_Ride (`data/generated/wfs/bike_and_ride.geojson`)

The dataset contains the location of bicycle parking facilities at rapid transit stations in the Hamburg metropolitan area. For each facility, the number of public parking spaces (covered and uncovered) and, if available, the number of lockable rental spaces are provided. More details [here](https://metaver.de/trefferanzeige?docuuid=337AA4A2-72EF-4AE0-A8F6-D35B243532DC). [License](https://www.govdata.de/dl-de/by-2-0). [Source](https://geodienste.hamburg.de/HH_WFS_Bike_und_Ride?SERVICE=WFS&REQUEST=GetFeature&outputFormat=application/geo%2Bjson&version=2.0.0&typeName=de.hh.up:bike_und_ride&srsname=EPSG:4326).

#### 2. HH_WFS_Verkehrslage (`data/generated/wfs/traffic.geojson`)

The dataset contains real-time traffic conditions (updated every 5 minutes) on the Hamburg road network and major roads in the immediate vicinity of Hamburg, as well as on highways running through Hamburg south to Lüneburg, Hannover, and Bremen, and north to Itzehoe, Flensburg, and Lübeck.

Traffic conditions are classified into four states, from state class 1, free-flowing traffic (green) to state class 4, congested traffic (dark red). If no data is available for individual segments, no traffic condition is displayed. More details [here](https://metaver.de/trefferanzeige?docuuid=22E00411-7932-47A6-B2DA-26F6E3E22B5E). [License](https://www.govdata.de/dl-de/by-2-0). [Source](https://geodienste.hamburg.de/HH_WFS_Verkehrslage?SERVICE=WFS&REQUEST=GetFeature&typeName=de.hh.up:verkehrslage&version=2.0.0&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326).

#### 3. HH_WFS_Baustellen (`data/generated/wfs/construction_sites.geojson`)

Construction sites on major roads and federal highways in Hamburg. More details [here](https://www.govdata.de/suchen/-/details/baustellen-auf-hauptverkehrs-und-bundesfernstrassen-hamburg). [License](https://www.govdata.de/dl-de/by-2-0). [Source](https://geodienste.hamburg.de/HH_WFS_Baustellen?SERVICE=WFS&REQUEST=GetFeature&typeName=de.hh.up:tns_steckbrief_visualisierung&version=2.0.0&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326).

#### 4. HH_WFS_Stadtrad (`data/generated/wfs/stadt_rad.geojson`)

The dataset contains the position of all StadtRAD stations in the Hamburg metropolitan area and the number of bicycles and cargo pedelecs currently available for rent. More details [here](https://metaver.de/trefferanzeige?docuuid=D18F375E-FA5F-4998-AFF8-557969F44479). [License](https://www.govdata.de/dl-de/by-2-0). [Source](https://geodienste.hamburg.de/HH_WFS_Stadtrad?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&typename=de.hh.up:stadtrad_stationen&outputFormat=application/geo%2bjson&srsname=EPSG:4326).

#### 5. HH_WFS_Fahrradluftstationen (`data/generated/wfs/bike_air_station.geojson`)

[License](https://www.govdata.de/dl-de/by-2-0). [Source](https://geodienste.hamburg.de/HH_WFS_Fahrradluftstationen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=de.hh.up:fahrradluftstationen&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326).

#### 6. HH_WFS_ITS_Dienste_Hamburg (`data/generated/wfs/static_green_waves.geojson`)

Static green waves in Hamburg. More details [here](https://metaver.de/trefferanzeige?cmd=doShowDocument&docuuid=A1ADDD06-FAF3-42B7-8C32-E430EAD67E9F&plugid=/ingrid-group:ige-iplug-hmdk.metaver). [License](https://www.govdata.de/dl-de/by-2-0). [Source](https://geodienste.hamburg.de/HH_WFS_ITS_Dienste_Hamburg?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typeName=de.hh.up:its_iot_registry&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326&Filter=%3Cogc:Filter%20xmlns:ogc=%22http://www.opengis.net/ogc%22%3E%3Cogc:PropertyIsEqualTo%3E%3Cogc:PropertyName%3Epurpose_id%3C/ogc:PropertyName%3E%3Cogc:Literal%3E14%3C/ogc:Literal%3E%3C/ogc:PropertyIsEqualTo%3E%3C/ogc:Filter%3E).

#### 7. HH_WFS_ITS_Dienste_Hamburg (`data/generated/wfs/prio_change.geojson`)

More details [here](https://metaver.de/trefferanzeige?cmd=doShowDocument&docuuid=A1ADDD06-FAF3-42B7-8C32-E430EAD67E9F&plugid=/ingrid-group:ige-iplug-hmdk.metaver). [License](https://www.govdata.de/dl-de/by-2-0). [Source](https://geodienste.hamburg.de/HH_WFS_ITS_Dienste_Hamburg?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typeName=de.hh.up:its_iot_registry&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326&Filter=%3Cogc:Filter%20xmlns:ogc=%22http://www.opengis.net/ogc%22%3E%3Cogc:PropertyIsEqualTo%3E%3Cogc:PropertyName%3Epurpose_id%3C/ogc:PropertyName%3E%3Cogc:Literal%3E15%3C/ogc:Literal%3E%3C/ogc:PropertyIsEqualTo%3E%3C/ogc:Filter%3E).

#### 8. HH_WFS_Velorouten (`data/generated/wfs/velo_routes.geojson`)

The dataset contains the network of the

 Hamburg veloroutes. More details [here](https://metaver.de/trefferanzeige?docuuid=5DBD9327-EAB3-4B60-AE8A-7A8B57D84D7F). [License](https://www.govdata.de/dl-de/by-2-0). [Source](https://geodienste.hamburg.de/HH_WFS_Velorouten?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&typename=de.hh.up:velorouten&outputFormat=application/geo%2Bjson&srsname=EPSG:4326).

### `filter_routing_data.py`

This script downloads the routing data for the city of Hamburg (provided by [Geofabrik](http://download.geofabrik.de/europe/germany/hamburg-latest-free.shp.zip)) and filters it based on the value of the `fclass` attribute. The remaining data is saved in a `geojson` file and used for routing.

- Streets (line data): `gis_osm_roads_free_1.shp` → `streets.geojson`
- Paths (line data): `gis_osm_roads_free_1.shp` → `paths.geojson`

### `reverse_geocoding.py`

This script contains methods to perform reverse geocoding using OpenStreetMap data.

## What else to know

- All geodata generated by these scripts is stored in the `EPSG:4326` coordinate system.
- The `main.py` script should be used to execute all scripts in the correct order to update all data.
- Ensure the required Python libraries are installed to avoid any issues during execution.
- The generated `geojson` files contain valuable geographical information for the PrioBike app and are saved in the `EPSG:4326` coordinate system.

## Contributing

We highly encourage you to open an issue or a pull request. You can also use our repository freely with the `MIT` license.

Every service runs through testing before it is deployed in our release setup. Read more in our [PrioBike deployment readme](https://github.com/priobike/.github/blob/main/wiki/deployment.md) to understand how specific branches/tags are deployed.

Additional credit goes to our external contributors: [SoWieMarkus](https://github.com/SoWieMarkus)

## Anything unclear?

Help us improve this documentation. If you have any problems or unclarities, feel free to open an issue.
