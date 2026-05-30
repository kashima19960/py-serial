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

"""Configuration Manager Module.

Provides persistent configuration storage using JSON files.
Manages user preferences, custom baud rates, presets, and window state.
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default configuration directory
_CONFIG_DIR = Path.home() / ".serial_assistant"
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# Default configuration values
_DEFAULTS: Dict[str, Any] = {
    # Window state
    "window": {
        "x": -1,
        "y": -1,
        "width": 1024,
        "height": 720,
        "maximized": False,
        "splitter_sizes": [700, 324],
        "left_splitter_sizes": [450, 200],
    },
    # Serial port parameters
    "serial": {
        "port": "",
        "baud_rate": "115200",
        "data_bits": "8",
        "stop_bits": "1",
        "parity_index": 0,
        "receive_mode_index": 1,
        "receive_encoding_index": 1,
        "send_mode_index": 1,
        "send_encoding_index": 1,
    },
    # Custom baud rates (in addition to defaults)
    "custom_baud_rates": [],
    # Preset commands
    "preset_commands": [],
    # UI preferences
    "ui": {
        "theme": "light",
        "language": "zh",
        "font_family": "Consolas",
        "font_size": 10,
        "show_timestamp": False,
        "timestamp_format": "HH:MM:SS.mmm",
    },
    # Filter settings
    "filter": {
        "text": "",
        "use_regex": False,
    },
    # Auto reconnect
    "auto_reconnect": {
        "enabled": False,
        "retry_interval": 3,
        "max_retries": 5,
    },
    # Logging session
    "session_log": {
        "enabled": False,
        "directory": "",
    },
    # Performance
    "performance": {
        "max_lines": 10000,
        "batch_refresh_ms": 50,
    },
    # Shortcuts (key -> action name)
    "shortcuts": {
        "Ctrl+Return": "send",
        "Ctrl+Shift+H": "toggle_receive_mode",
        "Ctrl+L": "clear_receive",
        "Ctrl+Shift+L": "clear_send",
        "Ctrl+S": "save_receive",
        "F5": "refresh_ports",
    },
}


class ConfigManager:
    """Singleton configuration manager.

    Loads configuration from a JSON file on startup and saves on changes.
    Falls back to default values for missing keys.
    """

    _instance: Optional["ConfigManager"] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from disk. Falls back to defaults on error."""
        try:
            if _CONFIG_FILE.exists():
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # Merge with defaults to ensure all keys exist.
                self._data = self._deep_merge(_DEFAULTS.copy(), loaded)
                logger.info("Configuration loaded from %s", _CONFIG_FILE)
            else:
                self._data = _DEFAULTS.copy()
                logger.info("No config file found, using defaults.")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load config: %s. Using defaults.", e)
            self._data = _DEFAULTS.copy()

    def save(self) -> None:
        """Save current configuration to disk."""
        try:
            _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.debug("Configuration saved to %s", _CONFIG_FILE)
        except OSError as e:
            logger.error("Failed to save config: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot-notation key.

        Args:
            key: Dot-separated key path (e.g., 'serial.baud_rate').
            default: Default value if key not found.

        Returns:
            The configuration value, or default if not found.
        """
        keys = key.split(".")
        current = self._data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot-notation key.

        Args:
            key: Dot-separated key path (e.g., 'serial.baud_rate').
            value: The value to set.
        """
        keys = key.split(".")
        current = self._data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def get_custom_baud_rates(self) -> List[str]:
        """Get the list of custom baud rates."""
        return self._data.get("custom_baud_rates", [])

    def add_custom_baud_rate(self, baud: str) -> None:
        """Add a custom baud rate if not already present.

        Args:
            baud: Baud rate string to add.
        """
        customs = self._data.setdefault("custom_baud_rates", [])
        if baud not in customs:
            customs.append(baud)
            customs.sort(key=lambda x: int(x) if x.isdigit() else 0)
            logger.info("Added custom baud rate: %s", baud)

    def get_preset_commands(self) -> List[Dict[str, str]]:
        """Get the list of preset commands."""
        return self._data.get("preset_commands", [])

    def set_preset_commands(self, presets: List[Dict[str, str]]) -> None:
        """Replace the preset commands list.

        Args:
            presets: List of dicts with 'name' and 'command' keys.
        """
        self._data["preset_commands"] = presets

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dictionaries. Override values take precedence.

        Args:
            base: Base dictionary with defaults.
            override: Override dictionary with user values.

        Returns:
            Merged dictionary.
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def reset_instance() -> None:
        """Reset the singleton instance (for testing)."""
        ConfigManager._instance = None
