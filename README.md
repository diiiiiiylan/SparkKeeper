# SparkKeeper 🔥

抖音 Windows 客户端自动续火花。每天定时给置顶好友发消息，保持火花不灭。

## 一键使用

1. 安装 [Python 3.8+](https://www.python.org/downloads/)（安装时勾选 Add to PATH）
2. 下载本项目
3. 双击 `start.bat`

完事。首次运行会自动安装依赖并引导你校准。

## 手动使用

```bash
pip install pyautogui pywinauto pyperclip apscheduler
python douyin_spark.py --setup       # 首次校准（只需一次）
python douyin_spark.py --now         # 立即测试
python douyin_spark.py               # 启动定时任务
python douyin_spark.py --stats       # 查看火花统计
python douyin_spark.py --autostart   # 设置开机自启
```

## 功能

### 🎲 随机消息池
每次给每个好友发不同的消息，不会被发现是机器人。
在 `config.json` 中自定义消息池：
```json
"messages": ["🔥", "早安", "续火花啦", "☀️", "今天也要开心", "👋"],
"use_random_message": true
```

### 📊 火花统计 (--stats)
```
  🔥 SparkKeeper 火花统计
  连续打卡: 15 天
  累计发送: 90 条
  最近 30 天:
  🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥🔥⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜
```

### 🚀 开机自启动 (--autostart)
一条命令加入 Windows 启动项，开机自动续火花：
```bash
python douyin_spark.py --autostart      # 开启
python douyin_spark.py --no-autostart   # 关闭
```

### ⏰ 火花倒计时
快到时间还没续？自动弹 Windows 通知提醒你。

### 😴 休眠补发
电脑休眠唤醒后，自动检测今天是否错过，错过了立即补发。

### 🪟 窗口置顶
运行时自动把抖音窗口置顶，防止被其他窗口遮挡导致点击偏移。

### 🔔 失败通知
发送失败弹 Windows 系统通知，不会让火花悄悄灭掉。

## 校准说明

运行 `--setup` 后按提示操作：
1. 输入要续几个好友
2. 把鼠标放到「私信图标」上，按回车
3. 放到「第1个好友」上，按回车
4. 放到「第2个好友」上，按回车
5. 放到「输入框」上，按回车
6. 放到「关闭会话按钮」上，按回车

坐标保存在 `config.json`，分辨率不变就不用重新校准。

## 配置

编辑 `config.json`：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| message | 固定消息（关闭随机时用） | 🔥 |
| messages | 随机消息池 | ["🔥","早安",...] |
| use_random_message | 是否随机发送 | true |
| top_friends_count | 续几个好友 | 6 |
| send_hour / send_minute | 每天几点发 | 8:00 |
| douyin_path | 抖音路径（自动检测） | - |
| coords | 坐标（--setup 生成） | - |

## 注意

- 运行时不要动鼠标
- 鼠标移到屏幕左上角可紧急中断
- 换显示器/改分辨率后需重新 `--setup`

## License

MIT
