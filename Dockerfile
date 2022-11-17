FROM python:3.9 AS builder

COPY download_wfs_sources.py ./

CMD ["python", "./download_wfs_sources.py"]

FROM nginx AS runner

COPY --from=builder ./data/generated/wfs ./