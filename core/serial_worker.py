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

"""Serial Port Worker Thread Module.

Provides asynchronous serial port communication using QThread.
Data is passed to the UI thread via Qt signals.
"""

from typing import List, Optional

import serial
from serial.tools import list_ports
from PySide6.QtCore import QMutex, QThread, Signal


class SerialWorker(QThread):
    """Worker thread for serial port communication.

    Handles serial data reading in a separate thread to avoid blocking the UI.
    Communicates with the main thread using Qt signals.

    Attributes:
        data_received: Signal emitted when data is received (bytes).
        error_occurred: Signal emitted on error (str).
        port_disconnected: Signal emitted when port disconnects.
    """

    # Qt signals for thread communication.
    data_received = Signal(bytes)
    error_occurred = Signal(str)
    port_disconnected = Signal()

    def __init__(self, parent=None) -> None:
        """Initialize the serial worker.

        Args:
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._mutex = QMutex()

    @property
    def serial_port(self) -> Optional[serial.Serial]:
        """Get the underlying serial port object."""
        return self._serial

    @property
    def is_open(self) -> bool:
        """Check if the serial port is currently open."""
        return self._serial is not None and self._serial.is_open

    def open_port(
        self,
        port_name: str,
        baud_rate: int,
        data_bits: int,
        stop_bits: float,
        parity: str,
    ) -> bool:
        """Open a serial port with the specified parameters.

        Args:
            port_name: Serial port name (e.g., 'COM1').
            baud_rate: Communication baud rate.
            data_bits: Number of data bits (5-8).
            stop_bits: Number of stop bits (1, 1.5, or 2).
            parity: Parity setting ('N', 'O', or 'E').

        Returns:
            True if port opened successfully, False otherwise.
        """
        # Map stop bits to pyserial constants.
        stop_bits_map = {
            1: serial.STOPBITS_ONE,
            1.5: serial.STOPBITS_ONE_POINT_FIVE,
            2: serial.STOPBITS_TWO,
        }

        # Map parity to pyserial constants.
        parity_map = {
            "N": serial.PARITY_NONE,
            "O": serial.PARITY_ODD,
            "E": serial.PARITY_EVEN,
        }

        try:
            self._serial = serial.Serial(
                port=port_name,
                baudrate=baud_rate,
                bytesize=data_bits,
                stopbits=stop_bits_map.get(stop_bits, serial.STOPBITS_ONE),
                parity=parity_map.get(parity, serial.PARITY_NONE),
                timeout=0.1,  # 100ms timeout
            )
            return True
        except serial.SerialException as e:
            self.error_occurred.emit(f"Failed to open port: {e}")
            return False

    def close_port(self) -> None:
        """Close the serial port and stop the worker thread."""
        self._running = False
        self.wait(500)  # Wait for thread to finish.

        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:  # pylint: disable=broad-except
                pass
        self._serial = None

    def write_data(self, data: bytes) -> bool:
        """Write data to the serial port.

        Args:
            data: Byte data to send.

        Returns:
            True if data was sent successfully, False otherwise.
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
            self.error_occurred.emit(f"Send failed: {e}")
            return False

    def run(self) -> None:
        """Thread main loop - continuously read from serial port."""
        self._running = True

        while self._running and self._serial:
            try:
                if self._serial.is_open:
                    if self._serial.in_waiting > 0:
                        self._mutex.lock()
                        data = self._serial.read(self._serial.in_waiting)
                        self._mutex.unlock()
                        if data:
                            self.data_received.emit(data)
                else:
                    self.port_disconnected.emit()
                    break
            except serial.SerialException:
                self.port_disconnected.emit()
                break
            except Exception:  # pylint: disable=broad-except
                pass

            # Brief sleep to reduce CPU usage.
            self.msleep(10)

    def stop(self) -> None:
        """Stop the worker thread."""
        self._running = False


def get_available_ports() -> List[str]:
    """Get a list of available serial port names.

    Returns:
        List of serial port device names.
    """
    ports = list_ports.comports()
    return [port.device for port in ports]
