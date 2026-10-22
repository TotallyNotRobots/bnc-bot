FROM python:3.15-alpine@sha256:d44b1254cb92329418d164b22b20d86bbd3869d48e80e09e476531a409a728bb

COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl

VOLUME ["/data", "/config"]

ENTRYPOINT [ "/usr/local/bin/bnc-bot" ]
CMD [ "--data-dir=/data", "--config=/config/config.json" ]
