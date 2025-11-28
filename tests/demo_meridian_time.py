#!/usr/bin/env python3
"""
中天时间显示功能演示
展示如何在任务开始时显示中天时间
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'lib')))

from datetime import datetime
from app.lib.meridian_flip_manager import MeridianFlipManager


def demo_meridian_time():
    """演示中天时间计算和显示"""
    print("🌟 中天时间显示功能演示")
    print("=" * 50)
    
    # 创建中天管理器
    meridian_manager = MeridianFlipManager(dryrun=True)
    
    # 设置观测站位置（北京）
    meridian_manager.set_observatory_location(26.868789, 100.220719)
    print(f"📍 观测站位置: 纬度 26.868789°, 经度 100.220719°")
    
    # 测试几个常见目标
    test_targets = [
        {"name": "IC 1871", "ra": "02:53:19.50", "dec": "60:26:59.1"},
        {"name": "M 31", "ra": "00:42:44.30", "dec": "41:16:09.0"},
        {"name": "M 42", "ra": "05:35:17.30", "dec": "-05:23:28.0"},
        {"name": "NGC 7000", "ra": "20:58:47.10", "dec": "44:19:48.0"},
    ]
    
    current_time = datetime.now()
    print(f"⏰ 当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for target in test_targets:
        print(f"🎯 目标: {target['name']}")
        print(f"📍 坐标: RA={target['ra']}, DEC={target['dec']}")
        
        # 计算中天时间
        meridian_time = meridian_manager.calculate_meridian_time(
            target['ra'], target['dec'], current_time
        )
        
        if meridian_time:
            meridian_str = meridian_time.strftime('%H:%M:%S')
            print(f"🌟 中天时间: {meridian_str}")
            
            # 计算时间差
            time_diff = meridian_time - current_time
            hours = abs(time_diff.total_seconds()) / 3600
            if time_diff.total_seconds() > 0:
                print(f"⏳ 距离中天还有: {hours:.1f} 小时")
            else:
                print(f"⏳ 已过中天: {hours:.1f} 小时")
            
            # 检查是否需要中天反转等待
            flip_info = meridian_manager.check_meridian_flip_needed(
                target['ra'], target['dec'], current_time
            )
            
            if flip_info:
                print(f"📊 状态: {flip_info['message']}")
                if flip_info.get('wait_needed'):
                    print(f"⏸️  需要等待中天反转")
                else:
                    print(f"✅ 可以正常观测")
        else:
            print("⚠️ 无法计算中天时间")
        
        print("-" * 30)
    
    print("\n🎉 演示完成！")
    print("💡 在实际观测中，系统会在每个任务开始时自动显示中天时间")


if __name__ == "__main__":
    demo_meridian_time()