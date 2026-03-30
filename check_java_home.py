#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查当前环境变量中的JAVA_HOME
"""

import os
import sys

print(f"Python版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")
print(f"JAVA_HOME环境变量: {os.environ.get('JAVA_HOME')}")

if 'JAVA_HOME' in os.environ:
    java_home = os.environ['JAVA_HOME']
    print(f"JAVA_HOME路径是否存在: {os.path.exists(java_home)}")
    if os.path.exists(java_home):
        print(f"JAVA_HOME路径内容: {os.listdir(java_home)}")

print("\n所有环境变量:")
for key, value in os.environ.items():
    if 'java' in key.lower():
        print(f"{key}: {value}")
