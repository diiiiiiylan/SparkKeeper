# SparkKeeper 🔥

抖音 Windows 客户端自动续火花工具。每天定时给置顶好友发消息，保持火花不灭。

## 原理

通过 pyautogui 模拟鼠标键盘操作抖音 Windows 客户端，自动点击私信面板中的置顶好友并发送消息。

## 安装

```bash
pip install pyautogui pywinauto pyperclip apscheduler
```

## 使用

1. 打开抖音 Windows 客户端，登录账号
2. 把要续火花的好友在私信列表中**置顶**
3. 编辑 `config.json` 配置参数
4. 测试运行：`python douyin_spark.py --now`
5. 启动定时任务：`python douyin_spark.py`

## 配置

编辑 `config.json`：

```json
{
    "message": "🔥",
    "top_friends_count": 6,
    "send_hour": 8,
    "send_minute": 0,
    "douyin_path": "D:\\Program Files (x86)\\ByteDance\\douyin\\Douyin.exe"
}
```

| 字段 | 说明 |
|------|------|
| message | 发送的消息内容 |
| top_friends_count | 置顶好友数量 |
| send_hour / send_minute | 每天几点执行 |
| douyin_path | 抖音安装路径 |

## 坐标校准

脚本中的点击坐标基于特定屏幕分辨率。如果点击位置不准，运行坐标工具查看实际位置：

```bash
python -c "import pyautogui,time;[print(pyautogui.position()) or time.sleep(1) for _ in range(30)]"
```

然后修改 `douyin_spark.py` 中对应的坐标值。

## 注意事项

- 运行时不要移动鼠标，程序需要控制鼠标操作
- 鼠标移到屏幕左上角可紧急中断（pyautogui failsafe）
- 抖音客户端更新后可能需要重新校准坐标
- 建议先用 `--now` 测试确认无误后再启动定时任务
