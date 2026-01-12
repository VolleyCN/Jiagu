#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证生成的渠道包是否为有效的ZIP文件
"""

import os
import sys
import zipfile

def validate_apk_files(apk_directory):
    """验证目录中所有APK文件是否为有效的ZIP文件"""
    print(f"正在验证目录中的APK文件: {apk_directory}")
    
    # 获取目录中所有APK文件
    apk_files = [f for f in os.listdir(apk_directory) 
                if f.endswith('.apk') and os.path.isfile(os.path.join(apk_directory, f))]
    
    if not apk_files:
        print("目录中没有找到APK文件")
        return
    
    print(f"找到 {len(apk_files)} 个APK文件，开始验证...\n")
    
    valid_count = 0
    invalid_count = 0
    
    for apk_file in apk_files:
        apk_path = os.path.join(apk_directory, apk_file)
        print(f"验证: {apk_file}")
        
        try:
            if zipfile.is_zipfile(apk_path):
                print(f"  ✓ 有效的ZIP文件")
                valid_count += 1
            else:
                print(f"  ✗ 无效的ZIP文件")
                invalid_count += 1
        except Exception as e:
            print(f"  ✗ 验证失败: {e}")
            invalid_count += 1
        
        print()
    
    print(f"验证完成！")
    print(f"有效APK: {valid_count}")
    print(f"无效APK: {invalid_count}")
    print(f"总APK数: {len(apk_files)}")

if __name__ == "__main__":
    # 默认使用channels目录
    apk_dir = "/Users/moses/Dev/Dev_trae/Jiagu/channels"
    if len(sys.argv) > 1:
        apk_dir = sys.argv[1]
    
    validate_apk_files(apk_dir)
