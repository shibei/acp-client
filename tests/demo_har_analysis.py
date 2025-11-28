# 基于HAR文件分析的ACP客户端完整功能演示

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.core.acp_client import ACPClient, ImagingPlan, ObservatoryStatus

def main():
    """
    基于HAR文件分析的ACP客户端完整功能演示
    """
    print("=== 基于HAR文件分析的ACP客户端功能演示 ===\n")
    
    # 初始化客户端
    client = ACPClient.__new__(ACPClient)
    client.base_url = 'http://27056t89i6.wicp.vip:1011'
    client.user = 'test'
    client.password = 'test'
    client.timeout = 30
    
    # 演示1: 解析实际HAR文件中的状态数据
    print("1. 解析实际HAR文件中的ACP状态数据")
    print("-" * 50)
    
    # 来自HAR文件的真实状态数据
    har_status_text = """ 
_s('sm_local','@an19%3A44%3A15');_s('sm_utc','@an11%3A44%3A15');_s('sm_lst','@an22%3A14%3A36');_s('sm_obsStat','@wnOffline');_s('sm_obsOwner','@anFree');_s('sm_obsShutter','@inn/a');_s('sm_obsDome','@inn/a');_s('sm_obsWeather','@inn/a');_s('sm_obsSchHdr','No%20Scheduler');_s('sm_obsSchStat','@inn/a');_s('sm_scopeHdr','Telescope');_s('sm_scopeStat','@wnOffline');_s('sm_ha','@in---%3A--.-');_s('sm_ra','@in--%3A--%3A--.--');_s('sm_dec','@in---%B0--%27--.-%22');_s('sm_pa','@inn/a');_s('sm_az','@in---.--%B0');_s('sm_alt','@in--.--%B0');_s('sm_gem','@inn/a');_s('sm_air','@in--.---');_s('sm_camHdr','Imager');_s('sm_camStat','@wnOffline');_s('sm_imgFilt','@inn/a');_s('sm_imgBin','@in-%3A-');_s('sm_imgTemp','@inn/a');_s('sm_imgTempLabel','Cooler');_s('sm_guideStat','@wnOffline');_s('sm_guideX','@in--.--');_s('sm_guideY','@in--.--');_s('sm_guideInt','@in--.--');_s('sm_actStat','@anIdle');_s('sm_plnTitle','Plan');_s('sm_plnSet','@in-/-');_s('sm_plnTgt','@inn/a%20%28-/-%29');_s('sm_plnRpt','@in-/-');_s('sm_plnFilt','@inn/a%20%28-/-%29');_s('sm_plnCnt','@in-/-');
"""
    
    parsed_status = client.parse_encoded_status_text(har_status_text)
    
    # 显示关键状态信息
    print(f"本地时间: {parsed_status.get('sm_local', 'N/A')}")
    print(f"UTC时间: {parsed_status.get('sm_utc', 'N/A')}")
    print(f"恒星时: {parsed_status.get('sm_lst', 'N/A')}")
    print(f"观测站状态: {parsed_status.get('sm_obsStat', 'N/A')}")
    print(f"观测站所有者: {parsed_status.get('sm_obsOwner', 'N/A')}")
    print(f"望远镜状态: {parsed_status.get('sm_scopeStat', 'N/A')}")
    print(f"相机状态: {parsed_status.get('sm_camStat', 'N/A')}")
    print(f"导星状态: {parsed_status.get('sm_guideStat', 'N/A')}")
    print(f"活动状态: {parsed_status.get('sm_actStat', 'N/A')}")
    print(f"当前坐标: RA {parsed_status.get('sm_ra', 'N/A')}, Dec {parsed_status.get('sm_dec', 'N/A')}")
    print(f"当前高度/方位: Alt {parsed_status.get('sm_alt', 'N/A')}, Az {parsed_status.get('sm_az', 'N/A')}")
    print(f"当前滤镜: {parsed_status.get('sm_imgFilt', 'N/A')}")
    print(f"计划进度: {parsed_status.get('sm_plnSet', 'N/A')} - {parsed_status.get('sm_plnTgt', 'N/A')}")
    
    # 演示2: 创建基于HAR文件参数的成像计划
    print("\n2. 创建基于HAR文件参数的M31成像计划")
    print("-" * 50)
    
    # 使用HAR文件中的实际参数
    m31_plan = ImagingPlan(
        target='m 31',  # HAR文件中的目标名称
        ra='00:42:42.12',  # HAR文件中的RA
        dec='41:16:01.2',  # HAR文件中的Dec
        filters=[
            {'filter': 0, 'count': 10, 'exposure': 600, 'binning': 1},  # Luminance
            {'filter': 1, 'count': 6, 'exposure': 600, 'binning': 1},   # Red
            {'filter': 2, 'count': 6, 'exposure': 600, 'binning': 1},  # Green
            {'filter': 3, 'count': 6, 'exposure': 600, 'binning': 1}   # Blue
        ],
        exposure_time=600,  # HAR文件中的曝光时间
        dither=5,  # HAR文件中的抖动参数
        auto_focus=True,  # 启用自动对焦
        periodic_af_interval=120  # 周期性自动对焦间隔
    )
    
    print(f"目标: {m31_plan.target}")
    print(f"坐标: RA {m31_plan.ra}, Dec {m31_plan.dec}")
    print(f"总滤镜配置: {len(m31_plan.filters)} 个")
    print(f"自动对焦: {'启用' if m31_plan.auto_focus else '禁用'}")
    print(f"抖动: {m31_plan.dither}")
    print(f"周期性AF间隔: {m31_plan.periodic_af_interval} 秒")
    
    # 显示滤镜配置详情
    for i, filt_config in enumerate(m31_plan.filters, 1):
        print(f"  滤镜{i}: 滤镜{filt_config['filter']} - {filt_config['count']}张 x {filt_config['exposure']}秒 (binning: {filt_config['binning']})")
    
    # 演示3: 构建完整的表单数据
    print("\n3. 构建完整的ACP表单数据")
    print("-" * 50)
    
    form_data = client._build_imaging_form_data(m31_plan)
    
    print(f"总表单字段数: {len(form_data)}")
    print("\n关键表单字段:")
    print(f"  Target: {form_data.get('Target')}")
    print(f"  RA: {form_data.get('RA')}")
    print(f"  Dec: {form_data.get('Dec')}")
    print(f"  可见性检查: {form_data.get('visOnly')}")
    print(f"  轨道检查: {form_data.get('isOrb')}")
    print(f"  自动对焦: {form_data.get('AF')}")
    print(f"  周期性AF: {form_data.get('PerAF')} (间隔: {form_data.get('PerAFInt')}秒)")
    print(f"  抖动: {form_data.get('Dither')}")
    
    # 显示滤镜配置
    print("\n滤镜配置:")
    for i in range(1, len(m31_plan.filters) + 1):
        use = form_data.get(f'ColorUse{i}')
        filt = form_data.get(f'ColorFilter{i}')
        count = form_data.get(f'ColorCount{i}')
        exp = form_data.get(f'ColorExposure{i}')
        binning = form_data.get(f'ColorBinning{i}')
        print(f"  滤镜{i}: {use} - 滤镜{filt} - {count}张 x {exp}秒 (binning: {binning})")
    
    # 演示4: 解析警告信息
    print("\n4. 解析ACP警告信息")
    print("-" * 50)
    
    warning_text = """ 

----
[lba warning]The observatory is offline
----
"""
    
    warnings = client.get_observatory_warnings(warning_text)
    
    if warnings:
        print("检测到警告:")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print("未检测到警告")
    
    # 演示5: 获取状态摘要
    print("\n5. 获取天文台状态摘要")
    print("-" * 50)
    
    # 创建一个模拟状态对象
    mock_status = ObservatoryStatus(
        observatory_status='离线',
        telescope_status='离线',
        camera_status='离线',
        guider_status='离线',
        current_ra='00:42:42.12',
        current_dec='41:16:01.2',
        current_alt='--.--°',
        current_az='--.--°',
        image_filter='n/a',
        plan_progress='0/0',
        last_fwhm='N/A'
    )
    
    # 模拟get_system_status返回这个状态
    def mock_get_system_status():
        return mock_status
    
    client.get_system_status = mock_get_system_status
    
    summary = client.get_current_status_summary()
    print(summary)
    
    print("\n=== 演示完成 ===")
    print("\n基于HAR文件分析，ACP客户端现在支持:")
    print("[OK] 完整的ACP编码状态解析")
    print("[OK] 多滤镜成像计划创建（支持最多16个滤镜）")
    print("[OK] 复杂的表单数据构建")
    print("[OK] 警告信息提取")
    print("[OK] 自动对焦和抖动控制")
    print("[OK] 状态摘要生成")
    print("\n这些功能完全基于HAR文件中的实际数据实现！")

if __name__ == "__main__":
    main()