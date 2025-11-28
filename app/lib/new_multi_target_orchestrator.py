"""
新的多目标观测协调器
基于重构的模块架构
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

# 导入新的核心模块
from lib.core.acp_connection_manager import ACPConnectionManager
from lib.core.acp_imaging_manager import ACPImagingManager
from lib.config.config_manager import MultiTargetConfigManager
from lib.execution.target_observation_executor import TargetObservationExecutor
from lib.scheduling.target_scheduler import TargetScheduler
from lib.utils.log_manager import LogManager
from lib.utils.time_utils import TimeUtils
from lib.utils.observation_utils import ObservationUtils


class NewMultiTargetOrchestrator:
    """新的多目标观测协调器"""
    
    def __init__(self, config_file: str, dry_run: bool = False):
        """初始化协调器
        
        Args:
            config_file: 配置文件路径
            dry_run: 是否为DRYRUN模式
        """
        self.config_file = config_file
        self.dry_run = dry_run
        self.config_manager = None
        self.connection_manager = None
        self.imaging_manager = None
        self.scheduler = None
        self.executor = None
        self.logger = None
        
        # 状态回调函数
        self.status_callbacks = []
        
        # 初始化组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化所有组件"""
        try:
            # 1. 配置管理器
            self.config_manager = MultiTargetConfigManager(self.config_file, self.dry_run)
            config = self.config_manager.get_config()
            
            # 2. 日志管理器
            self.logger = LogManager(
                name="MultiTargetOrchestrator",
                log_dir=config.global_settings.get('log_dir', 'logs'),
                log_level=config.global_settings.get('log_level', 'INFO'),
                enable_console=True
            )
            
            self.logger.info("正在初始化多目标观测协调器...")
            
            # 3. ACP连接管理器
            self.connection_manager = ACPConnectionManager(
                server_url=config.acp_server.url,
                username=config.acp_server.username,
                password=config.acp_server.password,
                dryrun=self.dry_run
            )
            
            # 4. ACP成像管理器
            self.imaging_manager = ACPImagingManager(
                connection_manager=self.connection_manager
            )
            
            # 5. 目标调度器
            self.scheduler = TargetScheduler(
                log_manager=self.logger,
                dryrun=self.dry_run
            )
            
            # 6. 目标观测执行器
            self.executor = TargetObservationExecutor(
                connection_manager=self.connection_manager,
                imaging_manager=self.imaging_manager,
                log_manager=self.logger,
                dryrun=self.dry_run
            )
            
            # 添加状态回调
            self.executor.add_status_callback(self._on_observation_status)
            
            self.logger.info("多目标观测协调器初始化完成")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"初始化失败: {e}")
            raise
    
    def add_status_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """添加状态回调函数
        
        Args:
            callback: 回调函数，接收(status, data)参数
        """
        self.status_callbacks.append(callback)
    
    def _on_observation_status(self, data: Dict[str, Any]):
        """观测状态回调"""
        # 记录日志
        if self.logger:
            self.logger.debug(f"观测状态更新: {data}")
        
        # 调用外部回调
        for callback in self.status_callbacks:
            try:
                callback(data)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"状态回调执行失败: {e}")
    
    def print_banner(self):
        """打印程序横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        多目标自动观测系统 v2.0                                 ║
║                        基于重构架构的观测协调器                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
        if self.logger:
            self.logger.info("多目标自动观测系统启动")
    
    def validate_targets(self) -> List[Dict[str, Any]]:
        """验证目标列表
        
        Returns:
            验证结果列表
        """
        self.logger.info("正在验证目标列表...")
        
        config = self.config_manager.get_config()
        targets = config.targets
        
        results = []
        
        for i, target in enumerate(targets):
            try:
                # 解析坐标
                ra_deg, dec_deg = ObservationUtils.parse_ra_dec(target.ra, target.dec)
                
                # 检查可观测性
                observability = ObservationUtils.is_observable(
                    ra_deg, dec_deg,
                    config.observatory.latitude_deg,
                    config.observatory.min_altitude
                )
                
                # 解析时间
                if target.start_time:
                    start_time = TimeUtils.parse_time_string(target.start_time.strftime('%Y-%m-%d %H:%M:%S'))
                    time_valid = start_time is not None
                else:
                    start_time = None
                    time_valid = True
                
                result = {
                    'index': i + 1,
                    'name': target.name,
                    'ra': target.ra,
                    'dec': target.dec,
                    'start_time': target.start_time.strftime('%Y-%m-%d %H:%M:%S') if target.start_time else None,
                    'ra_deg': ra_deg,
                    'dec_deg': dec_deg,
                    'observability': observability,
                    'time_valid': time_valid,
                    'valid': observability['is_observable'] and time_valid
                }
                
                results.append(result)
                
                self.logger.info(f"目标 {target.name}: "
                               f"可观测性={observability['is_observable']}, "
                               f"时间有效={time_valid}")
                
            except Exception as e:
                self.logger.error(f"验证目标 {target.name} 失败: {e}")
                results.append({
                    'index': i + 1,
                    'name': target.name,
                    'ra': target.ra,
                    'dec': target.dec,
                    'start_time': target.start_time.strftime('%Y-%m-%d %H:%M:%S') if target.start_time else None,
                    'valid': False,
                    'error': str(e)
                })
        
        return results
    
    def calculate_schedule_summary(self) -> Dict[str, Any]:
        """计算调度摘要
        
        Returns:
            调度摘要信息
        """
        self.logger.info("正在计算调度摘要...")
        
        config = self.config_manager.get_config()
        
        # 获取验证结果
        validation_results = self.validate_targets()
        
        # 计算调度摘要
        summary = self.scheduler.calculate_schedule_summary(
            config.targets,
            config.schedule.stop_time if config.schedule else None
        )
        
        # 添加验证结果
        summary['validation_results'] = validation_results
        summary['valid_targets'] = sum(1 for r in validation_results if r['valid'])
        summary['invalid_targets'] = sum(1 for r in validation_results if not r['valid'])
        
        # 记录日志
        self.logger.log_schedule_summary(
            summary['total_targets'],
            summary['valid_targets'],
            summary.get('start_time', summary.get('current_time')),
            summary.get('end_time', summary.get('current_time'))
        )
        
        return summary
    
    def wait_for_target_time(self, target: Any) -> bool:
        """等待目标观测时间
        
        Args:
            target: 目标配置 (TargetConfig对象)
            
        Returns:
            是否成功等待
        """
        return self.scheduler.wait_for_target_time(target)
    
    def execute_target_observation(self, target: Any) -> bool:
        """执行单个目标观测
        
        Args:
            target: 目标配置 (TargetConfig对象)
            
        Returns:
            是否成功执行
        """
        config = self.config_manager.get_config()
        return self.executor.execute_target(target, config.__dict__)
    
    def monitor_target_observation(self, target: Any, 
                                 timeout_minutes: int = 60) -> Dict[str, Any]:
        """监控目标观测
        
        Args:
            target: 目标配置 (TargetConfig对象)
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            观测结果
        """
        return self.executor.monitor_target_observation(target, timeout_minutes)
    
    def run_observation_sequence(self) -> Dict[str, Any]:
        """运行完整的观测序列
        
        Returns:
            观测序列结果
        """
        self.print_banner()
        
        self.logger.info("开始执行观测序列...")
        
        # 获取配置
        config = self.config_manager.get_config()
        targets = config.targets
        
        # 计算调度摘要
        schedule_summary = self.calculate_schedule_summary()
        
        self.logger.info(f"计划观测 {len(targets)} 个目标")
        
        # 连接ACP服务器
        if not self.connection_manager.connect():
            self.logger.error("无法连接到ACP服务器")
            return {
                'success': False,
                'error': '无法连接到ACP服务器',
                'completed_targets': 0,
                'failed_targets': 0
            }
        
        # 执行观测序列
        results = {
            'success': True,
            'completed_targets': 0,
            'failed_targets': 0,
            'target_results': []
        }
        
        for i, target in enumerate(targets):
            target_name = target.name
            self.logger.info(f"开始观测目标 {i+1}/{len(targets)}: {target_name}")
            
            try:
                # 等待目标时间
                if not self.wait_for_target_time(target):
                    self.logger.warning(f"跳过目标 {target_name}：时间等待失败或超时")
                    results['failed_targets'] += 1
                    continue
                
                # 执行目标观测
                if not self.execute_target_observation(target):
                    self.logger.error(f"目标 {target_name} 观测执行失败")
                    results['failed_targets'] += 1
                    continue
                
                # 监控观测过程
                observation_result = self.monitor_target_observation(target)
                
                if observation_result['success']:
                    self.logger.info(f"目标 {target_name} 观测完成")
                    results['completed_targets'] += 1
                else:
                    self.logger.error(f"目标 {target_name} 观测失败: {observation_result.get('error', '未知错误')}")
                    results['failed_targets'] += 1
                
                results['target_results'].append({
                    'target': target_name,
                    'success': observation_result['success'],
                    'result': observation_result
                })
                
            except Exception as e:
                self.logger.error(f"目标 {target_name} 观测过程中出错: {e}")
                results['failed_targets'] += 1
                results['target_results'].append({
                    'target': target_name,
                    'success': False,
                    'error': str(e)
                })
        
        # 断开连接
        self.connection_manager.disconnect()
        
        # 总结结果
        results['success'] = results['failed_targets'] == 0
        
        self.logger.info(f"观测序列完成: 成功 {results['completed_targets']} 个, "
                        f"失败 {results['failed_targets']} 个")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态
        
        Returns:
            状态信息
        """
        status = {
            'initialized': all([
                self.config_manager is not None,
                self.connection_manager is not None,
                self.imaging_manager is not None,
                self.scheduler is not None,
                self.executor is not None,
                self.logger is not None
            ]),
            'connected': self.connection_manager.get_status() if self.connection_manager else False,
            'config_loaded': self.config_manager is not None and self.config_manager.get_config() is not None,
            'dry_run': self.dry_run
        }
        
        return status
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("正在清理资源...")
        
        # 断开连接
        if self.connection_manager:
            self.connection_manager.disconnect()
        
        # 关闭日志
        if self.logger:
            self.logger.info("多目标观测协调器关闭")


# 向后兼容的别名
MultiTargetOrchestrator = NewMultiTargetOrchestrator