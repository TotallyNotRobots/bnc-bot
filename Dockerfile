FROM python:3.14-alpine@sha256:5f1ff369fb05e17a9b569a7d92488607c49514e958101ca8a2290fd0fa52cdaf

COPY dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl

VOLUME ["/data", "/config"]

ENTRYPOINT [ "/usr/local/bin/bnc-bot" ]
CMD [ "--data-dir=/data", "--config=/config/config.json" ]
