import logging
import unittest

from podcast_downloader.utils import ErrorSummaryHandler


class ErrorSummaryHandlerTest(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger(f"{__name__}.{self._testMethodName}")
        self.logger.handlers = []
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)
        self.handler = ErrorSummaryHandler()
        self.logger.addHandler(self.handler)

    def test_only_error_messages_are_collected(self):
        self.logger.info("informational")
        self.logger.warning("warning")
        self.logger.error("Feed %s failed", "example")

        self.assertEqual(["Feed example failed"], self.handler.messages)

    def test_exception_traceback_is_not_stored_in_summary(self):
        try:
            raise ValueError("details")
        except ValueError:
            self.logger.exception("Download failed")

        self.assertEqual(["Download failed"], self.handler.messages)


if __name__ == "__main__":
    unittest.main()
