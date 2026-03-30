#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查签名配置的状态
"""

from src.core.config_manager import ConfigManager
from loguru import logger

# 配置日志
logger.add("check_signature_config.log", rotation="500 MB")

def check_signature_config():
    """
    检查签名配置的状态
    """
    try:
        # 创建ConfigManager实例
        config_manager = ConfigManager()
        
        # 加载配置
        config = config_manager.load_config()
        logger.info(f"加载的配置: {config}")
        
        # 获取签名配置
        signature_config = config_manager.get_signature_config()
        logger.info(f"签名配置: {signature_config}")
        
        # 检查签名配置是否完整
        required_keys = ['keystore_path', 'keystore_pass', 'key_alias', 'key_pass']
        missing_keys = [key for key in required_keys if key not in signature_config]
        
        if missing_keys:
            logger.warning(f"缺少的签名配置键: {missing_keys}")
        else:
            logger.info("签名配置完整")
        
        # 检查keystore文件是否存在
        if 'keystore_path' in signature_config:
            import os
            keystore_path = signature_config['keystore_path']
            if os.path.exists(keystore_path):
                logger.info(f"Keystore文件存在: {keystore_path}")
            else:
                logger.warning(f"Keystore文件不存在: {keystore_path}")
        
        return True
    except Exception as e:
        logger.error(f"检查签名配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("开始检查签名配置")
    check_signature_config()
