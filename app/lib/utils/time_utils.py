"""
时间工具模块
包含时间相关的工具函数和类
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict


class TimeUtils:
    """时间工具类"""
    
    @staticmethod
    def parse_time_string(time_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
        """解析时间字符串
        
        Args:
            time_str: 时间字符串
            format_str: 格式字符串
            
        Returns:
            datetime对象或None
        """
        if not time_str:
            return None
        
        try:
            return datetime.strptime(time_str, format_str)
        except ValueError:
            return None
    
    @staticmethod
    def format_time_string(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """格式化时间对象为字符串
        
        Args:
            dt: datetime对象
            format_str: 格式字符串
            
        Returns:
            时间字符串
        """
        return dt.strftime(format_str)
    
    @staticmethod
    def calculate_duration(start_time: datetime, end_time: datetime) -> timedelta:
        """计算时间间隔
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            时间间隔
        """
        return end_time - start_time
    
    @staticmethod
    def is_time_expired(target_time: datetime, current_time: Optional[datetime] = None,
                       tolerance_minutes: int = 0) -> bool:
        """检查时间是否已过期
        
        Args:
            target_time: 目标时间
            current_time: 当前时间（默认为now）
            tolerance_minutes: 容忍时间（分钟）
            
        Returns:
            True: 已过期
            False: 未过期
        """
        if current_time is None:
            current_time = datetime.now()
        
        tolerance = timedelta(minutes=tolerance_minutes)
        return current_time > target_time + tolerance
    
    @staticmethod
    def get_time_until(target_time: datetime, current_time: Optional[datetime] = None) -> timedelta:
        """获取距离目标时间的间隔
        
        Args:
            target_time: 目标时间
            current_time: 当前时间（默认为now）
            
        Returns:
            时间间隔（负值表示已过期）
        """
        if current_time is None:
            current_time = datetime.now()
        
        return target_time - current_time
    
    @staticmethod
    def format_duration(td: timedelta) -> str:
        """格式化时间间隔为易读字符串
        
        Args:
            td: 时间间隔
            
        Returns:
            易读字符串
        """
        total_seconds = int(td.total_seconds())
        
        if total_seconds < 0:
            return "已过期"
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if days > 0:
            return f"{days}天 {hours}小时 {minutes}分钟"
        elif hours > 0:
            return f"{hours}小时 {minutes}分钟"
        elif minutes > 0:
            return f"{minutes}分钟 {seconds}秒"
        else:
            return f"{seconds}秒"
    
    @staticmethod
    def wait_until_time(target_time: datetime, check_interval: int = 30,
                       timeout: Optional[timedelta] = None) -> bool:
        """等待直到指定时间
        
        Args:
            target_time: 目标时间
            check_interval: 检查间隔（秒）
            timeout: 超时时间
            
        Returns:
            True: 成功等到目标时间
            False: 超时或被中断
        """
        import time
        
        start_time = datetime.now()
        
        while True:
            current_time = datetime.now()
            
            # 检查超时
            if timeout and current_time - start_time > timeout:
                return False
            
            # 检查是否到达目标时间
            if current_time >= target_time:
                return True
            
            # 计算剩余时间
            remaining = target_time - current_time
            
            # 如果剩余时间小于检查间隔，直接等待剩余时间
            if remaining.total_seconds() <= check_interval:
                time.sleep(remaining.total_seconds())
                return True
            
            time.sleep(check_interval)
    
    @staticmethod
    def get_current_time_info() -> Dict[str, str]:
        """获取当前时间信息
        
        Returns:
            时间信息字典
        """
        now = datetime.now()
        return {
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'timestamp': str(int(now.timestamp())),
            'iso_format': now.isoformat()
        }