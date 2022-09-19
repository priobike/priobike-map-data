# Generierung von zusätzlichen Karteninformationen im Umkreis Hamburg

- *Autor*: Markus Wieland
- *Email*: markus.wieland@mailbox.tu-dresden.de

**IMPORTANT** `git lfs pull` to get osm data for this project!

## Setup

* `ArcGIS` installieren. Für Studierende der TU-Dresden gibt es <a href="https://tu-dresden.de/zih/dienste/service-katalog/arbeitsumgebung/dir_software/softwareliste/esri/esri_Stud">hier</a> eine Anleitung
* Konfiguriere die `python.exe` von ArcGIS als Python Interpreter. Die Datei sollte im Normalfall unter diesem Pfad zu finden sein: `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`
* Erstelle ein neues ArcGIS-Projekt und/oder aktualisiere die Pfade in der `setup.py`
  * `script_path` ... Pfad zu diesem Ordner
  * `project_path` ... Pfad zu dem Ordner des ArcGIS-Projekts (Der Ordner in dem die .aprx- Datei liegt). In diesem Beispiel: `<script_path>/arcgisproject`
  * `project_name` ... Name der .aprx-Datei des Projekts (Beispiel: `arcgisproject.aprx`)
  * `database_path` ... Pfad zur Geodatenbank. In diesem Beispiel `<project_path>`
  * `database_name` ... Name der Geodatenbank. In diesem Beispiel `Forschungsprojekt.gdb`

## OpenStreetMap Daten umwandeln
 
Von `/data/open-street-map/` zu `/data/generated/osm`. Umgesetzt mit `export_osm_data.py`

1. Einladen der Dateien:
   1. `gis_osm_pois_free.shp` Points of Interest als Punkt Geometrie
   2. `gis_osm_pois_free_a.shp` Points of Interest als Polygon Geometrie
   3. `gis_osm_traffic_free.shp` Verkehrsdaten als Point Geometrie
   4. `gis_osm_traffic_free_a.shp` Verkehrsdaten als Polygon Geometrie
2. Selektion aller Punkte & speichern in GeoJSON Format
   1. Aus `gis_osm_traffic_free.shp` selektiere alle Felder wo `fclass = parking_bicycle` zu `bicycle_parking`.
   1. Aus `gis_osm_traffic_a_free.shp` selektiere alle Felder wo `fclass = parking_bicycle` zu `bicycle_parking_polygon`.
   1. Aus `gis_osm_pois_free.shp` selektiere alle Felder wo `fclass = bicycle_rental` zu `bicycle_rental`.
   1. Aus `gis_osm_pois_a_free.shp` selektiere alle Felder wo `fclass = bicycle_rental` zu `bicycle_rental_polygon`.
   1. Aus `gis_osm_pois_free.shp` selektiere alle Felder wo `fclass = bicylce_shop` zu `bicylce_shop`.
   1. Aus `gis_osm_pois_a_free.shp` selektiere alle Felder wo `fclass = bicylce_shop` zu `bicylce_shop_polygon`.

## Funktionen der Skripts
- `setup.py` Setup ArcGIS für dieses Projekt.
- `download_wfs_sources.py` Downloade aktuellen Snapshot von allen WFS Quellen. Für Demonstrationszwecke. In der App sollten ab und zu aktuelle Daten verwendet werden (Beispiel: Aktuelle Verkehrslage)
- `export_osm_data.py` Exportiere alle Fahrrad-bezogenen Features aus OpenStreetMap Daten
- `generate_accident_black_spots.py` Generiere Unfallschwerpunkte
- `prepare_files_for_presentation.py` Lade alle GeoJSON Dateien in ArcGIS

## Wetter Daten
- Deutscher Wetter Dienst
  - WMS: https://maps.dwd.de/geoserver/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetCapabilities
  - WCS: https://maps.dwd.de/geoserver/wcs?SERVICE=WCS&VERSION=2.0.0&REQUEST=GetCapabilities
  - `Deutsches Regenradar (mit time Attribut)`: https://maps.dwd.de/geoserver/dwd/wms?service=WMS&version=1.1.0&request=GetMap&layers=dwd%3ANiederschlagsradar&bbox=-543.462%2C-4808.645%2C556.538%2C-3608.645&width=703&height=768&srs=EPSG%3A1000001&styles=&format=image%2Fjpeg&time=2022-09-18T12:00:00.000Z


## Quellen

### <a href="https://geoportal-hamburg.de/geo-online/">Geoportal Hamburg</a>
- `/data/generated/wfs/stadt_rad`: StadtRAD Stationen Hamburg
  - `Lizenz`: https://www.govdata.de/dl-de/by-2-0
  - Download mit `download_wfs_sources.py`
  - `iot hamburg url`:https://iot.hamburg.de/v1.0/Things?$filter=Datastreams/properties/serviceName%20eq%20%27HH_STA_StadtRad%27&$count=true&$expand=Locations,Datastreams($expand=Observations($orderby=phenomenonTime%20desc;$top=3),Sensor,ObservedProperty)
  - `GetCapabilities`: https://geodienste.hamburg.de/HH_WFS_Stadtrad?SERVICE=WFS&REQUEST=GetCapabilities
  - `GetFeature`: https://geodienste.hamburg.de/HH_WFS_Stadtrad?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&typename=de.hh.up:stadtrad_stationen&outputFormat=application/geo%2bjson&srsname=EPSG:4326
- `/data/generated/wfs/bike_count`: Fahrradzählstellen
  - `Lizenz`: https://www.govdata.de/dl-de/by-2-0
  - Download mit `download_wfs_sources.py`
  - `iot hamburg url`: https://iot.hamburg.de/v1.0/Things?$filter=Datastreams/properties/serviceName%20eq%20%27HH_STA_HamburgerRadzaehlnetz%27%20and%20Datastreams/properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlfeld_5-Min%27&$count=true&$expand=Datastreams($filter=properties/layerName%20eq%20%27Anzahl_Fahrraeder_Zaehlfeld_5-Min%27;$expand=Observations($top=10;$orderby=phenomenonTime%20desc))
  - `GetCapabilities`: https://geodienste.hamburg.de/HH_WFS_Harazaen?SERVICE=WFS&REQUEST=GetCapabilities
  - `GetFeature`: https://geodienste.hamburg.de/HH_WFS_Harazaen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=de.hh.up:zaehlstellen_daten&outputFormat=application/geo%2Bjson&srsname=EPSG:4326
  - mögliche `layerName` Werte: 
    - Anzahl_Fahrraeder_Zaehlfeld_5-Min 
    - Anzahl_Fahrraeder_Zaehlfeld_15-Min 
    - Anzahl_Fahrraeder_Zaehlfeld_1-Tag 
    - Anzahl_Fahrraeder_Zaehlstelle_15-Min 
    - Anzahl_Fahrraeder_Zaehlstelle_1-Stunde 
    - Anzahl_Fahrraeder_Zaehlstelle_1-Tag 
    - Anzahl_Fahrraeder_Zaehlstelle_1-Woche
- `data/generated/wfs/bike_and_ride`: 
  - `Lizenz`: https://www.govdata.de/dl-de/by-2-0
  - Download mit `download_wfs_sources.py`
  - `GetCapabilities`: https://geodienste.hamburg.de/HH_WFS_Bike_und_Ride?SERVICE=WFS&REQUEST=GetCapabilities
  - `GetFeature`: https://geodienste.hamburg.de/HH_WFS_Bike_und_Ride?SERVICE=WFS&REQUEST=GetFeature&outputFormat=application/geo%2Bjson&version=2.0.0&typeName=de.hh.up:bike_und_ride&srsname=EPSG:4326

### <a href="https://geoportal-hamburg.de/geo-online/">Geoportal Vekehr Hamburg</a>
- `data/generated/wfs/traffic`: Aktuelle Verkehrsdaten
  - `Lizenz`: https://www.govdata.de/dl-de/by-2-0
  - Download mit `download_wfs_sources.py`
  - `GetCapabilities`: https://geodienste.hamburg.de/HH_WFS_Verkehrslage?SERVICE=WFS&REQUEST=GetCapabilities
  - `GetFeature`: https://geodienste.hamburg.de/HH_WFS_Verkehrslage?SERVICE=WFS&REQUEST=GetFeature&typeName=de.hh.up:verkehrslage&version=2.0.0&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326
- `data/generated/wfs/construction_sides`: Aktuelle Baustellen
  - `Lizenz`: https://www.govdata.de/dl-de/by-2-0
  - Download mit `download_wfs_sources.py`
  - `GetCapabilities`: https://geodienste.hamburg.de/HH_WFS_Baustellen?SERVICE=WFS&REQUEST=GetCapabilities
  - `GetFeature`: https://geodienste.hamburg.de/HH_WFS_Baustellen?SERVICE=WFS&REQUEST=GetFeature&typeName=de.hh.up:tns_steckbrief_visualisierung&version=2.0.0&OUTPUTFORMAT=application/geo%2Bjson

### <a href="https://suche.transparenz.hamburg.de/">Transparenzportal Hamburg</a>
- `data/generated/wfs/bike_air_station`: Fahrradluftstationen
  - `Lizenz`: https://www.govdata.de/dl-de/by-2-0
  - Download mit `download_wfs_sources.py`
  - `GetCapabilities`: https://geodienste.hamburg.de/HH_WFS_Fahrradluftstationen?SERVICE=WFS&REQUEST=GetCapabilities
  - `GetFeature`: https://geodienste.hamburg.de/HH_WFS_Fahrradluftstationen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=de.hh.up:fahrradluftstationen&OUTPUTFORMAT=application/geo%2Bjson



### Sonstige
- `/data/open-street-map`: OpenStreetMap Daten Hamburg
  - https://download.geofabrik.de/europe/germany/hamburg.html
- `/data/open-street-map-dresden`: OpenStreetMap Daten Dresden: 
  - https://download.geofabrik.de/europe/germany/sachsen.html
- `/data/generated/accidents` Unfalldaten: 
  - `Lizenz`: https://www.govdata.de/dl-de/by-2-0
  - https://unfallatlas.statistikportal.de/
  - Download mit `generate_accident_black_spots.py`
- `/data/boundary` Boundary-Dateien: 
  - http://opendatalab.de/projects/geojson-utilities/