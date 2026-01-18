# IDE 配置指南

本文档说明如何配置IDE以识别ErisPulse的类型存根文件，获得完整的类型提示和自动补全功能。

## 类型存根文件说明

ErisPulse提供了`.pyi`类型存根文件，用于IDE的类型提示和代码补全。这些文件位于项目的`stubs/`目录中，结构如下：

```
stubs/
└── ErisPulse/
    ├── __init__.pyi
    ├── __main__.pyi
    ├── sdk_protocol.pyi
    ├── Core/
    │   ├── __init__.pyi
    │   ├── adapter.pyi
    │   ├── module.pyi
    │   └── ...
    ├── utils/
    │   └── ...
    └── ...
```

## VSCode 配置

### 方法一：项目级别配置（推荐）

在项目根目录创建或编辑`.vscode/settings.json`文件：

```json
{
  "python.analysis.stubPath": "${workspaceFolder}/stubs",
  "python.analysis.typeCheckingMode": "basic",
  "python.languageServer": "Pylance"
}
```

### 方法二：用户级别配置

打开VSCode设置（`Ctrl+,`），搜索"Python > Analysis: Stub Path"，设置为：
- `stubs`（相对路径，从项目根目录）
- 或绝对路径，如`D:/devs/Python/ErisPulse-devs/SDK/ErisPulse/stubs`

### 安装Pylance扩展

确保安装了[Pylance扩展](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)，它是VSCode官方的Python语言服务器，提供最佳的类型提示体验。

## PyCharm 配置

### 步骤1：标记stubs目录为Sources Root

1. 在PyCharm中打开项目
2. 在项目视图中右键点击`stubs`目录
3. 选择`Mark Directory as` -> `Sources Root`

### 步骤2：验证配置

1. 打开`File` -> `Settings`（Windows/Linux）或`PyCharm` -> `Settings`（macOS）
2. 导航到`Project` -> `Python Interpreter`
3. 确保项目解释器已正确配置
4. 类型提示应该自动生效

## 其他IDE

### Vim/Neovim

使用[coc-pyright](https://github.com/fannheyward/coc-pyright)：

```vim
" .vimrc 或 init.vim
let g:coc_global_extensions = ['coc-pyright']
```

在项目根目录创建`pyrightconfig.json`：

```json
{
  "stubPath": "stubs",
  "typeCheckingMode": "basic"
}
```

### Sublime Text

使用[LSP-pyright](https://packagecontrol.io/packages/LSP-pyright)：

1. 通过Package Control安装LSP-pyright
2. 在项目设置中添加：

```json
{
  "settings": {
    "LSP": {
      "LSP-pyright": {
        "enabled": true,
        "command": ["pyright-langserver", "--stdio"],
        "selector": "source.python",
        "settings": {
          "python.analysis.stubPath": "${workspace}/stubs"
        }
      }
    }
  }
}
```

## 验证配置

配置完成后，可以通过以下方式验证类型提示是否正常工作：

1. 在Python文件中导入ErisPulse模块：
   ```python
   from ErisPulse import ErisPulse
   ```

2. 将鼠标悬停在`ErisPulse`上，应该看到类型提示

3. 输入`ErisPulse.`，应该看到自动补全列表

4. 查看方法参数的类型提示
