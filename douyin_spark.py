"""
SparkKeeper - 抖音 Windows 客户端自动续火花
直接点击私信面板中置顶的好友发消息，保持火花不灭。

使用前：
  1. pip install pyautogui pywinauto pyperclip apscheduler
  2. 确保抖音 Windows 客户端已安装并登录
  3. 把要续火花的好友在私信列表中置顶
  4. 首次运行: python douyin_spark.py --setup  (校准坐标)
  5. 测试运行: python douyin_spark.py --now
  6. 启动定时: python douyin_spark.py
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

DEFAULT_CONFIG = {
    "message": "🔥",
    "top_friends_count": 6,
    "send_hour": 8,
    "send_minute": 0,
    "douyin_path": "",
    "coords": None,
}


def load_config():
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        log.info(f"已生成默认配置: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=4), encoding="utf-8")


# ==================== 校准 ====================

def wait_for_click(prompt_text):
    """提示用户把鼠标放到指定位置，按回车记录坐标"""
    print(f"\n  👉 {prompt_text}")
    print("     把鼠标放到对应位置，然后按回车...")
    input()
    pos = pyautogui.position()
    print(f"     记录坐标: ({pos.x}, {pos.y})")
    return [pos.x, pos.y]


def setup():
    """交互式校准坐标"""
    config = load_config()

    print("=" * 50)
    print("  SparkKeeper 首次校准")
    print("=" * 50)
    print("\n请先打开抖音，确保能看到主界面。")
    print("接下来会让你把鼠标放到 4 个位置，每次放好后按回车。\n")

    input("准备好了按回车开始...")

    coords = {}
    coords["private_msg_icon"] = wait_for_click("鼠标放到右上角「私信」图标上")

    print("\n  现在请点开私信面板...")
    pyautogui.click(*coords["private_msg_icon"])
    time.sleep(2)

    coords["first_friend"] = wait_for_click("鼠标放到第 1 个置顶好友上")
    coords["second_friend"] = wait_for_click("鼠标放到第 2 个置顶好友上")

    print("\n  现在请点开任意一个好友的聊天...")
    pyautogui.click(*coords["first_friend"])
    time.sleep(1.5)

    coords["input_box"] = wait_for_click("鼠标放到聊天输入框上")
    coords["close_chat"] = wait_for_click("鼠标放到关闭会话按钮上")

    # 计算好友间距
    friend_height = coords["second_friend"][1] - coords["first_friend"][1]
    coords["friend_height"] = friend_height

    config["coords"] = coords
    save_config(config)

    print("\n" + "=" * 50)
    print("  校准完成！坐标已保存到 config.json")
    print(f"  好友间距: {friend_height}px")
    print("=" * 50)
    print("\n现在可以运行: python douyin_spark.py --now")

    # 如果没有设置抖音路径，提示设置
    if not config.get("douyin_path"):
        print("\n提示: config.json 中的 douyin_path 为空")
        print("请填入抖音安装路径，例如:")
        print('  "douyin_path": "D:\\\\Program Files (x86)\\\\ByteDance\\\\douyin\\\\Douyin.exe"')


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
        if not douyin_path:
            raise RuntimeError("抖音未运行，且 config.json 中未设置 douyin_path")
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


def open_private_messages(coords):
    pyautogui.click(*coords["private_msg_icon"])
    time.sleep(2)
    log.info("已打开私信面板")


def click_friend_by_index(coords, index):
    x = coords["first_friend"][0]
    y = coords["first_friend"][1] + index * coords["friend_height"]
    pyautogui.click(x, y)
    time.sleep(1.5)
    log.info(f"已点击第 {index + 1} 个好友")


def send_message(coords, text):
    pyautogui.click(*coords["input_box"])
    time.sleep(0.5)
    type_chinese(text)
    time.sleep(0.3)
    pyautogui.press("enter")
    time.sleep(1)
    log.info(f"已发送: {text}")


def close_chat(coords):
    pyautogui.click(*coords["close_chat"])
    time.sleep(1)
    log.info("已关闭聊天框")


# ==================== 主任务 ====================

def run_task():
    config = load_config()
    coords = config.get("coords")
    if not coords:
        print("错误: 未校准坐标，请先运行: python douyin_spark.py --setup")
        sys.exit(1)

    message = config.get("message", "🔥")
    count = config.get("top_friends_count", 6)
    log.info("===== 开始续火花任务 =====")

    try:
        win = activate_douyin(config.get("douyin_path", ""))
        time.sleep(1)

        open_private_messages(coords)

        success = 0
        for i in range(count):
            try:
                click_friend_by_index(coords, i)
                send_message(coords, message)
                close_chat(coords)
                success += 1
            except Exception as e:
                log.error(f"第 {i + 1} 个好友失败: {e}")
                try:
                    close_chat(coords)
                except Exception:
                    pass
            time.sleep(0.5)

        log.info(f"完成: {success}/{count} 个好友")

        # 收起私信面板
        pyautogui.click(*coords["private_msg_icon"])
        time.sleep(0.5)

    except Exception as e:
        log.error(f"任务失败: {e}")


# ==================== 入口 ====================

if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup()
        sys.exit(0)

    config = load_config()

    if not config.get("coords"):
        print("首次使用请先校准: python douyin_spark.py --setup")
        sys.exit(1)

    count = config.get("top_friends_count", 6)
    print("SparkKeeper - 抖音自动续火花")
    print(f"置顶好友数: {count}")
    print(f"发送内容: {config.get('message', '🔥')}")
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
