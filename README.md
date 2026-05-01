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
python douyin_spark.py --setup    # 首次校准（只需一次）
python douyin_spark.py --now      # 立即测试
python douyin_spark.py            # 启动定时任务
```

## 校准说明

运行 `--setup` 后按提示操作：
1. 输入要续几个好友
2. 把鼠标放到「私信图标」上，按回车
3. 把鼠标放到「第1个好友」上，按回车
4. 把鼠标放到「第2个好友」上，按回车
5. 把鼠标放到「输入框」上，按回车
6. 把鼠标放到「关闭会话按钮」上，按回车

坐标保存在 `config.json`，只要屏幕分辨率不变就不用重新校准。

## 配置

编辑 `config.json`：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| message | 发送的消息 | 🔥 |
| top_friends_count | 续几个好友 | 6 |
| send_hour / send_minute | 每天几点发 | 8:00 |
| douyin_path | 抖音路径（自动检测） | - |
| coords | 坐标（--setup 生成） | - |

## 特性

- **一键启动** — 双击 start.bat，自动装依赖、校准、运行
- **自动找抖音** — 不用手动填安装路径
- **休眠补发** — 电脑休眠唤醒后自动补发今天错过的任务
- **窗口置顶** — 运行时自动把抖音置顶，防止被其他窗口遮挡
- **失败通知** — 发送失败弹 Windows 系统通知提醒你

## 注意

- 运行时不要动鼠标
- 鼠标移到屏幕左上角可紧急中断
- 换显示器/改分辨率后需重新 `--setup`
