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
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont, QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.encoding_handler import (
    EncodingHandler,
    bytes_to_hex,
    hex_to_bytes,
    text_to_bytes,
)
from core.serial_worker import SerialWorker, get_available_ports
from ui.styles import get_stylesheet
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
        self.statusBar().showMessage(t("ready"))

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

        self.tb_receive = QTextEdit()
        self.tb_receive.setReadOnly(True)
        self.tb_receive.setFont(QFont("Consolas", 10))
        self.tb_receive.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.tb_receive.setAcceptRichText(False)
        self.tb_receive.setPlaceholderText(t("waiting_data"))
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
        self.cb_baud_rate.addItems([
            "300", "600", "1200", "2400", "4800", "9600", "14400",
            "19200", "38400", "43000", "56000", "57600", "115200",
            "128000", "256000"
        ])
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
            self.statusBar().showMessage(
                t("connected_to", port=self.cb_port_name.currentText())
            )
        else:
            self.btn_open.setText(t("open_port"))
            self.btn_open.setProperty("danger", False)
            self.btn_open.setProperty("primary", True)
            self.btn_send.setEnabled(False)
            self._set_config_enabled(True)
            self._set_status_badge("closed", t("disconnected"))
            self.statusBar().showMessage(t("not_connected"))

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

        if self._send_mode == "HEX模式":
            data = hex_to_bytes(text)
        else:
            data = text_to_bytes(text, self._send_encoding)

        self._serial_worker.write_data(data)

    def _on_clear_receive(self) -> None:
        """Clear the receive text area."""
        self.tb_receive.clear()

    def _on_clear_send(self) -> None:
        """Clear the send text area."""
        self.tb_send.clear()

    def _on_data_received(self, data: bytes) -> None:
        """Handle received serial data.

        Args:
            data: Received byte data.
        """
        if self._receive_mode == "HEX模式":
            text = bytes_to_hex(data)
        else:
            text = self._encoding_handler.decode(data)

        # Append text and scroll to bottom.
        self.tb_receive.moveCursor(QTextCursor.MoveOperation.End)
        self.tb_receive.insertPlainText(text)
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
            self.statusBar().showMessage(
                t("connected_to", port=self.cb_port_name.currentText())
            )
        else:
            self.btn_open.setText(t("open_port"))
            self._set_status_badge("closed", t("disconnected"))
            self.statusBar().showMessage(t("not_connected"))
        
        # Placeholders.
        self.tb_receive.setPlaceholderText(t("waiting_data"))
        self.tb_send.setPlaceholderText(t("enter_data"))
        
        # Combo box items.
        self._update_parity_items()
        self._update_receive_mode_items()
        self._update_send_mode_items()
        
        # Menu bar texts.
        self.menu_file.setTitle(t("menu_file"))
        self.menu_edit.setTitle(t("menu_edit"))
        self.menu_view.setTitle(t("menu_view"))
        self.menu_help.setTitle(t("menu_help"))
        self.act_open_port.setText(t("menu_open_port"))
        self.act_close_port.setText(t("menu_close_port"))
        self.act_exit.setText(t("menu_exit"))
        self.act_clear_receive.setText(t("menu_clear_receive"))
        self.act_clear_send.setText(t("menu_clear_send"))
        self.act_always_on_top.setText(t("menu_always_on_top"))
        self.menu_language.setTitle(t("menu_language"))
        self.act_lang_zh.setText(t("lang_zh"))
        self.act_lang_en.setText(t("lang_en"))
        self.act_about.setText(t("menu_about"))

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

        event.accept()
