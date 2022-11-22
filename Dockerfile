FROM python:3.9 AS builder

COPY ./download_wfs_sources.py ./
RUN mkdir -p /data/generated/wfs

CMD ["download_wfs_sources.py"]

FROM nginx AS runner

COPY --from=builder ./data/generated/wfs/ ./
COPY ./data/generated/accidents/accident_hot_spots.geojson ./

EXPOSE 8080
