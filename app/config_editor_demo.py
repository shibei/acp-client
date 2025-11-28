#!/usr/bin/env python3
"""
配置编辑器演示程序
展示图形化配置编辑器的功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.gui.config_editor import ConfigEditorAdvanced


class ConfigEditorDemo:
    """配置编辑器演示类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ACPClient 配置编辑器演示")
        self.root.geometry("900x700")
        
        # 设置窗口样式
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        
        # 配置主题
        try:
            # 尝试使用clam主题
            style.theme_use('clam')
        except:
            pass
            
        # 自定义按钮样式
        style.configure('Accent.TButton', 
                       foreground='white', 
                       background='#007acc',
                       borderwidth=1,
                       focusthickness=3,
                       focuscolor='none')
        style.map('Accent.TButton',
                 background=[('active', '#005a9e')])
        
        style.configure('Info.TButton',
                       foreground='white',
                       background='#17a2b8',
                       borderwidth=1)
        style.map('Info.TButton',
                 background=[('active', '#138496')])
        
        style.configure('Success.TButton',
                       foreground='white',
                       background='#28a745',
                       borderwidth=1)
        style.map('Success.TButton',
                 background=[('active', '#218838')])
        
        style.configure('Warning.TButton',
                       foreground='white',
                       background='#ffc107',
                       borderwidth=1)
        style.map('Warning.TButton',
                 background=[('active', '#e0a800')])
        
        style.configure('Danger.TButton',
                       foreground='white',
                       background='#dc3545',
                       borderwidth=1)
        style.map('Danger.TButton',
                 background=[('active', '#c82333')])
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="ACPClient 图形化配置编辑器演示",
                               font=('Arial', 16, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="功能强大的图形化配置编辑工具",
                                  font=('Arial', 10))
        subtitle_label.pack()
        
        # 说明文本
        info_frame = ttk.LabelFrame(main_frame, text="功能介绍", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = """
本演示程序展示了ACPClient的图形化配置编辑器功能：

• 多标签页配置编辑界面
• 直观的观测目标管理
• 实时配置验证和错误提示
• 配置模板快速加载
• 图形化参数设置
• 导入/导出功能

主要特点：
✓ 用户友好的图形界面
✓ 智能输入验证
✓ 实时配置预览
✓ 模板化配置管理
✓ 支持多种配置格式
        """
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.pack()
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 演示按钮
        ttk.Button(button_frame, text="启动配置编辑器",
                  command=self.launch_editor,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="加载示例配置",
                  command=self.load_sample_config,
                  style="Success.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="创建新配置",
                  command=self.create_new_config,
                  style="Info.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="显示帮助",
                  command=self.show_help,
                  style="Warning.TButton").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="退出演示",
                  command=self.quit_demo,
                  style="Danger.TButton").pack(side=tk.RIGHT, padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建日志文本框
        self.log_text = tk.Text(log_frame, height=10, width=80)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # 配置日志标签
        self.log_text.tag_configure('info', foreground='black')
        self.log_text.tag_configure('success', foreground='green')
        self.log_text.tag_configure('warning', foreground='orange')
        self.log_text.tag_configure('error', foreground='red')
        self.log_text.tag_configure('highlight', background='yellow')
        
        # 初始日志
        self.log_message("配置编辑器演示程序已启动", "success")
        self.log_message("点击按钮开始体验图形化配置编辑功能", "info")
        
    def log_message(self, message, level="info"):
        """记录日志消息"""
        timestamp = self.get_timestamp()
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry, level)
        self.log_text.see(tk.END)
        
        # 更新状态栏
        self.status_var.set(message)
        
    def get_timestamp(self):
        """获取时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
        
    def launch_editor(self):
        """启动配置编辑器"""
        try:
            self.log_message("正在启动配置编辑器...", "info")
            
            # 创建编辑器窗口
            editor_window = tk.Toplevel(self.root)
            editor_window.title("ACPClient 图形化配置编辑器")
            editor_window.geometry("900x700")
            
            # 创建配置编辑器
            config_editor = ConfigEditorAdvanced(editor_window)
            config_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 设置窗口模态
            editor_window.transient(self.root)
            editor_window.grab_set()
            
            self.log_message("配置编辑器已成功启动", "success")
            
            # 等待编辑器窗口关闭
            self.root.wait_window(editor_window)
            
            self.log_message("配置编辑器已关闭", "info")
            
        except Exception as e:
            error_msg = f"启动配置编辑器失败: {e}"
            self.log_message(error_msg, "error")
            messagebox.showerror("错误", error_msg)
            
    def load_sample_config(self):
        """加载示例配置"""
        try:
            self.log_message("正在加载示例配置...", "info")
            
            # 创建示例配置
            sample_config = {
                'schedule': {
                    'stop_time': '2025-11-29 02:00:00'
                },
                'acp_server': {
                    'url': 'http://localhost:8080',
                    'username': 'admin',
                    'password': 'password'
                },
                'targets': [
                    {
                        'name': 'M 31 - 仙女座星系',
                        'ra': '00:42:44.33',
                        'dec': '+41:16:07.5',
                        'start_time': '2025-11-28 20:00:00',
                        'priority': 1,
                        'filters': [
                            {'filter_id': 0, 'name': 'L', 'exposure': 300, 'count': 10, 'binning': 1},
                            {'filter_id': 1, 'name': 'R', 'exposure': 300, 'count': 10, 'binning': 1},
                            {'filter_id': 2, 'name': 'G', 'exposure': 300, 'count': 10, 'binning': 1},
                            {'filter_id': 3, 'name': 'B', 'exposure': 300, 'count': 10, 'binning': 1}
                        ]
                    },
                    {
                        'name': 'NGC 1499 - 加利福尼亚星云',
                        'ra': '04:01:07.51',
                        'dec': '+36:31:11.9',
                        'start_time': '2025-11-28 22:00:00',
                        'priority': 2,
                        'filters': [
                            {'filter_id': 4, 'name': 'H-alpha', 'exposure': 600, 'count': 20, 'binning': 1},
                            {'filter_id': 6, 'name': 'OIII', 'exposure': 600, 'count': 20, 'binning': 1}
                        ]
                    }
                ],
                'meridian_flip': {
                    'stop_minutes_before': 10,
                    'resume_minutes_after': 10,
                    'safety_margin': 5
                },
                'observatory': {
                    'latitude': 39.9,
                    'longitude': 116.4
                },
                'global_settings': {
                    'dither': 5,
                    'auto_focus': True,
                    'af_interval': 120,
                    'dryrun': False
                }
            }
            
            # 创建编辑器窗口并加载配置
            editor_window = tk.Toplevel(self.root)
            editor_window.title("示例配置 - 图形化配置编辑器")
            editor_window.geometry("900x700")
            
            config_editor = ConfigEditorAdvanced(editor_window)
            config_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 加载示例配置
            config_editor.set_config_data(sample_config)
            
            # 设置窗口模态
            editor_window.transient(self.root)
            editor_window.grab_set()
            
            self.log_message("示例配置已成功加载", "success")
            self.log_message("配置包含: 2个观测目标, 多种滤镜设置", "info")
            
            # 等待编辑器窗口关闭
            self.root.wait_window(editor_window)
            
        except Exception as e:
            error_msg = f"加载示例配置失败: {e}"
            self.log_message(error_msg, "error")
            messagebox.showerror("错误", error_msg)
            
    def create_new_config(self):
        """创建新配置"""
        try:
            self.log_message("正在创建新配置...", "info")
            
            # 创建编辑器窗口
            editor_window = tk.Toplevel(self.root)
            editor_window.title("新建配置 - 图形化配置编辑器")
            editor_window.geometry("900x700")
            
            config_editor = ConfigEditorAdvanced(editor_window)
            config_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 设置窗口模态
            editor_window.transient(self.root)
            editor_window.grab_set()
            
            self.log_message("已创建新的空配置", "success")
            self.log_message("您可以使用图形界面创建新的观测配置", "info")
            
            # 等待编辑器窗口关闭
            self.root.wait_window(editor_window)
            
        except Exception as e:
            error_msg = f"创建新配置失败: {e}"
            self.log_message(error_msg, "error")
            messagebox.showerror("错误", error_msg)
            
    def show_help(self):
        """显示帮助信息"""
        help_text = """
ACPClient 图形化配置编辑器使用说明

功能概述：
图形化配置编辑器提供了一个直观、易用的界面来创建和编辑ACPClient的观测配置文件。

主要功能：

1. 多标签页编辑
   • 常规设置：全局停止时间配置
   • 服务器：ACP服务器连接信息
   • 观测目标：添加和管理观测目标
   • 中天反转：中天观测保护设置
   • 观测站：地理位置信息
   • 全局设置：成像参数设置

2. 观测目标管理
   • 添加新目标
   • 编辑现有目标
   • 删除目标
   • 目标优先级设置
   • 滤镜配置管理

3. 配置验证
   • 实时输入验证
   • 配置完整性检查
   • 错误提示和修复建议

4. 模板功能
   • 基础观测模板
   • 深空观测模板
   • 行星观测模板
   • 自定义模板保存

5. 文件操作
   • 新建配置
   • 打开现有配置
   • 保存配置
   • 另存为
   • 导出JSON格式

使用方法：
1. 点击"启动配置编辑器"打开编辑界面
2. 使用"加载示例配置"查看预设配置示例
3. 使用"创建新配置"从零开始创建配置
4. 在各个标签页中设置相应参数
5. 使用工具栏按钮保存和验证配置

提示：
• 修改配置后请及时保存
• 使用验证功能检查配置有效性
• 可以利用模板快速创建常用配置
• 支持拖拽和键盘快捷键操作
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("使用帮助")
        help_window.geometry("600x500")
        
        # 创建滚动文本框
        text_frame = ttk.Frame(help_window, padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text = tk.Text(text_frame, wrap=tk.WORD, padx=10, pady=10)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.configure(yscrollcommand=scrollbar.set)
        
        text.insert(1.0, help_text)
        text.config(state=tk.DISABLED)
        
        # 关闭按钮
        button_frame = ttk.Frame(help_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="关闭", command=help_window.destroy).pack()
        
        self.log_message("已显示帮助信息", "info")
        
    def quit_demo(self):
        """退出演示"""
        if messagebox.askyesno("确认", "确定要退出配置编辑器演示吗？"):
            self.log_message("正在退出演示程序...", "warning")
            self.root.quit()
            
    def run(self):
        """运行演示程序"""
        self.log_message("配置编辑器演示程序正在运行...", "success")
        
        # 居中窗口
        self.center_window()
        
        # 运行主循环
        self.root.mainloop()
        
    def center_window(self):
        """居中窗口"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")


def main():
    """主函数"""
    print("正在启动ACPClient配置编辑器演示程序...")
    
    try:
        demo = ConfigEditorDemo()
        demo.run()
        print("配置编辑器演示程序已正常退出")
        
    except KeyboardInterrupt:
        print("\n演示程序被用户中断")
        
    except Exception as e:
        print(f"演示程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()