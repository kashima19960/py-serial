# Serial Assistant (PySide6 Edition)

A modern, lightweight serial debugging tool built with PySide6.
Ported from the Jiangxie Technology C# WinForms Serial Assistant.

## Project Structure

```
py-serial/
├── main.py                 # Application entry point
├── build.py                # Nuitka build script
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── core/                   # Core functionality modules
│   ├── __init__.py
│   ├── serial_worker.py    # Serial port worker thread
│   └── encoding_handler.py # Encoding utilities
└── ui/                     # User interface modules
    ├── __init__.py
    ├── main_window.py      # Main application window
    └── styles.py           # UI theme and styles
```

## Tech Stack

- **Language:** Python 3.8+
- **GUI Framework:** PySide6 (Qt6)
- **Serial Library:** pyserial
- **Build Tool:** Nuitka

## Features

### User Interface

- Modern light theme with clean, professional design
- Left-right split layout: receive/send areas on left, configuration on right
- Responsive and accessible interface

### Serial Port Functions

- ✅ Auto-scan available serial ports (refresh on dropdown)
- ✅ Configurable: baud rate, data bits, stop bits, parity
- ✅ Multi-threaded reception (QThread + Signal)
- ✅ USB hot-plug detection

### Data Processing

- ✅ HEX/Text mode switching (receive/send)
- ✅ GBK/UTF-8 encoding support
- ✅ Incremental decoder for handling packet fragmentation

## Quick Start

### Running the Application

```bash
python main.py
```

### Building Executable

```bash
python build.py
```

Or manually:

```bash
python -m nuitka --standalone --onefile --enable-plugin=pyside6 \
    --windows-disable-console main.py
```

### Installing Dependencies

```bash
pip install -r requirements.txt
```

## Implementation Notes

| C# Original                | Python Implementation        |
| -------------------------- | ---------------------------- |
| `SerialPort` class         | `pyserial` library           |
| `DataReceived` event       | `QThread` + `Signal`         |
| `DefWndProc` message       | `nativeEvent` + timer        |
| `BytesToText` fragmentation| `codecs.IncrementalDecoder`  |
| `TableLayoutPanel` layout  | `QGridLayout` + `QHBoxLayout`|

## Version History

- **v1.2.0** - Modern UI redesign with light theme
- **v1.1.0** - PySide6 port from PyQt5
- **v1.0.0** - Initial Python port from C#

