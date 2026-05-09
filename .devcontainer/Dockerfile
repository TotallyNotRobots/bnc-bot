FROM mcr.microsoft.com/devcontainers/python:3.14@sha256:9e51c13505754efe79dd4a0b1a29523d3854090dabb8add3f3fa642ea3c98fad

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
