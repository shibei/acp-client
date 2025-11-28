
from datetime import datetime

class ObservationConfig:
    """观测配置类"""
    def __init__(self):
        # 时间配置
        self.stop_time = datetime(2025, 11, 28, 10, 45, 0)
        self.start_time = datetime(2025, 11, 28, 10, 46, 0)
        
        # ACP服务器配置
        self.acp_url = "http://27056t89i6.wicp.vip:1011"
        self.acp_user = "share"
        self.acp_password = "1681"
        
        # 运行模式
        self.dryrun = False
        
        # 目标配置
        self.target_name = "NGC 1499"
        self.target_ra = "04:01:07.51"
        self.target_dec = "+36:31:11.9"
        
        # 多滤镜配置
        self.filters = [
            {
                'filter_id': 4,
                'name': 'H-alpha',
                'exposure': 600,
                'count': 30,
                'binning': 1
            },
            {
                'filter_id': 6,
                'name': 'OIII',
                'exposure': 600,
                'count': 30,
                'binning': 1
            },
            {
                'filter_id': 5,
                'name': 'SII',
                'exposure': 600,
                'count': 30,
                'binning': 1
            },
        ]
        
        # 其他参数
        self.dither = 5
        self.auto_focus = True
        self.af_interval = 120
    
    def get_total_hours(self):
        """计算预计总时间（小时）"""
        total_seconds = sum(f['exposure'] * f['count'] for f in self.filters)
        return total_seconds / 3600
    
    def get_total_images(self):
        """计算总图像数量"""
        return sum(f['count'] for f in self.filters)
