# 观测工具包 (Observation Tools)

这个工具包包含了用于天文观测计划、可视化和管理的各种工具。

## 📁 文件结构

```
tools/
├── __init__.py                    # 工具包初始化文件
├── visualizers/                   # 可视化工具目录
│   ├── __init__.py               # 可视化工具包初始化
│   ├── observation_scheduler_visualizer.py    # 基础观测计划可视化器
│   └── observation_visualizer_advanced.py     # 高级观测计划可视化器
├── utils/                         # 辅助工具目录
│   ├── __init__.py               # 辅助工具包初始化
│   ├── demo_visualizer.py        # 演示脚本，展示所有功能
│   └── view_gantt.py            # 快速查看甘特图工具
└── README.md                     # 本说明文档
```

## 🛠️ 可视化工具 (Visualizers)

### 基础可视化器 (observation_scheduler_visualizer.py)
- 功能：根据配置文件生成标准的mermaid甘特图
- 特点：简单轻量，适合基本需求
- 输出：Markdown格式的mermaid代码
- **新增**：支持自动生成后打开在线mermaid编辑器

### 高级可视化器 (observation_visualizer_advanced.py)
- 功能：生成带颜色编码的高级观测计划报告
- 特点：
  - 支持颜色编码（按目标、滤镜类型）
  - 可生成HTML完整报告
  - 支持多种输出格式（Markdown、HTML、同时生成）
  - 包含统计信息和详细分析
  - 自动输出到reports文件夹
  - **新增**：支持生成HTML后自动打开浏览器查看

## 🔧 辅助工具 (Utils)

### 演示工具 (demo_visualizer.py)
- 功能：自动演示所有可视化工具的功能
- 用法：运行后会依次展示各种功能和使用场景
- 输出：生成多个示例文件供参考

### 查看工具 (view_gantt.py)
- 功能：快速查看生成的甘特图文件
- 特点：
  - 自动查找甘特图文件
  - 支持直接打开文件
  - 提供在线查看建议
  - 支持多种文件格式

## 📋 使用方法

### 基础使用

```bash
# 使用基础可视化器
python tools\visualizers\observation_scheduler_visualizer.py configs\your_config.yaml

# 使用高级可视化器
python tools\visualizers\observation_visualizer_advanced.py configs\your_config.yaml

# 运行演示
python tools\utils\demo_visualizer.py

# 查看甘特图文件
python tools\utils\view_gantt.py
```

### 高级选项

```bash
# 生成HTML报告并自动打开浏览器
python tools\visualizers\observation_visualizer_advanced.py configs\your_config.yaml -f html -o report.html --open

# 生成Markdown文件并自动打开在线mermaid编辑器
python tools\visualizers\observation_scheduler_visualizer.py configs\your_config.yaml --open

# 同时生成多种格式
python tools\visualizers\observation_visualizer_advanced.py configs\your_config.yaml -f both -o report.md

# 只显示摘要信息
python tools\visualizers\observation_visualizer_advanced.py configs\your_config.yaml -s

# 禁用颜色编码
python tools\visualizers\observation_visualizer_advanced.py configs\your_config.yaml --no-colors
```

## 📊 输出文件

所有报告文件都会自动保存到 `reports/` 文件夹中：

- **Markdown文件** (`.md`)：包含mermaid甘特图代码，可在支持mermaid的编辑器中查看
- **HTML文件** (`.html`)：完整的网页报告，可直接在浏览器中打开
- **统计信息**：包含观测效率、总时间、目标详情等

## 🔍 查看生成的图表

### 本地查看
```bash
# 列出所有生成的文件
python tools\utils\view_gantt.py -l

# 打开特定文件
python tools\utils\view_gantt.py reports\your_report.md
```

### 在线查看
- 访问 [Mermaid Live Editor](https://mermaid.live)
- 复制Markdown文件中的mermaid代码
- 粘贴到在线编辑器中查看

### 支持的本地编辑器
- **VS Code**：安装Mermaid插件
- **Obsidian**：原生支持mermaid
- **Typora**：支持mermaid图表

## ⚙️ 配置文件

配置文件使用YAML格式，位于 `configs/` 目录中。基本结构包括：

```yaml
targets:
  - name: "目标名称"
    ra: "HH:MM:SS"      # 赤经
    dec: "±DD:MM:SS"    # 赤纬
    start_time: "YYYY-MM-DD HH:MM:SS"  # 开始时间
    priority: 1          # 优先级
    filters:            # 滤镜配置
      - name: "H-alpha"
        exposure: 300    # 曝光时间（秒）
        count: 10        # 拍摄数量
        
schedule:
  global_stop_time: "06:00"  # 全局停止时间
```

## 🚀 快速开始

### 基础用法
```bash
# 生成标准甘特图
python tools/visualizers/observation_scheduler_visualizer.py configs/config.yaml

# 生成高级HTML报告
python tools/visualizers/observation_visualizer_advanced.py configs/config.yaml -f html

# 查看生成的文件
python tools/utils/view_gantt.py -l
```

### 自动化新功能（推荐）
```bash
# 生成HTML报告并自动打开浏览器
python tools/visualizers/observation_visualizer_advanced.py configs/config.yaml -f html --open

# 生成Markdown文件并打开在线mermaid编辑器
python tools/visualizers/observation_scheduler_visualizer.py configs/config.yaml --open
```

## 💡 使用建议

### 新功能：自动化浏览器打开
- **高级可视化器**：使用 `--open` 参数生成HTML报告后自动在浏览器中打开
- **基础可视化器**：使用 `--open` 参数生成Markdown文件后自动打开在线mermaid编辑器
- **无需手动操作**：一键完成生成和查看，提高工作效率

- **基础版本**：适合快速生成简单的甘特图
- **高级版本**：适合需要详细报告和颜色编码的情况
- **HTML报告**：适合在浏览器中查看和分享
- **Markdown文件**：适合在支持mermaid的编辑器中查看和进一步编辑

## 📞 支持

如有问题，请检查：
1. 配置文件格式是否正确
2. Python环境是否配置完整
3. 所需的依赖包是否已安装
4. 文件路径是否正确