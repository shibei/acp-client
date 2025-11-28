"""
中天反转管理器
负责计算中天时间并在中天前后自动停止/恢复观测
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import math
import time
from datetime import datetime, timedelta
from ACP import LogManager


class MeridianFlipManager:
    """中天反转管理器"""
    
    def __init__(self, dryrun=False):
        """初始化中天反转管理器
        
        Args:
            dryrun: 是否启用DRYRUN模式
        """
        self.dryrun = dryrun
        self.log_manager = LogManager('MeridianFlip')
        
        # 中天反转参数
        self.stop_minutes_before = 10  # 中天前多少分钟停止观测
        self.resume_minutes_after = 10  # 中天后多少分钟恢复观测
        self.safety_margin = 2  # 额外安全时间（分钟）
        
        # 观测站参数（默认值，可以从配置文件读取）
        self.observatory_latitude = 39.9  # 北京纬度（度）
        self.observatory_longitude = 116.4  # 北京经度（度）
        
    def set_observatory_location(self, latitude: float, longitude: float):
        """设置观测站位置
        
        Args:
            latitude: 纬度（度）
            longitude: 经度（度）
        """
        self.observatory_latitude = latitude
        self.observatory_longitude = longitude
        
    def calculate_meridian_time(self, ra: str, dec: str, observation_date: datetime) -> datetime:
        """计算目标的中天时间
        
        Args:
            ra: 赤经（字符串格式，如 "04:01:07.51"）
            dec: 赤纬（字符串格式，如 "+36:31:11.9"）
            observation_date: 观测日期
            
        Returns:
            中天时间（本地时间）
        """
        try:
            # 解析赤经赤纬
            ra_hours = self._parse_ra(ra)
            dec_degrees = self._parse_dec(dec)
            
            # 计算本地恒星时（LST）
            lst = self._calculate_lst(observation_date)
            
            # 计算中天时间
            # 中天时，LST = RA
            meridian_lst = ra_hours
            
            # 计算当前LST与中天LST的时间差
            current_lst_hours = lst
            delta_lst = meridian_lst - current_lst_hours
            
            # 调整到-12到+12小时范围内
            if delta_lst > 12:
                delta_lst -= 24
            elif delta_lst < -12:
                delta_lst += 24
            
            # 计算中天时间
            meridian_time = observation_date + timedelta(hours=delta_lst)
            
            # 确保是今天的中天时间
            if meridian_time.date() < observation_date.date():
                meridian_time += timedelta(days=1)
            elif meridian_time.date() > observation_date.date():
                meridian_time -= timedelta(days=1)
            
            return meridian_time
            
        except Exception as e:
            self.log_manager.error(f"计算中天时间失败: {str(e)}")
            return None
    
    def calculate_meridian_flip_window(self, ra: str, dec: str, observation_date: datetime) -> dict:
        """计算中天反转时间窗口
        
        Args:
            ra: 赤经（字符串格式）
            dec: 赤纬（字符串格式）
            observation_date: 观测日期
            
        Returns:
            字典，包含停止时间、中天时间、恢复时间
        """
        meridian_time = self.calculate_meridian_time(ra, dec, observation_date)
        
        if not meridian_time:
            return None
        
        # 计算停止和恢复时间
        stop_time = meridian_time - timedelta(minutes=self.stop_minutes_before + self.safety_margin)
        resume_time = meridian_time + timedelta(minutes=self.resume_minutes_after + self.safety_margin)
        
        return {
            'stop_time': stop_time,
            'meridian_time': meridian_time,
            'resume_time': resume_time,
            'stop_minutes_before': self.stop_minutes_before,
            'resume_minutes_after': self.resume_minutes_after
        }
    
    def check_meridian_flip_needed(self, ra: str, dec: str, current_time: datetime) -> dict:
        """检查是否需要中天反转等待
        
        Args:
            ra: 赤经（字符串格式）
            dec: 赤纬（字符串格式）
            current_time: 当前时间
            
        Returns:
            字典，包含状态信息和等待时间
        """
        flip_window = self.calculate_meridian_flip_window(ra, dec, current_time)
        
        if not flip_window:
            return {
                'status': 'error',
                'message': '无法计算中天时间',
                'wait_needed': False
            }
        
        stop_time = flip_window['stop_time']
        resume_time = flip_window['resume_time']
        meridian_time = flip_window['meridian_time']
        
        # 检查当前时间状态
        if current_time < stop_time:
            # 在中天窗口之前，可以正常观测
            time_until_stop = (stop_time - current_time).total_seconds() / 60
            return {
                'status': 'before_window',
                'message': f'距离中天停止还有 {time_until_stop:.1f} 分钟',
                'wait_needed': False,
                'stop_time': stop_time,
                'meridian_time': meridian_time,
                'resume_time': resume_time,
                'time_until_stop': time_until_stop
            }
        
        elif stop_time <= current_time < meridian_time:
            # 在中天停止期间
            time_until_meridian = (meridian_time - current_time).total_seconds() / 60
            return {
                'status': 'stop_before_meridian',
                'message': f'中天前停止期，中天还有 {time_until_meridian:.1f} 分钟',
                'wait_needed': True,
                'wait_until': meridian_time,
                'stop_time': stop_time,
                'meridian_time': meridian_time,
                'resume_time': resume_time,
                'time_until_meridian': time_until_meridian
            }
        
        elif meridian_time <= current_time < resume_time:
            # 在中天恢复期间
            time_after_meridian = (current_time - meridian_time).total_seconds() / 60
            time_until_resume = (resume_time - current_time).total_seconds() / 60
            return {
                'status': 'wait_after_meridian',
                'message': f'中天后等待期，已中天 {time_after_meridian:.1f} 分钟，还需等待 {time_until_resume:.1f} 分钟',
                'wait_needed': True,
                'wait_until': resume_time,
                'stop_time': stop_time,
                'meridian_time': meridian_time,
                'resume_time': resume_time,
                'time_until_resume': time_until_resume
            }
        
        else:
            # 中天窗口已过，可以恢复观测
            time_after_resume = (current_time - resume_time).total_seconds() / 60
            return {
                'status': 'after_window',
                'message': f'中天窗口已过 {time_after_resume:.1f} 分钟，可以恢复观测',
                'wait_needed': False,
                'stop_time': stop_time,
                'meridian_time': meridian_time,
                'resume_time': resume_time,
                'time_after_resume': time_after_resume
            }
    
    def wait_for_meridian_flip(self, ra: str, dec: str, current_time: datetime) -> bool:
        """等待中天反转完成
        
        Args:
            ra: 赤经（字符串格式）
            dec: 赤纬（字符串格式）
            current_time: 当前时间
            
        Returns:
            True: 等待完成，可以继续观测
            False: 等待被中断
        """
        flip_info = self.check_meridian_flip_needed(ra, dec, current_time)
        
        if not flip_info['wait_needed']:
            return True
        
        wait_until = flip_info['wait_until']
        status = flip_info['status']
        
        if status == 'stop_before_meridian':
            print(f"\n[{current_time.strftime('%H:%M:%S')}] 🌟 中天反转等待")
            print(f"  目标将在 {flip_info['meridian_time'].strftime('%H:%M:%S')} 中天")
            print(f"  将在 {wait_until.strftime('%H:%M:%S')} 后继续观测")
            print(f"  预计等待时间: {flip_info['time_until_meridian']:.1f} 分钟")
            
            self.log_manager.info(f"中天前停止，等待中天反转，预计等待 {flip_info['time_until_meridian']:.1f} 分钟")
            
        elif status == 'wait_after_meridian':
            print(f"\n[{current_time.strftime('%H:%M:%S')}] 🌟 中天后恢复等待")
            print(f"  中天时间: {flip_info['meridian_time'].strftime('%H:%M:%S')}")
            print(f"  将在 {wait_until.strftime('%H:%M:%S')} 后恢复观测")
            print(f"  还需等待: {flip_info['time_until_resume']:.1f} 分钟")
            
            self.log_manager.info(f"中天后等待，还需等待 {flip_info['time_until_resume']:.1f} 分钟")
        
        # 执行等待
        if self.dryrun:
            print(f"  [DRYRUN] 模拟等待中天反转...")
            time.sleep(2)  # 模拟等待
            return True
        
        try:
            while datetime.now() < wait_until:
                remaining = (wait_until - datetime.now()).total_seconds() / 60
                print(f"\r  剩余等待时间: {remaining:.1f} 分钟", end='', flush=True)
                time.sleep(30)  # 每30秒更新一次
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✅ 中天反转等待完成")
            self.log_manager.info("中天反转等待完成")
            return True
            
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ❌ 中天反转等待被中断")
            self.log_manager.warning("中天反转等待被用户中断")
            return False
    
    def _parse_ra(self, ra_str: str) -> float:
        """解析赤经字符串为小时数
        
        Args:
            ra_str: 赤经字符串（如 "04:01:07.51"）
            
        Returns:
            赤经小时数
        """
        parts = ra_str.split(':')
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        
        return hours + minutes/60 + seconds/3600
    
    def _parse_dec(self, dec_str: str) -> float:
        """解析赤纬字符串为度数
        
        Args:
            dec_str: 赤纬字符串（如 "+36:31:11.9"）
            
        Returns:
            赤纬度数
        """
        sign = 1 if dec_str.startswith('+') else -1
        parts = dec_str[1:].split(':')
        degrees = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        
        return sign * (degrees + minutes/60 + seconds/3600)
    
    def _calculate_lst(self, observation_time: datetime) -> float:
        """计算本地恒星时（LST）
        
        Args:
            observation_time: 观测时间
            
        Returns:
            本地恒星时（小时）
        """
        # 简化的LST计算（实际应用中可能需要更精确的算法）
        # 这里使用近似公式
        
        # 计算儒略日
        jd = self._calculate_julian_day(observation_time)
        
        # 计算格林尼治恒星时（GST）
        t = (jd - 2451545.0) / 36525.0
        gst = 6.697374558 + 2400.051336 * t + 0.000025862 * t * t
        gst = gst % 24
        
        # 转换为本地恒星时
        longitude_hours = self.observatory_longitude / 15.0
        lst = gst + longitude_hours
        lst = lst % 24
        
        return lst
    
    def _calculate_julian_day(self, date: datetime) -> float:
        """计算儒略日
        
        Args:
            date: 日期时间
            
        Returns:
            儒略日
        """
        a = (14 - date.month) // 12
        y = date.year + 4800 - a
        m = date.month + 12 * a - 3
        
        jd = date.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        
        # 加上时间部分
        jd += (date.hour + date.minute / 60.0 + date.second / 3600.0) / 24.0
        
        return jd