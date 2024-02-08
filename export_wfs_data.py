import json
import logging
import requests
import time

urls = {
    # ERROR <No service with identifier 'wfs_hh_bike_und_ride' available.>
    # "bike_and_ride": "https://geodienste.hamburg.de/HH_WFS_Bike_und_Ride?SERVICE=WFS&REQUEST=GetFeature&outputFormat=application/geo%2Bjson&version=2.0.0&typeName=de.hh.up:bike_und_ride&srsname=EPSG:4326",
    "traffic": "https://geodienste.hamburg.de/HH_WFS_Verkehrslage?SERVICE=WFS&REQUEST=GetFeature&typeName=de.hh.up:verkehrslage&version=2.0.0&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326",
    "construction_sites": "https://geodienste.hamburg.de/HH_WFS_Baustellen?SERVICE=WFS&REQUEST=GetFeature&typeName=de.hh.up:tns_steckbrief_visualisierung&version=2.0.0&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326",
    "stadt_rad": "https://geodienste.hamburg.de/HH_WFS_Stadtrad?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&typename=de.hh.up:stadtrad_stationen&outputFormat=application/geo%2bjson&srsname=EPSG:4326",
    # INVALID URL 404
    # "bike_count": "https://geodienste.hamburg.de/HH_WFS_Harazaen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=de.hh.up:zaehlstellen_daten&outputFormat=application/geo%2Bjson&srsname=EPSG:4326",
    "bike_air_station": "https://geodienste.hamburg.de/HH_WFS_Fahrradluftstationen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=de.hh.up:fahrradluftstationen&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326",
    "static_green_waves": "https://geodienste.hamburg.de/HH_WFS_ITS_Dienste_Hamburg?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typeName=de.hh.up:its_iot_registry&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326&Filter=%3Cogc:Filter%20xmlns:ogc=%22http://www.opengis.net/ogc%22%3E%3Cogc:PropertyIsEqualTo%3E%3Cogc:PropertyName%3Epurpose_id%3C/ogc:PropertyName%3E%3Cogc:Literal%3E14%3C/ogc:Literal%3E%3C/ogc:PropertyIsEqualTo%3E%3C/ogc:Filter%3E",
    "prio_change": "https://geodienste.hamburg.de/HH_WFS_ITS_Dienste_Hamburg?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typeName=de.hh.up:its_iot_registry&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326&Filter=%3Cogc:Filter%20xmlns:ogc=%22http://www.opengis.net/ogc%22%3E%3Cogc:PropertyIsEqualTo%3E%3Cogc:PropertyName%3Epurpose_id%3C/ogc:PropertyName%3E%3Cogc:Literal%3E15%3C/ogc:Literal%3E%3C/ogc:PropertyIsEqualTo%3E%3C/ogc:Filter%3E",
    "velo_routes": "https://geodienste.hamburg.de/HH_WFS_Velorouten?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326&typename=de.hh.up:velorouten"
}

OUTPUT_DIRECTORY = "data/generated/wfs/"

def main():
    """
    Download and store GeoJSON data from Hamburg's web feature services.

    This function iterates through the specified URLs of the WFS, exports the data as GeoJSON from each WFS,
    and stores it in the `OUTPUT_DIRECTORY` with filenames corresponding to the service names.

    The geojson crs will be EPSG:4326.
    """
    for key, value in urls.items():
        logging.info(f"Downloading '{value}' -> '{key}.geojson'")
        r = requests.get(url=value)
        retry_count = 1
        valid_json = False
        try:
            result_json = r.json()
            valid_json = True
        except:
            valid_json = False
        while r.status_code != 200 or not valid_json:
            logging.warning(f"Failed to download '{value}'")
            logging.info(f"Retrying {retry_count}/5 in 10 seconds ...")
            time.sleep(10)
            r = requests.get(url=value)
            try:
                result_json = r.json()
                valid_json = True
            except:
                valid_json = False
            retry_count += 1
            if retry_count > 5:
                raise Exception(f"Failed to download '{value}' after 5 retries.")
        
        save(key, result_json)
            
def save(key, result_json):
    save_v2(key, result_json)
    with open(f"{OUTPUT_DIRECTORY}/{key}.geojson", "w") as file:
        json.dump(result_json, file)
        
def save_v2(key, result_json):
    for i in range(0, len(result_json['features'])):
        result_json['features'][i]['properties']['id'] = f"{key}-{i}"
    with open(f"{OUTPUT_DIRECTORY}/{key}_v2.geojson", "w") as file:
        json.dump(result_json, file)

if __name__ == "__main__":
    main()
