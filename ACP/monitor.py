"""
状态监控模块
"""
import threading
import time
from typing import Optional
from .ACPlib import ACPClient
from .gui.logger import LogManager


class StatusMonitor:
    """状态监控器"""
    
    MONITOR_INTERVAL = 5  # 秒
    
    def __init__(self, client: ACPClient, status_callback, log_manager: LogManager):
        self.client = client
        self.status_callback = status_callback
        self.log_manager = log_manager
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
    def start(self):
        """开始监控"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.shutdown_event.clear()
        self.log_manager.info("开始监控模式")
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop(self):
        """停止监控"""
        if not self.monitoring:
            return
            
        self.monitoring = False
        self.shutdown_event.set()
        self.log_manager.info("停止监控模式")
        
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring and not self.shutdown_event.is_set():
            try:
                self.status_callback()
                self.shutdown_event.wait(self.MONITOR_INTERVAL)
            except Exception as e:
                self.log_manager.error(f"监控循环出错: {str(e)}", exc_info=True)
                
    def is_monitoring(self) -> bool:
        """是否正在监控"""
        return self.monitoring
