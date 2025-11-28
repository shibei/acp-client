#!/usr/bin/env python3
"""
测试中天时间显示功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app', 'lib')))

from datetime import datetime
from lib.config.config_manager import MultiTargetConfigManager
from lib.execution.target_observation_executor import TargetObservationExecutor
from lib.core.acp_connection_manager import ACPConnectionManager
from lib.core.acp_imaging_manager import ACPImagingManager
from lib.utils.log_manager import LogManager
from lib.meridian_flip_manager import MeridianFlipManager


def test_meridian_display():
    """测试中天时间显示功能"""
    print("🌟 开始测试中天时间显示功能...")
    
    try:
        # 创建配置管理器
        config_file = os.path.join(os.path.dirname(__file__), 'app', 'multi_target_config.yaml')
        config_manager = MultiTargetConfigManager(config_file, dry_run=True)
        config = config_manager.get_config()
        
        # 创建日志管理器
        logger = LogManager(
            name="TestMeridianDisplay",
            log_dir="logs",
            log_level="INFO",
            enable_console=True
        )
        
        # 创建连接管理器
        connection_manager = ACPConnectionManager(
            server_url=config.acp_server.url,
            username=config.acp_server.username,
            password=config.acp_server.password,
            dryrun=True
        )
        
        # 创建成像管理器
        imaging_manager = ACPImagingManager(
            connection_manager=connection_manager
        )
        
        # 创建目标观测执行器
        executor = TargetObservationExecutor(
            connection_manager=connection_manager,
            imaging_manager=imaging_manager,
            log_manager=logger,
            dryrun=True
        )
        
        # 创建中天管理器
        meridian_manager = MeridianFlipManager(dryrun=True)
        
        # 设置观测站位置
        if hasattr(config, 'observatory'):
            meridian_manager.set_observatory_location(
                config.observatory.latitude,
                config.observatory.longitude
            )
            print(f"📍 观测站位置: 纬度 {config.observatory.latitude}°, 经度 {config.observatory.longitude}°")
        
        # 设置中天反转参数
        if hasattr(config, 'meridian_flip'):
            mf_config = config.meridian_flip
            if hasattr(mf_config, 'stop_minutes_before'):
                meridian_manager.stop_minutes_before = mf_config.stop_minutes_before
            if hasattr(mf_config, 'resume_minutes_after'):
                meridian_manager.resume_minutes_after = mf_config.resume_minutes_after
            if hasattr(mf_config, 'safety_margin'):
                meridian_manager.safety_margin = mf_config.safety_margin
        
        # 将中天管理器设置给执行器
        executor.set_meridian_manager(meridian_manager)
        
        # 测试目标
        if config.targets:
            test_target = config.targets[0]
            print(f"\n🎯 测试目标: {test_target.name}")
            print(f"📍 坐标: RA={test_target.ra}, DEC={test_target.dec}")
            
            # 测试中天时间计算
            current_time = datetime.now()
            meridian_time = meridian_manager.calculate_meridian_time(
                test_target.ra, test_target.dec, current_time
            )
            
            if meridian_time:
                print(f"🌟 中天时间: {meridian_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"⏰ 当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 计算时间差
                time_diff = meridian_time - current_time
                hours = abs(time_diff.total_seconds()) / 3600
                if time_diff.total_seconds() > 0:
                    print(f"⏳ 距离中天还有: {hours:.1f} 小时")
                else:
                    print(f"⏳ 已过中天: {hours:.1f} 小时")
            else:
                print("⚠️ 无法计算中天时间")
            
            # 测试执行目标（这将显示中天时间）
            print(f"\n🚀 测试执行目标观测...")
            success = executor.execute_target(test_target, config.global_settings.__dict__)
            
            if success:
                print("✅ 目标执行测试成功")
            else:
                print("❌ 目标执行测试失败")
                
        else:
            print("⚠️ 配置文件中没有找到目标")
            
        print("\n🎉 中天时间显示功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_meridian_display()
    sys.exit(0 if success else 1)