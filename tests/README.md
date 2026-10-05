# ErisPulse 测试目录说明

本目录包含 ErisPulse SDK 的测试文件，分为开发者快速测试和标准单元测试两部分。

## 目录结构

```
tests/
├── README.md              # 本说明文档
├── conftest.py           # pytest 配置和测试夹具
├── devs/                 # 开发者快速测试目录
│   ├── test_adapter.py   # 适配器综合测试框架
│   ├── test_cmd.py      # 命令系统测试示例
│   ├── test_event.py    # 事件系统综合测试
│   ├── test_compat.py   # SDK兼容性测试
│   └── test_files/      # 测试资源文件
├── unit/                # 标准单元测试目录
│   └── test_unit_*.py   # 各模块单元测试
├── integration/         # 集成测试目录（test_integration_*.py）
├── performance/         # 性能目录：test_perf_*.py + 全组件基准 benchmark.py
└── stress/              # 压力测试目录（test_stress_*.py）
```

## 开发者快速测试 (devs/)

`devs/` 目录用于开发者进行快速功能验证和测试，不是正式的单元测试目录。

### 特点

- 随时可用：可以直接运行，无需复杂的测试环境配置
- 灵活性高：可以自由修改、添加测试代码
- 用途广泛：用于验证向后兼容性、快速功能测试、问题排查等

### 测试文件说明

#### test_adapter.py
适配器综合测试框架，包含：
- 完整的适配器发送功能测试
- 支持多种消息类型（文本、图片、视频、文件等）
- 可配置的测试用例和运行方式
- 详细的测试结果报告

使用方法：
```bash
python tests/devs/test_adapter.py
```

#### test_cmd.py
命令系统测试示例，包含：
- 基本命令处理测试
- 命令别名测试
- 权限控制测试
- 交互式命令测试（wait_reply）
- 中间件测试

使用方法：
```bash
python tests/devs/test_cmd.py
```

#### test_event.py
事件系统综合测试，包含三个部分：
- 事件处理系统测试（命令、消息、通知、元事件）
- Event包装类基础功能测试
- Event包装类扩展功能测试

使用方法：
```bash
# 运行事件处理系统测试（默认）
python tests/devs/test_event.py

# 运行Event包装类基础功能测试
python tests/devs/test_event.py basic

# 运行Event包装类扩展功能测试
python tests/devs/test_event.py extended

# 运行Event包装类完整测试
python tests/devs/test_event.py wrapper
```

#### test_compat.py
SDK兼容性测试，验证：
- SDK 核心模块导入
- 向后兼容性
- 懒加载模块功能
- 加载器导入

使用方法：
```bash
python tests/devs/test_compat.py
```

## 性能基准 (performance/benchmark.py)

`performance/benchmark.py` 是覆盖全部核心组件的手动性能基准脚本（纯标准库实现，
pytest 不会收集）。运行期间所有状态（config.toml / sqlite 数据库）均落在系统临时
目录，不影响仓库真实配置。

覆盖套件：

- **config**：getConfig 热读/脏覆盖层、setConfig 各写入路径、getAllConfig、ConfigClass 属性访问、get_event_config 合成
- **event**：总线直连吞吐/延迟、中间件链、detail_type 匹配、handler 注册、lifecycle.fire、消息桥、命令命中/miss、事件洪泛
- **storage**：KV 异步/同步、批量 multi、查询构建器、事务、ORM（`--backend` 可切 mysql/postgres）
- **send**：SendDSL 链构建与完整 hooked 发送路径（mock 传输）
- **router**：ASGI 层请求（httpx ASGITransport，需 test extra）
- **module**：跨模块 RPC、属性访问、spawn_background
- **overall**：命令→存储→发送 端到端全链路、混合负载
- **startup**：冷导入、sdk.init()/uninit()、装载适配器+模块

使用方法：

```bash
# 全套件完整档
python tests/performance/benchmark.py

# 指定套件 / 快速冒烟档
python tests/performance/benchmark.py --suite event,config --quick

# 落盘基线 / 与旧基线对比 / 生成 HTML 报告
python tests/performance/benchmark.py --json base.json
python tests/performance/benchmark.py --compare base.json
python tests/performance/benchmark.py --html report.html

# 存储套件切换后端（mysql/postgres 需对应连接环境变量与驱动 extra）
python tests/performance/benchmark.py --suite storage --backend mysql
```

同目录的 `test_perf_*.py` 为批量操作正确性断言（被 pytest 默认忽略，仅手动运行）。

## 标准单元测试 (unit/)

`unit/` 目录包含正式的单元测试，使用 pytest 框架运行。

### 运行单元测试

```bash
# 运行所有单元测试
pytest tests/unit/

# 运行特定模块测试
pytest tests/unit/test_unit_adapter.py

# 运行测试并显示详细输出
pytest tests/unit/ -v

# 运行测试并生成覆盖率报告
pytest tests/unit/ --cov=ErisPulse --cov-report=html
```

## pytest 配置

测试配置文件为 `conftest.py`，提供以下功能：
- 测试夹具（fixtures）：mock_sdk、real_sdk、mock_event_data 等
- 测试环境设置：临时数据目录、配置文件等
- 测试标记：unit、integration、e2e 等

## 开发者使用建议

1. **快速验证功能**：使用 `devs/` 目录下的测试文件
2. **验证兼容性**：运行 `test_compat.py` 确保导入正常
3. **测试适配器**：使用 `test_adapter.py` 进行完整的适配器功能测试
4. **测试事件系统**：使用 `test_event.py` 验证事件处理和包装类
5. **参考命令实现**：查看 `test_cmd.py` 了解命令系统的使用方式

## 注意事项

- `devs/` 目录的测试文件可以根据需要随时修改
- `unit/` 目录的测试文件应遵循单元测试规范
- 测试资源文件（如测试图片、视频等）存放在 `devs/test_files/` 目录
- 运行测试前请确保已正确配置 SDK 和适配器