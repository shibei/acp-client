#!/usr/bin/env python3
"""
快速查看甘特图的工具
"""

import os
import sys
import webbrowser
import subprocess
import argparse
from pathlib import Path


def find_gantt_files(directory="."):
    """查找目录中的甘特图文件"""
    gantt_files = []
    for ext in ['.md', '.html']:
        files = list(Path(directory).glob(f"*{ext}"))
        for file in files:
            if 'gantt' in file.name.lower() or 'report' in file.name.lower():
                gantt_files.append(file)
    return gantt_files


def open_file(file_path):
    """打开文件"""
    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", file_path])
        else:  # Linux
            subprocess.run(["xdg-open", file_path])
        return True
    except Exception as e:
        print(f"打开文件失败: {e}")
        return False


def show_mermaid_online(file_path):
    """显示如何在在线编辑器中查看"""
    print(f"\n要在在线mermaid编辑器中查看 '{file_path}':")
    print("1. 打开 https://mermaid.live")
    print("2. 复制文件内容到编辑器")
    print("3. 点击 'Generate Diagram' 按钮")
    print("\n或者使用支持mermaid的本地编辑器:")
    print("- VS Code (安装Mermaid插件)")
    print("- Obsidian")
    print("- Typora")


def main():
    parser = argparse.ArgumentParser(description='快速查看甘特图文件')
    parser.add_argument('file', nargs='?', help='要查看的文件路径')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有甘特图文件')
    parser.add_argument('-o', '--online', action='store_true', help='显示在线查看方法')
    parser.add_argument('-d', '--directory', default='.', help='搜索目录')
    
    args = parser.parse_args()
    
    if args.list:
        # 列出所有甘特图文件
        files = find_gantt_files(args.directory)
        if files:
            print(f"在 '{args.directory}' 中找到的甘特图文件:")
            for i, file in enumerate(files, 1):
                print(f"{i}. {file.name} ({file.stat().st_size // 1024}KB)")
        else:
            print(f"在 '{args.directory}' 中没有找到甘特图文件")
        return
    
    if not args.file:
        # 如果没有指定文件，列出可用的文件
        files = find_gantt_files(args.directory)
        if not files:
            print(f"在 '{args.directory}' 中没有找到甘特图文件")
            return
        
        print("可用的甘特图文件:")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file.name}")
        
        try:
            choice = input("\n选择要查看的文件 (输入数字): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(files):
                file_path = files[int(choice) - 1]
            else:
                print("无效的选择")
                return
        except (KeyboardInterrupt, EOFError):
            print("\n取消操作")
            return
    else:
        file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return
    
    print(f"正在打开: {file_path}")
    
    if file_path.suffix == '.md' and args.online:
        show_mermaid_online(file_path)
    else:
        if open_file(file_path):
            print(f"已打开文件: {file_path}")
            
            if file_path.suffix == '.md':
                show_mermaid_online(file_path)
        else:
            print(f"无法打开文件，请手动查看: {file_path}")


if __name__ == '__main__':
    main()