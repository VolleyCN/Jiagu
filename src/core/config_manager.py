#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责配置信息的加密存储和加载
"""

import os
import json
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from loguru import logger

class ConfigManager:
    """
    配置管理器
    负责配置的加密存储和加载
    """
    
    def __init__(self, config_file=None):
        """
        初始化配置管理器
        :param config_file: 配置文件路径
        """
        self.config_dir = os.path.join(os.path.expanduser("~"), ".jiagu")
        self.config_file = config_file or os.path.join(self.config_dir, "config.json")
        self.master_key = self._get_or_create_master_key()
        self.iv = None
    
    def _get_or_create_master_key(self):
        """
        获取或创建主密钥
        :return: 主密钥
        """
        key_file = os.path.join(self.config_dir, ".key")
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 如果密钥文件存在，读取密钥
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        
        # 否则生成新密钥
        key = get_random_bytes(32)  # AES-256 密钥
        with open(key_file, 'wb') as f:
            f.write(key)
        
        # 设置密钥文件权限为只读
        os.chmod(key_file, 0o600)
        
        logger.info(f"生成新的主密钥，存储路径: {key_file}")
        return key
    
    def _encrypt(self, data):
        """
        加密数据
        :param data: 待加密数据
        :return: 加密后的数据
        """
        try:
            # 生成随机IV
            iv = get_random_bytes(AES.block_size)
            
            # 创建AES加密器
            cipher = AES.new(self.master_key, AES.MODE_CBC, iv)
            
            # 填充数据
            pad_length = AES.block_size - (len(data) % AES.block_size)
            padded_data = data + bytes([pad_length] * pad_length)
            
            # 加密
            encrypted = cipher.encrypt(padded_data)
            
            # 合并IV和加密数据，然后base64编码
            return base64.b64encode(iv + encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise
    
    def _decrypt(self, encrypted_data):
        """
        解密数据
        :param encrypted_data: 加密后的数据
        :return: 解密后的数据
        """
        try:
            # base64解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # 分离IV和加密数据
            iv = encrypted_bytes[:AES.block_size]
            encrypted = encrypted_bytes[AES.block_size:]
            
            # 创建AES解密器
            cipher = AES.new(self.master_key, AES.MODE_CBC, iv)
            
            # 解密
            decrypted_padded = cipher.decrypt(encrypted)
            
            # 去除填充
            pad_length = decrypted_padded[-1]
            decrypted = decrypted_padded[:-pad_length]
            
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise
    
    def _encrypt_config(self, config):
        """
        加密配置中的敏感信息
        :param config: 原始配置
        :return: 加密后的配置
        """
        encrypted_config = config.copy()
        
        # 加密签名配置中的密码
        if 'signature' in encrypted_config:
            signature = encrypted_config['signature']
            if 'keystore_pass' in signature:
                signature['keystore_pass'] = self._encrypt(signature['keystore_pass'].encode('utf-8'))
            if 'key_pass' in signature:
                signature['key_pass'] = self._encrypt(signature['key_pass'].encode('utf-8'))
        
        return encrypted_config
    
    def _decrypt_config(self, encrypted_config):
        """
        解密配置中的敏感信息
        :param encrypted_config: 加密后的配置
        :return: 解密后的配置
        """
        decrypted_config = encrypted_config.copy()
        
        # 解密签名配置中的密码
        if 'signature' in decrypted_config:
            signature = decrypted_config['signature']
            if 'keystore_pass' in signature:
                signature['keystore_pass'] = self._decrypt(signature['keystore_pass'])
            if 'key_pass' in signature:
                signature['key_pass'] = self._decrypt(signature['key_pass'])
        
        return decrypted_config
    
    def load_config(self):
        """
        加载配置
        :return: 配置字典
        """
        try:
            if not os.path.exists(self.config_file):
                logger.info(f"配置文件不存在: {self.config_file}")
                return {}
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                encrypted_config = json.load(f)
            
            logger.info(f"加载配置文件: {self.config_file}")
            return self._decrypt_config(encrypted_config)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return {}
    
    def save_config(self, config):
        """
        保存配置
        :param config: 配置字典
        """
        try:
            # 加密配置
            encrypted_config = self._encrypt_config(config)
            
            # 保存配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_config, f, ensure_ascii=False, indent=2)
            
            # 设置配置文件权限为只读
            os.chmod(self.config_file, 0o600)
            
            logger.info(f"配置保存成功: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def clear_config(self):
        """
        清除所有配置
        """
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                logger.info(f"配置文件已清除: {self.config_file}")
            else:
                logger.info("配置文件不存在，无需清除")
        except Exception as e:
            logger.error(f"清除配置失败: {e}")
            raise
    
    def get_signature_config(self):
        """
        获取签名配置
        :return: 签名配置字典
        """
        config = self.load_config()
        return config.get('signature', {})
    
    def save_signature_config(self, signature_config):
        """
        保存签名配置
        :param signature_config: 签名配置字典
        """
        config = self.load_config()
        config['signature'] = signature_config
        self.save_config(config)
    
    def clear_signature_config(self):
        """
        清除签名配置
        """
        config = self.load_config()
        if 'signature' in config:
            del config['signature']
            self.save_config(config)
            logger.info("签名配置已清除")
        else:
            logger.info("签名配置不存在，无需清除")
