"""
ErisPulse API 文档生成器

从Python源代码自动生成API文档

特性：
- 解析 Python 源码的 docstring 生成 Markdown 文档
- 支持 ``:param`` / ``:return`` / ``:raises`` / ``:example`` 等标记
- 示例块（``:example:`` 标签或裸 ``>>>`` doctest）自动剥离 ``>>>`` / ``...``
  前缀渲染为 ``python`` 代码块，并收入预期输出行
- ``.. code-block:: <lang>`` 指令与行尾 ``::`` 字面块自动转为围栏代码块
- 支持嵌套类与方法的递归提取，签名含全部参数形态（``/``、``*args``、
  仅关键字参数、``**kwargs``）与返回值注解，标注 property / staticmethod /
  classmethod 装饰器
- 支持多语言同步生成与复制

使用方法:
    python scripts/tools/generate-api-docs.py
    python scripts/tools/generate-api-docs.py --lang en
    python scripts/tools/generate-api-docs.py --src src --output docs/api-reference/auto_api
"""

import argparse
import ast
import os
import re
import shutil
import textwrap
from pathlib import Path
from typing import Any

from _common import Logger  # scripts/tools 公共日志器

# 首词形似类型标识：ASCII 标识符 / 点路径 / 下标泛型 / 管道联合（如 ``dict[str, Any]``、``str | None``）
_TYPE_TOKEN_RE = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*(?:\[[^\]\n]*\])?"
    r"(?:[ \t]*\|[ \t]*[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*(?:\[[^\]\n]*\])?)*"
)
_CJK_FIRST_RE = re.compile(r"[\u4e00-\u9fff]")
# True/False/None 是值字面量而非类型（如 ":return: True 表示已拦截"）
_VALUE_LITERALS = {"True", "False", "None"}


def _split_type_desc(desc: str) -> tuple[str | None, str]:
    """
    尝试将 "类型 描述" 形态的字段说明拆分为 (类型, 描述)

    仅当首词形似类型标识（含点路径、下标泛型、管道联合）且其余部分以中文开头
    时才认定为类型，避免把纯中文描述（"初始化前回调"）或英文句子
    （"event data"）误判为类型。``True`` / ``False`` / ``None`` 是值字面量，
    永远不作为类型回显。

    :param desc: 字段说明文本（单行）
    :return: (类型或 None, 描述)
    """
    text = desc.strip()
    if not text:
        return None, text
    m = _TYPE_TOKEN_RE.match(text)
    if not m:
        return None, text
    token, rest = m.group(0), text[m.end():].lstrip()
    if token in _VALUE_LITERALS or not rest or not _CJK_FIRST_RE.match(rest):
        return None, text
    return token, rest


def _strip_doctest_prefix(line: str) -> str:
    """
    剥离一行 doctest 前缀（``>>> `` / ``... ``），保留源码本身的缩进

    :param line: 已去除公共缩进的单行示例代码
    :return: 去除前缀后的代码行；裸前缀行（``>>>`` / ``...``）转为空行
    """
    for prefix in (">>> ", "... "):
        if line.startswith(prefix):
            return line[len(prefix):]
    if line in (">>>", "..."):
        return ""
    return line


def _convert_field_line(line: str) -> str | None:
    """
    将单行 ``:param`` / ``:return`` / ``:raises`` 字段标记转换为 Markdown 行

    匹配严格限定在本行内（不使用可跨行的 ``\\s``），避免把相邻字段的说明
    粘连到同一条目上。

    :param line: 单行文本
    :return: 转换后的 Markdown 行；非字段行返回 None
    """
    m = re.match(r"\s*:param (\w+):[ \t]*\[([^\]]+)\][ \t]*(.*)$", line)
    if m:
        return f"- **{m.group(1)}** (`{m.group(2)}`): {m.group(3)}".rstrip()

    m = re.match(r"\s*:param (\w+):[ \t]*(.*)$", line)
    if m:
        typ, desc = _split_type_desc(m.group(2))
        if typ:
            return f"- **{m.group(1)}** (`{typ}`): {desc}"
        return f"- **{m.group(1)}**: {desc}".rstrip()

    m = re.match(r"\s*:return:[ \t]*\[([^\]]+)\][ \t]*(.*)$", line)
    if m:
        return f"**返回值** (`{m.group(1)}`): {m.group(2)}".rstrip()

    m = re.match(r"\s*:return:[ \t]*(.*)$", line)
    if m:
        typ, desc = _split_type_desc(m.group(1))
        if typ:
            return f"**返回值** (`{typ}`): {desc}"
        return f"**返回值**: {desc}".rstrip()

    m = re.match(r"\s*:raises (\S+):[ \t]*(.*)$", line)
    if m:
        return f"**异常**: `{m.group(1)}` - {m.group(2)}".rstrip()

    return None


def _process_doc_lines(lines: list[str], quote: str = "", strip_plain: bool = False) -> list[str]:
    """
    将 docstring 行列表逐行转换为 Markdown 行列表（核心转换循环）

    处理顺序：既有 ``` 围栏原样透传 → 提示块递归转换 → 单行特殊标签 →
    ``:example:`` 标签 → ``.. code-block::`` 指令 → 行尾 ``::`` 字面块 →
    doctest 示例运行 → 多行/单行字段标记 → 普通行。

    :param lines: 已去除公共缩进的 docstring 行列表
    :param quote: 每行输出前缀（提示块内部使用 ``> ``）
    :param strip_plain: 是否去除普通行的缩进并跳过空行（提示块内部为 True）
    :return: Markdown 行列表
    """
    out: list[str] = []
    in_fence = False
    i, n = 0, len(lines)

    def emit(text: str) -> None:
        out.append(quote + text if quote else text)

    def emit_blank() -> None:
        out.append(quote.rstrip() if quote else "")

    def emit_code_block(block: list[str], lang: str = "") -> None:
        emit(f"```{lang}")
        code = [_strip_doctest_prefix(block_line) for block_line in block]
        while code and not code[-1].strip():
            code.pop()
        for code_line in code:
            emit(code_line)
        emit("```")
        emit_blank()

    def consume_indented(start: int, base_indent: int) -> tuple[list[str], int]:
        """收集 start 起缩进深于 base_indent 的连续块（空行归属其中），返回去公共缩进的行与停止下标"""
        raw: list[str] = []
        j = start
        while j < n:
            cur = lines[j]
            if not cur.strip():
                raw.append("")
                j += 1
                continue
            if len(cur) - len(cur.lstrip()) <= base_indent:
                break
            raw.append(cur)
            j += 1
        if not any(bl.strip() for bl in raw):
            return [], j
        dedented = textwrap.dedent("\n".join(raw)).split("\n")
        while dedented and not dedented[0].strip():
            dedented.pop(0)
        while dedented and not dedented[-1].strip():
            dedented.pop()
        return dedented, j

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 既有代码围栏：整体原样透传，内部不做任何转换
        if "```" in line:
            in_fence = not in_fence
            emit(line)
            i += 1
            continue
        if in_fence:
            emit(line)
            i += 1
            continue

        # 提示块：收集到结束标签后按引用块递归转换（内部示例/代码块同样生效）
        if "{!--< tips >!--}" in line:
            body = [line.split("{!--< tips >!--}")[-1]]
            i += 1
            while i < n and "{!--< /tips >!--}" not in lines[i]:
                body.append(lines[i])
                i += 1
            if i < n:
                body.append(lines[i].split("{!--< /tips >!--}")[0])
                i += 1
            inner_quote = (quote + "> ") if quote else "> "
            out.append(f"{inner_quote}**提示**")
            out.extend(_process_doc_lines(body, quote=inner_quote, strip_plain=True))
            emit_blank()
            continue

        # 单行特殊标签
        if "{!--< internal-use >!--}" in line:
            emit(f"**内部方法** {line.split('{!--< internal-use >!--}')[-1].strip()}".rstrip())
            i += 1
            continue
        if "{!--< deprecated >!--}" in line:
            emit(f"**已弃用** {line.split('{!--< deprecated >!--}')[-1].strip()}".rstrip())
            i += 1
            continue
        if "{!--< experimental >!--}" in line:
            emit(f"**实验性功能** {line.split('{!--< experimental >!--}')[-1].strip()}".rstrip())
            i += 1
            continue
        # 其余未知标签行直接跳过
        if "{!--<" in line and ">!--}" in line:
            i += 1
            continue

        # :example: 标签 → 示例标题
        if re.match(r"^\s*:example:\s*$", line):
            emit("**示例**:")
            emit_blank()
            i += 1
            continue

        # .. code-block:: <lang> 指令 → 围栏代码块
        m = re.match(r"^(\s*)\.\.[ \t]+code-block::[ \t]*(\S*)[ \t]*$", line)
        if m:
            block, j = consume_indented(i + 1, len(m.group(1)))
            if block:
                emit_code_block(block, m.group(2))
                i = j
                continue

        # 行尾 ``::`` 字面块（reST 风格，标签不含冒号才认定）→ 围栏代码块
        m = re.match(r"^(\s*)([^:]+)::[ \t]*$", line)
        if m:
            block, j = consume_indented(i + 1, len(m.group(1)))
            if block:
                emit(m.group(2).rstrip() + ":")
                emit_code_block(block)
                i = j
                continue

        # doctest 示例运行：连续的 >>> / ... 前缀行，紧随 >>> 语句行的
        # 非前缀非空行视为预期输出一并收入；空行、标签行、围栏行终止运行
        if stripped.startswith((">>>", "...")):
            run: list[str] = []
            j = i
            while j < n:
                cur = lines[j]
                cur_stripped = cur.strip()
                if not cur_stripped or "{!--<" in cur_stripped or "```" in cur_stripped:
                    break
                if cur_stripped.startswith((">>>", "...")):
                    run.append(cur)
                    j += 1
                    continue
                # 非前缀非空行视为预期输出：紧随 >>> 语句行，或处于连续输出中
                if run and not run[-1].strip().startswith("..."):
                    run.append(cur)
                    j += 1
                    continue
                break
            dedented = textwrap.dedent("\n".join(run)).split("\n")
            code = [_strip_doctest_prefix(run_line) for run_line in dedented]
            while code and not code[-1].strip():
                code.pop()
            if code:
                emit_code_block(code, "python")
            i = j
            continue

        # 多行 :return: 字典式说明（``:return:`` 后跟缩进的 ``键: 值`` 行）
        if re.match(r"^\s*:return:[ \t]*$", line):
            j = i + 1
            entries = []
            while j < n and lines[j].strip() and re.match(r"^\s+\S+:", lines[j]):
                entries.append(lines[j].strip())
                j += 1
            if entries:
                emit("**返回值**:")
                for entry in entries:
                    key, _, val = entry.partition(":")
                    emit(f"- `{key.strip()}`: {val.strip()}")
                i = j
                continue

        # :param / :return / :raises 单行字段标记
        converted = _convert_field_line(line)
        if converted is not None:
            emit(converted)
            i += 1
            continue

        # 普通行
        if strip_plain:
            if stripped:
                emit(stripped)
        else:
            emit(line)
        i += 1

    # 字段条目组结束后补空行，避免 Markdown 惰性续行把后续说明并入最后一个条目
    # （相邻参数条目之间不插，保持列表紧凑）
    field_prefixes = ("- **", "**返回值**", "**异常**")
    blank = quote.rstrip() if quote else ""
    padded: list[str] = []
    for idx, out_line in enumerate(out):
        padded.append(out_line)
        nxt = out[idx + 1] if idx + 1 < len(out) else None
        if (nxt and out_line.startswith(field_prefixes) and nxt.strip()
                and not (out_line.startswith("- **") and nxt.startswith("- **"))):
            padded.append(blank)
    return padded


def process_docstring_for_markdown(docstring: str | None) -> str | None:
    """
    将文档字符串转换为纯 Markdown 格式

    支持的 docstring 约定：
    - 字段标记：``:param`` / ``:return`` / ``:raises``（说明首词形似类型标识
      且后接中文时才回显为类型，如 ``dict 配置字典`` → ``dict``）
    - 示例：``:example:`` 标签或裸 ``>>>`` doctest 块，自动剥离 ``>>>`` /
      ``...`` 前缀渲染为 ``python`` 代码块；``>>>`` 行后紧跟的非前缀行视为
      预期输出一并收入代码块
    - 代码块：既有 ```` ``` ```` 围栏原样保留；``.. code-block:: <lang>`` 指令
      与行尾 ``::`` 字面块（后接缩进行）自动转为围栏代码块
    - 特殊标签：``{!--< ignore >!--}``（整个 docstring 不生成文档）、
      ``{!--< internal-use >!--}``、``{!--< deprecated >!--}``、
      ``{!--< experimental >!--}``、``{!--< tips >!--}...{!--< /tips >!--}``
      （引用块，内部示例与代码块同样转换）

    :param docstring: 原始文档字符串
    :return: Markdown格式的文档字符串或None（如果包含忽略标签）
    """
    if not docstring:
        return None
    if "{!--< ignore >!--}" in docstring:
        return None

    result = _process_doc_lines(docstring.split("\n"))
    processed = "\n".join(result)

    # 清理多余的空行
    processed = re.sub(r"\n{3,}", "\n\n", processed.strip())

    return processed or None


def _decorator_tag(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """
    识别函数的显著装饰器（property / staticmethod / classmethod）

    :param node: 函数 AST 节点
    :return: 装饰器名称；无则返回空串
    """
    for dec in node.decorator_list:
        name = ast.unparse(dec)
        if name in ("property", "staticmethod", "classmethod"):
            return name
    return ""


def _format_signature(node: ast.FunctionDef | ast.AsyncFunctionDef, is_method: bool) -> str:
    """
    依据 AST 生成完整函数签名

    覆盖位置仅限参数（``/``）、可变位置参数（``*args``）、仅关键字参数与
    可变关键字参数（``**kwargs``），并附带返回值注解；``property`` 装饰的
    方法按属性形态展示（不带调用括号）。

    :param node: 函数 AST 节点
    :param is_method: 是否为类方法（跳过首个 ``self`` / ``cls`` 参数）
    :return: 签名字符串，异步函数带 ``async`` 前缀
    """
    arguments = node.args

    def render(arg: ast.arg, default: ast.expr | None) -> str:
        text = arg.arg
        if arg.annotation is not None:
            text += f": {ast.unparse(arg.annotation)}"
        if default is not None:
            text += f" = {ast.unparse(default)}"
        return text

    positional = list(arguments.posonlyargs) + list(arguments.args)
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(arguments.defaults)) + list(arguments.defaults)
    start = 1 if is_method and positional and positional[0].arg in ("self", "cls") else 0

    parts = []
    for idx in range(start, len(positional)):
        parts.append(render(positional[idx], defaults[idx]))
        if arguments.posonlyargs and idx == len(arguments.posonlyargs) - 1:
            parts.append("/")

    if arguments.vararg is not None:
        vararg = f"*{arguments.vararg.arg}"
        if arguments.vararg.annotation is not None:
            vararg += f": {ast.unparse(arguments.vararg.annotation)}"
        parts.append(vararg)
    elif arguments.kwonlyargs:
        parts.append("*")

    for arg, default in zip(arguments.kwonlyargs, arguments.kw_defaults):
        parts.append(render(arg, default))

    if arguments.kwarg is not None:
        kwarg = f"**{arguments.kwarg.arg}"
        if arguments.kwarg.annotation is not None:
            kwarg += f": {ast.unparse(arguments.kwarg.annotation)}"
        parts.append(kwarg)

    if _decorator_tag(node) == "property":
        signature = node.name
    else:
        signature = f"{node.name}({', '.join(parts)})"

    if node.returns is not None:
        signature = f"{signature} -> {ast.unparse(node.returns)}"
    if isinstance(node, ast.AsyncFunctionDef):
        signature = f"async {signature}"
    return signature


def extract_class_info(class_node: ast.ClassDef, is_nested: bool = False) -> dict[str, Any]:
    """
    提取类的信息，包括嵌套类

    :param class_node: AST类节点
    :param is_nested: 是否为嵌套类
    :return: 类信息字典
    """
    class_doc = ast.get_docstring(class_node)

    methods = []
    nested_classes = []

    # 提取类方法和嵌套类
    for item in class_node.body:
        # 提取方法
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_doc = ast.get_docstring(item)

            if method_doc:  # 只有方法有文档才添加
                methods.append({
                    "name": item.name,
                    "signature": _format_signature(item, is_method=True),
                    "decorator": _decorator_tag(item),
                    "doc": method_doc,
                    "is_async": isinstance(item, ast.AsyncFunctionDef)
                })

        # 递归提取嵌套类
        elif isinstance(item, ast.ClassDef):
            nested_class_info = extract_class_info(item, is_nested=True)
            # 只添加有文档或方法/嵌套类的嵌套类
            if nested_class_info["doc"] or nested_class_info["methods"] or nested_class_info.get("nested_classes"):
                nested_classes.append(nested_class_info)

    # 获取类签名
    bases = [ast.unparse(base) for base in class_node.bases] if class_node.bases else []
    class_signature = f"class {class_node.name}({', '.join(bases)})" if bases else f"class {class_node.name}"

    return {
        "name": class_node.name,
        "signature": class_signature,
        "doc": class_doc,
        "methods": methods,
        "nested_classes": nested_classes,
        "is_nested": is_nested
    }


def parse_python_file(file_path: str) -> tuple[str | None, list[dict[str, Any]], list[dict[str, Any]]]:
    """
    解析Python文件，提取模块文档、类和函数信息

    :param file_path: Python文件路径
    :return: (模块文档, 类列表, 函数列表)
    """
    with open(file_path, encoding="utf-8") as f:
        source = f.read()

    try:
        module = ast.parse(source)
    except SyntaxError:
        Logger.log(f"  [FAIL] {file_path}  语法错误")
        return None, [], []

    # 提取模块文档
    module_doc = ast.get_docstring(module)

    classes = []
    functions = []

    # 遍历AST节点
    for node in module.body:
        # 处理类定义
        if isinstance(node, ast.ClassDef):
            class_info = extract_class_info(node, is_nested=False)

            # 只有类有文档或者有方法或嵌套类时才添加类
            if class_info["doc"] or class_info["methods"] or class_info.get("nested_classes"):
                classes.append(class_info)

        # 处理函数定义
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_doc = ast.get_docstring(node)

            if func_doc:
                functions.append({
                    "name": node.name,
                    "signature": _format_signature(node, is_method=False),
                    "decorator": _decorator_tag(node),
                    "doc": func_doc,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })

    return module_doc, classes, functions


def generate_class_markdown(cls: dict[str, Any], base_heading_level: int = 3) -> str:
    """
    生成类的Markdown文档，包括嵌套类

    :param cls: 类信息字典
    :param base_heading_level: 基础标题级别
    :return: Markdown格式的类文档字符串
    """
    content = []

    # 处理类文档
    processed_class_doc = process_docstring_for_markdown(cls["doc"]) if cls["doc"] else None
    class_doc = processed_class_doc or f"{cls['name']} 类提供相关功能。"

    # 类标题
    heading_prefix = "#" * base_heading_level
    content.append(f"""{heading_prefix} `{cls['signature']}`

{class_doc}

""")

    # 嵌套类（在方法之前显示）
    if cls.get("nested_classes"):
        nested_heading_level = base_heading_level + 1
        nested_heading_prefix = "#" * nested_heading_level
        content.append(f"{nested_heading_prefix} 嵌套类\n\n")

        for nested_cls in cls["nested_classes"]:
            # 递归生成嵌套类文档
            nested_content = generate_class_markdown(nested_cls, nested_heading_level + 1)
            content.append(nested_content)

    # 类方法
    if cls["methods"]:
        methods_heading_level = base_heading_level + 1
        methods_heading_prefix = "#" * methods_heading_level
        content.append(f"{methods_heading_prefix} 方法列表\n\n")

        for method in cls["methods"]:
            # signature 已包含 async 前缀与返回值注解，无需重复添加
            processed_doc = process_docstring_for_markdown(method["doc"])
            decorator = method.get("decorator", "")
            decorator_suffix = f"（{decorator}）" if decorator else ""

            method_heading_level = methods_heading_level + 1
            method_heading_prefix = "#" * method_heading_level
            content.append(f"""{method_heading_prefix} `{method['signature']}`{decorator_suffix}

{processed_doc}

---

""")

    return "\n".join(content)


def generate_markdown(module_path: str, module_doc: str | None,
                     classes: list[dict[str, Any]], functions: list[dict[str, Any]]) -> str:
    """
    生成Markdown格式API文档

    :param module_path: 模块路径（点分隔）
    :param module_doc: 模块文档
    :param classes: 类信息列表
    :param functions: 函数信息列表
    :return: Markdown格式的文档字符串
    """
    content = []

    # 处理模块文档
    processed_module_doc = process_docstring_for_markdown(module_doc) if module_doc else None

    # 文档头部
    content.append(f"""# `{module_path}` 模块

---

## 模块概述

""")

    # 模块文档
    if processed_module_doc:
        content.append(f"{processed_module_doc}\n\n---\n")
    else:
        content.append("该模块暂无概述信息。\n\n---\n")

    # 函数部分
    if functions:
        content.append("## 函数列表\n\n")
        for func in functions:
            # signature 已包含 async 前缀与返回值注解，无需重复添加
            processed_doc = process_docstring_for_markdown(func["doc"])
            decorator = func.get("decorator", "")
            decorator_suffix = f"（{decorator}）" if decorator else ""

            content.append(f"""### `{func['signature']}`{decorator_suffix}

{processed_doc}

---

""")

    # 类部分
    if classes:
        content.append("## 类列表\n\n")
        for cls in classes:
            # 使用辅助函数生成类文档（包括嵌套类）
            class_content = generate_class_markdown(cls, base_heading_level=3)
            content.append(class_content)

    return "\n".join(content)


def count_nested_classes(classes: list[dict[str, Any]]) -> int:
    """
    递归统计嵌套类数量

    :param classes: 类列表
    :return: 嵌套类总数
    """
    count = 0
    for cls in classes:
        nested_classes = cls.get('nested_classes', [])
        if nested_classes:
            count += len(nested_classes)
            # 递归统计更深层的嵌套类
            count += count_nested_classes(nested_classes)
    return count


def count_all_methods(classes: list[dict[str, Any]]) -> int:
    """
    递归统计所有类的方法数量（包括嵌套类）

    :param classes: 类列表
    :return: 方法总数
    """
    count = 0
    for cls in classes:
        count += len(cls.get('methods', []))
        # 递归统计嵌套类的方法
        nested_classes = cls.get('nested_classes', [])
        if nested_classes:
            count += count_all_methods(nested_classes)
    return count


def generate_index_markdown(modules_info: dict[str, dict[str, Any]]) -> str:
    """
    生成API文档索引页

    :param modules_info: 模块信息字典
    :return: Markdown格式的索引文档字符串
    """
    content = []

    # 统计信息（包括类的方法和嵌套类）
    total_modules = len(modules_info)
    total_classes = sum(len(info.get('classes', [])) for info in modules_info.values())
    total_functions = sum(len(info.get('functions', [])) for info in modules_info.values())
    # 统计所有类的方法（包括嵌套类）
    total_methods = sum(count_all_methods(info.get('classes', [])) for info in modules_info.values())
    # 统计所有嵌套类
    total_nested_classes = sum(count_nested_classes(info.get('classes', [])) for info in modules_info.values())

    content.append(f"""# ErisPulse API 文档

---

## 概述

本文档包含 ErisPulse SDK 的所有 API 参考文档。

> **重要说明**
> 本目录下的所有文档均为**自动生成**的 API 参考文档。
> 
> **请不要手动编辑此目录下的任何文件**，所有更改将在下次自动生成时被覆盖。
> 
> 如需修改 API 文档，请在源代码中更新对应模块、类和函数的 docstring。
> 
> 自动生成脚本位置：`scripts/tools/generate-api-docs.py`

---

## 统计信息

- **模块总数**: {total_modules}
- **类总数**: {total_classes}（包括 {total_nested_classes} 个嵌套类）
- **函数总数**: {total_functions}
- **方法总数**: {total_methods}

---

## 模块列表

""")

    # 按模块路径排序
    sorted_modules = sorted(modules_info.keys())

    for module_path in sorted_modules:
        info = modules_info[module_path]
        classes = info.get('classes', [])
        functions = info.get('functions', [])

        # 计算类的方法总数
        methods_count = sum(len(cls.get('methods', [])) for cls in classes)

        # 计算相对路径
        md_path = module_path.replace('.', '/') + '.md'

        # 统计标识
        badges = []
        if classes:
            badges.append(f"{len(classes)} 个类")
        if methods_count > 0:
            badges.append(f"{methods_count} 个方法")
        if functions:
            badges.append(f"{len(functions)} 个函数")
        badge_str = ' | '.join(badges) if badges else "模块文档"

        content.append(f"""### [{module_path}]({md_path})

{badge_str}

""")

    return "\n".join(content)


def generate_api_docs(src_dir: str, output_dir: str) -> dict[str, dict[str, Any]]:
    """
    生成API文档

    每次生成前会清理输出目录中的所有旧 Markdown 文件，
    确保没有因源码重命名/删除而残留的陈旧文档。

    :param src_dir: 源代码目录
    :param output_dir: Markdown输出目录
    :return: 模块信息字典
    """
    # 清理旧的 Markdown 文件（避免源码重命名后残留陈旧文档）
    if os.path.isdir(output_dir):
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        rel = os.path.relpath(file_path, output_dir).replace(os.sep, "/")
                        Logger.log(f"  [CLEAN] {rel}")
                    except OSError:
                        pass

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    modules_info = {}

    # 遍历源代码目录
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)

                # 计算模块路径
                rel_path = os.path.relpath(file_path, src_dir)
                module_path = rel_path.replace(".py", "").replace(os.sep, ".")

                # 解析Python文件
                module_doc, classes, functions = parse_python_file(file_path)

                # 跳过没有文档的文件
                if not module_doc and not classes and not functions:
                    continue

                # 保存模块信息
                modules_info[module_path] = {
                    "classes": classes,
                    "functions": functions
                }

                # 生成Markdown
                md_content = generate_markdown(module_path, module_doc, classes, functions)
                md_output_path = os.path.join(output_dir, f"{module_path.replace('.', '/')}.md")
                os.makedirs(os.path.dirname(md_output_path), exist_ok=True)

                with open(md_output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                Logger.log(f"  [GEN] {module_path}")

    # 生成索引页
    if modules_info:
        index_content = generate_index_markdown(modules_info)
        index_path = os.path.join(output_dir, "README.md")

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)
        Logger.log("  [GEN] README.md  索引页")

    return modules_info


def get_available_languages(docs_dir: Path) -> list[str]:
    """
    获取可用的语言列表

    :param docs_dir: 文档根目录
    :return: 语言代码列表
    """
    langs = []
    for item in docs_dir.iterdir():
        # 排除 _meta
        if item.is_dir() and item.name not in ['_meta']:
            langs.append(item.name)
    return sorted(langs)


def copy_directory(src: Path, dst: Path) -> None:
    """
    复制目录内容

    目标目录存在时会先被删除以确保与源目录一致。

    :param src: 源目录
    :param dst: 目标目录
    """
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ErisPulse API 文档生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认设置（为所有语言生成）
  python scripts/tools/generate-api-docs.py

  # 只为特定语言生成
  python scripts/tools/generate-api-docs.py --lang en

  # 自定义源目录和输出目录
  python scripts/tools/generate-api-docs.py --src src --output docs/api-reference/auto_api
        """
    )

    parser.add_argument("--src", default="src", help="源代码目录 (默认: src)")
    parser.add_argument("--docs", default="docs", help="文档根目录 (默认: docs)")
    parser.add_argument("--lang", help="指定语言代码（如: zh-CN, en, zh-TW），不指定则为所有语言生成")

    args = parser.parse_args()

    # 获取脚本所在目录
    script_dir = Path(__file__).parent

    # docs 目录
    docs_dir = script_dir.parent.parent / args.docs

    Logger.log("=" * 60)
    Logger.log("ErisPulse API 文档生成器")
    Logger.log("=" * 60)
    Logger.log(f"源代码目录: {args.src}")
    Logger.log(f"语言: {args.lang or '全部'}")
    Logger.log("")

    # 如果指定了语言，只为该语言生成
    if args.lang:
        # 生成 API 文档到指定语言目录
        output_dir = docs_dir / args.lang / "api-reference" / "auto_api"
        Logger.log(f"输出目录: {output_dir}")
        Logger.log("")

        modules_info = generate_api_docs(args.src, str(output_dir))

        # 输出统计
        total_modules = len(modules_info)
        total_classes = sum(len(info.get('classes', [])) for info in modules_info.values())
        total_functions = sum(len(info.get('functions', [])) for info in modules_info.values())
        total_methods = sum(count_all_methods(info.get('classes', [])) for info in modules_info.values())
        total_nested_classes = sum(count_nested_classes(info.get('classes', [])) for info in modules_info.values())

        Logger.log("")
        Logger.log("=" * 60)
        Logger.log(f"语言: {args.lang}")
        Logger.log(f"模块: {total_modules}")
        Logger.log(f"类: {total_classes}（包括 {total_nested_classes} 个嵌套类）")
        Logger.log(f"方法: {total_methods}")
        Logger.log(f"函数: {total_functions}")
        Logger.log("=" * 60)
    else:
        # 为所有语言生成
        langs = get_available_languages(docs_dir)
        Logger.log(f"发现 {len(langs)} 个语言: {', '.join(langs)}")
        Logger.log("")

        # 先生成到中文目录（如果有）
        if 'zh-CN' in langs:
            Logger.log("--- zh-CN ---")
            zh_output_dir = docs_dir / "zh-CN" / "api-reference" / "auto_api"
            Logger.log(f"  输出目录: {zh_output_dir}")
            Logger.log("")
            modules_info = generate_api_docs(args.src, str(zh_output_dir))

            # 复制到其他语言目录
            for lang in langs:
                if lang == 'zh-CN':
                    continue

                Logger.log("")
                Logger.log(f"--- {lang} ---")
                target_dir = docs_dir / lang / "api-reference" / "auto_api"
                copy_directory(zh_output_dir, target_dir)
                Logger.log(f"  [COPY] {target_dir}  从 zh-CN 复制")

            # 输出统计
            total_modules = len(modules_info)
            total_classes = sum(len(info.get('classes', [])) for info in modules_info.values())
            total_functions = sum(len(info.get('functions', [])) for info in modules_info.values())
            total_methods = sum(count_all_methods(info.get('classes', [])) for info in modules_info.values())
            total_nested_classes = sum(count_nested_classes(info.get('classes', [])) for info in modules_info.values())

            Logger.log("")
            Logger.log("=" * 60)
            Logger.log(f"模块: {total_modules}")
            Logger.log(f"类: {total_classes}（包括 {total_nested_classes} 个嵌套类）")
            Logger.log(f"方法: {total_methods}")
            Logger.log(f"函数: {total_functions}")
            Logger.log(f"已复制到: {len(langs)} 个语言")
            Logger.log("=" * 60)
        else:
            # 如果没有中文，使用第一个语言
            first_lang = langs[0]
            Logger.log(f"--- {first_lang} ---")

            output_dir = docs_dir / first_lang / "api-reference" / "auto_api"
            Logger.log(f"  输出目录: {output_dir}")
            Logger.log("")
            modules_info = generate_api_docs(args.src, str(output_dir))

            # 复制到其他语言目录
            for lang in langs[1:]:
                Logger.log("")
                Logger.log(f"--- {lang} ---")
                target_dir = docs_dir / lang / "api-reference" / "auto_api"
                copy_directory(output_dir, target_dir)
                Logger.log(f"  [COPY] {target_dir}  从 {first_lang} 复制")

            # 输出统计
            total_modules = len(modules_info)
            total_classes = sum(len(info.get('classes', [])) for info in modules_info.values())
            total_functions = sum(len(info.get('functions', [])) for info in modules_info.values())
            total_methods = sum(count_all_methods(info.get('classes', [])) for info in modules_info.values())
            total_nested_classes = sum(count_nested_classes(info.get('classes', [])) for info in modules_info.values())

            Logger.log("")
            Logger.log("=" * 60)
            Logger.log(f"模块: {total_modules}")
            Logger.log(f"类: {total_classes}（包括 {total_nested_classes} 个嵌套类）")
            Logger.log(f"方法: {total_methods}")
            Logger.log(f"函数: {total_functions}")
            Logger.log(f"已复制到: {len(langs)} 个语言")
            Logger.log("=" * 60)
