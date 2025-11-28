import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from ACP.ACPlib import ACPClient, ImagingPlan
import threading
import json
import logging
import requests
from datetime import datetime, timedelta
from urllib.parse import unquote as url_decode
from typing import Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass, asdict
import queue


@dataclass
class ScheduledTarget:
    """计划目标 - 带时间的成像任务"""
    name: str
    start_time: datetime
    plan_config: dict
    status: str = "等待中"  # 等待中、执行中、已完成、已跳过
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'name': self.name,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'plan_config': self.plan_config,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScheduledTarget':
        """从字典创建"""
        return cls(
            name=data['name'],
            start_time=datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S'),
            plan_config=data['plan_config'],
            status=data.get('status', '等待中')
        )


class LogManager:
    """日志管理器"""
    
    LOG_DIR = Path("logs")
    
    def __init__(self, name: str = 'ACPClient'):
        self.LOG_DIR.mkdir(exist_ok=True)
        self.logger = self._setup_logger(name)
        
    def _setup_logger(self, name: str) -> logging.Logger:
        """设置日志系统"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        if logger.handlers:
            logger.handlers.clear()
        
        # 文件处理器
        log_file = self.LOG_DIR / f"acp_client_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # 统一格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str):
        self.logger.info(message)
    
    def debug(self, message: str):
        self.logger.debug(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        self.logger.error(message, exc_info=exc_info)


class ConnectionPanel(ttk.LabelFrame):
    """连接配置面板"""
    
    DEFAULT_URL = "http://27056t89i6.wicp.vip:1011"
    DEFAULT_USER = "share"
    DEFAULT_PWD = "1681"
    
    def __init__(self, parent, on_connect, on_status_check):
        super().__init__(parent, text="连接配置", padding=10)
        self.on_connect = on_connect
        self.on_status_check = on_status_check
        self._create_widgets()
        self._set_defaults()
        
    def _create_widgets(self):
        """创建组件"""
        # 服务器配置
        ttk.Label(self, text="服务器地址:").grid(row=0, column=0, sticky="w", padx=5)
        self.url_entry = ttk.Entry(self, width=40)
        self.url_entry.grid(row=0, column=1, padx=5)
        
        # 认证信息
        ttk.Label(self, text="用户名:").grid(row=1, column=0, sticky="w", padx=5)
        self.user_entry = ttk.Entry(self, width=20)
        self.user_entry.grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(self, text="密码:").grid(row=1, column=2, sticky="w", padx=5)
        self.pwd_entry = ttk.Entry(self, width=20, show="*")
        self.pwd_entry.grid(row=1, column=3, sticky="w", padx=5)
        
        # 控制按钮
        self.connect_btn = ttk.Button(self, text="连接", command=self.on_connect)
        self.connect_btn.grid(row=0, column=2, padx=5)
        
        self.status_btn = ttk.Button(
            self, text="检查状态", 
            command=self.on_status_check, state="disabled"
        )
        self.status_btn.grid(row=0, column=3, padx=5)
        
    def _set_defaults(self):
        """设置默认值"""
        self.url_entry.insert(0, self.DEFAULT_URL)
        self.user_entry.insert(0, self.DEFAULT_USER)
        self.pwd_entry.insert(0, self.DEFAULT_PWD)
        
    def get_connection_info(self) -> tuple:
        """获取连接信息"""
        return (
            self.url_entry.get().strip(),
            self.user_entry.get().strip(),
            self.pwd_entry.get()
        )
    
    def set_connected_state(self, connected: bool):
        """设置连接状态"""
        state = "normal" if connected else "disabled"
        self.status_btn.config(state=state)


class StatusPanel(ttk.LabelFrame):
    """状态显示面板"""
    
    def __init__(self, parent):
        super().__init__(parent, text="系统状态", padding=10)
        self._create_widgets()
        
    def _create_widgets(self):
        """创建组件"""
        self.status_text = scrolledtext.ScrolledText(self, height=10, width=80)
        self.status_text.pack(fill="both", expand=True)
        
    def log(self, message: str, level: str = 'INFO'):
        """记录日志到文本框"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_msg = f"[{timestamp}] {level}: {message}\n"
        self.status_text.insert('end', formatted_msg)
        self.status_text.see('end')
        
    def clear(self):
        """清空日志"""
        self.status_text.delete('1.0', 'end')


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


class StatusMonitor:
    """状态监控器"""
    
    MONITOR_INTERVAL = 5  # 秒
    
    def __init__(self, client: ACPClient, status_callback, log_manager: LogManager):
        self.client = client
        self.status_callback = status_callback
        self.log_manager = log_manager
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
    def start(self):
        """开始监控"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.shutdown_event.clear()
        self.log_manager.info("开始监控模式")
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop(self):
        """停止监控"""
        if not self.monitoring:
            return
            
        self.monitoring = False
        self.shutdown_event.set()
        self.log_manager.info("停止监控模式")
        
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring and not self.shutdown_event.is_set():
            try:
                self.status_callback()
                self.shutdown_event.wait(self.MONITOR_INTERVAL)
            except Exception as e:
                self.log_manager.error(f"监控循环出错: {str(e)}", exc_info=True)
                
    def is_monitoring(self) -> bool:
        """是否正在监控"""
        return self.monitoring


class ACPClientGUI:
    """ACP客户端图形界面 - 主控制器"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ACP Client 控制面板")
        self.root.geometry("900x800")
        
        self.client: Optional[ACPClient] = None
        self.log_manager = LogManager()
        self.monitor: Optional[StatusMonitor] = None
        
        self.log_manager.info("应用程序启动")
        
        self._create_ui()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def _create_ui(self):
        """创建UI"""
        # 连接配置面板
        self.connection_panel = ConnectionPanel(
            self.root, 
            self.connect, 
            self.check_status
        )
        self.connection_panel.pack(fill="x", padx=10, pady=5)
        
        # 状态显示面板
        self.status_panel = StatusPanel(self.root)
        self.status_panel.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 成像计划面板
        self.plan_panel = ImagingPlanPanel(self.root)
        self.plan_panel.pack(fill="x", padx=10, pady=5)
        
        # 控制按钮
        self._create_control_buttons()
        
    def _create_control_buttons(self):
        """创建控制按钮"""
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_btn = ttk.Button(
            control_frame, text="启动成像计划", 
            command=self.start_imaging, state="disabled"
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.monitor_btn = ttk.Button(
            control_frame, text="开始监控", 
            command=self.toggle_monitoring, state="disabled"
        )
        self.monitor_btn.pack(side="left", padx=5)
        
        ttk.Button(
            control_frame, text="清除日志", 
            command=self.clear_log
        ).pack(side="left", padx=5)
        
    def connect(self):
        """连接到ACP服务器"""
        try:
            self.log_manager.info("开始连接到ACP服务器")
            self.status_panel.log("正在连接...", "INFO")
            
            url, user, pwd = self.connection_panel.get_connection_info()
            
            if not all([url, user, pwd]):
                raise ValueError("服务器地址、用户名和密码不能为空")
            
            self.log_manager.debug(f"连接参数 - URL: {url}, User: {user}")
            
            self.client = ACPClient(url, user, pwd)
            self.monitor = StatusMonitor(self.client, self.check_status, self.log_manager)
            
            self.log_manager.info("成功连接到ACP服务器")
            self.status_panel.log("✓ 连接成功", "SUCCESS")
            
            self._set_connected_state(True)
            
            messagebox.showinfo("成功", "连接成功!")
            self.root.title(f"{self.client.title} 控制面板")
            
        except ValueError as e:
            self.log_manager.error(f"输入验证失败: {str(e)}")
            self.status_panel.log(f"✗ {str(e)}", "ERROR")
            messagebox.showerror("错误", str(e))
        except Exception as e:
            self.log_manager.error(f"连接失败: {str(e)}", exc_info=True)
            self.status_panel.log(f"✗ 连接失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"连接失败: {str(e)}")
            
    def _set_connected_state(self, connected: bool):
        """设置连接状态"""
        self.connection_panel.set_connected_state(connected)
        state = "normal" if connected else "disabled"
        self.start_btn.config(state=state)
        self.monitor_btn.config(state=state)
        
    def check_status(self):
        """检查系统状态"""
        if not self.client:
            self.log_manager.warning("尝试检查状态但客户端未连接")
            return
            
        try:
            self.log_manager.debug("开始检查系统状态")
            status = self.client.get_system_status()
            
            # 清除之前的状态显示
            self.status_panel.clear()
            
            # 格式化并显示状态信息
            status_items = [
                ("本地时间", status.local_time),
                ("UTC时间", status.utc_time),
                ("天文台状态", status.observatory_status),
                ("所有者", status.owner),
                ("望远镜状态", status.telescope_status),
                ("相机状态", status.camera_status),
                ("导星状态", status.guider_status),
                ("当前位置", f"RA={url_decode(status.current_ra[3:])}, Dec={url_decode(status.current_dec[3:])}"),
                ("高度方位", f"Alt={url_decode(status.current_alt[3:])}, Az={url_decode(status.current_az[3:])}"),
                ("滤镜", status.image_filter),
                ("相机温度", status.image_temperature),
                ("计划进度", status.plan_progress),
                ("最后FWHM", status.last_fwhm),
            ]
            
            for label, value in status_items:
                decoded_value = url_decode(value[3:]) if isinstance(value, str) and value.startswith('%3D') else value
                self.status_panel.log(f"{label}: {decoded_value}", "INFO")
            
            self.log_manager.info(
                f"系统状态更新 - 天文台: {url_decode(status.observatory_status[3:])}, "
                f"望远镜: {url_decode(status.telescope_status[3:])}"
            )
            
        except requests.exceptions.Timeout:
            self.log_manager.error("网络读取超时")
            self.status_panel.log("✗ 网络超时，请检查网络连接", "ERROR")
        except requests.exceptions.ConnectionError:
            self.log_manager.error("网络连接错误")
            self.status_panel.log("✗ 网络连接失败，请检查服务器地址", "ERROR")
        except Exception as e:
            self.log_manager.error(f"获取状态失败: {str(e)}", exc_info=True)
            self.status_panel.log(f"✗ 获取状态失败: {str(e)}", "ERROR")
            
    def start_imaging(self):
        """启动成像计划"""
        if not self.client:
            self.log_manager.warning("尝试启动成像但客户端未连接")
            return
            
        try:
            self.log_manager.info("准备启动成像计划")
            
            config = self.plan_panel.get_plan_config()
            
            if not config['filters']:
                raise ValueError("请至少添加一个滤镜配置")
            
            if not all([config['target'], config['ra'], config['dec']]):
                raise ValueError("目标、RA和DEC不能为空")
            
            self.log_manager.debug(
                f"成像参数 - 目标: {config['target']}, RA: {config['ra']}, "
                f"DEC: {config['dec']}, 滤镜数: {len(config['filters'])}"
            )
            
            plan = ImagingPlan(**config)
            
            self.status_panel.log(f"启动成像计划 - 目标: {config['target']}", "INFO")
            success = self.client.start_imaging_plan(plan)
            
            if success:
                self.log_manager.info(f"成像计划启动成功 - 目标: {config['target']}")
                self.status_panel.log("✓ 成像计划已启动", "SUCCESS")
                messagebox.showinfo("成功", "成像计划已启动")
            else:
                self.log_manager.error("成像计划启动失败")
                self.status_panel.log("✗ 成像计划启动失败", "ERROR")
                messagebox.showerror("失败", "成像计划启动失败")
                
        except ValueError as e:
            self.log_manager.error(f"输入验证失败: {str(e)}")
            self.status_panel.log(f"✗ {str(e)}", "ERROR")
            messagebox.showerror("错误", str(e))
        except Exception as e:
            self.log_manager.error(f"启动成像计划失败: {str(e)}", exc_info=True)
            self.status_panel.log(f"✗ 启动失败: {str(e)}", "ERROR")
            messagebox.showerror("错误", f"启动失败: {str(e)}")
            
    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.monitor:
            return
            
        if self.monitor.is_monitoring():
            self.monitor.stop()
            self.monitor_btn.config(text="开始监控")
            self.status_panel.log("■ 停止监控", "INFO")
        else:
            self.monitor.start()
            self.monitor_btn.config(text="停止监控")
            self.status_panel.log("▶ 开始监控", "INFO")
            
    def clear_log(self):
        """清除日志"""
        self.status_panel.clear()
        self.log_manager.info("日志已清除")
        
    def on_closing(self):
        """窗口关闭事件处理"""
        if self.monitor and self.monitor.is_monitoring():
            self.monitor.stop()
        self.log_manager.info("应用程序关闭")
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = ACPClientGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
