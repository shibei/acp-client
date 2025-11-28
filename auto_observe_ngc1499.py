"""
自动观测脚本 - NGC 1499
在指定时间停止当前脚本，启动新的观测序列

目标：NGC 1499
坐标：RA 04:01:07.51, DEC +36:31:11.9
滤镜：H-alpha
曝光：600秒
数量：30张
启动时间：2025-11-20 02:30:00
"""

import time
from datetime import datetime
from ACP import ACPClient, ImagingPlan
from ACP.gui.logger import LogManager


def main():
    """主函数"""
    # 配置参数
    TARGET_TIME = datetime(2025, 11, 19, 23, 39, 0)  # 2025-11-20 02:30:00
    
    # ACP服务器配置
    ACP_URL = "http://27056t89i6.wicp.vip:1011"
    ACP_USER = "share"
    ACP_PASSWORD = "1681"
    
    # 目标配置
    TARGET_NAME = "NGC 1499"
    TARGET_RA = "04:01:07.51"
    TARGET_DEC = "+36:31:11.9"
    
    # 滤镜配置 (H-alpha滤镜)
    # 注意：需要根据你的滤镜轮配置调整filter_id
    # 通常 0=L, 1=R, 2=G, 3=B, 4=H-alpha, 5=O-III, 6=S-II
    FILTER_ID = 4  # H-alpha滤镜ID，请根据实际情况调整
    EXPOSURE_TIME = 600  # 600秒
    IMAGE_COUNT = 30  # 30张
    BINNING = 1  # 1x1像素合并
    
    # 其他参数
    DITHER = 5  # 抖动5像素
    AUTO_FOCUS = True  # 启用自动对焦
    AF_INTERVAL = 120  # 每120分钟对焦一次
    
    # 初始化日志
    log_manager = LogManager('AutoObserve_NGC1499')
    
    print("="*70)
    print("NGC 1499 自动观测脚本")
    print("="*70)
    print(f"目标名称: {TARGET_NAME}")
    print(f"坐标: RA {TARGET_RA}, DEC {TARGET_DEC}")
    print(f"滤镜: H-alpha (ID: {FILTER_ID})")
    print(f"曝光: {EXPOSURE_TIME}秒 x {IMAGE_COUNT}张")
    print(f"预计总时间: {EXPOSURE_TIME * IMAGE_COUNT / 3600:.1f}小时")
    print(f"计划启动时间: {TARGET_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 连接到ACP服务器
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在连接到ACP服务器...")
        client = ACPClient(ACP_URL, ACP_USER, ACP_PASSWORD)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 成功连接到ACP服务器")
        log_manager.info(f"成功连接到ACP服务器: {ACP_URL}")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 连接失败: {e}")
        log_manager.error(f"连接ACP服务器失败: {e}", exc_info=True)
        return
    
    # 等待到指定时间
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 等待到预定时间...")
    while True:
        now = datetime.now()
        time_diff = (TARGET_TIME - now).total_seconds()
        
        if time_diff <= 0:
            break
        
        # 每30秒显示一次倒计时
        if int(time_diff) % 30 == 0:
            hours = int(time_diff // 3600)
            minutes = int((time_diff % 3600) // 60)
            seconds = int(time_diff % 60)
            print(f"[{now.strftime('%H:%M:%S')}] 距离启动还有: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        time.sleep(1)
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⏰ 到达预定时间，开始执行任务...")
    log_manager.info("到达预定时间，开始执行NGC 1499观测任务")
    
    # 步骤1: 停止当前运行的脚本
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在停止当前脚本...")
        success = client.stop_script()
        time.sleep(300)  # 等待5分钟确保脚本停止
        if success:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 当前脚本已停止")
            log_manager.info("成功停止当前脚本")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ 停止脚本可能失败，继续执行...")
            log_manager.warning("停止脚本响应异常")
        
        # 等待5秒，确保脚本完全停止
        time.sleep(5)
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 停止脚本时出错: {e}")
        log_manager.error(f"停止脚本失败: {e}", exc_info=True)
    
    # 步骤2: 创建新的成像计划
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在创建成像计划...")
    
    # 配置滤镜
    filters = [{
        'filter_id': FILTER_ID,
        'count': IMAGE_COUNT,
        'exposure': EXPOSURE_TIME,
        'binning': BINNING
    }]
    
    # 创建成像计划
    plan = ImagingPlan(
        target=TARGET_NAME,
        ra=TARGET_RA,
        dec=TARGET_DEC,
        filters=filters,
        dither=DITHER,
        auto_focus=AUTO_FOCUS,
        periodic_af_interval=AF_INTERVAL
    )
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 成像计划详情:")
    print(f"  - 目标: {TARGET_NAME}")
    print(f"  - 坐标: {TARGET_RA} / {TARGET_DEC}")
    print(f"  - 滤镜ID: {FILTER_ID}")
    print(f"  - 曝光: {EXPOSURE_TIME}秒")
    print(f"  - 数量: {IMAGE_COUNT}张")
    print(f"  - 抖动: {DITHER}像素")
    print(f"  - 自动对焦: {'是' if AUTO_FOCUS else '否'}")
    print(f"  - 对焦间隔: {AF_INTERVAL}分钟")
    
    # 步骤3: 启动新的成像计划
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在启动成像计划...")
        success = client.start_imaging_plan(plan)
        
        if success:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 成像计划启动成功！")
            print(f"\n{'='*70}")
            print("任务已启动！")
            print(f"目标: {TARGET_NAME}")
            print(f"预计完成时间: {(datetime.now() + timedelta(hours=EXPOSURE_TIME * IMAGE_COUNT / 3600)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}")
            log_manager.info(f"成功启动NGC 1499成像计划: {IMAGE_COUNT}张 x {EXPOSURE_TIME}秒")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 成像计划启动失败！")
            log_manager.error("成像计划启动失败")
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 启动成像计划时出错: {e}")
        log_manager.error(f"启动成像计划失败: {e}", exc_info=True)
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 脚本执行完成")
    log_manager.info("自动观测脚本执行完成")


if __name__ == "__main__":
    from datetime import timedelta
    main()
