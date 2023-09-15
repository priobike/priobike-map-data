FROM python:3.9 AS builder

ARG CACHE_DATE=1970-01-01

COPY ./export_wfs_data.py ./
COPY ./download_accidents.py ./
COPY ./export_osm_data.py ./
COPY ./generate_accident_hot_spots.py ./
COPY ./merge_bicycle_rental.py ./
COPY ./requirements.txt ./

RUN mkdir -p /data/generated/wfs
RUN mkdir -p /data/generated/osm
RUN mkdir -p /data/generated/accidents
RUN mkdir -p /data/temp
RUN mkdir -p /data/boundary
RUN mkdir -p /data/accidents

COPY ./data/boundary/hamburg_boundary.geojson ./data/boundary/hamburg_boundary.geojson

RUN python -m pip install -r requirements.txt

RUN python export_wfs_data.py
RUN python export_osm_data.py
RUN python download_accidents.py
RUN python generate_accident_hot_spots.py
RUN python merge_bicycle_rental.py

RUN rm -r /data/temp

FROM nginx AS runner

WORKDIR /usr/share/nginx/html/
COPY --from=builder ./data/accidents/ ./
COPY --from=builder ./data/generated/accidents/ ./
COPY --from=builder ./data/generated/osm/ ./
COPY --from=builder ./data/generated/wfs/ ./