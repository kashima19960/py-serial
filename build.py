# -*- coding: utf-8 -*-
"""
Nuitka 打包脚本

使用 Nuitka 将 Python 项目编译为独立可执行文件。
"""

import subprocess
import sys
import os


def build():
    """执行 Nuitka 打包"""
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(project_root, 'main.py')
    
    # Nuitka 编译命令
    cmd = [
        sys.executable, '-m', 'nuitka',
        '--standalone',                    # 独立打包
        '--onefile',                       # 单文件模式
        '--msvc=latest',                   # 使用最新的 MSVC 编译器
        '--enable-plugin=pyqt5',           # PyQt5 插件
        '--windows-disable-console',       # Windows 下禁用控制台
        '--windows-icon-from-ico=icon.ico' if os.path.exists('icon.ico') else '',
        '--output-dir=dist',               # 输出目录
        '--company-name=SerialAssistant',
        '--product-name=串口助手',
        '--file-version=1.1.0',
        '--product-version=1.1.0',
        '--file-description=串口调试助手',
        main_file
    ]
    
    # 移除空字符串参数
    cmd = [c for c in cmd if c]
    
    print('正在编译，请稍候...')
    print(' '.join(cmd))
    
    try:
        subprocess.run(cmd, check=True)
        print('\n编译完成！输出目录: dist/')
    except subprocess.CalledProcessError as e:
        print(f'\n编译失败: {e}')
        sys.exit(1)


if __name__ == '__main__':
    build()
