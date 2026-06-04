# `ErisPulse.Core.client` 模块

---

## 模块概述


ErisPulse HTTP 客户端

基于 aiohttp 的统一 HTTP 客户端实现，提供完整的请求/响应抽象。
模块和适配器应优先使用此客户端发送 HTTP 请求，而非自行导入 aiohttp。

> **提示**
> 1. 使用 sdk.client 获取全局客户端单例
> 2. 支持 get / post / put / delete / patch / request 等常用方法
> 3. 自动记录请求日志和统计信息
> 4. 推荐所有模块和适配器使用此客户端发送 HTTP 请求

---

## 类列表


### `class HttpResponse`

HTTP 响应封装

提供与 aiohttp.ClientResponse 一致的访问接口。
自动读取并缓存响应体，避免重复读取。

> **提示**
> 通过 .raw 属性可访问底层原生响应对象

**示例**:
```python
>>> resp = await sdk.client.get("https://httpbin.org/get")
>>> print(resp.status)
>>> data = await resp.json()
```


#### 方法列表


##### `__init__(response)`

:param response: object 底层框架 Response 对象

---


##### `status()`

HTTP 状态码

:return: int 状态码 (如 200, 404)

---


##### `reason()`

状态描述

:return: str | None 状态原因短语

---


##### `headers()`

响应头

:return: object 大小写不敏感的响应头映射

---


##### `content_type()`

Content-Type 值

:return: str | None 内容类型

---


##### `charset()`

字符编码

:return: str | None 编码名称

---


##### `url()`

响应 URL (可能因重定向而与请求 URL 不同)

:return: object URL 对象

---


##### `raw()`

底层框架原生 Response 对象

:return: object 原生响应实例 (当前为 aiohttp.ClientResponse)

---


##### `async async read()`

读取响应体原始字节 (自动缓存)

:return: bytes 响应体内容

---


##### `async async text(encoding: str | None = None)`

读取响应体为文本

:param encoding: str | None 指定编码 (可选, 默认自动检测)
:return: str 文本内容

---


##### `async async json()`

解析响应体为 JSON

:param kwargs: 传递给 json.loads 的额外参数
:return: Any 解析后的数据

---


### `class HttpClient`

HTTP 客户端 (基于 aiohttp)

提供统一的异步 HTTP 请求接口，自动管理连接池和会话生命周期。
所有请求自动记录日志和统计信息。

> **提示**
> 1. 通过 sdk.client 获取全局单例，也可自行实例化
> 2. 使用 get/post/put/delete/patch 快捷方法或通用 request 方法
> 3. 支持自定义 headers、timeout、retry 等参数
> 4. 所有请求自动通过 lifecycle 发送事件，可用于监控

**示例**:
```python
>>> resp = await sdk.client.get("https://httpbin.org/get")
>>> data = await resp.json()
>>>
>>> resp = await sdk.client.post(
...     "https://httpbin.org/post",
...     json={"key": "value"},
...     headers={"Authorization": "Bearer token"},
... )
```


#### 方法列表


##### `__init__()`

:param timeout: float | None 请求总超时 (秒) (默认: 30)
:param connect_timeout: float | None 连接超时 (秒) (默认: 10)
:param max_retries: int 最大重试次数 (默认: 0)
:param retry_delay: float 重试间隔 (秒) (默认: 1)
:param headers: dict[str, str] 全局默认请求头 (可选)
:param user_agent: str User-Agent 字符串 (可选)

---


##### `async async _get_session()`

获取或创建 aiohttp 会话

> **内部方法**

---


##### `async async close()`

关闭客户端会话并释放资源

---


##### `async async request(method: str, url: str)`

发送 HTTP 请求

:param method: str HTTP 方法 (GET, POST, PUT, DELETE, PATCH 等)
:param url: str 请求 URL
:param params: dict[str, str] | None 查询参数 (可选)
:param headers: dict[str, str] | None 额外请求头 (可选)
:param data: Any 请求体 (表单或原始数据) (可选)
:param json: Any JSON 请求体 (可选)
:param timeout: float | None 本次请求超时 (秒) (可选, 覆盖默认值)
:param max_retries: int | None 本次最大重试次数 (可选, 覆盖默认值)
:param kwargs: 传递给底层请求的额外参数
:return: HttpResponse 响应对象

:raises: aiohttp 相关异常或连接错误

**示例**:
```python
>>> resp = await client.request("GET", "https://httpbin.org/get", params={"q": "test"})
```

---


##### `async async get(url: str)`

发送 GET 请求

:param url: str 请求 URL
:param params: dict[str, str] | None 查询参数 (可选)
:param headers: dict[str, str] | None 额外请求头 (可选)
:return: HttpResponse 响应对象

**示例**:
```python
>>> resp = await client.get("https://httpbin.org/get", params={"q": "test"})
>>> data = await resp.json()
```

---


##### `async async post(url: str)`

发送 POST 请求

:param url: str 请求 URL
:param data: Any 请求体 (表单或原始数据) (可选)
:param json: Any JSON 请求体 (可选)
:param headers: dict[str, str] | None 额外请求头 (可选)
:return: HttpResponse 响应对象

**示例**:
```python
>>> resp = await client.post("https://httpbin.org/post", json={"key": "value"})
```

---


##### `async async put(url: str)`

发送 PUT 请求

:param url: str 请求 URL
:param data: Any 请求体 (可选)
:param json: Any JSON 请求体 (可选)
:param headers: dict[str, str] | None 额外请求头 (可选)
:return: HttpResponse 响应对象

---


##### `async async delete(url: str)`

发送 DELETE 请求

:param url: str 请求 URL
:param headers: dict[str, str] | None 额外请求头 (可选)
:return: HttpResponse 响应对象

---


##### `async async patch(url: str)`

发送 PATCH 请求

:param url: str 请求 URL
:param data: Any 请求体 (可选)
:param json: Any JSON 请求体 (可选)
:param headers: dict[str, str] | None 额外请求头 (可选)
:return: HttpResponse 响应对象

---


##### `stats()`

请求统计

:return: dict[str, int] 统计数据 (total_requests, total_errors 等)

---


##### `reset_stats()`

重置统计数据

---

