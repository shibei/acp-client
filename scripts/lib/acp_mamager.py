import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from datetime import datetime, timedelta
from ACP import ACPClient


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
