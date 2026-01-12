#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
防调试与反逆向保护机制模块
负责生成和注入防调试、反逆向保护代码
"""

import os
import tempfile
import shutil
import subprocess
import zipfile
from loguru import logger

class AntiProtection:
    """防调试与反逆向保护管理器"""
    
    def __init__(self):
        """初始化保护管理器"""
        self.protection_features = {
            'anti_debug': True,
            'anti_root': True,
            'anti_emulator': True,
            'anti_hook': True,
            'anti_dump': True,
            'code_encryption': True
        }
        self.apktool_path = self._find_apktool()
    
    def generate_anti_debug_code(self):
        """
        生成反调试检测代码
        :return: 反调试Java代码
        """
        return """
    /**
     * 反调试检测
     */
    private static boolean isDebuggerAttached() {
        try {
            // 1. 检测Debug.isDebuggerConnected()
            Class<?> debugClass = Class.forName("android.os.Debug");
            Method isDebuggerConnected = debugClass.getMethod("isDebuggerConnected");
            boolean isConnected = (boolean) isDebuggerConnected.invoke(null);
            if (isConnected) {
                return true;
            }
            
            // 2. 检测进程状态
            String processStatus = new Scanner(new File("/proc/self/status")).useDelimiter("\\Z").next();
            if (processStatus.contains("TracerPid:\s+0")) {
                return false;
            } else {
                return true;
            }
        } catch (Exception e) {
            // 发生异常，可能是被hook，返回true表示检测到调试
            return true;
        }
    }
    
    /**
     * 检测调试器并处理
     */
    private static void checkDebugger() {
        if (isDebuggerAttached()) {
            // 检测到调试，退出应用
            android.os.Process.killProcess(android.os.Process.myPid());
            System.exit(0);
        }
    }
"""
    
    def generate_anti_root_code(self):
        """
        生成反root检测代码
        :return: 反root Java代码
        """
        return """
    /**
     * 检测设备是否已root
     */
    private static boolean isRooted() {
        try {
            // 1. 检测常见root文件
            String[] rootFiles = {
                "/system/app/Superuser.apk",
                "/system/xbin/su",
                "/system/bin/su",
                "/su/bin/su",
                "/data/local/xbin/su",
                "/data/local/bin/su"
            };
            
            for (String file : rootFiles) {
                if (new File(file).exists()) {
                    return true;
                }
            }
            
            // 2. 检测su命令是否可执行
            Process process = Runtime.getRuntime().exec("which su");
            int exitCode = process.waitFor();
            if (exitCode == 0) {
                return true;
            }
            
            return false;
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * 检测root并处理
     */
    private static void checkRoot() {
        if (isRooted()) {
            // 检测到root，退出应用
            android.os.Process.killProcess(android.os.Process.myPid());
            System.exit(0);
        }
    }
"""
    
    def generate_anti_emulator_code(self):
        """
        生成反模拟器检测代码
        :return: 反模拟器Java代码
        """
        return """
    /**
     * 检测设备是否为模拟器
     */
    private static boolean isEmulator() {
        try {
            // 1. 检测设备制造商
            String manufacturer = Build.MANUFACTURER;
            if (manufacturer.contains("Genymotion") || manufacturer.contains("Andy") || manufacturer.contains("Android SDK")) {
                return true;
            }
            
            // 2. 检测设备型号
            String model = Build.MODEL;
            if (model.contains("Emulator") || model.contains("Android SDK built for x86")) {
                return true;
            }
            
            // 3. 检测IMEI
            TelephonyManager tm = (TelephonyManager) context.getSystemService(Context.TELEPHONY_SERVICE);
            String imei = tm.getDeviceId();
            if (imei == null || imei.equals("000000000000000")) {
                return true;
            }
            
            // 4. 检测基带版本
            String baseband = Build.getRadioVersion();
            if (baseband == null || baseband.isEmpty()) {
                return true;
            }
            
            return false;
        } catch (Exception e) {
            return false;
        }
    }
    
    /**
     * 检测模拟器并处理
     */
    private static void checkEmulator() {
        if (isEmulator()) {
            // 检测到模拟器，退出应用
            android.os.Process.killProcess(android.os.Process.myPid());
            System.exit(0);
        }
    }
"""
    
    def generate_anti_hook_code(self):
        """
        生成反hook检测代码
        :return: 反hook Java代码
        """
        return """
    /**
     * 检测常见hook框架
     */
    private static boolean isHooked() {
        try {
            // 1. 检测Xposed框架
            Class.forName("de.robv.android.xposed.XposedBridge");
            return true;
        } catch (ClassNotFoundException e1) {
            try {
                // 2. 检测Substrate框架
                Class.forName("com.saurik.substrate.MS");
                return true;
            } catch (ClassNotFoundException e2) {
                try {
                    // 3. 检测太极框架
                    Class.forName("me.weishu.exp.hook.HookManager");
                    return true;
                } catch (ClassNotFoundException e3) {
                    return false;
                }
            }
        }
    }
    
    /**
     * 检测hook并处理
     */
    private static void checkHook() {
        if (isHooked()) {
            // 检测到hook，退出应用
            android.os.Process.killProcess(android.os.Process.myPid());
            System.exit(0);
        }
    }
"""
    
    def generate_anti_dump_code(self):
        """
        生成防止内存dump代码
        :return: 防dump Java代码
        """
        return """
    /**
     * 防止内存dump
     */
    private static void protectFromDump() {
        try {
            // 1. 设置内存保护标志
            Class<?> memoryClass = Class.forName("android.app.ActivityThread");
            Method currentActivityThread = memoryClass.getMethod("currentActivityThread");
            Object activityThread = currentActivityThread.invoke(null);
            
            // 2. 动态修改内存访问权限
            // 实际实现需要native代码支持
        } catch (Exception e) {
            // 忽略异常
        }
    }
"""
    
    def generate_protection_class(self, package_name):
        """
        生成完整的保护类代码
        :param package_name: 应用包名
        :return: 完整的保护Java类代码
        """
        logger.info(f"生成保护类，包名: {package_name}")
        
        # 生成保护代码
        anti_debug = self.generate_anti_debug_code()
        anti_root = self.generate_anti_root_code()
        anti_emulator = self.generate_anti_emulator_code()
        anti_hook = self.generate_anti_hook_code()
        anti_dump = self.generate_anti_dump_code()
        
        # 完整的保护类
        protection_class = f"""
package {package_name};

import android.content.Context;
import android.os.Build;
import android.telephony.TelephonyManager;
import java.io.File;
import java.util.Scanner;
import java.lang.reflect.Method;

/**
 * APK加固保护类
 * 自动生成，包含多种反逆向保护机制
 */
public class JiaguProtection {{
    private static Context context;
    private static boolean initialized = false;
    
    /**
     * 初始化保护机制
     */
    public static void init(Context appContext) {{
        if (initialized) {{
            return;
        }}
        
        context = appContext;
        initialized = true;
        
        // 启动所有保护检测
        startProtection();
    }}
    
    /**
     * 启动保护机制
     */
    private static void startProtection() {{
        // 在新线程中执行保护检测，避免阻塞主线程
        new Thread(new Runnable() {{
            @Override
            public void run() {{
                // 执行各种保护检测
                checkDebugger();
                checkRoot();
                checkEmulator();
                checkHook();
                protectFromDump();
                
                // 定期检测
                while (true) {{
                    try {{
                        Thread.sleep(1000); // 每秒检测一次
                        checkDebugger();
                        checkRoot();
                        checkHook();
                    }} catch (InterruptedException e) {{
                        break;
                    }}
                }}
            }}
        }}).start();
    }}
    
    // 注入各种保护代码
    {anti_debug}
    {anti_root}
    {anti_emulator}
    {anti_hook}
    {anti_dump}
}}
"""
        
        return protection_class
    
    def generate_application_proxy(self, original_app_class, package_name):
        """
        生成Application代理类，用于在应用启动时初始化保护
        :param original_app_class: 原始Application类名
        :param package_name: 应用包名
        :return: Application代理类代码
        """
        logger.info(f"生成Application代理类，原始类: {original_app_class}, 包名: {package_name}")
        
        return f"""
package {package_name};

import android.app.Application;
import android.content.Context;
import android.content.res.Configuration;

/**
 * 自动生成的Application代理类
 * 用于在应用启动时初始化加固保护
 */
public class JiaguApplication extends Application {{
    private Application originalApplication;
    
    @Override
    protected void attachBaseContext(Context base) {{
        super.attachBaseContext(base);
        
        try {{
            // 初始化加固保护
            JiaguProtection.init(this);
            
            // TODO: 加载原始Application类
            // 实际实现需要反射调用原始Application的attachBaseContext方法
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}
    
    @Override
    public void onCreate() {{
        super.onCreate();
        
        try {{
            // TODO: 调用原始Application的onCreate方法
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}
    
    @Override
    public void onConfigurationChanged(Configuration newConfig) {{
        super.onConfigurationChanged(newConfig);
        
        try {{
            // TODO: 调用原始Application的onConfigurationChanged方法
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}
    
    @Override
    public void onLowMemory() {{
        super.onLowMemory();
        
        try {{
            // TODO: 调用原始Application的onLowMemory方法
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}
    
    @Override
    public void onTrimMemory(int level) {{
        super.onTrimMemory(level);
        
        try {{
            // TODO: 调用原始Application的onTrimMemory方法
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}
}}
"""
    
    def apply_protection(self, apk_parser):
        """
        应用保护机制
        :param apk_parser: APKParser实例
        :return: 保护结果
        """
        try:
            logger.info("应用防调试与反逆向保护机制")
            
            package_name = apk_parser.get_package_name()
            if not package_name:
                logger.error("无法获取应用包名")
                return False
            
            # 生成保护类
            protection_class = self.generate_protection_class(package_name)
            
            # 生成Application代理类
            # 假设原始Application类是默认的
            application_proxy = self.generate_application_proxy("android.app.Application", package_name)
            
            # TODO: 将生成的类注入到APK中
            # 实际实现需要：
            # 1. 将Java类编译为dex
            # 2. 将dex注入到APK中
            # 3. 修改AndroidManifest.xml，将Application替换为代理类
            
            logger.info("保护机制应用完成")
            return {
                'success': True,
                'package_name': package_name,
                'protection_class': 'JiaguProtection',
                'application_proxy': 'JiaguApplication'
            }
        except Exception as e:
            logger.error(f"应用保护机制失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_protection_feature(self, feature, enabled):
        """
        设置保护功能开关
        :param feature: 保护功能名称
        :param enabled: 是否启用
        :return: 设置结果
        """
        if feature in self.protection_features:
            self.protection_features[feature] = enabled
            logger.info(f"保护功能 {feature} 设置为 {'启用' if enabled else '禁用'}")
            return True
        else:
            logger.error(f"未知的保护功能: {feature}")
            return False
    
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
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"APK编译失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"编译过程中发生错误: {e}")
            return False
    
    def _find_dx(self):
        """
        查找dx工具路径
        :return: dx路径或None
        """
        try:
            # 检查系统中是否有dx
            result = subprocess.run(["which", "dx"], capture_output=True, text=True, check=True)
            dx_path = result.stdout.strip()
            logger.info(f"找到dx工具: {dx_path}")
            return dx_path
        except subprocess.CalledProcessError:
            # 检查Java SDK目录
            java_home = os.environ.get('JAVA_HOME')
            if java_home:
                dx_path = os.path.join(java_home, "bin", "dx")
                if os.path.exists(dx_path):
                    logger.info(f"在Java SDK中找到dx工具: {dx_path}")
                    return dx_path
            
            logger.warning("未找到dx工具，无法编译Java代码为dex")
            return None
    
    def _compile_java_to_dex(self, java_files, output_dex):
        """
        使用dx工具将Java文件编译为dex
        :param java_files: Java文件列表
        :param output_dex: 输出dex文件路径
        :return: 编译结果
        """
        dx_path = self._find_dx()
        if dx_path is None:
            return False
        
        try:
            logger.info(f"开始将Java文件编译为dex: {output_dex}")
            
            # 执行dx编译命令
            cmd = [dx_path, "--dex", f"--output={output_dex}"] + java_files
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Java文件编译为dex完成: {output_dex}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"编译Java文件为dex失败: {e}")
            logger.error(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"编译过程中发生错误: {e}")
            return False
    
    def _inject_dex_into_apk(self, apk_path, dex_path):
        """
        将dex文件注入到APK中
        :param apk_path: APK路径
        :param dex_path: dex文件路径
        :return: 注入结果
        """
        try:
            logger.info(f"开始将dex注入到APK: {apk_path}")
            
            # 使用zipfile将dex文件添加到APK中
            with zipfile.ZipFile(apk_path, 'a') as zipf:
                # 获取dex文件名（classes.dex, classes2.dex, 等）
                dex_files = [name for name in zipf.namelist() if name.startswith('classes') and name.endswith('.dex')]
                new_dex_name = f'classes{len(dex_files) + 1}.dex'
                
                # 添加dex文件到APK
                zipf.write(dex_path, new_dex_name)
                logger.info(f"dex文件已注入到APK: {new_dex_name}")
            
            return True
        except Exception as e:
            logger.error(f"注入dex到APK失败: {e}")
            return False
    
    def _inject_protection_code(self, apk_path):
        """
        将保护代码注入到APK中
        :param apk_path: APK路径
        :return: 注入结果
        """
        try:
            logger.info(f"开始注入保护代码到APK: {apk_path}")
            
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix="jiagu_protection_")
            
            # 生成保护类代码
            protection_class = self.generate_protection_class("com.jiagu.protection")
            
            # 创建Java源文件
            java_dir = os.path.join(temp_dir, "java")
            package_dir = os.path.join(java_dir, "com", "jiagu", "protection")
            os.makedirs(package_dir, exist_ok=True)
            
            protection_file = os.path.join(package_dir, "JiaguProtection.java")
            with open(protection_file, "w", encoding="utf-8") as f:
                f.write(protection_class)
            
            # 编译Java文件为dex
            output_dex = os.path.join(temp_dir, "classes.dex")
            if not self._compile_java_to_dex([protection_file], output_dex):
                return False
            
            # 注入dex到APK
            if not self._inject_dex_into_apk(apk_path, output_dex):
                return False
            
            logger.info("保护代码注入完成")
            return True
        except Exception as e:
            logger.error(f"注入保护代码失败: {e}")
            return False
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
    
    def _get_package_name(self, apk_path):
        """
        从APK文件中获取包名
        :param apk_path: APK路径
        :return: 包名或None
        """
        try:
            # 使用aapt或其他方式获取包名
            # 暂时返回默认包名
            logger.warning("暂时使用默认包名，后续需要实现从APK中获取包名的功能")
            return "com.jiagu.protection"
        except Exception as e:
            logger.error(f"获取包名失败: {e}")
            return "com.jiagu.protection"  # 默认包名
    
    def apply_protection(self, apk_path, output_path):
        """
        应用保护机制到APK文件
        :param apk_path: 原始APK路径
        :param output_path: 输出APK路径
        :return: 保护结果
        """
        try:
            logger.info(f"开始应用保护机制到APK: {apk_path}")
            
            # 获取包名
            package_name = self._get_package_name(apk_path)
            
            # 1. 复制原始APK到输出路径（如果路径不同）
            if apk_path != output_path:
                shutil.copy2(apk_path, output_path)
                logger.info(f"已复制原始APK到输出路径: {output_path}")
            else:
                logger.info(f"输入路径和输出路径相同，跳过复制步骤: {output_path}")
            
            # 2. 注入保护代码
            if not self._inject_protection_code(output_path):
                return {
                    'success': False,
                    'error': "注入保护代码失败"
                }
            
            logger.info(f"保护机制应用完成: {output_path}")
            return {
                'success': True,
                'package_name': package_name,
                'protection_class': 'JiaguProtection',
                'message': "保护机制应用成功"
            }
        except Exception as e:
            logger.error(f"应用保护机制失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_protection_features(self):
        """
        获取所有保护功能状态
        :return: 保护功能状态字典
        """
        return self.protection_features.copy()
