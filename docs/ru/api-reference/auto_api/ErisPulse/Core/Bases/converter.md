# `ErisPulse.Core.Bases.converter` 模块

---

## 模块概述


OneBot12 事件转换器基类

适配器在"平台原生事件 → OneBot12 标准格式"之间转换时使用。
本基类提供 OneBot12 ``base_event`` 公共字段的构建与常用消息段辅助方法，
子类只需实现类型映射（``convert``）与平台特有字段填充。

> **提示**
> 1. ``build_base_event`` 已填充 id/time/platform/self/{platform}_raw 等公共字段
> 2. 常用消息段（text / at / image）可直接复用静态方法
> 3. 子类必须实现 ``convert()``，无法识别的事件返回 ``None``

---

## 类列表


### `class BaseConverter`

事件转换器基类

- **platform** (`str`): 平台标识（如 "myplatform" / "onebot11"）


#### 方法列表


##### `build_base_event(raw_event: dict, raw_type: str = '')`

构建 OneBot12 标准事件的公共字段（id / time / platform / self / raw）

- **raw_event** (`平台原始事件`): - **raw_type**: 平台原始事件类型
**返回值**: 含公共字段的事件字典

---


##### `text(text: str)`

构造文本消息段

---


##### `at(user_id: str)`

构造 @ 消息段

---


##### `image(file: str)`

构造图片消息段

---


##### `convert(raw_event: dict)`

将平台原生事件转换为 OneBot12 标准格式

- **raw_event** (`平台原始事件数据`): **返回值** (`OneBot12`): 标准格式事件字典；无法识别时返回 None

---

