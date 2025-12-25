# -*- coding: utf-8 -*-
"""
串口工作线程模块

使用 QThread 实现串口数据的异步接收，通过 pyqtSignal 将数据传递给 UI 线程。
"""

from typing import Optional
import serial
from serial.tools import list_ports
from PyQt5.QtCore import QThread, pyqtSignal, QMutex


class SerialWorker(QThread):
    """
    串口工作线程
    
    负责在独立线程中进行串口数据的读取，避免阻塞主界面。
    通过信号机制将接收到的数据传递给 UI 线程。
    
    Signals:
        data_received: 接收到数据时发出，携带字节数据
        error_occurred: 发生错误时发出，携带错误信息
        port_disconnected: 串口断开连接时发出
    """
    
    # 定义信号
    data_received = pyqtSignal(bytes)  # 数据接收信号
    error_occurred = pyqtSignal(str)   # 错误信号
    port_disconnected = pyqtSignal()   # 串口断开信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._mutex = QMutex()
    
    @property
    def serial_port(self) -> Optional[serial.Serial]:
        """获取串口对象"""
        return self._serial
    
    @property
    def is_open(self) -> bool:
        """检查串口是否打开"""
        return self._serial is not None and self._serial.is_open
    
    def open_port(self, port_name: str, baud_rate: int, data_bits: int,
                  stop_bits: float, parity: str) -> bool:
        """
        打开串口
        
        Args:
            port_name: 串口名称 (如 COM1)
            baud_rate: 波特率
            data_bits: 数据位
            stop_bits: 停止位
            parity: 校验位 ('N', 'O', 'E')
            
        Returns:
            是否成功打开
        """
        try:
            # 停止位映射
            stop_bits_map = {
                1: serial.STOPBITS_ONE,
                1.5: serial.STOPBITS_ONE_POINT_FIVE,
                2: serial.STOPBITS_TWO
            }
            
            # 校验位映射
            parity_map = {
                'N': serial.PARITY_NONE,
                'O': serial.PARITY_ODD,
                'E': serial.PARITY_EVEN
            }
            
            self._serial = serial.Serial(
                port=port_name,
                baudrate=baud_rate,
                bytesize=data_bits,
                stopbits=stop_bits_map.get(stop_bits, serial.STOPBITS_ONE),
                parity=parity_map.get(parity, serial.PARITY_NONE),
                timeout=0.1  # 100ms 超时
            )
            return True
        except serial.SerialException as e:
            self.error_occurred.emit(f"串口打开失败: {str(e)}")
            return False
    
    def close_port(self):
        """关闭串口"""
        self._running = False
        self.wait(500)  # 等待线程结束
        
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None
    
    def write_data(self, data: bytes) -> bool:
        """
        发送数据
        
        Args:
            data: 要发送的字节数据
            
        Returns:
            是否发送成功
        """
        if not self.is_open:
            return False
        
        try:
            self._mutex.lock()
            self._serial.write(data)
            self._mutex.unlock()
            return True
        except serial.SerialException as e:
            self._mutex.unlock()
            self.error_occurred.emit(f"发送失败: {str(e)}")
            return False
    
    def run(self):
        """线程运行函数 - 持续读取串口数据"""
        self._running = True
        
        while self._running and self._serial:
            try:
                if self._serial.is_open:
                    # 检查是否有数据可读
                    if self._serial.in_waiting > 0:
                        self._mutex.lock()
                        data = self._serial.read(self._serial.in_waiting)
                        self._mutex.unlock()
                        if data:
                            self.data_received.emit(data)
                else:
                    # 串口已断开
                    self.port_disconnected.emit()
                    break
            except serial.SerialException:
                # 串口异常断开
                self.port_disconnected.emit()
                break
            except Exception:
                pass
            
            # 短暂休眠，避免 CPU 占用过高
            self.msleep(10)
    
    def stop(self):
        """停止线程"""
        self._running = False


def get_available_ports() -> list:
    """
    获取可用串口列表
    
    Returns:
        串口名称列表
    """
    ports = list_ports.comports()
    return [port.device for port in ports]
