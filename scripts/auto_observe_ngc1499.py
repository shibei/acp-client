import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.config import ObservationConfig
from lib.orchestra import ObservationOrchestrator


def main():
    """主函数"""
    config = ObservationConfig()
    orchestrator = ObservationOrchestrator(config)
    orchestrator.run()


if __name__ == "__main__":
    main()
