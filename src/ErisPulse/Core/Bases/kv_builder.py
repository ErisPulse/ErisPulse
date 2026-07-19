"""
ErisPulse KV 查询构建器

将链式 SQL 操作（Table/Insert/Select/Where 等）映射为 KV 键前缀操作。
任何实现了 BaseStorage KV 接口的后端（Redis、内存字典等）均可使用。

键命名规则：
    _table:{table_name}:schema    — 表结构定义（列名 → 类型）
    _table:{table_name}:next_id   — 自增 ID 计数器
    _table:{table_name}:data:{id} — 行数据（JSON 序列化）

使用方式：
    >>> storage = MyKVStorage()
    >>> qb = KVQueryBuilder(storage, "users")
    >>> qb.Insert({"name": "Alice", "age": 30}).Execute()

{!--< tips >!--}
1. 查询性能取决于 get_all_keys() 的效率
2. WHERE 条件在 Python 内存中过滤，不适合百万级数据
3. 适合中小规模的结构化数据存储
{!--< /tips >!--}
"""

import json
from typing import Any

from .storage import BaseQueryBuilder

_TABLE_PREFIX = "__erispulse_sql__"


class KVQueryBuilder(BaseQueryBuilder):
    """
    基于 KV 存储的查询构建器

    将 Insert/Select/Update/Delete/Where/OrderBy/Limit 等链式操作
    映射为对 BaseStorage KV 接口的调用。
    """

    def __init__(self, storage, table: str):
        super().__init__(storage, table)
        self._table_prefix = f"{_TABLE_PREFIX}:{table}"
        self._bound_clauses: list[str] | None = None

    # ---- key helpers ----

    def _schema_key(self) -> str:
        return f"{self._table_prefix}:schema"

    def _next_id_key(self) -> str:
        return f"{self._table_prefix}:next_id"

    def _row_key(self, row_id: int) -> str:
        return f"{self._table_prefix}:data:{row_id}"

    def _row_prefix(self) -> str:
        return f"{self._table_prefix}:data:"

    # ---- ID management ----

    def _get_next_id(self) -> int:
        """获取并递增自增 ID"""
        current = self._storage.get(self._next_id_key(), 1)
        next_id = int(current)
        self._storage.set(self._next_id_key(), next_id + 1)
        return next_id

    def _set_next_id(self, value: int) -> None:
        self._storage.set(self._next_id_key(), value)

    # ---- row scan ----

    def _scan_rows(self) -> list[tuple[int, dict]]:
        """扫描所有行，返回 [(row_id, row_data), ...]"""
        all_keys = self._storage.get_all_keys()
        rows = []
        for key in all_keys:
            if key.startswith(self._row_prefix()):
                try:
                    row_id = int(key.rsplit(":", 1)[-1])
                except (ValueError, IndexError):
                    continue
                value = self._storage.get(key)
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        # 兼容非 JSON 值
                        pass
                if isinstance(value, dict):
                    rows.append((row_id, value))
        return rows

    # ---- where matching ----

    def _match_row(self, row: dict) -> bool:
        """检查行是否满足所有 WHERE 条件"""
        if self._bound_clauses is None:
            self._bind_clauses()
        assert self._bound_clauses is not None
        return all(self._eval_clause(row, clause) for clause in self._bound_clauses)

    def _bind_clauses(self):
        """将 WHERE 子句中的 ? 替换为实际参数（只执行一次）"""
        self._bound_clauses = []
        params = list(self._where_params)
        for clause in self._where_clauses:
            if "?" in clause and params:
                val = params.pop(0)
                if isinstance(val, str):
                    val = f"'{val}'"
                clause = clause.replace("?", str(val), 1)
            self._bound_clauses.append(clause)

    def _eval_clause(self, row: dict, clause: str) -> bool:
        """评估单条已绑定的 WHERE 子句

        clause 中的占位符 `?` 已在 `_bind_clauses` 中替换为实际值。
        支持的操作符: =, !=, >, >=, <, <=, LIKE
        """
        parts = clause.strip().split(None, 2)
        if len(parts) < 3:
            return True

        column, op, expected = parts[0], parts[1], parts[2]

        # 去掉引号
        expected = expected.strip("'\"")

        actual = row.get(column)

        # 类型转换
        try:
            expected = self._coerce_value(expected, actual)
        except (ValueError, TypeError):
            pass

        if op == "=":
            return actual == expected
        if op == "!=":
            return actual != expected
        if op == ">":
            return self._safe_cmp(actual, expected) > 0
        if op == ">=":
            return self._safe_cmp(actual, expected) >= 0
        if op == "<":
            return self._safe_cmp(actual, expected) < 0
        if op == "<=":
            return self._safe_cmp(actual, expected) <= 0
        if op.upper() == "LIKE":
            pattern = str(expected).replace("%", ".*").replace("_", ".")
            import re
            return bool(re.match(pattern, str(actual), re.IGNORECASE))
        return True

    @staticmethod
    def _coerce_value(expected: Any, actual: Any) -> Any:
        """根据 actual 的类型，将 expected 转换为同类型"""
        if expected is None or actual is None:
            return expected
        if isinstance(actual, bool):
            return str(expected).lower() in ("true", "1", "yes")
        if isinstance(actual, int):
            return int(expected)
        if isinstance(actual, float):
            return float(expected)
        return str(expected)

    @staticmethod
    def _safe_cmp(a: Any, b: Any) -> int:
        """安全比较，处理 None"""
        if a is None and b is None:
            return 0
        if a is None:
            return -1
        if b is None:
            return 1
        try:
            if a < b:
                return -1
            if a > b:
                return 1
            return 0
        except TypeError:
            return -1 if str(a) < str(b) else 1

    # ---- Execute ----

    def Execute(self) -> list[tuple] | int:
        if self._operation == "insert":
            return self._exec_insert()
        if self._operation == "insert_multi":
            return self._exec_insert_multi()
        if self._operation == "select":
            return self._exec_select()
        if self._operation == "update":
            return self._exec_update()
        if self._operation == "delete":
            return self._exec_delete()
        raise ValueError(f"Unknown operation: {self._operation}")

    def _exec_insert(self) -> int:
        if not isinstance(self._data, dict):
            raise ValueError("Insert 操作需要字典数据")
        row_id = self._get_next_id()
        self._storage.set(self._row_key(row_id), json.dumps(self._data, ensure_ascii=False))
        return 1

    def _exec_insert_multi(self) -> int:
        if not isinstance(self._data, list):
            raise ValueError("InsertMulti 操作需要列表数据")
        count = 0
        for row in self._data:
            row_id = self._get_next_id()
            self._storage.set(self._row_key(row_id), json.dumps(row, ensure_ascii=False))
            count += 1
        return count

    def _exec_select(self) -> list[tuple]:
        rows = self._scan_rows()
        # filter
        if self._where_clauses:
            rows = [(rid, r) for rid, r in rows if self._match_row(r)]
        # order
        if self._order_by:
            for col, desc in reversed(self._order_by):
                try:
                    rows.sort(key=lambda x: x[1].get(col, ""), reverse=desc)
                except TypeError:
                    rows.sort(key=lambda x: str(x[1].get(col, "")), reverse=desc)
        # offset
        if self._offset:
            rows = rows[self._offset:]
        # limit
        if self._limit is not None:
            rows = rows[:self._limit]
        # project
        if self._columns:
            return [tuple(r.get(c) for c in self._columns) for _, r in rows]
        return [tuple(r.values()) for _, r in rows]

    def _exec_update(self) -> int:
        if not isinstance(self._data, dict):
            raise ValueError("Update 操作需要字典数据")
        count = 0
        for row_id, row in self._scan_rows():
            if self._match_row(row):
                row.update(self._data)
                self._storage.set(self._row_key(row_id), json.dumps(row, ensure_ascii=False))
                count += 1
        return count

    def _exec_delete(self) -> int:
        count = 0
        for row_id, row in self._scan_rows():
            if self._match_row(row):
                self._storage.delete(self._row_key(row_id))
                count += 1
        return count

    # ---- ExecuteOne / Count / Exists ----

    def ExecuteOne(self) -> tuple | None:
        old_limit = self._limit
        self._limit = 1
        try:
            rows = self._exec_select()
            return rows[0] if rows else None
        finally:
            self._limit = old_limit

    def Count(self) -> int:
        rows = self._scan_rows()
        if self._where_clauses:
            rows = [(rid, r) for rid, r in rows if self._match_row(r)]
        return len(rows)

    def Exists(self) -> bool:
        return self.Count() > 0

    # ==================== 异步接口 ====================

    async def _ascan_rows(self) -> list[tuple[int, dict]]:
        """异步扫描所有行"""
        all_keys = await self._storage.aget_all_keys()
        rows = []
        for key in all_keys:
            if key.startswith(self._row_prefix()):
                try:
                    row_id = int(key.rsplit(":", 1)[-1])
                except (ValueError, IndexError):
                    continue
                value = await self._storage.aget(key)
                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass
                if isinstance(value, dict):
                    rows.append((row_id, value))
        return rows

    async def aExecute(self) -> list[tuple] | int:
        """异步执行查询"""
        if self._operation == "insert":
            if not isinstance(self._data, dict):
                raise ValueError("Insert 操作需要字典数据")
            row_id = self._get_next_id()
            await self._storage.aset(self._row_key(row_id), json.dumps(self._data, ensure_ascii=False))
            return 1
        if self._operation == "insert_multi":
            if not isinstance(self._data, list):
                raise ValueError("InsertMulti 操作需要列表数据")
            count = 0
            for row in self._data:
                row_id = self._get_next_id()
                await self._storage.aset(self._row_key(row_id), json.dumps(row, ensure_ascii=False))
                count += 1
            return count
        if self._operation == "select":
            return await self._aexec_select()
        if self._operation == "update":
            if not isinstance(self._data, dict):
                raise ValueError("Update 操作需要字典数据")
            count = 0
            for row_id, row in await self._ascan_rows():
                if self._match_row(row):
                    row.update(self._data)
                    await self._storage.aset(self._row_key(row_id), json.dumps(row, ensure_ascii=False))
                    count += 1
            return count
        if self._operation == "delete":
            count = 0
            for row_id, row in await self._ascan_rows():
                if self._match_row(row):
                    await self._storage.adelete(self._row_key(row_id))
                    count += 1
            return count
        raise ValueError(f"Unknown operation: {self._operation}")

    async def _aexec_select(self) -> list[tuple]:
        rows = await self._ascan_rows()
        if self._where_clauses:
            rows = [(rid, r) for rid, r in rows if self._match_row(r)]
        if self._order_by:
            for col, desc in reversed(self._order_by):
                try:
                    rows.sort(key=lambda x: x[1].get(col, ""), reverse=desc)
                except TypeError:
                    rows.sort(key=lambda x: str(x[1].get(col, "")), reverse=desc)
        if self._offset:
            rows = rows[self._offset:]
        if self._limit is not None:
            rows = rows[:self._limit]
        if self._columns:
            return [tuple(r.get(c) for c in self._columns) for _, r in rows]
        return [tuple(r.values()) for _, r in rows]

    async def aExecuteOne(self) -> tuple | None:
        old_limit = self._limit
        self._limit = 1
        try:
            rows = await self._aexec_select()
            return rows[0] if rows else None
        finally:
            self._limit = old_limit

    async def aCount(self) -> int:
        rows = await self._ascan_rows()
        if self._where_clauses:
            rows = [(rid, r) for rid, r in rows if self._match_row(r)]
        return len(rows)

    async def aExists(self) -> bool:
        return await self.aCount() > 0
