FROM python:3.9 AS builder

ARG CACHE_DATE=1970-01-01

COPY ./download_wfs_sources.py ./
COPY ./export_osm_data_open_source.py ./
RUN mkdir -p /data/generated/wfs
RUN mkdir -p /data/temp
RUN mkdir -p /data/generated/osm_os

RUN python -m pip install requests
RUN python -m pip install geopandas

RUN python download_wfs_sources.py
RUN python export_osm_data_open_source.py

RUN rm -r /data/temp

FROM nginx AS runner

WORKDIR /usr/share/nginx/html/
COPY ./data/generated/accidents/ ./
COPY --from=builder ./data/generated/osm_os/ ./
COPY --from=builder ./data/generated/wfs/ ./