"""
GUI工具模块
提供GUI相关的辅助功能和组件
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import queue


class StatusBar(ttk.Frame):
    """自定义状态栏组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_ui()
        self.update_clock()
        
    def setup_ui(self):
        """设置界面"""
        # 左侧状态信息
        self.status_label = ttk.Label(self, text="就绪", relief=tk.SUNKEN)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 右侧时间显示
        self.time_label = ttk.Label(self, text="", relief=tk.SUNKEN, width=20)
        self.time_label.pack(side=tk.RIGHT)
        
    def update_clock(self):
        """更新时间"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.time_label.config(text=current_time)
        self.after(1000, self.update_clock)
        
    def set_status(self, text):
        """设置状态文本"""
        self.status_label.config(text=text)
        

class LogPanel(ttk.Frame):
    """日志面板组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.log_queue = queue.Queue()
        self.setup_ui()
        self.start_log_updater()
        
    def setup_ui(self):
        """设置界面"""
        # 创建文本框
        self.text_widget = tk.Text(self, wrap=tk.NONE, state=tk.DISABLED)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text_widget.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.configure(yscrollcommand=v_scrollbar.set)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text_widget.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_widget.configure(xscrollcommand=h_scrollbar.set)
        
    def log_message(self, message, level="info"):
        """添加日志消息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"
        self.log_queue.put(log_entry)
        
    def start_log_updater(self):
        """启动日志更新器"""
        self.update_logs()
        
    def update_logs(self):
        """更新日志显示"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.insert_log_message(message)
        except queue.Empty:
            pass
        finally:
            # 继续定时更新
            self.after(100, self.update_logs)
            
    def insert_log_message(self, message):
        """插入日志消息"""
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message + '\n')
        self.text_widget.see(tk.END)  # 滚动到底部
        self.text_widget.configure(state=tk.DISABLED)
        
    def clear_logs(self):
        """清空日志"""
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.configure(state=tk.DISABLED)
        self.log_message("日志已清空")


class ProgressPanel(ttk.Frame):
    """进度面板组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var,
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        # 状态信息
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X)
        
        self.status_var = tk.StringVar(value="就绪")
        self.target_var = tk.StringVar(value="无")
        
        ttk.Label(info_frame, text="状态:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, textvariable=self.status_var).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(info_frame, text="当前目标:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(info_frame, textvariable=self.target_var).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
    def set_progress(self, value):
        """设置进度值"""
        self.progress_var.set(value)
        
    def set_status(self, status):
        """设置状态"""
        self.status_var.set(status)
        
    def set_target(self, target):
        """设置当前目标"""
        self.target_var.set(target)
        
    def reset(self):
        """重置进度"""
        self.progress_var.set(0)
        self.status_var.set("就绪")
        self.target_var.set("无")


class TargetTree(ttk.Frame):
    """目标树形视图组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        # 创建树形视图
        self.tree = ttk.Treeview(self, columns=('状态', '优先级', '开始时间', 'RA', 'DEC'), 
                                height=10)
        self.tree.heading('#0', text='目标名称')
        self.tree.heading('状态', text='状态')
        self.tree.heading('优先级', text='优先级')
        self.tree.heading('开始时间', text='开始时间')
        self.tree.heading('RA', text='赤经')
        self.tree.heading('DEC', text='赤纬')
        
        # 设置列宽
        self.tree.column('#0', width=150)
        self.tree.column('状态', width=80)
        self.tree.column('优先级', width=60)
        self.tree.column('开始时间', width=120)
        self.tree.column('RA', width=80)
        self.tree.column('DEC', width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def load_targets(self, targets):
        """加载目标列表"""
        # 清空现有目标
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 添加新目标
        for target in targets:
            name = target.get('name', 'Unknown')
            status = target.get('status', '待观测')
            priority = target.get('priority', 0)
            start_time = target.get('start_time', 'Unknown')
            ra = target.get('ra', 'Unknown')
            dec = target.get('dec', 'Unknown')
            
            self.tree.insert('', 'end', text=name, 
                           values=(status, priority, start_time, ra, dec))
                           
    def update_target_status(self, target_name, status):
        """更新目标状态"""
        for item in self.tree.get_children():
            if self.tree.item(item)['text'] == target_name:
                values = list(self.tree.item(item)['values'])
                values[0] = status  # 更新状态列
                self.tree.item(item, values=values)
                break
                
    def get_selected_target(self):
        """获取选中的目标"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            return {
                'name': self.tree.item(item)['text'],
                'values': self.tree.item(item)['values']
            }
        return None


class ObservatoryStatusPanel(ttk.Frame):
    """天文台状态面板组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.status_vars = {}
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        # 状态项
        status_items = [
            ("连接状态", "disconnected"),
            ("望远镜状态", "unknown"),
            ("相机状态", "unknown"),
            ("滤镜轮状态", "unknown"),
            ("当前坐标", "unknown"),
            ("当前时间", "unknown"),
            ("天气状态", "unknown"),
            ("安全状态", "unknown")
        ]
        
        # 创建状态显示
        for i, (label, default) in enumerate(status_items):
            ttk.Label(self, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=default)
            self.status_vars[label] = var
            ttk.Label(self, textvariable=var).grid(row=i, column=1, sticky=tk.W, padx=(10, 0))
            
        # 刷新按钮
        ttk.Button(self, text="刷新状态", command=self.refresh_status).grid(
            row=len(status_items), column=0, columnspan=2, pady=(10, 0))
            
    def set_status(self, status_type, value):
        """设置状态值"""
        if status_type in self.status_vars:
            self.status_vars[status_type].set(value)
            
    def refresh_status(self):
        """刷新状态（需要被子类重写）"""
        pass
        
    def update_all_status(self, status_dict):
        """更新所有状态"""
        for key, value in status_dict.items():
            self.set_status(key, value)


class ConfigEditor(ttk.Frame):
    """配置编辑器组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config_file = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        # 文本编辑器
        self.text_widget = tk.Text(self, wrap=tk.NONE, height=20)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=v_scrollbar.set)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text_widget.xview)
        self.text_widget.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def load_file(self, filepath):
        """加载文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(1.0, content)
            self.config_file = filepath
            
        except Exception as e:
            messagebox.showerror("加载失败", f"无法加载文件: {e}")
            
    def save_file(self):
        """保存文件"""
        if not self.config_file:
            messagebox.showerror("保存失败", "没有指定文件路径")
            return
            
        try:
            content = self.text_widget.get(1.0, tk.END)
            
            # 验证YAML格式
            import yaml
            yaml.safe_load(content)  # 这会抛出异常如果格式不正确
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            messagebox.showinfo("成功", "文件已保存")
            
        except yaml.YAMLError as e:
            messagebox.showerror("格式错误", f"YAML格式错误:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            
    def get_content(self):
        """获取编辑器内容"""
        return self.text_widget.get(1.0, tk.END)
        
    def set_content(self, content):
        """设置编辑器内容"""
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(1.0, content)


# 主题管理器
class ThemeManager:
    """主题管理器"""
    
    THEMES = {
        'light': {
            'bg': '#f0f0f0',
            'fg': '#333333',
            'accent': '#007acc',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545'
        },
        'dark': {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'accent': '#4a9eff',
            'success': '#28a745',
            'warning': '#ffc107',
            'danger': '#dc3545'
        },
        'blue': {
            'bg': '#e3f2fd',
            'fg': '#1976d2',
            'accent': '#2196f3',
            'success': '#4caf50',
            'warning': '#ff9800',
            'danger': '#f44336'
        }
    }
    
    @classmethod
    def apply_theme(cls, root, theme_name='light'):
        """应用主题"""
        if theme_name not in cls.THEMES:
            theme_name = 'light'
            
        theme = cls.THEMES[theme_name]
        
        # 配置根窗口
        root.configure(bg=theme['bg'])
        
        # 配置ttk样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置各种组件样式
        style.configure('TFrame', background=theme['bg'])
        style.configure('TLabel', background=theme['bg'], foreground=theme['fg'])
        style.configure('TButton', background=theme['accent'], foreground='white')
        style.map('TButton', background=[('active', theme['accent'] + '80')])
        
        style.configure('Header.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground=theme['success'])
        style.configure('Warning.TLabel', foreground=theme['warning'])
        style.configure('Danger.TLabel', foreground=theme['danger'])
        
        return theme