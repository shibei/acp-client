"""
多目标观测配置类
支持按时间顺序执行多个观测目标
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import yaml
from datetime import datetime
from typing import List, Dict, Optional


class MultiTargetConfig:
    """多目标观测配置类"""
    
    def __init__(self, config_file: str):
        """从YAML文件加载配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 解析配置
        self._parse_config()
    
    def _parse_config(self):
        """解析配置文件"""
        # 服务器配置
        acp_config = self.config.get('acp_server', {})
        self.acp_url = acp_config.get('url', '')
        self.acp_user = acp_config.get('username', '')
        self.acp_password = acp_config.get('password', '')
        
        # 调度配置
        schedule_config = self.config.get('schedule', {})
        self.global_stop_time = self._parse_time(schedule_config.get('stop_time'))
        
        # 全局设置
        global_settings = self.config.get('global_settings', {})
        self.dither = global_settings.get('dither', 5)
        self.auto_focus = global_settings.get('auto_focus', True)
        self.af_interval = global_settings.get('af_interval', 120)
        self.dryrun = global_settings.get('dryrun', False)
        
        # 目标配置
        self.targets = []
        for target_cfg in self.config.get('targets', []):
            target = {
                'name': target_cfg['name'],
                'ra': target_cfg['ra'],
                'dec': target_cfg['dec'],
                'start_time': self._parse_time(target_cfg['start_time']),
                'priority': target_cfg.get('priority', 1),
                'filters': target_cfg.get('filters', [])
            }
            self.targets.append(target)
        
        # 按开始时间和优先级排序
        self.targets.sort(key=lambda x: (x['start_time'], x['priority']))
    
    def _parse_time(self, time_str: Optional[str]) -> Optional[datetime]:
        """解析时间字符串"""
        if not time_str:
            return None
        try:
            return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
    
    def get_target_by_name(self, name: str) -> Optional[Dict]:
        """通过名称获取目标配置"""
        for target in self.targets:
            if target['name'] == name:
                return target
        return None
    
    def get_targets_in_time_order(self) -> List[Dict]:
        """获取按时间排序的目标列表"""
        return self.targets
    
    def get_next_target(self, current_time: datetime) -> Optional[Dict]:
        """获取下一个要观测的目标"""
        for target in self.targets:
            if target['start_time'] and target['start_time'] > current_time:
                return target
        return None
    
    def get_current_target(self, current_time: datetime) -> Optional[Dict]:
        """获取当前应该观测的目标（基于时间）"""
        current_target = None
        for target in self.targets:
            if target['start_time'] and target['start_time'] <= current_time:
                current_target = target
        return current_target
    
    def calculate_target_duration(self, target: Dict) -> float:
        """计算目标观测所需时间（小时）"""
        total_seconds = sum(f['exposure'] * f['count'] for f in target['filters'])
        return total_seconds / 3600
    
    def get_total_duration(self) -> float:
        """计算所有目标的总观测时间（小时）"""
        total = 0
        for target in self.targets:
            total += self.calculate_target_duration(target)
        return total
    
    def print_schedule(self):
        """打印观测计划时间表"""
        print("="*80)
        print("多目标观测计划")
        if self.dryrun:
            print("*** DRYRUN 模式 - 仅模拟运行 ***")
        print("="*80)
        
        if self.global_stop_time:
            print(f"全局停止时间: {self.global_stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"服务器: {self.acp_url}")
        print(f"总目标数: {len(self.targets)}")
        print(f"预计总时间: {self.get_total_duration():.1f}小时")
        print()
        
        for i, target in enumerate(self.targets, 1):
            duration = self.calculate_target_duration(target)
            print(f"目标 {i}: {target['name']}")
            print(f"  开始时间: {target['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  坐标: RA {target['ra']}, DEC {target['dec']}")
            print(f"  预计持续时间: {duration:.1f}小时")
            print(f"  滤镜配置 ({len(target['filters'])}个滤镜):")
            
            for j, filter_cfg in enumerate(target['filters'], 1):
                filter_name = filter_cfg.get('name', f"Filter {filter_cfg['filter_id']}")
                print(f"    {j}. {filter_name}: {filter_cfg['exposure']}秒 x {filter_cfg['count']}张")
            print()
        
        print("="*80)