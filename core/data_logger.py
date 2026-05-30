# -*- coding: utf-8 -*-
# Copyright 2024 Serial Assistant Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Data Logger Module.

Provides timestamped logging and file export for serial data.
Timestamp precision: seconds [HH:MM:SS].
"""

import threading
from datetime import datetime
from typing import Optional


class DataLogger:
    """Handles serial data logging with timestamps and file export.

    Thread-safe logger that records RX/TX data with second-precision
    timestamps to a file. Supports starting/stopping recording sessions
    and exporting receive buffer content to plain text files.

    Attributes:
        _filepath: Path to the log file.
        _file: Open file handle (or None).
        _lock: Threading lock for write safety.
        _is_recording: Whether recording is active.
    """

    def __init__(self) -> None:
        """Initialize the data logger."""
        self._filepath: Optional[str] = None
        self._file = None
        self._lock = threading.Lock()
        self._is_recording = False

    @property
    def is_recording(self) -> bool:
        """Whether the logger is currently recording to a file."""
        return self._is_recording

    def start_recording(self, filepath: str) -> bool:
        """Start recording data to the specified file.

        Args:
            filepath: Absolute path to the log file.

        Returns:
            True if recording started successfully, False otherwise.
        """
        with self._lock:
            if self._is_recording:
                self._stop_recording_locked()

            try:
                self._file = open(filepath, "a", encoding="utf-8")
                self._filepath = filepath
                self._is_recording = True
                # Write session header.
                header = (
                    f"--- Session Start: "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n"
                )
                self._file.write(header)
                self._file.flush()
                return True
            except OSError:
                self._file = None
                self._filepath = None
                self._is_recording = False
                return False

    def stop_recording(self) -> None:
        """Stop the current recording session."""
        with self._lock:
            self._stop_recording_locked()

    def _stop_recording_locked(self) -> None:
        """Stop recording (caller must hold lock)."""
        if self._file is not None:
            try:
                footer = (
                    f"--- Session End: "
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n"
                )
                self._file.write(footer)
                self._file.close()
            except OSError:
                pass
            finally:
                self._file = None
                self._filepath = None
                self._is_recording = False

    def log(self, direction: str, text: str) -> None:
        """Record a data entry with timestamp.

        Args:
            direction: Data direction, typically "RX" or "TX".
            text: The data content (already formatted as text or hex).
        """
        with self._lock:
            if not self._is_recording or self._file is None:
                return

            timestamp = datetime.now().strftime("[%H:%M:%S]")
            line = f"{timestamp} {direction}: {text}\n"
            try:
                self._file.write(line)
                self._file.flush()
            except OSError:
                self._stop_recording_locked()

    @staticmethod
    def format_timestamped(text: str) -> str:
        """Prepend a second-precision timestamp to text.

        Args:
            text: The data text to timestamp.

        Returns:
            Formatted string like "[14:32:05] <text>".
        """
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        return f"{timestamp} {text}"

    @staticmethod
    def export_txt(filepath: str, content: str) -> bool:
        """Export text content to a file.

        Args:
            filepath: Destination file path.
            content: Text content to write.

        Returns:
            True on success, False on failure.
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except OSError:
            return False

    def close(self) -> None:
        """Clean up resources."""
        self.stop_recording()
