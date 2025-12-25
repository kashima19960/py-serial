# -*- coding: utf-8 -*-
"""
串口助手 - 主入口文件

PyQt5 + qt_material 实现的串口调试工具
移植自 C# WinForms 串口助手
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# 应用 Material Design 主题
from qt_material import apply_stylesheet

from ui.main_window import MainWindow


def main():
    """主函数"""
    # 高 DPI 支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 应用 Material Design 主题
    # 可选主题: dark_teal, dark_cyan, dark_amber, dark_pink, 
    #          light_teal, light_cyan, light_amber, light_pink 等
    apply_stylesheet(app, theme='light_blue.xml')
    
    # 自定义样式补充
    extra_style = """
    QTextEdit {
        font-family: 'Consolas', 'Microsoft YaHei';
    }
    QGroupBox {
        font-weight: bold;
    }
    QPushButton#btn_open[text="关闭串口"] {
        background-color: #ffb6c1;
    }
    """
    app.setStyleSheet(app.styleSheet() + extra_style)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
