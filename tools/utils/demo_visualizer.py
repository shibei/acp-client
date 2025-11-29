#!/usr/bin/env python3
"""
观测队列可视化工具演示脚本
展示所有功能和用法
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """运行命令并显示描述"""
    print(f"\n{'='*60}")
    print(f"正在执行: {description}")
    print(f"命令: {cmd}")
    print('='*60)
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ 执行成功")
        if result.stdout:
            print("输出:")
            print(result.stdout)
    else:
        print("❌ 执行失败")
        if result.stderr:
            print("错误:")
            print(result.stderr)
    
    return result.returncode == 0


def main():
    """主演示函数"""
    print("🌟 观测队列可视化工具演示")
    print("="*60)
    
    # 检查Python文件是否存在（使用绝对路径）
    current_dir = Path(__file__).parent
    base_script = current_dir.parent / "visualizers" / "observation_scheduler_visualizer.py"
    advanced_script = current_dir.parent / "visualizers" / "observation_visualizer_advanced.py"
    
    if not Path(base_script).exists():
        print(f"❌ 基础脚本不存在: {base_script}")
        return 1
    
    if not Path(advanced_script).exists():
        print(f"❌ 高级脚本不存在: {advanced_script}")
        return 1
    
    # 检查配置文件
    config_files = [
        "configs/multi_target_config_example.yaml",
        "configs/demo_config.yaml"
    ]
    
    for config in config_files:
        if not Path(config).exists():
            print(f"❌ 配置文件不存在: {config}")
            return 1
    
    print("✅ 所有必需文件都存在")
    
    # 演示1: 基础版本
    print("\n📊 演示1: 基础版本功能")
    print("-"*40)
    
    run_command(
        f"python {base_script} configs/multi_target_config_example.yaml -o demo_basic.md",
        "基础版本 - 生成标准甘特图"
    )
    
    # 演示2: 高级版本基础功能
    print("\n📊 演示2: 高级版本基础功能")
    print("-"*40)
    
    run_command(
        f"python {advanced_script} configs/multi_target_config_example.yaml -o demo_advanced_basic.md",
        "高级版本 - 生成带颜色的甘特图"
    )
    
    # 演示3: HTML报告
    print("\n📊 演示3: 生成HTML报告")
    print("-"*40)
    
    run_command(
        f"python {advanced_script} configs/demo_config.yaml -o demo_html_report.html -f html",
        "生成完整的HTML报告"
    )
    
    # 演示4: 多种输出格式
    print("\n📊 演示4: 同时生成多种格式")
    print("-"*40)
    
    run_command(
        f"python {advanced_script} configs/demo_config.yaml -o demo_multi_format.md -f both",
        "同时生成Markdown和HTML格式"
    )
    
    # 演示5: 自定义选项
    print("\n📊 演示5: 自定义选项演示")
    print("-"*40)
    
    run_command(
        f"python {advanced_script} configs/multi_target_config_example.yaml -o demo_no_colors.md --no-colors --no-filters",
        "禁用颜色和滤镜详情"
    )
    
    # 演示6: 只显示摘要
    print("\n📊 演示6: 只显示摘要信息")
    print("-"*40)
    
    run_command(
        f"python {advanced_script} configs/multi_target_config_example.yaml -s",
        "只显示摘要信息"
    )
    
    # 演示7: 只输出mermaid代码
    print("\n📊 演示7: 只输出mermaid代码")
    print("-"*40)
    
    run_command(
        f"python {advanced_script} configs/multi_target_config_example.yaml -m",
        "只输出mermaid代码"
    )
    
    # 演示8: 自动打开浏览器功能
    print("\n📊 演示8: 自动打开浏览器功能")
    print("-"*40)
    
    run_command(
        f"python {advanced_script} configs/demo_config.yaml -o demo_auto_browser.html -f html --open",
        "生成HTML报告并自动打开浏览器"
    )
    
    run_command(
        f"python {base_script} configs/demo_config.yaml -o demo_auto_online.md --open",
        "生成Markdown文件并打开在线mermaid编辑器"
    )
    
    # 显示生成的文件
    print("\n📁 生成的文件列表:")
    print("-"*40)
    
    # 检查当前目录和reports目录
    current_files = [
        "demo_basic.md",
        "demo_auto_online.md"
    ]
    
    reports_files = [
        "demo_advanced_basic.md", 
        "demo_html_report.html",
        "demo_multi_format.md",
        "demo_multi_format.html",
        "demo_no_colors.md",
        "demo_auto_browser.html"
    ]
    
    # 检查当前目录文件
    for file in current_files:
        if Path(file).exists():
            size = Path(file).stat().st_size
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} (未生成)")
    
    # 检查reports目录文件
    reports_dir = Path("reports")
    if reports_dir.exists():
        for file in reports_files:
            file_path = reports_dir / file
            if file_path.exists():
                size = file_path.stat().st_size
                print(f"✅ reports/{file} ({size} bytes)")
            else:
                print(f"❌ reports/{file} (未生成)")
    
    # 使用建议
    print("\n💡 使用建议:")
    print("-"*40)
    print("1. 基础版本适合快速生成简单的甘特图")
    print("2. 高级版本适合需要详细报告和颜色编码的情况")
    print("3. HTML报告适合在浏览器中查看和分享")
    print("4. Markdown文件适合在支持mermaid的编辑器中查看")
    print("5. 使用--open参数可以自动生成后打开浏览器")
    print("6. 使用view_gantt.py工具可以快速查看生成的文件")
    
    print("\n🎉 演示完成！")
    print("你可以使用以下命令查看生成的文件:")
    print("python view_gantt.py -l")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())