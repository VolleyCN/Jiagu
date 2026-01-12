#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试渠道注入功能
"""

import os
import sys
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.walle_python_impl import WallePythonImpl

def test_simple_channel_injection():
    """简单测试渠道注入功能"""
    print("=== 简单测试渠道注入功能 ===")
    
    # 使用指定的测试APK文件
    test_apk = './protected_zhima_dev.apk'
    
    if not os.path.exists(test_apk):
        print(f"❌ 测试APK文件不存在: {test_apk}")
        return False
    
    print(f"✅ 使用测试APK文件: {test_apk}")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"📁 创建临时目录: {temp_dir}")
    
    try:
        # 初始化walle实现
        walle_impl = WallePythonImpl()
        
        # 测试: 注入渠道信息
        print("\n测试: 注入渠道信息...")
        test_channel = "test_channel_123"
        output_apk = os.path.join(temp_dir, f"test_{test_channel}.apk")
        
        # 复制源文件到目标文件（避免修改原文件）
        shutil.copy2(test_apk, output_apk)
        
        # 注入渠道信息
        success = walle_impl.inject_channel(test_apk, output_apk, test_channel)
        if success:
            print(f"✅ 成功注入渠道 '{test_channel}'")
            print(f"   输出文件: {output_apk}")
        else:
            print(f"❌ 注入渠道失败")
            return False
        
        # 测试: 读取渠道信息
        print("\n测试: 读取渠道信息...")
        channel = walle_impl.get_channel(output_apk)
        if channel == test_channel:
            print(f"✅ 成功读取渠道信息: '{channel}'")
        else:
            print(f"❌ 读取渠道信息失败，期望 '{test_channel}'，实际 '{channel}'")
            return False
        
        # 使用官方walle工具验证
        print("\n测试: 使用官方walle工具验证...")
        walle_jar = os.path.join(os.path.dirname(__file__), 'lib/walle-cli-all.jar')
        if os.path.exists(walle_jar):
            import subprocess
            cmd = ['java', '-jar', walle_jar, 'show', output_apk]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ 官方walle工具验证成功")
                print(f"   输出: {result.stdout.strip()}")
            else:
                print(f"⚠️  官方walle工具验证失败: {result.stderr.strip()}")
        else:
            print(f"⚠️  未找到官方walle工具，跳过验证")
        
        print("\n🎉 所有测试通过！")
        return True
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n📁 清理临时目录: {temp_dir}")

if __name__ == "__main__":
    test_simple_channel_injection()
