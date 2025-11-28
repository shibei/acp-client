"""
新的主程序入口
使用重构后的模块架构
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from datetime import datetime
from pathlib import Path

from lib.new_multi_target_orchestrator import NewMultiTargetOrchestrator


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='多目标自动观测系统 v2.0')
    parser.add_argument('--config', '-c', 
                       default='multi_target_config.yaml',
                       help='配置文件路径 (默认: multi_target_config.yaml)')
    parser.add_argument('--dry-run', '-d', 
                       action='store_true',
                       help='DRYRUN模式 (不实际执行观测)')
    parser.add_argument('--validate', '-v',
                       action='store_true',
                       help='仅验证配置和目标，不执行观测')
    parser.add_argument('--summary', '-s',
                       action='store_true',
                       help='显示调度摘要')
    
    args = parser.parse_args()
    
    try:
        # 检查配置文件是否存在
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"错误: 配置文件 {args.config} 不存在")
            return 1
        
        # 创建协调器
        orchestrator = NewMultiTargetOrchestrator(
            config_file=str(config_path),
            dry_run=args.dry_run
        )
        
        # 验证模式
        if args.validate:
            print("\n=== 配置验证模式 ===")
            validation_results = orchestrator.validate_targets()
            
            print(f"\n验证结果:")
            for result in validation_results:
                status = "✓" if result.get('valid', False) else "✗"
                print(f"{status} {result['name']}")
                if not result.get('valid', False):
                    if 'error' in result:
                        print(f"  错误: {result['error']}")
                    elif 'observability' in result and not result['observability']['is_observable']:
                        print(f"  不可观测: {result['observability']['reason']}")
            
            return 0
        
        # 摘要模式
        if args.summary:
            print("\n=== 调度摘要 ===")
            summary = orchestrator.calculate_schedule_summary()
            
            print(f"总目标数: {summary['total_targets']}")
            print(f"有效目标数: {summary['valid_targets']}")
            print(f"无效目标数: {summary['invalid_targets']}")
            print(f"开始时间: {summary['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"结束时间: {summary['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"总持续时间: {summary['total_duration_hours']:.1f} 小时")
            
            if summary['validation_results']:
                print(f"\n详细验证结果:")
                for result in summary['validation_results']:
                    status = "✓" if result.get('valid', False) else "✗"
                    print(f"{status} {result['name']}")
            
            return 0
        
        # 正常运行模式
        print(f"\n=== 多目标自动观测系统 v2.0 ===")
        print(f"配置文件: {args.config}")
        print(f"DRYRUN模式: {'是' if args.dry_run else '否'}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 运行观测序列
        results = orchestrator.run_observation_sequence()
        
        # 显示结果
        print(f"\n=== 观测结果 ===")
        print(f"总目标数: {len(results['target_results'])}")
        print(f"成功: {results['completed_targets']}")
        print(f"失败: {results['failed_targets']}")
        print(f"整体状态: {'成功' if results['success'] else '失败'}")
        
        if results['target_results']:
            print(f"\n详细结果:")
            for result in results['target_results']:
                status = "✓" if result['success'] else "✗"
                print(f"{status} {result['target']}")
        
        # 清理资源
        orchestrator.cleanup()
        
        return 0 if results['success'] else 1
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行")
        return 1
    except Exception as e:
        print(f"\n错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())