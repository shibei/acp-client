
from tkinter import messagebox, ttk
from typing import Dict, List


class FilterConfigPanel(ttk.LabelFrame):
    """滤镜配置面板"""
    
    def __init__(self, parent):
        super().__init__(parent, text="滤镜配置", padding=5)
        self.filter_configs: List[Dict] = []
        self._create_widgets()
        
    def _create_widgets(self):
        """创建组件"""
        # 滤镜列表显示区域
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="x", pady=5)
        
        columns = ("滤镜ID", "数量", "曝光(秒)", "像素合并")
        self.filter_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=4)
        
        for col in columns:
            self.filter_tree.heading(col, text=col)
            self.filter_tree.column(col, width=100, anchor="center")
        
        self.filter_tree.pack(side="left", fill="x", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.filter_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.filter_tree.configure(yscrollcommand=scrollbar.set)
        
        # 添加/编辑滤镜区域
        self._create_input_widgets()
        
        # 按钮区域
        self._create_buttons()
        
    def _create_input_widgets(self):
        """创建输入组件"""
        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", pady=5)
        
        ttk.Label(input_frame, text="滤镜ID:").grid(row=0, column=0, padx=5)
        self.filter_id_entry = ttk.Entry(input_frame, width=10)
        self.filter_id_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="数量:").grid(row=0, column=2, padx=5)
        self.filter_count_entry = ttk.Entry(input_frame, width=10)
        self.filter_count_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(input_frame, text="曝光(秒):").grid(row=0, column=4, padx=5)
        self.filter_exposure_entry = ttk.Entry(input_frame, width=10)
        self.filter_exposure_entry.grid(row=0, column=5, padx=5)
        
        ttk.Label(input_frame, text="像素合并:").grid(row=0, column=6, padx=5)
        self.filter_binning_entry = ttk.Entry(input_frame, width=10)
        self.filter_binning_entry.grid(row=0, column=7, padx=5)
        
    def _create_buttons(self):
        """创建按钮"""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=5)
        
        ttk.Button(button_frame, text="添加滤镜", command=self.add_filter).pack(side="left", padx=5)
        ttk.Button(button_frame, text="删除选中", command=self.remove_filter).pack(side="left", padx=5)
        ttk.Button(button_frame, text="清空全部", command=self.clear_filters).pack(side="left", padx=5)
        
    def add_filter(self):
        """添加滤镜配置"""
        try:
            filter_id = int(self.filter_id_entry.get())
            count = int(self.filter_count_entry.get())
            exposure = int(self.filter_exposure_entry.get())
            binning = int(self.filter_binning_entry.get())
            
            filter_config = {
                'filter_id': filter_id,
                'count': count,
                'exposure': exposure,
                'binning': binning
            }
            self.filter_configs.append(filter_config)
            self.filter_tree.insert('', 'end', values=(filter_id, count, exposure, binning))
            
            # 清空输入框
            for entry in [self.filter_id_entry, self.filter_count_entry, 
                         self.filter_exposure_entry, self.filter_binning_entry]:
                entry.delete(0, 'end')
                
            return True
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
            return False
            
    def remove_filter(self):
        """删除选中的滤镜配置"""
        selected = self.filter_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的滤镜配置")
            return
            
        for item in selected:
            index = self.filter_tree.index(item)
            self.filter_tree.delete(item)
            del self.filter_configs[index]
            
    def clear_filters(self):
        """清空所有滤镜配置"""
        for item in self.filter_tree.get_children():
            self.filter_tree.delete(item)
        self.filter_configs.clear()
        
    def get_filters(self) -> List[Dict]:
        """获取滤镜配置列表"""
        return self.filter_configs
    
    def add_default_filters(self):
        """添加默认滤镜配置"""
        default_filters = [
            {'filter_id': 0, 'count': 10, 'exposure': 600, 'binning': 1},
            {'filter_id': 1, 'count': 6, 'exposure': 600, 'binning': 1},
        ]
        
        for f in default_filters:
            self.filter_configs.append(f)
            self.filter_tree.insert('', 'end', values=(f['filter_id'], f['count'], f['exposure'], f['binning']))


class ImagingPlanPanel(ttk.LabelFrame):
    """成像计划面板"""
    
    def __init__(self, parent):
        super().__init__(parent, text="成像计划", padding=10)
        self._create_widgets()
        self._set_defaults()
        
    def _create_widgets(self):
        """创建组件"""
        # 目标信息
        self._create_target_inputs()
        
        # 滤镜配置
        self.filter_panel = FilterConfigPanel(self)
        self.filter_panel.pack(fill="x", pady=5)
        
        # 其他参数
        self._create_parameter_inputs()
        
    def _create_target_inputs(self):
        """创建目标输入区域"""
        target_frame = ttk.Frame(self)
        target_frame.pack(fill="x", pady=5)
        
        fields = [
            ("目标:", "target_entry", 15),
            ("RA:", "ra_entry", 15),
            ("DEC:", "dec_entry", 15)
        ]
        
        for col, (label, attr, width) in enumerate(fields):
            ttk.Label(target_frame, text=label).grid(row=0, column=col*2, sticky="w", padx=5)
            entry = ttk.Entry(target_frame, width=width)
            entry.grid(row=0, column=col*2+1, padx=5)
            setattr(self, attr, entry)
            
    def _create_parameter_inputs(self):
        """创建参数输入区域"""
        param_frame = ttk.Frame(self)
        param_frame.pack(fill="x", pady=5)
        
        ttk.Label(param_frame, text="抖动(像素):").grid(row=0, column=0, sticky="w", padx=5)
        self.dither_entry = ttk.Entry(param_frame, width=10)
        self.dither_entry.grid(row=0, column=1, padx=5)
        
        self.autofocus_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            param_frame, text="自动对焦", 
            variable=self.autofocus_var
        ).grid(row=0, column=2, padx=5)
        
        ttk.Label(param_frame, text="对焦间隔(分钟):").grid(row=0, column=3, sticky="w", padx=5)
        self.af_interval_entry = ttk.Entry(param_frame, width=10)
        self.af_interval_entry.grid(row=0, column=4, padx=5)
        
    def _set_defaults(self):
        """设置默认值"""
        self.target_entry.insert(0, "M 31")
        self.ra_entry.insert(0, "00:42:42.12")
        self.dec_entry.insert(0, "41:16:01.2")
        self.dither_entry.insert(0, "5")
        self.af_interval_entry.insert(0, "120")
        
        self.filter_panel.add_default_filters()
        
    def get_plan_config(self) -> dict:
        """获取成像计划配置"""
        return {
            'target': self.target_entry.get().strip(),
            'ra': self.ra_entry.get().strip(),
            'dec': self.dec_entry.get().strip(),
            'filters': self.filter_panel.get_filters(),
            'dither': int(self.dither_entry.get()),
            'auto_focus': self.autofocus_var.get(),
            'periodic_af_interval': int(self.af_interval_entry.get())
        }
