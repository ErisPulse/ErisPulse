# ErisPulse 运维治理示例模块

演示后台线程任务的资源归属、延迟任务、内存体检与运行时日志隐私开关。

## 功能特性

- `@bind_owner`：第三方线程（`threading.Timer`）入口缝归属上下文，卸载可回收
- `spawn_later`：归属化延迟任务（到期自动触发，模块卸载时取消）
- `log_snapshot` / `get_rss_mb`：一行内存体检（加载 / 卸载快照对比）
- `logger.exclude_level` / `allow_level`：运行时消息内容隐私开关（EVENT 等级）

## 安装

```bash
pip install -e .
```

## 使用

可用命令：

- `/mem` - 当前进程内存读数（RSS）
- `/privacy off` - 运行时屏蔽 EVENT 等级（消息收发内容不再进日志 / Dashboard）
- `/privacy on` - 恢复 EVENT 等级
- `/privacy status` - 查看当前被屏蔽的等级
- `/remind <秒> <内容>` - 归属化延迟任务：到期写入模块状态并打日志
- `/reminds` - 查看已触发的延迟提醒（`BaseModule.state` 持久化）

模块加载时会启动一个 `threading.Timer` 演示线程：经 `bind_owner` 包装后，
回调运行期携带本模块归属（日志可见 owner），模块卸载时随归属治理回收。

## 开发

参考 ErisPulse 归属权系统与 runtime 工具带文档了解全部能力。
