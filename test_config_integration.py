#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件集成测试脚本
测试重试配置是否正确从配置文件传递到各个组件
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.lib.core.acp_client import ACPClient
from app.lib.core.acp_connection_manager import ACPConnectionManager
from app.lib.config.config_manager import MultiTargetConfigManager
from app.lib.new_multi_target_orchestrator import NewMultiTargetOrchestrator

def test_config_integration():
    """测试配置集成"""
    print("配置文件集成测试")
    print("=" * 50)
    
    # 测试配置文件加载
    print("1. 测试配置文件加载...")
    config_manager = MultiTargetConfigManager('configs/tsq21.yaml')
    config = config_manager.get_config()
    
    print("配置文件重试设置:")
    if hasattr(config, 'retry_settings'):
        print(f"  enabled: {config.retry_settings.get('enabled')}")
        print(f"  max_attempts: {config.retry_settings.get('max_attempts')}")
        print(f"  retry_interval_seconds: {config.retry_settings.get('retry_interval_seconds')}")
    
    # 测试连接管理器创建
    print("\n2. 测试连接管理器配置...")
    connection_manager = ACPConnectionManager(
        server_url=config.acp_server.url,
        username=config.acp_server.username,
        password=config.acp_server.password,
        max_retries=config.retry_settings.get('max_attempts', 5),
        retry_interval_seconds=config.retry_settings.get('retry_interval_seconds', 60)
    )
    
    print(f"连接管理器配置:")
    print(f"  max_retries: {connection_manager.max_retries}")
    print(f"  retry_interval_seconds: {connection_manager.retry_interval_seconds}")
    
    # 测试ACP客户端创建
    print("\n3. 测试ACP客户端配置...")
    connection_manager.connect()
    client = connection_manager.client
    print(f"ACP客户端配置:")
    print(f"  max_retries: {client.max_retries}")
    print(f"  retry_interval_seconds: {client.retry_interval_seconds}")
    
    # 测试协调器创建
    print("\n4. 测试协调器配置...")
    orchestrator = NewMultiTargetOrchestrator(
        config_file='configs/tsq21.yaml',
        dry_run=True
    )
    
    print(f"协调器连接管理器配置:")
    print(f"  max_retries: {orchestrator.connection_manager.max_retries}")
    print(f"  retry_interval_seconds: {orchestrator.connection_manager.retry_interval_seconds}")
    
    # 验证配置一致性
    print("\n5. 验证配置一致性...")
    expected_max_attempts = config.retry_settings.get('max_attempts', 5)
    expected_retry_interval = config.retry_settings.get('retry_interval_seconds', 60)
    
    # 检查连接管理器
    if (connection_manager.max_retries == expected_max_attempts and 
        connection_manager.retry_interval_seconds == expected_retry_interval):
        print("✓ 连接管理器配置正确")
    else:
        print("✗ 连接管理器配置错误")
        print(f"  期望: max_retries={expected_max_attempts}, retry_interval={expected_retry_interval}")
        print(f"  实际: max_retries={connection_manager.max_retries}, retry_interval={connection_manager.retry_interval_seconds}")
    
    # 检查ACP客户端
    if (client.max_retries == expected_max_attempts and 
        client.retry_interval_seconds == expected_retry_interval):
        print("✓ ACP客户端配置正确")
    else:
        print("✗ ACP客户端配置错误")
        print(f"  期望: max_retries={expected_max_attempts}, retry_interval={expected_retry_interval}")
        print(f"  实际: max_retries={client.max_retries}, retry_interval={client.retry_interval_seconds}")
    
    # 检查协调器
    if (orchestrator.connection_manager.max_retries == expected_max_attempts and 
        orchestrator.connection_manager.retry_interval_seconds == expected_retry_interval):
        print("✓ 协调器配置正确")
    else:
        print("✗ 协调器配置错误")
        print(f"  期望: max_retries={expected_max_attempts}, retry_interval={expected_retry_interval}")
        print(f"  实际: max_retries={orchestrator.connection_manager.max_retries}, retry_interval={orchestrator.connection_manager.retry_interval_seconds}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_config_integration()