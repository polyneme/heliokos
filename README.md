# heliokos
A knowledge organization system (KOS) service for Heliophysics

# testing

```bash
# Example: run linting and tests for single module
tox run -e lint,py311 -- src/heliokos/domain/core.py
# Example: run all tests
tox
```

# release process

1. bump `version` in [pyproject.toml](/pyproject.toml).
2. git commit and push
3. git tag v$(pyproject.toml.version) # e.g. `git tag v0.0.5`.
4. python -m build
5. python -m twine upload dist/*
