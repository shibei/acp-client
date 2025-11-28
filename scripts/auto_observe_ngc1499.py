import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from datetime import datetime
from ACP.gui.logger import LogManager
from lib.config import ObservationConfig
from lib.plan_builder import ImagingPlanBuilder
from lib.time_manager import TimeManager
from lib.acp_mamager import ACPManager

def main():
    """主函数"""
    config = ObservationConfig()
    orchestrator = ObservationOrchestrator(config)
    orchestrator.run()


if __name__ == "__main__":
    main()
