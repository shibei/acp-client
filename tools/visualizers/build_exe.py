#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
观测计划调度器可视化工具打包脚本
将Python脚本打包成独立的exe文件
"""

import PyInstaller.__main__
import os
import sys

def build_visualizer_exe():
    """构建可视化工具exe"""
    print("开始构建观测计划调度器可视化工具...")
    
    # PyInstaller参数
    args = [
        'observation_scheduler_tkinter_gui.py',  # 主程序文件
        '--onefile',                             # 打包成单个exe文件
        '--windowed',                            # 无控制台窗口（GUI程序）
        '--name=观测计划调度器',                   # exe文件名
        '--distpath=./dist',                     # 输出目录
        '--workpath=./build',                    # 临时构建目录
        '--specpath=./',                         # spec文件目录
        '--clean',                               # 清理临时文件
        '--noconfirm',                           # 不确认覆盖
        # 添加图标（如果有的话）
        # '--icon=icon.ico',
        # 隐藏导入的模块
        '--hidden-import=observation_scheduler_visualizer',
        '--hidden-import=observation_visualizer_advanced',
        # 添加数据文件
        '--add-data=observation_scheduler_visualizer.py;.',
        '--add-data=observation_visualizer_advanced.py;.',
        # 排除不需要的模块以减小体积
        '--exclude-module=matplotlib',
        '--exclude-module=numpy',
        '--exclude-module=pandas',
        '--exclude-module=scipy',
        '--exclude-module=PIL',
        '--exclude-module=opencv',
    ]
    
    try:
        PyInstaller.__main__.run(args)
        print("✅ 构建完成！")
        print(f"📁 exe文件位置: {os.path.abspath('dist/观测计划调度器.exe')}")
        print("\n使用方法:")
        print("1. 双击运行 dist/观测计划调度器.exe")
        print("2. 选择配置文件")
        print("3. 设置参数并生成可视化")
        
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        return False
    
    return True

def build_all_tools():
    """构建所有可视化工具"""
    print("构建所有可视化工具...")
    
    # 基础可视化器
    base_args = [
        'observation_scheduler_visualizer.py',
        '--onefile',
        '--name=基础可视化器',
        '--distpath=./dist',
        '--clean',
        '--noconfirm',
    ]
    
    # 高级可视化器
    advanced_args = [
        'observation_visualizer_advanced.py',
        '--onefile',
        '--name=高级可视化器',
        '--distpath=./dist',
        '--clean',
        '--noconfirm',
        '--hidden-import=observation_scheduler_visualizer',
    ]
    
    try:
        print("构建基础可视化器...")
        PyInstaller.__main__.run(base_args)
        
        print("构建高级可视化器...")
        PyInstaller.__main__.run(advanced_args)
        
        print("✅ 所有工具构建完成！")
        print(f"📁 exe文件位置: {os.path.abspath('dist/')}")
        
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("观测计划调度器可视化工具打包脚本")
    print("=" * 60)
    
    print("\n选项:")
    print("1. 打包GUI界面程序")
    print("2. 打包所有工具")
    print("3. 退出")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "1":
        build_visualizer_exe()
    elif choice == "2":
        build_all_tools()
    elif choice == "3":
        print("退出程序")
    else:
        print("无效选择")