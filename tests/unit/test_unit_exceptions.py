"""
异步关停噪音折叠（runtime.exceptions）单元测试
"""

from ErisPulse.runtime import exceptions as exc_module


def test_noise_state_bounded():
    """折叠状态表超容量上限时淘汰最旧条目（防超长驻留进程无界增长）"""
    exc_module._async_noise_state.clear()
    cap = exc_module._ASYNC_NOISE_STATE_MAX_ENTRIES
    for i in range(cap + 10):
        exc_module._fold_async_noise(f"noise-{i}")
    assert len(exc_module._async_noise_state) <= cap
    # 最旧的条目已被淘汰（noise-0 等早期键不再保留全量）
    assert "noise-0" not in exc_module._async_noise_state
    exc_module._async_noise_state.clear()
