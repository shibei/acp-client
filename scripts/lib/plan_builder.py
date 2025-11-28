import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from ACP import ImagingPlan

class ImagingPlanBuilder:
    """成像计划构建类"""
    def __init__(self, config):
        self.config = config
    
    def build(self):
        """创建成像计划"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.config.dryrun else ''}正在创建成像计划...")
        
        filters = []
        for filter_cfg in self.config.filters:
            filters.append({
                'filter_id': filter_cfg['filter_id'],
                'count': filter_cfg['count'],
                'exposure': filter_cfg['exposure'],
                'binning': filter_cfg.get('binning', 1)
            })
        
        plan = ImagingPlan(
            target=self.config.target_name,
            ra=self.config.target_ra,
            dec=self.config.target_dec,
            filters=filters,
            dither=self.config.dither,
            auto_focus=self.config.auto_focus,
            periodic_af_interval=self.config.af_interval
        )
        
        self._print_plan_details()
        return plan
    
    def _print_plan_details(self):
        """打印计划详情"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 成像计划详情:")
        print(f"  - 目标: {self.config.target_name}")
        print(f"  - 坐标: {self.config.target_ra} / {self.config.target_dec}")
        print(f"  - 滤镜数量: {len(self.config.filters)}")
        for i, filter_cfg in enumerate(self.config.filters, 1):
            filter_name = filter_cfg.get('name', f"Filter {filter_cfg['filter_id']}")
            print(f"    {i}. {filter_name}: {filter_cfg['exposure']}秒 x {filter_cfg['count']}张")
        print(f"  - 总图像: {self.config.get_total_images()}张")
        print(f"  - 抖动: {self.config.dither}像素")
        print(f"  - 自动对焦: {'是' if self.config.auto_focus else '否'}")
        print(f"  - 对焦间隔: {self.config.af_interval}分钟")

