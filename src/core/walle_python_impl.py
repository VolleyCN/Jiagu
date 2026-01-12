#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯Python实现的walle渠道注入器
基于反编译的walle-cli-all.jar代码实现
"""

import os
import struct
import json
import shutil
from loguru import logger

class SignatureNotFoundException(Exception):
    """未找到签名异常"""
    pass

class WallePythonImpl:
    """
    纯Python实现的walle渠道注入器
    基于APK v2签名机制，在APK Signing Block中注入渠道信息
    """
    
    # walle自定义ID，用于标识渠道信息块
    WALLE_CHANNEL_BLOCK_ID = 0x71777777  # 1903654775，'waww'的ASCII码，小端序
    APK_SIG_BLOCK_MAGIC_LO = 0x20676953204b5041  # APK Sig Block Magic Low
    APK_SIG_BLOCK_MAGIC_HI = 0x3234206b636f6c42  # APK Sig Block Magic High
    APK_SIGNATURE_SCHEME_V2_BLOCK_ID = 0x7109871a  # APK v2签名块ID
    VERITY_PADDING_BLOCK_ID = 0x42726577  # 验证填充块ID
    APK_SIG_BLOCK_MIN_SIZE = 32  # APK签名块最小大小
    
    def __init__(self):
        """初始化walle渠道注入器"""
        pass
    
    def _get_comment_length(self, file_path):
        """
        获取ZIP文件的注释长度
        :param file_path: APK文件路径
        :return: 注释长度
        """
        with open(file_path, 'rb') as f:
            file_size = f.seek(0, 2)
            
            # EOCD记录最小22字节
            max_comment_length = min(file_size - 22, 65535)  # 注释长度最大65535字节
            
            # 从文件末尾开始查找EOCD标记
            for expected_comment_length in range(0, int(max_comment_length) + 1):
                eocd_pos = file_size - 22 - expected_comment_length
                f.seek(eocd_pos)
                sig = struct.unpack('<I', f.read(4))[0]
                
                if sig == 0x06054b50:  # EOCD标记
                    # 读取实际注释长度
                    f.seek(eocd_pos + 20)
                    actual_comment_length = struct.unpack('<H', f.read(2))[0]
                    
                    if actual_comment_length == expected_comment_length:
                        return actual_comment_length
        
        raise SignatureNotFoundException("未找到ZIP EOCD记录")
    
    def _find_central_dir_start_offset(self, file_path, comment_length):
        """
        查找ZIP Central Directory的起始偏移量
        :param file_path: APK文件路径
        :param comment_length: 注释长度
        :return: Central Directory起始偏移量
        """
        with open(file_path, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            
            # 读取Central Directory偏移量
            f.seek(file_size - comment_length - 6)  # 6 = 2(Comment length) + 4(Offset)
            central_dir_offset = struct.unpack('<I', f.read(4))[0]
            
            return central_dir_offset
    
    def _find_apk_signing_block(self, file_path, central_dir_offset):
        """
        查找APK Signing Block
        :param file_path: APK文件路径
        :param central_dir_offset: Central Directory起始偏移量
        :return: (APK Signing Block数据, APK Signing Block偏移量)
        """
        if central_dir_offset < self.APK_SIG_BLOCK_MIN_SIZE:
            raise SignatureNotFoundException(
                f"APK太小，无法容纳APK Signing Block。ZIP Central Directory偏移量: {central_dir_offset}")
        
        with open(file_path, 'rb') as f:
            # 读取APK Signing Block的footer
            f.seek(central_dir_offset - 24)
            footer = f.read(24)
            
            # 解析footer
            footer_magic_lo = struct.unpack('<Q', footer[8:16])[0]
            footer_magic_hi = struct.unpack('<Q', footer[16:24])[0]
            
            if footer_magic_lo != self.APK_SIG_BLOCK_MAGIC_LO or footer_magic_hi != self.APK_SIG_BLOCK_MAGIC_HI:
                raise SignatureNotFoundException("未找到有效的APK Signing Block魔法数字")
            
            # 读取footer中的大小
            footer_size = struct.unpack('<Q', footer[0:8])[0]
            
            # 计算APK Signing Block的起始位置和大小
            apk_signing_block_size = footer_size + 8  # 加上大小字段
            apk_signing_block_offset = central_dir_offset - apk_signing_block_size
            
            if apk_signing_block_offset < 0:
                raise SignatureNotFoundException(f"APK Signing Block偏移量超出范围: {apk_signing_block_offset}")
            
            # 读取完整的APK Signing Block
            f.seek(apk_signing_block_offset)
            apk_signing_block = f.read(apk_signing_block_size)
            
            # 验证header中的大小
            header_size = struct.unpack('<Q', apk_signing_block[0:8])[0]
            if header_size != footer_size:
                raise SignatureNotFoundException(
                    f"APK Signing Block头部和尾部大小不匹配: {header_size} vs {footer_size}")
            
            return apk_signing_block, apk_signing_block_offset
    
    def _find_id_values(self, apk_signing_block):
        """
        查找APK Signing Block中的ID值对
        :param apk_signing_block: APK Signing Block数据
        :return: ID值对字典
        """
        id_values = {}
        
        # 跳过header大小字段，从pairs开始
        pos = 8
        end = len(apk_signing_block) - 24  # 减去footer的24字节
        
        while pos < end:
            # 读取entry大小
            entry_size = struct.unpack('<Q', apk_signing_block[pos:pos+8])[0]
            pos += 8
            
            # 读取entry ID
            entry_id = struct.unpack('<I', apk_signing_block[pos:pos+4])[0]
            pos += 4
            
            # 读取entry值
            value_size = entry_size - 4
            entry_value = apk_signing_block[pos:pos+value_size]
            pos += value_size
            
            id_values[entry_id] = entry_value
        
        return id_values
    
    def _create_apk_signing_block(self, id_values):
        """
        创建新的APK Signing Block
        :param id_values: ID值对字典
        :return: 新的APK Signing Block数据
        """
        # 计算pairs部分的大小
        pairs_data = b''
        for entry_id, entry_value in id_values.items():
            # 计算entry大小
            entry_size = 4 + len(entry_value)  # ID(4字节) + 值
            pairs_data += struct.pack('<Q', entry_size)
            pairs_data += struct.pack('<I', entry_id)
            pairs_data += entry_value
        
        # 计算总大小
        total_size = 8 + len(pairs_data) + 24  # 大小字段(8) + pairs + footer(24)
        
        # 构建APK Signing Block
        apk_signing_block = b''
        apk_signing_block += struct.pack('<Q', total_size - 8)  # 总大小（不包括自身）
        apk_signing_block += pairs_data
        apk_signing_block += struct.pack('<Q', total_size - 8)  # 重复的总大小
        apk_signing_block += struct.pack('<Q', self.APK_SIG_BLOCK_MAGIC_LO)  # 魔法数字low
        apk_signing_block += struct.pack('<Q', self.APK_SIG_BLOCK_MAGIC_HI)  # 魔法数字high
        
        return apk_signing_block
    
    def parse_channel_info(self, channel_value):
        """
        解析渠道信息
        :param channel_value: 渠道信息的二进制数据
        :return: 渠道字典
        """
        try:
            channel_str = channel_value.decode('utf-8')
            return json.loads(channel_str)
        except (UnicodeDecodeError, json.JSONDecodeError):
            # 如果不是JSON格式，返回简单的渠道信息
            return {'channel': channel_value.decode('utf-8', errors='ignore')}
    
    def create_channel_info(self, channel):
        """
        创建渠道信息JSON
        :param channel: 渠道名
        :return: 渠道信息JSON字符串
        """
        channel_data = {'channel': channel}
        return json.dumps(channel_data, ensure_ascii=False)
    
    def inject_channel(self, source_apk, target_apk, channel):
        """
        向APK文件中注入渠道信息
        :param source_apk: 源APK文件路径
        :param target_apk: 目标APK文件路径
        :param channel: 渠道信息
        :return: 是否成功
        """
        try:
            logger.info(f"开始注入渠道: {channel}")
            logger.info(f"源文件: {source_apk}")
            logger.info(f"目标文件: {target_apk}")
            
            # 复制源文件到目标文件
            if source_apk != target_apk:
                shutil.copy2(source_apk, target_apk)
            
            # 1. 获取注释长度
            comment_length = self._get_comment_length(target_apk)
            logger.info(f"Comment长度: {comment_length}")
            
            # 2. 查找Central Directory起始偏移量
            central_dir_offset = self._find_central_dir_start_offset(target_apk, comment_length)
            logger.info(f"原始Central Directory偏移量: {central_dir_offset}")
            
            # 3. 查找APK Signing Block
            apk_signing_block, apk_signing_block_offset = self._find_apk_signing_block(target_apk, central_dir_offset)
            logger.info(f"找到APK Signing Block: 偏移量={apk_signing_block_offset}, 大小={len(apk_signing_block)}")
            
            # 4. 解析APK Signing Block中的ID值对
            id_values = self._find_id_values(apk_signing_block)
            logger.info(f"解析到 {len(id_values)} 个子块")
            
            # 5. 检查是否有APK v2签名块
            if self.APK_SIGNATURE_SCHEME_V2_BLOCK_ID not in id_values:
                raise SignatureNotFoundException("未找到APK Signature Scheme v2 block")
            
            # 6. 移除可能的验证填充块
            need_padding = self.VERITY_PADDING_BLOCK_ID in id_values
            if need_padding:
                del id_values[self.VERITY_PADDING_BLOCK_ID]
            
            # 7. 构建渠道信息
            channel_json = self.create_channel_info(channel)
            channel_bytes = channel_json.encode('utf-8')
            logger.info(f"渠道JSON: {channel_json}")
            
            # 8. 更新或添加渠道块
            id_values[self.WALLE_CHANNEL_BLOCK_ID] = channel_bytes
            
            # 9. 创建新的APK Signing Block
            new_apk_signing_block = self._create_apk_signing_block(id_values)
            logger.info(f"新的APK Signing Block大小: {len(new_apk_signing_block)}")
            
            # 10. 写入新的APK Signing Block
            with open(target_apk, 'r+b') as f:
                # 读取Central Directory数据
                f.seek(central_dir_offset)
                central_dir_data = f.read()
                logger.info(f"Central Directory数据大小: {len(central_dir_data)}")
                
                # 更新APK Signing Block
                f.seek(apk_signing_block_offset)
                f.write(new_apk_signing_block)
                
                # 写入Central Directory数据
                f.write(central_dir_data)
                
                # 更新文件长度
                f.truncate()
                
                # 计算新的Central Directory偏移量
                new_central_dir_offset = apk_signing_block_offset + len(new_apk_signing_block)
                
                # 更新EOCD中的Central Directory偏移量
                f.seek(0, 2)
                f.seek(f.tell() - comment_length - 6)  # 6 = 2(Comment length) + 4(Offset)
                f.write(struct.pack('<I', new_central_dir_offset))
            
            logger.info(f"渠道注入成功: {channel}")
            return True
        except Exception as e:
            logger.error(f"渠道注入失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_channel(self, apk_path):
        """
        从APK文件中读取渠道信息
        :param apk_path: APK文件路径
        :return: 渠道信息，如果没有找到返回None
        """
        try:
            logger.info(f"开始读取渠道信息: {apk_path}")
            
            # 1. 获取注释长度
            comment_length = self._get_comment_length(apk_path)
            
            # 2. 查找Central Directory起始偏移量
            central_dir_offset = self._find_central_dir_start_offset(apk_path, comment_length)
            
            # 3. 查找APK Signing Block
            apk_signing_block, _ = self._find_apk_signing_block(apk_path, central_dir_offset)
            
            # 4. 解析APK Signing Block中的ID值对
            id_values = self._find_id_values(apk_signing_block)
            
            # 5. 查找渠道块
            if self.WALLE_CHANNEL_BLOCK_ID in id_values:
                channel_value = id_values[self.WALLE_CHANNEL_BLOCK_ID]
                channel_info = self.parse_channel_info(channel_value)
                channel = channel_info.get('channel', None)
                logger.info(f"成功读取渠道信息: {channel}")
                return channel
            
            logger.warning("未找到渠道信息")
            return None
        except Exception as e:
            logger.error(f"读取渠道信息失败: {e}")
            import traceback
            traceback.print_exc()
            return None
