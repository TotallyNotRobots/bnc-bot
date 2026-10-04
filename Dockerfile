FROM python:3.14-alpine@sha256:f6a589d43c42b9e7f7dc67a12d37132491f362859a5d750607710cc56da3bc72

COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl

VOLUME ["/data", "/config"]

ENTRYPOINT [ "/usr/local/bin/bnc-bot" ]
CMD [ "--data-dir=/data", "--config=/config/config.json" ]
