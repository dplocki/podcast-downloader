# Podcast downloader

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Installing project

The project is using [pipenv](https://github.com/pypa/pipenv).

Setup the pipenv envirement (required only once).

```bash
pipenv --python 3.8
```

Install all dependencies for a project (including dev):

```bash
pipenv install --dev
```

## Develop on package

To install package from source control use the fallowing command:

```bash
pip install -e .
```

## Tests

After installing the package you run tests

```bash
python -m unittest discover -s tests -p *_test.py
```

## E2e tests

Running:

```bash
pytest e2e
```

## Uploading the package into repository

```bash
python setup.py sdist bdist_wheel
twine upload --repository pypi dist/*
```

## Black

Run code formatter:

```bash
black .
```
