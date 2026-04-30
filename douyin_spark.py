"""
抖音 Windows 客户端 - 自动续火花
直接点击私信面板中置顶的好友发消息，无需搜索。

使用前：
  1. pip install pyautogui pywinauto pyperclip apscheduler
  2. 确保抖音 Windows 客户端已安装并登录
  3. 把要续火花的好友在私信列表里置顶
  4. 编辑 config.json 调整参数
  5. python douyin_spark.py --now  测试一次
  6. python douyin_spark.py        启动定时任务
"""

import json
import sys
import time
import logging
import subprocess
from pathlib import Path

import pyautogui
import pyperclip
from pywinauto import Application, findwindows
from apscheduler.schedulers.blocking import BlockingScheduler

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(SCRIPT_DIR / "douyin_spark.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ==================== 配置 ====================

def load_config():
    if not CONFIG_PATH.exists():
        default = {
            "message": "早上好",
            "top_friends_count": 6,
            "send_hour": 8,
            "send_minute": 0,
            "douyin_path": r"D:\Program Files (x86)\ByteDance\douyin\Douyin.exe",
        }
        CONFIG_PATH.write_text(json.dumps(default, ensure_ascii=False, indent=4), encoding="utf-8")
        log.info(f"已生成默认配置: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


# ==================== 窗口管理 ====================

def find_douyin_window():
    try:
        handles = findwindows.find_windows(title_re=".*抖音.*", visible_only=True)
        if not handles:
            handles = findwindows.find_windows(class_name_re=".*Douyin.*")
        if handles:
            app = Application(backend="uia").connect(handle=handles[0])
            return app
    except Exception:
        pass
    return None


def activate_douyin(douyin_path):
    app = find_douyin_window()
    if app is None:
        log.info("抖音未运行，正在启动...")
        subprocess.Popen(douyin_path)
        time.sleep(5)
        for _ in range(10):
            app = find_douyin_window()
            if app:
                break
            time.sleep(2)
        if app is None:
            raise RuntimeError("无法启动抖音")

    win = app.top_window()
    if win.is_minimized():
        win.restore()
    win.set_focus()
    time.sleep(1)
    log.info("抖音窗口已激活")
    return win


# ==================== 核心操作 ====================

def type_chinese(text):
    pyperclip.copy(text)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)


def open_private_messages():
    """点击右上角私信图标"""
    pyautogui.click(3231, 103)
    time.sleep(2)
    log.info("已打开私信面板")


def click_friend_by_index(index):
    """点击私信列表中第 index 个置顶好友 (从0开始)
    好友列表从搜索框下方开始，每个好友大约占 72px 高度
    """
    base_x = 3349
    base_y = 298
    friend_height = 100

    y = base_y + index * friend_height
    pyautogui.click(base_x, y)
    time.sleep(1.5)
    log.info(f"已点击第 {index + 1} 个好友")


def send_message(text):
    """在聊天框输入消息并发送"""
    pyautogui.click(3139, 1141)
    time.sleep(0.5)
    type_chinese(text)
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(1)
    log.info(f"已发送: {text}")


def close_chat():
    """关闭聊天框，保留好友栏"""
    pyautogui.click(3381, 199)
    time.sleep(1)
    log.info("已关闭聊天框")


# ==================== 主任务 ====================

def run_task():
    config = load_config()
    message = config.get("message", "早上好")
    count = config.get("top_friends_count", 6)
    log.info("===== 开始续火花任务 =====")

    try:
        win = activate_douyin(config["douyin_path"])
        time.sleep(1)

        open_private_messages()

        success = 0
        for i in range(count):
            try:
                click_friend_by_index(i)
                send_message(message)
                close_chat()
                success += 1
            except Exception as e:
                log.error(f"第 {i + 1} 个好友失败: {e}")
                try:
                    close_chat()
                except Exception:
                    pass
            time.sleep(0.5)

        log.info(f"完成: {success}/{count} 个好友")

        # 关闭私信面板（点击私信图标收起）
        pyautogui.click(3231, 103)
        time.sleep(0.5)

    except Exception as e:
        log.error(f"任务失败: {e}")


# ==================== 入口 ====================

if __name__ == "__main__":
    config = load_config()
    count = config.get("top_friends_count", 6)
    print("抖音 Windows 客户端 - 自动续火花")
    print(f"置顶好友数: {count}")
    print(f"发送内容: {config.get('message', '早上好')}")
    print(f"每天 {config['send_hour']:02d}:{config['send_minute']:02d} 自动执行")
    print("Ctrl+C 退出\n")

    if "--now" in sys.argv:
        run_task()
        sys.exit(0)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_task,
        "cron",
        hour=config["send_hour"],
        minute=config["send_minute"],
        id="douyin_spark",
    )
    log.info(f"定时任务已启动，每天 {config['send_hour']:02d}:{config['send_minute']:02d} 执行")
    scheduler.start()
