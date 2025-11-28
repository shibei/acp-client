import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from datetime import datetime
from ACP.gui.logger import LogManager
from lib.plan_builder import ImagingPlanBuilder
from lib.time_manager import TimeManager
from lib.acp_mamager import ACPManager


class ObservationOrchestrator:
    """观测编排类 - 协调整个观测流程"""
    def __init__(self, config):
        self.config = config
        self.log_manager = LogManager('AutoObserve_NGC1499')
        self.time_manager = TimeManager(config.dryrun)
        self.acp_manager = ACPManager(config, self.log_manager)
        self.plan_builder = ImagingPlanBuilder(config)
    
    def print_banner(self):
        """打印脚本信息横幅"""
        print("="*70)
        print("NGC 1499 自动观测脚本")
        if self.config.dryrun:
            print("*** DRYRUN 模式 - 仅模拟运行，不实际执行 ***")
        print("="*70)
        print(f"目标名称: {self.config.target_name}")
        print(f"坐标: RA {self.config.target_ra}, DEC {self.config.target_dec}")
        print(f"\n滤镜配置 ({len(self.config.filters)}个滤镜):")
        for i, filter_cfg in enumerate(self.config.filters, 1):
            filter_name = filter_cfg.get('name', f"Filter {filter_cfg['filter_id']}")
            print(f"  {i}. {filter_name} (ID: {filter_cfg['filter_id']})")
            print(f"     曝光: {filter_cfg['exposure']}秒 x {filter_cfg['count']}张")
            print(f"     Binning: {filter_cfg['binning']}x{filter_cfg['binning']}")
        print(f"\n总图像数: {self.config.get_total_images()}张")
        print(f"预计总时间: {self.config.get_total_hours():.1f}小时")
        if self.config.stop_time:
            print(f"计划停止时间: {self.config.stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"计划启动时间: {self.config.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
    
    def monitor_status(self):
        """监控观测状态（每30秒刷新）"""
        self.log_manager.info("开始状态监控（每30秒刷新）")
        print(f"\n{'='*70}")
        print("开始状态监控 - 按 Ctrl+C 退出监控")
        print(f"{'='*70}\n")
        
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
                    status_msg = f"[{current_time}] ACP状态: "
                    
                    if is_running:
                        status_msg += "运行中 ✓"
                        
                        # 尝试获取更多状态信息
                        try:
                            target_name = acp.TargetName
                            filter_name = acp.Filter
                            status_msg += f" | 目标: {target_name} | 滤镜: {filter_name}"
                        except:
                            pass
                    else:
                        status_msg += "已停止 ✗"
                    
                    print(status_msg)
                    self.log_manager.info(status_msg)
                    
                except Exception as e:
                    error_msg = f"[{current_time}] 状态检测失败: {str(e)}"
                    print(error_msg)
                    self.log_manager.warning(error_msg)
                
                # 等待30秒
                time.sleep(30)
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 用户中断状态监控")
            self.log_manager.info("状态监控被用户中断")
    
    def run(self):
        """执行观测流程"""
        if self.config.dryrun:
            self.log_manager.info("="*50)
            self.log_manager.info("启动 DRYRUN 模式 - 仅模拟运行")
            self.log_manager.info("="*50)
        
        self.print_banner()
        
        # 连接ACP
        if not self.acp_manager.connect():
            return
        
        # 停止当前计划（如果需要）
        if self.config.stop_time:
            self.time_manager.wait_until(self.config.stop_time, "停止")
            self.log_manager.info(f"{'[DRYRUN] ' if self.config.dryrun else ''}到达停止时间，准备停止当前计划")
            self.acp_manager.stop_script()
        
        # 等待启动时间
        self.time_manager.wait_until(self.config.start_time, "启动")
        self.log_manager.info(f"{'[DRYRUN] ' if self.config.dryrun else ''}到达启动时间，开始执行{self.config.target_name}观测任务")
        
        # 启动前再次停止（确保干净启动）
        self.acp_manager.stop_script(wait_seconds=5)
        
        # 创建并启动计划
        plan = self.plan_builder.build()
        self.acp_manager.start_imaging(plan)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.config.dryrun else ''}观测计划已启动")
        self.log_manager.info(f"{'[DRYRUN] ' if self.config.dryrun else ''}观测计划已启动")
        
        # 开始状态监控
        if not self.config.dryrun:
            self.monitor_status()
        else:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 跳过状态监控")
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.config.dryrun else ''}脚本执行完成")
        self.log_manager.info(f"{'[DRYRUN] ' if self.config.dryrun else ''}自动观测脚本执行完成")