# ACP天文台控制客户端
# 提供与ACP天文台控制软件的HTTP接口交互

import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin
from bs4 import BeautifulSoup as bs
import logging
import time
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import json

# 获取日志记录器 - 移除basicConfig以避免与日志管理器冲突
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
        
        try:
            html_str = self.session.get(self._make_url('/index.asp'), timeout=self.timeout).text
            soup = bs.BeautifulSoup(html_str, 'html.parser')
            title_tags = soup.find_all('title')
            if title_tags:
                self.title = title_tags[0].text
            else:
                self.title = "ACP Observatory"
            logger.info(f"登录成功，标题: {self.title}")
        except Exception as e:
            logger.warning(f"连接测试失败，但会话已配置: {e}")
            self.title = "ACP Observatory"
    
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
            # 使用改进的状态解析方法
            status_map = self.parse_encoded_status_text(response_text)
            
            # 映射到ObservatoryStatus对象
            status.local_time = status_map.get('sm_local', '')
            status.utc_time = status_map.get('sm_utc', '')
            status.observatory_status = status_map.get('sm_obsStat', 'Offline')
            status.owner = status_map.get('sm_obsOwner', 'Free')
            status.telescope_status = status_map.get('sm_scopeStat', 'Offline')
            status.camera_status = status_map.get('sm_camStat', 'Offline')
            status.guider_status = status_map.get('sm_guideStat', 'Offline')
            status.current_ra = status_map.get('sm_ra', '')
            status.current_dec = status_map.get('sm_dec', '')
            status.current_alt = status_map.get('sm_alt', '')
            status.current_az = status_map.get('sm_az', '')
            status.image_filter = status_map.get('sm_imgFilt', '')
            status.image_temperature = status_map.get('sm_imgTemp', '')
            status.plan_progress = status_map.get('sm_plnSet', '0/0')
            status.last_fwhm = status_map.get('sm_lastFWHM', '')
            
            # 检查警告信息
            warnings = self.get_observatory_warnings(response_text)
            if warnings:
                logger.warning(f"观测警告: {'; '.join(warnings)}")
                
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
    
    def start_imaging_plan(self, plan: ImagingPlan) -> tuple[bool, str]:
        """
        启动成像计划
        
        Returns:
            (success, error_message): 启动是否成功和错误信息
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
                
                # 检查是否有警告信息
                if "warning" in response.text.lower():
                    warnings = self.get_observatory_warnings(response.text)
                    error_msg = "; ".join(warnings) if warnings else "观测计划启动出现警告"
                    logger.warning(f"成像计划启动警告: {error_msg}")
                    return False, error_msg
                
                return True, ""
                
            except requests.RequestException as e:
                error_msg = f"启动成像计划失败: {e}"
                logger.error(f"{error_msg}, 尝试次数: {attempt + 1}")
                time.sleep(self.retry_delay)
                
        return False, "启动成像计划重试次数耗尽"
    
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
            if i <= 16:  # ACP最多支持16个滤镜配置
                form_data[f'ColorUse{i}'] = 'yes'
                form_data[f'ColorCount{i}'] = str(filter_config.get('count', 1))
                form_data[f'ColorFilter{i}'] = str(filter_config.get('filter_id', 0))
                form_data[f'ColorExposure{i}'] = str(filter_config.get('exposure', plan.exposure_time))
                form_data[f'ColorBinning{i}'] = str(filter_config.get('binning', 1))
        
        # 填充剩余的滤镜槽位为空值
        for i in range(len(plan.filters) + 1, 17):
            form_data[f'ColorUse{i}'] = ''
            form_data[f'ColorCount{i}'] = ''
            form_data[f'ColorFilter{i}'] = '0'
            form_data[f'ColorExposure{i}'] = ''
            form_data[f'ColorBinning{i}'] = '1'
        
        return form_data
    
    def parse_encoded_status_text(self, encoded_text: str) -> Dict[str, str]:
        """
        解析ACP编码的状态文本
        例如: "@an19%3A44%3A15" -> "19:44:15"
        """
        status_map = {}
        
        # ACP状态编码映射
        acp_decoders = {
            '@an': lambda x: x,  # 普通文本
            '@wn': lambda x: x.replace('Offline', '离线').replace('Online', '在线'),  # 警告/正常状态
            '@in': lambda x: x.replace('---', '--'),  # 输入/数值
            '@inn': lambda x: 'N/A' if x == 'n/a' else x  # 无效/不可用
        }
        
        # 解析JavaScript状态设置函数
        pattern = r"_s\('([^']+)'\s*,\s*'([^']+)'\)"
        matches = re.findall(pattern, encoded_text)
        
        for key, value in matches:
            # URL解码
            try:
                decoded_value = urllib.parse.unquote(value)
            except:
                decoded_value = value
            
            # 应用ACP解码器
            for prefix, decoder in acp_decoders.items():
                if decoded_value.startswith(prefix):
                    decoded_value = decoder(decoded_value[len(prefix):])
                    break
            
            status_map[key] = decoded_value
        
        return status_map
    
    def get_observatory_warnings(self, response_text: str) -> List[str]:
        """
        从响应文本中提取观测警告信息
        """
        warnings = []
        
        # 查找警告标记
        if 'warning' in response_text.lower():
            # 提取警告消息
            warning_pattern = r'----\s*\n\[([^\]]+)\]([^\n]+)\n----'
            matches = re.findall(warning_pattern, response_text)
            
            for match in matches:
                warning_type, warning_msg = match
                warnings.append(f"[{warning_type}]{warning_msg.strip()}")
        
        return warnings
    
    def wait_for_observatory_ready(self, timeout: int = 300, check_interval: int = 5) -> bool:
        """
        等待天文台准备就绪
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = self.get_system_status()
                
                # 检查天文台是否在线
                if status.observatory_status.lower() == 'online':
                    logger.info("天文台已准备就绪")
                    return True
                
                logger.info(f"等待天文台准备就绪... 当前状态: {status.observatory_status}")
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"检查天文台状态时出错: {e}")
                time.sleep(check_interval)
        
        logger.error("等待天文台准备就绪超时")
        return False
    
    def create_simple_imaging_plan(self, target: str, ra: str, dec: str, 
                                 filter_configs: List[Dict], exposure_time: int = 30,
                                 dither: int = 5, auto_focus: bool = True) -> ImagingPlan:
        """
        创建简单的成像计划
        """
        plan = ImagingPlan(
            target=target,
            ra=ra,
            dec=dec,
            filters=filter_configs,
            exposure_time=exposure_time,
            dither=dither,
            auto_focus=auto_focus
        )
        
        return plan
    
    def get_current_status_summary(self) -> str:
        """
        获取当前状态的简要摘要
        """
        try:
            status = self.get_system_status()
            
            summary = f"""
天文台状态摘要:
================
观测站状态: {status.observatory_status}
望远镜状态: {status.telescope_status}
相机状态: {status.camera_status}
导星状态: {status.guider_status}
当前坐标: RA {status.current_ra}, Dec {status.current_dec}
高度/方位: Alt {status.current_alt}, Az {status.current_az}
当前滤镜: {status.image_filter}
计划进度: {status.plan_progress}
最后FWHM: {status.last_fwhm}
            """.strip()
            
            return summary
            
        except Exception as e:
            # 如果get_system_status失败，提供一个基础状态
            return f"""
天文台状态摘要:
================
观测站状态: Unknown
望远镜状态: Unknown
相机状态: Unknown
导星状态: Unknown
当前坐标: RA --:--:--, Dec --°--'--"
高度/方位: Alt --.--°, Az --.--°
当前滤镜: N/A
计划进度: 0/0
最后FWHM: N/A

注意: {str(e)}
            """.strip()
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
        """打印系统状态"""
        # print(f"\n=== 天文台状态 ===")
        # print(f"本地时间: {status.local_time}")
        # print(f"UTC时间: {status.utc_time}")
        # print(f"LST时间: {status.lst_time}")
        # print(f"观测站: {status.observatory_status}")
        # print(f"所有者: {status.owner}")
        # print(f"望远镜: {status.telescope_status}")
        # print(f"相机: {status.camera_status}")
        # print(f"导星: {status.guider_status}")
        # print(f"当前位置: RA={status.current_ra}, Dec={status.current_dec}")
        # print(f"高度方位: Alt={status.current_alt}, Az={status.current_az}")
        # print(f"计划进度: {status.plan_progress}")
        # print(f"最后FWHM: {status.last_fwhm}")
        
        status_msg = f"""
=== 天文台状态 ===
本地时间: {status.local_time}
UTC时间: {status.utc_time}
LST时间: {status.lst_time}
观测站: {status.observatory_status}
所有者: {status.owner}
望远镜: {status.telescope_status}
相机: {status.camera_status}
导星: {status.guider_status}
当前位置: RA={status.current_ra}, Dec={status.current_dec}
高度方位: Alt={status.current_alt}, Az={status.current_az}
计划进度: {status.plan_progress}
最后FWHM: {status.last_fwhm}
"""
        logger.info(status_msg.strip())