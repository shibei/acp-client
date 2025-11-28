"""
数据模型定义
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict


@dataclass
class ObservatoryStatus:
    """天文台状态"""
    local_time: str = ""
    utc_time: str = ""
    lst_time: str = ""
    observatory_status: str = "Offline"
    owner: str = "Free"
    telescope_status: str = "Offline"
    camera_status: str = "Offline"
    guider_status: str = "Offline"
    current_ra: str = ""
    current_dec: str = ""
    current_alt: str = ""
    current_az: str = ""
    image_filter: str = ""
    image_temperature: str = ""
    plan_progress: str = "0/0"
    last_fwhm: str = ""


@dataclass
class ImagingPlan:
    """成像计划"""
    target: str = ""
    ra: str = ""
    dec: str = ""
    filters: List[Dict] = None
    dither: int = 5
    auto_focus: bool = True
    periodic_af_interval: int = 120
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = []


@dataclass
class ScheduledTarget:
    """计划目标 - 带时间的成像任务"""
    name: str
    start_time: datetime
    plan_config: dict
    status: str = "等待中"  # 等待中、执行中、已完成、已跳过
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'plan_config': self.plan_config,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScheduledTarget':
        """从字典创建"""
        return cls(
            name=data['name'],
            start_time=datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S'),
            plan_config=data['plan_config'],
            status=data.get('status', '等待中')
        )
