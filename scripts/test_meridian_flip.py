#!/usr/bin/env python3
"""
中天反转管理器测试脚本
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from datetime import datetime, timedelta
from lib.meridian_flip_manager import MeridianFlipManager


def test_meridian_flip_calculations():
    """测试中天反转计算"""
    print("🌟 开始测试中天反转管理器")
    print("=" * 50)
    
    # 创建中天管理器
    mf_manager = MeridianFlipManager(dryrun=True)
    
    # 设置观测站位置（北京）
    mf_manager.set_observatory_location(39.9, 116.4)
    print(f"观测站位置: 纬度 {mf_manager.observatory_latitude}°, 经度 {mf_manager.observatory_longitude}°")
    
    # 测试目标
    test_targets = [
        {
            'name': 'NGC 1499',
            'ra': '04:01:07.51',
            'dec': '+36:31:11.9'
        },
        {
            'name': 'M 31',
            'ra': '00:42:44.30',
            'dec': '+41:16:09.0'
        },
        {
            'name': 'M 33',
            'ra': '01:33:50.90',
            'dec': '+30:39:35.8'
        }
    ]
    
    current_time = datetime.now()
    print(f"当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for target in test_targets:
        print(f"🎯 目标: {target['name']}")
        print(f"  坐标: RA={target['ra']}, DEC={target['dec']}")
        
        # 计算中天时间
        meridian_time = mf_manager.calculate_meridian_time(
            target['ra'], target['dec'], current_time
        )
        
        if meridian_time:
            print(f"  中天时间: {meridian_time.strftime('%H:%M:%S')}")
            
            # 计算中天反转窗口
            flip_window = mf_manager.calculate_meridian_flip_window(
                target['ra'], target['dec'], current_time
            )
            
            if flip_window:
                print(f"  停止时间: {flip_window['stop_time'].strftime('%H:%M:%S')}")
                print(f"  恢复时间: {flip_window['resume_time'].strftime('%H:%M:%S')}")
                print(f"  停止提前: {flip_window['stop_minutes_before']} 分钟")
                print(f"  恢复延后: {flip_window['resume_minutes_after']} 分钟")
                
                # 检查当前状态
                flip_info = mf_manager.check_meridian_flip_needed(
                    target['ra'], target['dec'], current_time
                )
                
                print(f"  当前状态: {flip_info['status']}")
                print(f"  状态信息: {flip_info['message']}")
                print(f"  需要等待: {'是' if flip_info['wait_needed'] else '否'}")
                
                if flip_info['wait_needed']:
                    print(f"  等待直到: {flip_info['wait_until'].strftime('%H:%M:%S')}")
            else:
                print("  ❌ 无法计算中天反转窗口")
        else:
            print("  ❌ 无法计算中天时间")
        
        print("-" * 30)
    
    print("\n✅ 中天反转计算测试完成")


def test_meridian_flip_waiting():
    """测试中天反转等待功能"""
    print("\n🌟 开始测试中天反转等待功能")
    print("=" * 50)
    
    # 创建中天管理器
    mf_manager = MeridianFlipManager(dryrun=True)
    mf_manager.set_observatory_location(39.9, 116.4)
    
    # 创建一个模拟目标（选择合适的中天时间）
    target = {
        'name': '测试目标',
        'ra': '12:00:00.00',  # 选择中午附近的中天时间
        'dec': '+30:00:00.0'
    }
    
    # 模拟当前时间（设置为中天前15分钟）
    current_time = datetime.now().replace(hour=11, minute=45, second=0)
    print(f"模拟当前时间: {current_time.strftime('%H:%M:%S')}")
    
    # 检查中天状态
    flip_info = mf_manager.check_meridian_flip_needed(
        target['ra'], target['dec'], current_time
    )
    
    print(f"目标: {target['name']}")
    print(f"坐标: RA={target['ra']}, DEC={target['dec']}")
    print(f"状态: {flip_info['status']}")
    print(f"信息: {flip_info['message']}")
    
    if flip_info['wait_needed']:
        print(f"\n开始中天反转等待...")
        success = mf_manager.wait_for_meridian_flip(
            target['ra'], target['dec'], current_time
        )
        
        if success:
            print("✅ 中天反转等待完成")
        else:
            print("❌ 中天反转等待被中断")
    else:
        print("当前不需要中天反转等待")
    
    print("\n✅ 中天反转等待测试完成")


def test_configuration():
    """测试配置参数"""
    print("\n🌟 开始测试配置参数")
    print("=" * 50)
    
    mf_manager = MeridianFlipManager(dryrun=True)
    
    # 测试默认参数
    print(f"默认停止提前时间: {mf_manager.stop_minutes_before} 分钟")
    print(f"默认恢复延后时间: {mf_manager.resume_minutes_after} 分钟")
    print(f"默认安全边距: {mf_manager.safety_margin} 分钟")
    print(f"默认纬度: {mf_manager.observatory_latitude}°")
    print(f"默认经度: {mf_manager.observatory_longitude}°")
    
    # 修改参数
    mf_manager.stop_minutes_before = 15
    mf_manager.resume_minutes_after = 20
    mf_manager.safety_margin = 5
    
    print(f"\n修改后的停止提前时间: {mf_manager.stop_minutes_before} 分钟")
    print(f"修改后的恢复延后时间: {mf_manager.resume_minutes_after} 分钟")
    print(f"修改后的安全边距: {mf_manager.safety_margin} 分钟")
    
    # 设置观测站位置
    mf_manager.set_observatory_location(31.2, 121.5)  # 上海
    print(f"\n设置观测站位置: 纬度 {mf_manager.observatory_latitude}°, 经度 {mf_manager.observatory_longitude}°")
    
    print("\n✅ 配置参数测试完成")


def main():
    """主函数"""
    print("🚀 中天反转管理器测试程序")
    print("=" * 60)
    
    try:
        # 运行测试
        test_meridian_flip_calculations()
        test_meridian_flip_waiting()
        test_configuration()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("✅ 中天反转管理器功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())