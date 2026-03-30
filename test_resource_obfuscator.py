#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试资源混淆功能
"""

import os
import sys
import tempfile
import shutil

# 设置Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.core.resource_obfuscator import ResourceProtection

# 创建临时测试文件
temp_dir = tempfile.mkdtemp()
try:
    # 复制一个APK文件到临时目录（使用用户提供的APK）
    test_apk = os.path.join('/Users/moses/Desktop', 'customer-release.apk')
    if not os.path.exists(test_apk):
        print(f"测试APK不存在: {test_apk}")
        sys.exit(1)
    
    output_apk = os.path.join(temp_dir, "test_output.apk")
    
    print(f"测试APK: {test_apk}")
    print(f"输出APK: {output_apk}")
    
    # 初始化资源保护管理器
    rp = ResourceProtection()
    
    # 执行资源混淆
    print("\n开始执行资源混淆...")
    result = rp.protect_apk_resources(test_apk, output_apk)
    
    print(f"\n混淆结果: {result}")
    
    if result['success']:
        print("资源混淆成功！")
    else:
        print(f"资源混淆失败: {result['message']}")
        if 'error' in result:
            print(f"错误详情: {result['error']}")
    
finally:
    # 清理临时文件
    shutil.rmtree(temp_dir)
    print("\n测试完成，临时文件已清理")
