"""
自动观测脚本 - NGC 1499
在指定时间停止当前脚本，启动新的观测序列

目标：NGC 1499
坐标：RA 04:01:07.51, DEC +36:31:11.9
滤镜：H-alpha
曝光：600秒
数量：30张
停止时间：可选，如果设置则先停止当前计划
启动时间：2025-11-20 02:30:00
"""

import time
from datetime import datetime, timedelta
from ACP import ACPClient, ImagingPlan
from ACP.gui.logger import LogManager


class ObservationConfig:
    """观测配置类"""
    def __init__(self):
        # 时间配置
        self.stop_time = datetime(2025, 11, 19, 23, 30, 0)  # 停止时间（None则不停止）
        self.start_time = datetime(2025, 11, 19, 23, 39, 0)  # 启动时间
        
        # ACP服务器配置
        self.acp_url = "http://27056t89i6.wicp.vip:1011"
        self.acp_user = "share"
        self.acp_password = "1681"
        
        # 目标配置
        self.target_name = "NGC 1499"
        self.target_ra = "04:01:07.51"
        self.target_dec = "+36:31:11.9"
        
        # 滤镜配置
        self.filter_id = 4  # H-alpha
        self.exposure_time = 600  # 秒
        self.image_count = 30
        self.binning = 1
        
        # 其他参数
        self.dither = 5  # 像素
        self.auto_focus = True
        self.af_interval = 120  # 分钟
    
    def get_total_hours(self):
        """计算预计总时间（小时）"""
        return self.exposure_time * self.image_count / 3600


def print_banner(config):
    """打印脚本信息横幅"""
    print("="*70)
    print("NGC 1499 自动观测脚本")
    print("="*70)
    print(f"目标名称: {config.target_name}")
    print(f"坐标: RA {config.target_ra}, DEC {config.target_dec}")
    print(f"滤镜: H-alpha (ID: {config.filter_id})")
    print(f"曝光: {config.exposure_time}秒 x {config.image_count}张")
    print(f"预计总时间: {config.get_total_hours():.1f}小时")
    if config.stop_time:
        print(f"计划停止时间: {config.stop_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"计划启动时间: {config.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)


def connect_to_acp(config, log_manager):
    """连接到ACP服务器"""
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在连接到ACP服务器...")
        client = ACPClient(config.acp_url, config.acp_user, config.acp_password)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 成功连接到ACP服务器")
        log_manager.info(f"成功连接到ACP服务器: {config.acp_url}")
        return client
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 连接失败: {e}")
        log_manager.error(f"连接ACP服务器失败: {e}", exc_info=True)
        return None


def wait_until(target_time, action_name="执行"):
    """等待到指定时间"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 等待到{action_name}时间...")
    
    while True:
        now = datetime.now()
        time_diff = (target_time - now).total_seconds()
        
        if time_diff <= 0:
            break
        
        # 每30秒显示一次倒计时
        if int(time_diff) % 30 == 0:
            hours = int(time_diff // 3600)
            minutes = int((time_diff % 3600) // 60)
            seconds = int(time_diff % 60)
            print(f"[{now.strftime('%H:%M:%S')}] 距离{action_name}还有: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        time.sleep(1)
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⏰ 到达{action_name}时间")


def stop_current_script(client, log_manager, wait_seconds=5):
    """停止当前运行的脚本"""
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在停止当前脚本...")
        success = client.stop_script()
        time.sleep(wait_seconds)
        
        if success:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 当前脚本已停止")
            log_manager.info("成功停止当前脚本")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ 停止脚本可能失败，继续执行...")
            log_manager.warning("停止脚本响应异常")
        
        return success
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 停止脚本时出错: {e}")
        log_manager.error(f"停止脚本失败: {e}", exc_info=True)
        return False


def create_imaging_plan(config):
    """创建成像计划"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在创建成像计划...")
    
    # 配置滤镜
    filters = [{
        'filter_id': config.filter_id,
        'count': config.image_count,
        'exposure': config.exposure_time,
        'binning': config.binning
    }]
    
    # 创建成像计划
    plan = ImagingPlan(
        target=config.target_name,
        ra=config.target_ra,
        dec=config.target_dec,
        filters=filters,
        dither=config.dither,
        auto_focus=config.auto_focus,
        periodic_af_interval=config.af_interval
    )
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 成像计划详情:")
    print(f"  - 目标: {config.target_name}")
    print(f"  - 坐标: {config.target_ra} / {config.target_dec}")
    print(f"  - 滤镜ID: {config.filter_id}")
    print(f"  - 曝光: {config.exposure_time}秒")
    print(f"  - 数量: {config.image_count}张")
    print(f"  - 抖动: {config.dither}像素")
    print(f"  - 自动对焦: {'是' if config.auto_focus else '否'}")
    print(f"  - 对焦间隔: {config.af_interval}分钟")
    
    return plan


def start_imaging(client, plan, config, log_manager):
    """启动成像计划"""
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在启动成像计划...")
        success = client.start_imaging_plan(plan)
        
        if success:
            estimated_finish = datetime.now() + timedelta(hours=config.get_total_hours())
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ 成像计划启动成功！")
            print(f"\n{'='*70}")
            print("任务已启动！")
            print(f"目标: {config.target_name}")
            print(f"预计完成时间: {estimated_finish.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}")
            log_manager.info(f"成功启动{config.target_name}成像计划: {config.image_count}张 x {config.exposure_time}秒")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 成像计划启动失败！")
            log_manager.error("成像计划启动失败")
        
        return success
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ 启动成像计划时出错: {e}")
        log_manager.error(f"启动成像计划失败: {e}", exc_info=True)
        return False


def main():
    """主函数"""
    # 加载配置
    config = ObservationConfig()
    
    # 初始化日志
    log_manager = LogManager('AutoObserve_NGC1499')
    
    # 打印信息横幅
    print_banner(config)
    
    # 连接到ACP服务器
    client = connect_to_acp(config, log_manager)
    if not client:
        return
    
    # 如果设置了停止时间，先等待并停止当前计划
    if config.stop_time:
        wait_until(config.stop_time, "停止")
        log_manager.info("到达停止时间，准备停止当前计划")
        stop_current_script(client, log_manager)
    
    # 等待到指定启动时间
    wait_until(config.start_time, "启动")
    log_manager.info(f"到达启动时间，开始执行{config.target_name}观测任务")
    
    # 启动前再次停止脚本（确保干净启动）
    stop_current_script(client, log_manager, wait_seconds=5)
    
    # 创建并启动成像计划
    plan = create_imaging_plan(config)
    start_imaging(client, plan, config, log_manager)
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 脚本执行完成")
    log_manager.info("自动观测脚本执行完成")


if __name__ == "__main__":
    main()
