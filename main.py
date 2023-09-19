import logging

import export_osm_data
import export_wfs_data
import export_accidents
import merge_bicycle_rental
import generate_accident_hot_spots

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s][%(filename)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def main():
    export_wfs_data.main()
    export_osm_data.main()
    merge_bicycle_rental.main()
    export_accidents.main()
    generate_accident_hot_spots.main()

if __name__ == "__main__":
    main()
