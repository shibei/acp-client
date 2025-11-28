#!/usr/bin/env python3
"""
多目标自动观测脚本

功能特点：
- 支持按时间顺序执行多个观测目标
- 每个目标可以有不同的滤镜配置
- 自动等待目标观测时间
- 支持全局停止时间
- 实时监控每个目标的观测状态
- 详细的日志记录

使用方法：
    python auto_observe_multi_target.py

配置文件：
    multi_target_config.yaml - 包含所有观测目标和参数配置
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.multi_target_orchestrator import MultiTargetOrchestrator


def main():
    """主函数"""
    # 配置文件路径
    config_file = os.path.join(os.path.dirname(__file__), 'multi_target_config.yaml')
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"错误: 配置文件 {config_file} 不存在")
        print("请创建 multi_target_config.yaml 文件并配置观测参数")
        return 1
    
    try:
        # 创建多目标观测编排器
        orchestrator = MultiTargetOrchestrator(config_file)
        
        # 运行观测流程
        orchestrator.run()
        
        return 0
        
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 用户中断脚本执行")
        return 1
        
    except Exception as e:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 脚本执行出错: {str(e)}")
        return 1


if __name__ == "__main__":
    from datetime import datetime
    sys.exit(main())