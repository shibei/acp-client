"""
多目标观测编排器
按时间顺序自动执行多个观测目标
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import time
from datetime import datetime, timedelta
from ACP import LogManager
from lib.multi_target_plan_builder import MultiTargetPlanBuilder
from lib.time_manager import TimeManager
from lib.acp_mamager import ACPManager
from lib.multi_target_config import MultiTargetConfig


class MultiTargetOrchestrator:
    """多目标观测编排器"""
    
    def __init__(self, config_file: str):
        """初始化编排器
        
        Args:
            config_file: 配置文件路径
        """
        self.config = MultiTargetConfig(config_file)
        self.log_manager = LogManager('MultiTarget_Observe')
        self.time_manager = TimeManager(self.config.dryrun)
        self.acp_manager = ACPManager(self.config, self.log_manager)
        self.plan_builder = MultiTargetPlanBuilder(self.config)
        
        # 状态跟踪
        self.current_target_index = 0
        self.observation_start_time = None
        self.target_completion_status = {}
    
    def print_banner(self):
        """打印脚本信息横幅"""
        print("="*80)
        print("多目标自动观测脚本")
        if self.config.dryrun:
            print("*** DRYRUN 模式 - 仅模拟运行，不实际执行 ***")
        print("="*80)
        
        self.config.print_schedule()
    
    def wait_for_target_time(self, target: dict) -> bool:
        """等待目标观测时间
        
        Args:
            target: 目标配置
            
        Returns:
            True: 成功等到目标时间
            False: 被中断或超时
        """
        target_time = target['start_time']
        current_time = datetime.now()
        
        if current_time >= target_time:
            print(f"\n[{current_time.strftime('%H:%M:%S')}] 目标 {target['name']} 时间已到，立即开始观测")
            return True
        
        # 计算等待时间
        wait_seconds = (target_time - current_time).total_seconds()
        wait_hours = wait_seconds / 3600
        
        print(f"\n[{current_time.strftime('%H:%M:%S')}] 等待目标 {target['name']} 观测时间...")
        print(f"  计划时间: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  还需等待: {wait_hours:.1f}小时 ({wait_seconds/60:.0f}分钟)")
        
        # 等待直到目标时间
        success = self.time_manager.wait_until(target_time, f"目标 {target['name']}")
        
        if success:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 到达 {target['name']} 观测时间")
        else:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 等待被中断")
        
        return success
    
    def execute_target_observation(self, target: dict) -> bool:
        """执行单个目标的观测
        
        Args:
            target: 目标配置
            
        Returns:
            True: 观测成功完成
            False: 观测失败或被中断
        """
        target_name = target['name']
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.config.dryrun else ''}开始执行 {target_name} 观测任务")
        self.log_manager.info(f"{'[DRYRUN] ' if self.config.dryrun else ''}开始执行 {target_name} 观测任务")
        
        try:
            # 停止当前计划（确保干净启动）
            self.acp_manager.stop_script(wait_seconds=5)
            
            # 为当前目标创建成像计划
            plan = self.plan_builder.build_plan_for_target(target)
            
            # 启动成像
            success = self.acp_manager.start_imaging(plan)
            
            if success:
                self.target_completion_status[target_name] = 'running'
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {target_name} 观测计划已启动")
                self.log_manager.info(f"{target_name} 观测计划已启动")
                
                # 监控此目标的观测进度
                self.monitor_target_observation(target)
                
                self.target_completion_status[target_name] = 'completed'
                return True
            else:
                self.target_completion_status[target_name] = 'failed'
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {target_name} 观测计划启动失败")
                self.log_manager.error(f"{target_name} 观测计划启动失败")
                return False
                
        except Exception as e:
            self.target_completion_status[target_name] = 'error'
            error_msg = f"{target_name} 观测执行出错: {str(e)}"
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
            self.log_manager.error(error_msg)
            return False
    
    def monitor_target_observation(self, target: dict):
        """监控单个目标的观测状态
        
        Args:
            target: 目标配置
        """
        target_name = target['name']
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始监控 {target_name} 观测状态（每30秒刷新）")
        print("按 Ctrl+C 可跳过当前目标监控，继续下一个目标")
        print("="*60)
        
        try:
            while True:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 获取ACP状态
                try:
                    # 检查 acp_manager 是否有 app 属性
                    if hasattr(self.acp_manager, 'app') and self.acp_manager.app:
                        acp = self.acp_manager.app
                    elif hasattr(self.acp_manager, 'acp') and self.acp_manager.acp:
                        acp = self.acp_manager.acp
                    else:
                        raise AttributeError("无法访问 ACP 对象")
                    
                    is_running = acp.IsRunning
                    status_msg = f"[{current_time}] {target_name} 状态: "
                    
                    if is_running:
                        status_msg += "运行中 ✓"
                        
                        # 尝试获取更多状态信息
                        try:
                            current_target = acp.TargetName
                            current_filter = acp.Filter
                            status_msg += f" | 目标: {current_target} | 滤镜: {current_filter}"
                        except:
                            pass
                    else:
                        status_msg += "已停止 ✗"
                        print(status_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {target_name} 观测似乎已完成")
                        break
                    
                    print(status_msg)
                    self.log_manager.info(status_msg)
                    
                except Exception as e:
                    error_msg = f"[{current_time}] {target_name} 状态检测失败: {str(e)}"
                    print(error_msg)
                    self.log_manager.warning(error_msg)
                
                # 等待30秒
                time.sleep(30)
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 用户中断 {target_name} 状态监控")
            self.log_manager.info(f"用户中断 {target_name} 状态监控")
    
    def check_global_stop_time(self) -> bool:
        """检查是否到达全局停止时间
        
        Returns:
            True: 可以继续观测
            False: 到达停止时间，应该停止
        """
        if not self.config.global_stop_time:
            return True
        
        current_time = datetime.now()
        if current_time >= self.config.global_stop_time:
            print(f"\n[{current_time.strftime('%H:%M:%S')}] 到达全局停止时间，准备结束观测")
            self.log_manager.info("到达全局停止时间，准备结束观测")
            return False
        
        return True
    
    def print_observation_summary(self):
        """打印观测摘要"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 多目标观测执行摘要:")
        print("="*60)
        
        completed_count = 0
        failed_count = 0
        
        for target in self.config.targets:
            target_name = target['name']
            status = self.target_completion_status.get(target_name, 'not_started')
            
            if status == 'completed':
                status_icon = "✓"
                completed_count += 1
            elif status == 'failed' or status == 'error':
                status_icon = "✗"
                failed_count += 1
            elif status == 'running':
                status_icon = "~"
            else:
                status_icon = "○"
            
            print(f"{status_icon} {target_name}: {status}")
        
        print(f"\n总计: {completed_count}个目标完成, {failed_count}个目标失败")
        print("="*60)
    
    def run(self):
        """执行多目标观测流程"""
        if self.config.dryrun:
            self.log_manager.info("="*50)
            self.log_manager.info("启动 DRYRUN 模式 - 仅模拟运行")
            self.log_manager.info("="*50)
        
        self.print_banner()
        
        # 连接ACP
        if not self.acp_manager.connect():
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ACP连接失败，脚本终止")
            return
        
        # 初始化目标完成状态
        for target in self.config.targets:
            self.target_completion_status[target['name']] = 'not_started'
        
        # 按时间顺序执行每个目标
        for i, target in enumerate(self.config.targets):
            # 检查全局停止时间
            if not self.check_global_stop_time():
                break
            
            print(f"\n{'='*60}")
            print(f"准备执行第 {i+1}/{len(self.config.targets)} 个目标: {target['name']}")
            print('='*60)
            
            # 等待目标观测时间
            if not self.wait_for_target_time(target):
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 等待被中断，跳转到下一个目标")
                continue
            
            # 执行目标观测
            self.execute_target_observation(target)
            
            # 检查全局停止时间
            if not self.check_global_stop_time():
                break
        
        # 打印观测摘要
        self.print_observation_summary()
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.config.dryrun else ''}多目标观测脚本执行完成")
        self.log_manager.info(f"{'[DRYRUN] ' if self.config.dryrun else ''}多目标观测脚本执行完成")