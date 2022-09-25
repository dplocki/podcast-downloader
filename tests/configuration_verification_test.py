import unittest

from podcast_downloader import configuration


class TestConfigurationVerification(unittest.TestCase):
    def test_check_for_name_in_podcast_subgroup(self):
        # Assign
        config = {configuration.CONFIG_PODCASTS: [{}]}

        # Act
        is_valid_result, message = configuration.configuration_verification(config)

        # Assert
        self.assertFalse(
            is_valid_result, "Validator should notice missing 'name' field in podcast"
        )
        self.assertIsNotNone(message, "The validator should return message")

    def test_check_for_path_in_podcast_subgroup(self):
        # Assign
        config = {
            configuration.CONFIG_PODCASTS: [
                {configuration.CONFIG_PODCASTS_NAME: "missing path"}
            ]
        }

        # Act
        is_valid_result, message = configuration.configuration_verification(config)

        # Assert
        self.assertFalse(
            is_valid_result, "Validator should notice missing 'path' field in podcast"
        )
        self.assertIsNotNone(message, "The validator should return message")

    def test_check_for_rss_link_in_podcast_subgroup(self):
        # Assign
        config = {
            configuration.CONFIG_PODCASTS: [
                {
                    configuration.CONFIG_PODCASTS_NAME: "missing path",
                    configuration.CONFIG_PODCASTS_PATH: "/podcast/directory",
                }
            ]
        }

        # Act
        is_valid_result, message = configuration.configuration_verification(config)

        # Assert
        self.assertFalse(
            is_valid_result,
            "Validator should notice missing 'rss_link' field in podcast",
        )
        self.assertIsNotNone(message, "The validator should return message")

    def test_check_for_valid_configuration(self):
        # Assign
        config = {
            configuration.CONFIG_PODCASTS: [
                {
                    configuration.CONFIG_PODCASTS_NAME: "missing path",
                    configuration.CONFIG_PODCASTS_PATH: "/podcast/directory",
                    configuration.CONFIG_PODCASTS_RSS_LINK: "https://podcasts/mine",
                }
            ]
        }

        # Act
        is_valid_result, message = configuration.configuration_verification(config)

        # Assert
        self.assertTrue(
            is_valid_result,
            "Validator should pass the fine configuration",
        )

        self.assertIsNone(message, "The validator should not return any message")
