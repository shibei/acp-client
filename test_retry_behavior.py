#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重试行为详细测试脚本"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from lib.execution.target_observation_executor import TargetObservationExecutor
from lib.config.config_manager import MultiTargetConfigManager

# 模拟目标配置
class MockTarget:
    def __init__(self, name):
        self.name = name
        self.ra = "05:16:32.2"
        self.dec = "+34:16:16"
        self.start_time = datetime.now()
        self.priority = 1
        self.filters = [
            {"filter_id": "Ha", "exposure": 300, "count": 1},
            {"filter_id": "OIII", "exposure": 300, "count": 1}
        ]
        self.meridian_time = "02:11:00"

# 模拟管理器
class MockConnectionManager:
    def connect(self): return True
    def disconnect(self): pass
    def get_status(self): return True

class MockImagingManager:
    def __init__(self):
        self.attempt_count = 0
    
    def create_imaging_plan(self, target, global_config):
        return {"target": target.name, "filters": target.filters}
    
    def start_imaging_plan(self, plan):
        """模拟成像计划启动，前两次失败，第三次成功"""
        self.attempt_count += 1
        print(f"[MockImagingManager] 第{self.attempt_count}次尝试启动成像计划")
        
        if self.attempt_count <= 2:
            return False, "[lba warning]The observatory is offline"
        else:
            return True, "成像计划启动成功"
    
    def monitor_imaging(self, timeout=3600):
        return {"success": True, "completed_exposures": 2}
    
    def get_current_plan_status(self):
        return {"status": "running", "completed_exposures": 2, "total_exposures": 2}

class MockLogManager:
    def info(self, msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] LOG INFO: {msg}")
    def warning(self, msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] LOG WARNING: {msg}")
    def error(self, msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] LOG ERROR: {msg}")

def test_retry_behavior():
    """测试重试行为"""
    print("=== 重试行为详细测试 ===")
    print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}")
    
    # 创建配置管理器
    config_manager = MultiTargetConfigManager("app/multi_target_config.yaml")
    config = config_manager.get_config()
    
    # 创建模拟管理器
    connection_manager = MockConnectionManager()
    imaging_manager = MockImagingManager()
    log_manager = MockLogManager()
    
    # 创建执行器
    executor = TargetObservationExecutor(
        connection_manager=connection_manager,
        imaging_manager=imaging_manager,
        log_manager=log_manager,
        dryrun=False
    )
    
    # 设置重试配置
    if hasattr(config, 'retry_settings') and config.retry_settings:
        retry_config = config.retry_settings.copy()
        retry_config['retry_interval_seconds'] = 2  # 缩短间隔便于测试
        executor.set_retry_config(retry_config)
        print(f"已设置重试配置: {retry_config}")
    
    # 创建目标
    target = MockTarget("ic 405")
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始执行目标观测...")
    
    # 执行观测
    start_time = datetime.now()
    success = executor.execute_target(target, {})
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 观测执行完成")
    print(f"执行结果: {'成功' if success else '失败'}")
    print(f"总耗时: {duration:.1f}秒")
    print(f"尝试次数: {imaging_manager.attempt_count}")
    
    # 验证结果
    if success and imaging_manager.attempt_count == 3:
        print("✅ 重试机制工作正常！第三次尝试成功")
    elif not success and imaging_manager.attempt_count > 1:
        print(f"⚠️ 重试机制触发，但最终失败。尝试次数: {imaging_manager.attempt_count}")
    else:
        print(f"❌ 重试机制未正常工作。尝试次数: {imaging_manager.attempt_count}")

if __name__ == "__main__":
    test_retry_behavior()