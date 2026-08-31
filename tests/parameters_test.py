import unittest

from podcast_downloader.__main__ import build_parser
from podcast_downloader.parameters import parse_argv


class ParseArgvTest(unittest.TestCase):
    def test_preserves_zero_downloads_limit(self):
        parameters = parse_argv(build_parser(), ["--downloads_limit", "0"])

        self.assertEqual(0, parameters["downloads_limit"])

    def test_preserves_zero_download_delay(self):
        parameters = parse_argv(build_parser(), ["--download_delay", "0"])

        self.assertEqual(0, parameters["download_delay"])

    def test_omits_parameters_not_provided(self):
        parameters = parse_argv(build_parser(), [])

        self.assertNotIn("downloads_limit", parameters)
        self.assertNotIn("download_delay", parameters)
        self.assertNotIn("config", parameters)
        self.assertNotIn("if_directory_empty", parameters)
