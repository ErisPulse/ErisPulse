"""
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

{!--< tips >!--}
1. 表名默认取类名 snake_case（``UserProfile → user_profile``），可用
   ``__tablename__`` 覆写
2. ``Field(autoincrement=True)`` 的主键由数据库自增，``create`` 后自动回填
   （``save`` 主键缺失退化为插入时同样回填）
3. ``list`` / ``dict`` 类型字段（含 ``list[int]`` 等参数化泛型）以 JSON
   文本列存储，读写自动序列化
4. 环境无关：``Model.__storage__`` 可覆写为自定义 ``BaseStorage`` 实例
   （默认使用全局 ``ErisPulse.Core.storage`` 单例）
5. 处于 ``storage.atransaction()`` 环境事务内时，读写自动复用事务连接，
   随事务统一提交/回滚
6. 自动迁移（schema diff）与关系映射为后续版本能力，本层不包含
{!--< /tips >!--}

:example:
>>> from ErisPulse.Core.Bases import Model, Field
>>>
>>> class User(Model):
...     id: int = Field(primary_key=True, autoincrement=True)
...     name: str = Field(max_length=64)
...     age: int = Field(default=0, ge=0, le=150)
>>> await User.create_table()
>>> alice = await User.create(name="Alice", age=20)
>>> adults = await User.where(User.age > 18).all()
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar

from .config_schema import python_type_category, validate_field_constraints
from .sql_base import BaseStorage, SQLDialect, SQLStorageBase
from .storage import _current_txn

_UNSET = object()
_SNAKE_RE = re.compile(r"(?<!^)(?=[A-Z])")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# 类别 → SQL 基础列类型（与 config 的 TOML 映射同源派生自 python_type_category）
_CATEGORY_TO_SQL: dict[str, str] = {
    "int": "INTEGER",
    "float": "REAL",
    "bool": "BOOLEAN",
    "str": "TEXT",
    "list": "TEXT",
    "dict": "TEXT",
}

# 需要读写 JSON 序列化的类别
_JSON_CATEGORIES = frozenset({"list", "dict"})


class Field:
    """
    模型字段描述符（声明式列定义）

    :param default: 字段默认值（未提供且非自增主键 → 必填 NOT NULL）
    :param primary_key: 是否主键
    :param autoincrement: 是否自增主键（隐含 primary_key，整型）
    :param max_length: 字符串最大长度（生成 VARCHAR(n)，并参与写入校验）
    :param nullable: 是否允许 NULL（默认 False → NOT NULL）
    :param index: 是否生成普通索引
    :param unique: 是否唯一约束
    :param choices: 枚举选项（写入校验）
    :param ge: 数值下界（写入校验）
    :param le: 数值上界（写入校验）
    :param description: 字段描述（i18n 字典格式与配置类一致，预留文档/面板用）
    :param column_type: 覆写 SQL 列类型定义（如 ``"TEXT"``）；默认按类型注册表派生

    :example:
    >>> id: int = Field(primary_key=True, autoincrement=True)
    >>> name: str = Field(max_length=64)
    """

    def __init__(
        self,
        default: Any = _UNSET,
        *,
        default_factory: Any | None = None,
        primary_key: bool = False,
        autoincrement: bool = False,
        max_length: int | None = None,
        nullable: bool = False,
        index: bool = False,
        unique: bool = False,
        choices: list | tuple | None = None,
        ge: int | float | None = None,
        le: int | float | None = None,
        description: dict | None = None,
        column_type: str | None = None,
    ):
        if autoincrement:
            primary_key = True
        self.default = default
        self.default_factory = default_factory
        self.primary_key = primary_key
        self.autoincrement = autoincrement
        self.max_length = max_length
        self.nullable = nullable
        self.index = index
        self.unique = unique
        self.choices = list(choices) if choices else None
        self.ge = ge
        self.le = le
        self.description = description
        self.column_type = column_type
        self.name: str = ""
        self.owner: type[Model] | None = None
        self.category: str = "str"

    def __set_name__(self, owner: type[Model], name: str) -> None:
        if not _IDENTIFIER_RE.fullmatch(name):
            raise ValueError(f"invalid field name: {name!r}")
        self.name = name
        self.owner = owner
        self.category = python_type_category(self._annotation())

    def _annotation(self) -> Any:
        """字段注解（__set_name__ 阶段从 owner __annotations__ 反查）"""
        if self.owner is None:
            return str
        for klass in self.owner.__mro__:
            if self.name in klass.__annotations__:
                return klass.__annotations__[self.name]
        return str

    @property
    def required(self) -> bool:
        """是否必填（无默认值且非自增）"""
        return self.default is _UNSET and self.default_factory is None and not self.autoincrement

    def effective_default(self) -> Any:
        """运行时默认值（default 优先，其次 default_factory，否则 None）"""
        if self.default is not _UNSET:
            return self.default
        if self.default_factory is not None:
            return self.default_factory()
        return None

    def to_db_value(self, value: Any) -> Any:
        """写入数据库的参数值（JSON 列序列化；其余原样）"""
        if value is not None and self.is_json and not isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        return value

    @property
    def is_json(self) -> bool:
        """是否 JSON 序列化列"""
        return self.category in _JSON_CATEGORIES

    # ---- 描述符协议 ----

    def __get__(self, instance: Any, owner: type[Model] | None = None) -> Any:
        if instance is None:
            # 类访问 → 查询列表达式（User.age > 18）
            return ColumnExpr(self.name, self.category)
        if self.name in instance.__dict__:
            return instance.__dict__[self.name]
        return None

    def __set__(self, instance: Any, value: Any) -> None:
        # 实例内存值保持原生类型（序列化仅在写库参数层：create/save/update）
        instance.__dict__[self.name] = value

    # ---- DDL 片段 ----

    def sql_type(self) -> str:
        """列类型定义（方言翻译前的统一记号，由 aCreateTable 翻译）"""
        if self.column_type:
            return self.column_type
        base = _CATEGORY_TO_SQL[self.category]
        if self.category == "str" and self.max_length:
            return f"VARCHAR({self.max_length})"
        return base

    def column_definition(self) -> str:
        """单列 DDL 定义（统一记号）"""
        parts = [self.sql_type()]
        if self.autoincrement:
            # 自增主键交给方言钩子（aCreateTable 翻译 AUTOINCREMENT 记号）
            parts = ["INTEGER PRIMARY KEY AUTOINCREMENT"]
        elif self.primary_key:
            parts.append("PRIMARY KEY")
        if not self.nullable and not self.primary_key:
            parts.append("NOT NULL")
        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        if self.default is not _UNSET and not self.autoincrement:
            parts.append(f"DEFAULT {self._sql_literal(self.default)}")
        return " ".join(parts)

    def _sql_literal(self, value: Any) -> str:
        """默认值的 DDL 字面量（仅声明性默认值，运行值走参数绑定）"""
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, (int, float)):
            return str(value)
        if self.is_json:
            value = json.dumps(value, ensure_ascii=False)
        return "'" + str(value).replace("'", "''") + "'"


class ColumnExpr:
    # __eq__ 被重载为条件构造（返回 Condition），本对象不支持哈希
    __hash__ = None  # type: ignore[assignment]

    """
    列查询表达式（模型类属性访问的返回值）

    支持比较运算符生成条件节点与 ``&`` / ``|`` 组合：
    ``(User.age > 18) & (User.name == "Alice")``

    {!--< internal-use >!--}
    由 Field.__get__ 在类访问时创建，模块作者无需直接实例化
    {!--< /internal-use >!--}
    """

    def __init__(self, column: str, category: str = "str"):
        self.column = column
        self.category = category

    def _cond(self, op: str, value: Any) -> Condition:
        return Condition(self.column, op, value)

    def __gt__(self, other: Any) -> Condition:
        return self._cond(">", other)

    def __ge__(self, other: Any) -> Condition:
        return self._cond(">=", other)

    def __lt__(self, other: Any) -> Condition:
        return self._cond("<", other)

    def __le__(self, other: Any) -> Condition:
        return self._cond("<=", other)

    def __eq__(self, other: Any) -> Condition:  # type: ignore[override]
        return self._cond("=", other)

    def __ne__(self, other: Any) -> Condition:  # type: ignore[override]
        return self._cond("!=", other)

    def in_(self, values: list | tuple) -> Condition:
        """IN 条件（``User.id.in_([1, 2, 3])``）"""
        return self._cond("IN", list(values))


class Condition:
    """查询条件节点（叶子比较 / AND-OR 组合），编译为参数化 WHERE 片段"""

    def __init__(
        self,
        column: str | None = None,
        op: str | None = None,
        value: Any = None,
        combinator: str | None = None,
        left: Condition | None = None,
        right: Condition | None = None,
    ):
        self.column = column
        self.op = op
        self.value = value
        self.combinator = combinator
        self.left = left
        self.right = right

    def __and__(self, other: Condition) -> Condition:
        return Condition(combinator="AND", left=self, right=other)

    def __or__(self, other: Condition) -> Condition:
        return Condition(combinator="OR", left=self, right=other)

    def compile(self, dialect: SQLDialect | None = None) -> tuple[str, list[Any]]:
        """
        编译为 (WHERE 片段, 参数列表)；片段为空串表示无条件

        :param dialect: 方言（提供时标识符按方言引号引用，缺省为双引号记号）
        """
        if self.combinator:
            left, right = self.left, self.right
            if left is None or right is None:
                return "", []
            left_sql, left_params = left.compile(dialect)
            right_sql, right_params = right.compile(dialect)
            if not left_sql:
                return right_sql, right_params
            if not right_sql:
                return left_sql, left_params
            return f"({left_sql} {self.combinator} {right_sql})", [*left_params, *right_params]

        assert self.column is not None  # 叶子节点必有列名
        quoted = _quote_ident(self.column, dialect)
        if self.op == "IN":
            if not self.value:
                return "1=0", []  # 空集合 IN 恒假
            marks = ", ".join("?" for _ in self.value)
            return f"{quoted} IN ({marks})", list(self.value)
        if self.value is None:
            if self.op == "=":
                return f"{quoted} IS NULL", []
            if self.op == "!=":
                return f"{quoted} IS NOT NULL", []
        return f"{quoted} {self.op} ?", [self.value]


def _validate_column(name: str) -> str:
    """列名合法性校验（防注入；与 sql_base 的标识符校验同一口径）"""
    if not _IDENTIFIER_RE.fullmatch(name):
        raise ValueError(f"invalid column name: {name!r}")
    return name


def _quote_ident(name: str, dialect: SQLDialect | None = None) -> str:
    """
    标识符引用（优先方言引号；无方言时回落双引号记号，SQLite/Postgres 通用）
    """
    _validate_column(name)
    return dialect.quote(name) if dialect is not None else f'"{name}"'


class QuerySet:
    """
    链式查询集（惰性构建，await 终结符执行）

    ``User.where(...).order_by("-age").limit(10).all()``

    {!--< internal-use >!--}
    由 :meth:`Model.where` 创建；update / delete 亦经由 QuerySet 应用条件
    {!--< /internal-use >!--}
    """

    def __init__(self, model: type[Model], condition: Condition | None = None):
        self._model = model
        self._condition = condition
        self._order: list[str] = []
        self._limit: int | None = None
        self._offset: int | None = None

    def order_by(self, *fields: str) -> QuerySet:
        """排序（``"age"`` 升序 / ``"-age"`` 降序）"""
        self._order.extend(fields)
        return self

    def limit(self, n: int) -> QuerySet:
        self._limit = n
        return self

    def offset(self, n: int) -> QuerySet:
        self._offset = n
        return self

    # ---- SQL 构建 ----

    def _where_clause(self, dialect: SQLDialect | None = None) -> tuple[str, list[Any]]:
        if self._condition is None:
            return "", []
        sql, params = self._condition.compile(dialect)
        return (f" WHERE {sql}", params) if sql else ("", [])

    def _order_clause(self, dialect: SQLDialect | None = None) -> str:
        if not self._order:
            return ""
        parts = []
        for item in self._order:
            desc = item.startswith("-")
            name = _quote_ident(item[1:] if desc else item, dialect)
            parts.append(f"{name} DESC" if desc else f"{name} ASC")
        return " ORDER BY " + ", ".join(parts)

    def _limit_clause(self, params: list[Any]) -> str:
        clause = ""
        if self._limit is not None:
            clause += " LIMIT ?"
            params.append(self._limit)
        if self._offset is not None:
            clause += " OFFSET ?"
            params.append(self._offset)
        return clause

    # ---- 终结符 ----

    async def all(self) -> list[Any]:
        """执行查询，返回模型实例列表"""
        storage = self._model._get_storage()
        dialect = storage.dialect
        where_sql, where_params = self._where_clause(dialect)
        params: list[Any] = [*where_params]
        sql = (
            f"SELECT * FROM {_quote_ident(self._model.table_name(), dialect)}{where_sql}"
            f"{self._order_clause(dialect)}{self._limit_clause(params)}"
        )
        rows, cols = await storage._execute_query("select", sql, params)
        return [self._model._row_to_instance(dict(zip(cols or [], row, strict=False))) for row in rows]

    async def first(self) -> Any | None:
        """执行查询，返回首个实例（无结果为 None）"""
        self.limit(1)
        results = await self.all()
        return results[0] if results else None

    async def count(self) -> int:
        """符合条件的行数"""
        storage = self._model._get_storage()
        dialect = storage.dialect
        where_sql, where_params = self._where_clause(dialect)
        sql = f"SELECT COUNT(*) FROM {_quote_ident(self._model.table_name(), dialect)}{where_sql}"
        return int(await storage._execute_query("count", sql, where_params))

    async def update(self, **values: Any) -> int:
        """
        批量更新符合条件的行

        :return: 受影响行数
        """
        fields_map = self._model.columns()
        updates = {k: v for k, v in values.items() if k in fields_map}
        if not updates:
            return 0
        storage = self._model._get_storage()
        dialect = storage.dialect
        sets, params = [], []
        for name, value in updates.items():
            sets.append(f"{_quote_ident(name, dialect)} = ?")
            params.append(fields_map[name].to_db_value(value))
        where_sql, where_params = self._where_clause(dialect)
        sql = (
            f"UPDATE {_quote_ident(self._model.table_name(), dialect)} "
            f"SET {', '.join(sets)}{where_sql}"
        )
        return int(await storage._execute_query("dml", sql, [*params, *where_params]))

    async def delete(self) -> int:
        """
        删除符合条件的行

        :return: 受影响行数
        """
        storage = self._model._get_storage()
        dialect = storage.dialect
        where_sql, where_params = self._where_clause(dialect)
        sql = f"DELETE FROM {_quote_ident(self._model.table_name(), dialect)}{where_sql}"
        return int(await storage._execute_query("dml", sql, where_params))


class Model:
    """
    模型基类（Active Record）

    继承并声明 :class:`Field` 类属性即可获得自动建表与 CRUD 能力：

    >>> class User(Model):
    ...     id: int = Field(primary_key=True, autoincrement=True)
    ...     name: str = Field(max_length=64)
    >>> await User.create_table()
    >>> user = await User.create(name="Alice")
    >>> user.name = "Bob"
    >>> await user.save()
    """

    __tablename__: ClassVar[str | None] = None
    # 存储后端覆写（None → 全局 ErisPulse.Core.storage 单例）
    __storage__: ClassVar[BaseStorage | None] = None

    _fields: ClassVar[dict[str, Field]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        collected: dict[str, Field] = {}
        for klass in reversed(cls.__mro__):
            collected.update(
                {n: a for n, a in vars(klass).items() if isinstance(a, Field)}
            )
        cls._fields = collected
        table = getattr(cls, "__tablename__", None) or _SNAKE_RE.sub("_", cls.__name__).lower()
        if not _IDENTIFIER_RE.fullmatch(table):
            raise ValueError(f"invalid table name: {table!r}")
        cls.__tablename__ = table

    @classmethod
    def _pk_field(cls) -> Field | None:
        """主键字段（Field 实例不可作类属性暴露——描述符协议会劫持类访问）"""
        return next((f for f in cls._fields.values() if f.primary_key), None)

    # ---- 元信息 ----

    @classmethod
    def table_name(cls) -> str:
        """表名（snake_case 自动派生或 ``__tablename__`` 覆写）"""
        return cls.__tablename__  # type: ignore[return-value]

    @classmethod
    def columns(cls) -> dict[str, Field]:
        """字段声明表（{字段名: Field}）"""
        return cls._fields

    @classmethod
    def _get_storage(cls) -> SQLStorageBase:
        """解析存储后端（覆写优先，否则全局单例）"""
        if cls.__storage__ is not None:
            return cls.__storage__  # type: ignore[return-value]
        from ..storage import storage as global_storage

        return global_storage  # type: ignore[return-value]

    # ---- 实例化 ----

    def __init__(self, **kwargs: Any):
        for name, field_obj in self._fields.items():
            if name in kwargs:
                setattr(self, name, kwargs.pop(name))
            else:
                setattr(self, name, field_obj.effective_default())
        if kwargs:
            unknown = ", ".join(sorted(kwargs))
            raise TypeError(f"unknown fields for {type(self).__name__}: {unknown}")

    @classmethod
    def _row_to_instance(cls, row: dict) -> Model:
        """行 dict → 实例（JSON 列反序列化）"""
        for name, value in row.items():
            field_obj = cls._fields.get(name)
            if field_obj is not None and field_obj.is_json and isinstance(value, str):
                try:
                    row[name] = json.loads(value)
                except (ValueError, TypeError):
                    pass
        for name, field_obj in cls._fields.items():
            row.setdefault(name, field_obj.effective_default())
        instance = cls.__new__(cls)
        instance.__dict__.update(row)
        return instance

    def to_dict(self) -> dict:
        """导出行数据（JSON 列已反序列化）"""
        result = {}
        for name, field_obj in self._fields.items():
            value = self.__dict__.get(name)
            if field_obj.is_json and isinstance(value, str):
                try:
                    value = json.loads(value)
                except (ValueError, TypeError):
                    pass
            result[name] = value
        return result

    def __repr__(self) -> str:
        pairs = ", ".join(f"{n}={self.__dict__.get(n)!r}" for n in self._fields)
        return f"{type(self).__name__}({pairs})"

    # ---- 校验 ----

    def _validate(self) -> None:
        """写入前逐字段约束校验（共享校验器引擎），失败抛 ValueError"""
        errors: list[str] = []
        for name, field_obj in self._fields.items():
            raw = self.__dict__.get(name)
            value = raw
            if field_obj.is_json and isinstance(raw, str):
                try:
                    value = json.loads(raw)
                except (ValueError, TypeError):
                    value = raw
            errors.extend(
                validate_field_constraints(
                    name,
                    value,
                    required=field_obj.required,
                    choices=field_obj.choices,
                    min_value=field_obj.ge,
                    max_value=field_obj.le,
                    max_length=field_obj.max_length,
                )
            )
        if errors:
            raise ValueError(" ".join(errors))

    # ---- DDL ----

    @classmethod
    async def create_table(cls) -> bool:
        """
        自动建表（幂等：CREATE TABLE IF NOT EXISTS；方言翻译由存储层承接）

        声明了 ``index=True`` 的字段会同步生成普通索引（MySQL 等不支持
        ``IF NOT EXISTS`` 建索引的方言由存在性预检保证幂等）。

        :return: 是否成功
        """
        storage = cls._get_storage()
        cols = {name: f.column_definition() for name, f in cls._fields.items()}
        if not await storage.aCreateTable(cls.table_name(), cols):
            return False
        dialect = storage.dialect
        for name, field_obj in cls._fields.items():
            if field_obj.index:
                idx = f"idx_{cls.table_name()}_{name}"
                exists_sql, exists_params = dialect.has_index_sql(cls.table_name(), idx)
                row, _ = await storage._execute_query("one", exists_sql, exists_params)
                if row is None:
                    await storage._execute_query(
                        "dml", dialect.create_index_sql(cls.table_name(), idx, name), []
                    )
        return True

    @classmethod
    async def drop_table(cls) -> bool:
        """删表（危险操作，仅测试与显式维护场景使用）"""
        return await cls._get_storage().aDropTable(cls.table_name())

    @classmethod
    async def has_table(cls) -> bool:
        """表是否存在"""
        return await cls._get_storage().aHasTable(cls.table_name())

    # ---- CRUD：类操作 ----

    @classmethod
    def where(cls, *conditions: Condition) -> QuerySet:
        """
        条件查询入口（``User.where(User.age > 18)`` → :class:`QuerySet`）

        多条件以 AND 连接；OR 用 ``(cond1) | (cond2)`` 组合。
        """
        condition: Condition | None = None
        for cond in conditions:
            condition = cond if condition is None else condition & cond
        return QuerySet(cls, condition)

    @classmethod
    def all(cls) -> QuerySet:
        """无条件查询集（等价 ``cls.where()``）"""
        return QuerySet(cls)

    @classmethod
    async def get(cls, **eq_kwargs: Any) -> Any | None:
        """
        等值查询首条（``User.get(id=1)``）；无结果返回 None

        :raises ValueError: 条件字段未在模型中声明时
        """
        unknown = [k for k in eq_kwargs if k not in cls._fields]
        if unknown:
            raise ValueError(f"unknown fields for {cls.__name__}.get: {', '.join(sorted(unknown))}")
        condition: Condition | None = None
        for name, value in eq_kwargs.items():
            cond = ColumnExpr(name)._cond("=", value)
            condition = cond if condition is None else condition & cond
        return await QuerySet(cls, condition).first()

    @classmethod
    async def create(cls, **kwargs: Any) -> Any:
        """
        插入一行并返回实例（自增主键自动回填）

        处于 ``storage.atransaction()`` 环境事务内时，INSERT 复用事务连接，
        随事务统一提交/回滚，不独立提交。

        :raises ValueError: 约束校验失败（必填缺失 / 枚举外 / 越界 / 超长）
        """
        instance = cls(**kwargs)
        instance._validate()
        await cls._insert_and_backfill(instance)
        return instance

    @classmethod
    async def _insert_and_backfill(cls, instance: Model) -> None:
        """
        {!--< internal-use >!--}
        INSERT 一行并按需回填自增主键到实例（:meth:`create` 与 :meth:`save` 共用）

        列参数构建（自增主键交由数据库、可空/有默认字段 None 跳过、JSON 序列化）
        与连接路由在此收敛：处于环境事务内复用事务连接，否则开事务专用连接
        自管提交（自增回填要求 INSERT 与 last-id 查询同连接）。

        :param instance: 已完成约束校验的待插入实例
        """
        storage = cls._get_storage()
        dialect = storage.dialect

        cols, params = [], []
        for name, field_obj in cls._fields.items():
            value = instance.__dict__.get(name)
            # 自增主键由数据库生成；可空字段 NULL 交由数据库默认
            if field_obj.autoincrement and value is None:
                continue
            if value is None and (field_obj.nullable or field_obj.default is not _UNSET):
                continue
            cols.append(name)
            params.append(field_obj.to_db_value(value))

        quoted = [_quote_ident(c, dialect) for c in cols]
        marks = ", ".join("?" for _ in cols)
        sql = f"INSERT INTO {_quote_ident(cls.table_name(), dialect)} ({', '.join(quoted)}) VALUES ({marks})"

        pk = cls._pk_field()
        needs_backfill = (
            pk is not None
            and pk.autoincrement
            and instance.__dict__.get(pk.name) is None
        )

        if not needs_backfill or storage.dialect is None:
            await storage._execute_query("dml", sql, params)
            return

        # 自增回填：INSERT 与 last-id 查询须同连接 → 事务连接承载
        assert pk is not None  # needs_backfill 隐含主键存在
        txn = _current_txn.get()
        if txn is not None and txn.conn is not None:
            # 环境事务内：直接复用事务连接，提交/回滚归外层事务
            await storage._execute_query("dml", sql, params, conn=txn.conn)
            row, _ = await storage._execute_query(
                "one", storage.dialect.last_insert_id_sql(), [], conn=txn.conn
            )
            if row:
                setattr(instance, pk.name, row[0])
            return

        conn = await storage._acquire_txn_conn()
        try:
            await storage._begin_txn(conn)
            await storage._execute_query("dml", sql, params, conn=conn)
            row, _ = await storage._execute_query(
                "one", storage.dialect.last_insert_id_sql(), [], conn=conn
            )
            await storage._commit_txn(conn)
        except Exception:
            await storage._rollback_txn(conn)
            raise
        finally:
            await storage._release_txn_conn(conn)
        if row:
            setattr(instance, pk.name, row[0])

    @classmethod
    async def count(cls, *conditions: Condition) -> int:
        """行数统计（``await User.count(User.age > 18)``）"""
        return await QuerySet(cls, _combine(conditions)).count()

    @classmethod
    async def delete_all(cls, *conditions: Condition) -> int:
        """批量删除（``await User.delete_all(User.age > 18)``；无条件则全表删除）"""
        return await QuerySet(cls, _combine(conditions)).delete()

    @classmethod
    async def update_all(cls, *conditions: Condition, **values: Any) -> int:
        """批量更新（``await User.update_all(User.age > 18, name="adult")``）"""
        return await QuerySet(cls, _combine(conditions)).update(**values)

    # ---- CRUD：实例操作 ----

    async def save(self) -> int:
        """
        按主键更新本行（先约束校验）；主键缺失时退化为插入（自增主键同样回填到本实例）

        :return: 受影响行数
        """
        self._validate()
        pk = self._pk_field()
        if pk is None or self.__dict__.get(pk.name) is None:
            await type(self)._insert_and_backfill(self)
            return 1
        storage = self._get_storage()
        dialect = storage.dialect
        sets, params = [], []
        for name in self._fields:
            if name == pk.name:
                continue
            sets.append(f"{_quote_ident(name, dialect)} = ?")
            params.append(self._fields[name].to_db_value(self.__dict__.get(name)))
        if not sets:
            return 0
        sql = (
            f"UPDATE {_quote_ident(type(self).table_name(), dialect)} "
            f"SET {', '.join(sets)} WHERE {_quote_ident(pk.name, dialect)} = ?"
        )
        params.append(self.__dict__.get(pk.name))
        return int(await storage._execute_query("dml", sql, params))

    async def delete(self) -> int:
        """
        按主键删除本行

        :raises ValueError: 模型无主键或实例主键为空时
        :return: 受影响行数
        """
        pk = self._pk_field()
        if pk is None or self.__dict__.get(pk.name) is None:
            raise ValueError(f"{type(self).__name__} has no primary key value to delete")
        storage = self._get_storage()
        dialect = storage.dialect
        sql = (
            f"DELETE FROM {_quote_ident(type(self).table_name(), dialect)} "
            f"WHERE {_quote_ident(pk.name, dialect)} = ?"
        )
        return int(await storage._execute_query("dml", sql, [self.__dict__.get(pk.name)]))


def _combine(conditions: tuple) -> Condition | None:
    """多条件 AND 组合（类级 CRUD 快捷入口用）"""
    condition: Condition | None = None
    for cond in conditions:
        condition = cond if condition is None else condition & cond
    return condition


__all__ = ["BaseModel", "ColumnExpr", "Condition", "Field", "Model", "QuerySet"]

# 向后兼容/命名对齐别名：Bases 层 Base* 惯例
BaseModel = Model
