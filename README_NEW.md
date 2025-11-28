# ACPClient 多目标自动观测系统

基于重构架构的多目标天文观测自动化系统。

## 系统架构

### 核心模块 (`scripts/lib/core/`)
- **acp_connection_manager.py**: ACP服务器连接管理
- **acp_imaging_manager.py**: 成像计划管理

### 配置管理 (`scripts/lib/config/`)
- **config_manager.py**: 统一的配置加载和验证

### 执行模块 (`scripts/lib/execution/`)
- **target_observation_executor.py**: 目标观测执行器

### 调度模块 (`scripts/lib/scheduling/`)
- **target_scheduler.py**: 目标调度器

### 工具模块 (`scripts/lib/utils/`)
- **time_utils.py**: 时间工具类
- **observation_utils.py**: 观测工具类
- **log_manager.py**: 日志管理器

### 新的主协调器
- **new_multi_target_orchestrator.py**: 基于重构架构的多目标协调器
- **new_main.py**: 新的主程序入口

## 新特性

### 1. 模块化架构
- 职责分离，每个模块专注于特定功能
- 更好的可维护性和可扩展性
- 清晰的模块间依赖关系

### 2. 增强的配置管理
- 统一的配置验证机制
- 类型安全的配置类
- 更好的错误处理和用户反馈

### 3. 改进的观测工具
- 坐标解析和格式化
- 可观测性计算
- 大气质量和高度角计算

### 4. 更好的日志管理
- 结构化的日志记录
- 轮转日志文件
- 专门的观测日志方法

### 5. 灵活的状态回调
- 支持外部状态监控
- 实时观测进度更新
- 更好的用户交互

## 使用方法

### 基本使用
```bash
# 正常运行观测序列
python scripts/new_main.py

# DRYRUN模式（不实际执行观测）
python scripts/new_main.py --dry-run

# 仅验证配置和目标
python scripts/new_main.py --validate

# 显示调度摘要
python scripts/new_main.py --summary

# 指定配置文件
python scripts/new_main.py --config my_config.yaml
```

### 程序化使用
```python
from scripts.lib.new_multi_target_orchestrator import NewMultiTargetOrchestrator

# 创建协调器
orchestrator = NewMultiTargetOrchestrator(
    config_file='multi_target_config.yaml',
    dry_run=False
)

# 添加状态回调
def status_callback(status, data):
    print(f"状态: {status}, 数据: {data}")

orchestrator.add_status_callback(status_callback)

# 验证目标
validation_results = orchestrator.validate_targets()

# 计算调度摘要
summary = orchestrator.calculate_schedule_summary()

# 运行观测序列
results = orchestrator.run_observation_sequence()

# 清理资源
orchestrator.cleanup()
```

## 配置文件

系统使用YAML格式的配置文件，支持以下主要配置项：

### ACP服务器配置
```yaml
acp_server:
  host: "localhost"
  port: 8080
```

### 观测站配置
```yaml
observatory_config:
  name: "我的观测站"
  latitude_deg: 39.9
  longitude_deg: 116.4
  min_altitude: 30.0
  max_airmass: 2.0
```

### 全局设置
```yaml
global_settings:
  log_dir: "logs"
  log_level: "INFO"
  wait_interval_seconds: 60
  max_wait_hours: 24
```

### 目标配置
```yaml
targets:
  - name: "目标1"
    ra: "12:34:56"
    dec: "+78:90:12"
    start_time: "2025-11-28 13:36:00"
    exposure_time: 300
    filter: "L"
    binning: 1
    count: 10
    meridian_flip:
      enabled: true
      wait_before_minutes: 5
      wait_after_minutes: 5
```

## 迁移指南

### 从旧版本迁移
1. 备份现有配置文件
2. 更新配置文件格式（如果需要）
3. 使用新的主程序入口：`new_main.py`
4. 测试DRYRUN模式
5. 验证所有功能正常工作

### 兼容性
- 新的协调器完全向后兼容
- 支持原有的配置文件格式
- 提供相同的API接口

## 开发指南

### 添加新模块
1. 在适当的包目录下创建新模块
2. 遵循现有的代码结构和命名约定
3. 添加适当的文档字符串
4. 更新相关的`__init__.py`文件

### 扩展现有模块
1. 保持向后兼容性
2. 添加适当的错误处理
3. 更新文档和测试
4. 遵循单一职责原则

## 故障排除

### 常见问题
1. **配置文件错误**: 使用`--validate`选项检查配置
2. **连接失败**: 检查ACP服务器状态和网络连接
3. **时间等待问题**: 检查系统时间和时区设置

### 调试模式
```bash
# 启用详细日志
python scripts/new_main.py --config config.yaml 2>&1 | tee debug.log
```

## 更新日志

### v2.0 (当前版本)
- 完全重构的模块化架构
- 增强的配置管理
- 改进的观测工具
- 更好的日志管理
- 灵活的状态回调系统