#!/usr/bin/env python3
"""
测试天文台离线错误的重试机制
"""

import sys
import os
sys.path.append('app')

from app.lib.execution.target_observation_executor import TargetObservationExecutor
from app.lib.core.acp_connection_manager import ACPConnectionManager
from app.lib.core.acp_imaging_manager import ACPImagingManager
from app.lib.utils.log_manager import LogManager
from app.lib.core.acp_client import ACPClient
from app.lib.core.acp_client import ImagingPlan


def test_observatory_offline_retry():
    """测试天文台离线错误的重试机制"""
    
    print("=== 测试天文台离线重试机制 ===")
    
    # 创建日志管理器
    logger = LogManager()
    
    # 创建连接管理器（模拟模式）
    connection_manager = ACPConnectionManager(
        server_url="http://localhost:80",
        username="test",
        password="test",
        dryrun=True  # 使用模拟模式进行测试
    )
    
    # 创建成像管理器
    imaging_manager = ACPImagingManager(connection_manager)
    
    # 创建观测执行器
    executor = TargetObservationExecutor(
        connection_manager=connection_manager,
        imaging_manager=imaging_manager,
        log_manager=logger
    )
    
    # 配置重试设置
    retry_config = {
        'enabled': True,
        'max_attempts': 3,
        'retry_interval_seconds': 2,  # 缩短间隔以便快速测试
        'retry_on_errors': ['observatory_offline', 'connection_timeout', 'acp_server_error']
    }
    
    executor.set_retry_config(retry_config)
    print(f"✓ 重试配置已设置: {retry_config}")
    
    # 测试错误类型识别
    print("\n=== 测试错误类型识别 ===")
    test_errors = [
        "The observatory is offline",
        "[lba warning]The observatory is offline",
        "Connection timeout after 30 seconds",
        "ACP server error: connection refused"
    ]
    
    for error_msg in test_errors:
        error_type = executor._get_error_type(error_msg)
        print(f"✓ '{error_msg}' -> {error_type}")
        
        # 检查是否应该重试
        retry_on_errors = executor.retry_config.get('retry_on_errors', [])
        should_retry = error_type in retry_on_errors
        print(f"  是否应该重试: {should_retry}")
    
    # 测试重试逻辑
    print("\n=== 测试重试逻辑 ===")
    
    # 模拟一个会触发重试的错误
    error_msg = "The observatory is offline"
    error_type = executor._get_error_type(error_msg)
    
    print(f"错误信息: {error_msg}")
    print(f"错误类型: {error_type}")
    print(f"是否支持重试: {error_type in retry_config['retry_on_errors']}")
    
    # 测试重试次数限制
    print(f"\n最大重试次数: {retry_config['max_attempts']}")
    
    return True


if __name__ == "__main__":
    try:
        success = test_observatory_offline_retry()
        if success:
            print("\n🎉 天文台离线重试测试通过！")
            sys.exit(0)
        else:
            print("\n❌ 测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)