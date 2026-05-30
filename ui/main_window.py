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

"""Main Window Module.

Contains the MainWindow class which implements the primary user interface
for the Serial Assistant application.
"""

import ctypes
import re
from datetime import datetime
from typing import List, Optional, Tuple

from PySide6.QtCore import QRegularExpression, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QActionGroup,
    QColor,
    QFont,
    QFontDatabase,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.data_logger import DataLogger
from core.encoding_handler import (
    EncodingHandler,
    bytes_to_hex,
    hex_to_bytes,
    text_to_bytes,
)
from core.serial_worker import SerialWorker, get_available_ports
from ui.styles import Colors, get_stylesheet
from ui.i18n import I18n, t, LANG_ZH, LANG_EN


# Windows message constants for device detection.
WM_DEVICECHANGE = 0x0219
DBT_DEVICEREMOVECOMPLETE = 0x8004


class MainWindow(QMainWindow):
    """Main window for the Serial Assistant application.

    Implements a left-right split layout:
        - Left side: Receive area (top) and Send area (bottom)
        - Right side: Serial port configuration and settings

    Attributes:
        tb_receive: Text editor for displaying received data.
        tb_send: Text editor for composing data to send.
        btn_open: Button to open/close serial port.
        btn_send: Button to send data.
    """

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()

        # Initialize serial worker.
        self._serial_worker = SerialWorker()
        self._serial_worker.data_received.connect(self._on_data_received)
        self._serial_worker.error_occurred.connect(self._on_error)
        self._serial_worker.port_disconnected.connect(self._on_port_disconnected)

        # Initialize encoding handler.
        self._encoding_handler = EncodingHandler("utf-8")

        # Mode and encoding state.
        self._receive_mode = "文本模式"
        self._receive_encoding = "UTF-8"
        self._send_mode = "文本模式"
        self._send_encoding = "UTF-8"
        
        # Port open state for language switching.
        self._is_port_open = False

        # Data logger.
        self._data_logger = DataLogger()

        # Timestamp and display options.
        self._show_timestamp = False
        self._auto_scroll = True

        # Byte counters.
        self._rx_byte_count = 0
        self._tx_byte_count = 0

        # Search / filter state.
        self._raw_receive_lines: List[str] = [""]
        self._search_matches: list = []
        self._current_match_index = -1

        # Font state.
        self._current_font_family = "Consolas"
        self._current_font_size = 10
        self._mono_only = True

        # Build UI.
        self._init_ui()
        self._init_connections()
        self._init_default_values()

        # Timer for port status monitoring (fallback for hot-plug detection).
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_port_status)
        self._check_timer.start(1000)

    def _init_ui(self) -> None:
        """Initialize the user interface layout."""
        self.setWindowTitle(t("window_title"))
        self.resize(1024, 720)
        self.setMinimumSize(800, 600)

        # Apply stylesheet.
        self.setStyleSheet(get_stylesheet())

        # Create menu bar.
        self._create_menu_bar()

        # Create central widget.
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with splitter.
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Build left and right panels.
        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Configure splitter proportions.
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        # Configure status bar.
        self.statusBar().setSizeGripEnabled(False)
        self._init_status_bar()

    def _init_status_bar(self) -> None:
        """Initialize permanent status bar widgets."""
        self.lbl_status_port = QLabel()
        self.lbl_status_port.setObjectName("status_field")
        self.statusBar().addPermanentWidget(self.lbl_status_port)

        self.lbl_status_rx = QLabel(t("status_rx", count="0 B"))
        self.lbl_status_rx.setObjectName("status_field")
        self.statusBar().addPermanentWidget(self.lbl_status_rx)

        self.lbl_status_tx = QLabel(t("status_tx", count="0 B"))
        self.lbl_status_tx.setObjectName("status_field")
        self.statusBar().addPermanentWidget(self.lbl_status_tx)

        self.lbl_status_rec = QLabel(t("status_recording"))
        self.lbl_status_rec.setObjectName("status_rec")
        self.lbl_status_rec.setVisible(False)
        self.statusBar().addPermanentWidget(self.lbl_status_rec)

        self.statusBar().showMessage(t("ready"))

    def _update_status_counters(self) -> None:
        """Update the RX/TX byte count labels in the status bar."""
        self.lbl_status_rx.setText(
            t("status_rx", count=self._format_bytes(self._rx_byte_count))
        )
        self.lbl_status_tx.setText(
            t("status_tx", count=self._format_bytes(self._tx_byte_count))
        )

    @staticmethod
    def _format_bytes(count: int) -> str:
        """Format a byte count into a human-readable string.

        Args:
            count: Number of bytes.

        Returns:
            Formatted string like "1.2 KB" or "345 B".
        """
        if count < 1024:
            return f"{count} B"
        if count < 1024 * 1024:
            return f"{count / 1024:.1f} KB"
        return f"{count / (1024 * 1024):.1f} MB"

    def _create_menu_bar(self) -> None:
        """Create the application menu bar with standard menus."""
        menu_bar = self.menuBar()

        # --- File Menu ---
        self.menu_file = menu_bar.addMenu(t("menu_file"))

        self.act_open_port = QAction(t("menu_open_port"), self)
        self.act_open_port.setShortcut("Ctrl+O")
        self.act_open_port.triggered.connect(self._on_open_clicked)
        self.menu_file.addAction(self.act_open_port)

        self.act_close_port = QAction(t("menu_close_port"), self)
        self.act_close_port.setShortcut("Ctrl+Shift+O")
        self.act_close_port.triggered.connect(self._on_open_clicked)
        self.act_close_port.setVisible(False)
        self.menu_file.addAction(self.act_close_port)

        self.menu_file.addSeparator()

        self.act_exit = QAction(t("menu_exit"), self)
        self.act_exit.setShortcut("Ctrl+Q")
        self.act_exit.triggered.connect(self.close)
        self.menu_file.addAction(self.act_exit)

        self.menu_file.addSeparator()

        # Recording toggle.
        self.act_record = QAction(t("record_log"), self)
        self.act_record.setCheckable(True)
        self.act_record.setShortcut("Ctrl+R")
        self.act_record.triggered.connect(self._on_record_toggled)
        self.menu_file.addAction(self.act_record)

        # Export submenu.
        self.act_export_txt = QAction(t("export_txt"), self)
        self.act_export_txt.setShortcut("Ctrl+S")
        self.act_export_txt.triggered.connect(self._on_export_txt)
        self.menu_file.addAction(self.act_export_txt)

        # --- Edit Menu ---
        self.menu_edit = menu_bar.addMenu(t("menu_edit"))

        self.act_clear_receive = QAction(t("menu_clear_receive"), self)
        self.act_clear_receive.setShortcut("Ctrl+Shift+C")
        self.act_clear_receive.triggered.connect(self._on_clear_receive)
        self.menu_edit.addAction(self.act_clear_receive)

        self.act_clear_send = QAction(t("menu_clear_send"), self)
        self.act_clear_send.setShortcut("Ctrl+Shift+D")
        self.act_clear_send.triggered.connect(self._on_clear_send)
        self.menu_edit.addAction(self.act_clear_send)

        self.menu_edit.addSeparator()

        self.act_find = QAction(t("find"), self)
        self.act_find.setShortcut("Ctrl+F")
        self.act_find.triggered.connect(self._on_find)
        self.menu_edit.addAction(self.act_find)

        # --- View Menu ---
        self.menu_view = menu_bar.addMenu(t("menu_view"))

        self.act_always_on_top = QAction(t("menu_always_on_top"), self)
        self.act_always_on_top.setCheckable(True)
        self.act_always_on_top.setShortcut("Ctrl+T")
        self.act_always_on_top.triggered.connect(self._on_always_on_top)
        self.menu_view.addAction(self.act_always_on_top)

        # Language submenu.
        self.menu_language = self.menu_view.addMenu(t("menu_language"))
        self.act_lang_zh = QAction(t("lang_zh"), self)
        self.act_lang_zh.setCheckable(True)
        self.act_lang_zh.setChecked(I18n.get_lang() == LANG_ZH)
        self.act_lang_zh.triggered.connect(
            lambda checked: self._on_language_menu_changed(LANG_ZH, checked)
        )
        self.menu_language.addAction(self.act_lang_zh)

        self.act_lang_en = QAction(t("lang_en"), self)
        self.act_lang_en.setCheckable(True)
        self.act_lang_en.setChecked(I18n.get_lang() == LANG_EN)
        self.act_lang_en.triggered.connect(
            lambda checked: self._on_language_menu_changed(LANG_EN, checked)
        )
        self.menu_language.addAction(self.act_lang_en)

        # Font submenu.
        self._build_font_submenu()

        # --- Help Menu ---
        self.menu_help = menu_bar.addMenu(t("menu_help"))

        self.act_about = QAction(t("menu_about"), self)
        self.act_about.triggered.connect(self._on_about)
        self.menu_help.addAction(self.act_about)

    def _create_left_panel(self) -> QWidget:
        """Create the left panel containing receive and send areas.

        Returns:
            A QWidget containing the left panel layout.
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Receive area.
        self.grp_receive = QGroupBox(t("receive"))
        receive_layout = QVBoxLayout(self.grp_receive)

        # Receive toolbar.
        receive_toolbar = QHBoxLayout()
        receive_toolbar.setSpacing(8)

        self.chk_timestamp = QCheckBox(t("show_timestamp"))
        self.chk_timestamp.setChecked(False)
        self.chk_timestamp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_timestamp.toggled.connect(self._on_timestamp_toggled)
        receive_toolbar.addWidget(self.chk_timestamp)

        self.chk_auto_scroll = QCheckBox(t("auto_scroll"))
        self.chk_auto_scroll.setChecked(True)
        self.chk_auto_scroll.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_auto_scroll.toggled.connect(self._on_auto_scroll_toggled)
        receive_toolbar.addWidget(self.chk_auto_scroll)

        receive_toolbar.addStretch()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(t("search_placeholder"))
        self.search_bar.setMinimumWidth(140)
        self.search_bar.setMaximumWidth(220)
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self._on_search_text_changed)
        self.search_bar.returnPressed.connect(self._on_search_next)
        receive_toolbar.addWidget(self.search_bar)

        self.chk_filter = QCheckBox(t("filter_mode"))
        self.chk_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_filter.toggled.connect(self._on_filter_toggled)
        receive_toolbar.addWidget(self.chk_filter)

        self.chk_regex = QCheckBox(t("regex_mode"))
        self.chk_regex.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_regex.toggled.connect(self._on_regex_toggled)
        receive_toolbar.addWidget(self.chk_regex)

        self.lbl_match_count = QLabel("")
        self.lbl_match_count.setObjectName("match_count")
        receive_toolbar.addWidget(self.lbl_match_count)

        receive_layout.addLayout(receive_toolbar)

        self.tb_receive = QTextEdit()
        self.tb_receive.setReadOnly(True)
        self.tb_receive.setFont(QFont("Consolas", 10))
        self.tb_receive.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.tb_receive.setAcceptRichText(False)
        self.tb_receive.setPlaceholderText(t("waiting_data"))
        self.tb_receive.document().setMaximumBlockCount(10000)
        receive_layout.addWidget(self.tb_receive, 1)

        # Receive area buttons.
        receive_btn_layout = QHBoxLayout()
        receive_btn_layout.addStretch()
        self.btn_clear_receive = QPushButton(t("clear"))
        self.btn_clear_receive.setMinimumWidth(80)
        self.btn_clear_receive.setProperty("muted", True)
        self.btn_clear_receive.setCursor(Qt.CursorShape.PointingHandCursor)
        receive_btn_layout.addWidget(self.btn_clear_receive)
        receive_layout.addLayout(receive_btn_layout)

        layout.addWidget(self.grp_receive, 2)

        # Send area.
        self.grp_send = QGroupBox(t("send"))
        send_layout = QVBoxLayout(self.grp_send)

        self.tb_send = QTextEdit()
        self.tb_send.setFont(QFont("Consolas", 10))
        self.tb_send.setMaximumHeight(100)
        self.tb_send.setAcceptRichText(False)
        self.tb_send.setTabChangesFocus(True)
        self.tb_send.setPlaceholderText(t("enter_data"))
        send_layout.addWidget(self.tb_send, 1)

        # Send area buttons.
        send_btn_layout = QHBoxLayout()

        self.chk_append_crlf = QCheckBox(t("append_crlf"))
        self.chk_append_crlf.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn_layout.addWidget(self.chk_append_crlf)

        send_btn_layout.addStretch()
        self.btn_clear_send = QPushButton(t("clear"))
        self.btn_clear_send.setMinimumWidth(80)
        self.btn_clear_send.setProperty("muted", True)
        self.btn_clear_send.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn_layout.addWidget(self.btn_clear_send)

        self.btn_send = QPushButton(t("send_btn"))
        self.btn_send.setMinimumWidth(100)
        self.btn_send.setEnabled(False)
        self.btn_send.setProperty("primary", True)
        self.btn_send.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn_layout.addWidget(self.btn_send)
        send_layout.addLayout(send_btn_layout)

        layout.addWidget(self.grp_send, 1)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right panel containing configuration options.

        Returns:
            A QWidget containing the right panel layout.
        """
        panel = QWidget()
        panel.setFixedWidth(260)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Serial port configuration.
        layout.addWidget(self._create_port_config_group())

        # Send/Receive configuration (merged).
        layout.addWidget(self._create_send_receive_config_group())

        layout.addStretch()

        return panel

    def _create_port_config_group(self) -> QGroupBox:
        """Create the serial port configuration group box.

        Returns:
            A QGroupBox containing port configuration controls.
        """
        self.grp_port_config = QGroupBox(t("port_config"))
        layout = QGridLayout(self.grp_port_config)
        layout.setSpacing(10)
        layout.setColumnStretch(1, 1)

        row = 0

        # Port selection.
        self.lbl_port = QLabel(t("port"))
        layout.addWidget(self.lbl_port, row, 0)
        self.cb_port_name = QComboBox()
        self.cb_port_name.setMinimumWidth(140)
        layout.addWidget(self.cb_port_name, row, 1)
        row += 1

        # Baud rate.
        self.lbl_baud_rate = QLabel(t("baud_rate"))
        layout.addWidget(self.lbl_baud_rate, row, 0)
        self.cb_baud_rate = QComboBox()
        self._DEFAULT_BAUDS = [
            "300", "600", "1200", "2400", "4800", "9600", "14400",
            "19200", "38400", "43000", "56000", "57600", "115200",
            "128000", "256000"
        ]
        self._custom_bauds: list[str] = []
        self._build_baud_rate_list()
        self.cb_baud_rate.activated.connect(self._on_baud_rate_activated)
        layout.addWidget(self.cb_baud_rate, row, 1)
        row += 1

        # Data bits.
        self.lbl_data_bits = QLabel(t("data_bits"))
        layout.addWidget(self.lbl_data_bits, row, 0)
        self.cb_data_bits = QComboBox()
        self.cb_data_bits.addItems(["5", "6", "7", "8"])
        layout.addWidget(self.cb_data_bits, row, 1)
        row += 1

        # Stop bits.
        self.lbl_stop_bits = QLabel(t("stop_bits"))
        layout.addWidget(self.lbl_stop_bits, row, 0)
        self.cb_stop_bits = QComboBox()
        self.cb_stop_bits.addItems(["1", "1.5", "2"])
        layout.addWidget(self.cb_stop_bits, row, 1)
        row += 1

        # Parity.
        self.lbl_parity = QLabel(t("parity"))
        layout.addWidget(self.lbl_parity, row, 0)
        self.cb_parity = QComboBox()
        self._update_parity_items()
        layout.addWidget(self.cb_parity, row, 1)
        row += 1

        # Open/Close button.
        self.lbl_action = QLabel(t("action"))
        layout.addWidget(self.lbl_action, row, 0)
        self.btn_open = QPushButton(t("open_port"))
        self.btn_open.setObjectName("btn_open")
        self.btn_open.setProperty("primary", True)
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.btn_open, row, 1)
        row += 1

        # Status indicator.
        self.lbl_port_status = QLabel(t("disconnected"))
        self.lbl_port_status.setObjectName("port_status")
        self.lbl_port_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_port_status, row, 0, 1, 2)

        return self.grp_port_config

    def _create_send_receive_config_group(self) -> QGroupBox:
        """Create the combined send/receive configuration group box.

        Returns:
            A QGroupBox containing both receive and send settings.
        """
        self.grp_send_receive_config = QGroupBox(t("send_receive_settings"))
        layout = QGridLayout(self.grp_send_receive_config)
        layout.setSpacing(10)
        layout.setColumnStretch(1, 1)

        row = 0

        # Receive mode.
        self.lbl_receive_mode = QLabel(t("receive_mode"))
        layout.addWidget(self.lbl_receive_mode, row, 0)
        self.cb_receive_mode = QComboBox()
        self._update_receive_mode_items()
        self.cb_receive_mode.setMinimumWidth(140)
        layout.addWidget(self.cb_receive_mode, row, 1)
        row += 1

        # Receive encoding.
        self.lbl_receive_encoding = QLabel(t("receive_encoding"))
        layout.addWidget(self.lbl_receive_encoding, row, 0)
        self.cb_receive_encoding = QComboBox()
        self.cb_receive_encoding.addItems(["GBK", "UTF-8"])
        self.cb_receive_encoding.setEnabled(False)
        layout.addWidget(self.cb_receive_encoding, row, 1)
        row += 1

        # Send mode.
        self.lbl_send_mode = QLabel(t("send_mode"))
        layout.addWidget(self.lbl_send_mode, row, 0)
        self.cb_send_mode = QComboBox()
        self._update_send_mode_items()
        self.cb_send_mode.setMinimumWidth(140)
        layout.addWidget(self.cb_send_mode, row, 1)
        row += 1

        # Send encoding.
        self.lbl_send_encoding = QLabel(t("send_encoding"))
        layout.addWidget(self.lbl_send_encoding, row, 0)
        self.cb_send_encoding = QComboBox()
        self.cb_send_encoding.addItems(["GBK", "UTF-8"])
        self.cb_send_encoding.setEnabled(False)
        layout.addWidget(self.cb_send_encoding, row, 1)

        return self.grp_send_receive_config
    
    def _update_parity_items(self) -> None:
        """Update parity combo box items based on current language."""
        current_index = self.cb_parity.currentIndex() if self.cb_parity.count() > 0 else 0
        self.cb_parity.clear()
        self.cb_parity.addItems([t("parity_none"), t("parity_odd"), t("parity_even")])
        self.cb_parity.setCurrentIndex(current_index)
    
    def _update_receive_mode_items(self) -> None:
        """Update receive mode combo box items based on current language."""
        current_index = self.cb_receive_mode.currentIndex() if self.cb_receive_mode.count() > 0 else 1
        self.cb_receive_mode.clear()
        self.cb_receive_mode.addItems([t("hex_mode"), t("text_mode")])
        self.cb_receive_mode.setCurrentIndex(current_index)
    
    def _update_send_mode_items(self) -> None:
        """Update send mode combo box items based on current language."""
        current_index = self.cb_send_mode.currentIndex() if self.cb_send_mode.count() > 0 else 1
        self.cb_send_mode.clear()
        self.cb_send_mode.addItems([t("hex_mode"), t("text_mode")])
        self.cb_send_mode.setCurrentIndex(current_index)

    def _init_connections(self) -> None:
        """Initialize signal-slot connections."""
        # Button clicks.
        self.btn_open.clicked.connect(self._on_open_clicked)
        self.btn_send.clicked.connect(self._on_send_clicked)
        self.btn_clear_receive.clicked.connect(self._on_clear_receive)
        self.btn_clear_send.clicked.connect(self._on_clear_send)

        # Port dropdown refresh.
        self.cb_port_name.showPopup = self._on_port_dropdown

        # Mode and encoding changes.
        self.cb_receive_mode.currentIndexChanged.connect(
            self._on_receive_mode_changed
        )
        self.cb_receive_encoding.currentIndexChanged.connect(
            self._on_receive_encoding_changed
        )
        self.cb_send_mode.currentIndexChanged.connect(
            self._on_send_mode_changed
        )
        self.cb_send_encoding.currentIndexChanged.connect(
            self._on_send_encoding_changed
        )

    def _init_default_values(self) -> None:
        """Initialize default control values."""
        self.cb_baud_rate.setCurrentIndex(12)  # 115200
        self.cb_data_bits.setCurrentIndex(3)   # 8
        self.cb_stop_bits.setCurrentIndex(0)   # 1
        self.cb_parity.setCurrentIndex(0)      # None
        self.cb_receive_mode.setCurrentIndex(1)  # Text Mode
        self.cb_receive_encoding.setCurrentIndex(1)  # UTF-8
        self.cb_send_mode.setCurrentIndex(1)   # Text Mode
        self.cb_send_encoding.setCurrentIndex(1)  # UTF-8

        # Refresh port list.
        self._refresh_port_list()

        # Initialize port status UI.
        self._update_port_ui(is_open=False)

    def _set_status_badge(self, status: str, text: str) -> None:
        """Update the port status badge.

        Args:
            status: Status type ('open', 'closed', or 'error').
            text: Display text for the badge.
        """
        self.lbl_port_status.setProperty("status", status)
        self.lbl_port_status.setText(text)
        self.lbl_port_status.style().unpolish(self.lbl_port_status)
        self.lbl_port_status.style().polish(self.lbl_port_status)
        self.lbl_port_status.update()

    def _update_port_ui(self, is_open: bool) -> None:
        """Update UI elements based on port connection state.

        Args:
            is_open: Whether the port is currently open.
        """
        self._is_port_open = is_open
        if is_open:
            self.btn_open.setText(t("close_port"))
            self.btn_open.setProperty("danger", True)
            self.btn_open.setProperty("primary", False)
            self.btn_send.setEnabled(True)
            self._set_config_enabled(False)
            self._set_status_badge("open", t("connected"))
            port_info = (
                f"{self.cb_port_name.currentText()} @ "
                f"{self.cb_baud_rate.currentText()}"
            )
            self.lbl_status_port.setText(port_info)
        else:
            self.btn_open.setText(t("open_port"))
            self.btn_open.setProperty("danger", False)
            self.btn_open.setProperty("primary", True)
            self.btn_send.setEnabled(False)
            self._set_config_enabled(True)
            self._set_status_badge("closed", t("disconnected"))
            self.lbl_status_port.setText("")

        # Update menu visibility.
        self._update_menu_port_state()

        # Force style update.
        self.btn_open.style().unpolish(self.btn_open)
        self.btn_open.style().polish(self.btn_open)
        self.btn_open.update()

    def _refresh_port_list(self) -> None:
        """Refresh the available serial ports list."""
        current = self.cb_port_name.currentText()
        self.cb_port_name.clear()
        ports = get_available_ports()
        self.cb_port_name.addItems(ports)

        # Restore previous selection if still available.
        if current in ports:
            self.cb_port_name.setCurrentText(current)

    def _on_port_dropdown(self) -> None:
        """Handle port dropdown expansion (refresh port list)."""
        self._refresh_port_list()
        QComboBox.showPopup(self.cb_port_name)

    def _open_serial_port(self) -> bool:
        """Open the serial port with current configuration.

        Returns:
            True if port opened successfully, False otherwise.
        """
        port_name = self.cb_port_name.currentText()
        if not port_name:
            QMessageBox.warning(self, t("warning"), t("select_port"))
            return False

        try:
            baud_rate = int(self.cb_baud_rate.currentText())
        except ValueError:
            QMessageBox.warning(self, t("warning"), t("invalid_baud"))
            return False

        data_bits = int(self.cb_data_bits.currentText())

        # Map stop bits.
        stop_bits_map = {"1": 1, "1.5": 1.5, "2": 2}
        stop_bits = stop_bits_map.get(self.cb_stop_bits.currentText(), 1)

        # Map parity (use index instead of text for language independence).
        parity_index = self.cb_parity.currentIndex()
        parity_map = {0: "N", 1: "O", 2: "E"}
        parity = parity_map.get(parity_index, "N")

        if self._serial_worker.open_port(
            port_name, baud_rate, data_bits, stop_bits, parity
        ):
            self._serial_worker.start()
            self._update_port_ui(is_open=True)
            return True
        else:
            QMessageBox.warning(self, t("warning"), t("open_failed"))
            return False

    def _close_serial_port(self) -> None:
        """Close the serial port."""
        self._serial_worker.close_port()
        self._encoding_handler.reset()
        self._update_port_ui(is_open=False)

    def _set_config_enabled(self, enabled: bool) -> None:
        """Enable or disable configuration controls.

        Args:
            enabled: Whether controls should be enabled.
        """
        self.cb_port_name.setEnabled(enabled)
        self.cb_baud_rate.setEnabled(enabled)
        self.cb_data_bits.setEnabled(enabled)
        self.cb_stop_bits.setEnabled(enabled)
        self.cb_parity.setEnabled(enabled)

    def _on_open_clicked(self) -> None:
        """Handle open/close button click."""
        if not self._is_port_open:
            self._open_serial_port()
        else:
            self._close_serial_port()

    def _on_send_clicked(self) -> None:
        """Handle send button click."""
        if not self._serial_worker.is_open:
            return

        text = self.tb_send.toPlainText()
        if not text:
            return

        # Append CR+LF if checkbox is checked.
        if self.chk_append_crlf.isChecked():
            text += "\r\n"

        if self._send_mode == "HEX模式":
            data = hex_to_bytes(text)
        else:
            data = text_to_bytes(text, self._send_encoding)

        self._tx_byte_count += len(data)
        self._update_status_counters()

        # Log to file.
        self._data_logger.log("TX", text.rstrip("\n"))

        self._serial_worker.write_data(data)

    def _on_clear_receive(self) -> None:
        """Clear the receive text area."""
        self.tb_receive.clear()
        self._raw_receive_lines = [""]
        self._rx_byte_count = 0
        self._update_status_counters()
        self._clear_search_highlight()

    def _on_clear_send(self) -> None:
        """Clear the send text area."""
        self.tb_send.clear()
        self._tx_byte_count = 0
        self._update_status_counters()

    def _on_data_received(self, data: bytes) -> None:
        """Handle received serial data.

        Args:
            data: Received byte data.
        """
        self._rx_byte_count += len(data)
        self._update_status_counters()

        if self._receive_mode == "HEX模式":
            text = bytes_to_hex(data)
        else:
            text = self._encoding_handler.decode(data)

        # Log to file.
        self._data_logger.log("RX", text.rstrip("\n"))

        # Apply timestamp if enabled.
        if self._show_timestamp:
            display_text = DataLogger.format_timestamped(text)
        else:
            display_text = text

        # Filter check — append to raw buffer.
        lines = display_text.split("\n")
        for line in lines:
            if line or (lines.index(line) == len(lines) - 1):
                self._raw_receive_lines.append(line)

        # Apply filter if active.
        if self.chk_filter.isChecked() and self.search_bar.text():
            keyword = self.search_bar.text()
            for line in lines:
                if line and self._matches_filter(line, keyword):
                    self.tb_receive.moveCursor(
                        QTextCursor.MoveOperation.End
                    )
                    self.tb_receive.insertPlainText(line + "\n")
        else:
            self.tb_receive.moveCursor(QTextCursor.MoveOperation.End)
            self.tb_receive.insertPlainText(display_text)

        # Auto-scroll.
        if self._auto_scroll:
            self.tb_receive.moveCursor(QTextCursor.MoveOperation.End)

    def _on_error(self, message: str) -> None:
        """Handle serial errors.

        Args:
            message: Error message to display.
        """
        self._set_status_badge("error", t("error"))
        QMessageBox.warning(self, t("error"), message)

    def _on_port_disconnected(self) -> None:
        """Handle port disconnection."""
        self._close_serial_port()
        self._set_status_badge("error", t("disconnected"))
        QMessageBox.warning(self, t("warning"), t("port_disconnected"))

    def _on_receive_mode_changed(self, index: int) -> None:
        """Handle receive mode selection change.

        Args:
            index: Selected index in the combo box.
        """
        if index == 0:  # HEX Mode
            self.cb_receive_encoding.setEnabled(False)
            self._receive_mode = "HEX模式"
        else:  # Text Mode
            self.cb_receive_encoding.setEnabled(True)
            self._receive_mode = "文本模式"

        self._encoding_handler.reset()

    def _on_receive_encoding_changed(self, index: int) -> None:
        """Handle receive encoding selection change.

        Args:
            index: Selected index in the combo box.
        """
        del index  # Unused.
        encoding = self.cb_receive_encoding.currentText()
        self._receive_encoding = encoding
        self._encoding_handler.encoding = encoding.lower().replace("-", "")
        self._encoding_handler.reset()

    def _on_send_mode_changed(self, index: int) -> None:
        """Handle send mode selection change.

        Args:
            index: Selected index in the combo box.
        """
        if index == 0:  # HEX Mode
            self.cb_send_encoding.setEnabled(False)
            self._send_mode = "HEX模式"
        else:  # Text Mode
            self.cb_send_encoding.setEnabled(True)
            self._send_mode = "文本模式"

    def _on_send_encoding_changed(self, index: int) -> None:
        """Handle send encoding selection change.

        Args:
            index: Selected index in the combo box.
        """
        del index  # Unused.
        self._send_encoding = self.cb_send_encoding.currentText()
    
    def _on_language_menu_changed(self, lang: str, checked: bool) -> None:
        """Handle language selection from menu.

        Args:
            lang: The selected language code.
            checked: Whether the menu item is checked.
        """
        if not checked:
            return

        I18n.set_lang(lang)

        # Update check states.
        self.act_lang_zh.setChecked(lang == LANG_ZH)
        self.act_lang_en.setChecked(lang == LANG_EN)

        # Update menu visibility based on port state.
        self._update_menu_port_state()

        # Update all UI texts.
        self._update_ui_texts()

    def _on_always_on_top(self, checked: bool) -> None:
        """Toggle always-on-top window flag.

        Args:
            checked: Whether the action is checked.
        """
        if checked:
            self.setWindowFlags(
                self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
            )
        else:
            self.setWindowFlags(
                self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint
            )
        self.show()

    def _on_about(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(self, t("about_title"), t("about_text"))

    def _update_menu_port_state(self) -> None:
        """Update menu item visibility based on port open/close state."""
        self.act_open_port.setVisible(not self._is_port_open)
        self.act_close_port.setVisible(self._is_port_open)
    
    def _update_ui_texts(self) -> None:
        """Update all UI texts after language change."""
        # Window title.
        self.setWindowTitle(t("window_title"))
        
        # Group boxes.
        self.grp_receive.setTitle(t("receive"))
        self.grp_send.setTitle(t("send"))
        self.grp_port_config.setTitle(t("port_config"))
        self.grp_send_receive_config.setTitle(t("send_receive_settings"))
        
        # Port config labels.
        self.lbl_port.setText(t("port"))
        self.lbl_baud_rate.setText(t("baud_rate"))
        self.lbl_data_bits.setText(t("data_bits"))
        self.lbl_stop_bits.setText(t("stop_bits"))
        self.lbl_parity.setText(t("parity"))
        self.lbl_action.setText(t("action"))
        
        # Send/Receive config labels.
        self.lbl_receive_mode.setText(t("receive_mode"))
        self.lbl_receive_encoding.setText(t("receive_encoding"))
        self.lbl_send_mode.setText(t("send_mode"))
        self.lbl_send_encoding.setText(t("send_encoding"))
        
        # Buttons.
        self.btn_clear_receive.setText(t("clear"))
        self.btn_clear_send.setText(t("clear"))
        self.btn_send.setText(t("send_btn"))
        
        # Open/Close button (based on state).
        if self._is_port_open:
            self.btn_open.setText(t("close_port"))
            self._set_status_badge("open", t("connected"))
        else:
            self.btn_open.setText(t("open_port"))
            self._set_status_badge("closed", t("disconnected"))
        
        # Placeholders.
        self.tb_receive.setPlaceholderText(t("waiting_data"))
        self.tb_send.setPlaceholderText(t("enter_data"))
        self.search_bar.setPlaceholderText(t("search_placeholder"))
        
        # Combo box items.
        self._update_parity_items()
        self._update_receive_mode_items()
        self._update_send_mode_items()
        
        # Toolbar checkboxes.
        self.chk_timestamp.setText(t("show_timestamp"))
        self.chk_auto_scroll.setText(t("auto_scroll"))
        self.chk_filter.setText(t("filter_mode"))
        self.chk_regex.setText(t("regex_mode"))
        self.chk_append_crlf.setText(t("append_crlf"))
        
        # Menu bar texts.
        self.menu_file.setTitle(t("menu_file"))
        self.menu_edit.setTitle(t("menu_edit"))
        self.menu_view.setTitle(t("menu_view"))
        self.menu_help.setTitle(t("menu_help"))
        self.act_open_port.setText(t("menu_open_port"))
        self.act_close_port.setText(t("menu_close_port"))
        self.act_exit.setText(t("menu_exit"))
        self.act_record.setText(t("record_log"))
        self.act_export_txt.setText(t("export_txt"))
        self.act_find.setText(t("find"))
        self.act_clear_receive.setText(t("menu_clear_receive"))
        self.act_clear_send.setText(t("menu_clear_send"))
        self.act_always_on_top.setText(t("menu_always_on_top"))
        self.menu_language.setTitle(t("menu_language"))
        self.act_lang_zh.setText(t("lang_zh"))
        self.act_lang_en.setText(t("lang_en"))
        self.act_about.setText(t("menu_about"))
        
        # Status bar counters.
        self._update_status_counters()

    def _on_timestamp_toggled(self, checked: bool) -> None:
        """Toggle timestamp display in receive area.

        Args:
            checked: Whether the checkbox is checked.
        """
        self._show_timestamp = checked

    def _on_auto_scroll_toggled(self, checked: bool) -> None:
        """Toggle auto-scroll in receive area.

        Args:
            checked: Whether the checkbox is checked.
        """
        self._auto_scroll = checked

    def _on_record_toggled(self, checked: bool) -> None:
        """Toggle log recording.

        Args:
            checked: Whether the record action is checked.
        """
        if checked:
            filepath, _ = QFileDialog.getSaveFileName(
                self, t("record_log"), "", "Log Files (*.log);;Text Files (*.txt);;All Files (*)"
            )
            if filepath:
                if self._data_logger.start_recording(filepath):
                    self.lbl_status_rec.setVisible(True)
                else:
                    self.act_record.setChecked(False)
                    QMessageBox.warning(self, t("warning"), t("open_failed"))
            else:
                self.act_record.setChecked(False)
        else:
            self._data_logger.stop_recording()
            self.lbl_status_rec.setVisible(False)

    def _on_export_txt(self) -> None:
        """Export receive buffer content to a text file."""
        content = self.tb_receive.toPlainText()
        if not content:
            QMessageBox.information(self, t("export_txt"), t("no_data"))
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, t("export_txt"), "", "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            if DataLogger.export_txt(filepath, content):
                self.statusBar().showMessage(t("export_success"), 3000)
            else:
                QMessageBox.warning(self, t("warning"), t("open_failed"))

    def _on_find(self) -> None:
        """Focus the search bar in the receive area."""
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def _on_search_text_changed(self, text: str) -> None:
        """Handle search text changes — update highlight and match count.

        Args:
            text: Current search text.
        """
        if not text:
            self._clear_search_highlight()
            self.lbl_match_count.setText("")
            return

        self._highlight_matches(text)

    def _on_search_next(self) -> None:
        """Navigate to the next search match."""
        if not self._search_matches:
            return
        self._current_match_index = (
            (self._current_match_index + 1) % len(self._search_matches)
        )
        self._scroll_to_match(self._current_match_index)

    def _on_filter_toggled(self, checked: bool) -> None:
        """Toggle filter mode — show only matching lines.

        Args:
            checked: Whether filter is enabled.
        """
        keyword = self.search_bar.text()
        if checked and keyword:
            self._apply_filter(keyword)
        elif not checked:
            self._restore_from_filter()

    def _on_regex_toggled(self, checked: bool) -> None:
        """Toggle regex mode and re-run search.

        Args:
            checked: Whether regex is enabled.
        """
        keyword = self.search_bar.text()
        if keyword:
            self._highlight_matches(keyword)
        if self.chk_filter.isChecked() and keyword:
            self._apply_filter(keyword)

    def _matches_filter(self, line: str, keyword: str) -> bool:
        """Check if a line matches the filter keyword.

        Args:
            line: The text line to check.
            keyword: The search keyword.

        Returns:
            True if the line matches.
        """
        if self.chk_regex.isChecked():
            try:
                return bool(re.search(keyword, line))
            except re.error:
                return False
        else:
            return keyword.lower() in line.lower()

    def _highlight_matches(self, keyword: str) -> None:
        """Highlight all matches of keyword in the receive area.

        Args:
            keyword: The text to highlight.
        """
        self._clear_search_highlight()
        self._search_matches = []
        self._current_match_index = -1

        if not keyword:
            self.lbl_match_count.setText("")
            return

        document = self.tb_receive.document()
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#FEF08A"))  # Yellow highlight.

        if self.chk_regex.isChecked():
            try:
                regex = QRegularExpression(keyword)
            except Exception:
                self.lbl_match_count.setText("0")
                return
            cursor = QTextCursor(document)
            while True:
                cursor = document.find(regex, cursor)
                if cursor.isNull():
                    break
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = fmt
                self._search_matches.append(selection)
        else:
            cursor = QTextCursor(document)
            while True:
                cursor = document.find(keyword, cursor, QTextDocument.FindFlag.FindCaseSensitively)
                if cursor.isNull():
                    break
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format = fmt
                self._search_matches.append(selection)

        self.tb_receive.setExtraSelections(self._search_matches)
        count = len(self._search_matches)
        self.lbl_match_count.setText(str(count) if count > 0 else t("no_match"))

    def _clear_search_highlight(self) -> None:
        """Clear all search highlights."""
        self._search_matches = []
        self._current_match_index = -1
        self.tb_receive.setExtraSelections([])

    def _scroll_to_match(self, index: int) -> None:
        """Scroll to a specific match by index.

        Args:
            index: Index of the match to scroll to.
        """
        if 0 <= index < len(self._search_matches):
            self.tb_receive.setTextCursor(self._search_matches[index].cursor)
            self.tb_receive.ensureCursorVisible()

    def _apply_filter(self, keyword: str) -> None:
        """Rebuild receive area showing only matching lines.

        Args:
            keyword: The filter keyword.
        """
        self.tb_receive.clear()
        for line in self._raw_receive_lines:
            if line and self._matches_filter(line, keyword):
                self.tb_receive.moveCursor(QTextCursor.MoveOperation.End)
                self.tb_receive.insertPlainText(line + "\n")

    def _restore_from_filter(self) -> None:
        """Restore receive area to show all buffered lines."""
        self.tb_receive.clear()
        for line in self._raw_receive_lines:
            self.tb_receive.moveCursor(QTextCursor.MoveOperation.End)
            self.tb_receive.insertPlainText(line + "\n")
        if self._auto_scroll:
            self.tb_receive.moveCursor(QTextCursor.MoveOperation.End)

    def _build_font_submenu(self) -> None:
        """Build the font submenu under the View menu.

        Populates monospace and proportional font groups from
        QFontDatabase, plus a font-size submenu and a monospace-only toggle.
        """
        self.menu_font = self.menu_view.addMenu(t("menu_font"))

        # --- Monospace font group ---
        self._font_mono_group = QActionGroup(self)
        self._font_mono_group.setExclusive(True)

        mono_header = QAction(t("font_mono_group"), self)
        mono_header.setEnabled(False)
        self.menu_font.addAction(mono_header)

        all_families = QFontDatabase.families()
        mono_families = [f for f in all_families if QFontDatabase.isFixedPitch(f)]
        prop_families = [f for f in all_families if not QFontDatabase.isFixedPitch(f)]

        self._font_actions: dict[str, QAction] = {}
        for family in mono_families[:20]:
            act = QAction(family, self)
            act.setCheckable(True)
            act.setChecked(family == self._current_font_family)
            act.setActionGroup(self._font_mono_group)
            act.triggered.connect(
                lambda checked, f=family: self._on_font_changed(f)
            )
            self.menu_font.addAction(act)
            self._font_actions[family] = act

        # --- Proportional font group ---
        self.menu_font.addSeparator()
        self._font_prop_group = QActionGroup(self)
        self._font_prop_group.setExclusive(True)

        prop_header = QAction(t("font_prop_group"), self)
        prop_header.setEnabled(False)
        self.menu_font.addAction(prop_header)

        for family in prop_families[:20]:
            act = QAction(family, self)
            act.setCheckable(True)
            act.setChecked(family == self._current_font_family)
            act.setActionGroup(self._font_prop_group)
            act.triggered.connect(
                lambda checked, f=family: self._on_font_changed(f)
            )
            self.menu_font.addAction(act)
            self._font_actions[family] = act

        # --- Font size submenu ---
        self.menu_font.addSeparator()
        self.menu_font_size = self.menu_font.addMenu(t("font_size"))

        self._size_group = QActionGroup(self)
        self._size_group.setExclusive(True)
        self._size_actions: dict[int, QAction] = {}

        for size in (8, 9, 10, 11, 12, 14, 16, 18, 20, 24):
            act = QAction(str(size), self)
            act.setCheckable(True)
            act.setChecked(size == self._current_font_size)
            act.setActionGroup(self._size_group)
            act.triggered.connect(
                lambda checked, s=size: self._on_font_size_changed(s)
            )
            self.menu_font_size.addAction(act)
            self._size_actions[size] = act

        # --- Monospace-only toggle ---
        self.menu_font.addSeparator()
        self.act_mono_only = QAction(t("mono_only"), self)
        self.act_mono_only.setCheckable(True)
        self.act_mono_only.setChecked(self._mono_only)
        self.act_mono_only.triggered.connect(self._on_mono_only_toggled)
        self.menu_font.addAction(self.act_mono_only)

    def _on_font_changed(self, family: str) -> None:
        """Handle font family selection from menu.

        Args:
            family: The selected font family name.
        """
        self._current_font_family = family
        self._apply_editor_font()
        # Update check states for both groups.
        for fam, act in self._font_actions.items():
            act.setChecked(fam == family)

    def _on_font_size_changed(self, size: int) -> None:
        """Handle font size selection from menu.

        Args:
            size: The selected font size.
        """
        self._current_font_size = size
        self._apply_editor_font()
        for s, act in self._size_actions.items():
            act.setChecked(s == size)

    def _on_mono_only_toggled(self, checked: bool) -> None:
        """Toggle monospace-only filter for font list.

        Args:
            checked: Whether the action is checked.
        """
        self._mono_only = checked
        # Rebuild font submenu with filter applied.
        self._rebuild_font_list()

    def _rebuild_font_list(self) -> None:
        """Rebuild font list items based on mono_only filter."""
        all_families = QFontDatabase.families()
        mono_families = [f for f in all_families if QFontDatabase.isFixedPitch(f)]
        prop_families = [f for f in all_families if not QFontDatabase.isFixedPitch(f)]

        # Update mono group visibility.
        for family in mono_families[:20]:
            if family in self._font_actions:
                self._font_actions[family].setVisible(True)

        # Update proportional group visibility.
        for family in prop_families[:20]:
            if family in self._font_actions:
                self._font_actions[family].setVisible(not self._mono_only)

    def _apply_editor_font(self) -> None:
        """Apply the current font settings to receive and send editors."""
        font = QFont(self._current_font_family, self._current_font_size)
        self.tb_receive.setFont(font)
        self.tb_send.setFont(font)

    def _build_baud_rate_list(self) -> None:
        """Rebuild the baud rate combo box with preset + custom values + actions."""
        current_text = self.cb_baud_rate.currentText()
        self.cb_baud_rate.blockSignals(True)
        self.cb_baud_rate.clear()

        # Preset baud rates.
        for baud in self._DEFAULT_BAUDS:
            self.cb_baud_rate.addItem(baud)

        # Custom baud rates.
        if self._custom_bauds:
            self.cb_baud_rate.insertSeparator(self.cb_baud_rate.count())
            for baud in self._custom_bauds:
                self.cb_baud_rate.addItem(f"★ {baud}")

        # Action items at the bottom.
        self.cb_baud_rate.insertSeparator(self.cb_baud_rate.count())
        self._baud_add_index = self.cb_baud_rate.count()
        self.cb_baud_rate.addItem(f"➕ {t('add_custom_baud')}")
        self._baud_edit_index = self.cb_baud_rate.count()
        self.cb_baud_rate.addItem(f"✏️ {t('edit_custom_baud')}")

        # Restore previous selection.
        idx = self.cb_baud_rate.findText(current_text)
        if idx >= 0:
            self.cb_baud_rate.setCurrentIndex(idx)
        else:
            # Try without ★ prefix (in case list was rebuilt).
            clean = current_text.replace("★ ", "")
            idx = self.cb_baud_rate.findText(clean)
            if idx >= 0:
                self.cb_baud_rate.setCurrentIndex(idx)
            else:
                self.cb_baud_rate.setCurrentIndex(12)  # Default: 115200

        self.cb_baud_rate.blockSignals(False)

    def _on_baud_rate_activated(self, index: int) -> None:
        """Handle baud rate combo box selection.

        Intercepts clicks on special action items (add/edit) and
        prevents them from being selected as baud rate values.

        Args:
            index: The activated index.
        """
        text = self.cb_baud_rate.currentText()

        if index == self._baud_add_index or text.startswith("➕"):
            self._add_custom_baud()
        elif index == self._baud_edit_index or text.startswith("✏️"):
            self._manage_custom_bauds()
        # else: normal baud rate selection, do nothing extra.

    def _add_custom_baud(self) -> None:
        """Show dialog to add a custom baud rate value."""
        from PySide6.QtWidgets import QInputDialog

        value, ok = QInputDialog.getInt(
            self,
            t("custom_baud_title"),
            t("custom_baud_label"),
            230400,  # default
            1,       # min
            10000000,  # max
        )

        if not ok:
            return

        baud_str = str(value)

        # Check duplicates (preset + custom).
        if baud_str in self._DEFAULT_BAUDS or baud_str in self._custom_bauds:
            QMessageBox.warning(self, t("warning"), t("custom_baud_exists"))
            return

        # Add to custom list and rebuild.
        self._custom_bauds.append(baud_str)
        self._build_baud_rate_list()

        # Select the newly added item.
        idx = self.cb_baud_rate.findText(f"★ {baud_str}")
        if idx >= 0:
            self.cb_baud_rate.setCurrentIndex(idx)

    def _manage_custom_bauds(self) -> None:
        """Show dialog to manage (delete) custom baud rates."""
        if not self._custom_bauds:
            return

        from PySide6.QtWidgets import QDialog, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle(t("custom_baud_manage"))
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        for baud in self._custom_bauds:
            list_widget.addItem(f"★ {baud}")
        layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()
        btn_delete = QPushButton(t("delete"))
        btn_delete.setProperty("danger", True)
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)

        def _delete_selected() -> None:
            row = list_widget.currentRow()
            if row >= 0:
                removed = self._custom_bauds.pop(row)
                list_widget.takeItem(row)

        btn_delete.clicked.connect(_delete_selected)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(dialog.accept)
        layout.addWidget(btn_box)

        dialog.exec()

        # Rebuild combo box with updated custom list.
        self._build_baud_rate_list()

    def _check_port_status(self) -> None:
        """Periodic check for port status (fallback hot-plug detection)."""
        if self._is_port_open:
            if not self._serial_worker.is_open:
                self._close_serial_port()

    def nativeEvent(
        self, event_type: bytes, message: int
    ) -> Tuple[bool, Optional[int]]:
        """Handle Windows native events for USB hot-plug detection.

        Args:
            event_type: The type of native event.
            message: The native message pointer.

        Returns:
            A tuple of (handled, result).
        """
        try:
            if event_type == b"windows_generic_MSG":
                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == WM_DEVICECHANGE:
                    if msg.wParam == DBT_DEVICEREMOVECOMPLETE:
                        if self._is_port_open:
                            if not self._serial_worker.is_open:
                                self._close_serial_port()
        except Exception:  # pylint: disable=broad-except
            pass

        return super().nativeEvent(event_type, message)

    def closeEvent(self, event) -> None:
        """Handle window close event.

        Args:
            event: The close event.
        """
        self._check_timer.stop()

        if self._serial_worker.is_open:
            self._serial_worker.close_port()

        self._data_logger.close()

        event.accept()
