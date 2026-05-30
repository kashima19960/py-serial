# Serial Assistant

> A modern, lightweight serial debugging tool built with PySide6 (Qt6).
> Ported from the C# WinForms version, rewritten in Python with significant enhancements.

[中文版本](README.md)

---

## Table of Contents

- [Features](#features)
- [UI Overview](#ui-overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Implementation Notes](#implementation-notes)
- [Version History](#version-history)

---

## Features

### Serial Communication

| Feature | Description |
|---------|-------------|
| Auto Port Scan | Automatically refresh available ports when dropdown opens |
| Configurable Parameters | Baud rate, data bits, stop bits, parity |
| Custom Baud Rates | Add, edit, and delete custom baud rate values |
| Port Presets | Save/load parameter combinations for quick switching |
| Multi-threaded Reception | QThread + Signal, non-blocking UI |
| USB Hot-plug Detection | Windows native event listener + timer fallback |

### Data Send & Receive

| Feature | Description |
|---------|-------------|
| HEX / Text Mode | Independently switch HEX or text mode for RX and TX |
| GBK / UTF-8 Encoding | Multi-byte encoding with incremental decoder for packet fragmentation |
| Append CR+LF | Optionally append `\r\n` on send |
| Timestamp Display | Show `[HH:MM:SS]` prefix on each received line |

### Search & Filter

| Feature | Description |
|---------|-------------|
| Live Search | Toolbar search box with keyword highlighting |
| Filter Mode | Show only matching lines, hide unrelated data |
| Regular Expressions | Support regex patterns for advanced matching |

### Data Logging

| Feature | Description |
|---------|-------------|
| Log Recording | Record TX/RX data to file (Ctrl+R) |
| Export TXT | Export receive buffer content to text file (Ctrl+S) |
| Timestamped Logs | Log files include second-precision timestamps |

### Statistics & Status

| Feature | Description |
|---------|-------------|
| RX/TX Byte Counter | Real-time byte count in status bar (auto B/KB/MB scaling) |
| RX/TX Throughput Rate | Real-time throughput display (B/s, KB/s) |
| Port Status Badge | Color-coded indicator: Connected / Disconnected / Error |
| Recording Indicator | Status bar shows recording state |

### UI & Interaction

| Feature | Description |
|---------|-------------|
| Standard Menu Bar | File / Edit / View / Help with full keyboard shortcuts |
| Chinese / English | Real-time language switching, all UI text updates dynamically |
| Font Selection | Choose any system font and size from the View menu |
| Always on Top | Window pin mode (Ctrl+T) |
| Modern Theme | Light professional style with rounded cards and blue accent |

---

## UI Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Menu Bar: File(F) | Edit(E) | View(V) | Help(H)           │
├───────────────────────────────────────┬─────────────────────┤
│  Receive Toolbar                      │  Port Config         │
│  [☑Timestamp] [☑Auto Scroll] [🔍]    │  │ Port             ││
│  ┌────────────────────────────────┐   │  │ Baud Rate        ││
│  │ Receive Area                    │   │  │ Data Bits        ││
│  │ [14:32:05] AA BB CC            │   │  │ Stop Bits        ││
│  │ [14:32:06] DE F0               │   │  │ Parity           ││
│  └────────────────────────────────┘   │  │ [Open Port]      ││
│  [Clear]                              │  │ Status Badge     ││
│                                       │  │ Preset ▼ [Save]  ││
│  Send Area                            │                    ││
│  ┌────────────────────────────────┐   │  TX/RX Settings    ││
│  │ Send Input                      │   │  │ RX Mode/Encoding││
│  └────────────────────────────────┘   │  │ TX Mode/Encoding││
│  [☑CR+LF] [Clear] [Send]             │                    ││
├───────────────────────────────────────┴─────────────────────┤
│  Status: [COM3@115200] [RX:1.2KB] [TX:345B] [512B/s] [●REC]│
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Run

```bash
pip install -r requirements.txt
python main.py
```

### Build Executable

```bash
python build.py
```

Or manually:

```bash
python -m nuitka --standalone --onefile --enable-plugin=pyside6 \
    --windows-disable-console main.py
```

### Run Tests

```bash
python -m unittest discover tests -v
```

---

## Project Structure

```
py-serial/
├── main.py                      # Application entry point
├── build.py                     # Nuitka build script
├── README.md                    # Chinese documentation
├── README_EN.md                 # English documentation
├── requirements.txt             # Dependencies
├── core/                        # Core modules
│   ├── __init__.py
│   ├── serial_worker.py         # Serial worker thread
│   ├── encoding_handler.py      # Encoding utilities
│   ├── data_logger.py           # Data logging & export
│   └── config_manager.py        # Configuration manager
├── ui/                          # UI modules
│   ├── __init__.py
│   ├── main_window.py           # Main window
│   ├── styles.py                # Theme & stylesheet
│   └── i18n.py                  # Internationalization
└── tests/                       # Unit tests
    └── test_data_logger.py      # Data logger tests
```

---

## Tech Stack

| Item | Technology |
|------|------------|
| Language | Python 3.8+ |
| GUI Framework | PySide6 (Qt6) |
| Serial Library | pyserial |
| Build Tool | Nuitka |

---

## Implementation Notes

| C# Original | Python Implementation |
|-------------|----------------------|
| `SerialPort` class | `pyserial` library |
| `DataReceived` event | `QThread` + `Signal` |
| `DefWndProc` message | `nativeEvent` + `QTimer` |
| `BytesToText` fragmentation | `codecs.IncrementalDecoder` |
| `TableLayoutPanel` layout | `QGridLayout` + `QHBoxLayout` |
| `Timer` component | `QTimer` |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | 2026-05 | Data logging & export, search & filter, timestamps, custom baud rates, port presets, RX/TX throughput stats, append CR+LF, font selection, standard menu bar, i18n |
| v1.2 | 2024 | Modern UI redesign with light theme |
| v1.1 | 2024 | Ported from PyQt5 to PySide6 |
| v1.0 | 2024 | Initial Python port from C# |

---

## License

Apache License 2.0
