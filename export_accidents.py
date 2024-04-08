import requests
import datetime
import logging
import zipfile
from pyogrio import read_dataframe
from pyogrio.errors import DataSourceError
import pandas as pd

MIN_YEAR = 2016
MAX_YEAR = datetime.date.today().year

def get_geojson_path(year):
    return f"./data/accidents/accidents_{year}.geojson"

def get_shp_path(year):

    # for some reason 2016 has another _ in the .shp file name
    if year == 2016:
        return f"{get_zip_extract_directory_path(year)}/Shapefile/Unfaelle_{year}_LinRef.shp"
    
    # after 2021 the accidents in the zip file are stored in a folder called "shp"
    if year > 2021:
        return f"{get_zip_extract_directory_path(year)}/shp/Unfallorte{year}_LinRef.shp"

    # for years 2017 to 2020
    return f"{get_zip_extract_directory_path(year)}/Shapefile/Unfallorte{year}_LinRef.shp"

def get_zip_path(year):
    return f"./data/temp/{year}.zip"

def get_zip_extract_directory_path(year):
    return f"./data/temp/{year}"

def get_url_by_year(year):
    #https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte2022_EPSG25832_CSV.zip
    return f"https://www.opengeodata.nrw.de/produkte/transport_verkehr/unfallatlas/Unfallorte{year}_EPSG25832_Shape.zip"

def download_zip(year):
    logging.info("Downloading .zip file.")
    url = get_url_by_year(year)
    output_file = get_zip_path(year)
    response = requests.get(url)

    if response.status_code != 200:
        return False

    with open(output_file, 'wb') as file:
        file.write(response.content)
    return True

def extract_zip(year):
    logging.info("Extracting .zip file.")
    zip_file_path = get_zip_path(year)
    extracted_dir_path = get_zip_extract_directory_path(year)

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_dir_path)


def process_shp_file_of_year(year):
    logging.info("Reading .shp file.")

    shp_file_path = get_shp_path(year)
    
    shp_file = None
    try:
        # using pyogrio for better performance while reading large .shp files
        shp_file = read_dataframe(shp_file_path)
    except DataSourceError:
        raise FileNotFoundError(f"The .shp file with the accident data for the year {year} could not be found. It is very likely that the 'Statistische Ämter' have changed the structure of the .zip files (containing the .shp file) they offer for download. This has already happened in the past. Please compare the structure of the folder `data/temp/{year}` with the given path {shp_file_path} (from get_shp_path({year})). Check the README.md for more information.")

    logging.info("Selecting features where bike was involved.")
    shp_file = shp_file[shp_file["IstRad"] !=  "0"]
    logging.info("Convert CRS to EPSG:4326")
    shp_file = shp_file.to_crs("EPSG:4326")
    return shp_file
    

def process_year(year):

    success = download_zip(year)
    if not success:
        logging.error(f"Failed to download .shp file for year: {year}")
        return None
    
    extract_zip(year)
    accidents_of_year = process_shp_file_of_year(year)

    # for some reason there is no OBJECTID column in 2018
    if year != 2018:
        accidents_of_year = accidents_of_year.drop('OBJECTID', axis=1)

    accidents_of_year.to_file(get_geojson_path(year), driver="GeoJSON")
    return accidents_of_year


def main():

    accidents = []

    for year in range(MIN_YEAR, MAX_YEAR + 1):
        logging.info(f"Processing year: {year} / {MAX_YEAR}")
        accidents_of_year = process_year(year)
        if accidents_of_year is None:
            continue
        accidents.append(accidents_of_year)

    accidents_total = pd.concat(accidents, ignore_index=True)
    accidents_total.to_file("./data/generated/accidents/accidents_total.geojson", driver="GeoJSON")
    

if __name__ == "__main__":
    main()





