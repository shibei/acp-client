"""
目标时间调度器
负责目标观测时间的等待和调度管理
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import time
from ..utils.time_utils import TimeUtils
from ..utils.log_manager import LogManager


class TargetScheduler:
    """目标时间调度器 - 负责目标观测时间的等待和调度管理"""
    
    def __init__(self, log_manager: LogManager, dryrun: bool = False):
        """初始化目标调度器
        
        Args:
            log_manager: 日志管理器
            dryrun: 是否模拟模式
        """
        self.log_manager = log_manager
        self.dryrun = dryrun
        self.waiting_target: Optional[Dict[str, Any]] = None
    
    def wait_for_target_time(self, target: Any, 
                           global_stop_time: Optional[datetime] = None) -> bool:
        """等待目标观测时间
        
        Args:
            target: 目标配置 (TargetConfig对象)
            global_stop_time: 全局停止时间
            
        Returns:
            True: 成功等到目标时间或被跳过
            False: 被中断或超时
        """
        target_time = target.start_time
        current_time = datetime.now()
        target_name = target.name
        
        # 检查是否已经过了目标时间
        if current_time >= target_time:
            print(f"[{current_time.strftime('%H:%M:%S')}] 目标 {target_name} 时间已到，立即开始观测")
            return True
        
        # 检查全局停止时间
        if global_stop_time and target_time >= global_stop_time:
            print(f"[{current_time.strftime('%H:%M:%S')}] 目标 {target_name} 时间超过全局停止时间，跳过")
            self.log_manager.info(f"目标 {target_name} 因超过全局停止时间而被跳过")
            return False
        
        # 计算等待时间
        wait_seconds = (target_time - current_time).total_seconds()
        wait_hours = wait_seconds / 3600
        
        print(f"\n[{current_time.strftime('%H:%M:%S')}] 等待目标 {target_name} 观测时间...")
        print(f"  计划时间: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  还需等待: {wait_hours:.1f}小时 ({wait_seconds/60:.0f}分钟)")
        
        self.waiting_target = target
        
        # 执行等待
        success = self._wait_until_time(target_time, f"目标 {target_name}", global_stop_time)
        
        if success:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 到达 {target_name} 观测时间")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 等待被中断")
        
        self.waiting_target = None
        return success
    
    def _wait_until_time(self, target_time: datetime, description: str,
                        global_stop_time: Optional[datetime] = None) -> bool:
        """等待直到指定时间
        
        Args:
            target_time: 目标时间
            description: 描述信息
            global_stop_time: 全局停止时间
            
        Returns:
            True: 成功等到目标时间
            False: 被中断
        """
        if self.dryrun:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟等待 {description}...")
            return True
        
        check_interval = 30  # 30秒检查一次
        
        while True:
            current_time = datetime.now()
            
            # 检查是否到达目标时间
            if current_time >= target_time:
                return True
            
            # 检查全局停止时间
            if global_stop_time and current_time >= global_stop_time:
                print(f"[{current_time.strftime('%H:%M:%S')}] 到达全局停止时间，中断等待")
                return False
            
            # 计算剩余时间
            remaining_seconds = (target_time - current_time).total_seconds()
            remaining_minutes = remaining_seconds / 60
            
            # 打印倒计时（每分钟一次）
            if int(remaining_minutes) % 1 == 0:
                print(f"[{current_time.strftime('%H:%M:%S')}] 等待 {description} 中... 剩余 {remaining_minutes:.0f}分钟")
            
            # 等待
            time.sleep(min(check_interval, remaining_seconds))
    
    def get_current_waiting_target(self) -> Optional[Dict[str, Any]]:
        """获取当前正在等待的目标
        
        Returns:
            当前等待的目标，如果没有则返回None
        """
        return self.waiting_target
    
    def should_skip_target(self, target: Any, 
                          current_time: Optional[datetime] = None,
                          global_stop_time: Optional[datetime] = None) -> bool:
        """判断是否应该跳过目标
        
        Args:
            target: 目标配置 (TargetConfig对象)
            current_time: 当前时间（默认为now）
            global_stop_time: 全局停止时间
            
        Returns:
            True: 应该跳过
            False: 不应该跳过
        """
        if current_time is None:
            current_time = datetime.now()
        
        target_time = target.start_time
        
        # 检查是否已经过了目标时间太久（超过1小时）
        if current_time > target_time + timedelta(hours=1):
            print(f"目标 {target.name} 已过期超过1小时，跳过")
            return True
        
        # 检查是否超过全局停止时间
        if global_stop_time and target_time >= global_stop_time:
            print(f"目标 {target.name} 时间超过全局停止时间，跳过")
            return True
        
        return False
    
    def calculate_schedule_summary(self, targets: List[Any], 
                                 global_stop_time: Optional[datetime] = None) -> Dict[str, Any]:
        """计算调度摘要
        
        Args:
            targets: 目标列表 (TargetConfig对象列表)
            global_stop_time: 全局停止时间
            
        Returns:
            摘要信息字典
        """
        current_time = datetime.now()
        total_targets = len(targets)
        
        # 分析目标状态
        completed_targets = []
        upcoming_targets = []
        skipped_targets = []
        
        for target in targets:
            if self.should_skip_target(target, current_time, global_stop_time):
                skipped_targets.append(target)
            elif target.start_time <= current_time:
                completed_targets.append(target)
            else:
                upcoming_targets.append(target)
        
        # 计算总观测时间
        total_duration = sum(
            sum(f['exposure'] * f['count'] for f in target.filters) 
            for target in targets
        ) / 3600  # 转换为小时
        
        return {
            'total_targets': total_targets,
            'completed_targets': len(completed_targets),
            'upcoming_targets': len(upcoming_targets),
            'skipped_targets': len(skipped_targets),
            'total_duration_hours': total_duration,
            'next_target': upcoming_targets[0] if upcoming_targets else None,
            'current_time': current_time
        }