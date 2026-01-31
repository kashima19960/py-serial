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

"""Nuitka Build Script.

Compiles the Python project into a standalone executable using Nuitka.
"""

import os
import subprocess
import sys


def build() -> None:
    """Execute the Nuitka compilation process."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(project_root, "main.py")

    # Build Nuitka command arguments.
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--msvc=latest",
        "--enable-plugin=pyside6",
        "--windows-disable-console",
        "--output-dir=dist",
        "--company-name=SerialAssistant",
        "--product-name=Serial Assistant",
        "--file-version=1.2.0",
        "--product-version=1.2.0",
        "--file-description=Serial Debugging Tool",
        main_file,
    ]

    # Add icon if available.
    icon_path = os.path.join(project_root, "icon.ico")
    if os.path.exists(icon_path):
        cmd.insert(-1, f"--windows-icon-from-ico={icon_path}")

    print("Building application, please wait...")
    print(" ".join(cmd))

    try:
        subprocess.run(cmd, check=True)
        print("\nBuild completed! Output directory: dist/")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()
