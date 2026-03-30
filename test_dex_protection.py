#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试DEX文件加固功能
"""

import os
import sys
import tempfile
import shutil

# 设置Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.core.dex_encryptor import DexProtection

# 创建临时测试文件
temp_dir = tempfile.mkdtemp()
try:
    # 使用用户提供的APK文件
    test_apk = os.path.join('/Users/moses/Desktop', 'customer-release.apk')
    if not os.path.exists(test_apk):
        print(f"测试APK不存在: {test_apk}")
        sys.exit(1)
    
    output_apk = os.path.join(temp_dir, "protected_customer-release.apk")
    
    print(f"测试APK: {test_apk}")
    print(f"输出APK: {output_apk}")
    
    # 初始化DEX保护管理器
    dex_protection = DexProtection()
    
    # 执行DEX加固
    print("\n开始执行DEX加固...")
    result = dex_protection.protect_apk(test_apk, output_apk)
    
    print(f"\n加固结果: {result}")
    
    if result['success']:
        print("DEX加固成功！")
        
        # 验证加固结果
        print("\n开始验证加固结果...")
        verify_result = dex_protection.verify_protection(output_apk)
        print(f"验证结果: {verify_result}")
        
        if verify_result['success']:
            print("加固结果验证成功！")
        else:
            print(f"加固结果验证失败: {verify_result['message']}")
    else:
        print(f"DEX加固失败: {result['message']}")
    
finally:
    # 清理临时文件
    shutil.rmtree(temp_dir)
    print("\n测试完成，临时文件已清理")
