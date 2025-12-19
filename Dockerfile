FROM python:3.14-alpine@sha256:7af51ebeb83610fb69d633d5c61a2efb87efa4caf66b59862d624bb6ef788345

COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl

VOLUME ["/data", "/config"]

ENTRYPOINT [ "/usr/local/bin/bnc-bot" ]
CMD [ "--data-dir=/data", "--config=/config/config.json" ]
