FROM python:3.14-alpine@sha256:d7fb7df19ca613dcebf0969d0ab2b04bb35e95f325c104da1b1718162468f6de

COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl

VOLUME ["/data", "/config"]

ENTRYPOINT [ "/usr/local/bin/bnc-bot" ]
CMD [ "--data-dir=/data", "--config=/config/config.json" ]
