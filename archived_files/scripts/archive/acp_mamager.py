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
        # 检查是否为dryrun模式（支持对象和字典两种方式）
        if hasattr(self.config, 'dryrun'):
            dryrun = self.config.dryrun
        elif isinstance(self.config, dict) and 'dryrun' in self.config:
            dryrun = self.config['dryrun']
        else:
            dryrun = False
            
        # 获取连接信息（支持对象和字典两种方式）
        if hasattr(self.config, 'acp_url'):
            acp_url = self.config.acp_url
            acp_user = getattr(self.config, 'acp_user', '')
            acp_password = getattr(self.config, 'acp_password', '')
        elif isinstance(self.config, dict):
            acp_url = self.config.get('acp_url', '')
            acp_user = self.config.get('acp_user', '')
            acp_password = self.config.get('acp_password', '')
        else:
            acp_url = ''
            acp_user = ''
            acp_password = ''
        
        if dryrun:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟连接到ACP服务器...")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] [OK] 模拟连接成功")
            self.log_manager.info(f"[DRYRUN] 模拟连接到ACP服务器: {acp_url}")
            self.client = "DRYRUN_CLIENT"
            return True
        
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在连接到ACP服务器...")
            self.client = ACPClient(acp_url, acp_user, acp_password)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 成功连接到ACP服务器")
            self.log_manager.info(f"成功连接到ACP服务器: {acp_url}")
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] 连接失败: {e}")
            self.log_manager.error(f"连接ACP服务器失败: {e}", exc_info=True)
            return False
    
    def stop_script(self, wait_seconds=5):
        """停止当前运行的脚本"""
        # 检查是否为dryrun模式（支持对象和字典两种方式）
        if hasattr(self.config, 'dryrun'):
            dryrun = self.config.dryrun
        elif isinstance(self.config, dict) and 'dryrun' in self.config:
            dryrun = self.config['dryrun']
        else:
            dryrun = False
            
        if dryrun:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟停止当前脚本...")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] [OK] 模拟停止成功")
            self.log_manager.info("[DRYRUN] 模拟停止当前脚本")
            return True
        
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在停止当前脚本...")
            success = self.client.stop_script()
            time.sleep(wait_seconds)
            
            if success:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 当前脚本已停止")
                self.log_manager.info("成功停止当前脚本")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [WARNING] 停止脚本可能失败，继续执行...")
                self.log_manager.warning("停止脚本响应异常")
            
            return success
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] 停止脚本时出错: {e}")
            self.log_manager.error(f"停止脚本失败: {e}", exc_info=True)
            return False
    
    def start_imaging(self, plan):
        """启动成像计划"""
        # 检查是否为dryrun模式（支持对象和字典两种方式）
        if hasattr(self.config, 'dryrun'):
            dryrun = self.config.dryrun
        elif isinstance(self.config, dict) and 'dryrun' in self.config:
            dryrun = self.config['dryrun']
        else:
            dryrun = False
        
        if dryrun:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟启动成像计划...")
            
            # 获取总小时数（支持对象和字典两种方式）
            if hasattr(self.config, 'get_total_hours'):
                total_hours = self.config.get_total_hours()
            elif isinstance(self.config, dict) and 'filters' in self.config:
                # 从滤镜配置计算总小时数
                filters = self.config.get('filters', [])
                total_seconds = sum(f.get('count', 0) * f.get('exposure', 0) for f in filters)
                total_hours = total_seconds / 3600
            else:
                total_hours = 1  # 默认值
                
            estimated_finish = datetime.now() + timedelta(hours=total_hours)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] [OK] 模拟启动成功！")
            self._print_success_info(estimated_finish, is_dryrun=True)
            return True
        
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在启动成像计划...")
            success = self.client.start_imaging_plan(plan)
            
            if success:
                # 获取总小时数（支持对象和字典两种方式）
                if hasattr(self.config, 'get_total_hours'):
                    total_hours = self.config.get_total_hours()
                elif isinstance(self.config, dict) and 'filters' in self.config:
                    # 从滤镜配置计算总小时数
                    filters = self.config.get('filters', [])
                    total_seconds = sum(f.get('count', 0) * f.get('exposure', 0) for f in filters)
                    total_hours = total_seconds / 3600
                else:
                    total_hours = 1  # 默认值
                    
                estimated_finish = datetime.now() + timedelta(hours=total_hours)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] 成像计划启动成功！")
                self._print_success_info(estimated_finish)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] 成像计划启动失败！")
                self.log_manager.error("成像计划启动失败")
            
            return success
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] 启动成像计划时出错: {e}")
            self.log_manager.error(f"启动成像计划失败: {e}", exc_info=True)
            return False
    
    def _print_success_info(self, estimated_finish, is_dryrun=False):
        """打印成功信息"""
        prefix = "[DRYRUN] 模拟" if is_dryrun else ""
        
        # 获取目标名称（支持对象和字典两种方式）
        if hasattr(self.config, 'target_name'):
            target_name = self.config.target_name
        elif isinstance(self.config, dict) and 'target_name' in self.config:
            target_name = self.config['target_name']
        else:
            target_name = "未知目标"
        
        # 获取总图像数（支持对象和字典两种方式）
        if hasattr(self.config, 'get_total_images'):
            total_images = self.config.get_total_images()
        elif isinstance(self.config, dict) and 'filters' in self.config:
            total_images = sum(f.get('count', 0) for f in self.config.get('filters', []))
        else:
            total_images = 0
        
        print(f"\n{'='*70}")
        print(f"{prefix}任务已启动！")
        print(f"目标: {target_name}")
        print(f"总图像数: {total_images}张")
        print(f"预计完成时间: {estimated_finish.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        
        # 获取滤镜信息（支持对象和字典两种方式）
        if hasattr(self.config, 'filters'):
            filters = self.config.filters
        elif isinstance(self.config, dict) and 'filters' in self.config:
            filters = self.config['filters']
        else:
            filters = []
        
        if filters:
            filter_summary = ", ".join([f"{f.get('name', 'Filter' + str(f.get('filter_id', i))}:{f.get('count', 0)}x{f.get('exposure', 0)}s" 
                                       for i, f in enumerate(filters)])
            self.log_manager.info(f"{prefix}启动{target_name}成像计划: {filter_summary}")
        else:
            self.log_manager.info(f"{prefix}启动{target_name}成像计划")
