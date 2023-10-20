# heliokos
A knowledge organization system (KOS) service for Heliophysics.

# use

Executable [functional tests](tests/test_functions.py) describe target use cases. Currently, the first two tests pass,
so you can follow their bodies as usage examples. The rest of the functional test suite can be considered a roadmap
for this tool.

You can `pip install heliokos` to get the last-released version,
or you can `git clone` this repository and `pip install .` to build the tool using the current `main`-branch head.

# development

`git clone` this repository, and in the root directory,
```bash
pip install -e .
```

## bill of materials (BOM)

|name|description|website|origin|
|----|-----------|-------|------|
|fastapi|API framework|https://github.com/tiangolo/fastapi | https://pypi.org/project/fastapi |
|rdflib|RDF graph library|https://github.com/RDFLib/rdflib | https://pypi.org/project/rdflib |
|toolz|utility functions library|https://github.com/pytoolz/toolz | https://pypi.org/project/toolz |


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
