"""
目标调度器模块
"""
from dataclasses import dataclass
import threading
import time
import json
from tkinter import ttk
from typing import Optional, List
from datetime import datetime
from ..ACPlib import ACPClient
from ..models import ImagingPlan, ScheduledTarget
from .logger import LogManager


class TargetScheduler:
    """目标调度器 - 管理带时间的多目标队列"""
    
    CHECK_INTERVAL = 10  # 秒 - 检查时间间隔
    
    def __init__(self, client: ACPClient, log_manager: LogManager, ui_callback):
        self.client = client
        self.log_manager = log_manager
        self.ui_callback = ui_callback  # 用于更新UI的回调函数
        self.targets: List[ScheduledTarget] = []
        self.current_target_index: Optional[int] = None
        self.running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()
        
    def add_target(self, target: ScheduledTarget):
        """添加目标到队列"""
        self.targets.append(target)
        # 按时间排序
        self.targets.sort(key=lambda t: t.start_time)
        self.log_manager.info(f"添加目标到队列: {target.name}, 开始时间: {target.start_time}")
        
    def remove_target(self, index: int):
        """从队列中移除目标"""
        if 0 <= index < len(self.targets):
            target = self.targets.pop(index)
            self.log_manager.info(f"从队列中移除目标: {target.name}")
            return True
        return False
        
    def clear_targets(self):
        """清空所有目标"""
        self.targets.clear()
        self.current_target_index = None
        self.log_manager.info("清空目标队列")
        
    def start(self):
        """启动调度器"""
        if self.running:
            return
            
        if not self.targets:
            raise ValueError("队列中没有目标")
            
        self.running = True
        self.shutdown_event.clear()
        self.log_manager.info("启动目标调度器")
        
        self.scheduler_thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self.scheduler_thread.start()
        
    def stop(self):
        """停止调度器"""
        if not self.running:
            return
            
        self.running = False
        self.shutdown_event.set()
        self.log_manager.info("停止目标调度器")
        
    def _schedule_loop(self):
        """调度循环 - 检查是否需要切换任务"""
        while self.running and not self.shutdown_event.is_set():
            try:
                now = datetime.now()
                
                # 查找应该执行的目标
                for i, target in enumerate(self.targets):
                    # 跳过已完成或已跳过的目标
                    if target.status in ["已完成", "已跳过"]:
                        continue
                        
                    # 如果当前时间已经到达或超过目标的开始时间
                    if now >= target.start_time:
                        # 如果这不是当前正在执行的目标，需要切换
                        if self.current_target_index != i:
                            self._switch_to_target(i)
                        break
                else:
                    # 没有需要执行的目标
                    if self.current_target_index is not None:
                        # 标记当前目标为已完成
                        self.targets[self.current_target_index].status = "已完成"
                        self.current_target_index = None
                        self._update_ui()
                
                self.shutdown_event.wait(self.CHECK_INTERVAL)
                
            except Exception as e:
                self.log_manager.error(f"调度循环出错: {str(e)}", exc_info=True)
                self.shutdown_event.wait(self.CHECK_INTERVAL)
                
    def _switch_to_target(self, target_index: int):
        """切换到指定的目标"""
        target = self.targets[target_index]
        
        self.log_manager.info(f"准备切换到目标: {target.name}")
        
        try:
            # 如果有正在执行的任务，先停止它
            if self.current_target_index is not None:
                old_target = self.targets[self.current_target_index]
                self.log_manager.info(f"停止当前任务: {old_target.name}")
                self.client.stop_script()
                old_target.status = "已完成"
                time.sleep(2)  # 等待停止完成
            
            # 标记之前跳过的目标
            for i, t in enumerate(self.targets):
                if i < target_index and t.status == "等待中":
                    t.status = "已跳过"
            
            # 启动新目标
            target.status = "执行中"
            self.current_target_index = target_index
            
            # 创建成像计划
            plan = ImagingPlan(
                target=target.plan_config['target'],
                ra=target.plan_config['ra'],
                dec=target.plan_config['dec'],
                filters=target.plan_config['filters'],
                dither=target.plan_config.get('dither', 5),
                auto_focus=target.plan_config.get('auto_focus', True),
                periodic_af_interval=target.plan_config.get('periodic_af_interval', 120)
            )
            
            self.log_manager.info(f"启动目标: {target.name}")
            success = self.client.start_imaging_plan(plan)
            
            if success:
                self.log_manager.info(f"目标启动成功: {target.name}")
            else:
                self.log_manager.error(f"目标启动失败: {target.name}")
                target.status = "失败"
                
            # 更新UI
            self._update_ui()
            
        except Exception as e:
            self.log_manager.error(f"切换目标失败: {str(e)}", exc_info=True)
            target.status = "失败"
            self._update_ui()
            
    def _update_ui(self):
        """更新UI显示"""
        if self.ui_callback:
            try:
                self.ui_callback()
            except Exception as e:
                self.log_manager.error(f"更新UI失败: {str(e)}", exc_info=True)
                
    def get_targets(self) -> List[ScheduledTarget]:
        """获取目标列表"""
        return self.targets
        
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.running
        
    def save_to_file(self, filepath: str):
        """保存队列到文件"""
        try:
            data = [t.to_dict() for t in self.targets]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.log_manager.info(f"队列已保存到: {filepath}")
        except Exception as e:
            self.log_manager.error(f"保存队列失败: {str(e)}", exc_info=True)
            raise
            
    def load_from_file(self, filepath: str):
        """从文件加载队列"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.targets = [ScheduledTarget.from_dict(d) for d in data]
            self.targets.sort(key=lambda t: t.start_time)
            self.log_manager.info(f"从文件加载队列: {filepath}, 共 {len(self.targets)} 个目标")
        except Exception as e:
            self.log_manager.error(f"加载队列失败: {str(e)}", exc_info=True)
            raise

class QueueManagementPanel(ttk.LabelFrame):
    """队列管理面板"""
    
    def __init__(self, parent, scheduler: TargetScheduler, plan_panel: ImagingPlan):
        super().__init__(parent, text="目标队列管理", padding=10)
        self.scheduler = scheduler
        self.plan_panel = plan_panel
        self._create_widgets()
        
    def _create_widgets(self):
        """创建组件"""
        # 顶部：添加目标区域
        self._create_add_target_section()
        
        # 中部：队列列表
        self._create_queue_list()
        
        # 底部：控制按钮
        self._create_control_buttons()
        
    def _create_add_target_section(self):
        """创建添加目标区域"""
        add_frame = ttk.LabelFrame(self, text="添加新目标", padding=5)
        add_frame.pack(fill="x", pady=5)
        
        # 目标名称
        ttk.Label(add_frame, text="目标名称:").grid(row=0, column=0, sticky="w", padx=5)
        self.target_name_entry = ttk.Entry(add_frame, width=20)
        self.target_name_entry.grid(row=0, column=1, padx=5)
        
        # 开始时间
        ttk.Label(add_frame, text="开始时间:").grid(row=0, column=2, sticky="w", padx=5)
        
        time_frame = ttk.Frame(add_frame)
        time_frame.grid(row=0, column=3, padx=5)
        
        # 日期
        self.date_entry = ttk.Entry(time_frame, width=12)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.date_entry.pack(side="left", padx=2)
        
        # 时间
        self.time_entry = ttk.Entry(time_frame, width=10)
        self.time_entry.insert(0, "20:00:00")
        self.time_entry.pack(side="left", padx=2)
        
        # 添加按钮
        ttk.Button(
            add_frame, text="从当前计划添加", 
            command=self.add_target_from_plan
        ).grid(row=0, column=4, padx=5)
        
    def _create_queue_list(self):
        """创建队列列表"""
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        # 创建表格
        columns = ("目标名称", "开始时间", "RA", "DEC", "滤镜数", "状态")
        self.queue_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        # 设置列
        widths = [150, 150, 100, 100, 80, 80]
        for col, width in zip(columns, widths):
            self.queue_tree.heading(col, text=col)
            self.queue_tree.column(col, width=width, anchor="center")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.queue_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.queue_tree.configure(yscrollcommand=scrollbar.set)
        
        self.queue_tree.pack(side="left", fill="both", expand=True)
        
    def _create_control_buttons(self):
        """创建控制按钮"""
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=5)
        
        self.start_queue_btn = ttk.Button(
            button_frame, text="启动队列", 
            command=self.start_queue
        )
        self.start_queue_btn.pack(side="left", padx=5)
        
        self.stop_queue_btn = ttk.Button(
            button_frame, text="停止队列", 
            command=self.stop_queue, state="disabled"
        )
        self.stop_queue_btn.pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, text="删除选中", 
            command=self.remove_selected
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, text="清空队列", 
            command=self.clear_queue
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, text="保存队列", 
            command=self.save_queue
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame, text="加载队列", 
            command=self.load_queue
        ).pack(side="left", padx=5)
        
    def add_target_from_plan(self):
        """从当前计划添加目标"""
        try:
            # 获取目标名称
            target_name = self.target_name_entry.get().strip()
            if not target_name:
                messagebox.showerror("错误", "请输入目标名称")
                return
            
            # 获取开始时间
            date_str = self.date_entry.get().strip()
            time_str = self.time_entry.get().strip()
            start_time = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M:%S')
            
            # 检查时间是否在未来
            if start_time < datetime.now():
                if not messagebox.askyesno("警告", "开始时间在过去，是否继续添加？"):
                    return
            
            # 获取计划配置
            plan_config = self.plan_panel.get_plan_config()
            
            # 创建计划目标
            target = ScheduledTarget(
                name=target_name,
                start_time=start_time,
                plan_config=plan_config
            )
            
            # 添加到调度器
            self.scheduler.add_target(target)
            
            # 更新显示
            self.refresh_queue_list()
            
            # 清空输入
            self.target_name_entry.delete(0, 'end')
            
            messagebox.showinfo("成功", f"目标 '{target_name}' 已添加到队列")
            
        except ValueError as e:
            messagebox.showerror("错误", f"时间格式错误: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"添加目标失败: {str(e)}")
            
    def refresh_queue_list(self):
        """刷新队列列表显示"""
        # 清空现有项
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        
        # 添加所有目标
        for target in self.scheduler.get_targets():
            values = (
                target.name,
                target.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                target.plan_config['ra'],
                target.plan_config['dec'],
                len(target.plan_config['filters']),
                target.status
            )
            
            # 根据状态设置不同的标签
            tags = []
            if target.status == "执行中":
                tags = ['executing']
            elif target.status == "已完成":
                tags = ['completed']
            elif target.status == "已跳过":
                tags = ['skipped']
            elif target.status == "失败":
                tags = ['failed']
                
            self.queue_tree.insert('', 'end', values=values, tags=tags)
        
        # 设置标签样式
        self.queue_tree.tag_configure('executing', background='lightgreen')
        self.queue_tree.tag_configure('completed', background='lightblue')
        self.queue_tree.tag_configure('skipped', background='lightgray')
        self.queue_tree.tag_configure('failed', background='lightcoral')
        
    def start_queue(self):
        """启动队列"""
        try:
            if not self.scheduler.get_targets():
                messagebox.showwarning("警告", "队列为空，无法启动")
                return
            
            self.scheduler.start()
            
            self.start_queue_btn.config(state="disabled")
            self.stop_queue_btn.config(state="normal")
            
            messagebox.showinfo("成功", "队列已启动")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动队列失败: {str(e)}")
            
    def stop_queue(self):
        """停止队列"""
        try:
            self.scheduler.stop()
            
            self.start_queue_btn.config(state="normal")
            self.stop_queue_btn.config(state="disabled")
            
            messagebox.showinfo("成功", "队列已停止")
            
        except Exception as e:
            messagebox.showerror("错误", f"停止队列失败: {str(e)}")
            
    def remove_selected(self):
        """删除选中的目标"""
        selected = self.queue_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的目标")
            return
        
        if self.scheduler.is_running():
            messagebox.showwarning("警告", "队列正在运行，无法删除")
            return
        
        for item in selected:
            index = self.queue_tree.index(item)
            self.scheduler.remove_target(index)
        
        self.refresh_queue_list()
        
    def clear_queue(self):
        """清空队列"""
        if self.scheduler.is_running():
            messagebox.showwarning("警告", "队列正在运行，无法清空")
            return
        
        if not messagebox.askyesno("确认", "确定要清空队列吗？"):
            return
        
        self.scheduler.clear_targets()
        self.refresh_queue_list()
        
    def save_queue(self):
        """保存队列到文件"""
        from tkinter import filedialog
        
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if filepath:
                self.scheduler.save_to_file(filepath)
                messagebox.showinfo("成功", "队列已保存")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
            
    def load_queue(self):
        """从文件加载队列"""
        from tkinter import filedialog
        
        if self.scheduler.is_running():
            messagebox.showwarning("警告", "队列正在运行，无法加载")
            return
        
        try:
            filepath = filedialog.askopenfilename(
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if filepath:
                self.scheduler.load_from_file(filepath)
                self.refresh_queue_list()
                messagebox.showinfo("成功", f"已加载 {len(self.scheduler.get_targets())} 个目标")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载失败: {str(e)}")

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

