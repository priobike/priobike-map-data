import datetime
import requests
from urllib.parse import urlencode
import time
import json
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s][download_accidents] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)

BASE_URL = "https://www.gis-idmz.nrw.de/arcgis/rest/services/stba/unfallstatistik/MapServer/100/query"

MIN_YEAR = 2016
MAX_YEAR = datetime.date.today().year

MAPPING_ACCIDENTS = {
    "Unfall mit Leichtverletzten": 1,
    "Unfall mit Schwerverletzten": 2,
    "Unfall mit Getöteten": 3
}

total_max_x = 606885.400445
total_max_y = 5957071.658003
total_min_x = 526588.190788
total_min_y = 5913195.599347

parts_x = 15
parts_y = 10

increase_x = (total_max_x - total_min_x) / parts_x
increase_y = (total_max_y - total_min_y) / parts_y

SLEEP_TIME = 1

spatial_reference = {
    "wkid": 25832
}

fields = [
    "OBJECTID", "Unfallkategorie", "PKW",
    "Fußgänger", "Kraftrad", "Rad", "GKFZ", "Sonstige"
]


def generate_url(options, current_year):
    geometry = {
        "spatialReference": spatial_reference,
        "xmin": options["x_min"],
        "ymin": options["y_min"],
        "xmax": options["x_max"],
        "ymax": options["y_max"]
    }
    where_clause = f"UJAHR={current_year}"
    params = {
        "f": "json",
        "geometry": str(geometry),
        "outFields": ','.join(fields),
        "spatialRel": "esriSpatialRelContains",
        "where": where_clause,
        "geometryType": "esriGeometryEnvelope",
        "inSR": "25832",
        "outSR": "25832"
    }
    
    encoded_params = urlencode(params)
    return f"{BASE_URL}?{encoded_params}"


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


def get_urls():
    all_urls = {}
    for year in range(MIN_YEAR, MAX_YEAR):
        all_urls[year] = generate_urls(year)
    return all_urls


def save_to_file(data, file_name: str):
    with open(file_name, "w") as file:
        logging.info(f"Saving {file_name} ...")
        json.dump(data, file)


def execute_requests_of_year(all_urls, year):
    responses = []
    current_step = 0
    total_steps = parts_y * parts_x * (MAX_YEAR - MIN_YEAR)
    for url in all_urls[year]:

        if current_step % 10 == 0:
            remaining_steps = total_steps - current_step
            time_remaining = convert_seconds_to_string(remaining_steps * SLEEP_TIME)
            logging.debug(f"{int(current_step/10)} / {int(total_steps / 10)} - {time_remaining}")
        
        response = requests.get(url=url)
        responses.append(response.json())
        time.sleep(SLEEP_TIME)
        current_step += 1
    return responses


def add_attribute_category_accident(geojson):
    for i in range(0, len(geojson["fields"])):
        if geojson["fields"][i]["name"] == "Unfallkategorie":
            geojson["fields"][i]["type"] = "esriFieldTypeSmallInteger"


def process_responses(responses, total_features, year):
    dict_features = {}
    for response in responses:
        for feature in response["features"]:
            if feature["attributes"]["Rad"] == 0:
                continue
            feature["attributes"]["Jahr"] = year
            feature["attributes"]["OBJECTID"] = str(feature["attributes"]["OBJECTID"]) + "_" + str(year)
            feature["attributes"]["Unfallkategorie"] = MAPPING_ACCIDENTS[feature["attributes"]["Unfallkategorie"]]

            # save by objectid to filter duplicates
            dict_features[feature["attributes"]["OBJECTID"]] = feature
            total_features[feature["attributes"]["OBJECTID"]] = feature
    return dict_features


def main():
    total_geojson = None
    total_features = {}
    
    all_urls = get_urls()

    for year in range(MIN_YEAR, MAX_YEAR):
        logging.info(f"YEAR: {year}")

        responses = execute_requests_of_year(all_urls, year)
        if total_geojson is None:
            total_geojson = responses[0]
            add_attribute_category_accident(total_geojson)
        dict_features = process_responses(responses, total_features, year)

        
        geojson = responses[0]
        geojson["features"] = []
        add_attribute_category_accident(geojson)

        for value in dict_features.values():
            geojson["features"].append(value)

        save_to_file(geojson, f"./data/accidents/accidents_{year}.geojson")
    
    for value in total_features.values():
        total_geojson["features"].append(value)

    save_to_file(total_geojson, "./data/generated/accidents/accidents_total.geojson")


if __name__ == "__main__":
    main()