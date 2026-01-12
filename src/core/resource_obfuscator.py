#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源文件混淆处理模块
负责资源文件的重命名、混淆和压缩
"""

import os
import tempfile
import shutil
import random
import string
from loguru import logger
import subprocess

class ResourceObfuscator:
    """资源文件混淆器"""
    
    def __init__(self):
        """初始化资源混淆器"""
        self.apktool_path = self._find_apktool()
        self.resource_mapping = {}
    
    def _find_apktool(self):
        """
        查找apktool工具路径
        :return: apktool路径或None
        """
        # 检查系统PATH中是否有apktool
        try:
            result = subprocess.run(["which", "apktool"], capture_output=True, text=True, check=True)
            apktool_path = result.stdout.strip()
            logger.info(f"找到apktool工具: {apktool_path}")
            return apktool_path
        except subprocess.CalledProcessError:
            # 如果系统中没有，检查tools目录
            apktool_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tools", "apktool")
            if os.path.exists(apktool_path):
                logger.info(f"在tools目录找到apktool工具: {apktool_path}")
                return apktool_path
            
            logger.warning("未找到apktool工具，请手动安装apktool或将其放在tools目录中")
            logger.warning("安装方法: 1. 访问 https://ibotpeaches.github.io/Apktool/ 下载")
            logger.warning("          2. 或使用命令: brew install apktool (需要Homebrew)")
            return None
    
    def _generate_random_name(self, length=8):
        """
        生成随机资源名称
        :param length: 名称长度
        :return: 随机名称
        """
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def decompile_apk(self, apk_path, output_dir):
        """
        使用apktool反编译APK文件
        :param apk_path: APK路径
        :param output_dir: 输出目录
        :return: 反编译结果
        """
        # 检查apktool是否可用
        if self.apktool_path is None:
            logger.error("apktool工具不可用，无法反编译APK")
            return False
        
        try:
            logger.info(f"开始反编译APK: {apk_path}")
            
            # 确保输出目录不存在
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            
            # 修复JAVA_HOME环境变量问题
            env = os.environ.copy()
            # 如果JAVA_HOME指向不存在的路径，取消它，让apktool使用默认值
            java_home = env.get('JAVA_HOME')
            if java_home and not os.path.exists(java_home):
                logger.warning(f"检测到无效的JAVA_HOME: {java_home}，已临时取消")
                del env['JAVA_HOME']
            
            # 执行apktool反编译命令
            result = subprocess.run([self.apktool_path, "d", apk_path, "-o", output_dir, "-f"], 
                                  capture_output=True, text=True, check=True, env=env)
            
            logger.info("APK反编译完成")
            logger.debug(f"apktool输出: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"APK反编译失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"反编译过程中发生错误: {e}")
            return False
    
    def compile_apk(self, decompiled_dir, output_apk):
        """
        使用apktool重新编译APK文件
        :param decompiled_dir: 反编译目录
        :param output_apk: 输出APK路径
        :return: 编译结果
        """
        # 检查apktool是否可用
        if self.apktool_path is None:
            logger.error("apktool工具不可用，无法编译APK")
            return False
        
        try:
            logger.info(f"开始重新编译APK: {output_apk}")
            
            # 修复JAVA_HOME环境变量问题
            env = os.environ.copy()
            # 如果JAVA_HOME指向不存在的路径，取消它，让apktool使用默认值
            java_home = env.get('JAVA_HOME')
            if java_home and not os.path.exists(java_home):
                logger.warning(f"检测到无效的JAVA_HOME: {java_home}，已临时取消")
                del env['JAVA_HOME']
            
            # 执行apktool编译命令
            result = subprocess.run([self.apktool_path, "b", decompiled_dir, "-o", output_apk], 
                                  capture_output=True, text=True, check=True, env=env)
            
            logger.info("APK重新编译完成")
            logger.debug(f"apktool输出: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"APK编译失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"编译过程中发生错误: {e}")
            return False
    
    def obfuscate_resources(self, decompiled_dir):
        """
        混淆资源文件
        :param decompiled_dir: 反编译目录
        :return: 混淆结果
        """
        try:
            logger.info(f"开始混淆资源文件: {decompiled_dir}")
            
            # 混淆assets目录下的文件（暂时跳过res目录混淆，避免资源引用问题）
            assets_dir = os.path.join(decompiled_dir, "assets")
            if os.path.exists(assets_dir):
                self._obfuscate_assets_dir(assets_dir)
            
            # 跳过res目录的资源混淆，因为会导致资源引用错误
            logger.info("跳过res目录资源混淆，避免资源引用问题")
            
            # 更新资源映射文件
            mapping_file = os.path.join(decompiled_dir, "resource_mapping.txt")
            with open(mapping_file, 'w') as f:
                for original, obfuscated in self.resource_mapping.items():
                    f.write(f"{original} -> {obfuscated}\n")
            
            logger.info(f"资源混淆完成，共混淆 {len(self.resource_mapping)} 个资源")
            return True
        except Exception as e:
            logger.error(f"资源混淆失败: {e}")
            return False
    
    def _obfuscate_res_dir(self, res_dir):
        """
        混淆res目录下的资源
        :param res_dir: res目录路径
        """
        # 遍历res目录下的所有子目录
        for root, dirs, files in os.walk(res_dir):
            for file in files:
                if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.xml', '.json', '.txt')):
                    original_path = os.path.join(root, file)
                    relative_path = os.path.relpath(original_path, res_dir)
                    
                    # 生成新名称
                    name, ext = os.path.splitext(file)
                    new_name = f"{self._generate_random_name()}{ext}"
                    new_path = os.path.join(root, new_name)
                    
                    # 重命名文件
                    os.rename(original_path, new_path)
                    
                    # 记录映射关系
                    self.resource_mapping[relative_path] = os.path.relpath(new_path, res_dir)
                    
                    logger.debug(f"资源重命名: {relative_path} -> {os.path.relpath(new_path, res_dir)}")
    
    def _obfuscate_assets_dir(self, assets_dir):
        """
        混淆assets目录下的资源
        :param assets_dir: assets目录路径
        """
        # 遍历assets目录下的所有文件
        for root, dirs, files in os.walk(assets_dir):
            for file in files:
                if not file.startswith('.'):
                    original_path = os.path.join(root, file)
                    relative_path = os.path.relpath(original_path, assets_dir)
                    
                    # 生成新名称
                    name, ext = os.path.splitext(file)
                    new_name = f"{self._generate_random_name()}{ext}"
                    new_path = os.path.join(root, new_name)
                    
                    # 重命名文件
                    os.rename(original_path, new_path)
                    
                    # 记录映射关系
                    self.resource_mapping[f"assets/{relative_path}"] = f"assets/{os.path.relpath(new_path, assets_dir)}"
                    
                    logger.debug(f"Assets重命名: assets/{relative_path} -> assets/{os.path.relpath(new_path, assets_dir)}")
    
    def remove_unused_resources(self, decompiled_dir):
        """
        移除未使用的资源
        基于文件引用分析，简单检测并移除未被引用的资源
        :param decompiled_dir: 反编译目录
        """
        try:
            logger.info("开始移除未使用的资源")
            
            # 1. 收集所有资源文件
            all_resources = set()
            res_dir = os.path.join(decompiled_dir, "res")
            
            if os.path.exists(res_dir):
                # 遍历res目录，收集所有资源文件
                for root, dirs, files in os.walk(res_dir):
                    for file in files:
                        if file.endswith((".png", ".jpg", ".jpeg", ".gif", ".xml", ".9.png")):
                            # 获取资源名称（不包含扩展名）
                            res_name = os.path.splitext(file)[0]
                            # 获取资源类型（如drawable, layout, values等）
                            res_type = os.path.basename(root)
                            # 添加到资源集合，格式：type/name
                            all_resources.add(f"{res_type}/{res_name}")
            
            logger.info(f"收集到 {len(all_resources)} 个资源文件")
            
            # 2. 扫描代码和配置文件，收集被引用的资源
            referenced_resources = set()
            
            # 扫描smali目录（如果存在）
            smali_dir = os.path.join(decompiled_dir, "smali")
            if os.path.exists(smali_dir):
                for root, dirs, files in os.walk(smali_dir):
                    for file in files:
                        if file.endswith(".smali"):
                            file_path = os.path.join(root, file)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # 查找资源引用，格式：Lcom/android/internal/R$type;->name:I
                                import re
                                matches = re.findall(r'Lcom/android/internal/R\$(\w+);->(\w+):I', content)
                                for res_type, res_name in matches:
                                    referenced_resources.add(f"{res_type}/{res_name}")
            
            # 扫描AndroidManifest.xml
            manifest_path = os.path.join(decompiled_dir, "AndroidManifest.xml")
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 查找资源引用，格式：@type/name
                    import re
                    matches = re.findall(r'@(\w+)/(\w+)', content)
                    for res_type, res_name in matches:
                        referenced_resources.add(f"{res_type}/{res_name}")
            
            # 扫描其他xml资源文件，查找资源引用
            if os.path.exists(res_dir):
                for root, dirs, files in os.walk(res_dir):
                    for file in files:
                        if file.endswith(".xml"):
                            file_path = os.path.join(root, file)
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # 查找资源引用，格式：@type/name 或 @android:type/name
                                import re
                                matches = re.findall(r'@(?:android:)?(\w+)/(\w+)', content)
                                for res_type, res_name in matches:
                                    referenced_resources.add(f"{res_type}/{res_name}")
            
            logger.info(f"检测到 {len(referenced_resources)} 个被引用的资源")
            
            # 3. 计算未被引用的资源
            unused_resources = all_resources - referenced_resources
            logger.info(f"发现 {len(unused_resources)} 个未被引用的资源")
            
            # 4. 移除未被引用的资源文件
            removed_count = 0
            for res in unused_resources:
                res_type, res_name = res.split("/")
                # 查找对应的资源文件
                res_type_dir = os.path.join(res_dir, res_type)
                if os.path.exists(res_type_dir):
                    for file in os.listdir(res_type_dir):
                        if file.startswith(res_name + "."):
                            file_path = os.path.join(res_type_dir, file)
                            try:
                                os.remove(file_path)
                                removed_count += 1
                                logger.debug(f"移除未使用资源: {file_path}")
                            except Exception as e:
                                logger.warning(f"移除资源失败: {file_path}, 错误: {e}")
            
            logger.info(f"成功移除 {removed_count} 个未使用的资源")
            return True
        except Exception as e:
            logger.error(f"移除未使用资源失败: {e}")
            return False
    
    def obfuscate_apk_resources(self, apk_path, output_path):
        """
        混淆APK资源文件
        :param apk_path: 原始APK路径
        :param output_path: 输出APK路径
        :return: 混淆结果
        """
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="jiagu_resource_")
        
        try:
            # 1. 反编译APK
            decompiled_dir = os.path.join(temp_dir, "decompiled")
            if not self.decompile_apk(apk_path, decompiled_dir):
                return False
            
            # 2. 混淆资源文件
            if not self.obfuscate_resources(decompiled_dir):
                return False
            
            # 3. 移除未使用资源（暂时禁用，避免误删重要资源）
            logger.info("暂时禁用移除未使用资源功能，避免误删重要资源")
            # self.remove_unused_resources(decompiled_dir)
            
            # 4. 重新编译APK
            if not self.compile_apk(decompiled_dir, output_path):
                return False
            
            logger.info(f"APK资源混淆完成: {output_path}")
            return True
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)

class ResourceProtection:
    """资源文件保护管理器"""
    
    def __init__(self):
        """初始化资源保护管理器"""
        self.obfuscator = ResourceObfuscator()
    
    def protect_apk_resources(self, apk_path, output_path):
        """
        保护APK资源文件
        :param apk_path: 原始APK路径
        :param output_path: 输出APK路径
        :return: 保护结果
        """
        try:
            logger.info(f"开始保护APK资源: {apk_path}")
            
            # 验证文件存在
            if not os.path.exists(apk_path):
                logger.error(f"APK文件不存在: {apk_path}")
                return {
                    'success': False,
                    'message': f"APK文件不存在: {apk_path}",
                    'error': f"APK文件不存在: {apk_path}"
                }
            
            # 检查apktool是否可用
            if self.obfuscator.apktool_path is None:
                logger.warning(f"apktool不可用，跳过资源混淆: {apk_path}")
                return {
                    'success': False,
                    'message': "apktool不可用，跳过资源混淆",
                    'error': "apktool not found"
                }
            
            # 执行资源混淆
            result = self.obfuscator.obfuscate_apk_resources(apk_path, output_path)
            
            if result:
                logger.info(f"APK资源保护完成: {output_path}")
                return {
                    'success': True,
                    'message': "APK资源保护成功",
                    'resource_count': len(self.obfuscator.resource_mapping)
                }
            else:
                return {
                    'success': False,
                    'message': "APK资源保护失败",
                    'error': "资源混淆执行失败"
                }
        except Exception as e:
            logger.error(f"APK资源保护失败: {e}")
            return {
                'success': False,
                'message': f"APK资源保护失败: {str(e)}",
                'error': str(e)
            }
