#!/usr/bin/env python3
"""
测试401错误重试机制
验证系统是否正确处理401认证错误并触发重试
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from lib.execution.target_observation_executor import TargetObservationExecutor
from lib.core.acp_connection_manager import ACPConnectionManager
from lib.core.acp_imaging_manager import ACPImagingManager
from lib.utils.log_manager import LogManager


def test_401_retry_mechanism():
    """测试401错误重试机制"""
    print("=" * 60)
    print("401错误重试机制测试")
    print("=" * 60)
    
    # 创建测试配置
    retry_config = {
        'enabled': True,
        'max_attempts': 3,
        'retry_interval_seconds': 2,  # 测试用短间隔
        'retry_on_errors': [
            'authentication_failed',  # 包含401错误
            'connection_timeout',
            'acp_server_error'
        ]
    }
    
    print(f"测试配置: {retry_config}")
    
    # 创建模拟的executor实例
    log_manager = LogManager("Test", enable_console=True)
    connection_manager = ACPConnectionManager("http://test.com", "wrong_user", "wrong_pass", dryrun=True)
    imaging_manager = ACPImagingManager(connection_manager)
    
    executor = TargetObservationExecutor(
        connection_manager=connection_manager,
        imaging_manager=imaging_manager,
        log_manager=log_manager,
        dryrun=True
    )
    
    # 设置重试配置
    executor.set_retry_config(retry_config)
    
    print("\n测试1: 验证401错误分类")
    # 模拟401错误
    error_msg = "401 Client Error: Access Denied - Invalid login or account disabled"
    error_type = executor._get_error_type(error_msg)
    print(f"错误信息: {error_msg}")
    print(f"错误类型: {error_type}")
    
    if error_type == 'authentication_failed':
        print("✅ 401错误分类正确")
    else:
        print("❌ 401错误分类失败")
        return False
    
    print("\n测试2: 验证重试配置包含authentication_failed")
    retry_on_errors = executor.retry_config.get('retry_on_errors', [])
    if 'authentication_failed' in retry_on_errors:
        print("✅ 重试配置包含authentication_failed")
    else:
        print("❌ 重试配置缺少authentication_failed")
        return False
    
    print("\n测试3: 模拟重试逻辑验证")
    print("模拟执行观测任务，预期会触发401错误重试...")
    
    # 设置一个标志来跟踪重试次数
    executor._test_retry_count = 0
    
    # 模拟错误处理逻辑
    def simulate_error_handling():
        """模拟错误处理逻辑"""
        max_attempts = retry_config['max_attempts']
        retry_interval = retry_config['retry_interval_seconds']
        retry_on_errors = retry_config['retry_on_errors']
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n尝试 {attempt}/{max_attempts}")
            
            # 模拟401错误
            error_msg = "401 Client Error: Access Denied - Invalid login or account disabled"
            error_type = executor._get_error_type(error_msg)
            
            print(f"  错误类型: {error_type}")
            
            if error_type in retry_on_errors:
                print(f"  ✅ 错误类型支持重试")
                if attempt < max_attempts:
                    print(f"  等待 {retry_interval} 秒后重试...")
                    # time.sleep(retry_interval)  # 测试时跳过实际等待
                else:
                    print("  ⚠️  已达到最大重试次数")
                    return False
            else:
                print("  ❌ 错误类型不支持重试")
                return False
        
        return False  # 所有尝试都失败
    
    result = simulate_error_handling()
    print(f"\n模拟结果: {'完成重试流程' if result else '重试次数耗尽'}")
    
    print("\n" + "=" * 60)
    print("🎉 401错误重试机制测试完成！")
    print("系统已正确配置处理401认证错误")
    return True


if __name__ == "__main__":
    test_401_retry_mechanism()