"""
目标观测执行器
负责单个目标的观测执行和监控
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from ..core.acp_imaging_manager import ACPImagingManager
from ..core.acp_connection_manager import ACPConnectionManager
from ..utils.time_utils import TimeUtils
from ..utils.observation_utils import ObservationUtils
from ..utils.log_manager import LogManager


class TargetObservationExecutor:
    """目标观测执行器 - 负责单个目标的观测执行和监控"""
    
    def __init__(self, connection_manager: ACPConnectionManager, 
                 imaging_manager: ACPImagingManager,
                 log_manager: LogManager,
                 dryrun: bool = False):
        """初始化目标观测执行器
        
        Args:
            connection_manager: ACP连接管理器
            imaging_manager: 成像管理器
            log_manager: 日志管理器
            dryrun: 是否模拟模式
        """
        self.connection_manager = connection_manager
        self.imaging_manager = imaging_manager
        self.log_manager = log_manager
        self.dryrun = dryrun
        self.current_target: Optional[Dict[str, Any]] = None
        self.observation_start_time: Optional[datetime] = None
        self.status_callbacks: list[Callable] = []
    
    def add_status_callback(self, callback: Callable):
        """添加状态回调函数
        
        Args:
            callback: 回调函数，接收状态字典
        """
        self.status_callbacks.append(callback)
    
    def execute_target(self, target: Any, global_config: Dict[str, Any]) -> bool:
        """执行目标观测
        
        Args:
            target: 目标配置 (TargetConfig对象)
            global_config: 全局配置
            
        Returns:
            True: 观测成功
            False: 观测失败
        """
        target_name = target.name
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.dryrun else ''}开始执行 {target_name} 观测任务")
        self.log_manager.info(f"{'[DRYRUN] ' if self.dryrun else ''}开始执行 {target_name} 观测任务")
        
        self.current_target = target
        self.observation_start_time = datetime.now()
        
        try:
            # 创建成像计划
            plan = self.imaging_manager.create_imaging_plan(target, global_config)
            
            # 启动成像
            success = self.imaging_manager.start_imaging_plan(plan)
            
            if success:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {target_name} 观测计划已启动")
                self.log_manager.info(f"{target_name} 观测计划已启动")
                
                # 监控观测过程
                self._monitor_observation(target)
                
                return True
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {target_name} 观测计划启动失败")
                self.log_manager.error(f"{target_name} 观测计划启动失败")
                return False
                
        except Exception as e:
            error_msg = f"{target_name} 观测执行出错: {str(e)}"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            self.log_manager.error(error_msg)
            return False
        finally:
            self.current_target = None
            self.observation_start_time = None
    
    def _monitor_observation(self, target: Any):
        """监控观测过程
        
        Args:
            target: 目标配置 (TargetConfig对象)
        """
        target_name = target.name
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始监控 {target_name} 观测状态（每30秒刷新）")
        print("按 Ctrl+C 可跳过当前目标监控，继续下一个目标")
        print("="*60)
        
        try:
            while True:
                current_time = datetime.now()
                
                # 获取状态
                status = self._get_observation_status(target, current_time)
                
                # 执行状态回调
                for callback in self.status_callbacks:
                    callback(status)
                
                # 打印状态
                self._print_status(status)
                
                # 检查是否完成
                if status['is_completed']:
                    break
                
                # 检查是否出错
                if status['has_error']:
                    print(f"[{current_time.strftime('%H:%M:%S')}] 观测出现错误，停止监控")
                    break
                
                time.sleep(30)  # 30秒检查一次
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 用户中断监控，继续执行")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 监控过程出错: {e}")
            self.log_manager.error(f"监控 {target_name} 时出错: {e}")
    
    def _get_observation_status(self, target: Any, current_time: datetime) -> Dict[str, Any]:
        """获取观测状态
        
        Args:
            target: 目标配置 (TargetConfig对象)
            current_time: 当前时间
            
        Returns:
            状态字典
        """
        # 获取ACP状态
        acp_status = self.connection_manager.get_status()
        
        # 获取当前计划状态
        plan_status = self.imaging_manager.get_current_plan_status()
        
        # 计算观测进度
        elapsed_time = current_time - self.observation_start_time if self.observation_start_time else timedelta(0)
        estimated_duration = plan_status.get('plan', {}).get('estimated_duration', timedelta(hours=1))
        progress = min(elapsed_time.total_seconds() / estimated_duration.total_seconds(), 1.0)
        
        # 检查是否完成
        is_completed = not acp_status.get('is_running', False)
        
        # 检查中天反转需求
        meridian_info = self._check_meridian_flip(target, current_time)
        
        return {
            'target_name': target.name,
            'current_time': current_time,
            'elapsed_time': elapsed_time,
            'estimated_duration': estimated_duration,
            'progress': progress,
            'is_completed': is_completed,
            'has_error': acp_status.get('error') is not None,
            'acp_status': acp_status,
            'plan_status': plan_status,
            'meridian_info': meridian_info
        }
    
    def _check_meridian_flip(self, target: Any, current_time: datetime) -> Dict[str, Any]:
        """检查中天反转
        
        Args:
            target: 目标配置 (TargetConfig对象)
            current_time: 当前时间
            
        Returns:
            中天反转信息
        """
        # 这里可以集成中天反转管理器
        # 暂时返回基本信息
        return {
            'check_needed': False,
            'wait_needed': False,
            'message': '中天反转检查未启用'
        }
    
    def _print_status(self, status: Dict[str, Any]):
        """打印状态信息
        
        Args:
            status: 状态字典
        """
        current_time = status['current_time'].strftime('%H:%M:%S')
        target_name = status['target_name']
        
        # 基础状态
        if status['acp_status'].get('is_running'):
            status_msg = f"[{current_time}] {target_name} 状态: 运行中 ✓"
        else:
            status_msg = f"[{current_time}] {target_name} 状态: 已停止 ✗"
        
        # 进度信息
        progress = status['progress'] * 100
        elapsed_min = status['elapsed_time'].total_seconds() / 60
        total_min = status['estimated_duration'].total_seconds() / 60
        
        status_msg += f" | 进度: {progress:.1f}% ({elapsed_min:.0f}/{total_min:.0f}分钟)"
        
        # 滤镜信息（如果有）
        if status['acp_status'].get('filter'):
            status_msg += f" | 滤镜: {status['acp_status']['filter']}"
        
        # 中天反转信息
        if status['meridian_info'].get('wait_needed'):
            status_msg += f" | 中天反转: {status['meridian_info']['message']}"
        
        print(status_msg)
        self.log_manager.info(status_msg)
    
    def monitor_target_observation(self, target: Any, timeout_minutes: int = 60) -> Dict[str, Any]:
        """监控目标观测
        
        Args:
            target: 目标配置 (TargetConfig对象)
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            观测结果字典
        """
        target_name = target.name
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始监控 {target_name} 观测状态（每30秒刷新）")
        print("按 Ctrl+C 可跳过当前目标监控，继续下一个目标")
        print("="*60)
        
        result = {
            'success': True,
            'target': target_name,
            'start_time': datetime.now(),
            'end_time': None,
            'error': None
        }
        
        try:
            while True:
                current_time = datetime.now()
                
                # 获取状态
                status = self._get_observation_status(target, current_time)
                
                # 执行状态回调
                for callback in self.status_callbacks:
                    callback(status)
                
                # 打印状态
                self._print_status(status)
                
                # 检查是否完成
                if status['is_completed']:
                    result['end_time'] = current_time
                    break
                
                # 检查是否出错
                if status['has_error']:
                    result['success'] = False
                    result['error'] = status['acp_status'].get('error', '未知错误')
                    print(f"[{current_time.strftime('%H:%M:%S')}] 观测出现错误，停止监控")
                    break
                
                # 检查超时
                elapsed_minutes = (current_time - result['start_time']).total_seconds() / 60
                if elapsed_minutes >= timeout_minutes:
                    result['success'] = False
                    result['error'] = '观测超时'
                    print(f"[{current_time.strftime('%H:%M:%S')}] 观测超时（{timeout_minutes}分钟）")
                    break
                
                time.sleep(30)  # 30秒检查一次
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 用户中断监控，继续执行")
            result['error'] = '用户中断'
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 监控过程出错: {e}")
            self.log_manager.error(f"监控 {target_name} 时出错: {e}")
            result['success'] = False
            result['error'] = str(e)
        
        return result