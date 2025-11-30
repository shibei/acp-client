#!/usr/bin/env python3
"""
测试401认证错误处理
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from lib.execution.target_observation_executor import TargetObservationExecutor
from lib.config.config_manager import MultiTargetConfigManager

def test_401_error_classification():
    """测试401错误分类"""
    print("测试401错误分类...")
    
    # 创建模拟的executor实例
    from lib.core.acp_connection_manager import ACPConnectionManager
    from lib.core.acp_imaging_manager import ACPImagingManager
    from lib.utils.log_manager import LogManager
    
    # 创建最小化的依赖项
    log_manager = LogManager("Test", enable_console=False)
    connection_manager = ACPConnectionManager("http://test", "user", "pass", dryrun=True)
    imaging_manager = ACPImagingManager(connection_manager)
    
    executor = TargetObservationExecutor(
        connection_manager=connection_manager,
        imaging_manager=imaging_manager,
        log_manager=log_manager,
        dryrun=True
    )
    
    # 测试不同的401错误信息
    test_errors = [
        "401 Client Error: Access Denied - Invalid login or account disabled for url: http://example.com/ac/astopscript.asp",
        "HTTP 401 Unauthorized",
        "Access Denied: Invalid credentials",
        "Invalid login or account disabled",
        "Connection timeout error",
        "ACP server error occurred"
    ]
    
    expected_results = [
        "authentication_failed",
        "authentication_failed", 
        "authentication_failed",
        "authentication_failed",
        "connection_timeout",
        "acp_server_error"
    ]
    
    print("\n错误分类测试结果:")
    print("-" * 60)
    
    all_passed = True
    for i, (error_msg, expected) in enumerate(zip(test_errors, expected_results)):
        result = executor._get_error_type(error_msg)
        status = "✅ 通过" if result == expected else "❌ 失败"
        print(f"测试 {i+1}: {status}")
        print(f"  错误信息: {error_msg}")
        print(f"  预期结果: {expected}")
        print(f"  实际结果: {result}")
        print()
        
        if result != expected:
            all_passed = False
    
    print("-" * 60)
    if all_passed:
        print("🎉 所有测试通过！401错误分类已正确配置。")
    else:
        print("⚠️  部分测试失败，请检查错误分类逻辑。")
    
    return all_passed

def test_retry_configuration():
    """测试重试配置"""
    print("\n测试重试配置...")
    
    try:
        # 加载配置文件
        config_file = os.path.join(os.path.dirname(__file__), 'configs', 'multi_target_config.yaml')
        config_manager = MultiTargetConfigManager(config_file)
        config = config_manager.get_config()
        
        retry_settings = config.retry_settings
        print(f"重试配置: {retry_settings}")
        
        # 检查是否包含authentication_failed
        if 'authentication_failed' in retry_settings.get('retry_on_errors', []):
            print("✅ 配置文件中已包含 authentication_failed 错误类型")
            return True
        else:
            print("❌ 配置文件中未包含 authentication_failed 错误类型")
            return False
            
    except Exception as e:
        print(f"❌ 测试重试配置失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("401认证错误处理测试")
    print("=" * 60)
    
    # 运行测试
    test1_passed = test_401_error_classification()
    test2_passed = test_retry_configuration()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 所有测试通过！系统已正确配置401错误处理。")
        print("\n下次遇到401认证错误时，系统将:")
        print("1. 正确识别错误类型为 'authentication_failed'")
        print("2. 根据配置的重试设置进行重试")
        print("3. 记录详细的错误日志")
    else:
        print("⚠️  部分测试失败，请检查配置和代码逻辑。")
    
    sys.exit(0 if (test1_passed and test2_passed) else 1)