#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多渠道打包模块
负责在加固和签名后，根据渠道配置生成多渠道APK
基于官方瓦力(walle)原理实现，纯Python版本
"""

# 设置Python路径，确保能正确导入模块
import sys
import os
import subprocess

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(current_dir))
# 将项目根目录添加到Python路径
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import shutil
from loguru import logger
from src.core.channel_manager import ChannelConfigManager
from src.core.walle_python_impl import WallePythonImpl

class ChannelPackageManager:
    """多渠道包管理器"""
    
    def __init__(self):
        """初始化多渠道包管理器"""
        self.channel_manager = ChannelConfigManager()
        self.walle_impl = WallePythonImpl()
    
    def _get_market_name(self, channel_name):
        """
        根据渠道名获取市场名称
        :param channel_name: 渠道名
        :return: 市场名称
        """
        # 1. 优先使用渠道配置中的MARKET_NAME元数据
        channel_config = self.channel_manager.get_channel_by_name(channel_name)
        if channel_config and 'metadata' in channel_config:
            market_name = channel_config['metadata'].get('MARKET_NAME')
            if market_name:
                return market_name
        
        # 2. 默认市场名称映射（作为最后的fallback）
        default_market_map = {
            'google_play': 'Google Play',
            'huawei': 'Huawei AppGallery',
            'xiaomi': 'Xiaomi MIUI Store',
            'oppo': 'OPPO App Market',
            'vivo': 'vivo App Store',
            'meizu': 'Meizu Flyme Store',
            'samsung': 'Samsung Galaxy Store',
            'lenovo': 'Lenovo App Store',
            '360': '360 Mobile Assistant',
            'baidu': 'Baidu Mobile Assistant',
            'tencent': 'Tencent MyApp',
            'yingyongbao': '应用宝'
        }
        
        # 3. 使用默认映射或首字母大写的渠道名
        return default_market_map.get(channel_name, channel_name.capitalize())
    
    def generate_channels(self, signed_apk_path, channel_config_path, keystore_info=None):
        """
        生成多渠道包主入口
        :param signed_apk_path: 已签名的APK路径
        :param channel_config_path: 渠道配置文件路径
        :param keystore_info: 签名信息（兼容旧接口）
        :return: 生成结果
        """
        try:
            logger.info("===== 开始多渠道打包流程 =====")
            
            # 验证输入文件
            if not os.path.exists(signed_apk_path):
                logger.error(f"APK文件不存在: {signed_apk_path}")
                return {
                    'success': False,
                    'message': f"APK文件不存在: {signed_apk_path}",
                    'channel_packages': []
                }
            
            if not os.path.exists(channel_config_path):
                logger.error(f"渠道配置文件不存在: {channel_config_path}")
                return {
                    'success': False,
                    'message': f"渠道配置文件不存在: {channel_config_path}",
                    'channel_packages': []
                }
            
            # 加载渠道配置
            if not self.channel_manager.load_config(channel_config_path):
                logger.error("加载渠道配置失败")
                return {
                    'success': False,
                    'message': "加载渠道配置失败",
                    'channel_packages': []
                }
            
            # 获取输出配置
            output_config = self.channel_manager.get_output_config()
            output_dir = output_config.get('directory', './channels')
            
            # 确保输出目录存在
            base_dir = os.path.dirname(signed_apk_path)
            final_output_dir = os.path.join(base_dir, output_dir)
            os.makedirs(final_output_dir, exist_ok=True)
            
            # 获取渠道列表
            channels = self.channel_manager.get_channels()
            if not channels:
                logger.error("渠道列表为空")
                return {
                    'success': False,
                    'message': "渠道列表为空",
                    'channel_packages': []
                }
            
            logger.info(f"使用纯Python walle实现生成渠道包...")
            logger.info(f"渠道数: {len(channels)}")
            logger.info(f"输出目录: {final_output_dir}")
            
            # 使用纯Python实现生成渠道包
            generated_packages = []
            for channel in channels:
                # 使用CHANNEL_ID作为渠道标识，若不存在则使用channel_name作为fallback
                channel_id = channel.get('metadata', {}).get('CHANNEL_ID', channel['name'])
                channel_name = channel['name']
                apk_name = os.path.basename(signed_apk_path)
                apk_base_name, apk_ext = os.path.splitext(apk_name)
                
                # 生成渠道包文件名
                channel_apk_name = f"{apk_base_name}_{channel_id}{apk_ext}"
                channel_apk_path = os.path.join(final_output_dir, channel_apk_name)
                
                # 首先检查是否有官方walle工具可用
                walle_jar = os.path.join(os.path.dirname(__file__), '../../lib/walle-cli-all.jar')
                if os.path.exists(walle_jar):
                    # 使用官方walle工具生成渠道包
                    logger.info(f"使用官方walle工具生成渠道包: {channel_apk_name}")
                    
                    cmd = [
                        'java', '-jar', walle_jar,
                        'put', '-c', channel_id,
                        signed_apk_path,
                        channel_apk_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        generated_packages.append(channel_apk_path)
                        logger.info(f"渠道包生成成功: {channel_apk_path}")
                    else:
                        logger.error(f"官方walle工具生成失败: {result.stderr}")
                        # 尝试使用纯Python实现
                        logger.info(f"尝试使用纯Python实现生成渠道包: {channel_apk_name}")
                        success = self.walle_impl.inject_channel(signed_apk_path, channel_apk_path, channel_id)
                        
                        if success:
                            generated_packages.append(channel_apk_path)
                            logger.info(f"渠道包生成成功: {channel_apk_path}")
                        else:
                            logger.error(f"渠道包生成失败: {channel_apk_path}")
                else:
                    # 只有纯Python实现可用
                    logger.info(f"正在生成渠道包: {channel_apk_name}")
                    success = self.walle_impl.inject_channel(signed_apk_path, channel_apk_path, channel_id)
                    
                    if success:
                        generated_packages.append(channel_apk_path)
                        logger.info(f"渠道包生成成功: {channel_apk_path}")
                    else:
                        logger.error(f"渠道包生成失败: {channel_apk_path}")
            
            logger.info(f"多渠道打包完成，共生成 {len(generated_packages)} 个渠道包")
            
            return {
                'success': True,
                'message': f"成功生成 {len(generated_packages)} 个渠道包",
                'channel_packages': generated_packages,
                'channel_count': len(generated_packages)
            }
        except Exception as e:
            logger.error(f"多渠道打包流程失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"多渠道打包失败: {str(e)}",
                'channel_packages': []
            }


if __name__ == "__main__":
    """
    当直接运行此文件时，显示使用说明
    """
    print("=== 多渠道打包模块使用说明 ===")
    print("此模块不能直接运行，应作为库被其他模块调用")
    print("\n使用示例：")
    print("from src.core.channel_packer import ChannelPackageManager")
    print("\n# 初始化渠道打包管理器")
    print("channel_manager = ChannelPackageManager()")
    print("\n# 生成渠道包")
    print("result = channel_manager.generate_channels(")
    print("    signed_apk_path='your_signed.apk',")
    print("    channel_config_path='channel_config.yaml'")
    print(")")
    print("\n# 处理结果")
    print("if result['success']:")
    print("    print(f'成功生成 {result['channel_count']} 个渠道包')")
    print("else:")
    print("    print(f'生成失败: {result['message']}')")
    print("\n详细文档请查看相关注释")