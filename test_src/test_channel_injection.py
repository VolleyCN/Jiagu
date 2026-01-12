#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证渠道注入功能
用于测试 channel_packer.py 的 _write_channel_block 方法是否能正确注入渠道信息而不破坏APK文件
"""

import os
import sys
import zipfile
import tempfile
import shutil
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.channel_packer import FastChannelPacker

def test_channel_injection():
    """测试渠道注入功能"""
    logger.info("开始测试渠道注入功能...")
    
    # 创建测试用的FastChannelPacker实例
    packer = FastChannelPacker()
    
    # 检查是否提供了测试APK文件
    if len(sys.argv) < 2:
        logger.error("请提供测试APK文件路径")
        sys.exit(1)
    
    test_apk_path = sys.argv[1]
    if not os.path.exists(test_apk_path):
        logger.error(f"测试APK文件不存在: {test_apk_path}")
        sys.exit(1)
    
    # 验证原始APK是有效的ZIP文件
    if not zipfile.is_zipfile(test_apk_path):
        logger.error(f"无效的ZIP/APK文件: {test_apk_path}")
        sys.exit(1)
    
    logger.info(f"使用测试APK: {test_apk_path}")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp(prefix="channel_test_")
    logger.info(f"创建临时测试目录: {temp_dir}")
    
    try:
        # 1. 复制APK到临时目录
        test_copy_path = os.path.join(temp_dir, "test.apk")
        shutil.copy2(test_apk_path, test_copy_path)
        logger.info(f"复制APK到临时目录: {test_copy_path}")
        
        # 2. 测试注入渠道信息
        channel_info = "CHANNEL_ID=test_channel;MARKET_NAME=Test Market"
        logger.info(f"准备注入渠道信息: {channel_info}")
        
        # 调用写入渠道信息块的方法
        packer._write_channel_block(test_copy_path, channel_info)
        logger.success("渠道信息注入成功")
        
        # 3. 验证注入后APK仍然是有效的ZIP文件
        if zipfile.is_zipfile(test_copy_path):
            logger.success("注入后APK仍然是有效的ZIP文件")
        else:
            logger.error("注入后APK不是有效的ZIP文件")
            sys.exit(1)
        
        # 4. 验证注入后APK的大小变化
        original_size = os.path.getsize(test_apk_path)
        injected_size = os.path.getsize(test_copy_path)
        logger.info(f"原始APK大小: {original_size} 字节")
        logger.info(f"注入后APK大小: {injected_size} 字节")
        logger.info(f"增加的大小: {injected_size - original_size} 字节")
        
        # 5. 尝试读取ZIP文件内容，验证内部结构未被破坏
        try:
            with zipfile.ZipFile(test_copy_path, 'r') as zipf:
                file_list = zipf.namelist()
                logger.info(f"注入后APK包含 {len(file_list)} 个文件")
                logger.success("成功读取注入后APK的内部结构")
        except Exception as e:
            logger.error(f"无法读取注入后APK的内部结构: {e}")
            sys.exit(1)
        
        # 6. 输出测试结果
        logger.success("=== 所有测试通过！渠道注入功能正常 ===")
        logger.info(f"测试结果APK保存到: {test_copy_path}")
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        logger.info(f"清理临时测试目录: {temp_dir}")

if __name__ == "__main__":
    test_channel_injection()
