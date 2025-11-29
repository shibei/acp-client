#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
观测计划调度器 GUI 界面 - Tkinter版本
使用 tkinter 创建图形用户界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import threading
from datetime import datetime

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入可视化器
try:
    from observation_scheduler_visualizer import ObservationScheduleVisualizer
    from observation_visualizer_advanced import ObservationScheduleVisualizer as AdvancedVisualizer
    print("可视化器导入成功")
except ImportError as e:
    print(f"导入可视化器失败: {e}")
    # 创建占位符类
    class ObservationScheduleVisualizer:
        def load_config(self, config_file):
            return True
        def calculate_observation_times(self):
            return []
        def generate_mermaid_gantt(self, schedule, use_colors=True, show_filters=True):
            return "甘特图生成功能暂不可用"
        def save_gantt_chart(self, content, file_path):
            with open(file_path, 'w') as f:
                f.write(content)
    
    class AdvancedVisualizer:
        def generate_html_report(self, schedule):
            return "<html><body>HTML生成功能暂不可用</body></html>"
        def save_gantt_chart(self, content, file_path):
            with open(file_path, 'w') as f:
                f.write(content)


class ObservationSchedulerTkinterGUI:
    def __init__(self):
        self.config_file = ""
        self.visualizer = ObservationScheduleVisualizer()
        self.advanced_visualizer = AdvancedVisualizer()
        self.observation_schedule = []
        self.output_dir = "reports"
        self.is_generating = False
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("观测计划调度器")
        self.root.geometry("1000x700")
        
        # 创建GUI组件
        self.create_widgets()
        
    def create_widgets(self):
        """创建GUI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置选择区域
        config_frame = ttk.LabelFrame(main_frame, text="配置文件选择", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.config_path_var = tk.StringVar(value="未选择配置文件")
        ttk.Label(config_frame, text="配置文件:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.config_path_var, width=60, state="readonly").grid(row=0, column=1, padx=5)
        ttk.Button(config_frame, text="浏览...", command=self.browse_config).grid(row=0, column=2, padx=5)
        ttk.Button(config_frame, text="加载", command=self.load_config).grid(row=0, column=3, padx=5)
        
        # 参数设置区域
        params_frame = ttk.LabelFrame(main_frame, text="可视化参数", padding="10")
        params_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 输出格式
        self.output_format_var = tk.StringVar(value="Markdown")
        ttk.Label(params_frame, text="输出格式:").grid(row=0, column=0, sticky=tk.W)
        
        format_frame = ttk.Frame(params_frame)
        format_frame.grid(row=0, column=1, padx=5)
        ttk.Radiobutton(format_frame, text="Markdown", variable=self.output_format_var, value="Markdown").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="HTML", variable=self.output_format_var, value="HTML").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="Both", variable=self.output_format_var, value="Both").pack(side=tk.LEFT, padx=5)
        
        # 选项
        self.use_colors_var = tk.BooleanVar(value=True)
        self.show_filters_var = tk.BooleanVar(value=True)
        self.auto_open_browser_var = tk.BooleanVar(value=True)
        
        options_frame = ttk.Frame(params_frame)
        options_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Checkbutton(options_frame, text="使用颜色", variable=self.use_colors_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="显示滤镜详情", variable=self.show_filters_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="自动打开浏览器", variable=self.auto_open_browser_var).pack(side=tk.LEFT, padx=10)
        
        # 操作按钮
        ttk.Button(main_frame, text="生成可视化", command=self.generate_visualization, style="Accent.TButton").grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="可视化结果", padding="10")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 创建标签页
        self.notebook = ttk.Notebook(result_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 甘特图标签页
        gantt_frame = ttk.Frame(self.notebook)
        self.notebook.add(gantt_frame, text="甘特图")
        
        self.gantt_text = scrolledtext.ScrolledText(gantt_frame, wrap=tk.NONE, width=80, height=15)
        self.gantt_text.pack(fill=tk.BOTH, expand=True)
        
        # 摘要信息标签页
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="摘要信息")
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.NONE, width=80, height=15)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置预览标签页
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="配置预览")
        
        self.config_text = scrolledtext.ScrolledText(config_frame, wrap=tk.NONE, width=80, height=15)
        self.config_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, text="状态:").pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        self.last_update_var = tk.StringVar(value="--")
        ttk.Label(status_frame, text="最后更新:").pack(side=tk.LEFT, padx=20)
        ttk.Label(status_frame, textvariable=self.last_update_var).pack(side=tk.LEFT, padx=5)
        
        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 设置样式
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 12, "bold"))
        
    def browse_config(self):
        """浏览配置文件"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")]
        )
        
        if file_path:
            self.config_path_var.set(file_path)
            self.config_file = file_path
    
    def load_config(self):
        """加载配置文件"""
        if not self.config_file:
            messagebox.showerror("错误", "请先选择配置文件")
            return
        
        try:
            self.update_status("正在加载配置...")
            
            if not self.visualizer.load_config(self.config_file):
                messagebox.showerror("错误", "配置文件加载失败")
                return
            
            # 显示配置预览
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_content = f.read()
            
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(1.0, config_content)
            
            self.update_status("配置加载成功")
            self.update_last_update()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def generate_visualization(self):
        """生成可视化"""
        if not self.config_file:
            messagebox.showerror("错误", "请先加载配置文件")
            return
        
        if self.is_generating:
            messagebox.showwarning("警告", "正在生成中，请稍候...")
            return
        
        # 在后台线程中生成
        thread = threading.Thread(target=self.generate_visualization_thread)
        thread.daemon = True
        thread.start()
    
    def generate_visualization_thread(self):
        """在后台线程中生成可视化"""
        self.is_generating = True
        self.update_status("正在生成可视化...")
        
        try:
            # 获取参数
            output_format = self.output_format_var.get()
            use_colors = self.use_colors_var.get()
            show_filters = self.show_filters_var.get()
            auto_open_browser = self.auto_open_browser_var.get()
            
            # 计算观测时间
            self.observation_schedule = self.visualizer.calculate_observation_times()
            
            # 生成甘特图（如果需要）
            if output_format in ["Markdown", "Both"]:
                gantt_code = self.visualizer.generate_mermaid_gantt(
                    self.observation_schedule,
                    use_colors=use_colors,
                    show_filters=show_filters
                )
                
                self.gantt_text.delete(1.0, tk.END)
                self.gantt_text.insert(1.0, gantt_code)
                
                # 保存到文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(self.output_dir, f"gantt_{timestamp}.md")
                self.visualizer.save_gantt_chart(gantt_code, output_file)
            
            # 生成HTML（如果需要）
            if output_format in ["HTML", "Both"]:
                html_content = self.advanced_visualizer.generate_html_report(self.observation_schedule)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                html_file = os.path.join(self.output_dir, f"report_{timestamp}.html")
                self.advanced_visualizer.save_gantt_chart(html_content, html_file)
                
                # 自动打开浏览器
                if auto_open_browser:
                    try:
                        import webbrowser
                        webbrowser.open(f'file://{os.path.abspath(html_file)}')
                    except Exception as e:
                        print(f"无法自动打开浏览器: {e}")
            
            # 显示摘要
            summary_text = self.get_summary_text()
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(1.0, summary_text)
            
            self.update_status("可视化生成完成")
            self.update_last_update()
            
        except Exception as e:
            self.update_status("生成失败")
            self.gantt_text.delete(1.0, tk.END)
            self.gantt_text.insert(1.0, f"生成可视化失败: {str(e)}")
        
        finally:
            self.is_generating = False
    
    def get_summary_text(self):
        """获取摘要信息文本"""
        if not self.observation_schedule:
            return "没有观测计划"
        
        summary_lines = []
        summary_lines.append("=" * 60)
        summary_lines.append("观测计划摘要")
        summary_lines.append("=" * 60)
        
        total_exposure = sum(item['exposure_seconds'] for item in self.observation_schedule)
        total_overhead = sum(item['overhead_seconds'] for item in self.observation_schedule)
        total_time = sum(item['duration_seconds'] for item in self.observation_schedule)
        
        summary_lines.append(f"目标数量: {len(self.observation_schedule)}")
        summary_lines.append(f"总曝光时间: {total_exposure/3600:.1f} 小时")
        summary_lines.append(f"总开销时间: {total_overhead/3600:.1f} 小时")
        summary_lines.append(f"总观测时间: {total_time/3600:.1f} 小时")
        summary_lines.append(f"观测效率: {(total_exposure/total_time)*100:.1f}%")
        
        summary_lines.append("\n目标详情:")
        for i, item in enumerate(self.observation_schedule):
            target = item['target']
            summary_lines.append(f"\n{i+1}. {target.name}")
            summary_lines.append(f"   时间: {item['start_time'].strftime('%H:%M')} - {item['end_time'].strftime('%H:%M')}")
            summary_lines.append(f"   持续时间: {item['duration_seconds']/3600:.1f}h")
            summary_lines.append(f"   曝光时间: {item['exposure_seconds']/3600:.1f}h")
            summary_lines.append(f"   优先级: {target.priority}")
            
            filter_summary = ", ".join([
                f"{f['filter_name']}({f['count']}×{f['exposure_time']}s)"
                for f in item['filter_breakdown']
            ])
            summary_lines.append(f"   滤镜: {filter_summary}")
        
        return "\n".join(summary_lines)
    
    def update_status(self, status):
        """更新状态文本"""
        self.status_var.set(status)
    
    def update_last_update(self):
        """更新最后更新时间"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_update_var.set(current_time)
    
    def run(self):
        """运行GUI程序"""
        self.root.mainloop()


if __name__ == "__main__":
    gui = ObservationSchedulerTkinterGUI()
    gui.run()