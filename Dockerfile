FROM python:3.14-alpine@sha256:2a77c2640cc80f5506babd027c883abc55f04d44173fd52eeacea9d3b978e811

COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl

VOLUME ["/data", "/config"]

ENTRYPOINT [ "/usr/local/bin/bnc-bot" ]
CMD [ "--data-dir=/data", "--config=/config/config.json" ]
