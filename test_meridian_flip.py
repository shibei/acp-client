#!/usr/bin/env python3
"""
测试中天反转等待功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from datetime import datetime, timedelta
from lib.meridian_flip_manager import MeridianFlipManager
from lib.utils.log_manager import LogManager

def test_meridian_flip():
    """测试中天反转功能"""
    print("🌟 开始测试中天反转等待功能")
    print("=" * 50)
    
    # 创建日志管理器
    log_manager = LogManager()
    
    # 创建中天管理器（使用北京天文台坐标）
    meridian_manager = MeridianFlipManager(dryrun=True)
    meridian_manager.set_observatory_location(39.9, 116.3)  # 设置观测站位置
    
    # 测试目标：IC 1871
    target_ra = "04:01:07.51"
    target_dec = "+36:31:11.9"
    
    # 测试当前时间（设置在中天前30分钟）
    current_time = datetime.now()
    
    print(f"测试目标: RA={target_ra}, DEC={target_dec}")
    print(f"当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查中天反转需求
    print("1. 检查中天反转需求...")
    flip_info = meridian_manager.check_meridian_flip_needed(
        target_ra, target_dec, current_time
    )
    
    print(f"   状态: {flip_info['status']}")
    print(f"   消息: {flip_info['message']}")
    print(f"   需要等待: {flip_info['wait_needed']}")
    
    if flip_info['wait_needed']:
        print(f"   等待直到: {flip_info['wait_until'].strftime('%H:%M:%S')}")
    print()
    
    # 测试等待功能
    print("2. 测试中天反转等待...")
    if flip_info['wait_needed']:
        print("   开始执行等待...")
        success = meridian_manager.wait_for_meridian_flip(
            target_ra, target_dec, current_time
        )
        print(f"   等待结果: {'成功' if success else '失败'}")
    else:
        print("   当前不需要等待")
    
    print()
    print("✅ 中天反转测试完成")
    
    # 测试不同时间点的状态
    print("\n3. 测试不同时间点的状态...")
    test_times = [
        ("中天前1小时", current_time - timedelta(minutes=60)),
        ("中天前10分钟", current_time - timedelta(minutes=10)),
        ("中天时间", current_time),
        ("中天后10分钟", current_time + timedelta(minutes=10)),
        ("中天后1小时", current_time + timedelta(minutes=60))
    ]
    
    for desc, test_time in test_times:
        info = meridian_manager.check_meridian_flip_needed(
            target_ra, target_dec, test_time
        )
        print(f"   {desc}: {info['status']} - {info['message']}")

if __name__ == "__main__":
    test_meridian_flip()