def merge_parameters_collection(default: dict, *args):
    result = dict(default)

    for arg in args:
        for key, value in arg.items():
            result[key] = value

    return result
