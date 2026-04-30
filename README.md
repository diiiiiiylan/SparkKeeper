# SparkKeeper 🔥

抖音 Windows 客户端自动续火花工具。每天定时给置顶好友发消息，保持火花不灭。

## 原理

通过 pyautogui 模拟鼠标键盘操作抖音 Windows 客户端，自动点击私信面板中的置顶好友并发送消息。

## 安装

```bash
pip install pyautogui pywinauto pyperclip apscheduler
```

## 快速开始

### 1. 准备工作
- 打开抖音 Windows 客户端并登录
- 把要续火花的好友在私信列表中**置顶**

### 2. 首次校准
```bash
python douyin_spark.py --setup
```
按提示把鼠标放到 4 个位置（私信图标、好友、输入框、关闭按钮），每次放好按回车。坐标会自动保存到 `config.json`。

### 3. 测试
```bash
python douyin_spark.py --now
```
运行时不要动鼠标，观察是否正常发送。

### 4. 启动定时任务
```bash
python douyin_spark.py
```
默认每天早上 8:00 自动执行。

## 配置

编辑 `config.json`：

| 字段 | 说明 | 默认值 |
|------|------|--------|
| message | 发送的消息内容 | 🔥 |
| top_friends_count | 置顶好友数量 | 6 |
| send_hour / send_minute | 每天几点执行 | 8:00 |
| douyin_path | 抖音安装路径（留空则需手动打开抖音） | - |
| coords | 校准坐标（--setup 自动生成） | - |

## 注意事项

- 运行时不要移动鼠标，程序需要控制鼠标操作
- 鼠标移到屏幕左上角可紧急中断（pyautogui failsafe）
- 更换显示器或调整分辨率后需要重新 `--setup` 校准
- 抖音客户端更新界面后可能需要重新校准
