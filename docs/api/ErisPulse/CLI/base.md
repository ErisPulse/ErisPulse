# `ErisPulse.CLI.base` 模块

> 最后更新：2026-02-02 05:58:18

---

## 模块概述


CLI 命令基类

定义所有命令的统一接口

---

## 类列表


### `class Command(ABC)`

命令基类

所有 CLI 命令都应继承此类并实现抽象方法

> **提示**
> 1. 每个命令类必须实现 add_arguments 和 execute 方法
> 2. name 和 description 为类属性，必须在子类中定义
> 3. execute 方法接收解析后的 args 对象


#### 方法列表


##### `add_arguments(parser: ArgumentParser)`

添加命令参数

:param parser: ArgumentParser 实例

---


##### `execute(args)`

执行命令

:param args: 解析后的参数对象

---


##### `help()`

获取帮助信息

:return: 命令描述

---

