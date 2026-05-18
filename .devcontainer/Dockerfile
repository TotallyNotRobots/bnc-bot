FROM mcr.microsoft.com/devcontainers/python:3.14@sha256:882b17d068262c7af4300180ead0ee14423d2c03393778c92435b0ca642dea07

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
