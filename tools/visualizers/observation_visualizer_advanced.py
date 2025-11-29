#!/usr/bin/env python3
"""
高级观测队列可视化工具
根据配置文件生成观测计划的mermaid甘特图，支持更多自定义选项
"""

import sys
import os
import yaml
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import colorsys
import webbrowser


@dataclass
class FilterConfig:
    """滤镜配置"""
    filter_id: int
    name: str
    exposure: int  # 秒
    count: int
    binning: int


@dataclass
class TargetConfig:
    """目标配置"""
    name: str
    ra: str
    dec: str
    start_time: datetime
    priority: int
    filters: List[FilterConfig]


@dataclass
class MeridianFlipConfig:
    """中天反转配置"""
    stop_minutes_before: int
    resume_minutes_after: int
    safety_margin: int


@dataclass
class ObservatoryConfig:
    """观测站配置"""
    latitude: float
    longitude: float


@dataclass
class GlobalSettings:
    """全局设置"""
    dither: int
    auto_focus: bool
    af_interval: int
    dryrun: bool


class ColorPalette:
    """颜色调色板"""
    
    FILTER_COLORS = {
        'L': '#FFD700',    # 金色
        'R': '#FF6B6B',    # 红色
        'G': '#4ECDC4',    # 绿色
        'B': '#45B7D1',    # 蓝色
        'H-alpha': '#FF4757',  # 深红色
        'Halpha': '#FF4757',   # 深红色
        'OIII': '#32CD32',     # 鲜绿色
        'O-III': '#32CD32',    # 鲜绿色
        'SII': '#8A2BE2',      # 紫色
        'S-II': '#8A2BE2',     # 紫色
        'U': '#9B59B6',        # 紫色
        'V': '#3498DB',        # 蓝色
        'Ha': '#FF4757',       # 深红色
        'H-a': '#FF4757',      # 深红色
    }
    
    @staticmethod
    def get_filter_color(filter_name: str) -> str:
        """获取滤镜对应的颜色"""
        return ColorPalette.FILTER_COLORS.get(filter_name, '#95A5A6')
    
    @staticmethod
    def get_priority_color(priority: int) -> str:
        """根据优先级获取颜色"""
        colors = ['#E74C3C', '#F39C12', '#F1C40F', '#2ECC71', '#3498DB']
        return colors[min(priority - 1, len(colors) - 1)]
    
    @staticmethod
    def generate_target_colors(count: int) -> List[str]:
        """为目标生成不同的颜色"""
        colors = []
        for i in range(count):
            hue = i / count
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.8)
            hex_color = '#{:02X}{:02X}{:02X}'.format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )
            colors.append(hex_color)
        return colors


class ObservationScheduleVisualizer:
    """观测计划可视化器"""
    
    def __init__(self):
        self.targets: List[TargetConfig] = []
        self.meridian_config: Optional[MeridianFlipConfig] = None
        self.observatory_config: Optional[ObservatoryConfig] = None
        self.global_settings: Optional[GlobalSettings] = None
        self.global_stop_time: Optional[datetime] = None
        
    def load_config(self, config_file: str) -> bool:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 解析目标配置
            if 'targets' in config_data:
                for target_data in config_data['targets']:
                    target = self._parse_target(target_data)
                    if target:
                        self.targets.append(target)
            
            # 按开始时间排序
            self.targets.sort(key=lambda x: x.start_time)
            
            # 解析全局停止时间（在targets之后）
            if 'schedule' in config_data and 'global_stop_time' in config_data['schedule']:
                stop_time_str = config_data['schedule']['global_stop_time']
                # 根据第一个目标的日期来确定停止日期
                if self.targets:
                    first_target_date = self.targets[0].start_time.date()
                    # 如果停止时间小于开始时间，说明是第二天
                    stop_time = datetime.strptime(stop_time_str, '%H:%M').time()
                    if stop_time < self.targets[0].start_time.time():
                        # 停止时间是第二天
                        stop_date = first_target_date + timedelta(days=1)
                    else:
                        stop_date = first_target_date
                    
                    self.global_stop_time = datetime.combine(stop_date, stop_time)
            
            # 解析中天反转配置
            if 'meridian_flip' in config_data:
                mf = config_data['meridian_flip']
                self.meridian_config = MeridianFlipConfig(
                    stop_minutes_before=mf.get('stop_minutes_before', 10),
                    resume_minutes_after=mf.get('resume_minutes_after', 10),
                    safety_margin=mf.get('safety_margin', 2)
                )
            
            # 解析观测站配置
            if 'obervatory' in config_data:  # 注意配置文件中的拼写
                obs = config_data['obervatory']
                self.observatory_config = ObservatoryConfig(
                    latitude=obs.get('latitude', 39.9),
                    longitude=obs.get('longitude', 116.4)
                )
            elif 'observatory' in config_data:  # 正确的拼写
                obs = config_data['observatory']
                self.observatory_config = ObservatoryConfig(
                    latitude=obs.get('latitude', 39.9),
                    longitude=obs.get('longitude', 116.4)
                )
            
            # 解析全局设置
            if 'global_settings' in config_data:
                gs = config_data['global_settings']
                self.global_settings = GlobalSettings(
                    dither=gs.get('dither', 5),
                    auto_focus=gs.get('auto_focus', True),
                    af_interval=gs.get('af_interval', 120),
                    dryrun=gs.get('dryrun', False)
                )
            
            print(f"成功加载配置文件: {config_file}")
            print(f"找到 {len(self.targets)} 个观测目标")
            return True
            
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return False
    
    def _parse_target(self, target_data: Dict[str, Any]) -> Optional[TargetConfig]:
        """解析单个目标配置"""
        try:
            name = target_data.get('name', 'Unknown')
            ra = target_data.get('ra', '00:00:00')
            dec = target_data.get('dec', '+00:00:00')
            start_time_str = target_data.get('start_time')
            priority = target_data.get('priority', 1)
            
            if not start_time_str:
                print(f"目标 {name} 缺少开始时间，跳过")
                return None
            
            # 解析开始时间
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            
            # 解析滤镜配置
            filters = []
            for filter_data in target_data.get('filters', []):
                filter_config = FilterConfig(
                    filter_id=filter_data.get('filter_id', 0),
                    name=filter_data.get('name', f"Filter_{filter_data.get('filter_id', 0)}"),
                    exposure=filter_data.get('exposure', 1),
                    count=filter_data.get('count', 1),
                    binning=filter_data.get('binning', 1)
                )
                filters.append(filter_config)
            
            return TargetConfig(
                name=name,
                ra=ra,
                dec=dec,
                start_time=start_time,
                priority=priority,
                filters=filters
            )
            
        except Exception as e:
            print(f"解析目标配置失败: {e}")
            return None
    
    def calculate_observation_times(self) -> List[Dict[str, Any]]:
        """计算每个目标的观测时间段"""
        observation_schedule = []
        
        for i, target in enumerate(self.targets):
            # 计算总曝光时间（秒）
            total_exposure_seconds = sum(f.exposure * f.count for f in target.filters)
            
            # 加上额外时间（读取、下载、抖动、对焦等）
            # 估算每张图片额外需要30秒
            total_images = sum(f.count for f in target.filters)
            overhead_seconds = total_images * 30
            
            # 自动对焦时间（如果启用）
            af_time = 0
            if self.global_settings and self.global_settings.auto_focus:
                # 假设每次对焦需要3分钟，根据af_interval计算需要多少次对焦
                total_duration_minutes = (total_exposure_seconds + overhead_seconds) / 60
                af_count = int(total_duration_minutes / self.global_settings.af_interval) + 1
                af_time = af_count * 3 * 60  # 3分钟每次
            
            total_duration_seconds = total_exposure_seconds + overhead_seconds + af_time
            
            # 严格按照配置文件中定义的开始时间
            start_time = target.start_time
            
            # 计算理论结束时间（基于持续时间）
            theoretical_end_time = start_time + timedelta(seconds=total_duration_seconds)
            
            # 确定实际结束时间：如果不是最后一个目标，使用下一个目标的开始时间
            if i < len(self.targets) - 1:
                # 不是最后一个目标，结束时间设置为下一个目标的开始时间
                actual_end_time = self.targets[i + 1].start_time
                # 如果理论结束时间早于下一个目标开始时间，使用理论时间；否则使用下一个目标开始时间
                end_time = min(theoretical_end_time, actual_end_time)
            else:
                # 最后一个目标，使用理论结束时间
                end_time = theoretical_end_time
            
            # 检查全局停止时间
            if self.global_stop_time and end_time > self.global_stop_time:
                end_time = self.global_stop_time
                total_duration_seconds = (end_time - start_time).total_seconds()
                print(f"目标 {target.name} 调整结束时间到全局停止时间")
            
            # 检查是否超过了全局停止时间
            if self.global_stop_time and start_time >= self.global_stop_time:
                print(f"目标 {target.name} 超过全局停止时间，跳过")
                continue
            
            # 检查结束时间是否超过全局停止时间
            if self.global_stop_time and end_time > self.global_stop_time:
                # 调整结束时间到全局停止时间
                end_time = self.global_stop_time
                total_duration_seconds = (end_time - start_time).total_seconds()
                print(f"目标 {target.name} 调整结束时间到全局停止时间")
            
            # 根据实际结束时间重新计算持续时间
            actual_duration_seconds = (end_time - start_time).total_seconds()
            
            # 如果持续时间被压缩，需要按比例调整曝光和开销时间
            if actual_duration_seconds < total_duration_seconds:
                # 保持曝光时间比例，优先保证曝光时间
                exposure_ratio = min(1.0, actual_duration_seconds / total_duration_seconds)
                adjusted_exposure_seconds = total_exposure_seconds * exposure_ratio
                adjusted_overhead_seconds = actual_duration_seconds - adjusted_exposure_seconds
                
                print(f"目标 {target.name} 持续时间被压缩: {total_duration_seconds/3600:.1f}h -> {actual_duration_seconds/3600:.1f}h")
                total_duration_seconds = actual_duration_seconds
                total_exposure_seconds = adjusted_exposure_seconds
                overhead_seconds = adjusted_overhead_seconds
            
            schedule_item = {
                'target': target,
                'start_time': start_time,
                'end_time': end_time,
                'duration_seconds': actual_duration_seconds,
                'exposure_seconds': total_exposure_seconds,
                'overhead_seconds': overhead_seconds + af_time,
                'filter_breakdown': self._calculate_filter_breakdown(target, start_time, end_time)
            }
            
            observation_schedule.append(schedule_item)
        
        return observation_schedule
    
    def _calculate_filter_breakdown(self, target: TargetConfig, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """计算每个滤镜的详细拍摄计划"""
        breakdown = []
        current_time = start_time
        
        # 计算总可用时间
        total_available_time = (end_time - start_time).total_seconds()
        
        for filter_config in target.filters:
            # 检查是否超过目标结束时间
            if current_time >= end_time:
                break
                
            filter_duration = filter_config.exposure * filter_config.count
            
            # 为每个滤镜添加额外时间（读取、下载、抖动）
            overhead_per_image = 30  # 秒
            filter_overhead = filter_config.count * overhead_per_image
            
            filter_start = current_time
            filter_end = current_time + timedelta(seconds=filter_duration + filter_overhead)
            
            # 检查是否超过目标结束时间
            if filter_start >= end_time:
                break
                
            if filter_end > end_time:
                # 如果滤镜结束时间超过目标结束时间，调整结束时间
                filter_end = end_time
                # 重新计算实际可拍摄的图片数量
                available_time = (filter_end - filter_start).total_seconds()
                # 计算每张图片的总时间（曝光+开销）
                time_per_image = filter_config.exposure + overhead_per_image
                # 计算在时间限制内可以拍摄的图片数量
                max_count = int(available_time // time_per_image)
                if max_count > 0:
                    # 更新滤镜配置
                    filter_config.count = max_count
                    filter_duration = filter_config.exposure * max_count
                    filter_overhead = max_count * overhead_per_image
                    print(f"  滤镜 {filter_config.name} 调整图片数量到 {max_count} 张（受目标结束时间限制）")
                else:
                    # 时间不够拍摄任何图片，跳过这个滤镜
                    break
            
            breakdown.append({
                'filter_name': filter_config.name,
                'filter_id': filter_config.filter_id,
                'exposure_time': filter_config.exposure,
                'count': filter_config.count,
                'start_time': filter_start,
                'end_time': filter_end,
                'total_duration': filter_duration + filter_overhead
            })
            
            current_time = filter_end
            
            # 如果已经达到目标结束时间，停止添加更多滤镜
            if current_time >= end_time:
                break
        
        return breakdown
    
    def _generate_pure_mermaid_gantt(self, observation_schedule: List[Dict[str, Any]]) -> str:
        """生成纯净的Mermaid甘特图代码（不包含Markdown代码块）"""
        if not observation_schedule:
            return ""
        
        # 获取整体时间范围
        start_time = min(item['start_time'] for item in observation_schedule)
        end_time = max(item['end_time'] for item in observation_schedule)
        
        # 生成目标颜色
        target_colors = ColorPalette.generate_target_colors(len(observation_schedule))
        
        gantt_code = []
        gantt_code.append("gantt")
        gantt_code.append(f"    title 观测计划甘特图 ({start_time.strftime('%Y-%m-%d')})")
        gantt_code.append(f"    dateFormat YYYY-MM-DD HH:mm:ss")
        gantt_code.append(f"    axisFormat %H:%M")
        gantt_code.append("")
        
        # 添加整体时间轴部分
        gantt_code.append("    section 整体时间轴")
        gantt_code.append(f"    观测开始 :milestone, start, {start_time.strftime('%Y-%m-%d %H:%M:%S')}, 0m")
        
        if self.global_stop_time:
            gantt_code.append(f"    全局停止 :milestone, stop, {self.global_stop_time.strftime('%Y-%m-%d %H:%M:%S')}, 0m")
        
        # 为每个目标创建部分
        for i, item in enumerate(observation_schedule):
            target = item['target']
            section_name = f"目标{i+1}: {target.name}"
            gantt_code.append(f"    section {section_name}")
            
            # 主要观测时间段
            duration_minutes = int(item['duration_seconds'] / 60)
            task_id = f"task{i}"
            gantt_code.append(f"    总观测 :active, {task_id}, {item['start_time'].strftime('%Y-%m-%d %H:%M:%S')}, {duration_minutes}m")
            
            # 添加颜色样式（使用颜色编码）
            if target_colors:
                color = target_colors[i % len(target_colors)]
                gantt_code.append(f"    %% style {task_id} fill:{color}")
            
            # 添加滤镜详情 - 在HTML模式中也显示详细信息
            filter_breakdown = self._calculate_filter_breakdown(item['target'], item['start_time'], item['end_time'])
            for j, filter_info in enumerate(filter_breakdown):
                filter_start = filter_info['start_time']
                filter_duration = int(filter_info['total_duration'] / 60)
                filter_id = f"filter{i}_{j}"
                count = filter_info['count']
                exposure_time = filter_info['exposure_time']
                total_minutes = (count * exposure_time) / 60
                filter_name = filter_info['filter_name']
                
                # 显示格式：滤镜名称 (数量×单张曝光时间=总曝光时间)
                gantt_code.append(f"    {filter_name} ({count}×{exposure_time}s={total_minutes:.0f}m) :{filter_id}, {filter_start.strftime('%Y-%m-%d %H:%M:%S')}, {filter_duration}m")
                
                # 添加滤镜颜色
                filter_color = ColorPalette.get_filter_color(filter_name)
                gantt_code.append(f"    %% style {filter_id} fill:{filter_color}")
        
        # 添加统计信息部分
        gantt_code.append("")
        gantt_code.append("    section 统计信息")
        gantt_code.append("    总曝光时间 :crit, 0m")
        gantt_code.append("    总开销时间 : 0m")
        gantt_code.append("    总观测时间 : 0m")
        
        return "\n".join(gantt_code)

    def generate_mermaid_gantt(self, observation_schedule: List[Dict[str, Any]], 
                               use_colors: bool = True, show_filters: bool = True) -> str:
        """生成mermaid甘特图代码"""
        if not observation_schedule:
            return ""
        
        # 获取整体时间范围
        start_time = min(item['start_time'] for item in observation_schedule)
        end_time = max(item['end_time'] for item in observation_schedule)
        
        # 生成目标颜色
        target_colors = ColorPalette.generate_target_colors(len(observation_schedule)) if use_colors else None
        
        gantt_code = []
        gantt_code.append("```mermaid")
        gantt_code.append("gantt")
        gantt_code.append(f"    title 观测计划甘特图 ({start_time.strftime('%Y-%m-%d')})")
        gantt_code.append(f"    dateFormat YYYY-MM-DD HH:mm:ss")
        gantt_code.append(f"    axisFormat %H:%M")
        gantt_code.append("")
        
        # 添加整体时间轴部分
        gantt_code.append("    section 整体时间轴")
        gantt_code.append(f"    观测开始 :milestone, start, {start_time.strftime('%Y-%m-%d %H:%M:%S')}, 0m")
        
        if self.global_stop_time:
            gantt_code.append(f"    全局停止 :milestone, stop, {self.global_stop_time.strftime('%Y-%m-%d %H:%M:%S')}, 0m")
        
        # 为每个目标创建部分
        for i, item in enumerate(observation_schedule):
            target = item['target']
            section_name = f"目标{i+1}: {target.name}"
            gantt_code.append(f"    section {section_name}")
            
            # 主要观测时间段
            start_str = item['start_time'].strftime('%Y-%m-%d %H:%M:%S')
            duration_minutes = int(item['duration_seconds'] / 60)
            
            # 主要观测任务
            task_id = f"task{i}"
            if use_colors and target_colors:
                gantt_code.append(f"    总观测 :active, {task_id}, {start_str}, {duration_minutes}m")
                # 添加颜色样式注释
                gantt_code.append(f"    %% style {task_id} fill:{target_colors[i]}")
            else:
                gantt_code.append(f"    总观测 :active, {task_id}, {start_str}, {duration_minutes}m")
            
            # 滤镜详细分解
            if show_filters:
                for j, filter_info in enumerate(item['filter_breakdown']):
                    filter_start = filter_info['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                    filter_duration = int(filter_info['total_duration'] / 60)
                    filter_name = filter_info['filter_name']
                    filter_task_id = f"filter{i}_{j}"
                    
                    gantt_code.append(f"    {filter_name} ({filter_info['count']}张) :{filter_task_id}, {filter_start}, {filter_duration}m")
                    
                    # 添加滤镜颜色样式
                    if use_colors:
                        filter_color = ColorPalette.get_filter_color(filter_name)
                        gantt_code.append(f"    %% style {filter_task_id} fill:{filter_color}")
            
            gantt_code.append("")
        
        # 添加统计信息作为注释
        total_exposure = sum(item['exposure_seconds'] for item in observation_schedule) / 3600
        total_overhead = sum(item['overhead_seconds'] for item in observation_schedule) / 3600
        total_time = sum(item['duration_seconds'] for item in observation_schedule) / 3600
        
        gantt_code.append("    section 统计信息")
        gantt_code.append(f"    总曝光时间 :crit, 0m")
        gantt_code.append(f"    总开销时间 : 0m")
        gantt_code.append(f"    总观测时间 : 0m")
        
        gantt_code.append("```")
        
        # 添加统计信息说明
        gantt_code.append("")
        gantt_code.append("## 观测计划统计")
        gantt_code.append(f"- **总曝光时间**: {total_exposure:.1f} 小时")
        gantt_code.append(f"- **总开销时间**: {total_overhead:.1f} 小时") 
        gantt_code.append(f"- **总观测时间**: {total_time:.1f} 小时")
        gantt_code.append(f"- **效率**: {(total_exposure/total_time)*100:.1f}%")
        
        if self.meridian_config:
            gantt_code.append("")
            gantt_code.append("## 中天反转配置")
            gantt_code.append(f"- **停止时间**: 中天前 {self.meridian_config.stop_minutes_before} 分钟")
            gantt_code.append(f"- **恢复时间**: 中天后 {self.meridian_config.resume_minutes_after} 分钟")
            gantt_code.append(f"- **安全边距**: {self.meridian_config.safety_margin} 分钟")
        
        gantt_code.append("")
        gantt_code.append("## 目标详情")
        
        for i, item in enumerate(observation_schedule):
            target = item['target']
            gantt_code.append(f"### 目标{i+1}: {target.name}")
            gantt_code.append(f"- **坐标**: RA={target.ra}, DEC={target.dec}")
            gantt_code.append(f"- **开始时间**: {item['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            gantt_code.append(f"- **结束时间**: {item['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            gantt_code.append(f"- **持续时间**: {item['duration_seconds']/3600:.1f} 小时")
            gantt_code.append(f"- **曝光时间**: {item['exposure_seconds']/3600:.1f} 小时")
            gantt_code.append(f"- **优先级**: {target.priority}")
            
            if use_colors:
                color_box = f"<span style='color: {target_colors[i] if target_colors else '#95A5A6'}'>■</span>"
                gantt_code.append(f"- **颜色标记**: {color_box}")
            
            gantt_code.append("")
            gantt_code.append("**滤镜拍摄计划**:")
            
            for filter_info in item['filter_breakdown']:
                filter_color = ColorPalette.get_filter_color(filter_info['filter_name'])
                color_box = f"<span style='color: {filter_color}'>■</span>"
                gantt_code.append(f"- {color_box} {filter_info['filter_name']}: {filter_info['count']}张 × {filter_info['exposure_time']}秒 = {filter_info['exposure_time']*filter_info['count']/60:.1f}分钟")
            
            gantt_code.append("")
        
        return "\n".join(gantt_code)
    
    def generate_html_report(self, observation_schedule: List[Dict[str, Any]]) -> str:
        """生成HTML格式的报告"""
        if not observation_schedule:
            return ""
        
        # 获取整体时间范围
        start_time = min(item['start_time'] for item in observation_schedule)
        end_time = max(item['end_time'] for item in observation_schedule)
        
        # 生成目标颜色
        target_colors = ColorPalette.generate_target_colors(len(observation_schedule))
        
        # 计算统计信息
        total_exposure = sum(item['exposure_seconds'] for item in observation_schedule) / 3600
        total_overhead = sum(item['overhead_seconds'] for item in observation_schedule) / 3600
        total_time = sum(item['duration_seconds'] for item in observation_schedule) / 3600
        
        # 生成纯净的Mermaid甘特图代码（不包含Markdown代码块）
        mermaid_code = self._generate_pure_mermaid_gantt(observation_schedule)
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>观测计划报告</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 25px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .target-card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            background-color: #fafafa;
        }}
        .target-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        .color-indicator {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .filter-item {{
            display: inline-block;
            margin: 5px;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.9em;
            color: white;
            font-weight: bold;
        }}
        .timeline {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .mermaid-container {{
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>观测计划可视化报告</h1>
        <p style="text-align: center; color: #7f8c8d;">
            生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
        
        <h2>📊 统计概览</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(observation_schedule)}</div>
                <div class="stat-label">观测目标</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_exposure:.1f}h</div>
                <div class="stat-label">总曝光时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_time:.1f}h</div>
                <div class="stat-label">总观测时间</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{(total_exposure/total_time)*100:.1f}%</div>
                <div class="stat-label">观测效率</div>
            </div>
        </div>
        
        <h2>📅 时间线概览</h2>
        <div class="timeline">
            <p><strong>开始时间:</strong> {start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>结束时间:</strong> {end_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>总持续时间:</strong> {(end_time - start_time).total_seconds() / 3600:.1f} 小时</p>
            {f'<p><strong>全局停止时间:</strong> {self.global_stop_time.strftime("%Y-%m-%d %H:%M:%S")}</p>' if self.global_stop_time else ''}
        </div>
        
        <h2>📈 甘特图</h2>
        <div class="mermaid-container">
            <div class="mermaid" id="gantt-diagram">
{mermaid_code}
            </div>
        </div>
        
        <h2>🎯 目标详情</h2>
"""
        
        # 添加每个目标的详细信息
        for i, item in enumerate(observation_schedule):
            target = item['target']
            color = target_colors[i]
            
            html += f"""
        <div class="target-card">
            <div class="target-header">
                <div class="color-indicator" style="background-color: {color}"></div>
                <h3>目标 {i+1}: {target.name}</h3>
            </div>
            <table>
                <tr><td><strong>坐标</strong></td><td>RA: {target.ra}, DEC: {target.dec}</td></tr>
                <tr><td><strong>开始时间</strong></td><td>{item['start_time'].strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                <tr><td><strong>结束时间</strong></td><td>{item['end_time'].strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                <tr><td><strong>持续时间</strong></td><td>{item['duration_seconds']/3600:.1f} 小时</td></tr>
                <tr><td><strong>曝光时间</strong></td><td>{item['exposure_seconds']/3600:.1f} 小时</td></tr>
                <tr><td><strong>优先级</strong></td><td>{target.priority}</td></tr>
            </table>
            <h4>滤镜拍摄计划</h4>
"""
            
            for filter_info in item['filter_breakdown']:
                filter_name = filter_info['filter_name']
                filter_color = ColorPalette.get_filter_color(filter_name)
                total_exposure = filter_info['exposure_time'] * filter_info['count']
                
                html += f"""
            <div class="filter-item" style="background-color: {filter_color}">
                {filter_name}: {filter_info['count']}张 × {filter_info['exposure_time']}s = {total_exposure/60:.1f}分钟
            </div>
"""
            
            html += "</div>"
        
        html += """
    </div>
    
    <script>
        // 初始化Mermaid
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            gantt: {
                useMaxWidth: true,
                leftPadding: 75,
                rightPadding: 20,
                topPadding: 50,
                bottomPadding: 50,
                gridLineStartPadding: 35,
                fontSize: 11,
                fontFamily: 'Arial'
            }
        });
    </script>
</body>
</html>
"""
        
        return html
    
    def save_gantt_chart(self, gantt_code: str, output_file: str):
        """保存甘特图代码到文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(gantt_code)
            print(f"甘特图已保存到: {output_file}")
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    def print_summary(self, observation_schedule: List[Dict[str, Any]]):
        """打印观测计划摘要"""
        if not observation_schedule:
            print("没有观测计划")
            return
        
        print("\n" + "="*60)
        print("观测计划摘要")
        print("="*60)
        
        total_exposure = sum(item['exposure_seconds'] for item in observation_schedule)
        total_overhead = sum(item['overhead_seconds'] for item in observation_schedule)
        total_time = sum(item['duration_seconds'] for item in observation_schedule)
        
        print(f"目标数量: {len(observation_schedule)}")
        print(f"总曝光时间: {total_exposure/3600:.1f} 小时")
        print(f"总开销时间: {total_overhead/3600:.1f} 小时") 
        print(f"总观测时间: {total_time/3600:.1f} 小时")
        print(f"观测效率: {(total_exposure/total_time)*100:.1f}%")
        
        print("\n目标详情:")
        for i, item in enumerate(observation_schedule):
            target = item['target']
            print(f"\n{i+1}. {target.name}")
            print(f"   时间: {item['start_time'].strftime('%H:%M')} - {item['end_time'].strftime('%H:%M')}")
            print(f"   持续时间: {item['duration_seconds']/3600:.1f}h")
            print(f"   曝光时间: {item['exposure_seconds']/3600:.1f}h")
            print(f"   优先级: {target.priority}")
            
            filter_summary = ", ".join([
                f"{f['filter_name']}({f['count']}×{f['exposure_time']}s)" 
                for f in item['filter_breakdown']
            ])
            print(f"   滤镜: {filter_summary}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='高级观测队列可视化工具')
    parser.add_argument('config_file', help='配置文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径', default='observation_report.md')
    parser.add_argument('-f', '--format', choices=['markdown', 'html', 'both'], 
                       default='markdown', help='输出格式')
    parser.add_argument('--no-colors', action='store_true', help='禁用颜色')
    parser.add_argument('--no-filters', action='store_true', help='在甘特图中隐藏滤镜详情')
    parser.add_argument('-s', '--summary', action='store_true', help='只显示摘要信息')
    parser.add_argument('-m', '--mermaid', action='store_true', help='只输出mermaid代码')
    parser.add_argument('--open', action='store_true', help='生成HTML报告后自动打开浏览器')
    
    args = parser.parse_args()
    
    # 创建reports文件夹（如果不存在）
    reports_dir = os.path.join(os.getcwd(), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # 创建可视化器
    visualizer = ObservationScheduleVisualizer()
    
    # 加载配置
    if not visualizer.load_config(args.config_file):
        return 1
    
    # 计算观测时间
    observation_schedule = visualizer.calculate_observation_times()
    
    if args.summary:
        # 只显示摘要
        visualizer.print_summary(observation_schedule)
    else:
        # 生成内容
        if args.format == 'html' or args.format == 'both':
            # 生成HTML报告
            html_content = visualizer.generate_html_report(observation_schedule)
            html_file = os.path.join(reports_dir, args.output.replace('.md', '.html'))
            if visualizer.save_gantt_chart(html_content, html_file):
                print(f"HTML报告已保存到: {html_file}")
                # 自动打开浏览器
                if args.open:
                    try:
                        webbrowser.open(f'file://{os.path.abspath(html_file)}')
                        print(f"正在打开浏览器查看HTML报告...")
                    except Exception as e:
                        print(f"无法自动打开浏览器: {e}")
                        print(f"请手动打开: {html_file}")
        
        if args.format == 'markdown' or args.format == 'both':
            # 生成Markdown甘特图
            gantt_code = visualizer.generate_mermaid_gantt(
                observation_schedule, 
                use_colors=not args.no_colors,
                show_filters=not args.no_filters
            )
            
            if args.mermaid:
                # 只输出mermaid代码
                print(gantt_code)
            else:
                # 保存到文件
                markdown_file = os.path.join(reports_dir, args.output)
                if visualizer.save_gantt_chart(gantt_code, markdown_file):
                    print(f"\n甘特图已生成并保存到: {markdown_file}")
                    print("你可以在支持mermaid的编辑器中查看，如:")
                    print("- VS Code (安装Mermaid插件)")
                    print("- Obsidian") 
                    print("- Typora")
                    print("- 在线mermaid编辑器: https://mermaid.live")
                    
                    # 同时显示摘要
                    visualizer.print_summary(observation_schedule)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())