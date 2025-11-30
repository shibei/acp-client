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
from ..meridian_flip_manager import MeridianFlipManager


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
        self.meridian_manager: Optional[MeridianFlipManager] = None
        self.retry_config: Dict[str, Any] = {
            'enabled': True,
            'max_attempts': 3,
            'retry_interval_seconds': 300,
            'retry_on_errors': ['connection_timeout', 'acp_server_error', 'meridian_flip_failed', 'observation_timeout']
        }
    
    def add_status_callback(self, callback: Callable):
        """添加状态回调函数
        
        Args:
            callback: 回调函数，接收状态字典
        """
        self.status_callbacks.append(callback)
    
    def set_retry_config(self, retry_config: Dict[str, Any]):
        """设置重试配置
        
        Args:
            retry_config: 重试配置字典
        """
        self.retry_config.update(retry_config)
        self.log_manager.info(f"重试配置已更新: {retry_config}")
    
    def set_meridian_manager(self, meridian_manager: MeridianFlipManager):
        """设置中天管理器
        
        Args:
            meridian_manager: 中天反转管理器
        """
        self.meridian_manager = meridian_manager
    
    def execute_target(self, target: Any, global_config: Dict[str, Any]) -> bool:
        """执行目标观测（支持重试）
        
        Args:
            target: 目标配置 (TargetConfig对象)
            global_config: 全局配置
            
        Returns:
            True: 观测成功
            False: 观测失败
        """
        target_name = target.name
        current_time = datetime.now()
        # print(f"\n[{current_time.strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.dryrun else ''}开始执行 {target_name} 观测任务")
        self.log_manager.info(f"{'[DRYRUN] ' if self.dryrun else ''}开始执行 {target_name} 观测任务")
        
        # 获取重试配置
        retry_enabled = self.retry_config.get('enabled', True)
        max_attempts = self.retry_config.get('max_attempts', 3)
        retry_interval = self.retry_config.get('retry_interval_seconds', 300)
        retry_on_errors = self.retry_config.get('retry_on_errors', [])
        
        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                # print(f"\n[{current_time.strftime('%H:%M:%S')}] 🔄 第 {attempt}/{max_attempts} 次重试，等待 {retry_interval} 秒...")
                self.log_manager.info(f"第 {attempt}/{max_attempts} 次重试，等待 {retry_interval} 秒")
                time.sleep(retry_interval)
                current_time = datetime.now()
            
            success = self._execute_target_attempt(target, global_config, attempt)
            
            if success:
                # print(f"[{current_time.strftime('%H:%M:%S')}] ✅ {target_name} 观测成功")
                self.log_manager.info(f"{target_name} 观测成功")
                return True
            
            # 检查是否需要重试
            if not retry_enabled or attempt >= max_attempts:
                break
                
            # 检查错误类型是否支持重试
            last_error = getattr(self, '_last_error', None)
            if last_error and retry_on_errors:
                error_type = self._get_error_type(last_error)
                if error_type not in retry_on_errors:
                    # print(f"[{current_time.strftime('%H:%M:%S')}] ❌ 错误类型 '{error_type}' 不支持重试")
                    break
        
        # print(f"[{current_time.strftime('%H:%M:%S')}] ❌ {target_name} 观测失败（重试{max_attempts}次后）")
        self.log_manager.error(f"{target_name} 观测失败（重试{max_attempts}次后）")
        return False
    
    def _execute_target_attempt(self, target: Any, global_config: Dict[str, Any], attempt: int) -> bool:
        """执行单次目标观测尝试
        
        Args:
            target: 目标配置 (TargetConfig对象)
            global_config: 全局配置
            attempt: 尝试次数
            
        Returns:
            True: 观测成功
            False: 观测失败
        """
        
        # 获取目标名称和当前时间
        target_name = target.name
        current_time = datetime.now()
        
        # 显示尝试次数信息
        if attempt > 1:
            # print(f"[{current_time.strftime('%H:%M:%S')}] 🔄 第 {attempt} 次尝试执行 {target_name}")
            self.log_manager.info(f"第 {attempt} 次尝试执行 {target_name}")
        
        # 显示中天时间（如果中天管理器可用）
        if self.meridian_manager:
            try:
                # 检查是否有手动指定的中天时间
                if hasattr(target, 'meridian_time') and target.meridian_time:
                    # 使用手动指定的中天时间
                    today = current_time.date()
                    meridian_time_str = f"{today} {target.meridian_time}"
                    meridian_time = datetime.strptime(meridian_time_str, '%Y-%m-%d %H:%M:%S')
                    meridian_str = target.meridian_time
                    # print(f"[{current_time.strftime('%H:%M:%S')}] 🌟 {target_name} 中天时间: {meridian_str} (手动指定)")
                    self.log_manager.info(f"{target_name} 中天时间: {meridian_str} (手动指定)")
                else:
                    # 自动计算中天时间
                    meridian_time = self.meridian_manager.calculate_meridian_time(
                        target.ra, target.dec, current_time
                    )
                    if meridian_time:
                        meridian_str = meridian_time.strftime('%H:%M:%S')
                        # print(f"[{current_time.strftime('%H:%M:%S')}] 🌟 {target_name} 中天时间: {meridian_str}")
                        self.log_manager.info(f"{target_name} 中天时间: {meridian_str}")
                    else:
                        # print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️ 无法计算 {target_name} 的中天时间")
                        self.log_manager.warning(f"无法计算 {target_name} 的中天时间")
            except Exception as e:
                # print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️ 计算中天时间出错: {str(e)}")
                self.log_manager.warning(f"计算 {target_name} 中天时间出错: {str(e)}")
        
        self.current_target = target
        self.observation_start_time = datetime.now()
        
        try:
            # 创建成像计划
            plan = self.imaging_manager.create_imaging_plan(target, global_config)
            
            # 启动成像
            success, error_msg = self.imaging_manager.start_imaging_plan(plan)
            
            if success:
                # print(f"[{datetime.now().strftime('%H:%M:%S')}] {target_name} 观测计划已启动")
                self.log_manager.info(f"{target_name} 观测计划已启动")
                
                # 监控观测过程
                monitor_result = self._monitor_observation(target)
                
                # 记录错误信息（如果有）
                if monitor_result and not monitor_result.get('success', True):
                    self._last_error = monitor_result.get('error', '未知错误')
                
                return monitor_result.get('success', True) if monitor_result else True
            else:
                error_msg = f"{target_name} 观测计划启动失败: {error_msg}"
                # print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
                self.log_manager.error(error_msg)
                self._last_error = error_msg
                return False
                
        except Exception as e:
            error_msg = f"{target_name} 观测执行出错: {str(e)}"
            # print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            self.log_manager.error(error_msg)
            self._last_error = str(e)
            return False
        
        finally:
            self.current_target = None
            self.observation_start_time = None
    
    def _get_error_type(self, error: str) -> str:
        """获取错误类型
        
        Args:
            error: 错误信息
            
        Returns:
            错误类型
        """
        error_lower = str(error).lower()
        
        # 401认证错误
        if '401' in error_lower or 'access denied' in error_lower or 'invalid login' in error_lower:
            return 'authentication_failed'
        elif 'connection' in error_lower and 'timeout' in error_lower:
            return 'connection_timeout'
        elif 'acp' in error_lower and 'server' in error_lower:
            return 'acp_server_error'
        elif 'observatory' in error_lower and 'offline' in error_lower:
            return 'observatory_offline'
        elif 'meridian' in error_lower and 'flip' in error_lower:
            return 'meridian_flip_failed'
        elif 'observation' in error_lower and 'timeout' in error_lower:
            return 'observation_timeout'
        elif 'imaging' in error_lower and 'plan' in error_lower:
            return 'imaging_plan_failed'
        elif 'status' in error_lower and 'check' in error_lower:
            return 'status_check_failed'
        elif 'telescope' in error_lower and ('not responding' in error_lower or 'error' in error_lower):
            return 'telescope_error'
        elif 'camera' in error_lower and ('error' in error_lower or 'not found' in error_lower):
            return 'camera_error'
        else:
            return 'unknown_error'
    
    def _monitor_observation(self, target: Any):
        """监控观测过程
        
        Args:
            target: 目标配置 (TargetConfig对象)
            
        Returns:
            dict: 监控结果，包含 success 和 error 信息
        """
        target_name = target.name
        # print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始监控 {target_name} 观测状态（每30秒刷新）")
        # print("按 Ctrl+C 可跳过当前目标监控，继续下一个目标")
        # print("="*60)
        
        self.log_manager.info(f"开始监控 {target_name} 观测状态（每30秒刷新）")
        self.log_manager.info("按 Ctrl+C 可跳过当前目标监控，继续下一个目标")
        self.log_manager.info("="*60)
        
        result = {'success': True, 'error': None}
        last_status = None
        
        try:
            while True:
                current_time = datetime.now()
                
                # 获取状态
                status = self._get_observation_status(target, current_time)
                
                if status is None:
                    # print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️ 无法获取 {target_name} 的观测状态")
                    self.log_manager.warning(f"无法获取 {target_name} 的观测状态")
                    time.sleep(5)
                    continue
                
                # 检查是否有状态更新
                if status != last_status:
                    last_status = status
                    
                    # 执行状态回调
                    for callback in self.status_callbacks:
                        try:
                            callback(target, status)
                        except Exception as e:
                            self.log_manager.warning(f"状态回调出错: {str(e)}")
                    
                    # 显示状态信息
                    self._display_status(target_name, status)
                
                # 检查是否完成
                if self._is_observation_complete(status):
                    # print(f"[{current_time.strftime('%H:%M:%S')}] ✅ {target_name} 观测完成")
                    self.log_manager.info(f"{target_name} 观测完成")
                    return {'success': True}
                
                # 检查是否需要等待中天反转
                if status.get('meridian_info', {}).get('wait_needed', False):
                    # print(f"[{current_time.strftime('%H:%M:%S')}] ⏳ {target_name} 等待中天反转...")
                    self.log_manager.info(f"{target_name} 等待中天反转")
                    
                    # 等待中天反转
                    wait_success = self.meridian_manager.wait_for_meridian_flip(target)
                    
                    if wait_success:
                        # print(f"[{current_time.strftime('%H:%M:%S')}] ✅ {target_name} 中天反转等待完成")
                        self.log_manager.info(f"{target_name} 中天反转等待完成")
                    else:
                        # print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️ {target_name} 中天反转等待失败，继续监控...")
                        self.log_manager.warning(f"{target_name} 中天反转等待失败，继续监控")
                
                # 检查是否有错误状态
                if status.get('error'):
                    error_msg = f"{target_name} 观测出现错误: {status['error']}"
                    # print(f"[{current_time.strftime('%H:%M:%S')}] ❌ {error_msg}")
                    self.log_manager.error(error_msg)
                    return {'success': False, 'error': status['error']}
                
                # 短暂休眠
                time.sleep(self.status_check_interval)
                
        except KeyboardInterrupt:
            # print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⏹️ 用户中断观测")
            self.log_manager.info(f"用户中断 {target_name} 观测")
            return {'success': False, 'error': 'user_interrupted'}
        except Exception as e:
            error_msg = f"监控 {target_name} 时出错: {str(e)}"
            # print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            self.log_manager.error(error_msg)
            return {'success': False, 'error': str(e)}
    
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
        # 如果目标配置中关闭了中天等待，直接返回不需要等待
        if hasattr(target, 'enable_meridian_wait') and not target.enable_meridian_wait:
            return {
                'status': 'disabled',
                'message': '该目标已禁用中天等待',
                'wait_needed': False,
                'disabled_by_target': True
            }
        
        # 如果中天管理器可用，使用实际的中天反转检查
        if self.meridian_manager:
            try:
                return self.meridian_manager.check_meridian_flip_needed(
                    target.ra, target.dec, current_time
                )
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'中天反转检查出错: {str(e)}',
                    'wait_needed': False
                }
        
        # 如果中天管理器不可用，返回默认信息
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
            status_msg = f"[{current_time}] {target_name} 状态: 运行中 [OK]"
        else:
            status_msg = f"[{current_time}] {target_name} 状态: 已停止 [STOP]"
        
        # 进度信息
        progress = status['progress'] * 100
        elapsed_min = status['elapsed_time'].total_seconds() / 60
        total_min = status['estimated_duration'].total_seconds() / 60
        
        status_msg += f" | 进度: {progress:.1f}% ({elapsed_min:.0f}/{total_min:.0f}分钟)"
        
        # 滤镜信息（如果有）
        if status['acp_status'].get('filter'):
            status_msg += f" | 滤镜: {status['acp_status']['filter']}"
        
        # 中天反转信息
        meridian_info = status['meridian_info']
        if meridian_info.get('wait_needed'):
            status_msg += f" | 中天反转: {meridian_info['message']}"
        elif meridian_info.get('status') == 'disabled':
            status_msg += f" | 中天反转: 已禁用"
        elif meridian_info.get('status') == 'error':
            status_msg += f" | 中天反转: 错误"
        
        # print(status_msg)
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
        # print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始监控 {target_name} 观测状态（每30秒刷新）")
        # print("按 Ctrl+C 可跳过当前目标监控，继续下一个目标")
        # print("="*60)
        
        self.log_manager.info(f"开始监控 {target_name} 观测状态（每30秒刷新）")
        self.log_manager.info("按 Ctrl+C 可跳过当前目标监控，继续下一个目标")
        self.log_manager.info("="*60)
        
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
                    # print(f"[{current_time.strftime('%H:%M:%S')}] 观测出现错误，停止监控")
                    self.log_manager.info("观测出现错误，停止监控")
                    break
                
                # 检查超时
                elapsed_minutes = (current_time - result['start_time']).total_seconds() / 60
                if elapsed_minutes >= timeout_minutes:
                    result['success'] = False
                    result['error'] = '观测超时'
                    # print(f"[{current_time.strftime('%H:%M:%S')}] 观测超时（{timeout_minutes}分钟）")
                    self.log_manager.info(f"观测超时（{timeout_minutes}分钟）")
                    break
                
                # 检查中天反转等待
                if status['meridian_info'].get('wait_needed'):
                    # print(f"[{current_time.strftime('%H:%M:%S')}] 检测到中天反转等待需求")
                    self.log_manager.info("检测到中天反转等待需求")
                    wait_success = self.meridian_manager.wait_for_meridian_flip(
                        target.ra, target.dec, current_time
                    )
                    if not wait_success:
                        result['success'] = False
                        result['error'] = '中天反转等待被中断'
                        # print(f"[{current_time.strftime('%H:%M:%S')}] 中天反转等待被中断")
                        self.log_manager.info("中天反转等待被中断")
                        break
                
                time.sleep(30)  # 30秒检查一次
                
        except KeyboardInterrupt:
            # print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 用户中断监控，继续执行")
            self.log_manager.info("用户中断监控，继续执行")
            result['error'] = '用户中断'
        except Exception as e:
            # print(f"[{datetime.now().strftime('%H:%M:%S')}] 监控过程出错: {e}")
            self.log_manager.error(f"监控过程出错: {e}")
            result['success'] = False
            result['error'] = str(e)
        
        return result