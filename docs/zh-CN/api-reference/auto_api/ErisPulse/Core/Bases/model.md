# `ErisPulse.Core.Bases.model` 模块

---

## 模块概述


ErisPulse 数据模型层（ORM）—— 声明式模型与 Active Record CRUD

构建于内置存储层（:mod:`ErisPulse.Core.storage`，SQLite / MySQL / PostgreSQL）
之上：模型对后端透明——切换 ``ErisPulse.storage.backend`` 配置即可换库，模型
代码不变。自动建表、增删改查、查询表达式均由字段声明驱动。

声明形态与声明式配置类（``Core/Bases/config_schema.py``）对齐：一份约束词表
（choices / ge / le / max_length）、同一校验器引擎
（:func:`ErisPulse.Core.Bases.config_schema.validate_field_constraints`）、
同一类型类别注册表（:func:`ErisPulse.Core.Bases.config_schema.python_type_category`）。
基座有意分立——配置字段是普通值（TOML 往返），模型字段是列描述符
（类访问=查询表达式，实例访问=行值），生命周期与消费点各自独立。

> **提示**
> 1. 表名默认取类名 snake_case（``UserProfile → user_profile``），可用
> ``__tablename__`` 覆写
> 2. ``Field(autoincrement=True)`` 的主键由数据库自增，``create`` 后自动回填
> （``save`` 主键缺失退化为插入时同样回填）
> 3. ``list`` / ``dict`` 类型字段（含 ``list[int]`` 等参数化泛型）以 JSON
> 文本列存储，读写自动序列化
> 4. 环境无关：``Model.__storage__`` 可覆写为自定义 ``BaseStorage`` 实例
> （默认使用全局 ``ErisPulse.Core.storage`` 单例）
> 5. 处于 ``storage.atransaction()`` 环境事务内时，读写自动复用事务连接，
> 随事务统一提交/回滚
> 6. 关系映射：``relationship()`` 声明 has-many / belongs-to，实例上链式查询
> 或直接 await（见 :class:`Relationship`）

**示例**:
```python
>>> from ErisPulse.Core.Bases import Model, Field
>>>
>>> class User(Model):
...     id: int = Field(primary_key=True, autoincrement=True)
...     name: str = Field(max_length=64)
...     age: int = Field(default=0, ge=0, le=150)
>>> await User.create_table()
>>> alice = await User.create(name="Alice", age=20)
>>> adults = await User.where(User.age > 18).all()
```

---

## 函数列表


### `_validate_column(name: str)`

列名合法性校验（防注入；与 sql_base 的标识符校验同一口径）

---


### `_quote_ident(name: str, dialect: SQLDialect | None = None)`

标识符引用（优先方言引号；无方言时回落双引号记号，SQLite/Postgres 通用）

---


### `relationship(related: str | type[Model], foreign_key: str)`

声明模型关系（:class:`Relationship` 的工厂函数，与 ``Field(...)`` 同风格）

- **related** (`对方模型（类名字符串或类）`): - **foreign_key**: 外键列名（声明在对方表为 has-many，本表为 belongs-to）
**返回值** (`关系描述符`): 
**示例**:
```python
>>> class User(Model):
...     messages = relationship("Message", foreign_key="user_id")
>>> msgs = await user.messages.all()
```

---


### `_combine(conditions: tuple)`

多条件 AND 组合（类级 CRUD 快捷入口用）

---


## 类列表


### `class Field`

模型字段描述符（声明式列定义）

- **default** (`字段默认值（未提供且非自增主键`): → 必填 NOT NULL）
- **primary_key** (`是否主键`): - **autoincrement**: 是否自增主键（隐含 primary_key，整型）
- **max_length** (`字符串最大长度（生成`): VARCHAR(n)，并参与写入校验）
- **nullable** (`是否允许`): NULL（默认 False → NOT NULL）
- **index** (`是否生成普通索引`): - **unique**: 是否唯一约束
- **choices** (`枚举选项（写入校验）`): - **ge**: 数值下界（写入校验）
- **le** (`数值上界（写入校验）`): - **description**: 字段描述（i18n 字典格式与配置类一致，预留文档/面板用）
- **column_type** (`覆写`): SQL 列类型定义（如 ``"TEXT"``）；默认按类型注册表派生
- **foreign_key** (`列级外键约束（``"表.列"``，如`): ``"users.id"``）——DDL 生成
    ``REFERENCES`` 约束（关系映射的基础设施；ORM 级关系对象后续版本交付）

**示例**:
```python
>>> id: int = Field(primary_key=True, autoincrement=True)
>>> name: str = Field(max_length=64)
```


#### 方法列表


##### `_annotation()`

字段注解（__set_name__ 阶段从 owner __annotations__ 反查）

---


##### `required()`

是否必填（无默认值且非自增）

---


##### `effective_default()`

运行时默认值（default 优先，其次 default_factory，否则 None）

---


##### `to_db_value(value: Any)`

写入数据库的参数值（JSON 列序列化；其余原样）

---


##### `is_json()`

是否 JSON 序列化列

---


##### `sql_type()`

列类型定义（方言翻译前的统一记号，由 aCreateTable 翻译）

---


##### `column_definition()`

单列 DDL 定义（统一记号）

---


##### `_sql_literal(value: Any)`

默认值的 DDL 字面量（仅声明性默认值，运行值走参数绑定）

---


### `class ColumnExpr`

ColumnExpr 类提供相关功能。


#### 方法列表


##### `in_(values: list | tuple)`

IN 条件（``User.id.in_([1, 2, 3])``）

---


### `class Condition`

查询条件节点（叶子比较 / AND-OR 组合），编译为参数化 WHERE 片段


#### 方法列表


##### `compile(dialect: SQLDialect | None = None)`

编译为 (WHERE 片段, 参数列表)；片段为空串表示无条件

- **dialect**: 方言（提供时标识符按方言引号引用，缺省为双引号记号）

---


### `class QuerySet`

链式查询集（惰性构建，await 终结符执行）

``User.where(...).order_by("-age").limit(10).all()``

> **内部方法**
由 :meth:`Model.where` 创建；update / delete 亦经由 QuerySet 应用条件


#### 方法列表


##### `order_by()`

排序（``"age"`` 升序 / ``"-age"`` 降序）

---


##### `async all()`

执行查询，返回模型实例列表

---


##### `async first()`

执行查询，返回首个实例（无结果为 None）

---


##### `async count()`

符合条件的行数

---


##### `async update()`

批量更新符合条件的行

**返回值**: 受影响行数

---


##### `async delete()`

删除符合条件的行

**返回值**: 受影响行数

---


### `class _RelatedMany(QuerySet)`

> **内部方法**
has-many 关系查询集：在 :class:`QuerySet` 全部链式能力之上，
附带 ``create`` 自动回填本表主键到对方外键列


#### 方法列表


##### `where()`

追加对方表字段的条件过滤（与关系外键条件 AND 组合）

**示例**:
```python
>>> await user.posts.where(Post.title == "hi").all()
```

---


##### `async create()`

创建对方表的一行并自动填入本实例主键

**示例**:
```python
>>> await user.messages.create(content="hi")   # user_id 自动 = user.id
```

---


### `class _RelatedOne`

> **内部方法**
belongs-to 单条等待器：``author = await msg.author`` 即解析为对方实例或 None


### `class Relationship`

模型关系声明描述符（has-many / belongs-to）

在模型类体中以类属性形式声明，实例上使用；方向按**外键列声明在哪张表**
自动判定，惰性解析（首次访问时查注册表），无需预注册顺序：

>>> class User(Model):
...     id: int = Field(primary_key=True, autoincrement=True)
...     name: str = Field(max_length=64)
...     messages = relationship("Message", foreign_key="user_id")   # has-many

>>> class Message(Model):
...     id: int = Field(primary_key=True, autoincrement=True)
...     user_id: int = Field(foreign_key="users.id")
...     content: str = Field()
...     author = relationship("User", foreign_key="user_id")        # belongs-to

> **提示**
> 1. 外键列声明在**对方表** → has-many：返回 :class:`QuerySet`，全部链式能力
> 可用（``await user.messages.order_by("-id").limit(10).all()`` / ``.first()``
> / ``.count()`` / ``.delete()``），且 ``await user.messages.create(...)``
> 自动回填本表主键到对方外键列
> 2. 外键列声明在**本表** → belongs-to：``author = await msg.author`` 直接
> await 得到对方实例（无匹配返回 None；外键值为 None 时跳过查询返回 None）
> 3. ``related`` 传类名字符串（按类名注册表惰性解析，两侧模型定义顺序无关）
> 或直接传模型类
> 4. 关系查询与对方模型走同一存储后端（不支持跨后端关联）


#### 方法列表


##### `__init__(related: str | type[Model], foreign_key: str)`

声明模型关系

- **related** (`对方模型（类名或类）`): - **foreign_key**: 外键列名（本表或对方表，判定方向）

---


##### `_related_model(owner: type)`

解析对方模型（类名字符串按注册表惰性查找）

---


### `class Model`

模型基类（Active Record）

继承并声明 :class:`Field` 类属性即可获得自动建表与 CRUD 能力：

>>> class User(Model):
...     id: int = Field(primary_key=True, autoincrement=True)
...     name: str = Field(max_length=64)
>>> await User.create_table()
>>> user = await User.create(name="Alice")
>>> user.name = "Bob"
>>> await user.save()


#### 方法列表


##### `_pk_field()`

主键字段（Field 实例不可作类属性暴露——描述符协议会劫持类访问）

---


##### `table_name()`

表名（snake_case 自动派生或 ``__tablename__`` 覆写）

---


##### `columns()`

字段声明表（{字段名: Field}）

---


##### `_get_storage()`

解析存储后端（覆写优先，否则全局单例）

---


##### `_row_to_instance(row: dict)`

行 dict → 实例（JSON 列反序列化）

---


##### `to_dict()`

导出行数据（JSON 列已反序列化）

---


##### `_validate()`

写入前逐字段约束校验（共享校验器引擎），失败抛 ValueError

---


##### `async create_table()`

自动建表 + 自动迁移（幂等）

表不存在时 ``CREATE TABLE IF NOT EXISTS``；已存在时对比现有列与
模型字段，为**新增字段**自动执行 ``ALTER TABLE ADD COLUMN``（阶段二
自动迁移）：非主键、剔除 NOT NULL 约束（存量行回填 NULL），主键与
类型变更不在自动迁移范围（需手工处理）。迁移列同步创建其声明的索引。

**返回值**: 是否成功

---


##### `async _migrate_new_columns(storage)`

> **内部方法**
自动迁移：为表中新增的模型字段执行 ``ALTER TABLE ADD COLUMN``

迁移列剔除 NOT NULL 约束（存量行回填 NULL），跳过主键（主键变更
需重建表，不属于自动迁移范围）。

- **storage** (`存储实例`): **返回值**: 本次新增的列名列表

---


##### `async drop_table()`

删表（危险操作，仅测试与显式维护场景使用）

---


##### `async has_table()`

表是否存在

---


##### `where()`

条件查询入口（``User.where(User.age > 18)`` → :class:`QuerySet`）

多条件以 AND 连接；OR 用 ``(cond1) | (cond2)`` 组合。

---


##### `all()`

无条件查询集（等价 ``cls.where()``）

---


##### `async get()`

等值查询首条（``User.get(id=1)``）；无结果返回 None

**异常**: `ValueError` - 条件字段未在模型中声明时

---


##### `async create()`

插入一行并返回实例（自增主键自动回填）

处于 ``storage.atransaction()`` 环境事务内时，INSERT 复用事务连接，
随事务统一提交/回滚，不独立提交。

**异常**: `ValueError` - 约束校验失败（必填缺失 / 枚举外 / 越界 / 超长）

---


##### `async _insert_and_backfill(instance: Model)`

> **内部方法**
INSERT 一行并按需回填自增主键到实例（:meth:`create` 与 :meth:`save` 共用）

列参数构建（自增主键交由数据库、可空/有默认字段 None 跳过、JSON 序列化）
与连接路由在此收敛：处于环境事务内复用事务连接，否则开事务专用连接
自管提交（自增回填要求 INSERT 与 last-id 查询同连接）。

- **instance**: 已完成约束校验的待插入实例

---


##### `async count()`

行数统计（``await User.count(User.age > 18)``）

---


##### `async delete_all()`

批量删除（``await User.delete_all(User.age > 18)``；无条件则全表删除）

---


##### `async update_all()`

批量更新（``await User.update_all(User.age > 18, name="adult")``）

---


##### `async save()`

按主键更新本行（先约束校验）；主键缺失时退化为插入（自增主键同样回填到本实例）

**返回值**: 受影响行数

---


##### `async delete()`

按主键删除本行

**异常**: `ValueError` - 模型无主键或实例主键为空时
**返回值**: 受影响行数

---

