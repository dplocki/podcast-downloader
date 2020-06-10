# Podcast downloader

## Installing project

The project is using [pipenv](https://github.com/pypa/pipenv).

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

## Uploading the package into repository

```bash
python setup.py sdist bdist_wheel
twine upload --repository pypi dist/*
```
