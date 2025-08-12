"""
ErisPulse 环境模块 (已弃用)

此模块已重命名为 storage，为保持向后兼容性而保留。
建议使用 from ErisPulse.Core import storage 替代 from ErisPulse.Core import env

{!--< deprecated >!--} 请使用 storage 模块替代
"""

from .storage import storage

# 向后兼容性
env = storage

__all__ = ['env']