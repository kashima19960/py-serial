# 串口助手 (PyQt5 版本)

移植自江协科技 C# WinForms 串口助手，使用 PyQt5 + qt_material 实现。

## 项目结构

```
py-serial/
├── main.py                           # 主入口文件
├── build.py                          # Nuitka 打包脚本
├── README.md                         # 项目说明
├── serial_assistant/                 # 主程序包
│   ├── __init__.py
│   ├── core/                         # 核心功能模块
│   │   ├── __init__.py
│   │   ├── serial_worker.py          # 串口工作线程
│   │   └── encoding_handler.py       # 编码处理器
│   └── ui/                           # 用户界面模块
│       ├── __init__.py
│       └── main_window.py            # 主窗口
└── CSharpFile/                       # 原 C# 源码 (参考)
```

## 技术栈

- **语言**: Python 3.8.10
- **GUI 框架**: PyQt5
- **串口库**: pyserial
- **UI 美化**: qt_material
- **打包工具**: Nuitka

## 功能特性

### 界面布局

- 左右分割结构，左侧为接收/发送区，右侧为配置区
- Material Design 风格主题

### 串口功能

- ✅ 自动扫描可用串口 (点击下拉框时刷新)
- ✅ 支持配置: 波特率、数据位、停止位、校验位
- ✅ 多线程接收 (QThread + pyqtSignal)
- ✅ USB 热拔插检测

### 数据处理

- ✅ HEX/文本模式切换 (接收/发送)
- ✅ GBK/UTF-8 编码支持
- ✅ 使用 codecs 增量解码器处理断包问题

## 运行方式

```bash
# 直接运行
python main.py
```

## 打包方式

```bash
# 使用 Nuitka 打包
python build.py

# 或者手动执行
python -m nuitka --standalone --onefile --enable-plugin=pyqt5 --windows-disable-console main.py
```

## 依赖安装

```bash
pip install PyQt5 pyserial qt-material nuitka
```

## 移植说明

| C# 原版                   | Python 实现                       |
| ------------------------- | --------------------------------- |
| `SerialPort` 类         | `pyserial` 库                   |
| `DataReceived` 事件     | `QThread` + `pyqtSignal`      |
| `DefWndProc` 消息处理   | `nativeEvent` + 定时器检测      |
| `BytesToText` 断包处理  | `codecs.IncrementalDecoder`     |
| `TableLayoutPanel` 布局 | `QGridLayout` + `QHBoxLayout` |

## 版本历史

- **v1.1.0** - PyQt5 移植版本
