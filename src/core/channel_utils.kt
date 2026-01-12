package com.example.channel

import android.content.Context
import android.util.Log
import java.io.BufferedReader
import java.io.IOException
import java.io.InputStreamReader
import java.util.HashMap
import java.util.zip.ZipEntry
import java.util.zip.ZipFile

/**
 * 渠道工具类 - 用于获取当前应用的渠道信息
 * 基于美团Walle打包原理，从APK的META-INF目录下的channel_*.txt文件中读取渠道信息
 */
object ChannelUtils {
    private const val TAG = "ChannelUtils"
    private const val DEFAULT_CHANNEL = "default"
    private const val DEFAULT_MARKET_NAME = "Default Market"
    private const val CHANNEL_DIR_PREFIX = "META-INF/channel_"
    private const val CHANNEL_FILE_SUFFIX = ".txt"
    
    // 缓存渠道信息，避免重复读取
    private var channelInfo: HashMap<String, String>? = null
    
    /**
     * 获取渠道ID
     * @param context 上下文
     * @return 渠道ID，默认为"default"
     */
    @JvmStatic
    fun getChannelId(context: Context): String {
        val info = getChannelInfo(context)
        return info["CHANNEL_ID"] ?: DEFAULT_CHANNEL
    }
    
    /**
     * 获取市场名称
     * @param context 上下文
     * @return 市场名称，默认为"Default Market"
     */
    @JvmStatic
    fun getMarketName(context: Context): String {
        val info = getChannelInfo(context)
        return info["MARKET_NAME"] ?: DEFAULT_MARKET_NAME
    }
    
    /**
     * 获取完整的渠道信息
     * @param context 上下文
     * @return 渠道信息键值对
     */
    @JvmStatic
    fun getChannelInfo(context: Context): Map<String, String> {
        // 如果已经缓存了渠道信息，直接返回
        channelInfo?.let { return it }
        
        try {
            // 获取APK路径
            val apkPath = context.applicationInfo.sourceDir
            
            // 从APK中读取渠道文件
            val channelInfoMap = readChannelInfoFromApk(apkPath)
            
            // 如果成功读取到渠道信息，缓存并返回
            if (channelInfoMap.isNotEmpty()) {
                channelInfo = channelInfoMap as HashMap<String, String>
                return channelInfoMap
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get channel info: ${e.message}")
        }
        
        // 所有方式都失败时返回默认渠道信息
        val defaultInfo = hashMapOf(
            "CHANNEL_ID" to DEFAULT_CHANNEL,
            "MARKET_NAME" to DEFAULT_MARKET_NAME
        )
        channelInfo = defaultInfo
        return defaultInfo
    }
    
    /**
     * 从APK文件中读取渠道信息
     * @param apkPath APK文件路径
     * @return 渠道信息键值对，空表示读取失败
     */
    private fun readChannelInfoFromApk(apkPath: String): Map<String, String> {
        var zipFile: ZipFile? = null
        var reader: BufferedReader? = null
        
        try {
            // 打开APK文件
            zipFile = ZipFile(apkPath)
            
            // 遍历所有条目，查找渠道文件
            val entries = zipFile.entries()
            while (entries.hasMoreElements()) {
                val entry = entries.nextElement()
                val entryName = entry.name
                
                // 查找META-INF目录下以channel_开头的.txt文件
                if (entryName.startsWith(CHANNEL_DIR_PREFIX) && entryName.endsWith(CHANNEL_FILE_SUFFIX)) {
                    // 读取渠道文件内容
                    val inputStream = zipFile.getInputStream(entry)
                    reader = BufferedReader(InputStreamReader(inputStream, "UTF-8"))
                    
                    // 解析渠道信息
                    val channelInfoMap = HashMap<String, String>()
                    var line: String?
                    while (reader.readLine().also { line = it } != null) {
                        line?.let { 
                            val parts = it.split("=", limit = 2)
                            if (parts.size == 2) {
                                val key = parts[0].trim()
                                val value = parts[1].trim()
                                channelInfoMap[key] = value
                            }
                        }
                    }
                    
                    return channelInfoMap
                }
            }
            
            Log.w(TAG, "No channel file found in APK")
            return emptyMap()
        } catch (e: IOException) {
            Log.e(TAG, "Failed to read channel info from APK: ${e.message}")
            return emptyMap()
        } finally {
            // 关闭资源
            try {
                reader?.close()
            } catch (e: IOException) {
                // 忽略关闭异常
            }
            
            try {
                zipFile?.close()
            } catch (e: IOException) {
                // 忽略关闭异常
            }
        }
    }
    
    /**
     * 清除渠道缓存
     * 用于测试或动态切换渠道的场景
     */
    @JvmStatic
    fun clearChannelCache() {
        channelInfo = null
    }
}