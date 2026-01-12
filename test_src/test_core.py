#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心功能测试脚本
用于验证APK加固工具的核心功能
"""

import os
import sys
from loguru import logger

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.apk_parser import APKParser, BatchAPKParser
from src.core.dex_encryptor import DexEncryptor
from src.core.report_generator import ReportGenerator

def test_apk_parser():
    """
    测试APK解析功能
    """
    print("\n=== 测试APK解析功能 ===")
    
    # 这个测试需要一个实际的APK文件，这里我们只测试类的初始化
    parser = APKParser("dummy.apk")
    print("✓ APKParser类初始化成功")
    
    batch_parser = BatchAPKParser(["dummy1.apk", "dummy2.apk"])
    print("✓ BatchAPKParser类初始化成功")
    
    return True

def test_dex_encryptor():
    """
    测试DEX加密功能
    """
    print("\n=== 测试DEX加密功能 ===")
    
    encryptor = DexEncryptor()
    print("✓ DexEncryptor类初始化成功")
    
    # 生成测试数据
    test_data = b"This is a test DEX file content"
    
    # 测试密钥生成
    encryptor.generate_key()
    print("✓ 密钥生成成功")
    
    # 测试加密解密
    encrypted = encryptor.encrypt_dex(test_data)
    print(f"✓ DEX加密成功，原始大小: {len(test_data)} bytes, 加密后大小: {len(encrypted)} bytes")
    
    decrypted = encryptor.decrypt_dex(encrypted)
    if decrypted == test_data:
        print("✓ DEX解密成功，数据一致")
    else:
        print("✗ DEX解密失败，数据不一致")
        return False
    
    return True

def test_report_generator():
    """
    测试报告生成功能
    """
    print("\n=== 测试报告生成功能 ===")
    
    generator = ReportGenerator()
    print("✓ ReportGenerator类初始化成功")
    
    # 生成测试结果
    test_results = [
        {
            'success': True,
            'apk_path': '/test/app1.apk',
            'output_dir': '/test/output',
            'message': '加固成功'
        },
        {
            'success': False,
            'apk_path': '/test/app2.apk',
            'error': '加固失败: 未知错误'
        }
    ]
    
    # 测试报告ID生成
    report_id = generator.generate_report_id()
    print(f"✓ 报告ID生成成功: {report_id}")
    
    # 测试报告生成
    output_dir = "./test_reports"
    os.makedirs(output_dir, exist_ok=True)
    
    report_path = generator.generate_report(test_results, output_dir)
    if report_path:
        print(f"✓ 报告生成成功: {report_path}")
    else:
        print("✗ 报告生成失败")
        return False
    
    return True

def main():
    """
    主测试函数
    """
    print("=== APK加固工具核心功能测试 ===")
    
    tests = [
        test_apk_parser,
        test_dex_encryptor,
        test_report_generator
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} 抛出异常: {e}")
            failed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}, 失败: {failed}, 总计: {len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有核心功能测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查代码")
        return 1

if __name__ == "__main__":
    sys.exit(main())
