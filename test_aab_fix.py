#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本，用于测试修复后的 dex_encryptor 是否能正确处理 AAB 文件
"""

import os
import tempfile
import shutil
from src.core.dex_encryptor import DexProtection
from loguru import logger

# 配置日志
logger.add("test_aab_fix.log", rotation="500 MB")

def test_aab_protection():
    """
    测试 AAB 文件的保护过程
    """
    try:
        # 原始 AAB 路径
        original_aab = "customer-release.aab"
        
        # 检查原始 AAB 是否存在
        if not os.path.exists(original_aab):
            logger.error(f"原始 AAB 文件不存在: {original_aab}")
            return False
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="jiagu_test_")
        
        # 复制原始 AAB 到临时目录
        test_aab = os.path.join(temp_dir, "test.aab")
        shutil.copy2(original_aab, test_aab)
        logger.info(f"已复制原始 AAB 到测试路径: {test_aab}")
        
        # 创建 DexProtection 实例
        dex_protection = DexProtection()
        
        # 调用 protect_apk 方法
        logger.info("开始保护 AAB")
        output_aab = os.path.join(temp_dir, "protected_test.aab")
        result = dex_protection.protect_apk(test_aab, output_aab)
        
        # 检查保护结果
        if result['success']:
            logger.info("AAB 保护成功！")
        else:
            logger.error(f"AAB 保护失败: {result.get('error', '未知错误')}")
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
        
        logger.info("测试脚本执行完成")
        return result['success']
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("开始测试修复后的 dex_encryptor 对 AAB 文件的支持")
    success = test_aab_protection()
    if success:
        logger.info("测试成功！修复有效")
    else:
        logger.error("测试失败，修复无效")
