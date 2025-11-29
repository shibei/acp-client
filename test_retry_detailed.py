#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细重试测试脚本"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from lib.execution.target_observation_executor import TargetObservationExecutor
from lib.core.acp_client import ImagingPlan
from lib.config.config_manager import MultiTargetConfigManager

# 模拟目标配置
class MockTarget:
    def __init__(self, name):
        self.name = name
        self.ra = "05:16:32.2"
        self.dec = "+34:16:16"
        self.start_time = None
        self.priority = 1
        self.filters = [
            {"filter_id": "Ha", "exposure": 300, "count": 1},
            {"filter_id": "OIII", "exposure": 300, "count": 1}
        ]
        self.meridian_time = "02:11:00"

def test_retry_mechanism():
    """测试重试机制"""
    print("=== 详细重试测试 ===")
    
    # 创建配置管理器
    config_manager = MultiTargetConfigManager("app/multi_target_config.yaml")
    config = config_manager.get_config()
    
    # 打印重试配置
    if hasattr(config, 'retry_settings'):
        print(f"重试配置: {config.retry_settings}")
    else:
        print("没有找到重试配置")
    
    # 创建模拟管理器
    class MockLogManager:
        def info(self, msg): print(f"LOG INFO: {msg}")
        def warning(self, msg): print(f"LOG WARNING: {msg}")
        def error(self, msg): print(f"LOG ERROR: {msg}")
    
    # 创建执行器
    executor = TargetObservationExecutor(
        connection_manager=None,
        imaging_manager=None,
        log_manager=MockLogManager(),
        dryrun=True
    )
    
    # 设置重试配置
    if hasattr(config, 'retry_settings') and config.retry_settings:
        executor.set_retry_config(config.retry_settings)
        print(f"已设置重试配置到执行器")
    else:
        # 使用默认配置
        retry_config = {
            'enabled': True,
            'max_attempts': 3,
            'retry_interval_seconds': 2,
            'retry_on_errors': ['connection_timeout', 'acp_server_error', 'meridian_flip_failed', 'observation_timeout', 'observatory_offline']
        }
        executor.set_retry_config(retry_config)
        print(f"使用默认重试配置: {retry_config}")
    
    # 测试错误类型识别
    test_errors = [
        "[lba warning]The observatory is offline",
        "Connection timeout",
        "ACP server error",
        "Unknown error"
    ]
    
    print("\n=== 错误类型识别测试 ===")
    for error_msg in test_errors:
        error_type = executor._get_error_type(error_msg)
        retry_config = executor.retry_config
        retry_on_errors = retry_config.get('retry_on_errors', [])
        should_retry = error_type in retry_on_errors
        
        print(f"错误信息: {error_msg}")
        print(f"错误类型: {error_type}")
        print(f"重试列表: {retry_on_errors}")
        print(f"是否支持重试: {should_retry}")
        print("---")
    
    # 检查执行器的重试配置
    print(f"\n执行器当前重试配置: {executor.retry_config}")

if __name__ == "__main__":
    test_retry_mechanism()