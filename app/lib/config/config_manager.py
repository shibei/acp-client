"""
配置管理模块
负责配置文件的加载、验证和管理
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import yaml
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


@dataclass
class ACPServerConfig:
    """ACP服务器配置"""
    url: str
    username: str
    password: str
    host: str = ''
    port: int = 80
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ACPServerConfig':
        """从字典创建配置"""
        url = data.get('url', '')
        host = ''
        port = 80
        
        # 从URL中解析host和port
        if url:
            try:
                if '://' in url:
                    host = url.split('://')[1].split('/')[0]
                else:
                    host = url.split('/')[0]
                
                if ':' in host:
                    host, port_str = host.split(':', 1)
                    port = int(port_str)
            except (ValueError, IndexError):
                pass
        
        return cls(
            url=url,
            username=data.get('username', ''),
            password=data.get('password', ''),
            host=host,
            port=port
        )
    
    def validate(self) -> List[str]:
        """验证配置
        
        Returns:
            错误信息列表
        """
        errors = []
        if not self.url:
            errors.append("ACP服务器URL不能为空")
        if not self.username:
            errors.append("ACP服务器用户名不能为空")
        return errors


@dataclass
class ScheduleConfig:
    """调度配置"""
    stop_time: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleConfig':
        """从字典创建配置"""
        stop_time_str = data.get('stop_time')
        stop_time = None
        if stop_time_str:
            try:
                stop_time = datetime.strptime(stop_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        
        return cls(stop_time=stop_time)
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        if self.stop_time and self.stop_time < datetime.now():
            errors.append("全局停止时间不能早于当前时间")
        return errors


@dataclass
class MeridianFlipConfig:
    """中天反转配置"""
    stop_minutes_before: int = 10
    resume_minutes_after: int = 10
    safety_margin: int = 5
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeridianFlipConfig':
        """从字典创建配置"""
        return cls(
            stop_minutes_before=data.get('stop_minutes_before', 10),
            resume_minutes_after=data.get('resume_minutes_after', 10),
            safety_margin=data.get('safety_margin', 5)
        )
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        if self.stop_minutes_before < 0:
            errors.append("中天前停止时间不能为负数")
        if self.resume_minutes_after < 0:
            errors.append("中天后恢复时间不能为负数")
        if self.safety_margin < 0:
            errors.append("安全边距不能为负数")
        return errors


@dataclass
class ObservatoryConfig:
    """观测站配置"""
    latitude: float = 0.0
    longitude: float = 0.0
    latitude_deg: float = 0.0
    min_altitude: float = 30.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObservatoryConfig':
        """从字典创建配置"""
        return cls(
            latitude=data.get('latitude', 0.0),
            longitude=data.get('longitude', 0.0),
            latitude_deg=data.get('latitude', 0.0),
            min_altitude=data.get('min_altitude', 30.0)
        )
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        if not (-90 <= self.latitude <= 90):
            errors.append("纬度必须在-90到90度之间")
        if not (-180 <= self.longitude <= 180):
            errors.append("经度必须在-180到180度之间")
        return errors


@dataclass
class GlobalSettingsConfig:
    """全局设置配置"""
    dither: int = 5
    auto_focus: bool = True
    af_interval: int = 120
    dryrun: bool = False
    log_dir: str = 'logs'
    log_level: str = 'INFO'
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GlobalSettingsConfig':
        """从字典创建配置"""
        return cls(
            dither=data.get('dither', 5),
            auto_focus=data.get('auto_focus', True),
            af_interval=data.get('af_interval', 120),
            dryrun=data.get('dryrun', False),
            log_dir=data.get('log_dir', 'logs'),
            log_level=data.get('log_level', 'INFO')
        )
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        if self.dither < 0:
            errors.append("抖动值不能为负数")
        if self.af_interval <= 0:
            errors.append("自动对焦间隔必须大于0")
        return errors
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（兼容字典访问）"""
        return getattr(self, key, default)


@dataclass
class TargetConfig:
    """目标配置"""
    name: str
    ra: str
    dec: str
    start_time: datetime
    priority: int
    filters: List[Dict[str, Any]]
    meridian_time: Optional[str] = None  # 手动指定的中天时间，格式为 'HH:MM:SS'
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TargetConfig':
        """从字典创建配置"""
        start_time_str = data.get('start_time')
        start_time = None
        if start_time_str:
            try:
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ConfigValidationError(f"目标 {data.get('name', 'Unknown')} 的开始时间格式错误")
        
        return cls(
            name=data.get('name', ''),
            ra=data.get('ra', ''),
            dec=data.get('dec', ''),
            start_time=start_time,
            priority=data.get('priority', 1),
            filters=data.get('filters', []),
            meridian_time=data.get('meridian_time')  # 手动指定的中天时间
        )
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        if not self.name:
            errors.append("目标名称不能为空")
        if not self.ra:
            errors.append("目标RA坐标不能为空")
        if not self.dec:
            errors.append("目标DEC坐标不能为空")
        if not self.start_time:
            errors.append("目标开始时间不能为空")
        if not self.filters:
            errors.append("目标滤镜配置不能为空")
        
        # 验证手动指定的中天时间格式
        if self.meridian_time:
            try:
                datetime.strptime(self.meridian_time, '%H:%M:%S')
            except ValueError:
                errors.append(f"目标 {self.name} 的中天时间格式错误，应为 HH:MM:SS")
        
        # 验证滤镜配置
        for i, filter_cfg in enumerate(self.filters):
            if 'filter_id' not in filter_cfg:
                errors.append(f"目标 {self.name} 的第 {i+1} 个滤镜缺少filter_id")
            if 'exposure' not in filter_cfg or filter_cfg['exposure'] <= 0:
                errors.append(f"目标 {self.name} 的第 {i+1} 个滤镜曝光时间无效")
            if 'count' not in filter_cfg or filter_cfg['count'] <= 0:
                errors.append(f"目标 {self.name} 的第 {i+1} 个滤镜数量无效")
        
        return errors
    
    def get_total_duration_hours(self) -> float:
        """获取总观测时间（小时）"""
        total_seconds = sum(f['exposure'] * f['count'] for f in self.filters)
        return total_seconds / 3600


class MultiTargetConfigManager:
    """多目标配置管理器"""
    
    def __init__(self, config_file: str, dry_run: bool = False):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.raw_config: Dict[str, Any] = {}
        
        # 配置对象
        self.acp_server: Optional[ACPServerConfig] = None
        self.schedule: Optional[ScheduleConfig] = None
        self.meridian_flip: Optional[MeridianFlipConfig] = None
        self.observatory: Optional[ObservatoryConfig] = None
        self.global_settings: Optional[GlobalSettingsConfig] = None
        self.targets: List[TargetConfig] = []
        
        # 加载配置
        self._load_config()
        self._parse_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.raw_config = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigValidationError(f"配置文件不存在: {self.config_file}")
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"配置文件格式错误: {e}")
    
    def _parse_config(self):
        """解析配置"""
        # ACP服务器配置
        acp_server_data = self.raw_config.get('acp_server', {})
        self.acp_server = ACPServerConfig.from_dict(acp_server_data)
        
        # 调度配置
        schedule_data = self.raw_config.get('schedule', {})
        self.schedule = ScheduleConfig.from_dict(schedule_data)
        
        # 中天反转配置（可选）
        meridian_flip_data = self.raw_config.get('meridian_flip', {})
        self.meridian_flip = MeridianFlipConfig.from_dict(meridian_flip_data)
        
        # 观测站配置（可选）
        observatory_data = self.raw_config.get('observatory', {})
        self.observatory = ObservatoryConfig.from_dict(observatory_data)
        
        # 全局设置
        global_settings_data = self.raw_config.get('global_settings', {})
        self.global_settings = GlobalSettingsConfig.from_dict(global_settings_data)
        
        # 重试设置（可选）
        self.retry_settings = self.raw_config.get('retry_settings', {})
        
        # 目标配置
        targets_data = self.raw_config.get('targets', [])
        self.targets = []
        for target_data in targets_data:
            self.targets.append(TargetConfig.from_dict(target_data))
        
        # 按开始时间和优先级排序
        self.targets.sort(key=lambda x: (x.start_time, x.priority))
    
    def validate(self) -> List[str]:
        """验证所有配置
        
        Returns:
            错误信息列表
        """
        errors = []
        
        # 验证各个配置
        if self.acp_server:
            errors.extend(self.acp_server.validate())
        
        if self.schedule:
            errors.extend(self.schedule.validate())
        
        if self.meridian_flip:
            errors.extend(self.meridian_flip.validate())
        
        if self.observatory:
            errors.extend(self.observatory.validate())
        
        if self.global_settings:
            errors.extend(self.global_settings.validate())
        
        # 验证目标
        for target in self.targets:
            errors.extend(target.validate())
        
        # 验证目标时间顺序
        if len(self.targets) > 1:
            for i in range(1, len(self.targets)):
                if self.targets[i].start_time <= self.targets[i-1].start_time:
                    errors.append(f"目标 {self.targets[i].name} 的开始时间不晚于前一个目标")
        
        return errors
    
    def is_valid(self) -> bool:
        """检查配置是否有效
        
        Returns:
            True: 有效
            False: 无效
        """
        return len(self.validate()) == 0
    
    def get_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            摘要信息字典
        """
        total_duration = sum(target.get_total_duration_hours() for target in self.targets)
        
        return {
            'total_targets': len(self.targets),
            'total_duration_hours': total_duration,
            'dryrun_mode': self.global_settings.dryrun if self.global_settings else False,
            'has_meridian_flip': self.meridian_flip is not None,
            'has_observatory': self.observatory is not None,
            'global_stop_time': self.schedule.stop_time if self.schedule else None,
            'acp_server_url': self.acp_server.url if self.acp_server else ''
        }
    
    def print_summary(self):
        """打印配置摘要"""
        summary = self.get_summary()
        
    def get_config(self):
        """获取配置对象
        
        Returns:
            配置管理器自身（兼容旧接口）
        """
        return self
        print("多目标观测配置摘要")
        if summary['dryrun_mode']:
            print("*** DRYRUN 模式 - 仅模拟运行 ***")
        print("="*80)
        
        print(f"总目标数: {summary['total_targets']}")
        print(f"预计总时间: {summary['total_duration_hours']:.1f}小时")
        print(f"ACP服务器: {summary['acp_server_url']}")
        
        if summary['global_stop_time']:
            print(f"全局停止时间: {summary['global_stop_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if summary['has_meridian_flip']:
            print("中天反转: 已启用")
        
        if summary['has_observatory']:
            print("观测站位置: 已配置")
        
        print("\n目标列表:")
        for i, target in enumerate(self.targets, 1):
            duration = target.get_total_duration_hours()
            print(f"  {i}. {target.name}")
            print(f"     时间: {target.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"     坐标: RA {target.ra}, DEC {target.dec}")
            print(f"     持续时间: {duration:.1f}小时")
            print(f"     滤镜数: {len(target.filters)}")
        
        print("="*80)