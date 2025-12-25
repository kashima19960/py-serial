# -*- coding: utf-8 -*-
"""
主窗口模块

移植自 C# WinForms Form1，实现左右布局的串口助手界面。
包含接收区、发送区和配置区。
"""

import ctypes
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QTextEdit, QLineEdit, QPushButton, QComboBox,
    QLabel, QSplitter, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from core.serial_worker import SerialWorker, get_available_ports
from core.encoding_handler import (
    EncodingHandler, bytes_to_hex, hex_to_bytes, text_to_bytes
)


# Windows 消息常量
WM_DEVICECHANGE = 0x0219
DBT_DEVICEREMOVECOMPLETE = 0x8004


class MainWindow(QMainWindow):
    """
    串口助手主窗口
    
    移植自 C# WinForms，采用左右布局：
    - 左侧：接收区（上）和发送区（下）
    - 右侧：串口配置、接收设置、发送设置
    """
    
    def __init__(self):
        super().__init__()
        
        # 初始化串口工作线程
        self._serial_worker = SerialWorker()
        self._serial_worker.data_received.connect(self._on_data_received)
        self._serial_worker.error_occurred.connect(self._on_error)
        self._serial_worker.port_disconnected.connect(self._on_port_disconnected)
        
        # 初始化编码处理器
        self._encoding_handler = EncodingHandler('gbk')
        
        # 模式和编码状态（移植自 C#）
        self._receive_mode = 'HEX模式'
        self._receive_coding = 'GBK'
        self._send_mode = 'HEX模式'
        self._send_coding = 'GBK'
        
        # 初始化 UI
        self._init_ui()
        self._init_connections()
        self._init_default_values()
        
        # 定时器用于检测串口状态（备用方案）
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._check_port_status)
        self._check_timer.start(1000)  # 每秒检查一次
    
    def _init_ui(self):
        """初始化界面布局（移植自 Form1.Designer.cs）"""
        self.setWindowTitle('串口助手 V1.1 (PyQt5)')
        self.resize(800, 500)
        self.setMinimumSize(750, 450)
        
        # 设置字体
        font = QFont('Microsoft YaHei', 9)
        self.setFont(font)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局：左右分割
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)
        
        # 使用 QSplitter 实现可调整的左右分割
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # ===== 左侧面板（接收区 + 发送区）=====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        
        # -- 接收区 GroupBox --
        receive_group = QGroupBox('接收区')
        receive_layout = QVBoxLayout(receive_group)
        
        self.tb_receive = QTextEdit()
        self.tb_receive.setReadOnly(True)
        self.tb_receive.setFont(QFont('Consolas', 10))
        self.tb_receive.setLineWrapMode(QTextEdit.WidgetWidth)
        receive_layout.addWidget(self.tb_receive, 1)
        
        # 接收区按钮行
        receive_btn_layout = QHBoxLayout()
        receive_btn_layout.addStretch()
        self.btn_clear_receive = QPushButton('清空接收区')
        self.btn_clear_receive.setMinimumWidth(110)
        receive_btn_layout.addWidget(self.btn_clear_receive)
        receive_layout.addLayout(receive_btn_layout)
        
        left_layout.addWidget(receive_group, 2)
        
        # -- 发送区 GroupBox --
        send_group = QGroupBox('发送区')
        send_layout = QVBoxLayout(send_group)
        
        self.tb_send = QTextEdit()
        self.tb_send.setFont(QFont('Consolas', 10))
        self.tb_send.setMaximumHeight(80)
        send_layout.addWidget(self.tb_send, 1)
        
        # 发送区按钮行
        send_btn_layout = QHBoxLayout()
        send_btn_layout.addStretch()
        self.btn_clear_send = QPushButton('清空发送区')
        self.btn_clear_send.setMinimumWidth(110)
        send_btn_layout.addWidget(self.btn_clear_send)
        self.btn_send = QPushButton('发送')
        self.btn_send.setMinimumWidth(80)
        self.btn_send.setEnabled(False)
        send_btn_layout.addWidget(self.btn_send)
        send_layout.addLayout(send_btn_layout)
        
        left_layout.addWidget(send_group, 1)
        
        splitter.addWidget(left_panel)
        
        # ===== 右侧面板（配置区）=====
        right_panel = QWidget()
        right_panel.setFixedWidth(220)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        
        # -- 串口配置 GroupBox --
        port_group = QGroupBox('串口配置')
        port_layout = QGridLayout(port_group)
        port_layout.setSpacing(8)
        
        # 串口号
        port_layout.addWidget(QLabel('串口号'), 0, 0)
        self.cb_port_name = QComboBox()
        self.cb_port_name.setMinimumWidth(130)
        self.cb_port_name.setFont(QFont('Microsoft YaHei', 9))
        port_layout.addWidget(self.cb_port_name, 0, 1)
        
        # 波特率
        port_layout.addWidget(QLabel('波特率'), 1, 0)
        self.cb_baud_rate = QComboBox()
        self.cb_baud_rate.addItems(['300', '600', '1200', '2400', '4800', '9600', '14400', '19200', '38400', '43000', '56000', '57600', '115200', '128000', '256000'])
        self.cb_baud_rate.setFont(QFont('Microsoft YaHei', 9))
        self.cb_baud_rate.setMinimumWidth(130)
        port_layout.addWidget(self.cb_baud_rate, 1, 1)
        
        # 数据位
        port_layout.addWidget(QLabel('数据位'), 2, 0)
        self.cb_data_bits = QComboBox()
        self.cb_data_bits.addItems(['5', '6', '7', '8'])
        self.cb_data_bits.setFont(QFont('Microsoft YaHei', 9))
        port_layout.addWidget(self.cb_data_bits, 2, 1)
        
        # 停止位
        port_layout.addWidget(QLabel('停止位'), 3, 0)
        self.cb_stop_bits = QComboBox()
        self.cb_stop_bits.addItems(['1', '1.5', '2'])
        self.cb_stop_bits.setFont(QFont('Microsoft YaHei', 9))
        port_layout.addWidget(self.cb_stop_bits, 3, 1)
        
        # 校验位
        port_layout.addWidget(QLabel('校验位'), 4, 0)
        self.cb_parity = QComboBox()
        self.cb_parity.addItems(['无', '奇校验', '偶校验'])
        self.cb_parity.setFont(QFont('Microsoft YaHei', 9))
        port_layout.addWidget(self.cb_parity, 4, 1)
        
        # 打开/关闭按钮
        port_layout.addWidget(QLabel('操作'), 5, 0)
        self.btn_open = QPushButton('打开串口')
        self.btn_open.setObjectName('btn_open')
        port_layout.addWidget(self.btn_open, 5, 1)
        
        right_layout.addWidget(port_group)
        
        # -- 接收区配置 GroupBox --
        receive_config_group = QGroupBox('接收区配置')
        receive_config_layout = QGridLayout(receive_config_group)
        receive_config_layout.setSpacing(8)
        
        receive_config_layout.addWidget(QLabel('接收模式'), 0, 0)
        self.cb_receive_mode = QComboBox()
        self.cb_receive_mode.addItems(['HEX模式', '文本模式'])
        self.cb_receive_mode.setFont(QFont('Microsoft YaHei', 9))
        self.cb_receive_mode.setMinimumWidth(130)
        receive_config_layout.addWidget(self.cb_receive_mode, 0, 1)
        
        receive_config_layout.addWidget(QLabel('文本编码'), 1, 0)
        self.cb_receive_coding = QComboBox()
        self.cb_receive_coding.addItems(['GBK', 'UTF-8'])
        self.cb_receive_coding.setEnabled(False)
        self.cb_receive_coding.setFont(QFont('Microsoft YaHei', 9))
        self.cb_receive_coding.setMinimumWidth(130)
        receive_config_layout.addWidget(self.cb_receive_coding, 1, 1)
        
        right_layout.addWidget(receive_config_group)
        
        # -- 发送区配置 GroupBox --
        send_config_group = QGroupBox('发送区配置')
        send_config_layout = QGridLayout(send_config_group)
        send_config_layout.setSpacing(8)
        
        send_config_layout.addWidget(QLabel('发送模式'), 0, 0)
        self.cb_send_mode = QComboBox()
        self.cb_send_mode.addItems(['HEX模式', '文本模式'])
        self.cb_send_mode.setFont(QFont('Microsoft YaHei', 9))
        self.cb_send_mode.setMinimumWidth(130)
        send_config_layout.addWidget(self.cb_send_mode, 0, 1)
        
        send_config_layout.addWidget(QLabel('文本编码'), 1, 0)
        self.cb_send_coding = QComboBox()
        self.cb_send_coding.addItems(['GBK', 'UTF-8'])
        self.cb_send_coding.setEnabled(False)
        self.cb_send_coding.setFont(QFont('Microsoft YaHei', 9))
        self.cb_send_coding.setMinimumWidth(130)
        send_config_layout.addWidget(self.cb_send_coding, 1, 1)
        
        right_layout.addWidget(send_config_group)
        
        # 添加弹性空间
        right_layout.addStretch()
        
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
    
    def _init_connections(self):
        """初始化信号槽连接"""
        # 按钮点击事件
        self.btn_open.clicked.connect(self._on_open_clicked)
        self.btn_send.clicked.connect(self._on_send_clicked)
        self.btn_clear_receive.clicked.connect(self._on_clear_receive)
        self.btn_clear_send.clicked.connect(self._on_clear_send)
        
        # 串口下拉框展开事件 - 自动刷新串口列表
        self.cb_port_name.showPopup = self._on_port_dropdown
        
        # 模式/编码选择事件
        self.cb_receive_mode.currentIndexChanged.connect(self._on_receive_mode_changed)
        self.cb_receive_coding.currentIndexChanged.connect(self._on_receive_coding_changed)
        self.cb_send_mode.currentIndexChanged.connect(self._on_send_mode_changed)
        self.cb_send_coding.currentIndexChanged.connect(self._on_send_coding_changed)
    
    def _init_default_values(self):
        """初始化控件默认值（移植自 Form1_Load）"""
        self.cb_baud_rate.setCurrentIndex(5)  # 9600
        self.cb_data_bits.setCurrentIndex(3)  # 8
        self.cb_stop_bits.setCurrentIndex(0)  # 1
        self.cb_parity.setCurrentIndex(0)     # 无
        self.cb_receive_mode.setCurrentIndex(0)  # HEX模式
        self.cb_receive_coding.setCurrentIndex(0)  # GBK
        self.cb_send_mode.setCurrentIndex(0)  # HEX模式
        self.cb_send_coding.setCurrentIndex(0)  # GBK
        
        # 刷新串口列表
        self._refresh_port_list()
    
    def _refresh_port_list(self):
        """刷新可用串口列表"""
        current = self.cb_port_name.currentText()
        self.cb_port_name.clear()
        ports = get_available_ports()
        self.cb_port_name.addItems(ports)
        
        # 尝试恢复之前选择的串口
        if current in ports:
            self.cb_port_name.setCurrentText(current)
    
    def _on_port_dropdown(self):
        """串口下拉框展开时刷新列表（移植自 cbPortName_DropDown）"""
        self._refresh_port_list()
        # 调用父类的 showPopup
        QComboBox.showPopup(self.cb_port_name)
    
    def _open_serial_port(self) -> bool:
        """打开串口（移植自 OpenSerialPort）"""
        port_name = self.cb_port_name.currentText()
        if not port_name:
            QMessageBox.warning(self, '提示', '请选择串口')
            return False
        
        try:
            baud_rate = int(self.cb_baud_rate.currentText())
        except ValueError:
            QMessageBox.warning(self, '提示', '波特率无效')
            return False
        
        data_bits = int(self.cb_data_bits.currentText())
        
        # 停止位映射
        stop_bits_map = {'1': 1, '1.5': 1.5, '2': 2}
        stop_bits = stop_bits_map.get(self.cb_stop_bits.currentText(), 1)
        
        # 校验位映射
        parity_map = {'无': 'N', '奇校验': 'O', '偶校验': 'E'}
        parity = parity_map.get(self.cb_parity.currentText(), 'N')
        
        if self._serial_worker.open_port(port_name, baud_rate, data_bits, stop_bits, parity):
            # 启动接收线程
            self._serial_worker.start()
            
            # 更新 UI 状态
            self.btn_open.setText('关闭串口')
            self.btn_open.setStyleSheet('background-color: #ffb6c1;')
            self.btn_send.setEnabled(True)
            self._set_config_enabled(False)
            return True
        else:
            QMessageBox.warning(self, '提示', '串口打开失败')
            return False
    
    def _close_serial_port(self):
        """关闭串口（移植自 CloseSerialPort）"""
        self._serial_worker.close_port()
        
        # 重置编码处理器
        self._encoding_handler.reset()
        
        # 更新 UI 状态
        self.btn_open.setText('打开串口')
        self.btn_open.setStyleSheet('')
        self.btn_send.setEnabled(False)
        self._set_config_enabled(True)
    
    def _set_config_enabled(self, enabled: bool):
        """设置配置控件的启用状态"""
        self.cb_port_name.setEnabled(enabled)
        self.cb_baud_rate.setEnabled(enabled)
        self.cb_data_bits.setEnabled(enabled)
        self.cb_stop_bits.setEnabled(enabled)
        self.cb_parity.setEnabled(enabled)
    
    def _on_open_clicked(self):
        """打开/关闭串口按钮点击事件（移植自 btnOpen_Click）"""
        if self.btn_open.text() == '打开串口':
            self._open_serial_port()
        else:
            self._close_serial_port()
    
    def _on_send_clicked(self):
        """发送按钮点击事件（移植自 btnSend_Click）"""
        if not self._serial_worker.is_open:
            return
        
        text = self.tb_send.toPlainText()
        if not text:
            return
        
        if self._send_mode == 'HEX模式':
            data = hex_to_bytes(text)
        else:
            data = text_to_bytes(text, self._send_coding)
        
        self._serial_worker.write_data(data)
    
    def _on_clear_receive(self):
        """清空接收区（移植自 btnClearReceive_Click）"""
        self.tb_receive.clear()
    
    def _on_clear_send(self):
        """清空发送区（移植自 btnClearSend_Click）"""
        self.tb_send.clear()
    
    def _on_data_received(self, data: bytes):
        """
        处理接收到的数据（移植自 serialPort_DataReceived）
        
        Args:
            data: 接收到的字节数据
        """
        if self._receive_mode == 'HEX模式':
            text = bytes_to_hex(data)
        else:
            text = self._encoding_handler.decode(data)
        
        # 追加文本并滚动到底部
        self.tb_receive.moveCursor(self.tb_receive.textCursor().End)
        self.tb_receive.insertPlainText(text)
        self.tb_receive.moveCursor(self.tb_receive.textCursor().End)
    
    def _on_error(self, message: str):
        """处理错误"""
        QMessageBox.warning(self, '错误', message)
    
    def _on_port_disconnected(self):
        """串口断开连接处理"""
        self._close_serial_port()
        QMessageBox.warning(self, '提示', '串口已断开')
    
    def _on_receive_mode_changed(self, index: int):
        """接收模式改变事件（移植自 cbReceiveMode_SelectedIndexChanged）"""
        mode = self.cb_receive_mode.currentText()
        if mode == 'HEX模式':
            self.cb_receive_coding.setEnabled(False)
            self._receive_mode = 'HEX模式'
        else:
            self.cb_receive_coding.setEnabled(True)
            self._receive_mode = '文本模式'
        
        # 重置编码处理器
        self._encoding_handler.reset()
    
    def _on_receive_coding_changed(self, index: int):
        """接收编码改变事件（移植自 cbReceiveCoding_SelectedIndexChanged）"""
        coding = self.cb_receive_coding.currentText()
        self._receive_coding = coding
        self._encoding_handler.encoding = coding.lower().replace('-', '')
        self._encoding_handler.reset()
    
    def _on_send_mode_changed(self, index: int):
        """发送模式改变事件（移植自 cbSendMode_SelectedIndexChanged）"""
        mode = self.cb_send_mode.currentText()
        if mode == 'HEX模式':
            self.cb_send_coding.setEnabled(False)
            self._send_mode = 'HEX模式'
        else:
            self.cb_send_coding.setEnabled(True)
            self._send_mode = '文本模式'
    
    def _on_send_coding_changed(self, index: int):
        """发送编码改变事件（移植自 cbSendCoding_SelectedIndexChanged）"""
        self._send_coding = self.cb_send_coding.currentText()
    
    def _check_port_status(self):
        """定时检查串口状态（备用的热拔插检测方案）"""
        if self.btn_open.text() == '关闭串口':
            if not self._serial_worker.is_open:
                self._close_serial_port()
    
    def nativeEvent(self, event_type, message):
        """
        处理 Windows 原生事件（移植自 DefWndProc）
        
        用于检测 USB 设备的热拔插。
        """
        try:
            if event_type == b'windows_generic_MSG':
                msg = ctypes.wintypes.MSG.from_address(message.__int__())
                if msg.message == WM_DEVICECHANGE:
                    if msg.wParam == DBT_DEVICEREMOVECOMPLETE:
                        # 设备移除，检查串口状态
                        if self.btn_open.text() == '关闭串口':
                            if not self._serial_worker.is_open:
                                self._close_serial_port()
        except Exception:
            pass
        
        return super().nativeEvent(event_type, message)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止定时器
        self._check_timer.stop()
        
        # 关闭串口
        if self._serial_worker.is_open:
            self._serial_worker.close_port()
        
        event.accept()
