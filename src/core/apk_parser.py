#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK文件解析模块
负责APK文件的导入、解析和信息提取
"""

import os
import tempfile
import zipfile
import subprocess
from loguru import logger

class APKParser:
    """APK文件解析器"""
    
    def __init__(self, apk_path):
        """
        初始化APK解析器
        :param apk_path: APK文件路径
        """
        self.apk_path = apk_path
        self.temp_dir = None
        self.dex_files = []
        self.resource_files = []
        self.package_name = None
        self.version_name = None
        self.version_code = None
        self.min_sdk_version = None
        self.target_sdk_version = None
        
    def parse(self):
        """
        解析APK文件
        :return: 解析结果（True/False）
        """
        try:
            logger.info(f"开始解析APK文件: {self.apk_path}")
            
            # 验证文件存在性
            if not os.path.exists(self.apk_path):
                logger.error(f"APK文件不存在: {self.apk_path}")
                return False
            
            # 检查是否为有效的ZIP文件
            if not zipfile.is_zipfile(self.apk_path):
                logger.error(f"不是有效的ZIP/APK文件: {self.apk_path}")
                return False
            
            # 解析APK基本信息
            self._parse_apk_info()
            
            # 提取DEX文件
            self._extract_dex_files()
            
            # 提取资源文件列表
            self._extract_resource_files()
            
            logger.info(f"APK解析成功，包名: {self.package_name}, 版本: {self.version_name}")
            return True
        except Exception as e:
            logger.error(f"APK解析失败: {e}")
            return False
    
    def _find_aapt2(self):
        """
        查找aapt2工具路径
        :return: aapt2路径或None
        """
        try:
            # 检查ANDROID_SDK_ROOT
            sdk_root = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
            if sdk_root:
                aapt2_path = os.path.join(sdk_root, "build-tools", "latest", "aapt2")
                if os.path.exists(aapt2_path):
                    return aapt2_path
                
                # 尝试查找最新版本的build-tools
                build_tools_dir = os.path.join(sdk_root, "build-tools")
                if os.path.exists(build_tools_dir):
                    versions = [v for v in os.listdir(build_tools_dir) if os.path.isdir(os.path.join(build_tools_dir, v))]
                    versions.sort(reverse=True)
                    for version in versions:
                        aapt2_path = os.path.join(build_tools_dir, version, "aapt2")
                        if os.path.exists(aapt2_path):
                            return aapt2_path
            
            logger.warning("未找到aapt2工具，将使用简单解析")
            return None
        except Exception as e:
            logger.warning(f"查找aapt2失败: {e}")
            return None
    
    def _parse_apk_info(self):
        """
        解析APK基本信息
        """
        # 尝试使用aapt2解析
        aapt2_path = self._find_aapt2()
        if aapt2_path:
            try:
                cmd = [aapt2_path, "dump", "badging", self.apk_path]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                output = result.stdout
                
                # 提取包名
                for line in output.split('\n'):
                    if line.startswith('package:'):
                        parts = line.split()
                        for part in parts:
                            if part.startswith('name='):
                                self.package_name = part.split('=')[1].strip("'")
                            elif part.startswith('versionName='):
                                self.version_name = part.split('=')[1].strip("'")
                            elif part.startswith('versionCode='):
                                self.version_code = part.split('=')[1].strip("'")
                
                # 提取SDK版本
                for line in output.split('\n'):
                    if line.startswith('sdkVersion:'):
                        parts = line.split()
                        for part in parts:
                            if part.startswith('minSdkVersion='):
                                self.min_sdk_version = int(part.split('=')[1].strip("'"))
                            elif part.startswith('targetSdkVersion='):
                                self.target_sdk_version = int(part.split('=')[1].strip("'"))
                
                return
            except Exception as e:
                logger.warning(f"使用aapt2解析失败，将使用zipfile解析: {e}")
        
        # 回退使用zipfile解析AndroidManifest.xml
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as zf:
                if 'AndroidManifest.xml' in zf.namelist():
                    # 这里简单处理，只提取文件名等基本信息
                    logger.info("使用zipfile解析APK信息")
                    # 可以使用xml.etree.ElementTree解析XML，但需要处理二进制XML格式
                    # 这里暂时设置默认值
                    self.package_name = os.path.basename(self.apk_path).replace('.apk', '')
                    self.version_name = "1.0"
                    self.version_code = "1"
        except Exception as e:
            logger.error(f"解析APK信息失败: {e}")
            # 设置默认值
            self.package_name = os.path.basename(self.apk_path).replace('.apk', '')
            self.version_name = "1.0"
            self.version_code = "1"
    
    def _extract_dex_files(self):
        """
        提取APK中的DEX文件
        """
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as zf:
                # 获取所有DEX文件
                for file_name in zf.namelist():
                    if file_name.endswith('.dex'):
                        with zf.open(file_name) as dex_file:
                            dex_data = dex_file.read()
                            self.dex_files.append({
                                'name': file_name,
                                'data': dex_data,
                                'size': len(dex_data)
                            })
            logger.info(f"提取到 {len(self.dex_files)} 个DEX文件")
        except Exception as e:
            logger.error(f"提取DEX文件失败: {e}")
    
    def _extract_resource_files(self):
        """
        提取APK中的资源文件列表
        """
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as zf:
                # 获取所有资源文件路径
                self.resource_files = [f for f in zf.namelist() if f.startswith('res/') or f == 'AndroidManifest.xml']
            logger.info(f"提取到 {len(self.resource_files)} 个资源文件")
        except Exception as e:
            logger.error(f"提取资源文件列表失败: {e}")
    
    def get_package_name(self):
        """
        获取APK包名
        :return: 包名字符串
        """
        return self.package_name
    
    def get_version_name(self):
        """
        获取APK版本名
        :return: 版本名字符串
        """
        return self.version_name
    
    def get_version_code(self):
        """
        获取APK版本号
        :return: 版本号字符串
        """
        return self.version_code
    
    def get_min_sdk_version(self):
        """
        获取APK最小SDK版本
        :return: 最小SDK版本号
        """
        return self.min_sdk_version
    
    def get_target_sdk_version(self):
        """
        获取APK目标SDK版本
        :return: 目标SDK版本号
        """
        return self.target_sdk_version
    
    def get_dex_files(self):
        """
        获取解析出的DEX文件
        :return: DEX文件列表
        """
        return self.dex_files
    
    def get_resource_files(self):
        """
        获取资源文件列表
        :return: 资源文件列表
        """
        return self.resource_files
    
    def get_apk_info(self):
        """
        获取APK完整信息
        :return: 包含APK信息的字典
        """
        return {
            'package_name': self.get_package_name(),
            'version_name': self.get_version_name(),
            'version_code': self.get_version_code(),
            'min_sdk': self.get_min_sdk_version(),
            'target_sdk': self.get_target_sdk_version(),
            'dex_count': len(self.dex_files),
            'resource_count': len(self.resource_files),
            'file_size': os.path.getsize(self.apk_path)
        }
    
    def close(self):
        """
        清理资源
        """
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"清理临时目录: {self.temp_dir}")

class BatchAPKParser:
    """批量APK解析器"""
    
    def __init__(self, apk_paths):
        """
        初始化批量解析器
        :param apk_paths: APK文件路径列表
        """
        self.apk_paths = apk_paths
        self.results = []
    
    def parse_all(self):
        """
        批量解析所有APK文件
        :return: 解析结果列表
        """
        logger.info(f"开始批量解析 {len(self.apk_paths)} 个APK文件")
        
        for apk_path in self.apk_paths:
            parser = APKParser(apk_path)
            success = parser.parse()
            
            result = {
                'path': apk_path,
                'success': success,
                'info': parser.get_apk_info() if success else None
            }
            
            self.results.append(result)
            parser.close()
        
        logger.info(f"批量解析完成，成功: {sum(1 for r in self.results if r['success'])}, 失败: {sum(1 for r in self.results if not r['success'])}")
        return self.results
    
    def get_successful_results(self):
        """
        获取成功解析的结果
        :return: 成功解析的结果列表
        """
        return [r for r in self.results if r['success']]
    
    def get_failed_results(self):
        """
        获取解析失败的结果
        :return: 解析失败的结果列表
        """
        return [r for r in self.results if not r['success']]
