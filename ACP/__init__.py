"""
ACP天文台控制客户端包

模块说明：
- ACPlib: ACP客户端核心功能
- models: 数据模型定义
- logger: 日志管理
- monitor: 状态监控
- scheduler: 目标调度器
"""

from .ACPlib import ACPClient
from .models import ObservatoryStatus, ImagingPlan, ScheduledTarget
from .gui.logger import LogManager
from .monitor import StatusMonitor
from .gui.scheduler import TargetScheduler

__all__ = [
    'ACPClient',
    'ObservatoryStatus',
    'ImagingPlan',
    'ScheduledTarget',
    'LogManager',
    'StatusMonitor',
    'TargetScheduler',
]
