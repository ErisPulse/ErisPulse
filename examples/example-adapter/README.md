# ErisPulse Example Adapter

ErisPulse 适配器参考实现：演示 `BaseAdapter` 完整接入方式（声明式配置、SendDSL、事件转换器）。

## 结构

```text
example-adapter/
├── pyproject.toml        # 包元数据与 erispulse.adapter entry-point
└── MyAdapter/
    ├── __init__.py       # 导出适配器与转换器
    ├── Core.py           # 适配器主类（ConfigClass / I18nClass / Send / Request / Api / 生命周期）
    └── Converter.py      # 平台原生事件 → OneBot12 标准事件
```

## 本地试用（免打包）

把本目录作为本地适配器插件直接放入你的 bot 项目运行（无需 `pip install -e .`）：

```bash
cp -r MyAdapter /path/to/your-bot/plugins/
# 框架启动时自动发现 plugins/ 下的适配器
```

## 正式安装

```bash
pip install -e .
# 或打包发布后：
epsdk install erispulse-example-adapter
```

> 提示：本地开发推荐 `epsdk create adapter -n MyAdapter --local` 直接生成相同结构；
> 验证完成后用 `epsdk create pack` 一键转换为可发布项目。
