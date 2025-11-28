"""
ACPClient GUI主应用程序
多目标天文观测系统图形界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import logging
from datetime import datetime
from pathlib import Path

# 导入项目模块
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.new_multi_target_orchestrator import NewMultiTargetOrchestrator


class ACPClientGUI:
    """ACPClient图形界面主类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ACPClient - 多目标天文观测系统 v2.0")
        self.root.geometry("1200x800")
        
        # 设置主题
        self.setup_theme()
        
        # 初始化变量
        self.orchestrator = None
        self.observation_thread = None
        self.log_queue = queue.Queue()
        self.is_observing = False
        self.config_file = "multi_target_config.yaml"
        
        # 创建界面
        self.create_widgets()
        
        # 启动日志更新定时器
        self.update_logs()
        
    def setup_theme(self):
        """设置界面主题"""
        # 设置样式
        style = ttk.Style()
        
        # 配置颜色主题
        self.colors = {
            'bg': '#f0f0f0',
            'fg': '#333333',
            'accent': '#007acc',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545',
            'dark': '#343a40',
            'light': '#ffffff'
        }
        
        # 配置根窗口
        self.root.configure(bg=self.colors['bg'])
        
        # 配置ttk样式
        style.theme_use('clam')
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TButton', background=self.colors['accent'], foreground='white')
        style.map('TButton', background=[('active', '#0056b3')])
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground=self.colors['success'])
        style.configure('Warning.TLabel', foreground=self.colors['warning'])
        style.configure('Danger.TLabel', foreground=self.colors['danger'])
        
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 创建标题栏
        self.create_header(main_frame)
        
        # 创建笔记本（标签页）
        self.create_notebook(main_frame)
        
        # 创建状态栏
        self.create_status_bar(main_frame)
        
    def create_header(self, parent):
        """创建标题栏"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 标题
        title_label = ttk.Label(header_frame, text="ACPClient - 多目标天文观测系统",
                                 style='Header.TLabel', font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # 配置文件路径
        self.config_label = ttk.Label(header_frame, text=f"配置文件: {self.config_file}")
        self.config_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 控制按钮
        button_frame = ttk.Frame(header_frame)
        button_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.E, tk.N, tk.S))
        
        ttk.Button(button_frame, text="选择配置", command=self.select_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="验证配置", command=self.validate_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="开始观测", command=self.start_observation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="停止观测", command=self.stop_observation).pack(side=tk.LEFT, padx=5)
        
    def create_notebook(self, parent):
        """创建标签页"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建各个标签页
        self.create_control_tab()
        self.create_status_tab()
        self.create_config_tab()
        self.create_log_tab()
        
    def create_control_tab(self):
        """创建控制面板标签页"""
        control_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(control_frame, text="观测控制")
        
        # 观测控制区域
        control_group = ttk.LabelFrame(control_frame, text="观测控制", padding="10")
        control_group.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 观测模式选择
        mode_frame = ttk.Frame(control_group)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mode_frame, text="观测模式:").pack(side=tk.LEFT, padx=(0, 10))
        self.observation_mode = tk.StringVar(value="normal")
        ttk.Radiobutton(mode_frame, text="正常观测", variable=self.observation_mode, 
                       value="normal").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="DRYRUN模式", variable=self.observation_mode,
                       value="dryrun").pack(side=tk.LEFT, padx=5)
        
        # 观测选项
        options_frame = ttk.Frame(control_group)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.validate_only = tk.BooleanVar()
        self.show_summary = tk.BooleanVar()
        
        ttk.Checkbutton(options_frame, text="仅验证配置", 
                       variable=self.validate_only).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(options_frame, text="显示摘要",
                       variable=self.show_summary).pack(side=tk.LEFT)
        
        # 控制按钮
        button_frame = ttk.Frame(control_group)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_button = ttk.Button(button_frame, text="开始观测", 
                                       command=self.start_observation)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="停止观测",
                                      command=self.stop_observation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # 观测进度
        progress_frame = ttk.LabelFrame(control_frame, text="观测进度", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # 当前状态
        self.current_status = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, text="当前状态:").pack(anchor=tk.W)
        self.status_label = ttk.Label(progress_frame, textvariable=self.current_status,
                                     style='Success.TLabel')
        self.status_label.pack(anchor=tk.W, pady=(5, 0))
        
        # 当前目标
        self.current_target = tk.StringVar(value="无")
        ttk.Label(progress_frame, text="当前目标:").pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(progress_frame, textvariable=self.current_target).pack(anchor=tk.W)
        
    def create_status_tab(self):
        """创建状态监控标签页"""
        status_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(status_frame, text="状态监控")
        
        # 左侧：天文台状态
        left_frame = ttk.Frame(status_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        observatory_group = ttk.LabelFrame(left_frame, text="天文台状态", padding="10")
        observatory_group.pack(fill=tk.BOTH, expand=True)
        
        # 状态显示
        self.observatory_status = {}
        status_items = [
            ("连接状态", "disconnected"),
            ("望远镜状态", "unknown"),
            ("相机状态", "unknown"),
            ("滤镜轮状态", "unknown"),
            ("当前坐标", "unknown"),
            ("当前时间", "unknown")
        ]
        
        for i, (label, default) in enumerate(status_items):
            ttk.Label(observatory_group, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=default)
            self.observatory_status[label] = var
            ttk.Label(observatory_group, textvariable=var).grid(row=i, column=1, sticky=tk.W, padx=(10, 0))
        
        # 刷新按钮
        ttk.Button(observatory_group, text="刷新状态", 
                  command=self.refresh_observatory_status).grid(row=len(status_items), column=0, columnspan=2, pady=(10, 0))
        
        # 右侧：目标列表
        right_frame = ttk.Frame(status_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        targets_group = ttk.LabelFrame(right_frame, text="观测目标", padding="10")
        targets_group.pack(fill=tk.BOTH, expand=True)
        
        # 目标树形视图
        self.targets_tree = ttk.Treeview(targets_group, columns=('状态', '优先级', '开始时间'), height=10)
        self.targets_tree.heading('#0', text='目标名称')
        self.targets_tree.heading('状态', text='状态')
        self.targets_tree.heading('优先级', text='优先级')
        self.targets_tree.heading('开始时间', text='开始时间')
        
        self.targets_tree.column('#0', width=150)
        self.targets_tree.column('状态', width=80)
        self.targets_tree.column('优先级', width=60)
        self.targets_tree.column('开始时间', width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(targets_group, orient=tk.VERTICAL, command=self.targets_tree.yview)
        self.targets_tree.configure(yscrollcommand=scrollbar.set)
        
        self.targets_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 加载目标按钮
        ttk.Button(targets_group, text="加载目标", 
                  command=self.load_targets).pack(pady=(10, 0))
        
    def create_config_tab(self):
        """创建配置管理标签页"""
        config_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(config_frame, text="配置管理")
        
        # 配置编辑区域
        editor_frame = ttk.LabelFrame(config_frame, text="配置文件编辑器", padding="10")
        editor_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文本编辑器
        self.config_text = tk.Text(editor_frame, wrap=tk.NONE, height=25)
        self.config_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL, command=self.config_text.yview)
        self.config_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(editor_frame, orient=tk.HORIZONTAL, command=self.config_text.xview)
        self.config_text.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 按钮区域
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="加载配置", command=self.load_config_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="保存配置", command=self.save_config_file).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="验证配置", command=self.validate_config_file).pack(side=tk.LEFT)
        
        # 加载默认配置
        self.load_config_file()
        
    def create_log_tab(self):
        """创建日志标签页"""
        log_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(log_frame, text="系统日志")
        
        # 日志显示区域
        log_group = ttk.LabelFrame(log_frame, text="系统日志", padding="10")
        log_group.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = tk.Text(log_group, wrap=tk.NONE, height=25, state=tk.DISABLED)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(log_group, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(log_group, orient=tk.HORIZONTAL, command=self.log_text.xview)
        self.log_text.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 控制按钮
        button_frame = ttk.Frame(log_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="清空日志", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="保存日志", command=self.save_logs).pack(side=tk.LEFT)
        
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 0))
        
        # 状态信息
        self.status_text = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_text)
        status_label.pack(side=tk.LEFT)
        
        # 时间显示
        self.time_text = tk.StringVar()
        time_label = ttk.Label(status_frame, textvariable=self.time_text)
        time_label.pack(side=tk.RIGHT)
        
        # 更新时钟
        self.update_clock()
        
    def update_clock(self):
        """更新时钟"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.time_text.set(current_time)
        self.root.after(1000, self.update_clock)
        
    def select_config(self):
        """选择配置文件"""
        filename = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if filename:
            self.config_file = filename
            self.config_label.config(text=f"配置文件: {filename}")
            self.load_config_file()
            self.log_message(f"已选择配置文件: {filename}")
            
    def validate_config(self):
        """验证配置"""
        self.log_message("开始验证配置...")
        try:
            orchestrator = NewMultiTargetOrchestrator(self.config_file, dry_run=True)
            results = orchestrator.validate_targets()
            
            valid_count = sum(1 for r in results if r.get('valid', False))
            total_count = len(results)
            
            self.log_message(f"配置验证完成: {valid_count}/{total_count} 个目标有效")
            
            # 显示验证结果对话框
            self.show_validation_results(results)
            
        except Exception as e:
            self.log_message(f"配置验证失败: {e}", level="error")
            messagebox.showerror("验证失败", str(e))
            
    def show_validation_results(self, results):
        """显示验证结果"""
        result_window = tk.Toplevel(self.root)
        result_window.title("配置验证结果")
        result_window.geometry("600x400")
        
        # 创建文本框显示结果
        text = tk.Text(result_window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 插入验证结果
        for result in results:
            status = "✓" if result.get('valid', False) else "✗"
            name = result['name']
            text.insert(tk.END, f"{status} {name}\n")
            
            if not result.get('valid', False):
                if 'error' in result:
                    text.insert(tk.END, f"  错误: {result['error']}\n")
                elif 'observability' in result and not result['observability']['is_observable']:
                    text.insert(tk.END, f"  不可观测: {result['observability']['reason']}\n")
            text.insert(tk.END, "\n")
        
        text.config(state=tk.DISABLED)
        
    def start_observation(self):
        """开始观测"""
        if self.is_observing:
            messagebox.showwarning("警告", "观测已在进行中")
            return
            
        self.log_message("开始观测序列...")
        self.is_observing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.current_status.set("观测中...")
        
        # 创建观测线程
        self.observation_thread = threading.Thread(target=self.observation_worker)
        self.observation_thread.daemon = True
        self.observation_thread.start()
        
    def stop_observation(self):
        """停止观测"""
        if not self.is_observing:
            return
            
        self.log_message("停止观测序列...")
        self.is_observing = False
        self.current_status.set("停止中...")
        
        # 等待线程结束
        if self.observation_thread and self.observation_thread.is_alive():
            self.observation_thread.join(timeout=5)
            
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.current_status.set("已停止")
        self.progress_var.set(0)
        
    def observation_worker(self):
        """观测工作线程"""
        try:
            # 创建协调器
            dry_run = self.observation_mode.get() == "dryrun"
            orchestrator = NewMultiTargetOrchestrator(self.config_file, dry_run=dry_run)
            
            # 如果是验证模式
            if self.validate_only.get():
                self.log_message("执行配置验证模式...")
                results = orchestrator.validate_targets()
                self.root.after(0, self.update_validation_display, results)
                return
                
            # 如果是摘要模式
            if self.show_summary.get():
                self.log_message("执行摘要模式...")
                summary = orchestrator.calculate_schedule_summary()
                self.root.after(0, self.update_summary_display, summary)
                return
                
            # 正常运行模式
            self.log_message("执行正常观测模式...")
            results = orchestrator.run_observation_sequence()
            self.root.after(0, self.update_results_display, results)
            
        except Exception as e:
            self.log_message(f"观测执行失败: {e}", level="error")
            self.root.after(0, self.observation_error, str(e))
        finally:
            self.is_observing = False
            self.root.after(0, self.observation_completed)
            
    def update_validation_display(self, results):
        """更新验证结果显示"""
        valid_count = sum(1 for r in results if r.get('valid', False))
        total_count = len(results)
        self.current_status.set(f"验证完成: {valid_count}/{total_count} 有效")
        self.show_validation_results(results)
        
    def update_summary_display(self, summary):
        """更新摘要显示"""
        self.current_status.set("摘要生成完成")
        summary_text = f"总目标: {summary['total_targets']}, 有效: {summary['valid_targets']}"
        self.log_message(summary_text)
        
    def update_results_display(self, results):
        """更新结果显示"""
        completed = results['completed_targets']
        failed = results['failed_targets']
        self.current_status.set(f"观测完成: 成功 {completed}, 失败 {failed}")
        self.log_message(f"观测序列完成 - 成功: {completed}, 失败: {failed}")
        
    def observation_error(self, error_msg):
        """处理观测错误"""
        self.current_status.set("观测失败")
        messagebox.showerror("观测错误", error_msg)
        
    def observation_completed(self):
        """观测完成处理"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_var.set(100)
        
    def refresh_observatory_status(self):
        """刷新天文台状态"""
        self.log_message("刷新天文台状态...")
        try:
            if not self.orchestrator:
                self.orchestrator = NewMultiTargetOrchestrator(self.config_file, dry_run=True)
                
            status = self.orchestrator.get_observatory_status()
            self.update_observatory_display(status)
            
        except Exception as e:
            self.log_message(f"状态刷新失败: {e}", level="warning")
            
    def update_observatory_display(self, status):
        """更新天文台状态显示"""
        # 这里需要根据实际的status数据结构来更新
        # 暂时显示模拟数据
        self.observatory_status["连接状态"].set("已连接")
        self.observatory_status["望远镜状态"].set("就绪")
        self.observatory_status["相机状态"].set("就绪")
        self.observatory_status["滤镜轮状态"].set("就绪")
        self.observatory_status["当前坐标"].set("未知")
        self.observatory_status["当前时间"].set(datetime.now().strftime('%H:%M:%S'))
        
    def load_targets(self):
        """加载观测目标"""
        self.log_message("加载观测目标...")
        try:
            # 清空现有目标
            for item in self.targets_tree.get_children():
                self.targets_tree.delete(item)
                
            # 加载配置文件中的目标
            import yaml
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            targets = config.get('targets', [])
            for target in targets:
                name = target.get('name', 'Unknown')
                priority = target.get('priority', 0)
                start_time = target.get('start_time', 'Unknown')
                status = "待观测"
                
                self.targets_tree.insert('', 'end', text=name, 
                                       values=(status, priority, start_time))
                                       
            self.log_message(f"已加载 {len(targets)} 个观测目标")
            
        except Exception as e:
            self.log_message(f"目标加载失败: {e}", level="error")
            
    def load_config_file(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(1.0, content)
            self.log_message(f"已加载配置文件: {self.config_file}")
            
        except Exception as e:
            self.log_message(f"配置文件加载失败: {e}", level="error")
            
    def save_config_file(self):
        """保存配置文件"""
        try:
            content = self.config_text.get(1.0, tk.END)
            
            # 验证YAML格式
            import yaml
            yaml.safe_load(content)  # 这会抛出异常如果格式不正确
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.log_message(f"配置文件已保存: {self.config_file}")
            messagebox.showinfo("成功", "配置文件已保存")
            
        except yaml.YAMLError as e:
            self.log_message(f"YAML格式错误: {e}", level="error")
            messagebox.showerror("格式错误", f"YAML格式错误:\n{str(e)}")
        except Exception as e:
            self.log_message(f"配置文件保存失败: {e}", level="error")
            messagebox.showerror("保存失败", str(e))
            
    def validate_config_file(self):
        """验证配置文件"""
        try:
            content = self.config_text.get(1.0, tk.END)
            import yaml
            config = yaml.safe_load(content)
            
            # 基本验证
            if 'targets' not in config:
                raise ValueError("配置缺少'targets'部分")
                
            targets = config['targets']
            if not targets:
                raise ValueError("目标列表为空")
                
            for i, target in enumerate(targets):
                if 'name' not in target:
                    raise ValueError(f"目标 {i+1} 缺少'name'字段")
                if 'ra' not in target or 'dec' not in target:
                    raise ValueError(f"目标 {target.get('name', i+1)} 缺少坐标信息")
                    
            self.log_message("配置文件格式正确")
            messagebox.showinfo("验证成功", "配置文件格式正确")
            
        except Exception as e:
            self.log_message(f"配置文件验证失败: {e}", level="error")
            messagebox.showerror("验证失败", str(e))
            
    def log_message(self, message, level="info"):
        """记录日志消息"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        self.log_queue.put(log_entry)
        
    def update_logs(self):
        """更新日志显示"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.insert_log_message(message)
        except queue.Empty:
            pass
            
        # 继续定时更新
        self.root.after(100, self.update_logs)
        
    def insert_log_message(self, message):
        """插入日志消息到文本框"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)  # 滚动到底部
        self.log_text.configure(state=tk.DISABLED)
        
    def clear_logs(self):
        """清空日志"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.log_message("日志已清空")
        
    def save_logs(self):
        """保存日志到文件"""
        filename = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log_message(f"日志已保存到: {filename}")
            except Exception as e:
                self.log_message(f"日志保存失败: {e}", level="error")


def main():
    """GUI主函数"""
    root = tk.Tk()
    app = ACPClientGUI(root)
    
    # 记录启动日志
    app.log_message("ACPClient GUI 启动成功")
    app.log_message(f"配置文件: {app.config_file}")
    
    # 运行主循环
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n用户中断程序")
    finally:
        print("ACPClient GUI 已关闭")


if __name__ == "__main__":
    main()