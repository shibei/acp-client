"""
GUI演示脚本
用于测试和演示ACPClient GUI功能
"""

import tkinter as tk
from tkinter import ttk
import sys
import os
import threading

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.gui_utils import (
    StatusBar, LogPanel, ProgressPanel, TargetTree, 
    ObservatoryStatusPanel, ConfigEditor, ThemeManager
)


class GUIDemo:
    """GUI组件演示类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ACPClient GUI 组件演示")
        self.root.geometry("1000x700")
        
        # 应用主题
        self.theme = ThemeManager.apply_theme(self.root, 'light')
        
        self.create_widgets()
        self.demo_data()
        
    def create_widgets(self):
        """创建演示界面"""
        # 创建笔记本
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 状态栏演示
        self.create_status_demo(notebook)
        
        # 日志面板演示
        self.create_log_demo(notebook)
        
        # 进度面板演示
        self.create_progress_demo(notebook)
        
        # 目标树演示
        self.create_target_demo(notebook)
        
        # 天文台状态演示
        self.create_observatory_demo(notebook)
        
        # 配置编辑器演示
        self.create_config_demo(notebook)
        
        # 创建状态栏
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
        
    def create_status_demo(self, parent):
        """状态栏演示"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="状态栏演示")
        
        ttk.Label(frame, text="这是一个状态栏组件，显示在窗口底部").pack(pady=20)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="更改状态文本",
                  command=self.change_status_text).pack(side=tk.LEFT, padx=5)
        
    def create_log_demo(self, parent):
        """日志面板演示"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="日志面板演示")
        
        # 创建日志面板
        self.log_panel = LogPanel(frame)
        self.log_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 控制按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="添加信息日志",
                  command=self.add_info_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="添加警告日志",
                  command=self.add_warning_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="添加错误日志",
                  command=self.add_error_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空日志",
                  command=self.log_panel.clear_logs).pack(side=tk.LEFT, padx=5)
                  
    def create_progress_demo(self, parent):
        """进度面板演示"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="进度面板演示")
        
        # 创建进度面板
        self.progress_panel = ProgressPanel(frame)
        self.progress_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 控制按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="开始进度",
                  command=self.start_progress_demo).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="重置进度",
                  command=self.progress_panel.reset).pack(side=tk.LEFT, padx=5)
                  
    def create_target_demo(self, parent):
        """目标树演示"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="目标树演示")
        
        # 创建目标树
        self.target_tree = TargetTree(frame)
        self.target_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 控制按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="加载示例目标",
                  command=self.load_demo_targets).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="更新目标状态",
                  command=self.update_target_status).pack(side=tk.LEFT, padx=5)
                  
    def create_observatory_demo(self, parent):
        """天文台状态演示"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="天文台状态演示")
        
        # 创建天文台状态面板
        self.observatory_panel = ObservatoryStatusPanel(frame)
        self.observatory_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 控制按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="模拟连接",
                  command=self.simulate_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="模拟断开",
                  command=self.simulate_disconnection).pack(side=tk.LEFT, padx=5)
                  
    def create_config_demo(self, parent):
        """配置编辑器演示"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="配置编辑器演示")
        
        # 创建配置编辑器
        self.config_editor = ConfigEditor(frame)
        self.config_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 加载示例配置
        demo_config = """# 示例配置文件
targets:
  - name: 'NGC 1499'
    ra: '04:01:07.51'
    dec: '+36:31:11.9'
    start_time: '2025-11-28 14:17:00'
    priority: 1
    filters:
      - filter_id: 4
        name: 'H-alpha'
        exposure: 600
        count: 20
        binning: 1

acp_server:
  url: 'http://localhost:8080'
  username: 'admin'
  password: 'password'
"""
        self.config_editor.set_content(demo_config)
        
        # 控制按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="验证配置",
                  command=self.validate_demo_config).pack(side=tk.LEFT, padx=5)
        
    def demo_data(self):
        """加载演示数据"""
        self.log_panel.log_message("GUI演示程序启动成功")
        self.log_panel.log_message("这是一个组件演示，展示ACPClient GUI的各种功能")
        
    def change_status_text(self):
        """更改状态栏文本"""
        import random
        messages = [
            "系统就绪",
            "正在连接服务器...",
            "观测进行中",
            "数据处理中...",
            "任务完成"
        ]
        message = random.choice(messages)
        self.status_bar.set_status(message)
        
    def add_info_log(self):
        """添加信息日志"""
        self.log_panel.log_message("这是一条信息日志")
        
    def add_warning_log(self):
        """添加警告日志"""
        self.log_panel.log_message("这是一条警告日志", level="warning")
        
    def add_error_log(self):
        """添加错误日志"""
        self.log_panel.log_message("这是一条错误日志", level="error")
        
    def start_progress_demo(self):
        """开始进度演示"""
        self.progress_panel.set_status("演示进行中...")
        self.progress_panel.set_target("示例目标")
        
        def update_progress():
            for i in range(101):
                self.progress_panel.set_progress(i)
                self.root.update()
                self.root.after(50)  # 50ms延迟
                
            self.progress_panel.set_status("演示完成")
            
        # 在新线程中运行，避免阻塞界面
        thread = threading.Thread(target=update_progress)
        thread.daemon = True
        thread.start()
        
    def load_demo_targets(self):
        """加载演示目标"""
        targets = [
            {
                'name': 'NGC 1499',
                'status': '待观测',
                'priority': 1,
                'start_time': '2025-11-28 14:17:00',
                'ra': '04:01:07.51',
                'dec': '+36:31:11.9'
            },
            {
                'name': 'M 31',
                'status': '待观测',
                'priority': 2,
                'start_time': '2025-11-28 14:18:00',
                'ra': '00:42:44.33',
                'dec': '+41:16:07.5'
            },
            {
                'name': 'M 33',
                'status': '待观测',
                'priority': 3,
                'start_time': '2025-11-28 14:19:00',
                'ra': '01:33:50.89',
                'dec': '+30:39:35.8'
            }
        ]
        
        self.target_tree.load_targets(targets)
        self.log_panel.log_message(f"已加载 {len(targets)} 个演示目标")
        
    def update_target_status(self):
        """更新目标状态"""
        import random
        statuses = ['观测中', '已完成', '失败', '跳过']
        
        # 获取第一个目标
        targets = ['NGC 1499', 'M 31', 'M 33']
        if targets:
            target = random.choice(targets)
            status = random.choice(statuses)
            self.target_tree.update_target_status(target, status)
            self.log_panel.log_message(f"目标 {target} 状态更新为: {status}")
            
    def simulate_connection(self):
        """模拟连接状态"""
        status_data = {
            '连接状态': '已连接',
            '望远镜状态': '就绪',
            '相机状态': '就绪',
            '滤镜轮状态': '就绪',
            '当前坐标': '04:01:07 +36:31:12',
            '当前时间': '14:30:00',
            '天气状态': '晴朗',
            '安全状态': '安全'
        }
        
        self.observatory_panel.update_all_status(status_data)
        self.log_panel.log_message("模拟连接成功")
        
    def simulate_disconnection(self):
        """模拟断开连接"""
        status_data = {
            '连接状态': '断开',
            '望远镜状态': '未知',
            '相机状态': '未知',
            '滤镜轮状态': '未知',
            '当前坐标': '未知',
            '当前时间': '14:30:00',
            '天气状态': '未知',
            '安全状态': '未知'
        }
        
        self.observatory_panel.update_all_status(status_data)
        self.log_panel.log_message("模拟断开连接")
        
    def validate_demo_config(self):
        """验证演示配置"""
        try:
            import yaml
            content = self.config_editor.get_content()
            config = yaml.safe_load(content)
            
            # 基本验证
            if 'targets' not in config:
                raise ValueError("配置缺少'targets'部分")
                
            self.log_panel.log_message("配置验证成功")
            
        except Exception as e:
            self.log_panel.log_message(f"配置验证失败: {e}", level="error")


def main():
    """演示程序主函数"""
    root = tk.Tk()
    app = GUIDemo(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("演示程序被用户中断")
    finally:
        print("GUI演示程序已关闭")


if __name__ == "__main__":
    main()