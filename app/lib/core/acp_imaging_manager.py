"""
ACP成像计划管理器
负责成像计划的创建、启动和管理
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .acp_connection_manager import ACPConnectionManager


class ACPImagingManager:
    """ACP成像计划管理器 - 负责成像计划的创建、启动和管理"""
    
    def __init__(self, connection_manager: ACPConnectionManager):
        """初始化成像管理器
        
        Args:
            connection_manager: ACP连接管理器实例
        """
        self.connection_manager = connection_manager
        self.current_plan: Optional[Dict[str, Any]] = None
        self.plan_start_time: Optional[datetime] = None
    
    def create_imaging_plan(self, target: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """创建成像计划
        
        Args:
            target: 目标信息 (TargetConfig对象)
            config: 配置信息
            
        Returns:
            成像计划字典
        """
        plan = {
            'target_name': target.name,
            'ra': target.ra,
            'dec': target.dec,
            'filters': getattr(target, 'filters', []),
            'dither': config.get('dither', 5),
            'auto_focus': config.get('auto_focus', True),
            'af_interval': config.get('af_interval', 120)
        }
        
        # 计算预计完成时间
        total_exposure_time = sum(f['exposure'] * f['count'] for f in plan['filters'])
        estimated_duration = timedelta(seconds=total_exposure_time * 1.2)  # 增加20%缓冲时间
        
        plan['estimated_duration'] = estimated_duration
        plan['estimated_finish_time'] = datetime.now() + estimated_duration
        
        return plan
    
    def start_imaging_plan(self, plan: Dict[str, Any]) -> bool:
        """启动成像计划

        Args:
            plan: 成像计划

        Returns:
            True: 启动成功
            False: 启动失败
        """
        if not self.connection_manager.is_connected:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 未连接到ACP服务器，无法启动成像计划")
            return False

        # 停止当前计划（确保干净启动）
        self.connection_manager.stop_current_operation(wait_seconds=5)

        self.current_plan = plan
        self.plan_start_time = datetime.now()

        if self.connection_manager.dryrun:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟启动成像计划...")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] [OK] 模拟启动成功！")
            self._print_plan_summary(plan, is_dryrun=True)
            return True

        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在启动成像计划...")

            # 获取实际的ACP客户端
            client = self.connection_manager.client
            if not client or client == "DRYRUN_CLIENT":
                return False

            # 将字典转换为ImagingPlan对象
            from .acp_client import ImagingPlan
            imaging_plan = ImagingPlan(
                target=plan['target_name'],
                ra=plan['ra'],
                dec=plan['dec'],
                filters=plan.get('filters', []),
                dither=plan.get('dither', 5),
                auto_focus=plan.get('auto_focus', True),
                periodic_af_interval=plan.get('af_interval', 120)
            )

            success = client.start_imaging_plan(imaging_plan)

            if success:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 成像计划启动成功！")
                self._print_plan_summary(plan)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] 成像计划启动失败！")

            return success

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] 启动成像计划时出错: {e}")
            return False
    
    def get_current_plan_status(self) -> Dict[str, Any]:
        """获取当前成像计划状态
        
        Returns:
            状态字典
        """
        if not self.current_plan:
            return {'has_plan': False}
        
        status = self.connection_manager.get_status()
        elapsed_time = datetime.now() - self.plan_start_time if self.plan_start_time else timedelta(0)
        
        return {
            'has_plan': True,
            'plan': self.current_plan,
            'elapsed_time': elapsed_time,
            'remaining_time': self.current_plan['estimated_duration'] - elapsed_time,
            'acp_status': status
        }
    
    def stop_current_plan(self) -> bool:
        """停止当前成像计划
        
        Returns:
            True: 停止成功
            False: 停止失败
        """
        if not self.current_plan:
            return True  # 没有计划，视为成功
        
        success = self.connection_manager.stop_current_operation()
        if success:
            self.current_plan = None
            self.plan_start_time = None
        
        return success
    
    def _print_plan_summary(self, plan: Dict[str, Any], is_dryrun: bool = False):
        """打印计划摘要
        
        Args:
            plan: 成像计划
            is_dryrun: 是否模拟模式
        """
        prefix = "[DRYRUN] 模拟" if is_dryrun else ""
        
        print(f"\n{'='*70}")
        print(f"{prefix}成像计划已启动！")
        print(f"目标: {plan['target_name']}")
        print(f"坐标: RA {plan['ra']}, DEC {plan['dec']}")
        
        # 计算总图像数和曝光时间
        total_images = sum(f['count'] for f in plan['filters'])
        total_exposure = sum(f['exposure'] * f['count'] for f in plan['filters'])
        
        print(f"总图像数: {total_images}张")
        print(f"总曝光时间: {total_exposure}秒 ({total_exposure/3600:.1f}小时)")
        print(f"预计完成时间: {plan['estimated_finish_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"滤镜配置:")
        for i, filter_cfg in enumerate(plan['filters'], 1):
            filter_name = filter_cfg.get('name', f"Filter {filter_cfg['filter_id']}")
            print(f"  {i}. {filter_name}: {filter_cfg['exposure']}秒 x {filter_cfg['count']}张")
        
        print(f"其他设置:")
        print(f"  抖动: {plan['dither']}像素")
        print(f"  自动对焦: {'开启' if plan['auto_focus'] else '关闭'}")
        if plan['auto_focus']:
            print(f"  对焦间隔: {plan['af_interval']}张")
        
        print(f"{'='*70}")