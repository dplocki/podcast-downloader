import os
import json
from argparse import ArgumentParser


def merge_parameters_collection(default: dict, *args) -> dict:
    result = dict(default)

    for arg in args:
        for key, value in arg.items():
            result[key] = value

    return result


def load_configuration_file(file_path: str) -> dict:
    if not os.path.isfile(file_path):
        raise Exception(f'Cannot read from configuration file "{file_path}"')

    with open(file_path, mode="r", encoding="utf-8") as json_file:
        return json.load(json_file)


def parse_argv(parser: ArgumentParser, args=None):
    return {key: value for key, value in vars(parser.parse_args(args)).items() if value}
