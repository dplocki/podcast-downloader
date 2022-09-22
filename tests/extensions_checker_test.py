import unittest

from podcast_downloader.downloaded import get_extensions_checker


class TestExtensionsChecker(unittest.TestCase):
    def test_only_extensions(self):
        self.assertTrue(
            get_extensions_checker([".abc"])("abc.abc"),
            "The file should be recognized when just one extension is provided",
        )
        self.assertTrue(
            get_extensions_checker([".xyz", ".abc"])("abc.abc"),
            "The file should be recognized even if there are multiple extensions",
        )

        self.assertFalse(
            get_extensions_checker([".xyz", ".abc"])("abc.not"),
            "The file should not be recognized even if provided extension is in the file name",
        )
