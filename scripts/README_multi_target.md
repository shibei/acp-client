# 多目标自动观测系统

## 概述

多目标自动观测系统允许您按时间顺序自动执行多个观测目标，每个目标可以有不同的滤镜配置和观测参数。

## 功能特点

- 🎯 **多目标支持**: 支持按时间顺序执行多个观测目标
- ⏰ **时间控制**: 每个目标可以设置独立的开始时间
- 🔬 **滤镜配置**: 每个目标可以有不同的滤镜组合和曝光参数
- 📊 **实时监控**: 实时监控每个目标的观测状态
- 📝 **详细日志**: 完整的操作日志记录
- 🛡️ **安全模式**: 支持DRYRUN模式进行测试
- ⏹️ **全局控制**: 支持全局停止时间

## 文件结构

```
scripts/
├── auto_observe_multi_target.py      # 主脚本
├── multi_target_config.yaml          # 配置文件
├── lib/
│   ├── multi_target_config.py        # 配置类
│   ├── multi_target_plan_builder.py  # 计划构建器
│   └── multi_target_orchestrator.py  # 编排器
└── README_multi_target.md            # 本文档
```

## 使用方法

### 1. 配置观测计划

编辑 `multi_target_config.yaml` 文件，配置您的观测计划：

```yaml
# 多目标自动观测配置文件
schedule:
  stop_time: '2025-11-29 02:00:00'  # 全局停止时间（可选）

acp_server:
  url: 'http://your-acp-server:port'
  username: 'your-username'
  password: 'your-password'

targets:
  - name: 'NGC 1499'
    ra: '04:01:07.51'
    dec: '+36:31:11.9'
    start_time: '2025-11-29 20:00:00'
    priority: 1
    filters:
      - filter_id: 4
        name: 'H-alpha'
        exposure: 600
        count: 20
        binning: 1
      - filter_id: 6
        name: 'OIII'
        exposure: 600
        count: 20
        binning: 1

  - name: 'M 31'
    ra: '00:42:44.33'
    dec: '+41:16:07.5'
    start_time: '2025-11-29 22:30:00'
    priority: 2
    filters:
      - filter_id: 1
        name: 'R'
        exposure: 300
        count: 15
        binning: 1

# 全局成像参数
global_settings:
  dither: 5
  auto_focus: true
  af_interval: 120
  dryrun: false
```

### 2. 运行观测脚本

```bash
python auto_observe_multi_target.py
```

### 3. 监控观测状态

脚本会自动：
- 按时间顺序等待每个目标的观测时间
- 自动启动每个目标的观测计划
- 实时监控观测状态（每30秒刷新）
- 记录详细的操作日志

## 配置参数说明

### 时间配置

- `stop_time`: 全局停止时间，到达此时间后停止所有观测（可选）
- `start_time`: 每个目标的开始时间，格式为 'YYYY-MM-DD HH:MM:SS'

### 目标配置

- `name`: 目标名称
- `ra`: 赤经坐标（例如：'04:01:07.51'）
- `dec`: 赤纬坐标（例如：'+36:31:11.9'）
- `start_time`: 该目标的开始观测时间
- `priority`: 优先级（数字越小优先级越高，用于排序）
- `filters`: 滤镜配置列表

### 滤镜配置

- `filter_id`: 滤镜ID（0=L, 1=R, 2=G, 3=B, 4=H-alpha, 5=O-III, 6=S-II）
- `name`: 滤镜名称（可选，用于显示）
- `exposure`: 曝光时间（秒）
- `count`: 图像数量
- `binning`: 像素合并（1, 2, 3, 4）

### 全局设置

- `dither`: 抖动像素数
- `auto_focus`: 是否启用自动对焦（true/false）
- `af_interval`: 自动对焦间隔（分钟）
- `dryrun`: 是否启用DRYRUN模式（仅模拟，不实际执行）

## 使用示例

### 示例1：整夜多目标观测

```yaml
targets:
  - name: 'NGC 7000'
    start_time: '2025-11-30 19:00:00'
    filters:
      - filter_id: 4
        exposure: 600
        count: 30

  - name: 'M 33'
    start_time: '2025-11-30 22:00:00'
    filters:
      - filter_id: 4
        exposure: 900
        count: 20
      - filter_id: 6
        exposure: 900
        count: 20

  - name: 'M 31'
    start_time: '2025-12-01 01:00:00'
    filters:
      - filter_id: 1
        exposure: 300
        count: 25
      - filter_id: 2
        exposure: 300
        count: 25
      - filter_id: 3
        exposure: 300
        count: 25
```

### 示例2：测试模式

设置 `dryrun: true` 可以在不实际执行的情况下测试配置：

```yaml
global_settings:
  dryrun: true
```

## 日志文件

日志文件保存在 `logs/` 目录下，文件名格式为：`multi_target_observe_YYYYMMDD.log`

## 注意事项

1. **时间设置**: 确保所有时间都是本地时间，并且考虑天文观测的最佳时间
2. **坐标精度**: 确保目标坐标准确，建议使用J2000坐标系
3. **滤镜配置**: 根据您的设备配置正确的滤镜ID
4. **网络连接**: 确保与ACP服务器的网络连接稳定
5. **存储空间**: 确保有足够的磁盘空间存储图像文件

## 故障排除

### 常见问题

1. **连接失败**: 检查ACP服务器地址和网络连接
2. **时间错误**: 检查系统时间和配置文件中的时间格式
3. **滤镜错误**: 确认滤镜ID与您的设备配置匹配
4. **坐标错误**: 检查目标坐标的格式和精度

### 调试模式

启用DRYRUN模式进行测试：

```yaml
global_settings:
  dryrun: true
```

这将模拟执行流程而不实际发送命令到ACP服务器。

## 更新日志

- v1.0.0: 初始版本，支持多目标观测
- v1.0.1: 增加实时监控和详细日志

## 支持

如有问题，请检查日志文件或联系技术支持。