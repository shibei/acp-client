"""
GUI启动器脚本
提供简单的命令行接口来启动ACPClient GUI
"""

import sys
import os
import argparse
from pathlib import Path

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ACPClient GUI 启动器')
    parser.add_argument('--config', '-c', 
                       default='multi_target_config.yaml',
                       help='配置文件路径 (默认: multi_target_config.yaml)')
    parser.add_argument('--theme', '-t',
                       choices=['light', 'dark', 'blue'],
                       default='light',
                       help='界面主题 (默认: light)')
    parser.add_argument('--debug', '-d',
                       action='store_true',
                       help='调试模式')
    
    args = parser.parse_args()
    
    # 检查配置文件
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"警告: 配置文件 {args.config} 不存在")
        print("GUI启动后将使用默认配置")
    
    # 设置环境变量
    os.environ['ACPCIENT_CONFIG'] = str(config_path)
    os.environ['ACPCIENT_THEME'] = args.theme
    if args.debug:
        os.environ['ACPCIENT_DEBUG'] = '1'
    
    try:
        # 导入并启动GUI
        from gui.main_gui import main as gui_main
        
        print("正在启动 ACPClient GUI...")
        print(f"配置文件: {config_path}")
        print(f"主题: {args.theme}")
        
        gui_main()
        
    except ImportError as e:
        print(f"错误: 无法导入GUI模块 - {e}")
        print("请确保所有依赖项已安装:")
        print("  pip install tkinter pyyaml")
        return 1
        
    except Exception as e:
        print(f"GUI启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())