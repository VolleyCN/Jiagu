# 生成Mac安装包方案

## 1. 方案概述
使用`py2app`工具将APK加固工具打包为Mac平台的安装包，包括.app应用程序和DMG安装镜像，包含所有依赖项和资源文件。

## 2. 实现步骤

### 步骤1: 安装py2app
```bash
pip install py2app
```

### 步骤2: 创建setup.py配置文件
在项目根目录创建`setup.py`文件，配置打包选项：
```python
from setuptools import setup

APP = ['main.py']
DATA_FILES = [
    ('lib', ['lib/walle-cli-all.jar', 'lib/CheckAndroidV2Signature.jar']),
    ('config', ['config/channel_config.yaml', 'config/simple_channel_config.yaml']),
    ('META-INF', ['META-INF/MANIFEST.MF'])
]
OPTIONS = {
    'packages': ['src', 'loguru', 'PyQt5', 'pycryptodome', 'androguard', 'yaml'],
    'includes': ['src.core', 'src.ui', 'src.jiagu_app'],
    'plist': {
        'CFBundleName': 'APK加固工具',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'CFBundleIdentifier': 'com.example.jiagu',
        'NSHighResolutionCapable': True,
    },
    'iconfile': 'icon.icns',  # 如果有图标文件
    'resources': ['README.md', 'requirements.txt'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

### 步骤3: 执行打包命令
```bash
# 开发模式（快速测试）
python setup.py py2app -A

# 正式打包
python setup.py py2app
```

### 步骤4: 验证生成的应用
```bash
# 运行生成的应用
open dist/APK加固工具.app
```

### 步骤5: 创建DMG安装包
使用`create-dmg`工具创建DMG安装包：
```bash
# 安装create-dmg
brew install create-dmg

# 创建DMG
create-dmg --volname "APK加固工具" --window-pos 200 120 --window-size 600 300 --icon-size 100 --icon "APK加固工具.app" 175 120 --hide-extension "APK加固工具.app" --app-drop-link 425 120 "APK加固工具.dmg" "dist/"
```

## 3. 配置说明

### 依赖打包
- 自动包含所有Python依赖库（从requirements.txt中获取）
- 包含lib目录下的外部JAR文件
- 包含config目录下的配置文件
- 包含META-INF目录下的签名文件

### 应用配置
- 设置应用名称和版本信息
- 配置应用图标（可选）
- 设置高分辨率支持
- 添加必要的资源文件

## 4. 注意事项

1. **Java环境**：应用运行时需要Java环境，建议在README中说明
2. **文件路径**：确保应用内部使用相对路径访问资源文件
3. **权限设置**：确保生成的应用具有执行权限
4. **测试验证**：在不同Mac版本上测试生成的应用

## 5. 最终输出
- `dist/APK加固工具.app`：Mac应用程序
- `APK加固工具.dmg`：DMG安装镜像

## 6. 后续优化
- 添加应用图标
- 完善DMG安装界面设计
- 添加安装引导
- 自动检测和提示Java环境安装

这个方案将帮助您将APK加固工具打包为完整的Mac安装包，包含所有必要的依赖和资源文件，方便用户安装和使用。