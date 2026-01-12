#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
签名验证与重签名功能模块
负责APK签名验证、重签名和密钥库管理
"""

import os
import tempfile
import subprocess
import shutil
from loguru import logger

class SignatureManager:
    """签名管理器"""
    
    def __init__(self):
        """初始化签名管理器"""
        self.jarsigner_path = self._find_jarsigner()
        self.apksigner_path = self._find_apksigner()
        self.zipalign_path = self._find_zipalign()
    
    def _find_jarsigner(self):
        """
        查找jarsigner工具路径
        :return: jarsigner路径
        """
        try:
            # 检查JAVA_HOME
            java_home = os.environ.get("JAVA_HOME")
            if java_home:
                jarsigner_path = os.path.join(java_home, "bin", "jarsigner")
                if os.path.exists(jarsigner_path):
                    return jarsigner_path
            
            # 检查系统PATH
            result = subprocess.run(["which", "jarsigner"], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"未找到jarsigner工具: {e}")
            raise FileNotFoundError("jarsigner not found")
    
    def _find_apksigner(self):
        """
        查找apksigner工具路径
        :return: apksigner路径
        """
        try:
            # 检查ANDROID_SDK_ROOT
            sdk_root = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
            if sdk_root:
                apksigner_path = os.path.join(sdk_root, "build-tools", "latest", "apksigner")
                if os.path.exists(apksigner_path):
                    return apksigner_path
                
                # 尝试查找最新版本的build-tools
                build_tools_dir = os.path.join(sdk_root, "build-tools")
                if os.path.exists(build_tools_dir):
                    versions = [v for v in os.listdir(build_tools_dir) if os.path.isdir(os.path.join(build_tools_dir, v))]
                    versions.sort(reverse=True)
                    for version in versions:
                        apksigner_path = os.path.join(build_tools_dir, version, "apksigner")
                        if os.path.exists(apksigner_path):
                            return apksigner_path
            
            logger.warning("未找到apksigner工具，将仅使用jarsigner")
            return None
        except Exception as e:
            logger.warning(f"查找apksigner失败: {e}")
            return None
    
    def _find_zipalign(self):
        """
        查找zipalign工具路径
        :return: zipalign路径
        """
        try:
            # 检查ANDROID_SDK_ROOT
            sdk_root = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
            if sdk_root:
                zipalign_path = os.path.join(sdk_root, "build-tools", "latest", "zipalign")
                if os.path.exists(zipalign_path):
                    return zipalign_path
                
                # 尝试查找最新版本的build-tools
                build_tools_dir = os.path.join(sdk_root, "build-tools")
                if os.path.exists(build_tools_dir):
                    versions = [v for v in os.listdir(build_tools_dir) if os.path.isdir(os.path.join(build_tools_dir, v))]
                    versions.sort(reverse=True)
                    for version in versions:
                        zipalign_path = os.path.join(build_tools_dir, version, "zipalign")
                        if os.path.exists(zipalign_path):
                            return zipalign_path
            
            logger.warning("未找到zipalign工具")
            return None
        except Exception as e:
            logger.warning(f"查找zipalign失败: {e}")
            return None
    
    def verify_signature(self, apk_path):
        """
        验证APK签名
        :param apk_path: APK路径
        :return: 签名验证结果
        """
        try:
            logger.info(f"开始验证APK签名: {apk_path}")
            
            # 首先检查文件是否存在
            if not os.path.exists(apk_path):
                return {
                    'success': False,
                    'message': f"APK文件不存在: {apk_path}"
                }
            
            # 优先使用apksigner验证
            if self.apksigner_path:
                result = subprocess.run([self.apksigner_path, "verify", "--verbose", apk_path], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("APK签名验证通过")
                    return {
                        'success': True,
                        'tool': 'apksigner',
                        'output': result.stdout
                    }
                else:
                    logger.warning(f"APK签名验证失败: {result.stderr}")
                    return {
                        'success': False,
                        'tool': 'apksigner',
                        'error': result.stderr
                    }
            # 回退使用jarsigner验证
            else:
                result = subprocess.run([self.jarsigner_path, "-verify", apk_path], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info("APK签名验证通过")
                    return {
                        'success': True,
                        'tool': 'jarsigner',
                        'output': result.stdout
                    }
                else:
                    logger.warning(f"APK签名验证失败: {result.stderr}")
                    return {
                        'success': False,
                        'tool': 'jarsigner',
                        'error': result.stderr
                    }
        except Exception as e:
            logger.error(f"签名验证失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sign_apk(self, apk_path, output_path, keystore_path, keystore_password, key_alias, key_password, 
                 v1_signature=True, v2_signature=True, v3_signature=False):
        """
        重签名APK文件
        :param apk_path: 原始APK路径
        :param output_path: 输出APK路径
        :param keystore_path: 密钥库路径
        :param keystore_password: 密钥库密码
        :param key_alias: 密钥别名
        :param key_password: 密钥密码
        :param v1_signature: 是否启用V1签名
        :param v2_signature: 是否启用V2签名
        :param v3_signature: 是否启用V3签名
        :return: 签名结果
        """
        try:
            logger.info(f"开始重签名APK: {apk_path}")
            
            # 验证输入文件
            if not os.path.exists(apk_path):
                return {
                    'success': False,
                    'message': f"APK文件不存在: {apk_path}"
                }
            
            if not os.path.exists(keystore_path):
                return {
                    'success': False,
                    'message': f"密钥库文件不存在: {keystore_path}"
                }
            
            # 创建临时文件用于签名
            temp_signed = tempfile.mktemp(suffix=".apk")
            
            try:
                # 先对齐APK
                aligned_input = apk_path
                if self.zipalign_path:
                    logger.info("使用zipalign对齐APK")
                    temp_aligned = tempfile.mktemp(suffix=".apk")
                    
                    cmd = [
                        self.zipalign_path,
                        "-f", "4",  # 4字节对齐
                        apk_path,
                        temp_aligned
                    ]
                    
                    subprocess.run(cmd, capture_output=True, text=True, check=True)
                    aligned_input = temp_aligned
                
                # 优先使用apksigner签名
                if self.apksigner_path:
                    logger.info("使用apksigner进行签名")
                    
                    # 构建apksigner命令
                    cmd = [
                        self.apksigner_path,
                        "sign",
                        "--ks", keystore_path,
                        "--ks-pass", f"pass:{keystore_password}",
                        "--ks-key-alias", key_alias,
                        "--key-pass", f"pass:{key_password}"
                    ]
                    
                    # 添加签名版本选项
                    if not v1_signature:
                        cmd.extend(["--v1-signing-enabled", "false"])
                    if not v2_signature:
                        cmd.extend(["--v2-signing-enabled", "false"])
                    if v3_signature:
                        cmd.extend(["--v3-signing-enabled", "true"])
                    else:
                        cmd.extend(["--v3-signing-enabled", "false"])
                    
                    # 添加输出路径参数
                    cmd.extend(["--out", output_path])
                    
                    # 最后添加输入APK路径（已对齐）
                    cmd.append(aligned_input)
                    
                    # 执行签名命令
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    logger.debug(f"apksigner输出: {result.stdout}")
                # 回退使用jarsigner签名（仅支持V1签名）
                else:
                    logger.info("使用jarsigner进行签名（仅V1）")
                    
                    # 首先复制对齐后的APK到临时文件
                    temp_signed = tempfile.mktemp(suffix=".apk")
                    shutil.copy2(aligned_input, temp_signed)
                    
                    # 使用jarsigner签名
                    cmd = [
                        self.jarsigner_path,
                        "-sigalg", "SHA256withRSA",
                        "-digestalg", "SHA-256",
                        "-keystore", keystore_path,
                        "-storepass", keystore_password,
                        "-keypass", key_password,
                        temp_signed,
                        key_alias
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                    logger.debug(f"jarsigner输出: {result.stdout}")
                    
                    # 复制到输出路径
                    shutil.copy2(temp_signed, output_path)
                    
                    # 清理临时文件
                    if temp_signed != aligned_input:
                        os.remove(temp_signed)
                
                # 清理对齐临时文件
                if aligned_input != apk_path:
                    os.remove(aligned_input)
                
                logger.info(f"APK重签名完成: {output_path}")
                
                # 验证签名结果
                verify_result = self.verify_signature(output_path)
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'verify_result': verify_result,
                    'signature_types': {
                        'v1': v1_signature,
                        'v2': v2_signature if self.apksigner_path else False,
                        'v3': v3_signature if self.apksigner_path else False
                    }
                }
            finally:
                # 清理临时文件
                if os.path.exists(temp_signed):
                    os.remove(temp_signed)
        except subprocess.CalledProcessError as e:
            logger.error(f"重签名命令执行失败: {e}")
            return {
                'success': False,
                'error': e.stderr or str(e),
                'cmd': e.cmd
            }
        except Exception as e:
            logger.error(f"重签名失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_keystore(self, keystore_path, keystore_password, key_alias, key_password, 
                       dname="CN=Unknown, OU=Unknown, O=Unknown, L=Unknown, ST=Unknown, C=Unknown", 
                       validity=3650):
        """
        创建新的密钥库
        :param keystore_path: 密钥库路径
        :param keystore_password: 密钥库密码
        :param key_alias: 密钥别名
        :param key_password: 密钥密码
        :param dname: 密钥所有者信息
        :param validity: 密钥有效期（天）
        :return: 创建结果
        """
        try:
            logger.info(f"开始创建密钥库: {keystore_path}")
            
            # 查找keytool
            try:
                java_home = os.environ.get("JAVA_HOME")
                if java_home:
                    keytool_path = os.path.join(java_home, "bin", "keytool")
                else:
                    result = subprocess.run(["which", "keytool"], capture_output=True, text=True, check=True)
                    keytool_path = result.stdout.strip()
            except Exception as e:
                logger.error(f"未找到keytool工具: {e}")
                raise FileNotFoundError("keytool not found")
            
            # 构建keytool命令
            cmd = [
                keytool_path,
                "-genkeypair",
                "-keystore", keystore_path,
                "-storepass", keystore_password,
                "-alias", key_alias,
                "-keypass", key_password,
                "-dname", dname,
                "-validity", str(validity),
                "-keyalg", "RSA",
                "-keysize", "2048",
                "-sigalg", "SHA256withRSA",
                "-deststoretype", "JKS"
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.debug(f"keytool输出: {result.stdout}")
            
            logger.info(f"密钥库创建成功: {keystore_path}")
            return {
                'success': True,
                'keystore_path': keystore_path,
                'key_alias': key_alias
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"创建密钥库失败: {e.stderr}")
            return {
                'success': False,
                'error': e.stderr or str(e)
            }
        except Exception as e:
            logger.error(f"创建密钥库失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_signature_info(self, apk_path):
        """
        提取APK签名信息
        :param apk_path: APK路径
        :return: 签名信息
        """
        try:
            logger.info(f"开始提取APK签名信息: {apk_path}")
            
            if not self.apksigner_path:
                return {
                    'success': False,
                    'message': "apksigner工具不可用，无法提取签名信息"
                }
            
            cmd = [self.apksigner_path, "verify", "--print-certs", "--verbose", apk_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("签名信息提取成功")
                return {
                    'success': True,
                    'signature_info': result.stdout
                }
            else:
                logger.warning(f"提取签名信息失败: {result.stderr}")
                return {
                    'success': False,
                    'error': result.stderr
                }
        except Exception as e:
            logger.error(f"提取签名信息失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
