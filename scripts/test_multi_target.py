#!/usr/bin/env python3
"""
多目标观测配置测试脚本
用于验证配置文件和系统功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from lib.multi_target_config import MultiTargetConfig
from lib.multi_target_plan_builder import MultiTargetPlanBuilder


def test_config():
    """测试配置文件"""
    print("正在测试多目标观测配置...")
    print("="*60)
    
    try:
        # 测试配置文件路径
        config_file = os.path.join(os.path.dirname(__file__), 'multi_target_config.yaml')
        
        if not os.path.exists(config_file):
            print(f"错误: 配置文件 {config_file} 不存在")
            return False
        
        # 加载配置
        config = MultiTargetConfig(config_file)
        
        print("✓ 配置文件加载成功")
        
        # 打印配置摘要
        config.print_schedule()
        
        # 测试目标获取
        current_time = datetime.now()
        current_target = config.get_current_target(current_time)
        next_target = config.get_next_target(current_time)
        
        if current_target:
            print(f"✓ 当前目标: {current_target['name']}")
        else:
            print("✓ 当前无目标")
        
        if next_target:
            print(f"✓ 下一个目标: {next_target['name']} (开始时间: {next_target['start_time']})")
        else:
            print("✓ 无后续目标")
        
        # 测试计划构建器
        plan_builder = MultiTargetPlanBuilder(config)
        plans = plan_builder.build_all_plans()
        
        print(f"✓ 成功创建 {len(plans)} 个观测计划")
        
        # 打印计划摘要
        plan_builder.print_summary()
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        return False


def test_yaml_syntax():
    """测试YAML文件语法"""
    print("正在测试YAML文件语法...")
    
    try:
        import yaml
        config_file = os.path.join(os.path.dirname(__file__), 'multi_target_config.yaml')
        
        with open(config_file, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        
        print("✓ YAML文件语法正确")
        return True
        
    except yaml.YAMLError as e:
        print(f"✗ YAML语法错误: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ 文件读取错误: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("多目标观测系统测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试YAML语法
    if not test_yaml_syntax():
        return 1
    
    print()
    
    # 测试配置
    if not test_config():
        return 1
    
    print()
    print("="*60)
    print("✓ 所有测试通过！")
    print("可以使用: python auto_observe_multi_target.py 开始观测")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())