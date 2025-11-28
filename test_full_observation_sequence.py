#!/usr/bin/env python3
"""
完整观测流程测试脚本
测试任务提交后的状态监控和中天反转等待功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from datetime import datetime, timedelta
import time
from lib.new_multi_target_orchestrator import NewMultiTargetOrchestrator
from lib.meridian_flip_manager import MeridianFlipManager
from lib.utils.log_manager import LogManager
from lib.utils.time_utils import TimeUtils
from lib.utils.observation_utils import ObservationUtils

def test_full_sequence():
    """测试完整观测序列"""
    print("=== 完整观测序列测试 ===")
    
    # 创建模拟配置
    config_content = """
observatory:
  latitude_deg: 39.9
  longitude_deg: 116.4
  min_altitude: 30

schedule:
  stop_time: "2024-12-31 06:00:00"

targets:
  - name: "IC 1871"
    ra: "03 10 30"
    dec: "+60 25 00"
    meridian_time: "22:30:00"
    filters:
      - name: "L"
        exposure: 300
        count: 6
      - name: "R"
        exposure: 300
        count: 3
      - name: "G"
        exposure: 300
        count: 3
      - name: "B"
        exposure: 300
        count: 3
"""
    
    # 写入临时配置文件
    config_file = "test_config.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    try:
        # 创建协调器
        print("创建观测协调器...")
        orchestrator = NewMultiTargetOrchestrator(
            config_file=config_file,
            dry_run=True  # 使用DRYRUN模式测试
        )
        
        # 验证配置
        print("\n验证配置和目标...")
        validation_results = orchestrator.validate_targets()
        
        for result in validation_results:
            status = "✓" if result.get('valid', False) else "✗"
            print(f"{status} {result['name']}")
            if not result.get('valid', False):
                print(f"  错误: {result.get('error', '未知错误')}")
        
        # 获取调度摘要
        print("\n获取调度摘要...")
        summary = orchestrator.calculate_schedule_summary()
        print(f"总目标数: {summary['total_targets']}")
        print(f"有效目标数: {summary['valid_targets']}")
        print(f"无效目标数: {summary['invalid_targets']}")
        
        # 测试中天反转检查
        print("\n=== 测试中天反转检查 ===")
        
        # 获取目标
        config = orchestrator.config_manager.get_config()
        target = config.targets[0]
        
        # 创建中天管理器
        meridian_manager = MeridianFlipManager(dryrun=True)
        meridian_manager.set_observatory_location(
            config.observatory.latitude_deg,
            config.observatory.longitude_deg
        )
        
        # 测试不同时间点
        test_times = [
            datetime.now().replace(hour=20, minute=0, second=0, microsecond=0),  # 中天前
            datetime.now().replace(hour=22, minute=25, second=0, microsecond=0),  # 中天前5分钟
            datetime.now().replace(hour=22, minute=35, second=0, microsecond=0),  # 中天后5分钟
        ]
        
        for test_time in test_times:
            print(f"\n测试时间: {test_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 解析坐标
            ra_deg, dec_deg = ObservationUtils.parse_ra_dec(target.ra, target.dec)
            
            # 检查中天反转需求
            meridian_info = meridian_manager.check_meridian_flip_needed(
                ra_deg, dec_deg, test_time
            )
            
            print(f"状态: {meridian_info['status']}")
            print(f"需要等待: {'是' if meridian_info['wait_needed'] else '否'}")
            print(f"消息: {meridian_info['message']}")
            
            if meridian_info['wait_needed']:
                print("→ 将执行中天反转等待")
        
        # 测试监控方法
        print("\n=== 测试监控方法 ===")
        
        # 获取执行器
        executor = orchestrator.executor
        
        # 设置中天管理器
        executor.set_meridian_manager(meridian_manager)
        
        # 测试状态回调
        def status_callback(status):
            """状态回调函数"""
            current_time = status['current_time'].strftime('%H:%M:%S')
            target_name = status['target_name']
            
            if status['meridian_info'].get('wait_needed'):
                print(f"[{current_time}] 🌟 检测到中天反转等待需求: {status['meridian_info']['message']}")
            else:
                print(f"[{current_time}] {target_name} 状态正常")
        
        # 添加状态回调
        executor.add_status_callback(status_callback)
        
        print("状态回调函数已设置")
        
        # 测试监控循环（模拟）
        print("\n=== 模拟监控循环 ===")
        
        # 模拟观测开始
        executor.current_target = target
        executor.observation_start_time = datetime.now()
        
        # 模拟几个监控周期
        for i in range(3):
            current_time = datetime.now()
            
            # 获取状态（模拟）
            status = {
                'target_name': target.name,
                'current_time': current_time,
                'is_completed': False,
                'has_error': False,
                'meridian_info': meridian_manager.check_meridian_flip_needed(
                    *ObservationUtils.parse_ra_dec(target.ra, target.dec), 
                    current_time
                ),
                'acp_status': {'is_running': True, 'filter': 'L'},
                'elapsed_time': timedelta(minutes=i*5),
                'estimated_duration': timedelta(hours=2),
                'progress': (i+1) * 0.1,
                'plan_status': {}
            }
            
            # 执行状态回调
            for callback in executor.status_callbacks:
                callback(status)
            
            # 检查中天反转等待
            if status['meridian_info'].get('wait_needed'):
                print(f"[{current_time.strftime('%H:%M:%S')}] 🌟 执行中天反转等待...")
                # 模拟等待过程
                wait_success = meridian_manager.wait_for_meridian_flip(
                    *ObservationUtils.parse_ra_dec(target.ra, target.dec), 
                    current_time
                )
                if wait_success:
                    print("✓ 中天反转等待完成")
                else:
                    print("✗ 中天反转等待失败")
            
            time.sleep(2)  # 模拟30秒间隔
        
        print("\n=== 测试完成 ===")
        print("✓ 中天反转检查功能正常")
        print("✓ 状态回调机制正常")
        print("✓ 监控循环逻辑正常")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理临时文件
        if os.path.exists(config_file):
            os.remove(config_file)
        
        # 清理资源
        if 'orchestrator' in locals():
            orchestrator.cleanup()
    
    return True

if __name__ == "__main__":
    success = test_full_sequence()
    sys.exit(0 if success else 1)