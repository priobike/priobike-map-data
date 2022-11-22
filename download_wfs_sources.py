import json

import requests

urls = {
    "bike_and_ride": "https://geodienste.hamburg.de/HH_WFS_Bike_und_Ride?SERVICE=WFS&REQUEST=GetFeature&outputFormat=application/geo%2Bjson&version=2.0.0&typeName=de.hh.up:bike_und_ride&srsname=EPSG:4326",
    "traffic": "https://geodienste.hamburg.de/HH_WFS_Verkehrslage?SERVICE=WFS&REQUEST=GetFeature&typeName=de.hh.up:verkehrslage&version=2.0.0&OUTPUTFORMAT=application/geo%2Bjson&srsname=EPSG:4326",
    "construction_sites": "https://geodienste.hamburg.de/HH_WFS_Baustellen?SERVICE=WFS&REQUEST=GetFeature&typeName=de.hh.up:tns_steckbrief_visualisierung&version=2.0.0&OUTPUTFORMAT=application/geo%2Bjson",
    "stadt_rad": "https://geodienste.hamburg.de/HH_WFS_Stadtrad?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&typename=de.hh.up:stadtrad_stationen&outputFormat=application/geo%2bjson&srsname=EPSG:4326",
    "bike_count": "https://geodienste.hamburg.de/HH_WFS_Harazaen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=de.hh.up:zaehlstellen_daten&outputFormat=application/geo%2Bjson&srsname=EPSG:4326",
    "bike_air_station": "https://geodienste.hamburg.de/HH_WFS_Fahrradluftstationen?SERVICE=WFS&VERSION=1.1.0&REQUEST=GetFeature&typename=de.hh.up:fahrradluftstationen&OUTPUTFORMAT=application/geo%2Bjson",
}


def main():
    for key, value in urls.items():
        r = requests.get(url=value)
        result_json = r.json()
        print("Downloading " + key)
        with open("data/generated/wfs/" + str(key) + ".geojson", "w") as file:
            json.dump(result_json, file)


if __name__ == "__main__":
    main()
