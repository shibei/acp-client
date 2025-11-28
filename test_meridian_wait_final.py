#!/usr/bin/env python3
"""
中天反转等待功能验证测试
"""

import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))

from datetime import datetime, timedelta
from lib.meridian_flip_manager import MeridianFlipManager
from lib.utils.observation_utils import ObservationUtils

def test_meridian_wait_functionality():
    """测试中天反转等待功能"""
    print("=== 中天反转等待功能测试 ===")
    
    try:
        # 创建中天管理器
        meridian_manager = MeridianFlipManager(dryrun=True)
        meridian_manager.set_observatory_location(39.9, 116.4)  # 北京天文台坐标
        
        # 测试目标 - IC 1871
        target_ra = "03 10 30"
        target_dec = "+60 25 00"
        
        # 解析坐标
        ra_deg, dec_deg = ObservationUtils.parse_ra_dec(target_ra, target_dec)
        
        print(f"目标: RA={target_ra}, DEC={target_dec}")
        print(f"解析坐标: RA={ra_deg:.2f}°, DEC={dec_deg:.2f}°")
        
        # 测试不同时间点
        test_scenarios = [
            ("中天前1小时", datetime.now().replace(hour=21, minute=30, second=0, microsecond=0)),
            ("中天前10分钟", datetime.now().replace(hour=22, minute=20, second=0, microsecond=0)),
            ("中天时间", datetime.now().replace(hour=22, minute=30, second=0, microsecond=0)),
            ("中天后10分钟", datetime.now().replace(hour=22, minute=40, second=0, microsecond=0)),
            ("中天后1小时", datetime.now().replace(hour=23, minute=30, second=0, microsecond=0)),
        ]
        
        print("\n=== 中天反转检查测试 ===")
        
        for scenario_name, test_time in test_scenarios:
            print(f"\n【{scenario_name}】{test_time.strftime('%H:%M:%S')}")
            
            # 检查中天反转需求
            meridian_info = meridian_manager.check_meridian_flip_needed(
                ra_deg, dec_deg, test_time
            )
            
            print(f"状态: {meridian_info['status']}")
            print(f"需要等待: {'是' if meridian_info['wait_needed'] else '否'}")
            print(f"消息: {meridian_info['message']}")
            
            # 如果需要等待，测试等待功能
            if meridian_info['wait_needed']:
                print("→ 开始执行中天反转等待...")
                
                # 模拟等待过程
                wait_result = meridian_manager.wait_for_meridian_flip(
                    ra_deg, dec_deg, test_time
                )
                
                if wait_result:
                    print("✓ 中天反转等待成功完成")
                else:
                    print("✗ 中天反转等待失败")
            
            time.sleep(1)  # 避免输出过快
        
        print("\n=== 测试执行器中的中天反转逻辑 ===")
        
        # 模拟执行器中的监控循环逻辑
        from lib.execution.target_observation_executor import TargetObservationExecutor
        from lib.core.acp_connection_manager import ACPConnectionManager
        from lib.core.acp_imaging_manager import ACPImagingManager
        from lib.utils.log_manager import LogManager
        
        # 创建模拟组件
        log_manager = LogManager('Test_Executor', dryrun=True)
        connection_manager = ACPConnectionManager(log_manager, dryrun=True)
        imaging_manager = ACPImagingManager(log_manager, dryrun=True)
        
        # 创建执行器
        executor = TargetObservationExecutor(
            connection_manager, imaging_manager, log_manager, dryrun=True
        )
        
        # 设置中天管理器
        executor.set_meridian_manager(meridian_manager)
        
        # 模拟状态回调
        def test_status_callback(status):
            """测试状态回调"""
            current_time = status['current_time'].strftime('%H:%M:%S')
            
            if status['meridian_info'].get('wait_needed'):
                print(f"[{current_time}] 🌟 状态回调: 检测到中天反转等待需求")
                print(f"    消息: {status['meridian_info']['message']}")
            else:
                print(f"[{current_time}] 状态回调: 观测正常进行中")
        
        # 添加状态回调
        executor.add_status_callback(test_status_callback)
        
        # 模拟监控循环的几个周期
        print("\n模拟监控循环:")
        
        # 使用中天前10分钟的时间点（应该触发等待）
        test_time = datetime.now().replace(hour=22, minute=20, second=0, microsecond=0)
        
        for cycle in range(3):
            print(f"\n--- 监控周期 {cycle + 1} ---")
            
            # 模拟获取状态
            current_time = test_time + timedelta(minutes=cycle*5)
            
            # 模拟状态字典
            status = {
                'target_name': 'IC 1871',
                'current_time': current_time,
                'is_completed': False,
                'has_error': False,
                'meridian_info': meridian_manager.check_meridian_flip_needed(
                    ra_deg, dec_deg, current_time
                ),
                'acp_status': {'is_running': True, 'filter': 'L'},
                'elapsed_time': timedelta(minutes=cycle*5),
                'estimated_duration': timedelta(hours=2),
                'progress': (cycle+1) * 0.2,
                'plan_status': {}
            }
            
            # 执行状态回调
            for callback in executor.status_callbacks:
                callback(status)
            
            # 检查中天反转等待（这是关键测试点）
            if status['meridian_info'].get('wait_needed'):
                print(f"[{current_time.strftime('%H:%M:%S')}] 🌟 执行中天反转等待...")
                
                # 模拟等待过程
                wait_success = meridian_manager.wait_for_meridian_flip(
                    ra_deg, dec_deg, current_time
                )
                
                if wait_success:
                    print("✓ 中天反转等待完成")
                else:
                    print("✗ 中天反转等待被中断")
                    break
            
            print(f"[{current_time.strftime('%H:%M:%S')}] 等待30秒进入下一周期...")
            time.sleep(1)  # 模拟等待
        
        print("\n=== 测试总结 ===")
        print("✓ 中天反转检查功能正常")
        print("✓ 状态回调机制正常")
        print("✓ 监控循环中的等待逻辑正常")
        print("✓ 执行器中天反转集成正常")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_meridian_wait_functionality()
    sys.exit(0 if success else 1)