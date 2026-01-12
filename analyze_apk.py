#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析渠道注入前后的APK文件
包括签名信息检查、渠道信息块验证等
"""

import os
import sys
import zipfile
import struct


def check_apk_signature(apk_path):
    """检查APK的签名信息"""
    print(f"\n=== 检查APK签名信息: {os.path.basename(apk_path)} ===")
    
    try:
        with zipfile.ZipFile(apk_path, 'r') as zipf:
            # 检查META-INF目录下的签名文件
            meta_inf_files = [f for f in zipf.namelist() if f.startswith('META-INF/')]
            print(f"META-INF目录文件数: {len(meta_inf_files)}")
            
            # 查找签名相关文件
            signature_files = []
            for file in meta_inf_files:
                if file.endswith(('.SF', '.RSA', '.DSA', '.EC')):
                    signature_files.append(file)
            
            print(f"签名相关文件: {signature_files}")
            
            if signature_files:
                print("✓ 找到签名文件")
            else:
                print("✗ 未找到签名文件")
                
    except Exception as e:
        print(f"✗ 检查签名信息失败: {e}")


def check_channel_block(apk_path):
    """检查APK中的渠道信息块"""
    print(f"\n=== 检查APK渠道信息块: {os.path.basename(apk_path)} ===")
    
    try:
        with open(apk_path, 'rb') as f:
            # 从文件末尾开始读取，寻找瓦力魔数
            f.seek(-4096, os.SEEK_END)
            end_data = f.read(4096)
            
            # 查找瓦力魔数 Walle
            WALLE_MAGIC = b'WALLE'
            magic_positions = []
            pos = 0
            
            while True:
                pos = end_data.find(WALLE_MAGIC, pos)
                if pos == -1:
                    break
                magic_positions.append(pos)
                pos += len(WALLE_MAGIC)
            
            print(f"找到瓦力魔数的位置: {magic_positions}")
            
            if len(magic_positions) >= 2:
                # 渠道信息块格式: WALLE + version + len + data + WALLE
                # 找到最后一对魔数
                magic1_pos = magic_positions[-2]
                magic2_pos = magic_positions[-1]
                
                print(f"最后一对魔数位置: {magic1_pos} 和 {magic2_pos}")
                
                # 提取渠道信息块
                channel_block = end_data[magic1_pos:magic2_pos + len(WALLE_MAGIC)]
                print(f"渠道信息块长度: {len(channel_block)} 字节")
                
                # 解析渠道信息块
                if len(channel_block) >= 13:  # WALLE(5) + version(1) + len(4) + WALLE(5) = 15 至少
                    version = channel_block[5]
                    data_len = struct.unpack('<I', channel_block[6:10])[0]
                    
                    print(f"版本号: {version}")
                    print(f"数据长度: {data_len} 字节")
                    
                    if len(channel_block) >= 10 + data_len + 5:
                        channel_data = channel_block[10:10 + data_len]
                        try:
                            channel_text = channel_data.decode('utf-8')
                            print(f"渠道数据: {channel_text}")
                            print("✓ 渠道信息块格式正确")
                            return channel_text
                        except UnicodeDecodeError:
                            print("✗ 渠道数据解码失败")
                    else:
                        print("✗ 渠道信息块长度不足")
                else:
                    print("✗ 渠道信息块格式错误")
            else:
                print("✗ 未找到完整的渠道信息块")
                
    except Exception as e:
        print(f"✗ 检查渠道信息块失败: {e}")
    
    return None


def compare_apk_files(original_apk, channel_apk):
    """比较原始APK和渠道APK"""
    print(f"\n=== 比较APK文件 ===")
    print(f"原始APK: {os.path.basename(original_apk)}")
    print(f"渠道APK: {os.path.basename(channel_apk)}")
    
    original_size = os.path.getsize(original_apk)
    channel_size = os.path.getsize(channel_apk)
    
    print(f"原始大小: {original_size} 字节")
    print(f"渠道大小: {channel_size} 字节")
    print(f"大小差异: {channel_size - original_size} 字节")
    
    # 检查是否只是末尾追加了数据
    with open(original_apk, 'rb') as f1, open(channel_apk, 'rb') as f2:
        original_data = f1.read()
        channel_data = f2.read()
        
        if channel_data.startswith(original_data):
            print("✓ 渠道APK是在原始APK末尾追加了数据")
        else:
            print("✗ 渠道APK不是简单的末尾追加")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python analyze_apk.py <原始APK> [<渠道APK>]")
        sys.exit(1)
    
    original_apk = sys.argv[1]
    channel_apk = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 检查原始APK
    if not os.path.exists(original_apk):
        print(f"原始APK不存在: {original_apk}")
        sys.exit(1)
    
    # 检查渠道APK（如果提供）
    if channel_apk and not os.path.exists(channel_apk):
        print(f"渠道APK不存在: {channel_apk}")
        sys.exit(1)
    
    # 检查原始APK
    check_apk_signature(original_apk)
    
    # 如果提供了渠道APK
    if channel_apk:
        check_apk_signature(channel_apk)
        channel_info = check_channel_block(channel_apk)
        compare_apk_files(original_apk, channel_apk)
    else:
        # 只检查原始APK的渠道信息块
        check_channel_block(original_apk)

if __name__ == "__main__":
    main()
