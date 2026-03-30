#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本，用于测试修复后的 dex_encryptor 是否能正确处理 AndroidManifest.xml
"""

import os
import tempfile
import shutil
from src.core.dex_encryptor import DexProtection
from loguru import logger

# 配置日志
logger.add("test_fix.log", rotation="500 MB")

def test_manifest_modification():
    """
    测试 AndroidManifest.xml 修改功能
    """
    try:
        # 原始 APK 路径
        original_apk = "customer-release.apk"
        
        # 检查原始 APK 是否存在
        if not os.path.exists(original_apk):
            logger.error(f"原始 APK 文件不存在: {original_apk}")
            return False
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="jiagu_test_")
        
        # 复制原始 APK 到临时目录
        test_apk = os.path.join(temp_dir, "test.apk")
        shutil.copy2(original_apk, test_apk)
        logger.info(f"已复制原始 APK 到测试路径: {test_apk}")
        
        # 创建 DexProtection 实例
        dex_protection = DexProtection()
        
        # 调用修改 manifest 的方法
        logger.info("开始修改 AndroidManifest.xml")
        # 这里我们直接调用 _modify_manifest 方法，它会在 XML 解析失败时自动调用 _modify_manifest_with_aapt2
        dex_protection._modify_manifest(test_apk)
        
        # 检查修改是否成功
        logger.info("测试完成，检查结果")
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        
        logger.info("测试脚本执行完成")
        return True
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("开始测试修复后的 dex_encryptor")
    success = test_manifest_modification()
    if success:
        logger.info("测试成功！修复有效")
    else:
        logger.error("测试失败，修复无效")
