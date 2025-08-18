# ErisPulse Documentation

欢迎阅读 ErisPulse 文档。ErisPulse 是一个可扩展的多平台消息处理框架，支持通过适配器与不同平台进行交互。

## 文档目录

```
docs/
├── README.md
├── quick-start.md
├── platform-features.md
├── ai/
│   ├── README.md
│   ├── module-generation.md
│   └── AIDocs/
│       ├── README.md
│       ├── ErisPulse-ModuleDev.md
│       ├── ErisPulse-AdapterDev.md
│       ├── ErisPulse-Core.md
|       └── ErisPulse-Full.md
├── core/
│   ├── README.md
│   ├── cli.md
│   ├── concepts.md
│   ├── modules.md
│   ├── adapters.md
│   ├── event-system.md
│   └── best-practices.md
├── development/
│   ├── README.md
│   ├── adapter.md
│   ├── module.md
│   └── cli.md
├── standards/
│   ├── README.md
│   ├── event-conversion.md
│   └── api-response.md
└── api/ (自动生成的API文档)
```

### 快速开始
- [快速开始指南](quick-start.md)            - 安装和运行 ErisPulse 的入门指南
- [各平台风格特性](platform-features.md)    - 各个适配器支持的发送方法，以及对于OneBot12的拓展字段介绍

### AI相关文档
- [AI模块生成](module-generation.md)        - 快速使用AIDocs生成一个AI模块/适配器
- 所有AI物料（注意，不推荐直接使用Full投喂给AI，除非这个模型具有强大的上下文能力）:
  - [模块开发物料](ai/AIDocs/ErisPulse-ModuleDev.md)
  - [适配器开发物料](ai/AIDocs/ErisPulse-AdapterDev.md)
  - [核心模块开发物料](ai/AIDocs/ErisPulse-Core.md)
  - [物料集合](ai/AIDocs/ErisPulse-Full.md)

### 核心功能
- [命令行接口](cli.md)              - 使用命令行界面管理 ErisPulse
- [核心概念](core/concepts.md)      - ErisPulse 的基础架构和设计理念
- [核心模块](core/modules.md)       - 存储、配置、日志等核心组件详解
- [适配器系统](core/adapters.md)    - 平台适配器的使用和开发
- [事件系统](core/event-system.md)  - Event 模块的使用(事件监听、事件处理、事件分发)
- [最佳实践](core/best-practices.md) - 开发和部署建议

### 开发指南
- [开发入门](development/README.md)     - 开发环境搭建和基本概念
- [模块开发](development/module.md)     - 开发自定义功能模块
- [适配器开发](development/adapter.md)  - 开发一个平台适配器
- [CLI 开发](development/cli.md)        - 扩展命令行工具功能

### 标准规范
- [标准规范](standards/README.md)           - ErisPulse 技术标准总览
- [事件转换](standards/event-conversion.md) - 平台事件到 OneBot12 标准的转换规范
- [API 响应](standards/api-response.md)     - 适配器 API 响应格式标准

### API 参考
- [API 文档](api/) - 自动生成的详细 API 参考
