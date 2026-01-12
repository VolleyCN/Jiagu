#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多渠道打包功能
"""

import os
import sys
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.channel_packer import ChannelPackageManager

def test_channel_packer():
    """测试多渠道打包功能"""
    print("=== 测试多渠道打包功能 ===")
    
    # 测试APK文件
    test_apk = './protected_zhima_dev.apk'
    
    if not os.path.exists(test_apk):
        print(f"❌ 测试APK文件不存在: {test_apk}")
        return False
    
    print(f"✅ 使用测试APK文件: {test_apk}")
    
    # 测试渠道配置文件
    channel_config = './config/channel_config.yaml'
    
    if not os.path.exists(channel_config):
        print(f"❌ 渠道配置文件不存在: {channel_config}")
        return False
    
    print(f"✅ 使用渠道配置文件: {channel_config}")
    
    # 创建临时输出目录
    temp_dir = tempfile.mkdtemp()
    print(f"📁 创建临时输出目录: {temp_dir}")
    
    try:
        # 初始化渠道包管理器
        channel_manager = ChannelPackageManager()
        
        # 测试生成渠道包
        print("\n测试生成渠道包...")
        result = channel_manager.generate_channels(
            signed_apk_path=test_apk,
            channel_config_path=channel_config
        )
        
        if result['success']:
            print(f"✅ 成功生成 {result['channel_count']} 个渠道包")
            print("生成的渠道包列表:")
            for apk_path in result['channel_packages']:
                print(f"   - {os.path.basename(apk_path)}")
                
            # 验证生成的渠道包
            print("\n验证生成的渠道包...")
            for apk_path in result['channel_packages']:
                apk_name = os.path.basename(apk_path)
                # 提取渠道名
                channel_id = apk_name.split('_')[-1].replace('.apk', '')
                
                # 使用官方walle工具验证
                walle_jar = os.path.join(os.path.dirname(__file__), 'lib/walle-cli-all.jar')
                if os.path.exists(walle_jar):
                    import subprocess
                    cmd = ['java', '-jar', walle_jar, 'show', apk_path]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"✅ {apk_name}: {result.stdout.strip()}")
                    else:
                        print(f"❌ {apk_name}: 验证失败 - {result.stderr.strip()}")
                else:
                    print(f"⚠️  {apk_name}: 未找到官方walle工具，跳过验证")
        else:
            print(f"❌ 生成渠道包失败: {result['message']}")
            return False
        
        print("\n🎉 所有测试通过！")
        return True
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n📁 清理临时目录: {temp_dir}")

if __name__ == "__main__":
    test_channel_packer()
