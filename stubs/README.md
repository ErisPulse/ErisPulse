# 类型存根文件目录

此目录包含ErisPulse项目的类型存根文件（`.pyi`），用于IDE的类型提示和自动补全功能。

## 目录说明

- **自动生成**：这些文件由`.github/tools/generate-type-stubs.py`脚本自动生成
- **版本控制**：文件会被提交到Git仓库，并由GitHub Actions自动更新
- **IDE支持**：配置正确的IDE后，可以获得完整的类型提示和代码补全

## IDE配置

要使IDE识别这些类型存根文件，请参考[IDE配置指南](ide-configuration.md)。

## 文件结构

```
stubs/
└── ErisPulse/
    ├── __init__.pyi          # 包初始化
    ├── __main__.pyi          # 主入口
    ├── sdk_protocol.pyi      # SDK协议
    ├── Core/                 # 核心模块
    │   ├── __init__.pyi
    │   ├── adapter.pyi       # 适配器
    │   ├── module.pyi        # 模块
    │   ├── lifecycle.pyi     # 生命周期
    │   └── ...
    ├── utils/                # 工具模块
    │   ├── __init__.pyi
    │   ├── cli.pyi
    │   └── ...
    └── ...
```

## 常见问题

### Q: 这些文件可以手动编辑吗？

A: **不可以**。这些文件由脚本自动生成，手动编辑会在下次更新时被覆盖。如果需要修改类型注解，请在源代码（`src/`目录）中进行修改。

### Q: 为什么文件在stubs目录而不是与源代码在一起？

A: 这样可以：
1. 保持源代码目录的清晰度
2. 方便管理自动生成的文件
3. 避免与开发源代码混淆

### Q: GitHub Actions会自动更新这些文件吗？

A: 是的。当代码推送到develop分支或创建PR时，会自动更新这些文件。

## 相关链接

- [类型存根生成脚本](../.github/scripts/generate-type-stubs.py)
- [IDE配置指南](../docs/development/ide-configuration.md)
- [开发文档](../docs/development/README.md)
