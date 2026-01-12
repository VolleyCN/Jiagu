#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多渠道打包模块 - 渠道元数据复用
验证_get_market_name方法是否正确复用渠道配置中的MARKET_NAME元数据
"""

import os
import tempfile
from src.core.channel_packer import FastChannelPacker
from src.core.channel_manager import ChannelConfigManager

# 创建测试用的渠道配置文件（包含MARKET_NAME元数据）
TEST_CONFIG_CONTENT = """
version: 1.0

output:
  overwrite: true
  directory: ./test_channels

# 自定义市场名称映射
market_map:
  custom_channel: "Config Market Name"
  google_play: "Config Google Play"

channels:
  # 渠道1：包含MARKET_NAME元数据
  - name: custom_channel
    metadata:
      CHANNEL_ID: custom_channel
      MARKET_NAME: Metadata Market Name  # 这里的优先级应该最高
  
  # 渠道2：包含MARKET_NAME元数据
  - name: test_channel
    metadata:
      CHANNEL_ID: test_channel
      MARKET_NAME: Test Market From Metadata
  
  # 渠道3：包含MARKET_NAME元数据但也有全局映射
  - name: google_play
    metadata:
      CHANNEL_ID: google_play
      MARKET_NAME: Metadata Google Play  # 这里的优先级应该高于全局映射
  
  # 渠道4：没有MARKET_NAME元数据，但有全局映射
  - name: huawei
    metadata:
      CHANNEL_ID: huawei
  
  # 渠道5：既没有MARKET_NAME元数据，也没有全局映射
  - name: xiaomi
    metadata:
      CHANNEL_ID: xiaomi
"""

def test_channel_metadata_reuse():
    """测试渠道元数据复用功能"""
    print("=== 测试渠道元数据复用 ===")
    
    # 创建临时配置文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(TEST_CONFIG_CONTENT)
        config_path = f.name
    
    try:
        # 初始化渠道管理器和打包器
        channel_manager = ChannelConfigManager()
        if channel_manager.load_config(config_path):
            print("✅ 配置文件加载成功")
            
            channel_packer = FastChannelPacker()
            channel_packer.channel_manager = channel_manager
            
            # 测试1: 优先使用渠道配置中的MARKET_NAME元数据
            result = channel_packer._get_market_name("custom_channel")
            expected = "Metadata Market Name"
            assert result == expected, f"测试1失败: 期望 '{expected}', 实际 '{result}'"
            print(f"✅ 测试1通过: custom_channel -> {result}")
            
            # 测试2: 优先使用渠道配置中的MARKET_NAME元数据
            result = channel_packer._get_market_name("test_channel")
            expected = "Test Market From Metadata"
            assert result == expected, f"测试2失败: 期望 '{expected}', 实际 '{result}'"
            print(f"✅ 测试2通过: test_channel -> {result}")
            
            # 测试3: 渠道元数据优先级高于全局market_map
            result = channel_packer._get_market_name("google_play")
            expected = "Metadata Google Play"
            assert result == expected, f"测试3失败: 期望 '{expected}', 实际 '{result}'"
            print(f"✅ 测试3通过: google_play -> {result}")
            
            # 测试4: 没有渠道元数据时使用全局market_map
            result = channel_packer._get_market_name("huawei")
            # huawei没有在全局market_map中，应该使用默认映射
            expected = "Huawei AppGallery"
            assert result == expected, f"测试4失败: 期望 '{expected}', 实际 '{result}'"
            print(f"✅ 测试4通过: huawei -> {result}")
            
            # 测试5: 既没有渠道元数据也没有全局映射时使用默认映射
            result = channel_packer._get_market_name("xiaomi")
            expected = "Xiaomi MIUI Store"
            assert result == expected, f"测试5失败: 期望 '{expected}', 实际 '{result}'"
            print(f"✅ 测试5通过: xiaomi -> {result}")
            
            # 测试6: 完全新渠道使用首字母大写
            result = channel_packer._get_market_name("new_channel")
            expected = "New_channel"
            assert result == expected, f"测试6失败: 期望 '{expected}', 实际 '{result}'"
            print(f"✅ 测试6通过: new_channel -> {result}")
            
            print("\n🎉 所有渠道元数据复用测试通过！")
            return True
        else:
            print("❌ 配置文件加载失败")
            return False
    
    except AssertionError as e:
        print(f"❌ 断言失败: {e}")
        return False
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    finally:
        # 清理临时文件
        if os.path.exists(config_path):
            os.remove(config_path)
    
    return True

if __name__ == "__main__":
    test_channel_metadata_reuse()
