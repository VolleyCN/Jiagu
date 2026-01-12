#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口界面
负责显示APK加固工具的主界面，支持批量处理
"""

import os
import sys
import shutil
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QFileDialog, QProgressBar, QGroupBox, QCheckBox,
    QGridLayout, QLineEdit, QTextEdit, QTabWidget, QMessageBox, QSplitter,
    QComboBox, QSpinBox, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont
from loguru import logger

from src.core.apk_parser import BatchAPKParser
from src.core.dex_encryptor import DexProtection
from src.core.resource_obfuscator import ResourceProtection
from src.core.anti_protection import AntiProtection
from src.core.signature_manager import SignatureManager
from src.core.report_generator import ReportGenerator
from src.core.config_manager import ConfigManager
from src.core.channel_packer import ChannelPackageManager

class JiaguThread(QThread):
    """
    加固处理线程
    用于在后台执行APK加固操作，避免阻塞主线程
    """
    progress_updated = pyqtSignal(int, str)
    task_completed = pyqtSignal(dict)
    all_tasks_completed = pyqtSignal(list)
    
    def __init__(self, apk_paths, options):
        """
        初始化加固线程
        :param apk_paths: APK文件路径列表
        :param options: 加固选项
        """
        super().__init__()
        self.apk_paths = apk_paths
        self.options = options
        self.results = []
    
    def run(self):
        """
        执行加固任务
        """
        total = len(self.apk_paths)
        
        for i, apk_path in enumerate(self.apk_paths):
            try:
                # 更新进度
                self.progress_updated.emit(int((i + 1) / total * 100), f"正在处理: {os.path.basename(apk_path)}")
                
                # 执行加固
                result = self._process_apk(apk_path)
                self.results.append(result)
                
                # 发送任务完成信号
                self.task_completed.emit(result)
            except Exception as e:
                logger.error(f"处理APK失败: {e}")
                self.results.append({
                    'success': False,
                    'apk_path': apk_path,
                    'error': str(e)
                })
        
        # 所有任务完成
        self.all_tasks_completed.emit(self.results)
    
    def _process_apk(self, apk_path):
        """
        处理单个APK文件
        :param apk_path: APK文件路径
        :return: 处理结果
        """
        logger.info(f"开始处理APK: {apk_path}")
        
        # 1. 解析APK
        from src.core.apk_parser import BatchAPKParser
        parser = BatchAPKParser([apk_path])
        parse_results = parser.parse_all()
        
        if not parse_results or not parse_results[0]['success']:
            return {
                'success': False,
                'apk_path': apk_path,
                'error': 'APK解析失败'
            }
        
        # 2. 创建输出目录
        output_dir = self.options.get('output_dir', os.path.dirname(apk_path))
        os.makedirs(output_dir, exist_ok=True)
        
        # 3. 执行DEX加密
        if self.options.get('dex_encrypt', True):
            dex_protection = DexProtection()
            dex_result = dex_protection.protect_apk(apk_path, os.path.join(output_dir, f"dex_protected_{os.path.basename(apk_path)}"))
            
            if not dex_result['success']:
                return {
                    'success': False,
                    'apk_path': apk_path,
                    'error': f"DEX加密失败: {dex_result.get('message', '未知错误')}"
                }
        
        # 4. 执行资源混淆
        if self.options.get('resource_obfuscate', True):
            resource_protection = ResourceProtection()
            resource_result = resource_protection.protect_apk_resources(apk_path, os.path.join(output_dir, f"resource_protected_{os.path.basename(apk_path)}"))
            
            if not resource_result['success']:
                # 如果是apktool不可用的错误，不中断整体加固流程
                if 'apktool not found' in str(resource_result.get('error', '')):
                    logger.warning(f"资源混淆跳过: {resource_result.get('error', '未知错误')}")
                    # 继续执行后续加固步骤
                else:
                    return {
                        'success': False,
                        'apk_path': apk_path,
                        'error': f"资源混淆失败: {resource_result.get('message', '未知错误')}"
                    }
        
        # 5. 执行防调试与反逆向保护
        # 检查是否需要启用任何保护功能
        if any(self.options.get(key, True) for key in ['anti_debug', 'anti_root', 'anti_emulator']):
            logger.info("开始执行防调试与反逆向保护")
            
            # 选择要保护的APK（优先使用资源混淆后的，否则使用DEX加密后的，否则使用原始APK）
            apk_to_protect = apk_path
            if os.path.exists(os.path.join(output_dir, f"resource_protected_{os.path.basename(apk_path)}")):
                apk_to_protect = os.path.join(output_dir, f"resource_protected_{os.path.basename(apk_path)}")
            elif os.path.exists(os.path.join(output_dir, f"dex_protected_{os.path.basename(apk_path)}")):
                apk_to_protect = os.path.join(output_dir, f"dex_protected_{os.path.basename(apk_path)}")
            
            # 初始化防保护管理器
            anti_protection = AntiProtection()
            
            # 设置保护功能开关
            for feature in ['anti_debug', 'anti_root', 'anti_emulator', 'anti_hook', 'anti_dump']:
                anti_protection.set_protection_feature(feature, self.options.get(feature, True))
            
            # 应用保护机制，简化实现，移除了apk_parser参数
            protection_result = anti_protection.apply_protection(
                apk_to_protect, 
                apk_to_protect  # 直接在原文件上修改
            )
            
            if protection_result['success']:
                logger.info("防调试与反逆向保护应用成功")
            else:
                logger.warning(f"防调试与反逆向保护应用失败: {protection_result.get('error', '未知错误')}")
                # 继续执行后续步骤，不中断整体流程
        
        # 6. 执行签名验证与重签名
        signature_config = self.options.get('signature', {})
        keystore_path = signature_config.get('keystore', '')
        keystore_pass = signature_config.get('keystore_pass', '')
        key_alias = signature_config.get('key_alias', '')
        key_pass = signature_config.get('key_pass', '')
        
        # 检查签名配置是否完整
        if keystore_path and keystore_pass and key_alias and key_pass:
            try:
                # 使用签名管理器进行签名
                signature_manager = SignatureManager()
                
                # 最终输出的APK路径
                final_output = os.path.join(output_dir, f"protected_{os.path.basename(apk_path)}")
                
                # 选择要签名的APK（优先使用资源混淆后的，否则使用DEX加密后的，否则使用原始APK）
                apk_to_sign = apk_path
                if os.path.exists(os.path.join(output_dir, f"resource_protected_{os.path.basename(apk_path)}")):
                    apk_to_sign = os.path.join(output_dir, f"resource_protected_{os.path.basename(apk_path)}")
                elif os.path.exists(os.path.join(output_dir, f"dex_protected_{os.path.basename(apk_path)}")):
                    apk_to_sign = os.path.join(output_dir, f"dex_protected_{os.path.basename(apk_path)}")
                
                # 执行签名
                sign_result = signature_manager.sign_apk(
                    apk_to_sign,
                    final_output,
                    keystore_path,
                    keystore_pass,
                    key_alias,
                    key_pass
                )
                
                if sign_result['success']:
                    logger.info(f"APK签名完成: {final_output}")
                    
                    # 7. 执行多渠道打包（如果启用，基于瓦力原理，签名后注入渠道信息）
                    channel_packaging = self.options.get('channel_packaging', {})
                    if channel_packaging.get('enabled', False):
                        logger.info("开始执行多渠道打包（基于瓦力原理，签名后注入）")
                        from src.core.channel_packer import ChannelPackageManager
                        channel_manager = ChannelPackageManager()
                        
                        # 准备签名信息（虽然瓦力原理不需要重新签名，但保留接口兼容）
                        keystore_info = {
                            'keystore_path': keystore_path,
                            'keystore_password': keystore_pass,
                            'key_alias': key_alias,
                            'key_password': key_pass,
                            'signature_versions': ['v1', 'v2', 'v3']
                        }
                        
                        # 生成渠道包
                        channel_result = channel_manager.generate_channels(
                            final_output,
                            channel_packaging.get('config_path'),
                            keystore_info
                        )
                        
                        if channel_result['success']:
                            logger.info(f"多渠道打包成功，生成 {channel_result['channel_count']} 个渠道包")
                        else:
                            logger.warning(f"多渠道打包失败: {channel_result['message']}")
                else:
                    logger.error(f"APK签名失败: {sign_result.get('error', '未知错误')}")
                    return {
                        'success': False,
                        'apk_path': apk_path,
                        'error': f"APK签名失败: {sign_result.get('error', '未知错误')}"
                    }
            except Exception as e:
                logger.error(f"签名过程中发生错误: {e}")
                return {
                    'success': False,
                    'apk_path': apk_path,
                    'error': f"签名过程中发生错误: {str(e)}"
                }
        else:
            logger.warning("签名配置不完整，跳过签名步骤")
            # 至少需要有一个输出文件
            final_output = apk_path
            if os.path.exists(os.path.join(output_dir, f"resource_protected_{os.path.basename(apk_path)}")):
                final_output = os.path.join(output_dir, f"resource_protected_{os.path.basename(apk_path)}")
            elif os.path.exists(os.path.join(output_dir, f"dex_protected_{os.path.basename(apk_path)}")):
                final_output = os.path.join(output_dir, f"dex_protected_{os.path.basename(apk_path)}")
        
        logger.info(f"APK处理完成: {final_output}")
        
        return {
            'success': True,
            'apk_path': apk_path,
            'output_path': final_output,
            'output_dir': output_dir,
            'message': 'APK加固完成'
        }

class MainWindow(QMainWindow):
    """
    APK加固工具主窗口
    """
    
    def __init__(self):
        """
        初始化主窗口
        """
        super().__init__()
        self.apk_list = []
        self.options = {
            'dex_encrypt': True,
            'resource_obfuscate': True,
            'anti_debug': True,
            'anti_root': True,
            'anti_emulator': True,
            'output_dir': os.getcwd()
        }
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化渠道配置管理器
        from src.core.channel_manager import ChannelConfigManager
        self.channel_config_manager = ChannelConfigManager()
        
        self.init_ui()
        self.jiagu_thread = None
        
        # 加载配置
        self.load_config()
        
        # 当前选中的渠道索引
        self.current_channel_index = -1
    
    def init_ui(self):
        """
        初始化用户界面
        """
        # 设置窗口属性
        self.setWindowTitle("Android APK加固工具")
        self.setMinimumSize(1000, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建顶部工具栏
        self.create_toolbar(main_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # 创建左侧APK列表和右侧选项面板
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        
        # APK列表
        self.apk_list_group = self.create_apk_list()
        content_layout.addWidget(self.apk_list_group, 1)
        
        # 选项标签页
        self.options_tab = self.create_options_tab()
        content_layout.addWidget(self.options_tab, 1)
        
        splitter.addWidget(content_widget)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # 日志输出
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        splitter.addWidget(self.log_text)
        
        # 允许拖放
        self.setAcceptDrops(True)
    
    def create_toolbar(self, layout):
        """
        创建顶部工具栏
        """
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        
        # 添加APK按钮
        add_btn = QPushButton("添加APK")
        add_btn.clicked.connect(self.add_apk)
        toolbar_layout.addWidget(add_btn)
        
        # 批量添加按钮
        batch_add_btn = QPushButton("批量添加")
        batch_add_btn.clicked.connect(self.batch_add_apk)
        toolbar_layout.addWidget(batch_add_btn)
        
        # 移除选中按钮
        remove_btn = QPushButton("移除选中")
        remove_btn.clicked.connect(self.remove_selected_apk)
        toolbar_layout.addWidget(remove_btn)
        
        # 清空按钮
        clear_btn = QPushButton("清空列表")
        clear_btn.clicked.connect(self.clear_apk_list)
        toolbar_layout.addWidget(clear_btn)
        
        # 输出目录选择
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("输出目录:"))
        
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(os.getcwd())
        self.output_dir_edit.setMinimumWidth(300)
        toolbar_layout.addWidget(self.output_dir_edit)
        
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_output_dir)
        toolbar_layout.addWidget(browse_btn)
        
        # 开始加固按钮
        start_btn = QPushButton("开始加固")
        start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        start_btn.clicked.connect(self.start_jiagu)
        toolbar_layout.addWidget(start_btn)
        
        layout.addWidget(toolbar)
    
    def create_apk_list(self):
        """
        创建APK列表组件
        """
        group_box = QGroupBox("待处理APK列表")
        layout = QVBoxLayout(group_box)
        
        # 列表控件
        list_widget = QListWidget()
        list_widget.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(list_widget)
        
        # 统计信息
        self.apk_count_label = QLabel("共 0 个APK文件")
        layout.addWidget(self.apk_count_label, alignment=Qt.AlignRight)
        
        # 保存列表控件引用
        self.apk_list_widget = list_widget
        
        return group_box
    
    def create_options_tab(self):
        """
        创建选项标签页
        """
        tab_widget = QTabWidget()
        
        # 1. 基本选项
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # DEX加密选项
        dex_group = QGroupBox("DEX文件保护")
        dex_layout = QVBoxLayout(dex_group)
        
        self.dex_encrypt_check = QCheckBox("启用DEX加密")
        self.dex_encrypt_check.setChecked(True)
        dex_layout.addWidget(self.dex_encrypt_check)
        
        basic_layout.addWidget(dex_group)
        
        # 资源混淆选项
        resource_group = QGroupBox("资源文件保护")
        resource_layout = QVBoxLayout(resource_group)
        
        self.resource_obfuscate_check = QCheckBox("启用资源混淆")
        self.resource_obfuscate_check.setChecked(True)
        resource_layout.addWidget(self.resource_obfuscate_check)
        
        basic_layout.addWidget(resource_group)
        
        basic_layout.addStretch()
        tab_widget.addTab(basic_tab, "基本选项")
        
        # 2. 高级选项
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # 防调试选项
        anti_debug_group = QGroupBox("防调试与反逆向")
        anti_debug_layout = QVBoxLayout(anti_debug_group)
        
        self.anti_debug_check = QCheckBox("启用防调试检测")
        self.anti_debug_check.setChecked(True)
        anti_debug_layout.addWidget(self.anti_debug_check)
        
        self.anti_root_check = QCheckBox("启用反Root检测")
        self.anti_root_check.setChecked(True)
        anti_debug_layout.addWidget(self.anti_root_check)
        
        self.anti_emulator_check = QCheckBox("启用反模拟器检测")
        self.anti_emulator_check.setChecked(True)
        anti_debug_layout.addWidget(self.anti_emulator_check)
        
        advanced_layout.addWidget(anti_debug_group)
        
        # 签名选项
        signature_group = QGroupBox("签名设置")
        signature_layout = QGridLayout(signature_group)
        
        signature_layout.addWidget(QLabel("密钥库路径:"), 0, 0)
        self.keystore_edit = QLineEdit()
        signature_layout.addWidget(self.keystore_edit, 0, 1)
        
        browse_keystore_btn = QPushButton("浏览")
        browse_keystore_btn.clicked.connect(self.browse_keystore)
        signature_layout.addWidget(browse_keystore_btn, 0, 2)
        
        signature_layout.addWidget(QLabel("密钥库密码:"), 1, 0)
        self.keystore_pass_edit = QLineEdit()
        self.keystore_pass_edit.setEchoMode(QLineEdit.Password)
        signature_layout.addWidget(self.keystore_pass_edit, 1, 1)
        
        signature_layout.addWidget(QLabel("密钥别名:"), 2, 0)
        self.key_alias_edit = QLineEdit()
        signature_layout.addWidget(self.key_alias_edit, 2, 1)
        
        signature_layout.addWidget(QLabel("密钥密码:"), 3, 0)
        self.key_pass_edit = QLineEdit()
        self.key_pass_edit.setEchoMode(QLineEdit.Password)
        signature_layout.addWidget(self.key_pass_edit, 3, 1)
        
        # 配置管理按钮
        config_layout = QHBoxLayout()
        save_config_btn = QPushButton("保存配置")
        save_config_btn.clicked.connect(self.save_config)
        config_layout.addWidget(save_config_btn)
        
        clear_config_btn = QPushButton("清除配置")
        clear_config_btn.clicked.connect(self.clear_config)
        config_layout.addWidget(clear_config_btn)
        
        signature_layout.addLayout(config_layout, 4, 1, 1, 2)
        
        advanced_layout.addWidget(signature_group)
        
        advanced_layout.addStretch()
        tab_widget.addTab(advanced_tab, "高级选项")
        
        # 3. 多渠道打包选项
        channel_tab = QWidget()
        channel_layout = QVBoxLayout(channel_tab)
        
        # 多渠道打包设置
        channel_group = QGroupBox("多渠道打包")
        channel_group_layout = QVBoxLayout(channel_group)
        
        self.channel_packaging_check = QCheckBox("启用多渠道打包")
        self.channel_packaging_check.setChecked(False)  # 默认禁用
        channel_group_layout.addWidget(self.channel_packaging_check)
        
        # 渠道配置文件
        config_layout = QHBoxLayout()
        config_layout.addWidget(QLabel("渠道配置文件:"))
        self.channel_config_edit = QLineEdit()
        # 默认使用示例配置文件
        default_config = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "channel_config.yaml")
        self.channel_config_edit.setText(default_config)
        config_layout.addWidget(self.channel_config_edit)
        
        browse_channel_config_btn = QPushButton("浏览")
        browse_channel_config_btn.clicked.connect(self.browse_channel_config)
        config_layout.addWidget(browse_channel_config_btn)
        channel_group_layout.addLayout(config_layout)
        
        channel_layout.addWidget(channel_group)
        channel_layout.addStretch()
        tab_widget.addTab(channel_tab, "多渠道打包")
        
        # 4. 渠道管理选项
        channel_manage_tab = QWidget()
        channel_manage_layout = QVBoxLayout(channel_manage_tab)
        
        # 渠道配置文件选择
        manage_config_layout = QHBoxLayout()
        manage_config_layout.addWidget(QLabel("渠道配置文件:"))
        self.channel_manage_config_edit = QLineEdit()
        self.channel_manage_config_edit.setText(default_config)  # 使用相同的默认配置文件
        manage_config_layout.addWidget(self.channel_manage_config_edit)
        
        browse_manage_config_btn = QPushButton("浏览")
        browse_manage_config_btn.clicked.connect(self.browse_channel_manage_config)
        manage_config_layout.addWidget(browse_manage_config_btn)
        
        load_config_btn = QPushButton("加载配置")
        load_config_btn.clicked.connect(self.load_channel_config)
        manage_config_layout.addWidget(load_config_btn)
        
        channel_manage_layout.addLayout(manage_config_layout)
        
        # 渠道列表
        channel_list_group = QGroupBox("渠道列表")
        channel_list_layout = QVBoxLayout(channel_list_group)
        
        # 渠道列表控件
        self.channel_list_widget = QListWidget()
        self.channel_list_widget.setSelectionMode(QListWidget.ExtendedSelection)  # 支持多选
        # 添加点击事件处理
        self.channel_list_widget.itemClicked.connect(self.on_channel_item_clicked)
        channel_list_layout.addWidget(self.channel_list_widget)
        
        # 渠道操作按钮
        channel_ops_layout = QHBoxLayout()
        
        add_channel_btn = QPushButton("新增渠道")
        add_channel_btn.clicked.connect(self.add_channel)
        channel_ops_layout.addWidget(add_channel_btn)
        
        delete_channel_btn = QPushButton("删除选中")
        delete_channel_btn.clicked.connect(self.delete_selected_channels)
        channel_ops_layout.addWidget(delete_channel_btn)
        
        import_channel_btn = QPushButton("批量导入")
        import_channel_btn.clicked.connect(self.import_channels)
        channel_ops_layout.addWidget(import_channel_btn)
        
        channel_ops_layout.addStretch()
        
        # 保存配置按钮
        save_channel_config_btn = QPushButton("保存配置")
        save_channel_config_btn.clicked.connect(self.save_channel_config)
        channel_ops_layout.addWidget(save_channel_config_btn)
        
        channel_list_layout.addLayout(channel_ops_layout)
        channel_manage_layout.addWidget(channel_list_group)
        
        # 渠道详情编辑
        channel_detail_group = QGroupBox("渠道详情")
        channel_detail_layout = QGridLayout(channel_detail_group)
        
        channel_detail_layout.addWidget(QLabel("渠道名称:"), 0, 0)
        self.channel_name_edit = QLineEdit()
        self.channel_name_edit.setPlaceholderText("请输入渠道名称")
        channel_detail_layout.addWidget(self.channel_name_edit, 0, 1)
        
        channel_detail_layout.addWidget(QLabel("渠道ID:"), 1, 0)
        self.channel_id_edit = QLineEdit()
        self.channel_id_edit.setPlaceholderText("请输入渠道ID")
        channel_detail_layout.addWidget(self.channel_id_edit, 1, 1)
        
        channel_detail_layout.addWidget(QLabel("市场名称:"), 2, 0)
        self.channel_market_edit = QLineEdit()
        self.channel_market_edit.setPlaceholderText("请输入市场名称")
        channel_detail_layout.addWidget(self.channel_market_edit, 2, 1)
        
        # 保存渠道详情按钮
        save_channel_btn = QPushButton("保存渠道")
        save_channel_btn.clicked.connect(self.save_channel)
        channel_detail_layout.addWidget(save_channel_btn, 3, 1)
        
        channel_manage_layout.addWidget(channel_detail_group)
        
        channel_manage_layout.addStretch()
        tab_widget.addTab(channel_manage_tab, "渠道管理")
        
        return tab_widget
    
    def add_apk(self):
        """
        添加单个APK文件
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "选择APK文件", ".", "APK文件 (*.apk)")
        if file_path:
            self.add_apk_to_list(file_path)
    
    def batch_add_apk(self):
        """
        批量添加APK文件
        """
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择多个APK文件", ".", "APK文件 (*.apk)")
        for file_path in file_paths:
            self.add_apk_to_list(file_path)
    
    def add_apk_to_list(self, file_path):
        """
        将APK文件添加到列表
        """
        if file_path and file_path not in self.apk_list:
            self.apk_list.append(file_path)
            self.apk_list_widget.addItem(os.path.basename(file_path))
            self.update_apk_count()
            self.log(f"添加APK: {file_path}")
    
    def remove_selected_apk(self):
        """
        移除选中的APK文件
        """
        selected_items = self.apk_list_widget.selectedItems()
        for item in selected_items:
            index = self.apk_list_widget.row(item)
            file_path = self.apk_list.pop(index)
            self.apk_list_widget.takeItem(index)
            self.log(f"移除APK: {file_path}")
        self.update_apk_count()
    
    def clear_apk_list(self):
        """
        清空APK列表
        """
        self.apk_list.clear()
        self.apk_list_widget.clear()
        self.update_apk_count()
        self.log("清空APK列表")
    
    def update_apk_count(self):
        """
        更新APK计数显示
        """
        self.apk_count_label.setText(f"共 {len(self.apk_list)} 个APK文件")
    
    def browse_output_dir(self):
        """
        浏览输出目录
        """
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_dir_edit.text())
        if dir_path:
            self.output_dir_edit.setText(dir_path)
    
    def browse_keystore(self):
        """
        浏览密钥库文件
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "选择密钥库文件", ".", "密钥库文件 (*.jks *.keystore)")
        if file_path:
            self.keystore_edit.setText(file_path)
    
    def browse_channel_config(self):
        """
        浏览选择渠道配置文件
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "选择渠道配置文件", ".", "YAML配置文件 (*.yaml *.yml)")
        if file_path:
            self.channel_config_edit.setText(file_path)
    
    def browse_channel_manage_config(self):
        """
        浏览选择渠道管理配置文件
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "选择渠道配置文件", ".", "YAML配置文件 (*.yaml *.yml)")
        if file_path:
            self.channel_manage_config_edit.setText(file_path)
    
    def load_channel_config(self):
        """
        加载渠道配置文件
        """
        config_path = self.channel_manage_config_edit.text()
        if not os.path.exists(config_path):
            QMessageBox.warning(self, "警告", f"渠道配置文件不存在: {config_path}")
            return
        
        if self.channel_config_manager.load_config(config_path):
            # 加载成功，更新渠道列表
            self.update_channel_list()
            QMessageBox.information(self, "提示", f"成功加载渠道配置，共 {len(self.channel_config_manager.get_channels())} 个渠道")
        else:
            QMessageBox.warning(self, "警告", f"加载渠道配置失败: {config_path}")
    
    def update_channel_list(self):
        """
        更新渠道列表显示
        """
        self.channel_list_widget.clear()
        channels = self.channel_config_manager.get_channels()
        for channel in channels:
            self.channel_list_widget.addItem(channel['name'])
    
    def add_channel(self):
        """
        新增渠道
        """
        # 清空编辑框
        self.channel_name_edit.clear()
        self.channel_market_edit.clear()
        self.channel_id_edit.clear()
        self.app_channel_edit.clear()
        # 设置当前选中索引为-1，表示新增
        self.current_channel_index = -1
        QMessageBox.information(self, "提示", "请在下方填写渠道信息，然后点击'保存渠道'按钮")
    
    def on_channel_item_clicked(self, item):
        """
        渠道列表项点击事件处理，将渠道信息回显到编辑框
        """
        # 获取点击的渠道名称
        channel_name = item.text()
        
        # 获取渠道配置
        channel_config = self.channel_config_manager.get_channel_by_name(channel_name)
        if channel_config:
            # 将渠道信息回显到编辑框
            self.channel_name_edit.setText(channel_config['name'])
            
            # 获取metadata
            metadata = channel_config.get('metadata', {})
            self.channel_id_edit.setText(metadata.get('CHANNEL_ID', channel_name))
            self.channel_market_edit.setText(metadata.get('MARKET_NAME', ''))
            
            # 更新当前选中索引
            self.current_channel_index = self.channel_list_widget.row(item)
    
    def save_channel(self):
        """
        保存渠道信息
        """
        # 获取渠道信息
        channel_name = self.channel_name_edit.text().strip()
        if not channel_name:
            QMessageBox.warning(self, "警告", "渠道名称不能为空")
            return
        
        channel_id = self.channel_id_edit.text().strip() or channel_name
        market_name = self.channel_market_edit.text().strip()
        
        # 构建渠道配置（只保留必要字段：CHANNEL_ID和MARKET_NAME）
        channel_config = {
            'name': channel_name,
            'metadata': {
                'CHANNEL_ID': channel_id,
                'MARKET_NAME': market_name
            }
        }
        
        # 添加或更新渠道
        if self.channel_config_manager.add_channel(channel_config):
            # 更新渠道列表
            self.update_channel_list()
            
            # 保持当前编辑框内容，方便继续修改
            # 重新选中当前渠道（如果是修改现有渠道）
            if self.current_channel_index >= 0 and self.current_channel_index < self.channel_list_widget.count():
                # 保存成功后，重新选中当前渠道
                self.channel_list_widget.setCurrentRow(self.current_channel_index)
            
            QMessageBox.information(self, "提示", f"渠道 '{channel_name}' 保存成功")
        else:
            QMessageBox.warning(self, "警告", f"渠道 '{channel_name}' 保存失败")
    
    def delete_selected_channels(self):
        """
        删除选中的渠道
        """
        selected_items = self.channel_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "请先选择要删除的渠道")
            return
        
        # 二次确认
        channel_names = [item.text() for item in selected_items]
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除选中的 {len(channel_names)} 个渠道吗？\n{', '.join(channel_names)}", 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 删除选中的渠道
            deleted_count = 0
            for channel_name in channel_names:
                if self.channel_config_manager.remove_channel(channel_name):
                    deleted_count += 1
            
            # 更新渠道列表
            self.update_channel_list()
            QMessageBox.information(self, "提示", f"成功删除 {deleted_count} 个渠道")
    
    def import_channels(self):
        """
        批量导入渠道，支持Excel和CSV格式
        """
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择渠道导入文件", ".", 
            "支持的文件格式 (*.xlsx *.csv *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # 导入pandas库
            import pandas as pd
            
            # 读取文件
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, dtype=str)
            else:  # Excel格式
                df = pd.read_excel(file_path, dtype=str)
            
            # 数据验证
            if df.empty:
                QMessageBox.warning(self, "警告", "导入的文件为空")
                return
            
            # 确保包含必要的列
            required_columns = ['channel_name']
            for col in required_columns:
                if col not in df.columns:
                    QMessageBox.warning(self, "警告", f"导入文件缺少必要的列: {col}")
                    return
            
            # 处理数据
            success_count = 0
            error_count = 0
            error_messages = []
            
            # 获取当前渠道列表，用于检查重复
            existing_channels = {channel['name'] for channel in self.channel_config_manager.get_channels()}
            
            for index, row in df.iterrows():
                try:
                    # 获取渠道名称
                    channel_name = row['channel_name'].strip()
                    if not channel_name:
                        error_count += 1
                        error_messages.append(f"第 {index+1} 行: 渠道名称不能为空")
                        continue
                    
                    # 检查渠道名称是否重复
                    if channel_name in existing_channels:
                        error_count += 1
                        error_messages.append(f"第 {index+1} 行: 渠道 '{channel_name}' 已存在")
                        continue
                    
                    # 获取其他可选字段
                    channel_id = row.get('channel_id', channel_name).strip()
                    market_name = row.get('market_name', '').strip()
                    
                    # 构建渠道配置（只保留必要字段：CHANNEL_ID和MARKET_NAME）
                    channel_config = {
                        'name': channel_name,
                        'metadata': {
                            'CHANNEL_ID': channel_id,
                            'MARKET_NAME': market_name
                        }
                    }
                    
                    # 添加渠道
                    if self.channel_config_manager.add_channel(channel_config):
                        success_count += 1
                        existing_channels.add(channel_name)
                    else:
                        error_count += 1
                        error_messages.append(f"第 {index+1} 行: 渠道 '{channel_name}' 添加失败")
                        
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"第 {index+1} 行: 处理失败 - {str(e)}")
            
            # 更新渠道列表
            self.update_channel_list()
            
            # 显示导入结果
            result_message = f"批量导入完成！\n成功导入: {success_count} 个渠道\n失败: {error_count} 个渠道"
            
            if error_count > 0:
                # 如果有错误，显示详细错误信息
                error_details = "\n\n详细错误信息:\n" + "\n".join(error_messages[:10])  # 只显示前10个错误
                if error_count > 10:
                    error_details += f"\n... 还有 {error_count - 10} 个错误未显示"
                
                QMessageBox.warning(self, "导入结果", result_message + error_details)
            else:
                QMessageBox.information(self, "导入结果", result_message)
                
        except ImportError:
            QMessageBox.warning(self, "错误", "缺少必要的依赖库，请先安装 pandas 和 openpyxl")
        except pd.errors.EmptyDataError:
            QMessageBox.warning(self, "错误", "导入的文件为空")
        except pd.errors.ParserError:
            QMessageBox.warning(self, "错误", "文件格式解析失败，请检查文件格式是否正确")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"批量导入失败: {str(e)}")
    
    def save_channel_config(self):
        """
        保存渠道配置到文件
        """
        # 使用当前界面显示的配置文件路径
        config_path = self.channel_manage_config_edit.text()
        if not config_path:
            QMessageBox.warning(self, "警告", "请先选择渠道配置文件")
            return
        
        # 更新渠道配置管理器的配置路径
        self.channel_config_manager.config_path = config_path
        
        if self.channel_config_manager.save_config():
            QMessageBox.information(self, "提示", f"渠道配置已成功保存到: {config_path}")
        else:
            QMessageBox.warning(self, "警告", "渠道配置保存失败")
    
    def start_jiagu(self):
        """
        开始加固处理
        """
        if not self.apk_list:
            QMessageBox.warning(self, "警告", "请先添加APK文件")
            return
        
        # 检查输出目录
        output_dir = self.output_dir_edit.text()
        if not os.path.exists(output_dir):
            reply = QMessageBox.question(self, "确认", f"输出目录不存在，是否创建？\n{output_dir}", 
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                os.makedirs(output_dir, exist_ok=True)
            else:
                return
        
        # 获取加固选项
        self.options = {
            'dex_encrypt': self.dex_encrypt_check.isChecked(),
            'resource_obfuscate': self.resource_obfuscate_check.isChecked(),
            'anti_debug': self.anti_debug_check.isChecked(),
            'anti_root': self.anti_root_check.isChecked(),
            'anti_emulator': self.anti_emulator_check.isChecked(),
            'output_dir': output_dir,
            'signature': {
                'keystore': self.keystore_edit.text(),
                'keystore_pass': self.keystore_pass_edit.text(),
                'key_alias': self.key_alias_edit.text(),
                'key_pass': self.key_pass_edit.text()
            },
            'channel_packaging': {
                'enabled': self.channel_packaging_check.isChecked(),
                'config_path': self.channel_config_edit.text()
            }
        }
        
        # 开始处理
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 检查多渠道打包选项是否启用
        channel_enabled = self.channel_packaging_check.isChecked()
        channel_config = self.channel_config_edit.text()
        
        # 确保多渠道打包配置完整
        if channel_enabled and not os.path.exists(channel_config):
            QMessageBox.warning(self, "警告", f"渠道配置文件不存在: {channel_config}")
            return
        
        # 添加多渠道打包选项到options
        self.options['channel_packaging'] = {
            'enabled': channel_enabled,
            'config_path': channel_config
        }
        
        # 创建并启动线程
        self.jiagu_thread = JiaguThread(self.apk_list, self.options)
        self.jiagu_thread.progress_updated.connect(self.update_progress)
        self.jiagu_thread.task_completed.connect(self.on_task_completed)
        self.jiagu_thread.all_tasks_completed.connect(self.on_all_tasks_completed)
        self.jiagu_thread.start()
        
        self.log("开始批量加固处理...")
    
    def update_progress(self, value, message):
        """
        更新进度条
        """
        self.progress_bar.setValue(value)
        self.log(message)
    
    def on_task_completed(self, result):
        """
        单个任务完成处理
        """
        if result['success']:
            self.log(f"✓ 成功: {os.path.basename(result['apk_path'])}")
        else:
            self.log(f"✗ 失败: {os.path.basename(result['apk_path'])} - {result['error']}")
    
    def on_all_tasks_completed(self, results):
        """
        所有任务完成处理
        """
        self.progress_bar.setVisible(False)
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        self.log(f"\n加固完成！成功: {success_count}/{total_count}")
        
        # 生成报告
        report_gen = ReportGenerator()
        report_path = report_gen.generate_report(results, self.options.get('output_dir', '.'))
        
        if report_path:
            self.log(f"加固报告已生成: {report_path}")
        
        # 显示结果对话框
        QMessageBox.information(self, "完成", f"加固处理完成！\n成功: {success_count}/{total_count}\n\n报告已保存到: {report_path}")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        拖放进入事件
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """
        拖放事件处理
        """
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.apk'):
                self.add_apk_to_list(file_path)
    
    def load_config(self):
        """
        加载配置并填充到UI
        """
        signature_config = self.config_manager.get_signature_config()
        if signature_config:
            self.keystore_edit.setText(signature_config.get('keystore', ''))
            self.keystore_pass_edit.setText(signature_config.get('keystore_pass', ''))
            self.key_alias_edit.setText(signature_config.get('key_alias', ''))
            self.key_pass_edit.setText(signature_config.get('key_pass', ''))
            self.log("已加载保存的签名配置")
    
    def save_config(self):
        """
        保存配置
        """
        signature_config = {
            'keystore': self.keystore_edit.text(),
            'keystore_pass': self.keystore_pass_edit.text(),
            'key_alias': self.key_alias_edit.text(),
            'key_pass': self.key_pass_edit.text()
        }
        self.config_manager.save_signature_config(signature_config)
        self.log("签名配置已保存")
    
    def clear_config(self):
        """
        清除配置
        """
        reply = QMessageBox.question(self, "确认", "确定要清除所有保存的配置吗？", 
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config_manager.clear_signature_config()
            # 清空UI中的配置
            self.keystore_edit.clear()
            self.keystore_pass_edit.clear()
            self.key_alias_edit.clear()
            self.key_pass_edit.clear()
            self.log("签名配置已清除")
    
    def log(self, message):
        """
        添加日志信息
        """
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        logger.info(message)
    
    def is_config_changed(self):
        """
        检测配置是否发生变化
        """
        current_config = {
            'keystore': self.keystore_edit.text(),
            'keystore_pass': self.keystore_pass_edit.text(),
            'key_alias': self.key_alias_edit.text(),
            'key_pass': self.key_pass_edit.text()
        }
        saved_config = self.config_manager.get_signature_config()
        return current_config != saved_config
    
    def closeEvent(self, event):
        """
        窗口关闭事件
        """
        # 检查是否有正在运行的任务
        if self.jiagu_thread and self.jiagu_thread.isRunning():
            reply = QMessageBox.question(self, "确认", "有任务正在运行，确定要关闭吗？", 
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # 检查配置是否发生变化
        if self.is_config_changed():
            reply = QMessageBox.question(self, "保存配置", "签名配置已发生变化，是否保存？", 
                                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                                        QMessageBox.Yes)
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.Yes:
                self.save_config()
        event.accept()
