#!/usr/bin/env python3
"""
艾莉丝的类型炼金工房 - 类型存根生成器

从Python源代码自动生成.pyi类型存根文件，支持：
- 类、函数、方法的类型注解提取
- 参数和返回值类型标注
- 继承关系
- 文档字符串转换
- 增量更新机制
"""

import ast
import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class TypeStubGenerator:
    """类型存根生成器"""
    
    # 需要忽略的特殊标签
    IGNORE_TAGS = {
        "internal-use",
        "ignore"
    }
    
    def __init__(self, src_dir: str, output_dir: str, force: bool = False, clean: bool = False, clean_only: bool = False):
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
        """清理所有 .pyi 文件"""
        print("🧹 艾莉丝正在清理旧的类型存根文件~")
        
        # 查找所有 .pyi 文件
        pyi_files = list(self.output_dir.rglob("*.pyi"))
        
        for pyi_file in pyi_files:
            try:
                pyi_file.unlink()
                self.cleaned_files.add(pyi_file)
            except Exception as e:
                print(f"⚠️ 删除 {pyi_file} 时出错: {e}")
        
        # 清理缓存
        cache_files = list(self.cache_dir.rglob("*.hash"))
        for cache_file in cache_files:
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"⚠️ 删除缓存 {cache_file} 时出错: {e}")
        
        print(f"✅ 已清理 {len(self.cleaned_files)} 个 .pyi 文件")
    
    def generate(self) -> Dict[str, Any]:
        """生成所有类型存根文件"""
        print("🔮 艾莉丝开始施展类型存根生成魔法~")
        
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
                print(f"⚠️ 处理 {py_file} 时出错: {e}")
        
        return {
            "total": total,
            "processed": processed,
            "generated": len(self.generated_files),
            "skipped": len(self.skipped_files),
            "cleaned": len(self.cleaned_files)
        }
    
    def _generate_stub(self, py_file: Path):
        """为单个Python文件生成类型存根"""
        # 计算相对路径和输出路径
        rel_path = py_file.relative_to(self.src_dir)
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
                        return
        
        # 读取并解析源文件
        with open(py_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            print(f"⚠️ 无法解析 {py_file}: {e}")
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
    
    def _generate_stub_content(self, tree: ast.AST, source_file: Path) -> str:
        """生成类型存根文件内容"""
        lines = []
        
        # 添加文件头部注释
        lines.append('# type: ignore')
        lines.append('#')
        lines.append(f'# Auto-generated type stub for {source_file.name}')
        lines.append(f'# DO NOT EDIT MANUALLY - Generated by generate-type-stubs.py')
        lines.append('#')
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
        
        # 处理类和函数定义
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
        
        return '\n'.join(lines)
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """提取所有导入语句（仅限顶层导入）"""
        imports = []
        seen_imports = set()
        
        # 只处理顶层导入，跳过函数/类内部的导入
        for node in tree.body:
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
        
        return imports
    
    def _generate_class_def(self, node: ast.ClassDef) -> str:
        """生成类定义"""
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
    
    def _generate_method_def(self, node: ast.FunctionDef) -> str:
        """生成方法定义"""
        # 方法名
        is_async = isinstance(node, ast.AsyncFunctionDef)
        async_prefix = "async " if is_async else ""
        
        # 提取文档字符串
        docstring = ast.get_docstring(node)
        
        # 参数
        params = self._generate_params(node)
        
        # 返回类型
        return_type = self._get_annotation(node.returns) if node.returns else "..."
        
        # 生成方法定义
        decorator = "    "
        decorator_line = decorator + f"{async_prefix}def {node.name}{params} -> {return_type}:"
        
        if docstring:
            lines = [decorator_line]
            lines.append('        """')
            for line in docstring.split('\n'):
                lines.append(f'        {line}')
            lines.append('        """')
            lines.append("        ...")
            return '\n'.join(lines)
        else:
            return f"{decorator_line}\n        ..."
    
    def _generate_function_def(self, node: ast.FunctionDef) -> str:
        """生成函数定义"""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        async_prefix = "async " if is_async else ""
        
        # 提取文档字符串
        docstring = ast.get_docstring(node)
        
        # 参数
        params = self._generate_params(node)
        
        # 返回类型
        return_type = self._get_annotation(node.returns) if node.returns else "..."
        
        # 生成函数定义
        line = f"{async_prefix}def {node.name}{params} -> {return_type}:"
        
        if docstring:
            lines = [line]
            lines.append('    """')
            for line in docstring.split('\n'):
                lines.append(f'    {line}')
            lines.append('    """')
            lines.append("    ...")
            return '\n'.join(lines)
        else:
            return f"{line}\n    ..."
    
    def _generate_params(self, node: ast.FunctionDef) -> str:
        """生成参数列表"""
        params = []
        
        # 特殊处理 __init__ 方法
        is_init = node.name == '__init__'
        
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
                # 添加 self 或 cls 参数
                param_name = first_arg.arg
                annotation = self._get_annotation(first_arg.annotation) if first_arg.annotation else ("None" if is_init else "object")
                params.append(f"{param_name}: {annotation}")
                # 添加剩余参数
                for arg in node.args.args[1:]:
                    param = self._generate_param(arg, node)
                    params.append(param)
            else:
                # 没有特殊参数，全部添加
                for arg in node.args.args:
                    param = self._generate_param(arg, node)
                    params.append(param)
        
        # 处理 *args
        if node.args.vararg:
            param = self._generate_param(node.args.vararg, node, is_vararg=True)
            params.append(param)
        
        # 处理 **kwargs
        if node.args.kwarg:
            param = self._generate_param(node.args.kwarg, node, is_kwarg=True)
            params.append(param)
        
        return f"({', '.join(params)})"
    
    def _generate_param(self, arg: ast.arg, node: ast.FunctionDef, 
                        is_vararg: bool = False, is_kwarg: bool = False) -> str:
        """生成单个参数"""
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
        """生成变量定义"""
        if not node.annotation:
            return None
        
        var_name = self._get_var_name(node.target)
        annotation = self._get_annotation(node.annotation)
        
        return f"{var_name}: {annotation}"
    
    def _get_annotation(self, annotation: ast.AST) -> str:
        """获取类型注解字符串"""
        if annotation is None:
            return "..."
        
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Attribute):
            return self._get_attribute_name(annotation)
        elif isinstance(annotation, ast.Subscript):
            value = self._get_annotation(annotation.value)
            slice_val = self._get_annotation(annotation.slice)
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
            return str(annotation.value)
        elif isinstance(annotation, ast.List):
            elts = [self._get_annotation(elt) for elt in annotation.elts]
            return f"[{', '.join(elts)}]"
        elif isinstance(annotation, ast.Dict):
            keys = [self._get_annotation(k) for k in annotation.keys]
            values = [self._get_annotation(v) for v in annotation.values]
            kv_pairs = [f"{k}: {v}" for k, v in zip(keys, values)]
            return f"{{{', '.join(kv_pairs)}}}"
        else:
            return "..."
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """获取属性访问的完整名称"""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        else:
            return node.attr
    
    def _get_var_name(self, target: ast.AST) -> str:
        """获取变量名"""
        if isinstance(target, ast.Name):
            return target.id
        elif isinstance(target, ast.Attribute):
            return self._get_attribute_name(target)
        else:
            return "..."
    
    def _should_ignore(self, node: ast.AST) -> bool:
        """检查是否应该忽略此节点"""
        docstring = ast.get_docstring(node)
        if not docstring:
            return False
        
        # 检查是否包含忽略标签
        for tag in self.IGNORE_TAGS:
            if f"{{!--< {tag} >!--}}" in docstring:
                return True
        
        return False
    
    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件内容的哈希值"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="🔮 艾莉丝的类型炼金工房 - 自动生成类型存根文件"
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
    
    # 创建生成器
    generator = TypeStubGenerator(args.src, args.output, force=args.force, clean=args.clean, clean_only=args.clean_only)
    
    # 如果只是清理，直接返回
    if args.clean_only:
        print(f"\n✨ 清理完成! 已删除 {len(generator.cleaned_files)} 个 .pyi 文件")
        return 0
    
    # 生成类型存根
    stats = generator.generate()
    
    # 输出统计信息
    print(f"\n📊 艾莉丝的统计报告:")
    print(f"  总文件数: {stats['total']}")
    print(f"  处理文件: {stats['processed']}")
    if stats.get('cleaned', 0) > 0:
        print(f"  清理文件: {stats['cleaned']}")
    print(f"  生成文件: {stats['generated']}")
    print(f"  跳过文件: {stats['skipped']}")
    print(f"\n✨ 类型存根生成完成!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
