"""
高级配置编辑器模块
提供图形化的配置编辑功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yaml
import json
from datetime import datetime
from pathlib import Path


class ConfigEditorAdvanced(ttk.Frame):
    """高级配置编辑器"""
    
    def __init__(self, parent, config_file=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.config_file = config_file
        self.config_data = {}
        self.is_modified = False
        self.setup_ui()
        
        if config_file:
            self.load_config_file(config_file)
    
    def setup_ui(self):
        """设置界面"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 顶部工具栏
        toolbar = self.create_toolbar(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # 创建标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个配置标签页
        self.create_general_tab()
        self.create_server_tab()
        self.create_targets_tab()
        self.create_meridian_tab()
        self.create_observatory_tab()
        self.create_global_tab()
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar = ttk.Frame(parent)
        
        # 文件操作按钮
        ttk.Button(toolbar, text="新建", command=self.new_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="打开", command=self.open_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="保存", command=self.save_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="另存为", command=self.save_config_as).pack(side=tk.LEFT, padx=2)
        
        # 分隔线
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 配置操作按钮
        ttk.Button(toolbar, text="验证配置", command=self.validate_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="加载模板", command=self.load_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出JSON", command=self.export_json).pack(side=tk.LEFT, padx=2)
        
        # 分隔线
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 帮助按钮
        ttk.Button(toolbar, text="帮助", command=self.show_help).pack(side=tk.LEFT, padx=2)
        
        return toolbar
        
    def create_general_tab(self):
        """创建常规配置标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="常规")
        
        # 全局停止时间
        ttk.Label(frame, text="全局停止时间:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.stop_time_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.stop_time_var, width=30).grid(row=0, column=1, pady=5, padx=5)
        ttk.Label(frame, text="格式: YYYY-MM-DD HH:MM:SS").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        
        # 配置信息
        info_frame = ttk.LabelFrame(frame, text="配置信息", padding="10")
        info_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.config_info_var = tk.StringVar(value="未加载配置文件")
        ttk.Label(info_frame, textvariable=self.config_info_var).pack(anchor=tk.W)
        
        # 快速操作按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="设置为当前时间", 
                  command=self.set_current_time).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除停止时间",
                  command=self.clear_stop_time).pack(side=tk.LEFT, padx=5)
        
    def create_server_tab(self):
        """创建服务器配置标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="服务器")
        
        # ACP服务器URL
        ttk.Label(frame, text="服务器URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.server_url_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.server_url_var, width=40).grid(row=0, column=1, pady=5, padx=5)
        
        # 用户名
        ttk.Label(frame, text="用户名:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.username_var, width=30).grid(row=1, column=1, pady=5, padx=5)
        
        # 密码
        ttk.Label(frame, text="密码:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.password_var, width=30, show="*").grid(row=2, column=1, pady=5, padx=5)
        
        # 连接测试按钮
        ttk.Button(frame, text="测试连接", command=self.test_connection).grid(row=3, column=0, columnspan=2, pady=10)
        
    def create_targets_tab(self):
        """创建目标配置标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="观测目标")
        
        # 目标列表框架
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 目标列表
        self.target_listbox = tk.Listbox(list_frame, height=8)
        self.target_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.target_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.target_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 按钮框架
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="添加目标", command=self.add_target).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="编辑目标", command=self.edit_target).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="删除目标", command=self.delete_target).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="上移", command=self.move_target_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="下移", command=self.move_target_down).pack(side=tk.LEFT, padx=2)
        
        # 绑定双击事件
        self.target_listbox.bind('<Double-Button-1>', lambda e: self.edit_target())
        
    def create_meridian_tab(self):
        """创建中天反转配置标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="中天反转")
        
        # 中天前停止时间
        ttk.Label(frame, text="中天前停止时间(分钟):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.stop_before_var = tk.IntVar(value=10)
        ttk.Spinbox(frame, from_=0, to=60, textvariable=self.stop_before_var, width=10).grid(row=0, column=1, pady=5, padx=5)
        
        # 中天后恢复时间
        ttk.Label(frame, text="中天后恢复时间(分钟):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.resume_after_var = tk.IntVar(value=10)
        ttk.Spinbox(frame, from_=0, to=60, textvariable=self.resume_after_var, width=10).grid(row=1, column=1, pady=5, padx=5)
        
        # 安全边距
        ttk.Label(frame, text="安全边距(分钟):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.safety_margin_var = tk.IntVar(value=5)
        ttk.Spinbox(frame, from_=0, to=30, textvariable=self.safety_margin_var, width=10).grid(row=2, column=1, pady=5, padx=5)
        
        # 说明信息
        info_frame = ttk.LabelFrame(frame, text="说明", padding="10")
        info_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        info_text = "中天反转功能会在天体通过中天时暂停观测，避免望远镜翻转。\n" \
                   "设置合适的时间可以保护设备并确保观测连续性。"
        ttk.Label(info_frame, text=info_text, wraplength=400).pack()
        
    def create_observatory_tab(self):
        """创建观测站配置标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="观测站")
        
        # 纬度
        ttk.Label(frame, text="纬度(度):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.latitude_var = tk.DoubleVar(value=39.9)
        ttk.Spinbox(frame, from_=-90, to=90, increment=0.1, textvariable=self.latitude_var, width=15).grid(row=0, column=1, pady=5, padx=5)
        
        # 经度
        ttk.Label(frame, text="经度(度):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.longitude_var = tk.DoubleVar(value=116.4)
        ttk.Spinbox(frame, from_=-180, to=180, increment=0.1, textvariable=self.longitude_var, width=15).grid(row=1, column=1, pady=5, padx=5)
        
        # 常用观测站按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="北京", command=lambda: self.set_observatory(39.9, 116.4)).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="上海", command=lambda: self.set_observatory(31.2, 121.5)).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="广州", command=lambda: self.set_observatory(23.1, 113.3)).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="成都", command=lambda: self.set_observatory(30.7, 104.1)).pack(side=tk.LEFT, padx=2)
        
    def create_global_tab(self):
        """创建全局设置标签页"""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="全局设置")
        
        # 抖动设置
        ttk.Label(frame, text="抖动范围(像素):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.dither_var = tk.IntVar(value=5)
        ttk.Spinbox(frame, from_=0, to=50, textvariable=self.dither_var, width=10).grid(row=0, column=1, pady=5, padx=5)
        
        # 自动对焦
        self.auto_focus_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="启用自动对焦", variable=self.auto_focus_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 对焦间隔
        ttk.Label(frame, text="对焦间隔(分钟):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.af_interval_var = tk.IntVar(value=120)
        ttk.Spinbox(frame, from_=0, to=600, textvariable=self.af_interval_var, width=10).grid(row=2, column=1, pady=5, padx=5)
        
        # 试运行模式
        self.dryrun_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="试运行模式(不实际执行观测)", variable=self.dryrun_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
    def load_config_file(self, filepath):
        """加载配置文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
                
            self.config_file = filepath
            self.update_ui_from_config()
            self.is_modified = False
            self.update_status(f"已加载配置文件: {Path(filepath).name}")
            
        except Exception as e:
            messagebox.showerror("加载失败", f"无法加载配置文件: {e}")
            
    def update_ui_from_config(self):
        """从配置数据更新UI"""
        # 常规设置
        if 'schedule' in self.config_data and 'stop_time' in self.config_data['schedule']:
            self.stop_time_var.set(self.config_data['schedule']['stop_time'])
        else:
            self.stop_time_var.set("")
            
        # 服务器设置
        if 'acp_server' in self.config_data:
            server = self.config_data['acp_server']
            self.server_url_var.set(server.get('url', ''))
            self.username_var.set(server.get('username', ''))
            self.password_var.set(server.get('password', ''))
            
        # 目标列表
        if 'targets' in self.config_data:
            self.update_target_list()
            
        # 中天反转设置
        if 'meridian_flip' in self.config_data:
            mf = self.config_data['meridian_flip']
            self.stop_before_var.set(mf.get('stop_minutes_before', 10))
            self.resume_after_var.set(mf.get('resume_minutes_after', 10))
            self.safety_margin_var.set(mf.get('safety_margin', 5))
            
        # 观测站设置
        if 'observatory' in self.config_data:
            obs = self.config_data['observatory']
            self.latitude_var.set(obs.get('latitude', 39.9))
            self.longitude_var.set(obs.get('longitude', 116.4))
            
        # 全局设置
        if 'global_settings' in self.config_data:
            gs = self.config_data['global_settings']
            self.dither_var.set(gs.get('dither', 5))
            self.auto_focus_var.set(gs.get('auto_focus', True))
            self.af_interval_var.set(gs.get('af_interval', 120))
            self.dryrun_var.set(gs.get('dryrun', False))
            
        # 更新配置信息
        self.update_config_info()
        
    def update_config_info(self):
        """更新配置信息显示"""
        if self.config_file:
            info = f"配置文件: {Path(self.config_file).name}\n"
            info += f"目标数量: {len(self.config_data.get('targets', []))}\n"
            info += f"最后修改: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            info = "未加载配置文件"
        self.config_info_var.set(info)
        
    def update_target_list(self):
        """更新目标列表显示"""
        self.target_listbox.delete(0, tk.END)
        
        if 'targets' in self.config_data:
            for i, target in enumerate(self.config_data['targets']):
                name = target.get('name', f'目标{i+1}')
                priority = target.get('priority', 0)
                filter_count = len(target.get('filters', []))
                display_text = f"{name} (优先级:{priority}, 滤镜:{filter_count})"
                self.target_listbox.insert(tk.END, display_text)
                
    def new_config(self):
        """新建配置"""
        if self.is_modified:
            if not messagebox.askyesno("确认", "当前配置有未保存的更改，确定要新建吗？"):
                return
                
        self.config_data = self.get_default_config()
        self.config_file = None
        self.update_ui_from_config()
        self.is_modified = False
        self.update_status("已创建新配置")
        
    def get_default_config(self):
        """获取默认配置"""
        return {
            'schedule': {'stop_time': ''},
            'acp_server': {
                'url': 'http://localhost:8080',
                'username': 'admin',
                'password': 'password'
            },
            'targets': [],
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
        
    def open_config(self):
        """打开配置文件"""
        if self.is_modified:
            if not messagebox.askyesno("确认", "当前配置有未保存的更改，确定要打开新文件吗？"):
                return
                
        filename = filedialog.askopenfilename(
            title="打开配置文件",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        
        if filename:
            self.load_config_file(filename)
            
    def save_config(self):
        """保存配置"""
        if not self.config_file:
            self.save_config_as()
            return
            
        try:
            self.update_config_from_ui()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
                
            self.is_modified = False
            self.update_status(f"配置已保存: {Path(self.config_file).name}")
            messagebox.showinfo("成功", "配置保存成功！")
            
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存配置文件: {e}")
            
    def save_config_as(self):
        """另存为"""
        filename = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        
        if filename:
            self.config_file = filename
            self.save_config()
            
    def update_config_from_ui(self):
        """从UI更新配置数据"""
        # 常规设置
        stop_time = self.stop_time_var.get().strip()
        if stop_time:
            self.config_data['schedule'] = {'stop_time': stop_time}
        else:
            self.config_data.pop('schedule', None)
            
        # 服务器设置
        self.config_data['acp_server'] = {
            'url': self.server_url_var.get().strip(),
            'username': self.username_var.get().strip(),
            'password': self.password_var.get().strip()
        }
        
        # 中天反转设置
        self.config_data['meridian_flip'] = {
            'stop_minutes_before': self.stop_before_var.get(),
            'resume_minutes_after': self.resume_after_var.get(),
            'safety_margin': self.safety_margin_var.get()
        }
        
        # 观测站设置
        self.config_data['observatory'] = {
            'latitude': self.latitude_var.get(),
            'longitude': self.longitude_var.get()
        }
        
        # 全局设置
        self.config_data['global_settings'] = {
            'dither': self.dither_var.get(),
            'auto_focus': self.auto_focus_var.get(),
            'af_interval': self.af_interval_var.get(),
            'dryrun': self.dryrun_var.get()
        }
        
    def validate_config(self):
        """验证配置"""
        try:
            self.update_config_from_ui()
            
            # 基本验证
            if not self.config_data.get('acp_server', {}).get('url'):
                raise ValueError("服务器URL不能为空")
                
            if not self.config_data.get('targets'):
                messagebox.showwarning("警告", "没有配置任何观测目标")
                
            # 验证目标数据
            for i, target in enumerate(self.config_data.get('targets', [])):
                if not target.get('name'):
                    raise ValueError(f"目标 {i+1} 缺少名称")
                if not target.get('ra') or not target.get('dec'):
                    raise ValueError(f"目标 {target.get('name', i+1)} 缺少坐标")
                if not target.get('filters'):
                    raise ValueError(f"目标 {target.get('name', i+1)} 没有配置滤镜")
                    
            messagebox.showinfo("验证成功", "配置验证通过！")
            self.update_status("配置验证通过")
            
        except Exception as e:
            messagebox.showerror("验证失败", str(e))
            
    def add_target(self):
        """添加目标"""
        dialog = TargetEditDialog(self, "添加观测目标")
        if dialog.result:
            if 'targets' not in self.config_data:
                self.config_data['targets'] = []
            self.config_data['targets'].append(dialog.result)
            self.update_target_list()
            self.is_modified = True
            self.update_status(f"已添加目标: {dialog.result['name']}")
            
    def edit_target(self):
        """编辑目标"""
        selection = self.target_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个目标")
            return
            
        index = selection[0]
        target = self.config_data['targets'][index]
        
        dialog = TargetEditDialog(self, "编辑观测目标", target)
        if dialog.result:
            self.config_data['targets'][index] = dialog.result
            self.update_target_list()
            self.is_modified = True
            self.update_status(f"已更新目标: {dialog.result['name']}")
            
    def delete_target(self):
        """删除目标"""
        selection = self.target_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个目标")
            return
            
        index = selection[0]
        target_name = self.config_data['targets'][index].get('name', f'目标{index+1}')
        
        if messagebox.askyesno("确认", f"确定要删除目标 '{target_name}' 吗？"):
            del self.config_data['targets'][index]
            self.update_target_list()
            self.is_modified = True
            self.update_status(f"已删除目标: {target_name}")
            
    def move_target_up(self):
        """上移目标"""
        selection = self.target_listbox.curselection()
        if not selection or selection[0] == 0:
            return
            
        index = selection[0]
        self.config_data['targets'][index], self.config_data['targets'][index-1] = \
            self.config_data['targets'][index-1], self.config_data['targets'][index]
        
        self.update_target_list()
        self.target_listbox.selection_set(index-1)
        self.is_modified = True
        
    def move_target_down(self):
        """下移目标"""
        selection = self.target_listbox.curselection()
        if not selection or selection[0] >= len(self.config_data['targets']) - 1:
            return
            
        index = selection[0]
        self.config_data['targets'][index], self.config_data['targets'][index+1] = \
            self.config_data['targets'][index+1], self.config_data['targets'][index]
        
        self.update_target_list()
        self.target_listbox.selection_set(index+1)
        self.is_modified = True
        
    def set_current_time(self):
        """设置为当前时间"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.stop_time_var.set(current_time)
        self.is_modified = True
        
    def clear_stop_time(self):
        """清除停止时间"""
        self.stop_time_var.set("")
        self.is_modified = True
        
    def test_connection(self):
        """测试连接"""
        url = self.server_url_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not url:
            messagebox.showwarning("警告", "请输入服务器URL")
            return
            
        self.update_status("正在测试连接...")
        
        # 这里可以添加实际的连接测试逻辑
        # 现在只是模拟
        self.after(1000, lambda: self.update_status("连接测试完成（模拟）"))
        
    def set_observatory(self, lat, lon):
        """设置观测站坐标"""
        self.latitude_var.set(lat)
        self.longitude_var.set(lon)
        self.is_modified = True
        
    def load_template(self):
        """加载模板"""
        templates = {
            "基础观测": self.get_basic_template(),
            "深空观测": self.get_deep_space_template(),
            "行星观测": self.get_planetary_template()
        }
        
        template_window = tk.Toplevel(self)
        template_window.title("选择模板")
        template_window.geometry("300x200")
        
        ttk.Label(template_window, text="选择配置模板:").pack(pady=10)
        
        listbox = tk.Listbox(template_window, height=5)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for template in templates.keys():
            listbox.insert(tk.END, template)
            
        def load_selected():
            selection = listbox.curselection()
            if selection:
                template_name = listbox.get(selection[0])
                self.config_data = templates[template_name]
                self.update_ui_from_config()
                self.is_modified = True
                template_window.destroy()
                self.update_status(f"已加载模板: {template_name}")
                
        ttk.Button(template_window, text="加载", command=load_selected).pack(pady=10)
        
    def get_basic_template(self):
        """获取基础观测模板"""
        return {
            'acp_server': {
                'url': 'http://localhost:8080',
                'username': 'admin',
                'password': 'password'
            },
            'targets': [
                {
                    'name': 'M 31',
                    'ra': '00:42:44.33',
                    'dec': '+41:16:07.5',
                    'start_time': '2025-11-28 20:00:00',
                    'priority': 1,
                    'filters': [
                        {'filter_id': 0, 'name': 'L', 'exposure': 300, 'count': 10, 'binning': 1}
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
        
    def get_deep_space_template(self):
        """获取深空观测模板"""
        return {
            'schedule': {'stop_time': '2025-11-29 02:00:00'},
            'acp_server': {
                'url': 'http://localhost:8080',
                'username': 'admin',
                'password': 'password'
            },
            'targets': [
                {
                    'name': 'NGC 1499',
                    'ra': '04:01:07.51',
                    'dec': '+36:31:11.9',
                    'start_time': '2025-11-28 22:00:00',
                    'priority': 1,
                    'filters': [
                        {'filter_id': 4, 'name': 'H-alpha', 'exposure': 600, 'count': 20, 'binning': 1},
                        {'filter_id': 6, 'name': 'OIII', 'exposure': 600, 'count': 20, 'binning': 1},
                        {'filter_id': 5, 'name': 'SII', 'exposure': 600, 'count': 20, 'binning': 1}
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
                'af_interval': 60,
                'dryrun': False
            }
        }
        
    def get_planetary_template(self):
        """获取行星观测模板"""
        return {
            'acp_server': {
                'url': 'http://localhost:8080',
                'username': 'admin',
                'password': 'password'
            },
            'targets': [
                {
                    'name': '木星',
                    'ra': '21:00:00',
                    'dec': '-15:00:00',
                    'start_time': '2025-11-28 21:00:00',
                    'priority': 1,
                    'filters': [
                        {'filter_id': 0, 'name': 'L', 'exposure': 30, 'count': 100, 'binning': 1}
                    ]
                }
            ],
            'meridian_flip': {
                'stop_minutes_before': 5,
                'resume_minutes_after': 5,
                'safety_margin': 2
            },
            'observatory': {
                'latitude': 39.9,
                'longitude': 116.4
            },
            'global_settings': {
                'dither': 2,
                'auto_focus': False,
                'af_interval': 0,
                'dryrun': False
            }
        }
        
    def export_json(self):
        """导出为JSON格式"""
        filename = filedialog.asksaveasfilename(
            title="导出JSON配置",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.update_config_from_ui()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.config_data, f, indent=2, ensure_ascii=False)
                    
                messagebox.showinfo("成功", "配置已导出为JSON格式！")
                self.update_status(f"已导出JSON配置: {Path(filename).name}")
                
            except Exception as e:
                messagebox.showerror("导出失败", str(e))
                
    def show_help(self):
        """显示帮助信息"""
        help_text = """
配置编辑器使用说明：

1. 文件操作：
   - 新建：创建新的配置文件
   - 打开：打开现有配置文件
   - 保存：保存当前配置
   - 另存为：保存到新文件

2. 配置内容：
   - 常规：全局停止时间设置
   - 服务器：ACP服务器连接信息
   - 观测目标：添加和管理观测目标
   - 中天反转：中天观测保护设置
   - 观测站：地理位置信息
   - 全局设置：成像参数设置

3. 目标管理：
   - 添加目标：添加新的观测目标
   - 编辑目标：修改选中目标
   - 删除目标：删除选中目标
   - 双击目标：快速编辑目标

4. 其他功能：
   - 验证配置：检查配置有效性
   - 加载模板：使用预设模板
   - 导出JSON：导出为JSON格式
   - 测试连接：测试服务器连接

提示：修改配置后请及时保存！
        """
        
        help_window = tk.Toplevel(self)
        help_window.title("使用帮助")
        help_window.geometry("500x400")
        
        text = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(1.0, help_text)
        text.config(state=tk.DISABLED)
        
    def update_status(self, message):
        """更新状态栏"""
        self.status_var.set(message)
        
    def get_config_data(self):
        """获取配置数据"""
        self.update_config_from_ui()
        return self.config_data
        
    def set_config_data(self, config_data):
        """设置配置数据"""
        self.config_data = config_data.copy()
        self.update_ui_from_config()
        self.is_modified = True


class TargetEditDialog(tk.Toplevel):
    """目标编辑对话框"""
    
    def __init__(self, parent, title, target_data=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x600")
        self.result = None
        
        # 设置模态
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        if target_data:
            self.load_target_data(target_data)
            
        # 居中显示
        self.center_window()
        
        # 等待窗口关闭
        self.wait_window()
        
    def center_window(self):
        """居中窗口"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_ui(self):
        """设置界面"""
        # 主框架
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 基本信息
        basic_frame = ttk.LabelFrame(main_frame, text="基本信息", padding="10")
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 目标名称
        ttk.Label(basic_frame, text="目标名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5, padx=5)
        
        # 坐标
        ttk.Label(basic_frame, text="赤经(RA):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ra_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.ra_var, width=20).grid(row=1, column=1, pady=5, padx=5)
        ttk.Label(basic_frame, text="格式: HH:MM:SS").grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(basic_frame, text="赤纬(DEC):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.dec_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.dec_var, width=20).grid(row=2, column=1, pady=5, padx=5)
        ttk.Label(basic_frame, text="格式: +/-DD:MM:SS").grid(row=2, column=2, sticky=tk.W, pady=5, padx=5)
        
        # 开始时间
        ttk.Label(basic_frame, text="开始时间:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.start_time_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.start_time_var, width=20).grid(row=3, column=1, pady=5, padx=5)
        ttk.Label(basic_frame, text="格式: YYYY-MM-DD HH:MM:SS").grid(row=3, column=2, sticky=tk.W, pady=5, padx=5)
        
        # 优先级
        ttk.Label(basic_frame, text="优先级:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.priority_var = tk.IntVar(value=1)
        ttk.Spinbox(basic_frame, from_=1, to=10, textvariable=self.priority_var, width=10).grid(row=4, column=1, pady=5, padx=5)
        
        # 滤镜配置
        filter_frame = ttk.LabelFrame(main_frame, text="滤镜配置", padding="10")
        filter_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 滤镜列表
        list_frame = ttk.Frame(filter_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.filter_listbox = tk.Listbox(list_frame, height=6)
        self.filter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.filter_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.filter_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 滤镜按钮
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="添加滤镜", command=self.add_filter).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="编辑滤镜", command=self.edit_filter).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="删除滤镜", command=self.delete_filter).pack(side=tk.LEFT, padx=2)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
        # 常用目标按钮
        common_frame = ttk.LabelFrame(main_frame, text="常用目标", padding="10")
        common_frame.pack(fill=tk.X, pady=(0, 10))
        
        common_targets = [
            ("M 31", "00:42:44.33", "+41:16:07.5"),
            ("M 33", "01:33:50.89", "+30:39:35.8"),
            ("NGC 1499", "04:01:07.51", "+36:31:11.9"),
            ("M 42", "05:35:17.3", "-05:23:28"),
            ("M 45", "03:47:24", "+24:07:00")
        ]
        
        for name, ra, dec in common_targets:
            ttk.Button(common_frame, text=name, 
                      command=lambda n=name, r=ra, d=dec: self.set_common_target(n, r, d)).pack(side=tk.LEFT, padx=2)
        
    def load_target_data(self, target_data):
        """加载目标数据"""
        self.name_var.set(target_data.get('name', ''))
        self.ra_var.set(target_data.get('ra', ''))
        self.dec_var.set(target_data.get('dec', ''))
        self.start_time_var.set(target_data.get('start_time', ''))
        self.priority_var.set(target_data.get('priority', 1))
        
        # 加载滤镜
        self.filter_listbox.delete(0, tk.END)
        for filter_data in target_data.get('filters', []):
            display_text = f"{filter_data.get('name', 'Unknown')}: " \
                          f"ID={filter_data.get('filter_id', 0)}, " \
                          f"曝光={filter_data.get('exposure', 0)}s, " \
                          f"数量={filter_data.get('count', 0)}, " \
                          f"合并={filter_data.get('binning', 1)}x"
            self.filter_listbox.insert(tk.END, display_text)
            
    def set_common_target(self, name, ra, dec):
        """设置常用目标"""
        self.name_var.set(name)
        self.ra_var.set(ra)
        self.dec_var.set(dec)
        
    def add_filter(self):
        """添加滤镜"""
        dialog = FilterEditDialog(self, "添加滤镜")
        if dialog.result:
            display_text = f"{dialog.result['name']}: ID={dialog.result['filter_id']}, " \
                          f"曝光={dialog.result['exposure']}s, 数量={dialog.result['count']}, " \
                          f"合并={dialog.result['binning']}x"
            self.filter_listbox.insert(tk.END, display_text)
            
    def edit_filter(self):
        """编辑滤镜"""
        selection = self.filter_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个滤镜")
            return
            
        # 这里可以添加滤镜编辑对话框
        messagebox.showinfo("提示", "滤镜编辑功能开发中...")
        
    def delete_filter(self):
        """删除滤镜"""
        selection = self.filter_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个滤镜")
            return
            
        self.filter_listbox.delete(selection[0])
        
    def ok(self):
        """确定按钮"""
        # 验证输入
        if not self.name_var.get().strip():
            messagebox.showerror("错误", "目标名称不能为空")
            return
            
        if not self.ra_var.get().strip() or not self.dec_var.get().strip():
            messagebox.showerror("错误", "坐标不能为空")
            return
            
        if self.filter_listbox.size() == 0:
            messagebox.showerror("错误", "至少需要配置一个滤镜")
            return
            
        # 构建结果数据
        self.result = {
            'name': self.name_var.get().strip(),
            'ra': self.ra_var.get().strip(),
            'dec': self.dec_var.get().strip(),
            'start_time': self.start_time_var.get().strip(),
            'priority': self.priority_var.get(),
            'filters': []  # 这里应该包含实际的滤镜数据
        }
        
        self.destroy()
        
    def cancel(self):
        """取消按钮"""
        self.destroy()


class FilterEditDialog(tk.Toplevel):
    """滤镜编辑对话框"""
    
    def __init__(self, parent, title, filter_data=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x300")
        self.result = None
        
        # 设置模态
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        if filter_data:
            self.load_filter_data(filter_data)
            
        # 等待窗口关闭
        self.wait_window()
        
    def setup_ui(self):
        """设置界面"""
        # 主框架
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滤镜ID
        ttk.Label(main_frame, text="滤镜ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.filter_id_var = tk.IntVar()
        ttk.Spinbox(main_frame, from_=0, to=20, textvariable=self.filter_id_var, width=10).grid(row=0, column=1, pady=5, padx=5)
        
        # 滤镜名称
        ttk.Label(main_frame, text="滤镜名称:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=20).grid(row=1, column=1, pady=5, padx=5)
        
        # 曝光时间
        ttk.Label(main_frame, text="曝光时间(秒):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.exposure_var = tk.IntVar(value=300)
        ttk.Spinbox(main_frame, from_=1, to=3600, textvariable=self.exposure_var, width=10).grid(row=2, column=1, pady=5, padx=5)
        
        # 拍摄数量
        ttk.Label(main_frame, text="拍摄数量:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.count_var = tk.IntVar(value=10)
        ttk.Spinbox(main_frame, from_=1, to=1000, textvariable=self.count_var, width=10).grid(row=3, column=1, pady=5, padx=5)
        
        # 合并模式
        ttk.Label(main_frame, text="合并模式:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.binning_var = tk.IntVar(value=1)
        ttk.Spinbox(main_frame, from_=1, to=4, textvariable=self.binning_var, width=10).grid(row=4, column=1, pady=5, padx=5)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
    def load_filter_data(self, filter_data):
        """加载滤镜数据"""
        self.filter_id_var.set(filter_data.get('filter_id', 0))
        self.name_var.set(filter_data.get('name', ''))
        self.exposure_var.set(filter_data.get('exposure', 300))
        self.count_var.set(filter_data.get('count', 10))
        self.binning_var.set(filter_data.get('binning', 1))
        
    def ok(self):
        """确定按钮"""
        self.result = {
            'filter_id': self.filter_id_var.get(),
            'name': self.name_var.get().strip(),
            'exposure': self.exposure_var.get(),
            'count': self.count_var.get(),
            'binning': self.binning_var.get()
        }
        self.destroy()
        
    def cancel(self):
        """取消按钮"""
        self.destroy()