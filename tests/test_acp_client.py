#!/usr/bin/env python3
"""
测试ACP客户端功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.lib.core.acp_client import ACPClient, ImagingPlan, ObservatoryStatus

def test_acp_client():
    """测试ACP客户端功能"""
    print('=== 测试ACP客户端功能 ===')
    
    # 创建客户端实例（不测试连接）
    client = ACPClient.__new__(ACPClient)
    client.base_url = 'http://test.com'
    client.user = 'test'
    client.password = 'test'
    client.timeout = 30
    
    # 测试状态解析
    status_text = """
_s('sm_local','@an19%3A44%3A15');_s('sm_utc','@an11%3A44%3A15');_s('sm_lst','@an22%3A14%3A36');_s('sm_obsStat','@wnOffline');_s('sm_obsOwner','@anFree');_s('sm_scopeStat','@wnOffline');_s('sm_camStat','@wnOffline');
"""
    
    parsed_status = client.parse_encoded_status_text(status_text)
    print('状态解析测试成功:')
    for key, value in parsed_status.items():
        print(f'  {key}: {value}')
    
    # 测试成像计划创建
    filter_configs = [
        {'filter': 0, 'count': 10, 'exposure': 600, 'binning': 1},
        {'filter': 1, 'count': 6, 'exposure': 600, 'binning': 1},
        {'filter': 2, 'count': 6, 'exposure': 600, 'binning': 1}
    ]
    
    plan = ImagingPlan(
        target='m 31',
        ra='00:42:42.12',
        dec='41:16:01.2',
        filters=filter_configs,
        exposure_time=600,
        dither=5,
        auto_focus=True
    )
    
    print(f'\n成像计划创建成功:')
    print(f'  目标: {plan.target}')
    print(f'  坐标: RA {plan.ra}, Dec {plan.dec}')
    print(f'  曝光时间: {plan.exposure_time}秒')
    print(f'  抖动: {plan.dither}')
    print(f'  滤镜配置: {len(plan.filters)} 个滤镜')
    
    # 测试表单数据构建
    form_data = client._build_imaging_form_data(plan)
    print('\n表单数据构建成功:')
    print(f'  目标: {form_data.get("Target")}')
    print(f'  RA: {form_data.get("RA")}')
    print(f'  Dec: {form_data.get("Dec")}')
    print(f'  滤镜1: {form_data.get("ColorUse1")} - {form_data.get("ColorFilter1")} - {form_data.get("ColorCount1")}张')
    print(f'  滤镜2: {form_data.get("ColorUse2")} - {form_data.get("ColorFilter2")} - {form_data.get("ColorCount2")}张')
    print(f'  ... 总共 {len(form_data)} 个字段')
    
    print('\n所有功能测试通过！')

if __name__ == '__main__':
    test_acp_client()