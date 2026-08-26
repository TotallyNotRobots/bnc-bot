FROM mcr.microsoft.com/devcontainers/python:3.14@sha256:42ca12ea426dbf5c99173b283665da6f1445a8b947e8ad530c73d0c27e05c16d

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
