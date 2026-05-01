# SparkKeeper 🔥

自动续火花工具，支持抖音、微信等多个 App。可视化界面，一键校准，定时执行。

## 一键使用

1. 安装 [Python 3.8+](https://www.python.org/downloads/)（勾选 Add to PATH）
2. 下载本项目
3. 双击 `start.bat`

## 界面预览

```
┌──────────┬─────────────────────────────────┐
│ 应用列表  │ 🔥 抖音续火花                     │
│          │ 每天自动给置顶好友发消息续火花        │
│ 🔥 抖音   │                                  │
│ 💬 微信   │ 好友数量: [6]                     │
│          │ 消息池:   [🔥,早安,续火花啦]         │
│          │ 随机发送: [✓]                      │
│          │ 发送时间: [08:00]                  │
│          │                                  │
│          │ [🎯校准] [▶执行] [⏰定时] [💾保存]  │
│          │                                  │
│          │ [日志输出区域]                      │
│          │                                  │
│          │ ✅已校准 | 连续15天 | 🔥🔥🔥🔥🔥    │
└──────────┴─────────────────────────────────┘
```

## 功能

- **可视化界面** — 不用敲命令，所有操作点点就行
- **多 App 支持** — 插件化架构，抖音/微信/更多 App
- **一键校准** — 按 F8 标记位置，自动保存坐标
- **随机消息池** — 每个好友发不同消息
- **定时执行** — 设好时间自动跑
- **火花统计** — 连续打卡天数、14天日历
- **失败通知** — Windows 系统通知提醒

## 项目结构

```
├── app.py              # GUI 主程序（入口）
├── core/
│   ├── engine.py       # 通用自动化引擎
│   ├── scheduler.py    # 定时调度器
│   └── stats.py        # 统计模块
├── plugins/
│   ├── __init__.py     # 插件基类
│   ├── douyin.py       # 抖音续火花
│   └── wechat.py       # 微信自动消息
├── configs/            # 每个 App 的配置（自动生成）
├── start.bat           # 一键启动
└── README.md
```

## 添加新插件

继承 `BasePlugin`，实现几个方法就行：

```python
from plugins import BasePlugin

class MyPlugin(BasePlugin):
    name = "我的插件"
    plugin_id = "my_plugin"
    icon = "⭐"

    def config_fields(self):
        return [{"key": "count", "label": "数量", "type": "int", "default": 3}]

    def setup_steps(self):
        return [{"key": "button", "prompt": "鼠标放到按钮上"}]

    def run(self, log_callback=None):
        # 你的自动化逻辑
        pass
```

然后在 `app.py` 的 `ALL_PLUGINS` 列表里加上就行。

## 注意

- 校准时按 **F8** 确认鼠标位置
- 执行时不要动鼠标
- 鼠标移到屏幕左上角可紧急中断
- 换显示器/改分辨率后需重新校准

## License

MIT
