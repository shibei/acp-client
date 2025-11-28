"""
ACP客户端连接管理器
负责与ACP服务器的连接和基础通信
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import time
from datetime import datetime
from typing import Optional, Dict, Any
from ACP import ACPClient


class ACPConnectionManager:
    """ACP连接管理器 - 负责与ACP服务器的连接和基础通信"""
    
    def __init__(self, server_url: str, username: str, password: str, dryrun: bool = False):
        """初始化连接管理器
        
        Args:
            server_url: ACP服务器URL
            username: 用户名
            password: 密码
            dryrun: 是否模拟模式
        """
        self.server_url = server_url
        self.username = username
        self.password = password
        self.dryrun = dryrun
        self.client: Optional[ACPClient] = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """连接到ACP服务器
        
        Returns:
            True: 连接成功
            False: 连接失败
        """
        if self.dryrun:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟连接到ACP服务器...")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] ✓ 模拟连接成功")
            self.client = "DRYRUN_CLIENT"
            self.is_connected = True
            return True
        
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在连接到ACP服务器...")
            self.client = ACPClient(self.server_url, self.username, self.password)
            self.is_connected = True
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 成功连接到ACP服务器")
            return True
        except Exception as e:
            self.is_connected = False
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开与ACP服务器的连接
        
        Returns:
            True: 断开成功
            False: 断开失败
        """
        if self.dryrun:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟断开ACP服务器连接")
            self.client = None
            self.is_connected = False
            return True
        
        try:
            if self.client:
                # ACPClient没有显式的disconnect方法
                self.client = None
            self.is_connected = False
            return True
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 断开连接时出错: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取ACP服务器状态
        
        Returns:
            状态字典
        """
        if self.dryrun:
            return {
                'connected': True,
                'is_running': False,
                'target_name': 'DRYRUN_TARGET',
                'filter': 'LUM',
                'status': 'idle'
            }
        
        if not self.client or not self.is_connected:
            return {'connected': False, 'error': '未连接'}
        
        try:
            return {
                'connected': True,
                'is_running': self.client.IsRunning,
                'target_name': self.client.TargetName if hasattr(self.client, 'TargetName') else 'Unknown',
                'filter': self.client.Filter if hasattr(self.client, 'Filter') else 'Unknown',
                'status': 'running' if self.client.IsRunning else 'idle'
            }
        except Exception as e:
            return {'connected': True, 'error': str(e)}
    
    def stop_current_operation(self, wait_seconds: int = 5) -> bool:
        """停止当前操作
        
        Args:
            wait_seconds: 等待时间（秒）
            
        Returns:
            True: 停止成功
            False: 停止失败
        """
        if self.dryrun:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] 模拟停止当前操作...")
            time.sleep(1)  # 模拟等待
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [DRYRUN] ✓ 模拟停止成功")
            return True
        
        if not self.client or not self.is_connected:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 未连接，无法停止操作")
            return False
        
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在停止当前操作...")
            success = self.client.stop_script()
            time.sleep(wait_seconds)
            
            if success:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 当前操作已停止")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ 停止操作响应异常")
            
            return success
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 停止操作时出错: {e}")
            return False