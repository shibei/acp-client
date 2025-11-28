"""
日志管理模块
"""
import logging
from datetime import datetime
from pathlib import Path

class LogManager:
    """日志管理器"""
    
    LOG_DIR = Path("logs")
    
    def __init__(self, name: str = 'ACPClient'):
        self.LOG_DIR.mkdir(exist_ok=True)
        self.logger = self._setup_logger(name)
        
    def _setup_logger(self, name: str) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        if logger.handlers:
            logger.handlers.clear()
        
        # 文件处理器
        log_file = self.LOG_DIR / f"acp_client_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 统一格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str):
        self.logger.info(message)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        self.logger.error(message, exc_info=exc_info)
