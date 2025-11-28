"""
多目标观测计划构建器
为每个目标创建独立的成像计划
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datetime import datetime
from typing import Dict, List
from ACP import ImagingPlan


class MultiTargetPlanBuilder:
    """多目标成像计划构建器"""
    
    def __init__(self, config):
        """初始化构建器
        
        Args:
            config: MultiTargetConfig 实例
        """
        self.config = config
    
    def build_plan_for_target(self, target: Dict) -> ImagingPlan:
        """为特定目标创建成像计划
        
        Args:
            target: 目标配置字典
            
        Returns:
            ImagingPlan 实例
        """
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.config.dryrun else ''}正在为 {target['name']} 创建成像计划...")
        
        # 构建滤镜列表
        filters = []
        for filter_cfg in target['filters']:
            filters.append({
                'filter_id': filter_cfg['filter_id'],
                'count': filter_cfg['count'],
                'exposure': filter_cfg['exposure'],
                'binning': filter_cfg.get('binning', 1)
            })
        
        # 创建成像计划
        plan = ImagingPlan(
            target=target['name'],
            ra=target['ra'],
            dec=target['dec'],
            filters=filters,
            dither=self.config.dither,
            auto_focus=self.config.auto_focus,
            periodic_af_interval=self.config.af_interval
        )
        
        self._print_target_plan_details(target)
        return plan
    
    def build_all_plans(self) -> Dict[str, ImagingPlan]:
        """为所有目标创建成像计划
        
        Returns:
            字典，键为目标名称，值为对应的 ImagingPlan 实例
        """
        plans = {}
        
        for target in self.config.targets:
            plan = self.build_plan_for_target(target)
            plans[target['name']] = plan
        
        return plans
    
    def _print_target_plan_details(self, target: Dict):
        """打印目标的计划详情
        
        Args:
            target: 目标配置字典
        """
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {target['name']} 成像计划详情:")
        print(f"  - 目标: {target['name']}")
        print(f"  - 坐标: RA {target['ra']} / DEC {target['dec']}")
        print(f"  - 开始时间: {target['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  - 滤镜数量: {len(target['filters'])}")
        
        total_images = 0
        total_exposure_time = 0
        
        for i, filter_cfg in enumerate(target['filters'], 1):
            filter_name = filter_cfg.get('name', f"Filter {filter_cfg['filter_id']}")
            images = filter_cfg['count']
            exposure = filter_cfg['exposure']
            total_images += images
            total_exposure_time += images * exposure
            
            print(f"    {i}. {filter_name}: {exposure}秒 x {images}张")
        
        duration_hours = total_exposure_time / 3600
        print(f"  - 总图像: {total_images}张")
        print(f"  - 总曝光时间: {duration_hours:.1f}小时")
        print(f"  - 抖动: {self.config.dither}像素")
        print(f"  - 自动对焦: {'是' if self.config.auto_focus else '否'}")
        print(f"  - 对焦间隔: {self.config.af_interval}分钟")
        print()
    
    def print_summary(self):
        """打印所有目标的计划摘要"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 多目标观测计划摘要:")
        print("="*60)
        
        total_images = 0
        total_exposure_time = 0
        
        for target in self.config.targets:
            target_images = sum(f['count'] for f in target['filters'])
            target_exposure = sum(f['exposure'] * f['count'] for f in target['filters'])
            
            total_images += target_images
            total_exposure_time += target_exposure
            
            duration_hours = target_exposure / 3600
            print(f"{target['name']}:")
            print(f"  - 开始时间: {target['start_time'].strftime('%m-%d %H:%M')}")
            print(f"  - 图像数量: {target_images}张")
            print(f"  - 曝光时间: {duration_hours:.1f}小时")
        
        total_duration = total_exposure_time / 3600
        print(f"\n总计:")
        print(f"  - 总图像: {total_images}张")
        print(f"  - 总曝光时间: {total_duration:.1f}小时")
        print(f"  - 目标数量: {len(self.config.targets)}个")
        print("="*60)