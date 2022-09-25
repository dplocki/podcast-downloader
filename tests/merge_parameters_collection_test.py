import unittest

from podcast_downloader.parameters import merge_parameters_collection


class TestMergeParametersCollection(unittest.TestCase):
    def test_should_return_default_if_args_is_empty(self):
        # Assign
        default = {"a": 1}

        # Act
        result = merge_parameters_collection(default)

        # Assert
        self.assertDictEqual(result, default, "Should return the same dictionary")

    def test_should_rewrite_collection_values(self):
        # Assign
        default = {"a": 1, "b": 2}
        new_values = {"b": 3}
        expected = {"a": 1, "b": 3}

        # Act
        result = merge_parameters_collection(default, new_values)

        # Assert
        self.assertDictEqual(result, expected, "Should return merged directory")

    def test_should_rewrite_from_many_collection_values(self):
        # Assign
        default = {"a": 1, "b": 2, "c": 3, "d": 4}

        new_values_1 = {"a": 11}
        new_values_2 = {"b": 22}
        new_values_3 = {"c": 33}

        expected = {"a": 11, "b": 22, "c": 33, "d": 4}

        # Act
        result = merge_parameters_collection(
            default, new_values_1, new_values_2, new_values_3
        )

        # Assert
        self.assertDictEqual(result, expected, "Should return merged directory")

    def test_should_collection_be_written_by_themselves(self):
        # Assign
        default = {"a": 1, "b": 2, "c": 3, "d": 4}

        new_values_1 = {"a": 11, "b": 22}
        new_values_2 = {"a": 22}
        new_values_3 = {"c": 33}

        expected = {"a": 22, "b": 22, "c": 33, "d": 4}

        # Act
        result = merge_parameters_collection(
            default, new_values_1, new_values_2, new_values_3
        )

        # Assert
        self.assertDictEqual(result, expected, "Should return merged directory")
