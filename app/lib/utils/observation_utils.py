"""
观测工具模块
包含观测相关的工具函数和类
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple


class ObservationUtils:
    """观测工具类"""
    
    @staticmethod
    def parse_ra_dec(ra_str: str, dec_str: str) -> Tuple[float, float]:
        """解析RA和DEC坐标字符串为度数
        
        Args:
            ra_str: RA坐标字符串 (格式: HH:MM:SS 或 HH MM SS)
            dec_str: DEC坐标字符串 (格式: DD:MM:SS 或 DD MM SS)
            
        Returns:
            (ra_degrees, dec_degrees) 元组
        """
        # 解析RA
        ra_parts = ra_str.replace(':', ' ').split()
        if len(ra_parts) != 3:
            raise ValueError(f"无效的RA格式: {ra_str}")
        
        ra_hours = float(ra_parts[0])
        ra_minutes = float(ra_parts[1])
        ra_seconds = float(ra_parts[2])
        
        ra_degrees = (ra_hours + ra_minutes/60 + ra_seconds/3600) * 15
        
        # 解析DEC
        dec_parts = dec_str.replace(':', ' ').split()
        if len(dec_parts) != 3:
            raise ValueError(f"无效的DEC格式: {dec_str}")
        
        dec_deg = float(dec_parts[0])
        dec_min = float(dec_parts[1])
        dec_sec = float(dec_parts[2])
        
        # 处理符号
        sign = 1 if dec_deg >= 0 else -1
        dec_degrees = sign * (abs(dec_deg) + dec_min/60 + dec_sec/3600)
        
        return ra_degrees, dec_degrees
    
    @staticmethod
    def format_ra_dec(ra_deg: float, dec_deg: float) -> Tuple[str, str]:
        """将度数格式化为RA和DEC字符串
        
        Args:
            ra_deg: RA度数
            dec_deg: DEC度数
            
        Returns:
            (ra_str, dec_str) 元组
        """
        # 格式化RA
        ra_hours = ra_deg / 15
        ra_h = int(ra_hours)
        ra_m = int((ra_hours - ra_h) * 60)
        ra_s = ((ra_hours - ra_h) * 60 - ra_m) * 60
        
        ra_str = f"{ra_h:02d}:{ra_m:02d}:{ra_s:05.2f}"
        
        # 格式化DEC
        sign = '+' if dec_deg >= 0 else '-'
        dec_abs = abs(dec_deg)
        dec_d = int(dec_abs)
        dec_m = int((dec_abs - dec_d) * 60)
        dec_s = ((dec_abs - dec_d) * 60 - dec_m) * 60
        
        dec_str = f"{sign}{dec_d:02d}:{dec_m:02d}:{dec_s:05.2f}"
        
        return ra_str, dec_str
    
    @staticmethod
    def calculate_airmass(altitude_deg: float) -> float:
        """计算大气质量
        
        Args:
            altitude_deg: 高度角（度）
            
        Returns:
            大气质量
        """
        if altitude_deg <= 0:
            return 99.0
        
        altitude_rad = math.radians(altitude_deg)
        return 1.0 / math.sin(altitude_rad)
    
    @staticmethod
    def calculate_altitude_azimuth(ra_deg: float, dec_deg: float, 
                                 lst_hours: float, latitude_deg: float) -> Tuple[float, float]:
        """计算高度角和方位角
        
        Args:
            ra_deg: RA度数
            dec_deg: DEC度数
            lst_hours: 本地恒星时（小时）
            latitude_deg: 观测站纬度（度）
            
        Returns:
            (altitude_deg, azimuth_deg) 元组
        """
        # 转换为弧度
        ra_rad = math.radians(ra_deg)
        dec_rad = math.radians(dec_deg)
        lst_rad = math.radians(lst_hours * 15)  # LST转为度数再转弧度
        lat_rad = math.radians(latitude_deg)
        
        # 计算时角
        ha_rad = lst_rad - ra_rad
        
        # 计算高度角
        sin_alt = (math.sin(dec_rad) * math.sin(lat_rad) + 
                  math.cos(dec_rad) * math.cos(lat_rad) * math.cos(ha_rad))
        altitude_rad = math.asin(sin_alt)
        altitude_deg = math.degrees(altitude_rad)
        
        # 计算方位角
        cos_az = (math.sin(dec_rad) - math.sin(altitude_rad) * math.sin(lat_rad)) / (math.cos(altitude_rad) * math.cos(lat_rad))
        azimuth_rad = math.acos(max(-1, min(1, cos_az)))  # 限制在有效范围内
        
        # 判断方位角方向
        if math.sin(ha_rad) >= 0:
            azimuth_deg = math.degrees(azimuth_rad)
        else:
            azimuth_deg = 360 - math.degrees(azimuth_rad)
        
        return altitude_deg, azimuth_deg
    
    @staticmethod
    def calculate_lst(longitude_deg: float, utc_time: Optional[datetime] = None) -> float:
        """计算本地恒星时（LST）
        
        Args:
            longitude_deg: 观测站经度（度，东经为正）
            utc_time: UTC时间（默认为当前时间）
            
        Returns:
            本地恒星时（小时，0-24）
        """
        if utc_time is None:
            utc_time = datetime.utcnow()
        
        # 简化的LST计算（实际需要更精确的公式）
        # 这里使用近似公式
        jd = ObservationUtils._datetime_to_julian(utc_time)
        
        # 格林威治恒星时（GST）
        t = (jd - 2451545.0) / 36525.0
        gst = 6.697374558 + 2400.051336 * t + 0.000025862 * t * t
        gst = gst % 24
        if gst < 0:
            gst += 24
        
        # 本地恒星时
        lst = gst + longitude_deg / 15.0
        lst = lst % 24
        if lst < 0:
            lst += 24
        
        return lst
    
    @staticmethod
    def _datetime_to_julian(dt: datetime) -> float:
        """将datetime转换为儒略日
        
        Args:
            dt: datetime对象
            
        Returns:
            儒略日
        """
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        
        jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        
        # 添加时间部分
        jd += (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
        
        return jd
    
    @staticmethod
    def is_observable(ra_deg: float, dec_deg: float, latitude_deg: float, 
                     min_altitude: float = 30.0, max_airmass: float = 2.0) -> Dict[str, Any]:
        """检查目标是否可观测
        
        Args:
            ra_deg: RA度数
            dec_deg: DEC度数
            latitude_deg: 观测站纬度
            min_altitude: 最小高度角（度）
            max_airmass: 最大大气质量
            
        Returns:
            可观测性信息字典
        """
        # 计算当前LST
        lst = ObservationUtils.calculate_lst(latitude_deg)
        
        # 计算高度角和方位角
        altitude, azimuth = ObservationUtils.calculate_altitude_azimuth(ra_deg, dec_deg, lst, latitude_deg)
        
        # 计算大气质量
        airmass = ObservationUtils.calculate_airmass(altitude)
        
        # 判断可观测性
        is_observable = altitude >= min_altitude and airmass <= max_airmass
        
        return {
            'is_observable': is_observable,
            'altitude': altitude,
            'azimuth': azimuth,
            'airmass': airmass,
            'reason': '可观测' if is_observable else f"高度角{altitude:.1f}°太低或大气质量{airmass:.1f}太高"
        }
    
    @staticmethod
    def calculate_observation_plan(targets: List[Dict[str, Any]], 
                                 latitude_deg: float,
                                 min_altitude: float = 30.0) -> List[Dict[str, Any]]:
        """计算观测计划（简化版）
        
        Args:
            targets: 目标列表
            latitude_deg: 观测站纬度
            min_altitude: 最小高度角
            
        Returns:
            带可观测性信息的目标列表
        """
        results = []
        
        for target in targets:
            # 解析坐标
            try:
                ra_deg, dec_deg = ObservationUtils.parse_ra_dec(target['ra'], target['dec'])
            except ValueError:
                results.append({
                    **target,
                    'observability': {
                        'is_observable': False,
                        'reason': '坐标格式错误'
                    }
                })
                continue
            
            # 检查可观测性
            observability = ObservationUtils.is_observable(ra_deg, dec_deg, latitude_deg, min_altitude)
            
            results.append({
                **target,
                'observability': observability
            })
        
        return results