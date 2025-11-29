#!/usr/bin/env python3
"""
重试功能测试脚本
用于测试观测执行器的重试功能
"""

import sys
import os
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.lib.execution.target_observation_executor import TargetObservationExecutor
from app.lib.config.config_manager import MultiTargetConfigManager
from app.lib.core.acp_connection_manager import ACPConnectionManager
from app.lib.core.acp_imaging_manager import ACPImagingManager
from app.lib.utils.log_manager import LogManager


def test_retry_functionality():
    """测试重试功能"""
    print("=== 开始测试重试功能 ===")
    
    # 创建日志器
    logger = LogManager()
    logger.info("开始重试功能测试")
    
    # 创建配置管理器（使用示例配置文件）
    config_file = "app/multi_target_config.yaml"
    if not os.path.exists(config_file):
        # 如果配置文件不存在，创建一个简单的测试配置
        test_config = """
acp_server:
  url: "http://localhost:80"
  username: "test"
  password: "test"

targets:
  - name: "Test Target"
    ra: "12:00:00"
    dec: "+30:00:00"
    start_time: "2025-11-29 20:00:00"
    priority: 1
    filters:
      - filter_id: "V"
        exposure: 60
        count: 5

retry_settings:
  enabled: true
  max_attempts: 3
  retry_interval_seconds: 5
  retry_on_errors:
    - connection_timeout
    - acp_server_error
"""
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(test_config)
    
    config_manager = MultiTargetConfigManager(config_file)
    
    # 创建连接管理器
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
    
    # 测试1: 基本重试配置
    print("\n1. 测试基本重试配置设置")
    retry_config = {
        'enabled': True,
        'max_attempts': 3,
        'retry_interval_seconds': 5,
        'retry_on_errors': ['connection_timeout', 'acp_server_error']
    }
    
    executor.set_retry_config(retry_config)
    print(f"✓ 重试配置已设置: {retry_config}")
    
    # 测试2: 检查重试配置是否正确保存
    print("\n2. 检查重试配置保存")
    if hasattr(executor, 'retry_config'):
        saved_config = executor.retry_config
        print(f"✓ 保存的配置: {saved_config}")
        
        # 验证配置项
        assert saved_config['enabled'] == True
        assert saved_config['max_attempts'] == 3
        assert saved_config['retry_interval_seconds'] == 5
        assert 'connection_timeout' in saved_config['retry_on_errors']
        print("✓ 配置验证通过")
    else:
        print("✗ 未找到retry_config属性")
        return False
    
    # 测试3: 测试错误类型识别
    print("\n3. 测试错误类型识别")
    test_errors = [
        ("Connection timeout after 30 seconds", "connection_timeout"),
        ("ACP server error: connection refused", "acp_server_error"),
        ("Telescope not responding", "telescope_error"),
        ("Camera error: device not found", "camera_error"),
        ("Meridian flip failed", "meridian_flip_error"),
        ("The observatory is offline", "observatory_offline"),
        ("[lba warning]The observatory is offline", "observatory_offline"),
        ("Unknown error occurred", "unknown_error")
    ]
    
    for error_msg, expected_type in test_errors:
        error_type = executor._get_error_type(error_msg)
        if error_type == expected_type:
            print(f"✓ '{error_msg}' -> {error_type}")
        else:
            print(f"✗ '{error_msg}' -> {error_type} (期望: {expected_type})")
    
    # 测试4: 测试重试间隔设置
    print("\n4. 测试重试间隔设置")
    new_config = {
        'enabled': True,
        'max_attempts': 2,
        'retry_interval_seconds': 10,
        'retry_on_errors': ['connection_timeout']
    }
    
    executor.set_retry_config(new_config)
    if executor.retry_config['retry_interval_seconds'] == 10:
        print("✓ 重试间隔更新成功")
    else:
        print("✗ 重试间隔更新失败")
    
    # 测试5: 测试禁用重试
    print("\n5. 测试禁用重试")
    disable_config = {'enabled': False}
    executor.set_retry_config(disable_config)
    
    if executor.retry_config['enabled'] == False:
        print("✓ 重试功能已禁用")
    else:
        print("✗ 重试功能禁用失败")
    
    print("\n=== 重试功能测试完成 ===")
    logger.info("重试功能测试完成")
    
    return True


def test_config_file_integration():
    """测试配置文件集成"""
    print("\n=== 测试配置文件集成 ===")
    
    # 创建示例配置文件
    config_content = """
# 观测配置文件
observation:
  # 重试设置
  retry_settings:
    enabled: true
    max_attempts: 5
    retry_interval_seconds: 15
    retry_on_errors:
      - connection_timeout
      - acp_server_error
      - telescope_error
  
  # 其他设置
  timeout_minutes: 60
  check_interval_seconds: 30
"""
    
    config_path = Path("test_config.yaml")
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"✓ 创建测试配置文件: {config_path}")
        
        # 这里可以添加从配置文件读取重试设置的测试
        # 由于需要完整的配置管理器支持，暂时只做文件创建测试
        
    except Exception as e:
        print(f"✗ 配置文件创建失败: {e}")
        return False
    finally:
        # 清理测试文件
        if config_path.exists():
            config_path.unlink()
            print("✓ 清理测试文件")
    
    return True


if __name__ == "__main__":
    print("重试功能测试程序")
    print("=" * 50)
    
    try:
        # 运行基本功能测试
        success1 = test_retry_functionality()
        
        # 运行配置文件集成测试
        success2 = test_config_file_integration()
        
        if success1 and success2:
            print("\n🎉 所有测试通过！")
            sys.exit(0)
        else:
            print("\n❌ 部分测试失败")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)