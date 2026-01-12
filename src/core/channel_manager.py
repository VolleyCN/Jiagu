#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渠道配置管理模块
负责读取和解析渠道配置文件，提供渠道配置访问接口
"""

import os
import yaml
from loguru import logger

class ChannelConfigManager:
    """渠道配置管理器"""
    
    def __init__(self):
        """初始化渠道配置管理器"""
        self.config = {}
        self.channels = []
        self.config_path = None
    
    def load_config(self, config_path):
        """
        加载渠道配置文件
        :param config_path: 渠道配置文件路径
        :return: 是否加载成功
        """
        try:
            logger.info(f"开始加载渠道配置文件: {config_path}")
            
            # 检查文件是否存在
            if not os.path.exists(config_path):
                logger.error(f"渠道配置文件不存在: {config_path}")
                return False
            
            # 读取并解析YAML文件
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # 验证配置格式
            if not self._validate_config():
                logger.error("渠道配置文件格式无效")
                return False
            
            # 提取渠道列表
            self.channels = self.config.get('channels', [])
            self.config_path = config_path
            
            logger.info(f"成功加载渠道配置，共 {len(self.channels)} 个渠道")
            logger.debug(f"渠道配置: {self.config}")
            return True
        except yaml.YAMLError as e:
            logger.error(f"解析渠道配置文件失败: {e}")
            return False
        except Exception as e:
            logger.error(f"加载渠道配置文件失败: {e}")
            return False
    
    def _validate_config(self):
        """
        验证渠道配置格式
        :return: 配置是否有效
        """
        try:
            # 验证基本结构
            if not isinstance(self.config, dict):
                return False
            
            # 验证版本号
            if 'version' not in self.config:
                logger.warning("渠道配置文件缺少version字段，使用默认版本1.0")
                self.config['version'] = 1.0
            
            # 验证输出配置
            if 'output' not in self.config:
                logger.warning("渠道配置文件缺少output字段，使用默认配置")
                self.config['output'] = {
                    'overwrite': True,
                    'directory': './channels'
                }
            
            # 验证渠道列表
            if 'channels' not in self.config:
                logger.error("渠道配置文件缺少channels字段")
                return False
            
            if not isinstance(self.config['channels'], list):
                logger.error("channels字段必须是列表类型")
                return False
            
            # 验证每个渠道的格式
            for i, channel in enumerate(self.config['channels']):
                if not isinstance(channel, dict):
                    logger.error(f"第 {i+1} 个渠道配置必须是字典类型")
                    return False
                
                if 'name' not in channel:
                    logger.error(f"第 {i+1} 个渠道缺少name字段")
                    return False
                
                if 'metadata' not in channel:
                    logger.warning(f"第 {i+1} 个渠道缺少metadata字段，使用空字典")
                    channel['metadata'] = {}
                
                if not isinstance(channel['metadata'], dict):
                    logger.error(f"第 {i+1} 个渠道的metadata字段必须是字典类型")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"验证渠道配置失败: {e}")
            return False
    
    def get_output_config(self):
        """
        获取输出配置
        :return: 输出配置字典
        """
        return self.config.get('output', {
            'overwrite': True,
            'directory': './channels'
        })
    
    def get_channels(self):
        """
        获取渠道列表
        :return: 渠道列表
        """
        return self.channels
    
    def get_channel_by_name(self, channel_name):
        """
        根据渠道名称获取渠道配置
        :param channel_name: 渠道名称
        :return: 渠道配置字典，不存在则返回None
        """
        for channel in self.channels:
            if channel['name'] == channel_name:
                return channel
        return None
    
    def save_config(self, config_path=None):
        """
        保存渠道配置到文件
        :param config_path: 保存路径，默认使用加载时的路径
        :return: 是否保存成功
        """
        try:
            save_path = config_path or self.config_path
            if not save_path:
                logger.error("未指定保存路径")
                return False
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"成功保存渠道配置到: {save_path}")
            return True
        except Exception as e:
            logger.error(f"保存渠道配置失败: {e}")
            return False
    
    def add_channel(self, channel_config):
        """
        添加新渠道
        :param channel_config: 渠道配置字典
        :return: 是否添加成功
        """
        try:
            # 验证渠道配置格式
            if not isinstance(channel_config, dict):
                logger.error("渠道配置必须是字典类型")
                return False
            
            if 'name' not in channel_config:
                logger.error("渠道配置缺少name字段")
                return False
            
            if 'metadata' not in channel_config:
                channel_config['metadata'] = {}
            
            # 检查渠道是否已存在
            existing_channel = self.get_channel_by_name(channel_config['name'])
            if existing_channel:
                logger.warning(f"渠道 {channel_config['name']} 已存在，将覆盖现有配置")
                # 移除现有渠道
                self.channels = [c for c in self.channels if c['name'] != channel_config['name']]
            
            # 添加新渠道
            self.channels.append(channel_config)
            self.config['channels'] = self.channels
            
            logger.info(f"成功添加渠道: {channel_config['name']}")
            return True
        except Exception as e:
            logger.error(f"添加渠道失败: {e}")
            return False
    
    def remove_channel(self, channel_name):
        """
        移除指定渠道
        :param channel_name: 渠道名称
        :return: 是否移除成功
        """
        try:
            # 检查渠道是否存在
            existing_channel = self.get_channel_by_name(channel_name)
            if not existing_channel:
                logger.error(f"渠道 {channel_name} 不存在")
                return False
            
            # 移除渠道
            self.channels = [c for c in self.channels if c['name'] != channel_name]
            self.config['channels'] = self.channels
            
            logger.info(f"成功移除渠道: {channel_name}")
            return True
        except Exception as e:
            logger.error(f"移除渠道失败: {e}")
            return False

class ChannelConfigValidator:
    """渠道配置验证器"""
    
    @staticmethod
    def validate_config_file(config_path):
        """
        验证渠道配置文件的格式和完整性
        :param config_path: 渠道配置文件路径
        :return: 验证结果字典
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'channel_count': 0
        }
        
        try:
            # 检查文件是否存在
            if not os.path.exists(config_path):
                result['errors'].append(f"文件不存在: {config_path}")
                return result
            
            # 读取并解析YAML文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 验证基本结构
            if not isinstance(config, dict):
                result['errors'].append("配置文件必须是字典类型")
                return result
            
            # 验证版本号
            if 'version' not in config:
                result['warnings'].append("缺少version字段，将使用默认版本1.0")
            
            # 验证输出配置
            if 'output' not in config:
                result['warnings'].append("缺少output字段，将使用默认配置")
            
            # 验证渠道列表
            if 'channels' not in config:
                result['errors'].append("缺少channels字段")
                return result
            
            if not isinstance(config['channels'], list):
                result['errors'].append("channels字段必须是列表类型")
                return result
            
            # 验证每个渠道的格式
            for i, channel in enumerate(config['channels']):
                if not isinstance(channel, dict):
                    result['errors'].append(f"第 {i+1} 个渠道必须是字典类型")
                    continue
                
                if 'name' not in channel:
                    result['errors'].append(f"第 {i+1} 个渠道缺少name字段")
                    continue
                
                if 'metadata' not in channel:
                    result['warnings'].append(f"第 {i+1} 个渠道缺少metadata字段")
                elif not isinstance(channel['metadata'], dict):
                    result['errors'].append(f"第 {i+1} 个渠道的metadata字段必须是字典类型")
            
            result['channel_count'] = len(config['channels'])
            result['valid'] = len(result['errors']) == 0
            return result
        except yaml.YAMLError as e:
            result['errors'].append(f"YAML解析错误: {e}")
            return result
        except Exception as e:
            result['errors'].append(f"验证失败: {e}")
            return result