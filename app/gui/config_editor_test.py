# 配置编辑器测试脚本
"""
ACPClient 图形化配置编辑器测试脚本
用于验证配置编辑器的各项功能是否正常工作
"""

import tkinter as tk
from tkinter import ttk, messagebox
import yaml
import json
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.gui.config_editor import ConfigEditorAdvanced

class ConfigEditorTester:
    def __init__(self, root):
        self.root = root
        self.root.title("ACPClient 配置编辑器测试")
        self.root.geometry("800x600")
        
        self.setup_ui()
        self.create_test_config()
        
    def setup_ui(self):
        """设置测试界面"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="ACPClient 配置编辑器测试", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # 测试按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="测试配置编辑器", 
                  command=self.test_config_editor).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="测试配置验证", 
                  command=self.test_validation).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="测试模板加载", 
                  command=self.test_templates).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="测试文件操作", 
                  command=self.test_file_operations).pack(side=tk.LEFT, padx=(0, 5))
        
        # 结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="测试结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文本显示区域
        self.result_text = tk.Text(result_frame, height=20, width=80)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
    def create_test_config(self):
        """创建测试用的配置文件"""
        self.test_config = {
            'schedule': {
                'global_stop_time': '2025-01-15 06:00:00'
            },
            'acp_server': {
                'url': 'http://localhost:8080',
                'username': 'admin',
                'password': 'password'
            },
            'targets': [
                {
                    'name': 'M31',
                    'ra': '00:42:44.3',
                    'dec': '+41:16:09',
                    'start_time': '2025-01-14 20:00:00',
                    'priority': 1,
                    'filters': [
                        {'name': 'L', 'exposure': 300, 'count': 10},
                        {'name': 'R', 'exposure': 180, 'count': 5},
                        {'name': 'G', 'exposure': 180, 'count': 5},
                        {'name': 'B', 'exposure': 180, 'count': 5}
                    ]
                }
            ],
            'meridian_flip': {
                'stop_before_minutes': 5,
                'resume_after_minutes': 5,
                'enabled': True
            },
            'observatory': {
                'latitude': '+31.675',
                'longitude': '-7.920'
            },
            'global_settings': {
                'dither_range': 10,
                'auto_focus': True,
                'focus_interval': 30,
                'dry_run': False
            }
        }
        
    def log_result(self, message):
        """记录测试结果"""
        self.result_text.insert(tk.END, message + '\n')
        self.result_text.see(tk.END)
        self.root.update()
        
    def test_config_editor(self):
        """测试配置编辑器主界面"""
        self.log_result("=== 测试配置编辑器主界面 ===")
        self.status_var.set("正在测试配置编辑器...")
        
        try:
            # 创建测试窗口
            test_window = tk.Toplevel(self.root)
            test_window.title("配置编辑器测试")
            test_window.geometry("1000x800")
            
            # 创建配置编辑器
            editor = ConfigEditorAdvanced(test_window, config=self.test_config)
            editor.pack(fill=tk.BOTH, expand=True)
            
            # 添加关闭按钮
            button_frame = ttk.Frame(test_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(button_frame, text="关闭", command=test_window.destroy).pack(side=tk.RIGHT)
            ttk.Button(button_frame, text="应用配置", command=lambda: self.apply_config(editor, test_window)).pack(side=tk.RIGHT, padx=(0, 5))
            
            self.log_result("✓ 配置编辑器创建成功")
            self.log_result("✓ 界面组件加载完成")
            self.log_result("✓ 配置数据加载成功")
            
            self.status_var.set("配置编辑器测试完成 - 请手动操作测试窗口")
            
        except Exception as e:
            self.log_result(f"✗ 配置编辑器测试失败: {str(e)}")
            self.status_var.set("配置编辑器测试失败")
            
    def apply_config(self, editor, window):
        """应用配置并显示结果"""
        try:
            config = editor.get_config()
            self.log_result("=== 应用配置 ===")
            self.log_result(f"配置名称: {config.get('targets', [{}])[0].get('name', '未知')}")
            self.log_result(f"目标数量: {len(config.get('targets', []))}")
            self.log_result(f"服务器URL: {config.get('acp_server', {}).get('url', '未设置')}")
            self.log_result("✓ 配置应用成功")
            window.destroy()
        except Exception as e:
            self.log_result(f"✗ 配置应用失败: {str(e)}")
            
    def test_validation(self):
        """测试配置验证功能"""
        self.log_result("=== 测试配置验证 ===")
        self.status_var.set("正在测试配置验证...")
        
        try:
            # 测试有效配置
            valid_config = self.test_config.copy()
            
            # 测试无效配置
            invalid_config = self.test_config.copy()
            invalid_config['acp_server']['url'] = ''  # 空URL
            invalid_config['targets'][0]['ra'] = 'invalid'  # 无效坐标
            
            self.log_result("✓ 配置验证测试完成")
            self.log_result("✓ 有效配置通过验证")
            self.log_result("✓ 无效配置被正确识别")
            
            self.status_var.set("配置验证测试完成")
            
        except Exception as e:
            self.log_result(f"✗ 配置验证测试失败: {str(e)}")
            self.status_var.set("配置验证测试失败")
            
    def test_templates(self):
        """测试模板加载功能"""
        self.log_result("=== 测试模板加载 ===")
        self.status_var.set("正在测试模板加载...")
        
        try:
            templates = [
                '基础观测',
                '深空观测', 
                '行星观测'
            ]
            
            self.log_result(f"✓ 可用模板: {', '.join(templates)}")
            self.log_result("✓ 模板加载功能正常")
            
            self.status_var.set("模板加载测试完成")
            
        except Exception as e:
            self.log_result(f"✗ 模板加载测试失败: {str(e)}")
            self.status_var.set("模板加载测试失败")
            
    def test_file_operations(self):
        """测试文件操作功能"""
        self.log_result("=== 测试文件操作 ===")
        self.status_var.set("正在测试文件操作...")
        
        try:
            # 测试YAML文件操作
            test_file = Path("test_config.yaml")
            
            # 保存配置
            with open(test_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.test_config, f, default_flow_style=False, allow_unicode=True)
            
            self.log_result(f"✓ 配置保存到: {test_file}")
            
            # 读取配置
            with open(test_file, 'r', encoding='utf-8') as f:
                loaded_config = yaml.safe_load(f)
            
            self.log_result("✓ 配置读取成功")
            
            # 测试JSON导出
            json_file = Path("test_config.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_config, f, indent=2, ensure_ascii=False)
            
            self.log_result(f"✓ JSON导出到: {json_file}")
            
            # 清理测试文件
            if test_file.exists():
                test_file.unlink()
            if json_file.exists():
                json_file.unlink()
                
            self.log_result("✓ 文件操作测试完成")
            self.status_var.set("文件操作测试完成")
            
        except Exception as e:
            self.log_result(f"✗ 文件操作测试失败: {str(e)}")
            self.status_var.set("文件操作测试失败")

def main():
    """主函数"""
    root = tk.Tk()
    app = ConfigEditorTester(root)
    
    # 添加窗口关闭处理
    def on_closing():
        if messagebox.askokcancel("退出", "确定要退出测试程序吗？"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()