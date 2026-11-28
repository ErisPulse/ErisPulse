# 风格指南

本目录包含 ErisPulse 项目的工程纪律与写作规范。

## 文档列表

- [术语表（唯一真相源）](glossary.md) - Client/HttpClient、storage/env/StorageManager、BaseConfig/AdapterConfig、scope 三维、归属权、服务契约/目录/白名单等易漂移术语的唯一定义
- [注释风格规范](docstring.md) - 方法注释和文档字符串的格式规范与标签解析契约
- [工程健壮性规则](engineering.md) - 异常留痕分级、日志分级、行为参数集中、API 契约、单例回引禁忌、清理与回滚纪律、测试纪律
- [文档与对外写作规则](docs-writing.md) - 文档行文、版本标注、README 与发布页的三段式骨架、场景化表达、变更记录写作

## 适用对象

- ErisPulse 核心贡献者
- 模块和适配器开发者
- 维护 README 与对外页面的贡献者
- 需要生成 API 文档的开发者

## 与其它规范的关系

- [技术标准](../standards/) - 适配器的**技术**规范（会话类型、事件转换、API 形态）；本目录是**工程与写作**纪律，两者互补不重叠
- `CONTRIBUTING.md` - 贡献流程与 CI 门禁（本目录规则中的可机检部分由门禁脚本执行）
- `CHANGELOG.md` 头部「写作规范」 - 变更记录的详细规范（本文档只做引用，不重复正文）
