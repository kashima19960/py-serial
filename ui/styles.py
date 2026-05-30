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

"""UI Theme and Styles Module.

Provides a modern, light-themed stylesheet for the Serial Assistant application.
Design inspired by professional productivity tools with clean, minimal aesthetics.

Color Palette (Productivity Tool):
    - Primary: #3B82F6 (Blue)
    - Secondary: #60A5FA (Light Blue)
    - CTA: #F97316 (Orange)
    - Background: #F8FAFC (Off-white)
    - Text: #1E293B (Dark slate)
    - Border: #E2E8F0 (Light gray)
"""


# Color constants for easy customization.
class Colors:
    """Application color palette constants."""

    PRIMARY = "#3B82F6"
    PRIMARY_HOVER = "#2563EB"
    PRIMARY_PRESSED = "#1D4ED8"

    SECONDARY = "#60A5FA"

    DANGER = "#EF4444"
    DANGER_HOVER = "#DC2626"

    SUCCESS = "#22C55E"
    SUCCESS_BG = "#F0FDF4"
    SUCCESS_BORDER = "#BBF7D0"

    WARNING = "#F97316"
    WARNING_BG = "#FFF7ED"
    WARNING_BORDER = "#FED7AA"

    BACKGROUND = "#F8FAFC"
    SURFACE = "#FFFFFF"
    SURFACE_HOVER = "#F1F5F9"

    TEXT_PRIMARY = "#1E293B"
    TEXT_SECONDARY = "#475569"
    TEXT_MUTED = "#94A3B8"
    TEXT_ON_PRIMARY = "#FFFFFF"

    BORDER = "#E2E8F0"
    BORDER_FOCUS = "#3B82F6"

    SCROLLBAR_BG = "#F1F5F9"
    SCROLLBAR_HANDLE = "#CBD5E1"
    SCROLLBAR_HANDLE_HOVER = "#94A3B8"


def get_stylesheet() -> str:
    """Generate the application stylesheet.

    Returns:
        A complete Qt stylesheet string for the application.
    """
    return f"""
    /* ===== Global Styles ===== */
    QMainWindow {{
        background-color: {Colors.BACKGROUND};
    }}

    QWidget {{
        color: {Colors.TEXT_PRIMARY};
        font-family: "Segoe UI", "Microsoft YaHei UI", "Microsoft YaHei", sans-serif;
        font-size: 13px;
    }}

    /* ===== Menu Bar ===== */
    QMenuBar {{
        background-color: {Colors.SURFACE};
        border-bottom: 1px solid {Colors.BORDER};
        padding: 2px 4px;
        font-size: 13px;
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 6px 12px;
        border-radius: 4px;
        color: {Colors.TEXT_PRIMARY};
    }}

    QMenuBar::item:selected {{
        background-color: {Colors.SURFACE_HOVER};
    }}

    QMenuBar::item:pressed {{
        background-color: {Colors.BORDER};
    }}

    /* ===== Menu (Drop-down) ===== */
    QMenu {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: 8px;
        padding: 4px;
    }}

    QMenu::item {{
        padding: 8px 32px 8px 12px;
        border-radius: 4px;
        color: {Colors.TEXT_PRIMARY};
    }}

    QMenu::item:selected {{
        background-color: {Colors.SURFACE_HOVER};
    }}

    QMenu::item:disabled {{
        color: {Colors.TEXT_MUTED};
    }}

    QMenu::separator {{
        height: 1px;
        background: {Colors.BORDER};
        margin: 4px 8px;
    }}

    QMenu::indicator {{
        width: 16px;
        height: 16px;
        margin-left: 8px;
    }}

    /* ===== Group Box ===== */
    QGroupBox {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: 8px;
        margin-top: 16px;
        padding: 12px;
        padding-top: 24px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 8px;
        color: {Colors.TEXT_PRIMARY};
        font-weight: 600;
        font-size: 13px;
    }}

    /* ===== Text Edit / Line Edit ===== */
    QTextEdit, QLineEdit {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 8px;
        selection-background-color: {Colors.PRIMARY};
        selection-color: {Colors.TEXT_ON_PRIMARY};
    }}

    QTextEdit:focus, QLineEdit:focus {{
        border: 1px solid {Colors.BORDER_FOCUS};
    }}

    QTextEdit:disabled, QLineEdit:disabled {{
        background-color: {Colors.BACKGROUND};
        color: {Colors.TEXT_MUTED};
    }}

    /* ===== Combo Box ===== */
    QComboBox {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 6px 12px;
        padding-right: 30px;
        min-height: 20px;
    }}

    QComboBox:hover {{
        border-color: {Colors.SECONDARY};
    }}

    QComboBox:focus {{
        border-color: {Colors.BORDER_FOCUS};
    }}

    QComboBox:disabled {{
        background-color: {Colors.BACKGROUND};
        color: {Colors.TEXT_MUTED};
    }}

    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border: none;
        border-left: 1px solid {Colors.BORDER};
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
    }}

    QComboBox::down-arrow {{
        image: none;
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {Colors.TEXT_SECONDARY};
    }}

    QComboBox QAbstractItemView {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        selection-background-color: {Colors.SURFACE_HOVER};
        selection-color: {Colors.TEXT_PRIMARY};
        outline: none;
        padding: 4px;
    }}

    QComboBox QAbstractItemView::item {{
        padding: 6px 12px;
        border-radius: 4px;
    }}

    QComboBox QAbstractItemView::item:hover {{
        background-color: {Colors.SURFACE_HOVER};
    }}

    /* ===== Push Button ===== */
    QPushButton {{
        background-color: {Colors.SURFACE};
        border: 1px solid {Colors.BORDER};
        border-radius: 6px;
        padding: 8px 16px;
        color: {Colors.TEXT_PRIMARY};
        font-weight: 500;
        min-height: 18px;
    }}

    QPushButton:hover {{
        background-color: {Colors.SURFACE_HOVER};
        border-color: {Colors.SECONDARY};
    }}

    QPushButton:pressed {{
        background-color: {Colors.BORDER};
    }}

    QPushButton:disabled {{
        color: {Colors.TEXT_MUTED};
        background-color: {Colors.BACKGROUND};
        border-color: {Colors.BORDER};
    }}

    /* Primary Button */
    QPushButton[primary="true"] {{
        background-color: {Colors.PRIMARY};
        border-color: {Colors.PRIMARY};
        color: {Colors.TEXT_ON_PRIMARY};
    }}

    QPushButton[primary="true"]:hover {{
        background-color: {Colors.PRIMARY_HOVER};
        border-color: {Colors.PRIMARY_HOVER};
    }}

    QPushButton[primary="true"]:pressed {{
        background-color: {Colors.PRIMARY_PRESSED};
        border-color: {Colors.PRIMARY_PRESSED};
    }}

    QPushButton[primary="true"]:disabled {{
        background-color: {Colors.SECONDARY};
        border-color: {Colors.SECONDARY};
        color: {Colors.TEXT_ON_PRIMARY};
        opacity: 0.6;
    }}

    /* Danger Button */
    QPushButton[danger="true"] {{
        background-color: {Colors.DANGER};
        border-color: {Colors.DANGER};
        color: {Colors.TEXT_ON_PRIMARY};
    }}

    QPushButton[danger="true"]:hover {{
        background-color: {Colors.DANGER_HOVER};
        border-color: {Colors.DANGER_HOVER};
    }}

    /* Muted Button */
    QPushButton[muted="true"] {{
        background-color: transparent;
        border-color: {Colors.BORDER};
        color: {Colors.TEXT_SECONDARY};
    }}

    QPushButton[muted="true"]:hover {{
        background-color: {Colors.SURFACE_HOVER};
        color: {Colors.TEXT_PRIMARY};
    }}

    /* ===== Labels ===== */
    QLabel {{
        color: {Colors.TEXT_PRIMARY};
        font-size: 13px;
    }}

    QLabel#port_status {{
        padding: 4px 12px;
        border-radius: 12px;
        border: 1px solid {Colors.BORDER};
        background-color: {Colors.BACKGROUND};
        color: {Colors.TEXT_SECONDARY};
        font-weight: 500;
        font-size: 12px;
    }}

    QLabel#port_status[status="open"] {{
        color: {Colors.SUCCESS};
        border-color: {Colors.SUCCESS_BORDER};
        background-color: {Colors.SUCCESS_BG};
    }}

    QLabel#port_status[status="closed"] {{
        color: {Colors.TEXT_MUTED};
        border-color: {Colors.BORDER};
        background-color: {Colors.BACKGROUND};
    }}

    QLabel#port_status[status="error"] {{
        color: {Colors.WARNING};
        border-color: {Colors.WARNING_BORDER};
        background-color: {Colors.WARNING_BG};
    }}

    /* ===== Splitter ===== */
    QSplitter::handle {{
        background-color: {Colors.BACKGROUND};
        width: 6px;
    }}

    QSplitter::handle:hover {{
        background-color: {Colors.BORDER};
    }}

    /* ===== Scroll Bar ===== */
    QScrollBar:vertical {{
        background: {Colors.SCROLLBAR_BG};
        width: 10px;
        margin: 2px;
        border-radius: 5px;
    }}

    QScrollBar::handle:vertical {{
        background: {Colors.SCROLLBAR_HANDLE};
        min-height: 30px;
        border-radius: 5px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {Colors.SCROLLBAR_HANDLE_HOVER};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
        background: none;
    }}

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background: {Colors.SCROLLBAR_BG};
        height: 10px;
        margin: 2px;
        border-radius: 5px;
    }}

    QScrollBar::handle:horizontal {{
        background: {Colors.SCROLLBAR_HANDLE};
        min-width: 30px;
        border-radius: 5px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {Colors.SCROLLBAR_HANDLE_HOVER};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
        background: none;
    }}

    /* ===== Status Bar ===== */
    QStatusBar {{
        background-color: {Colors.SURFACE};
        border-top: 1px solid {Colors.BORDER};
        color: {Colors.TEXT_SECONDARY};
        font-size: 12px;
        padding: 4px 8px;
    }}

    /* ===== Message Box ===== */
    QMessageBox {{
        background-color: {Colors.SURFACE};
    }}

    QMessageBox QLabel {{
        color: {Colors.TEXT_PRIMARY};
    }}
    """
