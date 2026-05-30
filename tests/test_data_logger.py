# -*- coding: utf-8 -*-
"""Unit tests for the DataLogger class."""

import os
import tempfile
import unittest

from core.data_logger import DataLogger


class TestDataLogger(unittest.TestCase):
    """Tests for DataLogger functionality."""

    def setUp(self) -> None:
        """Create a temporary directory for test files."""
        self._tmp_dir = tempfile.mkdtemp()
        self._log_path = os.path.join(self._tmp_dir, "test.log")
        self._logger = DataLogger()

    def tearDown(self) -> None:
        """Clean up logger and temp files."""
        self._logger.close()
        if os.path.exists(self._log_path):
            os.remove(self._log_path)
        if os.path.exists(self._tmp_dir):
            os.rmdir(self._tmp_dir)

    def test_initial_state(self) -> None:
        """Logger should not be recording initially."""
        self.assertFalse(self._logger.is_recording)

    def test_start_stop_recording(self) -> None:
        """Start and stop recording should toggle is_recording."""
        result = self._logger.start_recording(self._log_path)
        self.assertTrue(result)
        self.assertTrue(self._logger.is_recording)

        self._logger.stop_recording()
        self.assertFalse(self._logger.is_recording)

    def test_start_creates_file(self) -> None:
        """Starting recording should create the log file."""
        self._logger.start_recording(self._log_path)
        self._logger.stop_recording()
        self.assertTrue(os.path.exists(self._log_path))

    def test_log_writes_timestamped_line(self) -> None:
        """Logged data should include direction and be timestamped."""
        self._logger.start_recording(self._log_path)
        self._logger.log("RX", "AA BB CC")
        self._logger.stop_recording()

        with open(self._log_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("RX: AA BB CC", content)
        # Check timestamp format [HH:MM:SS]
        import re
        self.assertRegex(content, r"\[\d{2}:\d{2}:\d{2}\] RX: AA BB CC")

    def test_log_tx_direction(self) -> None:
        """TX data should be logged with TX direction."""
        self._logger.start_recording(self._log_path)
        self._logger.log("TX", "AT+RST")
        self._logger.stop_recording()

        with open(self._log_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("TX: AT+RST", content)

    def test_log_noop_when_not_recording(self) -> None:
        """Logging when not recording should not raise or write."""
        self._logger.log("RX", "data")
        self.assertFalse(os.path.exists(self._log_path))

    def test_session_headers(self) -> None:
        """Log file should contain session start/end headers."""
        self._logger.start_recording(self._log_path)
        self._logger.log("RX", "test")
        self._logger.stop_recording()

        with open(self._log_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Session Start:", content)
        self.assertIn("Session End:", content)

    def test_restart_recording(self) -> None:
        """Restarting recording should append to the same file."""
        self._logger.start_recording(self._log_path)
        self._logger.log("RX", "first")
        self._logger.stop_recording()

        self._logger.start_recording(self._log_path)
        self._logger.log("TX", "second")
        self._logger.stop_recording()

        with open(self._log_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("first", content)
        self.assertIn("second", content)

    def test_format_timestamped(self) -> None:
        """format_timestamped should prepend [HH:MM:SS]."""
        result = DataLogger.format_timestamped("hello")
        import re
        self.assertRegex(result, r"^\[\d{2}:\d{2}:\d{2}\] hello$")

    def test_export_txt(self) -> None:
        """export_txt should write content to file."""
        export_path = os.path.join(self._tmp_dir, "export.txt")
        try:
            result = DataLogger.export_txt(export_path, "line1\nline2\n")
            self.assertTrue(result)
            with open(export_path, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "line1\nline2\n")
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)


if __name__ == "__main__":
    unittest.main()
