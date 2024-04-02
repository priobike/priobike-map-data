FROM python:3.9 AS builder

ARG CACHE_DATE=1970-01-01

COPY *.py ./
COPY ./requirements.txt ./

RUN mkdir -p /data/generated/wfs
RUN mkdir -p /data/generated/osm
RUN mkdir -p /data/generated/accidents
RUN mkdir -p /data/temp
RUN mkdir -p /data/boundary
RUN mkdir -p /data/accidents

RUN python -m pip install -r requirements.txt
RUN python main.py

RUN rm -r /data/temp

# We cant differentiate between staging (main), beta/production (stable) or release (release) here.
# Therefore we just use the release tag since it is the most stable one.
FROM bikenow.vkw.tu-dresden.de/priobike/priobike-nginx:release AS runner

WORKDIR /usr/share/nginx/html/
COPY --from=builder ./data/accidents/ ./
COPY --from=builder ./data/generated/accidents/ ./
COPY --from=builder ./data/generated/osm/ ./
COPY --from=builder ./data/generated/wfs/ ./