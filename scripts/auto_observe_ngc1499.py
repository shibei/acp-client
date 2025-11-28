"""
自动观测脚本 - NGC 1499
在指定时间停止当前脚本，启动新的观测序列

目标：NGC 1499
坐标：RA 04:01:07.51, DEC +36:31:11.9
滤镜：支持多滤镜配置
曝光：每个滤镜可单独配置
数量：每个滤镜可单独配置
停止时间：可选，如果设置则先停止当前计划
启动时间：2025-11-20 02:30:00
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from datetime import datetime, timedelta
from ACP import ACPClient, ImagingPlan
from ACP.gui.logger import LogManager


class ObservationConfig:
    """观测配置类"""
    def __init__(self):
        # 时间配置
        self.stop_time = datetime(2025, 11, 28, 10, 45, 0)
        self.start_time = datetime(2025, 11, 28, 10, 46, 0)
        
        # ACP服务器配置
        self.acp_url = "http://27056t89i6.wicp.vip:1011"
        self.acp_user = "share"
        self.acp_password = "1681"
        
        # 运行模式
        self.dryrun = False
        
        # 目标配置
        self.target_name = "NGC 1499"
        self.target_ra = "04:01:07.51"
        self.target_dec = "+36:31:11.9"
        
        # 多滤镜配置
        self.filters = [
            {
                'filter_id': 4,
                'name': 'H-alpha',
                'exposure': 600,
                'count': 30,
                'binning': 1
            },
            {
                'filter_id': 6,
                'name': 'OIII',
                'exposure': 600,
                'count': 30,
                'binning': 1
            },
            {
                'filter_id': 5,
                'name': 'SII',
                'exposure': 600,
                'count': 30,
                'binning': 1
            },
        ]
        
        # 其他参数
        self.dither = 5
        self.auto_focus = True
        self.af_interval = 120
    
    def get_total_hours(self):
        """计算预计总时间（小时）"""
        total_seconds = sum(f['exposure'] * f['count'] for f in self.filters)
        return total_seconds / 3600
    
    def get_total_images(self):
        """计算总图像数量"""
        return sum(f['count'] for f in self.filters)


class TimeManager:
    """时间管理类"""
    def __init__(self, dryrun=False):
        self.dryrun = dryrun
    
    def wait_until(self, target_time, action_name="执行"):
        """等待到指定时间"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.dryrun else ''}等待到{action_name}时间...")
        
        if self.dryrun:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 跳过等待，目标时间: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        while True:
            now = datetime.now()
            time_diff = (target_time - now).total_seconds()
            
            if time_diff <= 0:
                break
            
            if int(time_diff) % 30 == 0:
                hours = int(time_diff // 3600)
                minutes = int((time_diff % 3600) // 60)
                seconds = int(time_diff % 60)
                print(f"[{now.strftime('%H:%M:%S')}] 距离{action_name}还有: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            time.sleep(1)
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⏰ 到达{action_name}时间")


class ACPManager:
    """ACP客户端管理类"""
    def __init__(self, config, log_manager):
        self.config = config
        self.log_manager = log_manager
        self.client = None
    
    def connect(self):
        """连接到ACP服务器"""
        if self.config.dryrun:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟连接到ACP服务器...")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] ✓ 模拟连接成功")
            self.log_manager.info(f"[DRYRUN] 模拟连接到ACP服务器: {self.config.acp_url}")
            self.client = "DRYRUN_CLIENT"
            return True
        
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在连接到ACP服务器...")
            self.client = ACPClient(self.config.acp_url, self.config.acp_user, self.config.acp_password)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 成功连接到ACP服务器")
            self.log_manager.info(f"成功连接到ACP服务器: {self.config.acp_url}")
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 连接失败: {e}")
            self.log_manager.error(f"连接ACP服务器失败: {e}", exc_info=True)
            return False
    
    def stop_script(self, wait_seconds=5):
        """停止当前运行的脚本"""
        if self.config.dryrun:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟停止当前脚本...")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] ✓ 模拟停止成功")
            self.log_manager.info("[DRYRUN] 模拟停止当前脚本")
            return True
        
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在停止当前脚本...")
            success = self.client.stop_script()
            time.sleep(wait_seconds)
            
            if success:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 当前脚本已停止")
                self.log_manager.info("成功停止当前脚本")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ 停止脚本可能失败，继续执行...")
                self.log_manager.warning("停止脚本响应异常")
            
            return success
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 停止脚本时出错: {e}")
            self.log_manager.error(f"停止脚本失败: {e}", exc_info=True)
            return False
    
    def start_imaging(self, plan):
        """启动成像计划"""
        if self.config.dryrun:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟启动成像计划...")
            estimated_finish = datetime.now() + timedelta(hours=self.config.get_total_hours())
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] ✓ 模拟启动成功！")
            self._print_success_info(estimated_finish, is_dryrun=True)
            return True
        
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在启动成像计划...")
            success = self.client.start_imaging_plan(plan)
            
            if success:
                estimated_finish = datetime.now() + timedelta(hours=self.config.get_total_hours())
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 成像计划启动成功！")
                self._print_success_info(estimated_finish)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 成像计划启动失败！")
                self.log_manager.error("成像计划启动失败")
            
            return success
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 启动成像计划时出错: {e}")
            self.log_manager.error(f"启动成像计划失败: {e}", exc_info=True)
            return False
    
    def _print_success_info(self, estimated_finish, is_dryrun=False):
        """打印成功信息"""
        prefix = "[DRYRUN] 模拟" if is_dryrun else ""
        print(f"\n{'='*70}")
        print(f"{prefix}任务已启动！")
        print(f"目标: {self.config.target_name}")
        print(f"总图像数: {self.config.get_total_images()}张")
        print(f"预计完成时间: {estimated_finish.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        filter_summary = ", ".join([f"{f.get('name', 'Filter' + str(f['filter_id']))}:{f['count']}x{f['exposure']}s" 
                                   for f in self.config.filters])
        self.log_manager.info(f"{prefix}启动{self.config.target_name}成像计划: {filter_summary}")


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
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {'[DRYRUN] ' if self.config.dryrun else ''}脚本执行完成")
        self.log_manager.info(f"{'[DRYRUN] ' if self.config.dryrun else ''}自动观测脚本执行完成")


def main():
    """主函数"""
    config = ObservationConfig()
    orchestrator = ObservationOrchestrator(config)
    orchestrator.run()


if __name__ == "__main__":
    main()
