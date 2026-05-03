"""
ErisPulse 存储基类

提供存储后端和查询构建器的抽象接口，支持不同存储介质的统一访问

{!--< tips >!--}
1. BaseStorage 定义了键值存储和表管理的标准接口
2. BaseQueryBuilder 定义了链式查询构建的标准接口
3. 具体存储后端（如 SQLite、Redis、MySQL）需继承并实现这些接口
{!--< /tips >!--}
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseQueryBuilder(ABC):
    """
    查询构建器抽象基类

    定义链式调用风格的查询构建接口，所有链式方法返回 self，
    终止方法（Execute、ExecuteOne、Count、Exists）返回实际结果。

    {!--< tips >!--}
    使用方式：
    1. storage.Table("users").Insert({"name": "Alice"}).Execute()
    2. storage.Table("users").Select("name").Where("age > ?", 18).Limit(10).Execute()
    {!--< /tips >!--}
    """

    def __init__(self, storage: "BaseStorage", table: str):
        self._storage = storage
        self._table = table
        self._operation: str | None = None
        self._columns: list[str] = []
        self._data: dict[str, Any] | list[dict[str, Any]] | None = None
        self._where_clauses: list[str] = []
        self._where_params: list[Any] = []
        self._order_by: list[tuple[str, bool]] = []
        self._limit: int | None = None
        self._offset: int | None = None

    def Select(self, *columns: str) -> "BaseQueryBuilder":
        """
        指定查询列

        :param columns: 列名列表，为空时表示 SELECT *
        :return: self

        :example:
        >>> storage.Table("users").Select("name", "age").Execute()
        """
        self._operation = "select"
        self._columns = list(columns)
        return self

    def Insert(self, data: dict[str, Any]) -> "BaseQueryBuilder":
        """
        插入一行数据

        :param data: 列名到值的映射
        :return: self

        :example:
        >>> storage.Table("users").Insert({"name": "Alice", "age": 30}).Execute()
        """
        self._operation = "insert"
        self._data = data
        return self

    def InsertMulti(self, data: list[dict[str, Any]]) -> "BaseQueryBuilder":
        """
        批量插入多行数据

        :param data: 列名到值的映射列表
        :return: self

        :example:
        >>> storage.Table("users").InsertMulti([
        ...     {"name": "Alice", "age": 30},
        ...     {"name": "Bob", "age": 25}
        ... ]).Execute()
        """
        self._operation = "insert_multi"
        self._data = data
        return self

    def Update(self, data: dict[str, Any]) -> "BaseQueryBuilder":
        """
        更新数据

        :param data: 列名到新值的映射
        :return: self

        :example:
        >>> storage.Table("users").Update({"age": 31}).Where("name = ?", "Alice").Execute()
        """
        self._operation = "update"
        self._data = data
        return self

    def Delete(self) -> "BaseQueryBuilder":
        """
        删除行

        :return: self

        :example:
        >>> storage.Table("users").Delete().Where("name = ?", "Bob").Execute()
        """
        self._operation = "delete"
        return self

    def Where(self, condition: str, *params: Any) -> "BaseQueryBuilder":
        """
        添加 WHERE 条件

        多次调用时条件之间以 AND 连接

        :param condition: 条件表达式（使用占位符，如 "age > ?"）
        :param params: 占位符对应的参数值
        :return: self

        :example:
        >>> storage.Table("users").Where("age > ?", 18).Where("name LIKE ?", "A%").Execute()
        """
        self._where_clauses.append(condition)
        self._where_params.extend(params)
        return self

    def OrderBy(self, column: str, desc: bool = False) -> "BaseQueryBuilder":
        """
        添加排序规则

        多次调用时按添加顺序组合 ORDER BY

        :param column: 排序列名
        :param desc: 是否降序（默认升序）
        :return: self

        :example:
        >>> storage.Table("users").OrderBy("age", desc=True).OrderBy("name").Execute()
        """
        self._order_by.append((column, desc))
        return self

    def Limit(self, count: int) -> "BaseQueryBuilder":
        """
        限制返回条数

        :param count: 最大返回条数
        :return: self

        :example:
        >>> storage.Table("users").Limit(10).Execute()
        """
        self._limit = count
        return self

    def Offset(self, count: int) -> "BaseQueryBuilder":
        """
        设置偏移量

        :param count: 跳过的条数
        :return: self

        :example:
        >>> storage.Table("users").Limit(10).Offset(20).Execute()
        """
        self._offset = count
        return self

    def copy(self) -> "BaseQueryBuilder":
        """
        深拷贝当前构建器状态

        :return: 新的构建器实例
        """
        new = self.__class__(self._storage, self._table)
        new._operation = self._operation
        new._columns = list(self._columns)
        new._data = (
            dict(self._data) if isinstance(self._data, dict)
            else [dict(d) for d in self._data] if isinstance(self._data, list)
            else None
        )
        new._where_clauses = list(self._where_clauses)
        new._where_params = list(self._where_params)
        new._order_by = list(self._order_by)
        new._limit = self._limit
        new._offset = self._offset
        return new

    def clear(self) -> "BaseQueryBuilder":
        """
        重置构建器状态

        :return: self
        """
        self._operation = None
        self._columns = []
        self._data = None
        self._where_clauses = []
        self._where_params = []
        self._order_by = []
        self._limit = None
        self._offset = None
        return self

    @abstractmethod
    def Execute(self) -> list[tuple] | int:
        """
        执行构建的查询

        - SELECT 返回 list[tuple]
        - INSERT/UPDATE/DELETE 返回受影响行数 int

        :return: 查询结果或受影响行数
        """
        ...

    @abstractmethod
    def ExecuteOne(self) -> tuple | None:
        """
        执行查询并返回单条结果

        :return: 单行元组或 None
        """
        ...

    @abstractmethod
    def Count(self) -> int:
        """
        执行 COUNT 查询

        :return: 匹配的行数
        """
        ...

    @abstractmethod
    def Exists(self) -> bool:
        """
        检查是否存在匹配的记录

        :return: 是否存在
        """
        ...

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(table={self._table!r}, op={self._operation!r})"
        )


class BaseStorage(ABC):
    """
    存储后端抽象基类

    定义键值存储和表管理的统一接口，所有存储后端必须继承并实现此基类。

    {!--< tips >!--}
    1. 键值操作（get/set/delete）用于简单数据存取
    2. Table/CreateTable/DropTable 用于结构化数据操作
    3. transaction 提供事务支持
    {!--< /tips >!--}
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取存储项的值

        :param key: 存储项键名
        :param default: 默认值
        :return: 存储项的值
        """
        ...

    @abstractmethod
    def set(self, key: str, value: Any) -> bool:
        """
        设置存储项的值

        :param key: 存储项键名
        :param value: 存储项的值
        :return: 操作是否成功
        """
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除存储项

        :param key: 存储项键名
        :return: 操作是否成功
        """
        ...

    @abstractmethod
    def get_all_keys(self) -> list[str]:
        """
        获取所有存储项的键名

        :return: 键名列表
        """
        ...

    @abstractmethod
    def clear(self) -> bool:
        """
        清空所有存储项

        :return: 操作是否成功
        """
        ...

    @abstractmethod
    def transaction(self) -> Any:
        """
        创建事务上下文

        :return: 事务上下文管理器
        """
        ...

    @abstractmethod
    def Table(self, table_name: str) -> BaseQueryBuilder:
        """
        获取指定表的查询构建器

        :param table_name: 表名
        :return: 查询构建器实例
        """
        ...

    @abstractmethod
    def CreateTable(self, table_name: str, columns: dict[str, str]) -> bool:
        """
        创建表

        :param table_name: 表名
        :param columns: 列名到类型的映射（如 {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}）
        :return: 操作是否成功
        """
        ...

    @abstractmethod
    def DropTable(self, table_name: str) -> bool:
        """
        删除表

        :param table_name: 表名
        :return: 操作是否成功
        """
        ...

    @abstractmethod
    def HasTable(self, table_name: str) -> bool:
        """
        检查表是否存在

        :param table_name: 表名
        :return: 是否存在
        """
        ...

    def get_multi(self, keys: list[str]) -> dict[str, Any]:
        """
        批量获取多个存储项的值

        :param keys: 键名列表
        :return: 键值对字典
        """
        results = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                results[key] = value
        return results

    def set_multi(self, items: dict[str, Any]) -> bool:
        """
        批量设置多个存储项

        :param items: 键值对字典
        :return: 操作是否成功
        """
        for key, value in items.items():
            if not self.set(key, value):
                return False
        return True

    def delete_multi(self, keys: list[str]) -> bool:
        """
        批量删除多个存储项

        :param keys: 键名列表
        :return: 操作是否成功
        """
        for key in keys:
            if not self.delete(key):
                return False
        return True

    def keys(self) -> list[str]:
        """
        获取所有存储项的键名（代理到 get_all_keys）

        :return: 键名列表
        """
        return self.get_all_keys()

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_"):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{key}'"
            )
        value = self.get(key)
        if value is None:
            raise AttributeError(f"存储项 {key} 不存在")
        return value

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_"):
            super().__setattr__(key, value)
            return
        try:
            self.set(key, value)
        except Exception:
            super().__setattr__(key, value)


__all__ = [
    "BaseStorage",
    "BaseQueryBuilder",
]
