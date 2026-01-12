#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android APK加固工具主入口
兼容macOS 10.15及以上版本，支持Android SDK 21以上
"""

import sys
import os
from loguru import logger

# 创建log文件夹（如果不存在）
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
os.makedirs(log_dir, exist_ok=True)

# 设置日志配置
logger.add(os.path.join(log_dir, "jiagu.log"), rotation="10 MB", level="INFO")

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.jiagu_app import JiaguApp

if __name__ == "__main__":
    try:
        logger.info("启动APK加固工具")
        app = JiaguApp()
        sys.exit(app.run())
    except Exception as e:
        logger.error(f"启动失败: {e}")
        print(f"错误: {e}")
        sys.exit(1)
