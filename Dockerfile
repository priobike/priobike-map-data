FROM python:3.9 AS builder

COPY ./download_wfs_sources.py ./
RUN mkdir -p /data/generated/wfs

RUN python -m pip install requests
RUN python download_wfs_sources.py

FROM nginx AS runner

WORKDIR /usr/share/nginx/html/
COPY --from=builder ./data/generated/wfs/ ./
COPY ./data/generated/accidents/accident_hot_spots.geojson ./