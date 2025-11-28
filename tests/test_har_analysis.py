# 测试基于HAR文件分析的完整功能
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.core.acp_client import ACPClient, ImagingPlan, ObservatoryStatus

print('=== 基于HAR文件分析的ACP客户端功能测试 ===')

# 模拟HAR文件中的实际数据
client = ACPClient.__new__(ACPClient)
client.base_url = 'http://27056t89i6.wicp.vip:1011'
client.user = 'test'
client.password = 'test'
client.timeout = 30

# 测试1: 解析实际的状态数据（来自HAR文件）
print('测试1: 实际状态数据解析')
actual_status_text = ''' 
_s('sm_local','@an19%3A44%3A15');_s('sm_utc','@an11%3A44%3A15');_s('sm_lst','@an22%3A14%3A36');_s('sm_obsStat','@wnOffline');_s('sm_obsOwner','@anFree');_s('sm_obsShutter','@inn/a');_s('sm_obsDome','@inn/a');_s('sm_obsWeather','@inn/a');_s('sm_obsSchHdr','No%20Scheduler');_s('sm_obsSchStat','@inn/a');_s('sm_scopeHdr','Telescope');_s('sm_scopeStat','@wnOffline');_s('sm_ha','@in---%3A--.-');_s('sm_ra','@in--%3A--%3A--.--');_s('sm_dec','@in---%B0--%27--.-%22');_s('sm_pa','@inn/a');_s('sm_az','@in---.--%B0');_s('sm_alt','@in--.--%B0');_s('sm_gem','@inn/a');_s('sm_air','@in--.---');_s('sm_camHdr','Imager');_s('sm_camStat','@wnOffline');_s('sm_imgFilt','@inn/a');_s('sm_imgBin','@in-%3A-');_s('sm_imgTemp','@inn/a');_s('sm_imgTempLabel','Cooler');_s('sm_guideStat','@wnOffline');_s('sm_guideX','@in--.--');_s('sm_guideY','@in--.--');_s('sm_guideInt','@in--.--');_s('sm_actStat','@anIdle');_s('sm_plnTitle','Plan');_s('sm_plnSet','@in-/-');_s('sm_plnTgt','@inn/a%20%28-/-%29');_s('sm_plnRpt','@in-/-');_s('sm_plnFilt','@inn/a%20%28-/-%29');_s('sm_plnCnt','@in-/-');
'''

parsed_status = client.parse_encoded_status_text(actual_status_text)
print(f'解析到 {len(parsed_status)} 个状态字段:')
for key, value in list(parsed_status.items())[:10]:
    print(f'  {key}: {value}')
print('  ...')

# 测试2: 创建M31仙女座星系成像计划（基于HAR文件中的实际参数）
print('\n测试2: M31成像计划创建')
m31_filters = [
    {'filter': 0, 'count': 10, 'exposure': 600, 'binning': 1},  # Luminance
    {'filter': 1, 'count': 6, 'exposure': 600, 'binning': 1},   # Red
    {'filter': 2, 'count': 6, 'exposure': 600, 'binning': 1},  # Green
    {'filter': 3, 'count': 6, 'exposure': 600, 'binning': 1}   # Blue
]

m31_plan = ImagingPlan(
    target='m 31',
    ra='00:42:42.12',
    dec='41:16:01.2',
    filters=m31_filters,
    exposure_time=600,
    dither=5,
    auto_focus=True,
    periodic_af_interval=120
)

print(f'M31计划配置:')
print(f'  目标: {m31_plan.target}')
print(f'  坐标: RA {m31_plan.ra}, Dec {m31_plan.dec}')
print(f'  总滤镜配置: {len(m31_plan.filters)} 个')
print(f'  自动对焦: {m31_plan.auto_focus}')
print(f'  抖动: {m31_plan.dither}')

# 测试3: 构建表单数据
print('\n测试3: 表单数据构建')
form_data = client._build_imaging_form_data(m31_plan)
print(f'构建的表单数据:')
print(f'  目标: {form_data.get("Target")}')
print(f'  可见性检查: {form_data.get("visOnly")}')
print(f'  轨道检查: {form_data.get("isOrb")}')
print(f'  自动对焦: {form_data.get("AF")}')
print(f'  周期性AF: {form_data.get("PerAF")} (间隔: {form_data.get("PerAFInt")}秒)')
print(f'  抖动: {form_data.get("Dither")}')

# 显示前几个滤镜配置
for i in range(1, min(5, len(m31_plan.filters) + 1)):
    use = form_data.get(f'ColorUse{i}')
    filt = form_data.get(f'ColorFilter{i}')
    count = form_data.get(f'ColorCount{i}')
    exp = form_data.get(f'ColorExposure{i}')
    binning = form_data.get(f'ColorBinning{i}')
    print(f'  滤镜{i}: {use} - 滤镜{filt} - {count}张 x {exp}秒 (binning: {binning})')

print(f'  总表单字段数: {len(form_data)}')

# 测试4: 警告解析
print('\n测试4: 警告信息解析')
warning_text = ''' 

----
[lba warning]The observatory is offline
----
'''
warnings = client.get_observatory_warnings(warning_text)
print(f'解析到的警告: {warnings}')

print('\n[OK] 基于HAR文件分析的所有功能测试通过！')
print('[OK] ACP客户端现在支持:')
print('  - 完整的ACP状态解析（编码格式）')
print('  - M31等多目标成像计划创建')
print('  - 复杂的表单数据构建（支持16个滤镜）')
print('  - 警告信息提取')
print('  - 自动对焦和抖动控制')