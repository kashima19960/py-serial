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

"""Encoding Handler Module.

Provides utilities for handling character encoding conversion,
specifically designed to handle packet fragmentation issues with
multi-byte encodings like GBK and UTF-8.
"""

import codecs
import re


class EncodingHandler:
    """Incremental decoder for handling byte stream to text conversion.

    Uses Python's incremental decoder to gracefully handle multi-byte
    character boundaries that may be split across packets.

    Attributes:
        encoding: The current character encoding (e.g., 'utf-8', 'gbk').
    """

    def __init__(self, encoding: str = "gbk") -> None:
        """Initialize the encoding handler.

        Args:
            encoding: Character encoding to use (default: 'gbk').
        """
        self._encoding = encoding.lower()
        self._decoder = codecs.getincrementaldecoder(self._encoding)("ignore")

    @property
    def encoding(self) -> str:
        """Get the current encoding."""
        return self._encoding

    @encoding.setter
    def encoding(self, value: str) -> None:
        """Set the encoding and reset the decoder.

        Args:
            value: New encoding value.
        """
        new_encoding = value.lower()
        if new_encoding != self._encoding:
            self._encoding = new_encoding
            self.reset()

    def reset(self) -> None:
        """Reset the decoder state (clear any buffered bytes)."""
        self._decoder = codecs.getincrementaldecoder(self._encoding)("ignore")

    def decode(self, data: bytes, final: bool = False) -> str:
        """Decode byte data to text using incremental decoding.

        Incomplete multi-byte characters are buffered until the next
        call provides the remaining bytes.

        Args:
            data: Input byte data.
            final: Whether this is the last chunk of data.

        Returns:
            Decoded text string.
        """
        try:
            return self._decoder.decode(data, final)
        except Exception:  # pylint: disable=broad-except
            # On decode failure, reset and use replacement characters.
            self.reset()
            return data.decode(self._encoding, errors="replace")


def bytes_to_hex(data: bytes) -> str:
    """Convert byte data to a hexadecimal string.

    Args:
        data: Input byte data.

    Returns:
        Formatted hex string (e.g., "AA BB CC ").
    """
    if not data:
        return ""
    return " ".join(f"{b:02X}" for b in data) + " "


def hex_to_bytes(hex_str: str) -> bytes:
    """Convert a hexadecimal string to byte data.

    Automatically removes invalid characters and handles odd-length strings.

    Args:
        hex_str: Hex string (e.g., "AA BB CC" or "AABBCC").

    Returns:
        Parsed byte data.
    """
    # Remove all non-hex characters.
    clean_str = re.sub(r"[^A-Fa-f0-9]", "", hex_str)

    if not clean_str:
        return bytes()

    # Ensure even length by padding.
    if len(clean_str) % 2 != 0:
        clean_str = clean_str + "0"

    # Convert pairs of characters to bytes.
    result = []
    for i in range(0, len(clean_str), 2):
        byte_str = clean_str[i : i + 2]
        try:
            result.append(int(byte_str, 16))
        except ValueError:
            pass

    return bytes(result)


def text_to_bytes(text: str, encoding: str = "gbk") -> bytes:
    """Convert text to byte data using the specified encoding.

    Args:
        text: Input text string.
        encoding: Character encoding to use.

    Returns:
        Encoded byte data.
    """
    try:
        return text.encode(encoding.lower())
    except Exception:  # pylint: disable=broad-except
        return text.encode(encoding.lower(), errors="replace")
