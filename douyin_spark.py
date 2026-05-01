"""
SparkKeeper - 抖音 Windows 客户端自动续火花
https://github.com/diiiiiiylan/SparkKeeper

功能：
  - 自动给私信置顶好友发消息续火花
  - 交互式校准，适配任何屏幕分辨率
  - 自动查找抖音安装路径
  - 休眠/锁屏唤醒后自动补发
  - 发送失败弹 Windows 通知提醒

用法：
  首次校准:  python douyin_spark.py --setup
  立即测试:  python douyin_spark.py --now
  定时运行:  python douyin_spark.py
  或直接双击 start.bat
"""

import json
import sys
import os
import glob
import time
import ctypes
import logging
import subprocess
from datetime import datetime, date
from pathlib import Path

import pyautogui
import pyperclip
from pywinauto import Application, findwindows
from apscheduler.schedulers.blocking import BlockingScheduler

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
LAST_RUN_PATH = SCRIPT_DIR / ".last_run"

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
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=4), encoding="utf-8"
    )


# ==================== Windows 通知 ====================

def notify(title, msg):
    try:
        ps = (
            '[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;'
            '$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(0);'
            f'$t.GetElementsByTagName("text").Item(0).AppendChild($t.CreateTextNode("{title}: {msg}")) > $null;'
            '$n = [Windows.UI.Notifications.ToastNotification]::new($t);'
            '[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("SparkKeeper").Show($n)'
        )
        subprocess.Popen(
            ["powershell", "-Command", ps],
            creationflags=0x08000000,
        )
    except Exception:
        try:
            ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)
        except Exception:
            pass


# ==================== 自动查找抖音 ====================

def find_douyin_path():
    candidates = []
    for drive in "CDEFGH":
        for pf in ["Program Files", "Program Files (x86)"]:
            candidates.append(f"{drive}:\\{pf}\\Douyin\\Douyin.exe")
            candidates.append(f"{drive}:\\{pf}\\ByteDance\\douyin\\Douyin.exe")
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if localappdata:
        candidates.append(os.path.join(localappdata, "Douyin", "Douyin.exe"))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return ""


# ==================== 运行记录（休眠补发） ====================

def get_last_run_date():
    if LAST_RUN_PATH.exists():
        try:
            return LAST_RUN_PATH.read_text().strip()
        except Exception:
            pass
    return ""


def save_last_run_date():
    LAST_RUN_PATH.write_text(date.today().isoformat())


def missed_today(config):
    last = get_last_run_date()
    if last == date.today().isoformat():
        return False
    now = datetime.now()
    scheduled = now.replace(
        hour=config["send_hour"], minute=config["send_minute"], second=0
    )
    return now > scheduled


# ==================== 校准 ====================

def wait_for_click(prompt_text):
    print(f"\n  👉 {prompt_text}")
    print("     把鼠标放到对应位置，然后按回车...")
    input()
    pos = pyautogui.position()
    print(f"     ✓ 记录坐标: ({pos.x}, {pos.y})")
    return [pos.x, pos.y]


def setup():
    config = load_config()

    print("=" * 50)
    print("  SparkKeeper 首次校准（只需校准一次）")
    print("=" * 50)

    # 自动查找抖音路径
    if not config.get("douyin_path"):
        found = find_douyin_path()
        if found:
            config["douyin_path"] = found
            print(f"\n  自动找到抖音: {found}")
        else:
            print("\n  未找到抖音，请手动输入安装路径")
            print("  (例如: D:\\Program Files (x86)\\ByteDance\\douyin\\Douyin.exe)")
            path = input("  路径: ").strip().strip('"')
            config["douyin_path"] = path

    # 好友数量
    while True:
        count = input("\n  你要续几个好友的火花？(直接回车默认6): ").strip()
        if not count:
            config["top_friends_count"] = 6
            break
        if count.isdigit() and int(count) > 0:
            config["top_friends_count"] = int(count)
            break
        print("  请输入一个正整数")

    print(f"\n  好，续 {config['top_friends_count']} 个好友。")
    print("  请先打开抖音，确保能看到主界面。")
    print("  接下来把鼠标放到指定位置，放好后按回车。")

    input("\n  准备好了按回车开始...")

    coords = {}
    coords["private_msg_icon"] = wait_for_click("鼠标放到右上角「私信」图标上")

    print("\n  正在打开私信面板...")
    pyautogui.click(*coords["private_msg_icon"])
    time.sleep(2)

    coords["first_friend"] = wait_for_click("鼠标放到第 1 个置顶好友上")
    coords["second_friend"] = wait_for_click("鼠标放到第 2 个置顶好友上")

    print("\n  正在打开聊天...")
    pyautogui.click(*coords["first_friend"])
    time.sleep(1.5)

    coords["input_box"] = wait_for_click("鼠标放到聊天输入框上")
    coords["close_chat"] = wait_for_click("鼠标放到关闭会话按钮上（叉号旁边那个）")

    coords["friend_height"] = coords["second_friend"][1] - coords["first_friend"][1]
    config["coords"] = coords
    save_config(config)

    print("\n" + "=" * 50)
    print("  ✓ 校准完成！")
    print(f"  ✓ 好友数: {config['top_friends_count']}")
    print(f"  ✓ 好友间距: {coords['friend_height']}px")
    print(f"  ✓ 抖音路径: {config['douyin_path']}")
    print(f"  ✓ 每天 {config['send_hour']:02d}:{config['send_minute']:02d} 自动发送")
    print("=" * 50)
    print("\n  测试: python douyin_spark.py --now")
    print("  启动: python douyin_spark.py")


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
            raise RuntimeError("抖音未运行，且未设置安装路径，请运行 --setup")
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
    # 置顶窗口，防止被遮挡
    try:
        hwnd = win.handle
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        ctypes.windll.user32.BringWindowToTop(hwnd)
    except Exception:
        pass
    time.sleep(1)
    log.info("抖音窗口已激活并置顶")
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
        log.error("未校准坐标，请先运行: python douyin_spark.py --setup")
        notify("SparkKeeper", "未校准，请运行 --setup")
        return

    message = config.get("message", "🔥")
    count = config.get("top_friends_count", 6)
    log.info("===== 开始续火花任务 =====")

    try:
        win = activate_douyin(config.get("douyin_path", ""))
        time.sleep(1)
        open_private_messages(coords)

        success = 0
        failed = []
        for i in range(count):
            try:
                click_friend_by_index(coords, i)
                send_message(coords, message)
                close_chat(coords)
                success += 1
            except Exception as e:
                log.error(f"第 {i + 1} 个好友失败: {e}")
                failed.append(i + 1)
                try:
                    close_chat(coords)
                except Exception:
                    pass
            time.sleep(0.5)

        log.info(f"完成: {success}/{count} 个好友")

        # 收起私信面板
        pyautogui.click(*coords["private_msg_icon"])
        time.sleep(0.5)

        # 记录今天已运行
        save_last_run_date()

        # 失败通知
        if failed:
            notify("SparkKeeper", f"第 {','.join(map(str, failed))} 个好友发送失败！")

    except Exception as e:
        log.error(f"任务失败: {e}")
        notify("SparkKeeper", f"续火花失败: {e}")


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
    print("SparkKeeper - 抖音自动续火花 🔥")
    print(f"  好友数: {count}")
    print(f"  消息: {config.get('message', '🔥')}")
    print(f"  定时: 每天 {config['send_hour']:02d}:{config['send_minute']:02d}")
    print("  Ctrl+C 退出\n")

    if "--now" in sys.argv:
        run_task()
        sys.exit(0)

    # 启动时检查是否错过了今天的任务（休眠补发）
    if missed_today(config):
        log.info("检测到今天的任务被错过（可能因休眠），立即补发")
        run_task()

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_task,
        "cron",
        hour=config["send_hour"],
        minute=config["send_minute"],
        id="douyin_spark",
    )
    # 每 10 分钟检查一次是否错过任务（应对休眠唤醒）
    scheduler.add_job(
        lambda: run_task() if missed_today(load_config()) else None,
        "interval",
        minutes=10,
        id="missed_check",
    )
    log.info(f"定时任务已启动，每天 {config['send_hour']:02d}:{config['send_minute']:02d} 执行")
    scheduler.start()