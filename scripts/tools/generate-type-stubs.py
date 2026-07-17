#!/usr/bin/env python3
"""
ErisPulse 类型存根生成器

从Python源代码自动生成.pyi类型存根文件

特性：
- 类、函数、方法的类型注解提取
- 参数和返回值类型标注
- 继承关系
- 文档字符串转换
- 增量更新机制

使用方法:
    python scripts/tools/generate-type-stubs.py
    python scripts/tools/generate-type-stubs.py --force
    python scripts/tools/generate-type-stubs.py --clean
    python scripts/tools/generate-type-stubs.py --clean-only
"""

import ast
import argparse
import hashlib
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class Logger:
    """线程安全的标准输出日志器"""

    _lock = threading.Lock()

    @classmethod
    def log(cls, msg: str):
        """
        输出一行日志

        :param msg: 日志内容
        """
        with cls._lock:
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()

    @classmethod
    def progress(cls, rel_path: str, status: str, detail: str = ""):
        """
        输出单条进度日志

        :param rel_path: 文件相对路径
        :param status: 状态标识（gen/skip/fail 等）
        :param detail: 附加详情，可选
        """
        tag = {
            "gen": "[GEN]",
            "skip": "[SKIP]",
            "fail": "[FAIL]",
            "clean": "[DEL]",
            "warn": "[WARN]",
        }.get(status, f"[{status.upper()}]")
        line = f"  {tag} {rel_path}"
        if detail:
            line += f"  {detail}"
        cls.log(line)


class TypeStubGenerator:
    """类型存根生成器

    解析 Python 源代码 AST 并生成对应的 ``.pyi`` 类型存根文件，
    支持增量更新、强制重生与清理旧文件。
    """

    # 需要忽略的特殊标签
    IGNORE_TAGS = {
        "internal-use",
        "ignore"
    }

    def __init__(self, src_dir: str, output_dir: str, force: bool = False, clean: bool = False, clean_only: bool = False):
        """
        初始化类型存根生成器

        :param src_dir: 源代码目录
        :param output_dir: 类型存根输出目录
        :param force: 是否强制重新生成（忽略缓存）
        :param clean: 生成前是否清理旧 .pyi 文件
        :param clean_only: 仅清理旧 .pyi 文件，不生成新文件
        """
        self.src_dir = Path(src_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.force = force
        self.clean = clean
        self.clean_only = clean_only
        self.generated_files: Set[Path] = set()
        self.skipped_files: Set[Path] = set()
        self.cleaned_files: Set[Path] = set()

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 缓存目录，用于存储文件哈希
        self.cache_dir = Path(".github/.cache/type-stubs")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 如果只需要清理
        if clean_only:
            self._clean_stubs()
            return

        # 如果需要清理，先清理所有 .pyi 文件
        if clean:
            self._clean_stubs()

    def _clean_stubs(self):
        """清理所有 .pyi 文件以及对应的哈希缓存"""
        # 查找所有 .pyi 文件
        pyi_files = list(self.output_dir.rglob("*.pyi"))

        for pyi_file in pyi_files:
            rel = str(pyi_file.relative_to(self.output_dir)).replace("\\", "/")
            try:
                pyi_file.unlink()
                self.cleaned_files.add(pyi_file)
                Logger.progress(rel, "clean")
            except Exception as e:
                Logger.progress(rel, "fail", str(e))

        # 清理缓存
        cache_files = list(self.cache_dir.rglob("*.hash"))
        for cache_file in cache_files:
            try:
                cache_file.unlink()
            except Exception:
                pass

    def generate(self) -> Dict[str, Any]:
        """
        生成所有类型存根文件

        :return: 生成统计字典，包含 total/processed/generated/skipped/cleaned 字段
        """
        # 遍历所有Python文件
        python_files = list(self.src_dir.rglob("*.py"))
        total = len(python_files)
        processed = 0

        for py_file in python_files:
            # 跳过__pycache__和测试文件
            if "__pycache__" in str(py_file) or "test" in py_file.name:
                continue

            try:
                self._generate_stub(py_file)
                processed += 1
            except Exception as e:
                rel = str(py_file.relative_to(self.src_dir)).replace("\\", "/")
                Logger.progress(rel, "fail", str(e))

        return {
            "total": total,
            "processed": processed,
            "generated": len(self.generated_files),
            "skipped": len(self.skipped_files),
            "cleaned": len(self.cleaned_files)
        }

    def _generate_stub(self, py_file: Path):
        """
        为单个Python文件生成类型存根

        根据 .hash 缓存判断是否需要重新生成；当 ``force=True`` 时跳过缓存检查。

        :param py_file: 源 Python 文件路径
        """
        # 计算相对路径和输出路径
        rel_path = py_file.relative_to(self.src_dir)
        rel_str = str(rel_path).replace("\\", "/")
        stub_path = self.output_dir / rel_path.with_suffix(".pyi")

        # 创建输出目录
        stub_path.parent.mkdir(parents=True, exist_ok=True)

        # 计算源文件哈希
        content_hash = self._calculate_hash(py_file)

        # 检查是否需要更新（如果 force 为 True，则跳过缓存检查）
        if not self.force:
            cache_file = self.cache_dir / f"{rel_path.with_suffix('.hash')}"
            cache_file.parent.mkdir(parents=True, exist_ok=True)

            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_hash = f.read().strip()
                    if cached_hash == content_hash and stub_path.exists():
                        self.skipped_files.add(stub_path)
                        Logger.progress(rel_str, "skip")
                        return

        # 读取并解析源文件
        with open(py_file, 'r', encoding='utf-8') as f:
            source = f.read()

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            Logger.progress(rel_str, "fail", f"语法错误: {e}")
            return

        # 生成类型存根内容
        stub_content = self._generate_stub_content(tree, py_file)

        # 写入类型存根文件
        with open(stub_path, 'w', encoding='utf-8') as f:
            f.write(stub_content)

        # 更新缓存
        cache_file = self.cache_dir / f"{rel_path.with_suffix('.hash')}"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(content_hash)

        self.generated_files.add(stub_path)
        Logger.progress(rel_str, "gen")

    def _generate_stub_content(self, tree: ast.AST, source_file: Path) -> str:
        """
        生成类型存根文件内容

        拼接顺序：模块 docstring -> 顶层导入 -> 类/函数/变量定义。
        当源文件为 ``__init__.py`` 时，额外调用 ``_fix_ambiguous_init_imports``
        修复同名子模块/属性的导入歧义。

        :param tree: 已解析的源码 AST
        :param source_file: 源文件路径（用于判断是否为 ``__init__.py``）
        :return: 完整存根文件文本
        """
        lines = []
        
        # 添加文件头部注释（不加 # type: ignore，.pyi 文件本身就是类型声明）
        lines.append(f'# Auto-generated type stub for {source_file.name}')
        lines.append('# DO NOT EDIT MANUALLY - Generated by generate-type-stubs.py')
        lines.append('')
        
        # 提取模块文档字符串
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            lines.append('"""')
            lines.append(module_docstring)
            lines.append('"""')
            lines.append('')
        
        # 处理导入语句
        imports = self._extract_imports(tree)
        if imports:
            lines.extend(imports)
            lines.append('')
        
        # 判断是否是 ``__init__.py``：需要处理因 import 的子模块名与导入属性重名
        # 导致的类型检查器歧义（如 ``from .sdk import sdk`` → 子模块 ``sdk`` vs 属性 ``sdk``）
        is_init = source_file.name == "__init__.py"
        
        # 处理类、函数、变量定义
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if not self._should_ignore(node):
                    class_def = self._generate_class_def(node)
                    lines.append(class_def)
                    lines.append('')
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                if not self._should_ignore(node):
                    func_def = self._generate_function_def(node)
                    lines.append(func_def)
                    lines.append('')
            elif isinstance(node, ast.AnnAssign):
                # 处理类型变量赋值
                var_def = self._generate_var_def(node)
                if var_def:
                    lines.append(var_def)
                    lines.append('')
            elif isinstance(node, ast.Assign):
                # 处理普通赋值（如 ``sdk = SDK()``），推断类型
                var_def = self._generate_assign_def(node)
                if var_def:
                    lines.append(var_def)
                    lines.append('')
        
        # 仅 ``__init__.pyi``：替换可能导致歧义的导入为显式类型声明
        # 形如 ``from .xxx import xxx`` 的导入中，xxx 既是子模块名又是属性名
        if is_init:
            lines = self._fix_ambiguous_init_imports(lines, source_file)
        
        return '\n'.join(lines)

    def _generate_assign_def(self, node: ast.Assign) -> Optional[str]:
        """
        从普通赋值语句推断类型声明

        处理模式如 ``sdk = SDK()``，当 RHS 是类调用时推断变量类型。
        对于 ``target = SomeClass(...)`` 生成 ``target: SomeClass``。

        :param node: AST Assign 节点
        :return: 类型声明字符串，无法推断时返回 None
        """
        # 只处理单目标赋值
        if len(node.targets) != 1:
            return None
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return None

        var_name = target.id
        if var_name.startswith("_"):
            return None

        # RHS 必须是 Call（函数/类调用）
        if not isinstance(node.value, ast.Call):
            return None

        func = node.value.func

        # 获取类名
        if isinstance(func, ast.Name):
            class_name = func.id
        elif isinstance(func, ast.Attribute):
            class_name = self._get_attribute_name(func)
        else:
            return None

        return f"{var_name}: {class_name}"

    def _fix_ambiguous_init_imports(self, lines: List[str], source_file: Path) -> List[str]:
        """
        修复 ``__init__.pyi`` 中可能导致歧义的导入

        形如 ``from .xxx import xxx`` 的导入在包 ``__init__.pyi`` 中会
        让类型检查器混淆 ``xxx`` 是子模块还是导入的属性。
        修复方法：
        1. 检测 ``from .xxx import name1, name2`` 中 name_i == xxx 的冲突名
        2. 从源模块中解析出冲突名的实际类型
        3. 生成 ``from .xxx import ClassName, NonConflictName; ambig_name: ClassName`` 等显式声明

        :param lines: 存根文件行列表
        :param source_file: 源文件路径（用于计算兄弟模块相对路径）
        :return: 修复后的行列表
        """
        import re as _re

        result: List[str] = []
        src_dir = source_file.parent if source_file else None

        for line in lines:
            stripped = line.strip()
            # 匹配 ``from .xxx import ...``
            if stripped.startswith("from .") and " import " in stripped:
                match = _re.match(r"^from \.(\S+) import (.+)$", stripped)
                if match:
                    module_name = match.group(1)
                    all_names = [n.strip() for n in match.group(2).split(",")]

                    # 分离冲突名（与模块名相同）和非冲突名
                    conflicting = [n for n in all_names if n == module_name]
                    if not conflicting:
                        # 无冲突，保留原行
                        result.append(line)
                        continue
                    non_conflicting = [n for n in all_names if n != module_name]

                    # 查找源模块文件（优先 .py，其次 __init__.py）
                    source_module = src_dir / f"{module_name}.py"
                    if not source_module.exists():
                        source_module = src_dir / module_name / "__init__.py"

                    type_name = "Any"
                    if source_module.exists():
                        type_name = self._get_type_for_name(source_module, module_name)

                    # 生成：``from .xxx import TypeName, OtherName``
                    # 其中 TypeName 是冲突变量的实际类型，OtherName 是其他导入
                    import_names = []
                    if type_name and type_name != module_name and type_name not in non_conflicting:
                        import_names.append(type_name)
                    import_names.extend(non_conflicting)

                    if import_names:
                        result.append(f"from .{module_name} import {', '.join(import_names)}")
                    # 为每个冲突名生成显式类型声明
                    for cn in conflicting:
                        result.append(f"{cn}: {type_name}")
                    # 跳过原行
                    continue
            # 非导入行或未命中模式，保留原行
            result.append(line)

        return result

    def _get_type_for_name(self, module_path: Path, name: str) -> str:
        """
        解析源模块文件中指定名称的类型

        在 ``sdk.py`` 中查找 ``sdk = SDK()`` → 返回 ``SDK``；
        在 ``command.py`` 中查找 ``command: CommandHandler = CommandHandler()`` → 返回 ``CommandHandler``。

        :param module_path: 源模块文件路径
        :param name: 要查找的变量名
        :return: 类型名，无法确定时返回 "Any"
        """
        try:
            with open(module_path, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, OSError):
            return "Any"

        for node in tree.body:
            # AnnAssign: ``name: TypeName = ...``
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id == name and node.annotation:
                    return self._get_annotation(node.annotation)

            # Assign: ``name = ClassName()``
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id == name:
                    if isinstance(node.value, ast.Call):
                        func = node.value.func
                        if isinstance(func, ast.Name):
                            return func.id
                        if isinstance(func, ast.Attribute):
                            return self._get_attribute_name(func)

        return "Any"

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """
        提取所有导入语句（顶层导入和 TYPE_CHECKING 块中的导入）

        :param tree: 已解析的 AST
        :return: 导入语句字符串列表（已去重）
        """
        imports = []
        seen_imports = set()

        def _process_import_node(node):
            """
            处理单个导入节点

            :param node: ``ast.Import`` 或 ``ast.ImportFrom`` 节点
            """
            if isinstance(node, ast.ImportFrom):
                # 相对导入
                module = node.module or ''
                names = []
                for alias in node.names:
                    if alias.asname:
                        names.append(f"{alias.name} as {alias.asname}")
                    else:
                        names.append(alias.name)
                if names:
                    level = '.' * node.level
                    import_stmt = f"from {level}{module} import {', '.join(names)}"
                    if import_stmt not in seen_imports:
                        imports.append(import_stmt)
                        seen_imports.add(import_stmt)
            elif isinstance(node, ast.Import):
                names = []
                for alias in node.names:
                    if alias.asname:
                        names.append(f"{alias.name} as {alias.asname}")
                    else:
                        names.append(alias.name)
                import_stmt = f"import {', '.join(names)}"
                if import_stmt not in seen_imports:
                    imports.append(import_stmt)
                    seen_imports.add(import_stmt)
        
        for node in tree.body:
            # 处理顶层导入
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                _process_import_node(node)
            # 处理 if TYPE_CHECKING: 块中的导入
            elif isinstance(node, ast.If):
                test = node.test
                is_type_checking = (
                    (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or
                    (isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")
                )
                if is_type_checking:
                    imports.append("if TYPE_CHECKING:")
                    has_inner_imports = False
                    for inner_node in node.body:
                        if isinstance(inner_node, (ast.Import, ast.ImportFrom)):
                            _process_import_node(inner_node)
                            imports[-1] = "    " + imports[-1]
                            has_inner_imports = True
                    if has_inner_imports:
                        imports.append("")
                    else:
                        # 无有效导入时移除 if TYPE_CHECKING 行（避免空块语法错误）
                        imports.pop()
        
        return imports
    
    def _generate_class_def(self, node: ast.ClassDef) -> str:
        """
        生成类定义

        :param node: ``ast.ClassDef`` 节点
        :return: ``.pyi`` 中的类定义文本（含 docstring 与成员声明）
        """
        # 类名和基类
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(self._get_attribute_name(base))
        
        bases_str = f"({', '.join(bases)})" if bases else ""
        
        # 提取类文档字符串
        docstring = ast.get_docstring(node)
        
        # 收集所有成员
        members = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef) or isinstance(item, ast.AsyncFunctionDef):
                if not self._should_ignore(item):
                    members.append(self._generate_method_def(item))
            elif isinstance(item, ast.AnnAssign):
                if item.annotation:
                    var_name = self._get_var_name(item.target)
                    annotation = self._get_annotation(item.annotation)
                    members.append(f"    {var_name}: {annotation}")
        
        # 生成类定义
        lines = []
        lines.append(f"class {node.name}{bases_str}:")
        
        if docstring:
            lines.append('    """')
            for line in docstring.split('\n'):
                lines.append(f'    {line}')
            lines.append('    """')
        
        if members:
            lines.extend(members)
        else:
            lines.append("    ...")
        
        return '\n'.join(lines)
    
    def _get_decorators(self, node: ast.AST, indent: str = "") -> List[str]:
        """提取需要保留的装饰器（staticmethod/classmethod/property 等）
        
        :param node: AST 节点
        :param indent: 缩进字符串
        :return: 装饰器行列表
        """
        important_decorators = {"staticmethod", "classmethod", "property",
                                "abstractmethod", "override"}
        decorator_lines = []
        
        for decorator in getattr(node, 'decorator_list', []):
            if isinstance(decorator, ast.Name) and decorator.id in important_decorators:
                decorator_lines.append(f"{indent}@{decorator.id}")
            elif isinstance(decorator, ast.Attribute) and decorator.attr in important_decorators:
                decorator_lines.append(f"{indent}@{self._get_attribute_name(decorator)}")
        
        return decorator_lines
    
    def _generate_method_def(self, node: ast.FunctionDef) -> str:
        """
        生成方法定义

        :param node: ``ast.FunctionDef`` 或 ``ast.AsyncFunctionDef`` 节点
        :return: 含缩进的方法定义文本（含装饰器、签名、docstring 与 ``...`` 主体）
        """
        # 方法名
        is_async = isinstance(node, ast.AsyncFunctionDef)
        async_prefix = "async " if is_async else ""
        
        # 提取文档字符串
        docstring = ast.get_docstring(node)
        
        # 参数
        params = self._generate_params(node)
        
        # 返回类型
        return_type = self._get_annotation(node.returns) if node.returns else "..."
        
        # 收集装饰器
        decorator_lines = self._get_decorators(node, indent="    ")
        
        # 生成方法定义
        decorator_line = "    " + f"{async_prefix}def {node.name}{params} -> {return_type}:"
        
        result_lines = list(decorator_lines)
        
        if docstring:
            result_lines.append(decorator_line)
            result_lines.append('        """')
            for line in docstring.split('\n'):
                result_lines.append(f'        {line}')
            result_lines.append('        """')
            result_lines.append("        ...")
        else:
            result_lines.append(f"{decorator_line}\n        ...")
        
        return '\n'.join(result_lines)
    
    def _generate_function_def(self, node: ast.FunctionDef) -> str:
        """
        生成函数定义

        :param node: ``ast.FunctionDef`` 或 ``ast.AsyncFunctionDef`` 节点
        :return: 顶层函数定义文本（含装饰器、签名、docstring 与 ``...`` 主体）
        """
        is_async = isinstance(node, ast.AsyncFunctionDef)
        async_prefix = "async " if is_async else ""
        
        # 提取文档字符串
        docstring = ast.get_docstring(node)
        
        # 参数
        params = self._generate_params(node)
        
        # 返回类型
        return_type = self._get_annotation(node.returns) if node.returns else "..."
        
        # 收集装饰器
        decorator_lines = self._get_decorators(node, indent="")
        
        # 生成函数定义
        line = f"{async_prefix}def {node.name}{params} -> {return_type}:"
        
        result_lines = list(decorator_lines)
        
        if docstring:
            result_lines.append(line)
            result_lines.append('    """')
            for line in docstring.split('\n'):
                result_lines.append(f'    {line}')
            result_lines.append('    """')
            result_lines.append("    ...")
        else:
            result_lines.append(f"{line}\n    ...")
        
        return '\n'.join(result_lines)
    
    def _generate_params(self, node: ast.FunctionDef) -> str:
        """
        生成参数列表字符串

        处理顺序：posonly -> 普通 -> *args/* -> kwonly -> **kwargs。
        ``self`` 与 ``cls`` 不附加类型注解。

        :param node: 函数节点
        :return: 形如 ``(a: int, b: str = ...)`` 的参数字符串
        """
        params = []
        
        # 处理位置参数和关键字参数
        for arg in node.args.posonlyargs:
            param = self._generate_param(arg, node)
            params.append(param)
        
        if node.args.posonlyargs:
            params.append("/")
        
        # 处理普通参数
        if node.args.args:
            # 检查第一个参数是否是 self 或 cls
            first_arg = node.args.args[0]
            if first_arg.arg in ('self', 'cls'):
                # self/cls 不需要类型注解
                params.append(first_arg.arg)
                # 添加剩余参数
                for arg in node.args.args[1:]:
                    param = self._generate_param(arg, node)
                    params.append(param)
            else:
                # 没有特殊参数，全部添加
                for arg in node.args.args:
                    param = self._generate_param(arg, node)
                    params.append(param)
        
        # 处理 *args 或 * 作为 kwonly 分隔符
        if node.args.vararg:
            param = self._generate_param(node.args.vararg, node, is_vararg=True)
            params.append(param)
        elif node.args.kwonlyargs:
            # 存在关键字参数但没有 *args，需要添加 * 分隔符
            params.append("*")
        
        # 处理关键字参数 (kwonlyargs)
        for arg in node.args.kwonlyargs:
            param = self._generate_param(arg, node)
            params.append(param)
        
        # 处理 **kwargs
        if node.args.kwarg:
            param = self._generate_param(node.args.kwarg, node, is_kwarg=True)
            params.append(param)
        
        return f"({', '.join(params)})"
    
    def _generate_param(self, arg: ast.arg, node: ast.FunctionDef, 
                        is_vararg: bool = False, is_kwarg: bool = False) -> str:
        """
        生成单个参数声明

        :param arg: 参数 AST 节点
        :param node: 所属函数节点（用于读取默认值偏移）
        :param is_vararg: 是否为 ``*args`` 参数
        :param is_kwarg: 是否为 ``**kwargs`` 参数
        :return: 单个参数的声明字符串（含默认值 ``= ...``）
        """
        param_name = arg.arg
        
        # 添加星号
        if is_vararg:
            param_name = f"*{param_name}"
        elif is_kwarg:
            param_name = f"**{param_name}"
        
        # 检查是否有默认值
        has_default = False
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        if arg in node.args.args:
            idx = node.args.args.index(arg)
            has_default = idx >= defaults_offset
        elif arg == node.args.vararg or arg == node.args.kwarg:
            has_default = False
        
        # 获取类型注解
        annotation = self._get_annotation(arg.annotation) if arg.annotation else "..."
        
        # 生成参数字符串
        if has_default:
            return f"{param_name}: {annotation} = ..."
        else:
            return f"{param_name}: {annotation}"
    
    def _generate_var_def(self, node: ast.AnnAssign) -> Optional[str]:
        """
        生成带注解的变量定义

        :param node: ``ast.AnnAssign`` 节点
        :return: ``name: Annotation`` 字符串，无注解时返回 None
        """
        if not node.annotation:
            return None
        
        var_name = self._get_var_name(node.target)
        annotation = self._get_annotation(node.annotation)
        
        return f"{var_name}: {annotation}"
    
    def _get_annotation(self, annotation: ast.AST) -> str:
        """
        获取类型注解字符串

        递归处理 ``Subscript`` / ``Tuple`` / ``BinOp`` (``X | Y``) / ``Constant`` 等。

        :param annotation: 类型注解的 AST 节点
        :return: 注解字符串，无法识别时返回 ``...``
        """
        if annotation is None:
            return "..."
        
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return self._get_attribute_name(annotation)
        elif isinstance(annotation, ast.Subscript):
            value = self._get_annotation(annotation.value)
            slice_val = self._get_annotation(annotation.slice)
            # 当 slice 是 Tuple 时，_get_annotation 会返回 (a, b)，
            # 在下标中需要去掉括号: Dict[str, str] 而非 Dict[(str, str)]
            if isinstance(annotation.slice, ast.Tuple) and slice_val.startswith('(') and slice_val.endswith(')'):
                slice_val = slice_val[1:-1]
            return f"{value}[{slice_val}]"
        elif isinstance(annotation, ast.Tuple):
            elts = [self._get_annotation(elt) for elt in annotation.elts]
            return f"({', '.join(elts)})"
        elif isinstance(annotation, ast.BinOp):
            left = self._get_annotation(annotation.left)
            right = self._get_annotation(annotation.right)
            op = " | " if isinstance(annotation.op, ast.BitOr) else " & "
            return f"{left}{op}{right}"
        elif isinstance(annotation, ast.Constant):
            # None / True / False / 数字 / 字符串字面量
            return repr(annotation.value)
        elif isinstance(annotation, ast.List):
            elts = [self._get_annotation(elt) for elt in annotation.elts]
            return f"[{', '.join(elts)}]"
        elif isinstance(annotation, ast.Dict):
            keys = [self._get_annotation(k) for k in annotation.keys]
            values = [self._get_annotation(v) for v in annotation.values]
            kv_pairs = [f"{k}: {v}" for k, v in zip(keys, values)]
            return f"{{{', '.join(kv_pairs)}}}"
        elif isinstance(annotation, ast.Call):
            # 处理 Annotated[int, ...] 等调用形式的注解
            func = self._get_annotation(annotation.func)
            return func
        else:
            return "..."
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """
        获取属性访问的完整名称

        :param node: ``ast.Attribute`` 节点
        :return: 形如 ``module.Class.attr`` 的完整名称
        """
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        else:
            return node.attr

    def _get_var_name(self, target: ast.AST) -> str:
        """
        获取变量名

        :param target: 赋值目标 AST 节点
        :return: 变量名，无法识别时返回 ``...``
        """
        if isinstance(target, ast.Name):
            return target.id
        elif isinstance(target, ast.Attribute):
            return self._get_attribute_name(target)
        else:
            return "..."

    def _should_ignore(self, node: ast.AST) -> bool:
        """
        检查是否应该忽略此节点

        根据 docstring 中是否包含 ``IGNORE_TAGS`` 中的标签判断。

        :param node: AST 节点（类、函数等）
        :return: 包含忽略标签返回 True，否则 False
        """
        docstring = ast.get_docstring(node)
        if not docstring:
            return False
        
        # 检查是否包含忽略标签
        for tag in self.IGNORE_TAGS:
            if f"{{!--< {tag} >!--}}" in docstring:
                return True
        
        return False
    
    def _calculate_hash(self, file_path: Path) -> str:
        """
        计算文件内容的哈希值

        :param file_path: 文件路径
        :return: MD5 哈希十六进制字符串
        """
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()


def main():
    """命令行入口：解析参数并运行类型存根生成器"""
    parser = argparse.ArgumentParser(
        description="ErisPulse 类型存根生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--src",
        type=str,
        default="src",
        help="源代码目录 (默认: src)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="src",
        help="输出目录，与源目录相同以生成.pyi文件 (默认: src)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新生成所有类型存根文件，忽略缓存"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="在生成前清理所有现有的 .pyi 文件"
    )
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="只清理所有现有的 .pyi 文件，不生成新的文件"
    )

    args = parser.parse_args()

    Logger.log("=" * 60)
    Logger.log("ErisPulse 类型存根生成器")
    Logger.log("=" * 60)
    Logger.log(f"源代码目录: {args.src}")
    Logger.log(f"输出目录: {args.output}")
    Logger.log(f"强制重生: {'开启' if args.force else '关闭'}")
    Logger.log("")

    # 创建生成器
    generator = TypeStubGenerator(args.src, args.output, force=args.force, clean=args.clean, clean_only=args.clean_only)

    # 如果只是清理，直接返回
    if args.clean_only:
        Logger.log("")
        Logger.log("=" * 60)
        Logger.log(f"已清理: {len(generator.cleaned_files)} 个 .pyi 文件")
        Logger.log("=" * 60)
        return 0

    # 生成类型存根
    start_time = time.time()
    stats = generator.generate()
    duration = time.time() - start_time

    Logger.log("")
    Logger.log("=" * 60)
    Logger.log(f"总文件: {stats['total']}")
    Logger.log(f"处理: {stats['processed']}")
    if stats.get('cleaned', 0) > 0:
        Logger.log(f"清理: {stats['cleaned']}")
    Logger.log(f"生成: {stats['generated']}")
    Logger.log(f"跳过: {stats['skipped']}")
    Logger.log(f"耗时: {duration:.1f}s")
    Logger.log("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
