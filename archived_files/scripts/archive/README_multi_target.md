# 多目标自动观测系统

## 概述

多目标自动观测系统允许您按时间顺序自动执行多个观测目标，每个目标可以有不同的滤镜配置和观测参数。

## 功能特点

- 🎯 **多目标支持**: 支持按时间顺序执行多个观测目标
- ⏰ **时间控制**: 每个目标可以设置独立的开始时间
- 🌟 **中天反转**: 自动计算中天时间，在中天前后智能停止/恢复观测
- 🔬 **滤镜配置**: 每个目标可以有不同的滤镜组合和曝光参数
- 📊 **实时监控**: 实时监控每个目标的观测状态
- 📝 **详细日志**: 完整的操作日志记录
- 🛡️ **安全模式**: 支持DRYRUN模式进行测试，包含中天反转保护
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

配置文件使用YAML格式，主要参数如下：

### 全局参数
- `global_stop_time`: 全局停止时间（格式：HH:MM），所有观测将在指定时间停止
- `meridian_flip`: 中天反转配置
  - `stop_minutes_before`: 中天前停止观测时间（分钟）
  - `resume_minutes_after`: 中天后恢复观测时间（分钟）
  - `safety_margin`: 安全边距（分钟）
- `observatory`: 观测站位置（用于中天计算）
  - `latitude`: 纬度（度）
  - `longitude`: 经度（度）
- `acp_server`: ACP服务器配置
  - `host`: 服务器地址
  - `port`: 服务器端口
  - `timeout`: 超时时间（秒）

### 目标参数
每个目标包含以下参数：
- `name`: 目标名称
- `ra`: 赤经（格式：HH:MM:SS.SS）
- `dec`: 赤纬（格式：+DD:MM:SS.S）
- `start_time`: 开始时间（格式：YYYY-MM-DD HH:MM）
- `priority`: 优先级（数字越大优先级越高）
- `filters`: 滤镜配置，每个滤镜包含：
  - `filter`: 滤镜名称（L, R, G, B, H-alpha, OIII, SII）
  - `exposure_time`: 曝光时间（秒）
  - `num_images`: 图像数量

### 全局成像参数
- `dithering`: 抖动像素数
- `autofocus`: 是否自动对焦（true/false）
- `autofocus_interval`: 自动对焦间隔（分钟）

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

## 中天反转功能

系统现在支持自动中天反转等待功能，主要特性：

### 功能特点
- 🌟 **自动计算**: 根据目标坐标自动计算中天时间
- ⏰ **智能等待**: 在中天前后自动停止和恢复观测
- ⚙️ **灵活配置**: 支持自定义停止和恢复时间
- 🛡️ **安全保护**: 包含安全边距，确保设备安全

### 配置参数
```yaml
meridian_flip:
  stop_minutes_before: 10    # 中天前10分钟停止观测
  resume_minutes_after: 10   # 中天后10分钟恢复观测
  safety_margin: 2          # 额外安全时间（分钟）

observatory:
  latitude: 39.9    # 观测站纬度（度）
  longitude: 116.4  # 观测站经度（度）
```

### 工作流程
1. **计算中天时间**: 根据目标赤经和观测站位置计算中天时间
2. **确定时间窗口**: 计算停止观测和恢复观测的时间点
3. **自动等待**: 在中天期间自动暂停观测
4. **安全恢复**: 中天过后自动恢复观测

## 注意事项

1. **时间设置**: 确保系统时间准确，建议使用网络时间同步
2. **坐标精度**: 目标坐标必须精确，建议使用专业星表数据
3. **观测站位置**: 正确设置观测站经纬度，确保中天时间计算准确
4. **网络连接**: 确保与ACP服务器的网络连接稳定
5. **存储空间**: 确保有足够的磁盘空间存储图像文件
6. **DRYRUN模式**: 首次使用时建议启用DRYRUN模式进行测试

## 故障排除

### 常见问题

1. **连接失败**: 检查ACP服务器地址和网络连接
2. **时间错误**: 检查系统时间和配置文件中的时间格式
3. **滤镜错误**: 确认滤镜ID与您的设备配置匹配
4. **坐标错误**: 检查目标坐标的格式和精度

**Q: 中天时间计算不准确**
- 检查观测站经纬度设置
- 确认目标坐标精度
- 检查时区设置是否正确

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