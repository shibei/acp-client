# 自动中天等待开关功能说明

## 功能概述

在每个子任务（目标观测）中添加了自动中天等待的开关功能，允许用户为每个目标单独控制是否启用中天等待。

## 配置方法

在 `multi_target_config.yaml` 文件中，为每个目标添加 `enable_meridian_wait` 参数：

```yaml
targets:
  - name: 'ic 405'
    ra: '05:16:30.00'
    dec: '34:21:00.0'
    start_time: '2025-11-29 19:34:00'
    priority: 2
    meridian_time: '02:11:00'      # 可选：手动指定中天时间
    enable_meridian_wait: true     # 启用中天等待（默认true，可省略）
    filters:
      - filter_id: 6
        name: 'OIII'
        exposure: 600
        count: 6
        binning: 1

  - name: 'ic 405'
    ra: '05:16:30.00'
    dec: '34:21:00.0'
    start_time: '2025-11-29 02:30:00'
    priority: 2
    meridian_time: '02:11:00'      # 可选：手动指定中天时间
    enable_meridian_wait: false     # 禁用此目标的中天等待
    filters:
      - filter_id: 5
        name: 'SII'
        exposure: 600
        count: 6
        binning: 1
```

## 参数说明

- `enable_meridian_wait`: 布尔值，控制是否启用该目标的中天等待
  - `true` (默认): 启用中天等待，系统会在需要时等待中天反转
  - `false`: 禁用中天等待，该目标不会触发中天等待逻辑

## 实现细节

### 1. 配置管理器 (config_manager.py)

在 `TargetConfig` 类中添加了 `enable_meridian_wait` 字段：

```python
@dataclass
class TargetConfig:
    name: str
    ra: str
    dec: str
    start_time: str
    priority: int
    filters: List[FilterConfig]
    meridian_time: Optional[str] = None
    enable_meridian_wait: bool = True  # 新增字段，默认启用
```

### 2. 目标观测执行器 (target_observation_executor.py)

修改了 `_check_meridian_flip` 方法，优先检查目标的中天等待开关：

```python
def _check_meridian_flip(self, target: Any, current_time: datetime) -> Dict[str, Any]:
    """检查中天反转"""
    # 如果目标配置中关闭了中天等待，直接返回不需要等待
    if hasattr(target, 'enable_meridian_wait') and not target.enable_meridian_wait:
        return {
            'status': 'disabled',
            'message': '该目标已禁用中天等待',
            'wait_needed': False,
            'disabled_by_target': True
        }
    
    # 如果中天管理器可用，使用实际的中天反转检查
    if self.meridian_manager:
        try:
            return self.meridian_manager.check_meridian_flip_needed(
                target.ra, target.dec, current_time
            )
        except Exception as e:
            return {
                'status': 'error',
                'message': f'中天反转检查出错: {str(e)}',
                'wait_needed': False
            }
    
    # 如果中天管理器不可用，返回默认信息
    return {
        'check_needed': False,
        'wait_needed': False,
        'message': '中天反转检查未启用'
    }
```

### 3. 状态显示

更新了状态显示函数，能够显示中天等待开关的状态：

```python
# 中天反转信息
meridian_info = status['meridian_info']
if meridian_info.get('wait_needed'):
    status_msg += f" | 中天反转: {meridian_info['message']}"
elif meridian_info.get('status') == 'disabled':
    status_msg += f" | 中天反转: 已禁用"
elif meridian_info.get('status') == 'error':
    status_msg += f" | 中天反转: 错误"
```

## 使用场景

1. **需要中天等待的目标**: 保持默认值 `true` 或省略该参数
2. **不需要中天等待的目标**: 设置为 `false`

这个功能特别适用于：
- 快速观测任务，不想等待中天反转
- 中天时间附近的目标，可以禁用等待以节省时间
- 测试和调试场景

## 注意事项

- 该参数是可选的，默认为 `true`
- 只对当前目标生效，不影响其他目标的中天等待行为
- 系统会记录每个目标的中天等待开关状态，便于调试和监控