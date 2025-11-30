#!/usr/bin/env python3
"""
重试机制测试脚本
用于验证401认证错误的重试行为
"""

import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from lib.core.acp_connection_manager import ACPConnectionManager
from lib.core.acp_client import ACPClient
from lib.new_multi_target_orchestrator import NewMultiTargetOrchestrator


def test_acp_client_retry():
    """测试ACP客户端的重试机制"""
    print("=== 测试ACP客户端重试机制 ===")
    
    # 创建ACP客户端，使用错误的密码触发401错误
    client = ACPClient(
        base_url='http://27056t89i6.wicp.vip:2121/',
        user='share',
        password='wrong_password',  # 错误密码
        max_retries=3  # 设置较少的重试次数用于测试
    )
    
    print(f"客户端配置: max_retries={client.max_retries}, retry_delay={client.retry_delay}")
    
    start_time = datetime.now()
    print(f"开始时间: {start_time.strftime('%H:%M:%S')}")
    
    # 尝试执行会触发401错误的操作
    try:
        success = client.stop_script()
        print(f"停止脚本结果: {success}")
    except Exception as e:
        print(f"捕获异常: {e}")
    
    end_time = datetime.now()
    print(f"结束时间: {end_time.strftime('%H:%M:%S')}")
    print(f"总耗时: {(end_time - start_time).total_seconds():.1f} 秒")
    print()


def test_connection_manager_retry():
    """测试连接管理器的重试机制"""
    print("=== 测试连接管理器重试机制 ===")
    
    # 创建连接管理器，使用错误的密码
    manager = ACPConnectionManager(
        server_url='http://27056t89i6.wicp.vip:2121/',
        username='share',
        password='wrong_password',  # 错误密码
        max_retries=3  # 设置较少的重试次数用于测试
    )
    
    print(f"连接管理器配置: max_retries={manager.max_retries}")
    
    start_time = datetime.now()
    print(f"开始时间: {start_time.strftime('%H:%M:%S')}")
    
    # 尝试连接（会触发401错误）
    success = manager.connect()
    print(f"连接结果: {success}")
    
    if manager.client and manager.client != "DRYRUN_CLIENT":
        # 尝试执行操作
        try:
            result = manager.stop_current_operation()
            print(f"停止操作结果: {result}")
        except Exception as e:
            print(f"执行操作时捕获异常: {e}")
    
    end_time = datetime.now()
    print(f"结束时间: {end_time.strftime('%H:%M:%S')}")
    print(f"总耗时: {(end_time - start_time).total_seconds():.1f} 秒")
    print()


def test_configured_retry():
    """测试配置文件中的重试设置"""
    print("=== 测试配置文件重试设置 ===")
    
    # 使用配置文件创建协调器
    config_file = 'configs/tsq21.yaml'
    
    try:
        orchestrator = NewMultiTargetOrchestrator(
            config_file=config_file,
            dry_run=False  # 实际运行模式
        )
        
        # 获取配置
        config = orchestrator.config_manager.get_config()
        
        if hasattr(config, 'retry_settings'):
            retry_settings = config.retry_settings
            print(f"配置文件重试设置:")
            print(f"  enabled: {retry_settings.get('enabled', 'N/A')}")
            print(f"  max_attempts: {retry_settings.get('max_attempts', 'N/A')}")
            print(f"  retry_interval_seconds: {retry_settings.get('retry_interval_seconds', 'N/A')}")
            print(f"  retry_on_errors: {retry_settings.get('retry_on_errors', [])}")
        else:
            print("配置文件中没有retry_settings")
            
        # 检查连接管理器的配置
        print(f"连接管理器max_retries: {orchestrator.connection_manager.max_retries}")
        
        # 检查执行器的配置
        executor_config = orchestrator.executor.retry_config
        print(f"执行器默认重试配置:")
        print(f"  max_attempts: {executor_config.get('max_attempts')}")
        print(f"  retry_interval_seconds: {executor_config.get('retry_interval_seconds')}")
        
    except Exception as e:
        print(f"测试配置文件时出错: {e}")
    
    print()


def main():
    """主函数"""
    print("重试机制测试脚本")
    print("=" * 50)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行测试
    test_configured_retry()
    
    # 注意：以下测试需要实际的服务器连接，可能产生大量重试
    print("注意：实际连接测试已跳过，避免产生过多重试")
    print("如需测试实际重试行为，请手动取消注释相关测试")
    
    # test_acp_client_retry()
    # test_connection_manager_retry()
    
    print("=" * 50)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()