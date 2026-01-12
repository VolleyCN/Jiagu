# APK加固工具

一款功能全面的Android APK加固工具，基于Python开发，支持DEX加密、资源混淆、反保护机制和多渠道打包等功能。

## 功能特性

### 核心加固功能
- **DEX加密**：对APK中的DEX文件进行加密，防止反编译
- **资源混淆**：混淆APK中的资源文件名和内容，增加逆向难度
- **签名管理**：支持自定义签名配置，自动为加固后的APK重新签名

### 反保护机制
- **防调试**：检测并阻止调试器附加
- **反Root**：检测设备是否Root，对Root设备进行保护
- **反模拟器**：检测运行环境是否为模拟器，对模拟器环境进行保护

### 多渠道打包
- 基于纯Python实现的walle渠道注入器
- 支持通过配置文件批量生成渠道包
- 与官方walle工具完全兼容
- 支持双引擎机制（优先使用官方walle工具，失败时自动降级到纯Python实现）

### 报告生成
- 生成详细的加固报告，包含加固结果和统计信息
- 支持HTML、JSON和TXT三种格式
- 报告自动保存到log目录

## 依赖环境

### 基础依赖
- **Python 3.8+**：项目主要开发语言
- **Java 8+**：用于运行walle-cli-all.jar（可选，纯Python实现不需要）

### Python依赖库
项目依赖的Python库列在`requirements.txt`文件中，主要包括：
- loguru：日志管理
- PyQt5：GUI界面（可选）
- yaml：配置文件解析

### 外部工具（可选）
- **walle-cli-all.jar**：官方walle工具，位于`lib/`目录下
- **CheckAndroidV2Signature.jar**：用于检查APK v2签名

## 安装和使用

### 环境准备
1. 确保安装了Python 3.8+环境
2. 安装依赖库：
   ```bash
   pip install -r requirements.txt
   ```
3. 确保Java环境可用（如果需要使用官方walle工具）

### 基本使用

#### 命令行方式
```bash
# 基本加固命令
python main.py --input <input_apk> --output <output_dir> [options]

# 示例
python main.py --input test.apk --output output_dir --dex_encrypt --resource_obfuscate --anti_debug
```

#### 配置文件方式
1. 准备渠道配置文件（如`config/channel_config.yaml`）
2. 运行加固工具：
   ```bash
   python main.py --input test.apk --output output_dir --config config/channel_config.yaml
   ```

#### GUI方式
```bash
python main.py --gui
```

## 项目结构

```
Jiagu/
├── config/              # 配置文件目录
│   ├── channel_config.yaml      # 完整渠道配置示例
│   └── simple_channel_config.yaml # 简单渠道配置示例
├── docs/                # 文档目录
├── lib/                 # 外部依赖库
│   ├── walle-cli-all.jar        # 官方walle工具
│   └── CheckAndroidV2Signature.jar # APK v2签名检查工具
├── log/                 # 日志和报告目录
├── src/                 # 源代码目录
│   ├── core/            # 核心功能模块
│   │   ├── anti_protection.py    # 反保护机制实现
│   │   ├── apk_parser.py         # APK解析工具
│   │   ├── channel_manager.py    # 渠道配置管理
│   │   ├── channel_packer.py     # 多渠道打包实现
│   │   ├── config_manager.py     # 配置管理
│   │   ├── dex_encryptor.py      # DEX加密实现
│   │   ├── resource_obfuscator.py # 资源混淆实现
│   │   ├── signature_manager.py  # 签名管理
│   │   └── walle_python_impl.py  # 纯Python实现的walle渠道注入器
│   ├── ui/               # GUI界面模块
│   │   └── main_window.py        # 主窗口实现
│   └── jiagu_app.py      # 应用程序入口
├── test_src/            # 测试代码目录
├── analyze_apk.py       # APK分析工具
├── main.py              # 命令行入口
├── requirements.txt      # Python依赖库
└── validate_apks.py     # APK验证工具
```

## 核心模块说明

### walle_python_impl.py
纯Python实现的walle渠道注入器，支持以下功能：
- 查找和解析APK Signing Block
- 向APK Signing Block中注入渠道信息
- 从APK中读取渠道信息
- 与官方walle工具完全兼容

### channel_packer.py
多渠道包管理器，支持：
- 双引擎机制（官方walle工具 + 纯Python实现）
- 通过配置文件批量生成渠道包
- 支持自定义渠道标识（CHANNEL_ID）
- 自动处理渠道包命名和输出

### anti_protection.py
反保护机制实现，支持：
- 防调试检测
- 反Root检测
- 反模拟器检测

## 配置文件说明

### 渠道配置文件（YAML格式）
```yaml
# 渠道配置示例
output:
  directory: channels    # 渠道包输出目录
  overwrite: true        # 是否覆盖已存在的渠道包

# 渠道列表
channels:
  - name: google_play
    metadata:
      CHANNEL_ID: zhima-android-google_play
      MARKET_NAME: Google Play
  - name: huawei
    metadata:
      CHANNEL_ID: zhima-android-huawei
      MARKET_NAME: Huawei AppGallery
  # 更多渠道...
```

## 日志和报告

- 日志文件：`log/jiagu.log`
- 加固报告：`log/jiagu_report_<timestamp>.<format>`（支持html、json、txt格式）

## 常见问题和解决方案

### 1. 多渠道打包失败
**可能原因**：
- 官方walle工具不可用或版本不兼容
- APK没有APK v2签名
- 渠道配置文件格式错误

**解决方案**：
- 确保Java环境可用
- 确保APK已使用APK v2签名
- 检查渠道配置文件格式是否正确

### 2. 加固后的APK无法安装
**可能原因**：
- 签名配置错误
- DEX加密过程中出现问题
- 资源混淆导致资源引用错误

**解决方案**：
- 检查签名配置是否正确
- 查看log目录下的日志文件，定位具体错误
- 尝试关闭部分加固功能，逐步排查

### 3. 渠道信息无法读取
**可能原因**：
- APK没有APK v2签名
- 渠道注入过程中出现问题
- 读取渠道的方式不正确

**解决方案**：
- 确保APK已使用APK v2签名
- 使用官方walle工具验证渠道注入是否成功
- 检查读取渠道的代码是否正确

## 贡献指南

1. Fork本仓库
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 提交Pull Request

## 许可证

本项目采用Apache License 2.0许可证，详见LICENSE文件。

## 致谢

- 感谢美团Walle项目提供的渠道注入原理
- 感谢所有为项目做出贡献的开发者

## 联系方式

如有问题或建议，欢迎通过以下方式联系：
- GitHub Issues：https://github.com/VolleyCN/Jiagu/issues
- Email：您的邮箱地址

---

**注意**：本工具仅用于学习和研究目的，请勿用于非法用途。使用本工具加固的APK，开发者需自行承担相关法律责任。