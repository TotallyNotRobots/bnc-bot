## 0.1.0 (2025-12-05)

### BREAKING CHANGE

- Technically this removes a feature, but it wasn't utilized by the existing code anyways and only caused trouble

### Feat

- add docker image, allow setting datadir and config file from cli
- add support for python 3.14
- **logging**: Add additional logging to assist with debugging #85
- add support for python 3.13

### Fix

- **deps**: update dependency pydantic to v2.12.5
- **deps**: update dependency async-irc to v0.3.0
- **deps**: update dependency pydantic to v2.12.4
- **core**: remove broken/inconsistent restart handler
- **nickserv**: don't deadlock nickserv lookups if one fails
- **nickserv**: correcrtly match nickserv info section for account creation time in anope 2.1
- **deps**: update dependency pydantic to v2.12.3
- correct workflow permissions for lockfiles updates
- update pre-commit updater with fixes from other repos
- update pre-commit updater with fixes from other repos
- drop support for EOL Python 3.9
- **deps**: update dependency pydantic to v2.12.2
- **deps**: update aiofiles to v25
- **main**: use aiofiles to write PID file
- **lint**: correct linting issues
- update ref to devcontainer features

### Refactor

- fix ruff issues
- remove runtime asserts
