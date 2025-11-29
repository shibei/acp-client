#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""错误类型识别测试"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from lib.execution.target_observation_executor import TargetObservationExecutor

# 测试错误信息
test_errors = [
    "[lba warning]The observatory is offline",
    "ic 405 观测计划启动失败: [lba warning]The observatory is offline",
    "观测计划启动失败: [lba warning]The observatory is offline"
]

def test_error_detection():
    """测试错误类型识别"""
    print("=== 错误类型识别测试 ===")
    
    # 创建临时的执行器实例来测试错误识别
    class MockExecutor:
        def _get_error_type(self, error):
            """获取错误类型"""
            error_lower = str(error).lower()
            
            if 'connection' in error_lower and 'timeout' in error_lower:
                return 'connection_timeout'
            elif 'acp' in error_lower and 'server' in error_lower:
                return 'acp_server_error'
            elif 'observatory' in error_lower and 'offline' in error_lower:
                return 'observatory_offline'
            elif 'meridian' in error_lower and 'flip' in error_lower:
                return 'meridian_flip_failed'
            elif 'observation' in error_lower and 'timeout' in error_lower:
                return 'observation_timeout'
            elif 'imaging' in error_lower and 'plan' in error_lower:
                return 'imaging_plan_failed'
            elif 'status' in error_lower and 'check' in error_lower:
                return 'status_check_failed'
            elif 'telescope' in error_lower and ('not responding' in error_lower or 'error' in error_lower):
                return 'telescope_error'
            elif 'camera' in error_lower and ('error' in error_lower or 'not found' in error_lower):
                return 'camera_error'
            else:
                return 'unknown_error'
    
    executor = MockExecutor()
    
    for error in test_errors:
        error_type = executor._get_error_type(error)
        print(f"错误信息: {error}")
        print(f"识别类型: {error_type}")
        print(f"是否支持重试: {'是' if error_type in ['observatory_offline'] else '否'}")
        print("-" * 50)

if __name__ == "__main__":
    test_error_detection()