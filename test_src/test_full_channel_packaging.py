#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试完整的渠道打包流程
"""

import os
import sys
import tempfile
import shutil
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.channel_packer import ChannelPackageManager

def test_full_channel_packaging():
    """测试完整的渠道打包流程"""
    logger.info("开始测试完整的渠道打包流程...")
    
    # 检查是否提供了测试APK文件
    if len(sys.argv) < 2:
        logger.error("请提供测试APK文件路径")
        sys.exit(1)
    
    test_apk_path = sys.argv[1]
    if not os.path.exists(test_apk_path):
        logger.error(f"测试APK文件不存在: {test_apk_path}")
        sys.exit(1)
    
    # 验证原始APK是有效的ZIP文件
    import zipfile
    if not zipfile.is_zipfile(test_apk_path):
        logger.error(f"无效的ZIP/APK文件: {test_apk_path}")
        sys.exit(1)
    
    logger.info(f"使用测试APK: {test_apk_path}")
    
    # 使用简单的渠道配置文件
    channel_config_path = "/Users/moses/Dev/Dev_trae/Jiagu/config/simple_channel_config.yaml"
    if not os.path.exists(channel_config_path):
        logger.error(f"渠道配置文件不存在: {channel_config_path}")
        sys.exit(1)
    
    logger.info(f"使用渠道配置: {channel_config_path}")
    
    # 创建ChannelPackageManager实例
    channel_manager = ChannelPackageManager()
    
    # 生成渠道包
    logger.info("开始生成渠道包...")
    channel_result = channel_manager.generate_channels(
        test_apk_path,
        channel_config_path,
        None  # 不需要签名信息
    )
    
    if not channel_result['success']:
        logger.error(f"生成渠道包失败: {channel_result['message']}")
        sys.exit(1)
    
    logger.success(f"生成渠道包成功，共 {channel_result['channel_count']} 个")
    
    # 输出生成的渠道包列表
    for apk_path in channel_result['channel_packages']:
        logger.info(f"生成的渠道包: {apk_path}")
        
        # 验证生成的APK是有效的ZIP文件
        if zipfile.is_zipfile(apk_path):
            logger.success(f"✓ {os.path.basename(apk_path)} 是有效的ZIP文件")
        else:
            logger.error(f"✗ {os.path.basename(apk_path)} 不是有效的ZIP文件")
    
    logger.success("=== 完整渠道打包测试完成 ===")

if __name__ == "__main__":
    test_full_channel_packaging()
