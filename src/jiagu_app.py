#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK加固工具主应用类
负责协调各个加固模块，管理加固流程
"""

import sys
from PyQt5.QtWidgets import QApplication
from loguru import logger
from src.ui.main_window import MainWindow

class JiaguApp:
    """APK加固工具主应用"""
    
    def __init__(self):
        """初始化应用"""
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        logger.info("初始化加固工具应用")
    
    def run(self):
        """运行应用"""
        self.main_window.show()
        logger.info("显示主窗口")
        return self.app.exec_()
