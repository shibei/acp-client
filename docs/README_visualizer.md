# 观测队列可视化工具

这个工具可以根据配置文件生成观测计划的mermaid甘特图，帮助您直观地了解观测安排。

## 功能特点

### 基础版本 (`observation_scheduler_visualizer.py`)
- ✅ 读取YAML配置文件
- ✅ 计算观测时间和持续时间
- ✅ 生成mermaid甘特图
- ✅ 支持全局停止时间
- ✅ 自动时间调整和重叠处理

### 高级版本 (`observation_visualizer_advanced.py`)
- ✅ 所有基础功能
- ✅ 颜色编码（目标和滤镜）
- ✅ 详细的滤镜拍摄计划
- ✅ HTML报告生成
- ✅ 多种输出格式（Markdown/HTML/Both）
- ✅ 统计信息展示
- ✅ 中天反转配置显示
- ✅ 美观的Web界面

## 使用方法

### 基础版本
```bash
# 基本用法
python observation_scheduler_visualizer.py configs/multi_target_config_example.yaml

# 指定输出文件
python observation_scheduler_visualizer.py configs/multi_target_config_example.yaml -o my_gantt_chart.md
```

### 高级版本
```bash
# 生成Markdown格式的甘特图
python observation_visualizer_advanced.py configs/multi_target_config_example.yaml

# 生成HTML报告
python observation_visualizer_advanced.py configs/multi_target_config_example.yaml -f html

# 同时生成Markdown和HTML
python observation_visualizer_advanced.py configs/multi_target_config_example.yaml -f both

# 只显示摘要信息
python observation_visualizer_advanced.py configs/multi_target_config_example.yaml -s

# 只输出mermaid代码
python observation_visualizer_advanced.py configs/multi_target_config_example.yaml -m

# 禁用颜色
python observation_visualizer_advanced.py configs/multi_target_config_example.yaml --no-colors

# 在甘特图中隐藏滤镜详情
python observation_visualizer_advanced.py configs/multi_target_config_example.yaml --no-filters
```

## 输出文件说明

### Markdown文件 (.md)
- 包含mermaid甘特图代码
- 可以在支持mermaid的编辑器中查看
- 包含详细的统计信息和目标详情

### HTML文件 (.html)
- 完整的Web报告
- 交互式甘特图（需要mermaid支持）
- 美观的统计卡片和表格
- 颜色编码的目标和滤镜信息

## 支持的滤镜颜色

| 滤镜 | 颜色 |
|------|------|
| L | 金色 (#FFD700) |
| R | 红色 (#FF6B6B) |
| G | 绿色 (#4ECDC4) |
| B | 蓝色 (#45B7D1) |
| H-alpha/Ha/H-a | 深红色 (#FF4757) |
| OIII/O-III | 鲜绿色 (#32CD32) |
| SII/S-II | 紫色 (#8A2BE2) |
| U | 紫色 (#9B59B6) |
| V | 蓝色 (#3498DB) |

## 时间计算逻辑

1. **曝光时间**: 所有滤镜的 `exposure × count` 总和
2. **开销时间**: 每张图片额外30秒（读取、下载、抖动）
3. **对焦时间**: 如果启用自动对焦，根据AF间隔计算
4. **总时间**: 曝光时间 + 开销时间 + 对焦时间
5. **时间调整**: 自动处理重叠时间和全局停止时间

## 查看甘特图

### 在线工具
- [Mermaid Live Editor](https://mermaid.live)
- [Mermaid在线编辑器](https://mermaid-js.github.io/mermaid-live-editor)

### 本地工具
- VS Code (安装Mermaid插件)
- Obsidian
- Typora
- 任何支持mermaid的Markdown编辑器

## 示例输出

### 统计信息
```
============================================================
观测计划摘要
============================================================
目标数量: 3
总曝光时间: 11.8 小时
总开销时间: 1.2 小时
总观测时间: 10.0 小时
观测效率: 117.5%
```

### 甘特图预览
生成的甘特图会显示：
- 每个目标的观测时间段
- 滤镜拍摄的详细时间安排
- 颜色编码的目标和滤镜
- 里程碑标记（开始、停止时间）

## 注意事项

1. **全局停止时间**: 如果目标的结束时间超过全局停止时间，会自动调整到停止时间
2. **时间重叠**: 如果目标开始时间早于前一个目标的结束时间，会使用较晚的时间作为开始
3. **滤镜颜色**: 未识别的滤镜会使用默认的灰色
4. **HTML报告**: 需要在浏览器中打开，甘特图需要网络连接加载mermaid库

## 故障排除

### 时间显示异常
- 检查配置文件中的时间格式是否正确
- 确认全局停止时间是否合理

### 甘特图不显示
- 确保使用支持mermaid的编辑器
- 检查网络连接（在线mermaid库）

### 颜色不生效
- 确认滤镜名称是否正确
- 尝试重新生成报告