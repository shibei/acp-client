#!/usr/bin/env python3
"""
观测队列可视化工具
根据配置文件生成观测计划的mermaid甘特图
"""

import sys
import os
import yaml
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import webbrowser
from dataclasses import dataclass


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
            
            # 确定开始时间 - 始终使用配置文件中定义的开始时间
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
            
            # 检查是否超过了全局停止时间
            if self.global_stop_time and start_time >= self.global_stop_time:
                print(f"目标 {target.name} 开始时间超过全局停止时间，跳过")
                continue
            
            # 检查结束时间是否超过全局停止时间
            if self.global_stop_time and end_time > self.global_stop_time:
                # 调整结束时间到全局停止时间
                end_time = self.global_stop_time
                total_duration_seconds = (end_time - start_time).total_seconds()
                print(f"目标 {target.name} 调整结束时间到全局停止时间")
            
            # 移除current_time跟踪，每个目标独立使用自己的开始时间
            # current_time = end_time
            
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
        
        # 计算可用的总时间
        total_available_time = (end_time - start_time).total_seconds()
        current_time = start_time
        
        for filter_config in target.filters:
            filter_duration = filter_config.exposure * filter_config.count
            
            # 为每个滤镜添加额外时间（读取、下载、抖动）
            overhead_per_image = 30  # 秒
            filter_overhead = filter_config.count * overhead_per_image
            
            # 检查是否还有足够的时间进行这个滤镜的观测
            if current_time >= end_time:
                break
                
            # 计算这个滤镜的理论结束时间
            theoretical_filter_end = current_time + timedelta(seconds=filter_duration + filter_overhead)
            
            # 如果这个滤镜的理论结束时间超过了目标结束时间，调整拍摄数量
            if theoretical_filter_end > end_time:
                available_time = (end_time - current_time).total_seconds()
                # 计算每张图片的总时间（曝光+开销）
                time_per_image = filter_config.exposure + overhead_per_image
                # 计算在时间限制内可以拍摄的图片数量
                max_count = int(available_time // time_per_image)
                if max_count > 0:
                    # 更新滤镜配置
                    filter_config.count = max_count
                    filter_duration = filter_config.exposure * max_count
                    filter_overhead = max_count * overhead_per_image
                    print(f"  滤镜 {filter_config.name} 调整图片数量到 {max_count} 张（受时间限制）")
                else:
                    # 时间不够拍摄任何图片，跳过这个滤镜
                    break
                
                # 重新计算滤镜结束时间
                filter_end = current_time + timedelta(seconds=filter_duration + filter_overhead)
            else:
                filter_end = theoretical_filter_end
            
            filter_start = current_time
            
            breakdown.append({
                'filter_name': filter_config.name,
                'filter_id': filter_config.filter_id,
                'exposure_time': filter_config.exposure,
                'count': filter_config.count,
                'start_time': filter_start,
                'end_time': filter_end,
                'total_duration': filter_duration + filter_overhead
            })
            
            # 检查是否超过全局停止时间
            if self.global_stop_time and filter_start >= self.global_stop_time:
                # 如果滤镜开始时间已经超过全局停止时间，跳过这个滤镜
                break
                
            if self.global_stop_time and filter_end > self.global_stop_time:
                # 如果滤镜结束时间超过全局停止时间，调整结束时间
                filter_end = self.global_stop_time
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
                    print(f"  滤镜 {filter_config.name} 调整图片数量到 {max_count} 张（受全局停止时间限制）")
                else:
                    # 时间不够拍摄任何图片，跳过这个滤镜
                    break
            
            current_time = filter_end
            
            # 如果已经达到全局停止时间，停止添加更多滤镜
            if self.global_stop_time and current_time >= self.global_stop_time:
                break
        
        return breakdown
    
    def generate_mermaid_gantt(self, observation_schedule: List[Dict[str, Any]]) -> str:
        """生成mermaid甘特图代码"""
        if not observation_schedule:
            return ""
        
        # 获取整体时间范围
        start_time = min(item['start_time'] for item in observation_schedule)
        end_time = max(item['end_time'] for item in observation_schedule)
        
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
            gantt_code.append(f"    总观测 :active, obs{i}, {start_str}, {duration_minutes}m")
            
            # 滤镜详细分解
            for j, filter_info in enumerate(item['filter_breakdown']):
                filter_start = filter_info['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                filter_duration = int(filter_info['total_duration'] / 60)
                filter_name = filter_info['filter_name']
                
                gantt_code.append(f"    {filter_name} ({filter_info['count']}张) : {filter_start}, {filter_duration}m")
            
            gantt_code.append("")
        
        # 添加统计信息作为注释
        total_exposure = sum(item['exposure_seconds'] for item in observation_schedule) / 3600
        total_overhead = sum(item['overhead_seconds'] for item in observation_schedule) / 3600
        total_time = sum(item['duration_seconds'] for item in observation_schedule) / 3600
        
        gantt_code.append("    section 统计信息")
        gantt_code.append(f"    总曝光时间 :crit, 0m")
        gantt_code.append(f"    总开销时间 : 0m")
        gantt_code.append(f"    总观测时间 : 0m")
        gantt_code.append("")
        
        gantt_code.append("```")
        
        # 添加统计信息说明
        gantt_code.append("")
        gantt_code.append("## 观测计划统计")
        gantt_code.append(f"- **总曝光时间**: {total_exposure:.1f} 小时")
        gantt_code.append(f"- **总开销时间**: {total_overhead:.1f} 小时")
        gantt_code.append(f"- **总观测时间**: {total_time:.1f} 小时")
        gantt_code.append(f"- **效率**: {(total_exposure/total_time)*100:.1f}%")
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
            gantt_code.append("")
            gantt_code.append("**滤镜拍摄计划**:")
            
            for filter_info in item['filter_breakdown']:
                gantt_code.append(f"- {filter_info['filter_name']}: {filter_info['count']}张 × {filter_info['exposure_time']}秒 = {filter_info['exposure_time']*filter_info['count']/60:.1f}分钟")
            
            gantt_code.append("")
        
        return "\n".join(gantt_code)
    
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
    parser = argparse.ArgumentParser(description='观测队列可视化工具')
    parser.add_argument('config_file', help='配置文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径', default='observation_gantt.md')
    parser.add_argument('-s', '--summary', action='store_true', help='显示摘要信息')
    parser.add_argument('-m', '--mermaid', action='store_true', help='只输出mermaid代码')
    parser.add_argument('--open', action='store_true', help='生成文件后自动打开浏览器查看在线mermaid编辑器')
    
    args = parser.parse_args()
    
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
        # 生成甘特图
        gantt_code = visualizer.generate_mermaid_gantt(observation_schedule)
        
        if args.mermaid:
            # 只输出mermaid代码
            print(gantt_code)
        else:
            # 保存到文件
            if visualizer.save_gantt_chart(gantt_code, args.output):
                print(f"\n甘特图已生成并保存到: {args.output}")
                print("你可以在支持mermaid的编辑器中查看，如:")
                print("- VS Code (安装Mermaid插件)")
                print("- Obsidian") 
                print("- Typora")
                print("- 在线mermaid编辑器: https://mermaid.live")
                
                # 自动打开浏览器
                if args.open:
                    try:
                        webbrowser.open('https://mermaid.live')
                        print(f"正在打开浏览器访问在线mermaid编辑器...")
                    except Exception as e:
                        print(f"无法自动打开浏览器: {e}")
                        print(f"请手动访问: https://mermaid.live")
                
                # 同时显示摘要
                visualizer.print_summary(observation_schedule)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())