# 自动观测脚本配置说明

## 快速开始

### 1. 创建配置文件模板

```bash
python auto_observe_ngc1499.py --create-template
```

这将创建一个 `observation_config.yaml` 配置文件模板。

### 2. 编辑配置文件

编辑 `observation_config.yaml`，设置你的观测参数：

```yaml
schedule:
  stop_time: '2025-11-19 23:30:00'  # 可选
  start_time: '2025-11-19 23:39:00'  # 必填

target:
  name: 'NGC 1499'
  ra: '04:01:07.51'
  dec: '+36:31:11.9'

imaging:
  filter_id: 4
  exposure_time: 600
  image_count: 30
```

### 3. 运行脚本

```bash
# 使用默认配置文件 (observation_config.yaml)
python auto_observe_ngc1499.py

# 或指定配置文件
python auto_observe_ngc1499.py my_observation.yaml
```

## 配置参数说明

### schedule（时间安排）
- `stop_time`: 停止当前计划的时间（可选，格式：'YYYY-MM-DD HH:MM:SS'）
- `start_time`: 启动新计划的时间（必填，格式：'YYYY-MM-DD HH:MM:SS'）

### acp_server（ACP服务器）
- `url`: ACP服务器地址
- `username`: 用户名
- `password`: 密码

### target（目标天体）
- `name`: 目标名称
- `ra`: 赤经（格式：'HH:MM:SS.SS'）
- `dec`: 赤纬（格式：'+DD:MM:SS.S'）

### imaging（成像参数）
- `filter_id`: 滤镜ID（0=L, 1=R, 2=G, 3=B, 4=H-alpha, 5=O-III, 6=S-II）
- `exposure_time`: 单张曝光时间（秒）
- `image_count`: 图像数量
- `binning`: 像素合并（1=1x1, 2=2x2）
- `dither`: 抖动距离（像素）
- `auto_focus`: 自动对焦（true/false）
- `af_interval`: 对焦间隔（分钟）

## 示例

### 示例1：只启动新计划（不停止当前计划）

```yaml
schedule:
  # 不设置 stop_time
  start_time: '2025-11-20 02:30:00'

target:
  name: 'M31'
  ra: '00:42:44.3'
  dec: '+41:16:09'

imaging:
  filter_id: 0  # L滤镜
  exposure_time: 300
  image_count: 50
```

### 示例2：先停止再启动

```yaml
schedule:
  stop_time: '2025-11-20 01:00:00'
  start_time: '2025-11-20 02:30:00'

target:
  name: 'NGC 1499'
  ra: '04:01:07.51'
  dec: '+36:31:11.9'

imaging:
  filter_id: 4  # H-alpha
  exposure_time: 600
  image_count: 30
```

## 注意事项

1. 时间格式必须严格遵守 `'YYYY-MM-DD HH:MM:SS'` 格式
2. 如果不需要停止当前计划，直接删除或注释 `stop_time` 行
3. 确保配置文件编码为 UTF-8
4. 坐标格式需要与ACP兼容
