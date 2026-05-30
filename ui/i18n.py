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

"""Internationalization (i18n) Module.

Provides multi-language support for the Serial Assistant application.
Supports Chinese (default) and English.
"""

from typing import Dict

# Language codes
LANG_ZH = "zh"
LANG_EN = "en"

# Default language
DEFAULT_LANG = LANG_ZH

# Translation dictionaries
_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Window title
    "window_title": {
        LANG_ZH: "串口助手 v1.2",
        LANG_EN: "Serial Assistant v1.2",
    },
    
    # Group boxes
    "receive": {
        LANG_ZH: "接收区",
        LANG_EN: "Receive",
    },
    "send": {
        LANG_ZH: "发送区",
        LANG_EN: "Send",
    },
    "port_config": {
        LANG_ZH: "串口配置",
        LANG_EN: "Port Configuration",
    },
    "receive_settings": {
        LANG_ZH: "接收设置",
        LANG_EN: "Receive Settings",
    },
    "send_settings": {
        LANG_ZH: "发送设置",
        LANG_EN: "Send Settings",
    },
    "send_receive_settings": {
        LANG_ZH: "收发设置",
        LANG_EN: "Send/Receive Settings",
    },

    # Menu Bar - Top-level Menus
    "menu_file": {
        LANG_ZH: "文件(&F)",
        LANG_EN: "File(&F)",
    },
    "menu_edit": {
        LANG_ZH: "编辑(&E)",
        LANG_EN: "Edit(&E)",
    },
    "menu_view": {
        LANG_ZH: "视图(&V)",
        LANG_EN: "View(&V)",
    },
    "menu_help": {
        LANG_ZH: "帮助(&H)",
        LANG_EN: "Help(&H)",
    },

    # Menu Bar - File Menu Items
    "menu_open_port": {
        LANG_ZH: "打开串口",
        LANG_EN: "Open Port",
    },
    "menu_close_port": {
        LANG_ZH: "关闭串口",
        LANG_EN: "Close Port",
    },
    "menu_exit": {
        LANG_ZH: "退出",
        LANG_EN: "Exit",
    },

    # Menu Bar - Edit Menu Items
    "menu_clear_receive": {
        LANG_ZH: "清空接收区",
        LANG_EN: "Clear Receive Area",
    },
    "menu_clear_send": {
        LANG_ZH: "清空发送区",
        LANG_EN: "Clear Send Area",
    },

    # Menu Bar - View Menu Items
    "menu_always_on_top": {
        LANG_ZH: "始终置顶",
        LANG_EN: "Always on Top",
    },
    "menu_encoding": {
        LANG_ZH: "编码设置",
        LANG_EN: "Encoding Settings",
    },
    "menu_language": {
        LANG_ZH: "语言",
        LANG_EN: "Language",
    },

    # Menu Bar - Help Menu Items
    "menu_about": {
        LANG_ZH: "关于",
        LANG_EN: "About",
    },
    "about_title": {
        LANG_ZH: "关于串口助手",
        LANG_EN: "About Serial Assistant",
    },
    "about_text": {
        LANG_ZH: "串口助手 v1.2\n一个简洁实用的串口调试工具。",
        LANG_EN: "Serial Assistant v1.2\nA simple and practical serial debugging tool.",
    },
    
    # Labels
    "port": {
        LANG_ZH: "串口号",
        LANG_EN: "Port",
    },
    "baud_rate": {
        LANG_ZH: "波特率",
        LANG_EN: "Baud Rate",
    },
    "data_bits": {
        LANG_ZH: "数据位",
        LANG_EN: "Data Bits",
    },
    "stop_bits": {
        LANG_ZH: "停止位",
        LANG_EN: "Stop Bits",
    },
    "parity": {
        LANG_ZH: "校验位",
        LANG_EN: "Parity",
    },
    "action": {
        LANG_ZH: "操作",
        LANG_EN: "Action",
    },
    "mode": {
        LANG_ZH: "模式",
        LANG_EN: "Mode",
    },
    "encoding": {
        LANG_ZH: "编码",
        LANG_EN: "Encoding",
    },
    "language": {
        LANG_ZH: "语言",
        LANG_EN: "Language",
    },
    "receive_mode": {
        LANG_ZH: "接收模式",
        LANG_EN: "RX Mode",
    },
    "send_mode": {
        LANG_ZH: "发送模式",
        LANG_EN: "TX Mode",
    },
    "receive_encoding": {
        LANG_ZH: "接收编码",
        LANG_EN: "RX Encoding",
    },
    "send_encoding": {
        LANG_ZH: "发送编码",
        LANG_EN: "TX Encoding",
    },
    
    # Parity options
    "parity_none": {
        LANG_ZH: "无",
        LANG_EN: "None",
    },
    "parity_odd": {
        LANG_ZH: "奇校验",
        LANG_EN: "Odd",
    },
    "parity_even": {
        LANG_ZH: "偶校验",
        LANG_EN: "Even",
    },
    
    # Mode options
    "hex_mode": {
        LANG_ZH: "HEX模式",
        LANG_EN: "HEX Mode",
    },
    "text_mode": {
        LANG_ZH: "文本模式",
        LANG_EN: "Text Mode",
    },
    
    # Buttons
    "open_port": {
        LANG_ZH: "打开串口",
        LANG_EN: "Open Port",
    },
    "close_port": {
        LANG_ZH: "关闭串口",
        LANG_EN: "Close Port",
    },
    "clear": {
        LANG_ZH: "清空",
        LANG_EN: "Clear",
    },
    "send_btn": {
        LANG_ZH: "发送",
        LANG_EN: "Send",
    },
    
    # Status
    "connected": {
        LANG_ZH: "已连接",
        LANG_EN: "Connected",
    },
    "disconnected": {
        LANG_ZH: "未连接",
        LANG_EN: "Disconnected",
    },
    "error": {
        LANG_ZH: "错误",
        LANG_EN: "Error",
    },
    "ready": {
        LANG_ZH: "就绪",
        LANG_EN: "Ready",
    },
    "not_connected": {
        LANG_ZH: "未连接",
        LANG_EN: "Not connected",
    },
    "connected_to": {
        LANG_ZH: "已连接到 {port}",
        LANG_EN: "Connected to {port}",
    },
    
    # Placeholders
    "waiting_data": {
        LANG_ZH: "等待接收数据...",
        LANG_EN: "Waiting for data...",
    },
    "enter_data": {
        LANG_ZH: "请输入要发送的内容（HEX或文本）...",
        LANG_EN: "Enter data to send (HEX or text)...",
    },
    
    # Messages
    "warning": {
        LANG_ZH: "提示",
        LANG_EN: "Warning",
    },
    "select_port": {
        LANG_ZH: "请选择串口",
        LANG_EN: "Please select a port.",
    },
    "invalid_baud": {
        LANG_ZH: "波特率无效",
        LANG_EN: "Invalid baud rate.",
    },
    "open_failed": {
        LANG_ZH: "串口打开失败",
        LANG_EN: "Failed to open port.",
    },
    "port_disconnected": {
        LANG_ZH: "串口已断开",
        LANG_EN: "Port disconnected.",
    },
    
    # Language names
    "lang_zh": {
        LANG_ZH: "中文",
        LANG_EN: "中文",
    },
    "lang_en": {
        LANG_ZH: "English",
        LANG_EN: "English",
    },
}


class I18n:
    """Internationalization manager class.
    
    Manages the current language and provides translation lookup.
    """
    
    _current_lang: str = DEFAULT_LANG
    
    @classmethod
    def get_lang(cls) -> str:
        """Get the current language code."""
        return cls._current_lang
    
    @classmethod
    def set_lang(cls, lang: str) -> None:
        """Set the current language.
        
        Args:
            lang: Language code (LANG_ZH or LANG_EN).
        """
        if lang in (LANG_ZH, LANG_EN):
            cls._current_lang = lang
    
    @classmethod
    def t(cls, key: str, **kwargs) -> str:
        """Translate a key to the current language.
        
        Args:
            key: Translation key.
            **kwargs: Format arguments for the translated string.
            
        Returns:
            Translated string, or the key if not found.
        """
        if key in _TRANSLATIONS:
            text = _TRANSLATIONS[key].get(cls._current_lang, key)
            if kwargs:
                text = text.format(**kwargs)
            return text
        return key


# Convenience function
def t(key: str, **kwargs) -> str:
    """Translate a key to the current language.
    
    Args:
        key: Translation key.
        **kwargs: Format arguments for the translated string.
        
    Returns:
        Translated string.
    """
    return I18n.t(key, **kwargs)
