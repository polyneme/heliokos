# heliokos
A knowledge organization system (KOS) service for Heliophysics

# development

`git clone` this repository, and in the root directory,
```bash
pip install -e .
```

To start the Web server for development:
```bash
uvicorn heliokos.ui.main:app --reload
```

# testing

```bash
# Example: run linting and tests for single module
tox run -e lint,py311 -- tests/test_units.py
# Example run single test by name
tox run -e py311 -- -k test_harmonizing_two_concept_schemes
# Example: run all tests
tox
```

# release process

1. bump `version` in [pyproject.toml](/pyproject.toml).
2. git commit
3. git tag v$(pyproject.toml.version) # e.g. `git tag v0.0.5`.
4. python -m build
5. python -m twine upload dist/*
6. rm -rf dist
