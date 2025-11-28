FROM mcr.microsoft.com/devcontainers/python:3.14@sha256:9ad909ce6d84fdcbc7b337ce6d04aa630b766de78074fe64232f6f836f79f0f5

RUN \
    pipx uninstall mypy \
    && pipx uninstall pylint \
    && pipx uninstall pytest \
    && pipx uninstall flake8 \
    && pipx uninstall black \
    && pipx install commitizen \
    && pip install -U hatch hatch-containers hatch-pip-compile

RUN su vscode -c "hatch config set dirs.env.virtual /home/vscode/.virtualenvs"

ENV SHELL=/bin/bash
