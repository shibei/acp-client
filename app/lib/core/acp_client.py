import requests
import time
import logging
from typing import Dict, List
from urllib.parse import urljoin
from dataclasses import dataclass
import bs4 as bs



# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ObservatoryStatus:
    """天文台状态"""
    local_time: str = ""
    utc_time: str = ""
    lst_time: str = ""
    observatory_status: str = "Offline"
    owner: str = "Free"
    telescope_status: str = "Offline"
    camera_status: str = "Offline"
    guider_status: str = "Offline"
    current_ra: str = ""
    current_dec: str = ""
    current_alt: str = ""
    current_az: str = ""
    image_filter: str = ""
    image_temperature: str = ""
    plan_progress: str = "0/0"
    last_fwhm: str = ""

@dataclass
class ImagingPlan:
    """成像计划"""
    target: str = ""
    ra: str = ""
    dec: str = ""
    filters: List[Dict] = None
    dither: int = 5
    auto_focus: bool = True
    periodic_af_interval: int = 120
    exposure_time: int = 30
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = []

class ACPClient:
    """ACP天文台控制客户端"""
    
    def __init__(
            self, base_url: str, user: str, password: str, timeout: int = 30,
            polling_interval: int = 5,
            max_retries: int = 3,
            retry_delay: float = 1.0,
            ):
        self.base_url = base_url
        self.user = user
        self.password = password
        self.timeout = timeout
        self.polling_interval = polling_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.session = requests.Session()
        self._setup_session()
        
    def _setup_session(self):
        """设置会话头信息"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/index.asp'
        }
        self.session.auth = (self.user, self.password)
        self.session.headers.update(headers)
        html_str = self.session.get(self._make_url('/index.asp')).text
        self.title = bs.BeautifulSoup(html_str, 'html.parser').find_all('title')[0].text
        logger.info(f"登录成功，标题: {self.title}")
    
    def _make_url(self, endpoint: str) -> str:
        """构建完整URL"""
        return urljoin(self.base_url, endpoint)
    
    def get_system_status(self) -> ObservatoryStatus:
        """
        获取系统状态
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    self._make_url('/ac/asystemstatus.asp'),
                    data="",  # 空内容
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # 解析返回的JavaScript代码为状态对象
                status = self._parse_status_response(response.text)
                return status
                
            except requests.RequestException as e:
                logger.error(f"获取系统状态失败: {e}, 尝试次数: {attempt + 1}")
                time.sleep(self.retry_delay)
                
        return ObservatoryStatus()
    
    def _parse_status_response(self, response_text: str) -> ObservatoryStatus:
        """
        解析系统状态响应
        """
        status = ObservatoryStatus()
        
        try:
            # 简单的解析逻辑 - 实际实现需要更复杂的正则表达式匹配
            lines = response_text.split(';')
            for line in lines:
                line = line.strip()
                if line.startswith("_s('sm_local'"):
                    status.local_time = self._extract_value(line)
                elif line.startswith("_s('sm_utc'"):
                    status.utc_time = self._extract_value(line)
                elif line.startswith("_s('sm_obsStat'"):
                    status.observatory_status = self._extract_value(line)
                elif line.startswith("_s('sm_obsOwner'"):
                    status.owner = self._extract_value(line)
                elif line.startswith("_s('sm_scopeStat'"):
                    status.telescope_status = self._extract_value(line)
                elif line.startswith("_s('sm_camStat'"):
                    status.camera_status = self._extract_value(line)
                elif line.startswith("_s('sm_guideStat'"):
                    status.guider_status = self._extract_value(line)
                elif line.startswith("_s('sm_ra'"):
                    status.current_ra = self._extract_value(line)
                elif line.startswith("_s('sm_dec'"):
                    status.current_dec = self._extract_value(line)
                elif line.startswith("_s('sm_alt'"):
                    status.current_alt = self._extract_value(line)
                elif line.startswith("_s('sm_az'"):
                    status.current_az = self._extract_value(line)
                elif line.startswith("_s('sm_imgFilt'"):
                    status.image_filter = self._extract_value(line)
                elif line.startswith("_s('sm_imgTemp'"):
                    status.image_temperature = self._extract_value(line)
                elif line.startswith("_s('sm_plnSet'"):
                    status.plan_progress = self._extract_value(line)
                elif line.startswith("_s('sm_lastFWHM'"):
                    status.last_fwhm = self._extract_value(line)
                    
        except Exception as e:
            logger.warning(f"解析状态响应时出错: {e}")
            
        return status
    
    def _extract_value(self, line: str) -> str:
        """从JavaScript代码行中提取值"""
        try:
            # 简单的值提取，实际需要更健壮的解析
            parts = line.split("'")
            if len(parts) >= 4:
                return parts[3]
        except:
            pass
        return ""
    
    def start_imaging_plan(self, plan: ImagingPlan) -> bool:
        """
        启动成像计划
        """
        for attempt in range(self.max_retries):
            try:
                # 构建表单数据
                form_data = self._build_imaging_form_data(plan)
                
                response = self.session.post(
                    self._make_url('/ac/aacqform.asp'),
                    data=form_data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                logger.info(f"成像计划提交响应: {response.text}")
                return "warning" not in response.text.lower()
                
            except requests.RequestException as e:
                logger.error(f"启动成像计划失败: {e}, 尝试次数: {attempt + 1}")
                time.sleep(self.retry_delay)
                
        return False
    
    def _build_imaging_form_data(self, plan: ImagingPlan) -> Dict[str, str]:
        """构建成像计划表单数据"""
        form_data = {
            'Target': plan.target,
            'visOnly': 'true',
            'isOrb': 'dsky',
            'RA': plan.ra,
            'Dec': plan.dec,
            'Dither': str(plan.dither),
            'AF': 'yes' if plan.auto_focus else 'no',
            'PerAF': 'yes' if plan.periodic_af_interval > 0 else 'no',
            'PerAFInt': str(plan.periodic_af_interval)
        }
        
        # 添加滤镜配置
        for i, filter_config in enumerate(plan.filters, 1):
            form_data.update({
                f'ColorUse{i}': 'yes',
                f'ColorCount{i}': str(filter_config.get('count', 1)),
                f'ColorFilter{i}': str(filter_config.get('filter_id', 0)),
                f'ColorExposure{i}': str(filter_config.get('exposure', 60)),
                f'ColorBinning{i}': str(filter_config.get('binning', 1))
            })
        
        # 填充剩余的滤镜槽位
        for i in range(len(plan.filters) + 1, 17):
            form_data.update({
                f'ColorCount{i}': '',
                f'ColorFilter{i}': '0',
                f'ColorExposure{i}': '',
                f'ColorBinning{i}': '1'
            })
            
        return form_data
    
    def stop_script(self) -> bool:
        """
        停止当前运行的脚本
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    self._make_url('/ac/astopscript.asp'),
                    data={'Command': 'StopScript'},
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                logger.info(f"停止脚本响应: {response.text}")
                return "Received" in response.text
                
            except requests.RequestException as e:
                logger.error(f"停止脚本失败: {e}, 尝试次数: {attempt + 1}")
                time.sleep(self.retry_delay)
                
        return False
    
    def start_monitoring(self, callback=None):
        """
        开始监控天文台状态
        """
        logger.info("开始监控天文台状态...")
        
        try:
            while True:
                status = self.get_system_status()
                
                # 打印状态信息
                self._print_status(status)
                
                # 调用回调函数
                if callback:
                    callback(status)
                
                time.sleep(self.polling_interval)
                
        except KeyboardInterrupt:
            logger.info("监控已停止")
    
    def _print_status(self, status: ObservatoryStatus):
        """打印状态信息"""
        print(f"\n=== 天文台状态 ===")
        print(f"本地时间: {status.local_time}")
        print(f"UTC时间: {status.utc_time}")
        print(f"LST时间: {status.lst_time}")
        print(f"观测站: {status.observatory_status}")
        print(f"所有者: {status.owner}")
        print(f"望远镜: {status.telescope_status}")
        print(f"相机: {status.camera_status}")
        print(f"导星: {status.guider_status}")
        print(f"当前位置: RA={status.current_ra}, Dec={status.current_dec}")
        print(f"高度方位: Alt={status.current_alt}, Az={status.current_az}")
        print(f"计划进度: {status.plan_progress}")
        print(f"最后FWHM: {status.last_fwhm}")
