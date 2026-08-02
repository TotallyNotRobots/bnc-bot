FROM mcr.microsoft.com/devcontainers/python:3.14@sha256:f04a1e9c29e371436d6086908eed22ac0ba087bae0f8edb826838283cf3d1726

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
