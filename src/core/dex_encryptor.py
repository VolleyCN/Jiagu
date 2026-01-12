#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEX文件加密保护模块
负责DEX文件的加密、加载器生成和替换
"""

import os
import tempfile
import shutil
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from loguru import logger

class DexEncryptor:
    """DEX文件加密器"""
    
    def __init__(self):
        """初始化DEX加密器"""
        self.encryption_key = None
        self.iv = None
    
    def generate_key(self):
        """
        生成加密密钥和IV
        """
        self.encryption_key = get_random_bytes(32)
        self.iv = get_random_bytes(16)
        logger.info("生成AES加密密钥和IV")
    
    def encrypt_dex(self, dex_data):
        """
        加密DEX文件数据
        :param dex_data: 原始DEX文件数据
        :return: 加密后的DEX数据
        """
        try:
            if self.encryption_key is None or self.iv is None:
                self.generate_key()
            
            logger.info("开始加密DEX文件，大小: " + str(len(dex_data)) + " bytes")
            
            pad_length = AES.block_size - (len(dex_data) % AES.block_size)
            padded_data = dex_data + bytes([pad_length] * pad_length)
            
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, self.iv)
            encrypted_data = cipher.encrypt(padded_data)
            
            logger.info("DEX文件加密完成，加密后大小: " + str(len(encrypted_data)) + " bytes")
            return encrypted_data
        except Exception as e:
            logger.error("DEX加密失败: " + str(e))
            raise
    
    def decrypt_dex(self, encrypted_data):
        """
        解密DEX文件数据（用于测试）
        :param encrypted_data: 加密后的DEX数据
        :return: 原始DEX数据
        """
        try:
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, self.iv)
            decrypted_padded = cipher.decrypt(encrypted_data)
            
            pad_length = decrypted_padded[-1]
            decrypted_data = decrypted_padded[:-pad_length]
            
            return decrypted_data
        except Exception as e:
            logger.error("DEX解密失败: " + str(e))
            raise
    
    def generate_loader_dex(self, original_dex_name):
        """
        生成DEX加载器代码
        :param original_dex_name: 原始DEX文件名
        :return: 加载器Java代码
        """
        try:
            logger.info("生成DEX加载器，原始DEX文件名: " + original_dex_name)
            
            key_hex = self.encryption_key.hex()
            iv_hex = self.iv.hex()
            
            # 使用简单的字符串，避免任何f-string问题
            loader_code = "package com.jiagu.loader;\n"
            loader_code += "import java.io.*;\n"
            loader_code += "import java.lang.reflect.*;\n"
            loader_code += "import java.util.*;\n"
            loader_code += "import javax.crypto.*;\n"
            loader_code += "import javax.crypto.spec.*;\n"
            loader_code += "import android.content.Context;\n"
            loader_code += "import android.content.res.AssetManager;\n"
            loader_code += "import android.app.ActivityThread;\n"
            loader_code += "\n"
            loader_code += "public class DexLoader {\n"
            loader_code += "    private static final String ORIGINAL_DEX = \"" + original_dex_name + "\";\n"
            loader_code += "    private static final String ENCRYPTION_KEY = \"" + key_hex + "\";\n"
            loader_code += "    private static final String IV = \"" + iv_hex + "\";\n"
            loader_code += "\n"
            loader_code += "    public static void load() {\n"
            loader_code += "        try {\n"
            loader_code += "            ClassLoader classLoader = DexLoader.class.getClassLoader();\n"
            loader_code += "            byte[] encryptedDex = readEncryptedDex();\n"
            loader_code += "            byte[] decryptedDex = decryptDex(encryptedDex);\n"
            loader_code += "            if (!verifyDexHeader(decryptedDex)) {\n"
            loader_code += "                throw new RuntimeException(\"Invalid DEX file header\");\n"
            loader_code += "            }\n"
            loader_code += "            loadDex(classLoader, decryptedDex);\n"
            loader_code += "        } catch (Exception e) {\n"
            loader_code += "            e.printStackTrace();\n"
            loader_code += "            throw new RuntimeException(\"Failed to load DEX\", e);\n"
            loader_code += "        }\n"
            loader_code += "    }\n"
            loader_code += "\n"
            loader_code += "    private static byte[] readEncryptedDex() throws IOException {\n"
            loader_code += "        // 从assets目录读取加密的DEX文件\n"
            loader_code += "        // 获取应用上下文\n"
            loader_code += "        Context context = getApplicationContext();\n"
            loader_code += "        // 获取AssetManager\n"
            loader_code += "        AssetManager assetManager = context.getAssets();\n"
            loader_code += "        // 打开assets中的加密DEX文件\n"
            loader_code += "        try (InputStream is = assetManager.open(ORIGINAL_DEX);\n"
            loader_code += "             ByteArrayOutputStream baos = new ByteArrayOutputStream()) {\n"
            loader_code += "            byte[] buffer = new byte[1024 * 4];\n"
            loader_code += "            int bytesRead;\n"
            loader_code += "            while ((bytesRead = is.read(buffer)) != -1) {\n"
            loader_code += "                baos.write(buffer, 0, bytesRead);\n"
            loader_code += "            }\n"
            loader_code += "            return baos.toByteArray();\n"
            loader_code += "        }\n"
            loader_code += "    }\n"
            loader_code += "\n"
            loader_code += "    // 获取应用上下文的辅助方法\n"
            loader_code += "    private static Context getApplicationContext() {\n"
            loader_code += "        try {\n"
            loader_code += "            Class<?> activityThreadClass = Class.forName(\"android.app.ActivityThread\");\n"
            loader_code += "            Method currentActivityThreadMethod = activityThreadClass.getDeclaredMethod(\"currentActivityThread\");\n"
            loader_code += "            Object currentActivityThread = currentActivityThreadMethod.invoke(null);\n"
            loader_code += "            Field applicationField = activityThreadClass.getDeclaredField(\"mInitialApplication\");\n"
            loader_code += "            applicationField.setAccessible(true);\n"
            loader_code += "            return (Context) applicationField.get(currentActivityThread);\n"
            loader_code += "        } catch (Exception e) {\n"
            loader_code += "            e.printStackTrace();\n"
            loader_code += "            throw new RuntimeException(\"Failed to get ApplicationContext\", e);\n"
            loader_code += "        }\n"
            loader_code += "    }\n"
            loader_code += "\n"
            loader_code += "    private static byte[] decryptDex(byte[] encryptedDex) throws Exception {\n"
            loader_code += "        byte[] keyBytes = hexStringToByteArray(ENCRYPTION_KEY);\n"
            loader_code += "        byte[] ivBytes = hexStringToByteArray(IV);\n"
            loader_code += "        SecretKeySpec keySpec = new SecretKeySpec(keyBytes, \"AES\");\n"
            loader_code += "        IvParameterSpec ivSpec = new IvParameterSpec(ivBytes);\n"
            loader_code += "        Cipher cipher = Cipher.getInstance(\"AES/CBC/PKCS5Padding\");\n"
            loader_code += "        cipher.init(Cipher.DECRYPT_MODE, keySpec, ivSpec);\n"
            loader_code += "        byte[] decryptedPadded = cipher.doFinal(encryptedDex);\n"
            loader_code += "        int padLength = decryptedPadded[decryptedPadded.length - 1];\n"
            loader_code += "        return Arrays.copyOf(decryptedPadded, decryptedPadded.length - padLength);\n"
            loader_code += "    }\n"
            loader_code += "\n"
            loader_code += "    private static boolean verifyDexHeader(byte[] dexData) {\n"
            loader_code += "        byte[] magic = Arrays.copyOfRange(dexData, 0, 8);\n"
            loader_code += "        String magicStr = new String(magic);\n"
            loader_code += "        return magicStr.equals(\"dex\\n035\\0\") || magicStr.equals(\"dex\\n036\\0\");\n"
            loader_code += "    }\n"
            loader_code += "\n"
            loader_code += "    /**\n"
            loader_code += "     * 绕过Android 9.0+的Hidden API限制\n"
            loader_code += "     */\n"
            loader_code += "    private static void bypassHiddenApiRestrictions() {\n"
            loader_code += "        try {\n"
            loader_code += "            // 获取当前Android版本\n"
            loader_code += "            int androidVersion = android.os.Build.VERSION.SDK_INT;\n"
            loader_code += "            if (androidVersion < 28) { // Android 9.0以下不需要绕过\n"
            loader_code += "                return;\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            // 尝试绕过Hidden API限制\n"
            loader_code += "            Class<?> vmRuntimeClass = Class.forName(\"dalvik.system.VMRuntime\");\n"
            loader_code += "            Method getRuntimeMethod = vmRuntimeClass.getDeclaredMethod(\"getRuntime\");\n"
            loader_code += "            getRuntimeMethod.setAccessible(true);\n"
            loader_code += "            Object vmRuntime = getRuntimeMethod.invoke(null);\n"
            loader_code += "            \n"
            loader_code += "            // 设置disableHiddenApiPolicy标志\n"
            loader_code += "            Method setHiddenApiExemptionsMethod = vmRuntimeClass.getDeclaredMethod(\"setHiddenApiExemptions\", String[].class);\n"
            loader_code += "            setHiddenApiExemptionsMethod.setAccessible(true);\n"
            loader_code += "            setHiddenApiExemptionsMethod.invoke(vmRuntime, new Object[]{new String[]{\"L\"}});\n"
            loader_code += "        } catch (Exception e) {\n"
            loader_code += "            // 绕过失败，继续执行，可能在某些设备上不支持\n"
            loader_code += "            e.printStackTrace();\n"
            loader_code += "        }\n"
            loader_code += "    }\n"
            loader_code += "    \n"
            loader_code += "    private static void loadDex(ClassLoader classLoader, byte[] dexData) throws Exception {\n"
            loader_code += "        if (classLoader == null) {\n"
            loader_code += "            throw new IllegalArgumentException(\"ClassLoader cannot be null\");\n"
            loader_code += "        }\n"
            loader_code += "        if (dexData == null || dexData.length < 8) {\n"
            loader_code += "            throw new IllegalArgumentException(\"Invalid DEX data: null or too short\");\n"
            loader_code += "        }\n"
            loader_code += "        \n"
            loader_code += "        // 绕过Hidden API限制（Android 9.0+）\n"
            loader_code += "        bypassHiddenApiRestrictions();\n"
            loader_code += "        \n"
            loader_code += "        // 获取当前Android版本\n"
            loader_code += "        int androidVersion = android.os.Build.VERSION.SDK_INT;\n"
            loader_code += "        \n"
            loader_code += "        // 根据Android版本选择不同的加载方式\n"
            loader_code += "        if (androidVersion >= 26) { // Android 8.0+ (Oreo)\n"
            loader_code += "            loadDexForOreoAndAbove(classLoader, dexData);\n"
            loader_code += "        } else if (androidVersion >= 21) { // Android 5.0-7.1 (Lollipop to Nougat)\n"
            loader_code += "            loadDexForLollipopToNougat(classLoader, dexData);\n"
            loader_code += "        } else {\n"
            loader_code += "            throw new UnsupportedOperationException(\"Unsupported Android version: \" + androidVersion + \", require Android 5.0+\");\n"
            loader_code += "        }\n"
            loader_code += "    }\n"            

            loader_code += "    /**\n"
            loader_code += "     * 获取应用的缓存目录，用于创建临时文件\n"
            loader_code += "     */\n"
            loader_code += "    private static File getAppCacheDir() {\n"
            loader_code += "        Context context = getApplicationContext();\n"
            loader_code += "        return context.getCacheDir();\n"
            loader_code += "    }\n"
            loader_code += "    \n"
            loader_code += "    /**\n"
            loader_code += "     * 为Android 8.0+版本加载DEX文件\n"
            loader_code += "     */\n"
            loader_code += "    private static void loadDexForOreoAndAbove(ClassLoader classLoader, byte[] dexData) throws Exception {\n"
            loader_code += "        try {\n"
            loader_code += "            // Android 8.0+ 的类加载器结构\n"
            loader_code += "            Class<?> baseDexClassLoaderClass = Class.forName(\"dalvik.system.BaseDexClassLoader\");\n"
            loader_code += "            Field pathListField = baseDexClassLoaderClass.getDeclaredField(\"pathList\");\n"
            loader_code += "            pathListField.setAccessible(true);\n"
            loader_code += "            Object pathList = pathListField.get(classLoader);\n"
            loader_code += "            \n"
            loader_code += "            Class<?> dexPathListClass = pathList.getClass();\n"
            loader_code += "            Field dexElementsField = dexPathListClass.getDeclaredField(\"dexElements\");\n"
            loader_code += "            dexElementsField.setAccessible(true);\n"
            loader_code += "            Object[] oldDexElements = (Object[]) dexElementsField.get(pathList);\n"
            loader_code += "            \n"
            loader_code += "            // 创建临时文件保存DEX数据（使用应用缓存目录，避免权限问题）\n"
            loader_code += "            File tempDir = getAppCacheDir();\n"
            loader_code += "            File tempDexFile = File.createTempFile(\"encrypted\", \".dex\", tempDir);\n"
            loader_code += "            tempDexFile.deleteOnExit();\n"
            loader_code += "            try (FileOutputStream fos = new FileOutputStream(tempDexFile)) {\n"
            loader_code += "                fos.write(dexData);\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            // 使用不同的方式创建DexFile\n"
            loader_code += "            Class<?> dexFileClass = Class.forName(\"dalvik.system.DexFile\");\n"
            loader_code += "            Object dexFile = null;\n"
            loader_code += "            \n"
            loader_code += "            // 尝试多种DexFile加载方式\n"
            loader_code += "            Exception lastException = null;\n"
            loader_code += "            \n"
            loader_code += "            // 方式1: 使用loadDex静态方法\n"
            loader_code += "            try {\n"
            loader_code += "                Method loadDexMethod = dexFileClass.getDeclaredMethod(\"loadDex\", String.class, String.class, int.class);\n"
            loader_code += "                loadDexMethod.setAccessible(true);\n"
            loader_code += "                dexFile = loadDexMethod.invoke(null, tempDexFile.getAbsolutePath(), null, 0);\n"
            loader_code += "            } catch (Exception e) {\n"
            loader_code += "                lastException = e;\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            // 方式2: 使用构造函数\n"
            loader_code += "            if (dexFile == null) {\n"
            loader_code += "                try {\n"
            loader_code += "                    Constructor<?>[] constructors = dexFileClass.getDeclaredConstructors();\n"
            loader_code += "                    for (Constructor<?> constructor : constructors) {\n"
            loader_code += "                        try {\n"
            loader_code += "                            constructor.setAccessible(true);\n"
            loader_code += "                            Class<?>[] paramTypes = constructor.getParameterTypes();\n"
            loader_code += "                            if (paramTypes.length == 2) {\n"
            loader_code += "                                // DexFile(File, String)\n"
            loader_code += "                                dexFile = constructor.newInstance(tempDexFile, tempDexFile.getAbsolutePath());\n"
            loader_code += "                                break;\n"
            loader_code += "                            } else if (paramTypes.length == 1) {\n"
            loader_code += "                                // DexFile(File)\n"
            loader_code += "                                dexFile = constructor.newInstance(tempDexFile);\n"
            loader_code += "                                break;\n"
            loader_code += "                            } else if (paramTypes.length == 4) {\n"
            loader_code += "                                // DexFile(File, String, File, DexFile)\n"
            loader_code += "                                dexFile = constructor.newInstance(tempDexFile, tempDexFile.getAbsolutePath(), tempDexFile, null);\n"
            loader_code += "                                break;\n"
            loader_code += "                            }\n"
            loader_code += "                        } catch (Exception e) {\n"
            loader_code += "                            // 尝试下一个构造函数\n"
            loader_code += "                            continue;\n"
            loader_code += "                        }\n"
            loader_code += "                    }\n"
            loader_code += "                } catch (Exception e) {\n"
            loader_code += "                    lastException = e;\n"
            loader_code += "                }\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            if (dexFile == null) {\n"
            loader_code += "                throw new RuntimeException(\"Failed to create DexFile\", lastException);\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            // 创建Element对象\n"
            loader_code += "            Class<?> elementClass = Class.forName(\"dalvik.system.DexPathList$Element\");\n"
            loader_code += "            Constructor<?>[] elementConstructors = elementClass.getDeclaredConstructors();\n"
            loader_code += "            Object newElement = null;\n"
            loader_code += "            \n"
            loader_code += "            for (Constructor<?> constructor : elementConstructors) {\n"
            loader_code += "                try {\n"
            loader_code += "                    constructor.setAccessible(true);\n"
            loader_code += "                    Class<?>[] paramTypes = constructor.getParameterTypes();\n"
            loader_code += "                    \n"
            loader_code += "                    // 根据构造函数参数类型选择合适的调用方式\n"
            loader_code += "                    if (paramTypes.length == 2) {\n"
            loader_code += "                        // Element(DexFile, File)\n"
            loader_code += "                        newElement = constructor.newInstance(dexFile, tempDexFile);\n"
            loader_code += "                        break;\n"
            loader_code += "                    } else if (paramTypes.length == 3) {\n"
            loader_code += "                        // Element(DexFile, File, boolean)\n"
            loader_code += "                        newElement = constructor.newInstance(dexFile, tempDexFile, false);\n"
            loader_code += "                        break;\n"
            loader_code += "                    } else if (paramTypes.length == 4) {\n"
            loader_code += "                        // Element(DexFile, File, File, DexFile)\n"
            loader_code += "                        newElement = constructor.newInstance(dexFile, tempDexFile, tempDexFile, null);\n"
            loader_code += "                        break;\n"
            loader_code += "                    }\n"
            loader_code += "                } catch (Exception e) {\n"
            loader_code += "                    // 尝试下一个构造函数\n"
            loader_code += "                    continue;\n"
            loader_code += "                }\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            if (newElement == null) {\n"
            loader_code += "                throw new RuntimeException(\"Failed to create Element\");\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            // 合并dexElements\n"
            loader_code += "            Object[] newDexElements = new Object[oldDexElements.length + 1];\n"
            loader_code += "            System.arraycopy(oldDexElements, 0, newDexElements, 0, oldDexElements.length);\n"
            loader_code += "            newDexElements[oldDexElements.length] = newElement;\n"
            loader_code += "            \n"
            loader_code += "            // 更新dexElements\n"
            loader_code += "            dexElementsField.set(pathList, newDexElements);\n"
            loader_code += "        } catch (Exception e) {\n"
            loader_code += "            throw new RuntimeException(\"Failed to load DEX for Android 8.0+\", e);\n"
            loader_code += "        }\n"
            loader_code += "    }\n"
            loader_code += "    \n"
            loader_code += "    /**\n"
            loader_code += "     * 为Android 5.0-7.1版本加载DEX文件\n"
            loader_code += "     */\n"
            loader_code += "    private static void loadDexForLollipopToNougat(ClassLoader classLoader, byte[] dexData) throws Exception {\n"
            loader_code += "        try {\n"
            loader_code += "            // Android 5.0-7.1 的类加载器结构\n"
            loader_code += "            Class<?> baseDexClassLoaderClass = Class.forName(\"dalvik.system.BaseDexClassLoader\");\n"
            loader_code += "            Field pathListField = baseDexClassLoaderClass.getDeclaredField(\"pathList\");\n"
            loader_code += "            pathListField.setAccessible(true);\n"
            loader_code += "            Object pathList = pathListField.get(classLoader);\n"
            loader_code += "            \n"
            loader_code += "            Class<?> dexPathListClass = pathList.getClass();\n"
            loader_code += "            Field dexElementsField = dexPathListClass.getDeclaredField(\"dexElements\");\n"
            loader_code += "            dexElementsField.setAccessible(true);\n"
            loader_code += "            Object[] oldDexElements = (Object[]) dexElementsField.get(pathList);\n"
            loader_code += "            \n"
            loader_code += "            // 创建临时文件（使用应用缓存目录，避免权限问题）\n"
            loader_code += "            File tempDir = getAppCacheDir();\n"
            loader_code += "            File tempDexFile = File.createTempFile(\"encrypted\", \".dex\", tempDir);\n"
            loader_code += "            tempDexFile.deleteOnExit();\n"
            loader_code += "            try (FileOutputStream fos = new FileOutputStream(tempDexFile)) {\n"
            loader_code += "                fos.write(dexData);\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            // 创建DexFile\n"
            loader_code += "            Class<?> dexFileClass = Class.forName(\"dalvik.system.DexFile\");\n"
            loader_code += "            Object dexFile = null;\n"
            loader_code += "            \n"
            loader_code += "            // 尝试多种DexFile加载方式\n"
            loader_code += "            try {\n"
            loader_code += "                Method loadDexMethod = dexFileClass.getDeclaredMethod(\"loadDex\", String.class, String.class, int.class);\n"
            loader_code += "                loadDexMethod.setAccessible(true);\n"
            loader_code += "                dexFile = loadDexMethod.invoke(null, tempDexFile.getAbsolutePath(), null, 0);\n"
            loader_code += "            } catch (Exception e) {\n"
            loader_code += "                // 尝试构造函数\n"
            loader_code += "                Constructor<?>[] constructors = dexFileClass.getDeclaredConstructors();\n"
            loader_code += "                for (Constructor<?> constructor : constructors) {\n"
            loader_code += "                    try {\n"
            loader_code += "                        constructor.setAccessible(true);\n"
            loader_code += "                        Class<?>[] paramTypes = constructor.getParameterTypes();\n"
            loader_code += "                        if (paramTypes.length == 2) {\n"
            loader_code += "                            dexFile = constructor.newInstance(tempDexFile, tempDexFile.getAbsolutePath());\n"
            loader_code += "                            break;\n"
            loader_code += "                        } else if (paramTypes.length == 1) {\n"
            loader_code += "                            dexFile = constructor.newInstance(tempDexFile);\n"
            loader_code += "                            break;\n"
            loader_code += "                        }\n"
            loader_code += "                    } catch (Exception ex) {\n"
            loader_code += "                        continue;\n"
            loader_code += "                    }\n"
            loader_code += "                }\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            if (dexFile == null) {\n"
            loader_code += "                throw new RuntimeException(\"Failed to create DexFile\");\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            // 创建Element\n"
            loader_code += "            Class<?> elementClass = Class.forName(\"dalvik.system.DexPathList$Element\");\n"
            loader_code += "            Object newElement = null;\n"
            loader_code += "            \n"
            loader_code += "            Constructor<?>[] elementConstructors = elementClass.getDeclaredConstructors();\n"
            loader_code += "            for (Constructor<?> constructor : elementConstructors) {\n"
            loader_code += "                try {\n"
            loader_code += "                    constructor.setAccessible(true);\n"
            loader_code += "                    Class<?>[] paramTypes = constructor.getParameterTypes();\n"
            loader_code += "                    if (paramTypes.length == 2) {\n"
            loader_code += "                        newElement = constructor.newInstance(dexFile, tempDexFile);\n"
            loader_code += "                        break;\n"
            loader_code += "                    }\n"
            loader_code += "                } catch (Exception e) {\n"
            loader_code += "                    continue;\n"
            loader_code += "                }\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            if (newElement == null) {\n"
            loader_code += "                throw new RuntimeException(\"Failed to create Element\");\n"
            loader_code += "            }\n"
            loader_code += "            \n"
            loader_code += "            // 合并dexElements\n"
            loader_code += "            Object[] newDexElements = new Object[oldDexElements.length + 1];\n"
            loader_code += "            System.arraycopy(oldDexElements, 0, newDexElements, 0, oldDexElements.length);\n"
            loader_code += "            newDexElements[oldDexElements.length] = newElement;\n"
            loader_code += "            \n"
            loader_code += "            // 更新dexElements\n"
            loader_code += "            dexElementsField.set(pathList, newDexElements);\n"
            loader_code += "        } catch (Exception e) {\n"
            loader_code += "            throw new RuntimeException(\"Failed to load DEX for Android 5.0-7.1\", e);\n"
            loader_code += "        }\n"
            loader_code += "    }\n"
            loader_code += "\n"
            loader_code += "    private static byte[] hexStringToByteArray(String s) {\n"
            loader_code += "        int len = s.length();\n"
            loader_code += "        byte[] data = new byte[len / 2];\n"
            loader_code += "        for (int i = 0; i < len; i += 2) {\n"
            loader_code += "            data[i / 2] = (byte) ((Character.digit(s.charAt(i), 16) << 4) + Character.digit(s.charAt(i+1), 16));\n"
            loader_code += "        }\n"
            loader_code += "        return data;\n"
            loader_code += "    }\n"
            loader_code += "}"
            
            return loader_code
        except Exception as e:
            logger.error("生成DEX加载器失败: " + str(e))
            raise
    
    def encrypt_apk_dex(self, apk_parser, output_dir):
        """
        加密APK中的所有DEX文件
        :param apk_parser: APKParser实例
        :param output_dir: 输出目录
        :return: 加密结果字典
        """
        try:
            logger.info("开始加密APK中的DEX文件: " + apk_parser.apk_path)
            
            os.makedirs(output_dir, exist_ok=True)
            
            results = {
                'original_dex_count': len(apk_parser.dex_files),
                'encrypted_dex_files': [],
                'loader_code': None
            }
            
            for dex_info in apk_parser.dex_files:
                self.generate_key()
                
                encrypted_data = self.encrypt_dex(dex_info['data'])
                
                if results['loader_code'] is None:
                    results['loader_code'] = self.generate_loader_dex(dex_info['name'])
                
                encrypted_dex_path = os.path.join(output_dir, "encrypted_" + dex_info['name'])
                with open(encrypted_dex_path, 'wb') as f:
                    f.write(encrypted_data)
                
                results['encrypted_dex_files'].append({
                    'original_name': dex_info['name'],
                    'encrypted_path': encrypted_dex_path,
                    'key': self.encryption_key.hex(),
                    'iv': self.iv.hex()
                })
                
                logger.info("加密完成: " + dex_info['name'] + " -> " + encrypted_dex_path)
            
            logger.info("所有DEX文件加密完成，共 " + str(len(results['encrypted_dex_files'])) + " 个")
            return results
        except Exception as e:
            logger.error("加密APK DEX失败: " + str(e))
            raise

class DexProtection:
    """DEX文件保护管理器"""
    
    def __init__(self):
        """初始化DEX保护管理器"""
        self.encryptor = DexEncryptor()
    
    def protect_apk(self, apk_path, output_path):
        """
        保护APK中的DEX文件
        :param apk_path: 原始APK路径
        :param output_path: 输出APK路径
        :return: 保护结果
        """
        from src.core.apk_parser import APKParser
        
        try:
            logger.info("开始保护APK: " + apk_path)
            
            parser = APKParser(apk_path)
            if not parser.parse():
                raise Exception("APK解析失败")
            
            temp_dir = tempfile.mkdtemp(prefix="jiagu_")
            
            try:
                encrypt_results = self.encryptor.encrypt_apk_dex(parser, temp_dir)
                
                logger.info("APK保护完成: " + output_path)
                return {
                    'success': True,
                    'message': "APK保护成功，加密了 " + str(encrypt_results['original_dex_count']) + " 个DEX文件",
                    'details': encrypt_results
                }
            finally:
                shutil.rmtree(temp_dir)
                parser.close()
        except Exception as e:
            logger.error("APK保护失败: " + str(e))
            return {
                'success': False,
                'message': "APK保护失败: " + str(e),
                'details': None
            }
