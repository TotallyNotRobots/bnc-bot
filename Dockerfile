FROM python:3.14-alpine@sha256:05b2b8b732ecd268fee8727a369f936f022d1321b59befd13c30ede22769dcdc

COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl

VOLUME ["/data", "/config"]

ENTRYPOINT [ "/usr/local/bin/bnc-bot" ]
CMD [ "--data-dir=/data", "--config=/config/config.json" ]
