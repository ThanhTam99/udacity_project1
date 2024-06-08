from collections import Iterable
from itertools import groupby


def group_by(iterable: Iterable, key_selector, value_selector=None):
    result = dict()

    for key, values in groupby(iterable, key_selector):
        mapped_values = values if value_selector is None else map(
            value_selector, values)
        if key in result:
            result[key].append(mapped_values)
        else:
            result[key] = list(mapped_values)

    return result


def map_field_names(keys: tuple, fields_names: list):
    result = {}

    for index in range(len(fields_names)):
        field_name = fields_names[index]
        key_value = keys[index]

        result[field_name] = key_value

    return result


def group_by_multiple_key(
    iterable: Iterable,
    key_selector,
    value_selector,
    keys_field_names,
    value_field_name="values",
):
    result = []

    for key, original_values in group_by(iterable, key_selector).items():
        result_item = map_field_names(key, keys_field_names)
        mapped_values = map(value_selector, original_values)
        result_item[value_field_name] = list(mapped_values)

        result.append(result_item)

    return result
