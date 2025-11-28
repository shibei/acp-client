"""
日志管理器模块
提供统一的日志记录功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path


class LogManager:
    """日志管理器类"""
    
    def __init__(self, name: str = "ACPClient", log_dir: Optional[str] = None, 
                 log_level: str = "INFO", max_bytes: int = 10*1024*1024, 
                 backup_count: int = 5, enable_console: bool = True):
        """初始化日志管理器
        
        Args:
            name: 日志记录器名称
            log_dir: 日志文件目录（默认为当前目录下的logs）
            log_level: 日志级别
            max_bytes: 日志文件最大大小（字节）
            backup_count: 备份文件数量
            enable_console: 是否启用控制台输出
        """
        self.name = name
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), '..', '..', '..', 'logs')
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.enable_console = enable_console
        
        # 创建日志目录
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # 配置日志记录器
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # 如果日志记录器已经有处理器，先清除它们
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器（轮转日志）
        log_file = os.path.join(self.log_dir, f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=self.max_bytes, backupCount=self.backup_count
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            # 设置控制台编码为UTF-8，避免Unicode字符编码错误
            if hasattr(console_handler.stream, 'reconfigure'):
                try:
                    console_handler.stream.reconfigure(encoding='utf-8')
                except:
                    pass  # 如果reconfigure失败，使用默认编码
            logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """记录异常日志"""
        self.logger.exception(message, **kwargs)
    
    def log_target_observation(self, target_name: str, ra: str, dec: str, 
                              observation_time: datetime, status: str, 
                              details: Optional[Dict[str, Any]] = None):
        """记录目标观测日志
        
        Args:
            target_name: 目标名称
            ra: RA坐标
            dec: DEC坐标
            observation_time: 观测时间
            status: 观测状态
            details: 详细信息
        """
        details_str = ""
        if details:
            details_str = f" - 详情: {details}"
        
        message = f"目标观测: {target_name} (RA: {ra}, DEC: {dec}) - " \
                 f"时间: {observation_time.strftime('%Y-%m-%d %H:%M:%S')} - " \
                 f"状态: {status}{details_str}"
        
        self.info(message)
    
    def log_meridian_flip(self, target_name: str, flip_time: datetime, 
                         before_side: str, after_side: str, success: bool):
        """记录中天反转日志
        
        Args:
            target_name: 目标名称
            flip_time: 反转时间
            before_side: 反转前天体侧
            after_side: 反转后天体侧
            success: 是否成功
        """
        status = "成功" if success else "失败"
        message = f"中天反转: {target_name} - 时间: {flip_time.strftime('%Y-%m-%d %H:%M:%S')} - " \
                 f"从 {before_side} 到 {after_side} - {status}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_schedule_summary(self, total_targets: int, observable_targets: int, 
                           start_time: datetime, end_time: datetime):
        """记录调度摘要日志
        
        Args:
            total_targets: 总目标数
            observable_targets: 可观测目标数
            start_time: 开始时间
            end_time: 结束时间
        """
        duration = (end_time - start_time).total_seconds() / 3600  # 小时
        
        message = f"观测调度摘要: 总目标 {total_targets} 个，可观测 {observable_targets} 个 - " \
                 f"时间范围: {start_time.strftime('%Y-%m-%d %H:%M')} 到 " \
                 f"{end_time.strftime('%Y-%m-%d %H:%M')} (持续 {duration:.1f} 小时)"
        
        self.info(message)
    
    def get_log_files(self) -> List[str]:
        """获取日志文件列表
        
        Returns:
            日志文件路径列表
        """
        log_files = []
        log_dir_path = Path(self.log_dir)
        
        if log_dir_path.exists():
            for log_file in log_dir_path.glob(f"{self.name}_*.log"):
                log_files.append(str(log_file))
        
        return sorted(log_files)
    
    def get_recent_logs(self, lines: int = 50) -> List[str]:
        """获取最近的日志内容
        
        Args:
            lines: 要获取的行数
            
        Returns:
            日志行列表
        """
        log_files = self.get_log_files()
        if not log_files:
            return []
        
        # 获取最新的日志文件
        latest_log = log_files[-1]
        
        try:
            with open(latest_log, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
        except Exception as e:
            self.error(f"读取日志文件失败: {e}")
            return []