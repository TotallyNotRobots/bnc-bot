FROM python:3.14-alpine@sha256:601e99e090cb08c2784a42395487709500bc39930307fe72f3f11a8f3c430762

COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl

VOLUME ["/data", "/config"]

ENTRYPOINT [ "/usr/local/bin/bnc-bot" ]
CMD [ "--data-dir=/data", "--config=/config/config.json" ]
