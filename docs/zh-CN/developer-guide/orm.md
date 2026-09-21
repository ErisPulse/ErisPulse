# 数据模型层（ORM）

2.9.0 起框架内置声明式数据模型层：继承 `Model` 并用 `Field` 声明字段，即可获得自动建表与增删改查能力。模型直接构建在内置存储层之上——SQLite / MySQL / PostgreSQL 由 `ErisPulse.storage.backend` 配置决定，**切换后端无需修改模型代码**。

## 声明模型

```python
from ErisPulse.Core.Bases import Model, Field

class User(Model):
    id: int = Field(primary_key=True, autoincrement=True)
    name: str = Field(max_length=64)
    age: int = Field(default=0, ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    tags: list = Field(default_factory=list)          # JSON 列，读写自动序列化
    bio: str = Field(default="", description={"i18n": "user.bio", "default": "简介"})
```

- 表名默认取类名 snake_case（`UserProfile → user_profile`），可用 `__tablename__ = "xxx"` 覆写
- `Field` 的约束词表与声明式配置类一致（`choices` / `ge` / `le` / `max_length`，`description` 同样支持 i18n 字典）；校验器引擎与配置校验同源

## 字段参数

| 参数 | 说明 |
|------|------|
| `default` | 默认值（未提供且非自增 → 必填 NOT NULL） |
| `default_factory` | 可变默认值工厂（如 `list`） |
| `primary_key` | 主键 |
| `autoincrement` | 自增主键（隐含主键，`create` 后自动回填） |
| `max_length` | 字符串最大长度（生成 `VARCHAR(n)`，写入校验） |
| `nullable` | 是否允许 NULL（默认 False） |
| `index` | 生成普通索引 |
| `unique` | 唯一约束 |
| `choices` / `ge` / `le` | 枚举 / 数值范围（写入校验） |
| `description` | 描述（i18n 字典，与配置类同格式） |
| `column_type` | 覆写 SQL 列类型定义 |

## 建表与 CRUD

```python
await User.create_table()                      # 幂等（IF NOT EXISTS）

user = await User.create(name="Alice", age=20) # 插入（自增主键自动回填）
got = await User.get(id=user.id)               # 等值查询首条

users = await User.where(User.age > 18).order_by("-age").limit(10).all()
first = await User.where(User.name == "Alice").first()
total = await User.count(User.age > 18)

user.age = 21
await user.save()                              # 按主键更新（先约束校验）；主键缺失时退化为插入（自增主键同样回填到实例）
await user.delete()                            # 按主键删除

await User.update_all(User.age > 18, role="adult")  # 批量更新
await User.delete_all(User.age > 100)               # 批量删除
```

查询表达式支持 `> >= < <= == !=`、`in_([...])`，以及 `&`（与）/ `|`（或）组合：

```python
await User.where((User.age > 18) & User.name.in_(["Alice", "Bob"])).all()
```

## 事务

ORM 读写与框架存储层共用同一事务路由：处于 `storage.atransaction()` 环境事务内时，`create` / `save` / `delete` 与查询自动复用事务连接，随事务统一提交或回滚，不会独立提交。

```python
async with storage.atransaction():
    await User.create(name="Alice")
    ...  # 块内抛异常时，上面的 INSERT 一并回滚
```

## 与声明式配置类的关系

模型声明与 `ConfigClass`（`@dataclass + field(metadata=...)`）**共享同一套底层**——约束词表、校验器引擎（`validate_field_constraints`）、类型类别注册表（`python_type_category`）；但类基座有意分立：配置字段是普通值（TOML 往返、一次加载热更新），模型字段是列描述符（类访问 = 查询表达式、逐行实例）。一份声明语法，两个各司其职的基座。

## 边界与注意事项

- 后端由全局存储配置决定；模型可用 `__storage__` 类属性覆写为自定义 `BaseStorage` 实例（测试注入用）
- `list` / `dict` 字段（含参数化泛型如 `list[int]`、`dict[str, int]`）按容器类别以 JSON 文本列存储，读写自动序列化
- 写入（`create` / `save`）前自动执行约束校验，失败抛 `ValueError`（本地化消息）
- 自动迁移（schema diff）与关系映射为后续版本能力
- 触发存储连接失败时的行为与存储层一致：不崩溃框架，冷却后自动重连
