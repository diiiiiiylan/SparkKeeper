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
import random
import logging
import subprocess
import winreg
from datetime import datetime, date, timedelta
from pathlib import Path

import pyautogui
import pyperclip
from pywinauto import Application, findwindows
from apscheduler.schedulers.blocking import BlockingScheduler

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
LAST_RUN_PATH = SCRIPT_DIR / ".last_run"
STATS_PATH = SCRIPT_DIR / "stats.json"

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
    "messages": ["🔥", "早安", "续火花啦", "☀️", "今天也要开心", "👋"],
    "use_random_message": True,
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


# ==================== 统计 ====================

def load_stats():
    if STATS_PATH.exists():
        try:
            return json.loads(STATS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"history": [], "total_sent": 0, "total_failed": 0}


def save_stats(stats):
    STATS_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


def record_stats(success_count, fail_count):
    stats = load_stats()
    today = date.today().isoformat()
    stats["history"].append({
        "date": today,
        "success": success_count,
        "failed": fail_count,
    })
    # 只保留最近 90 天
    stats["history"] = stats["history"][-90:]
    stats["total_sent"] = stats.get("total_sent", 0) + success_count
    stats["total_failed"] = stats.get("total_failed", 0) + fail_count
    save_stats(stats)


def get_streak(stats):
    """计算连续打卡天数"""
    dates = {item["date"] for item in stats["history"] if item["success"] > 0}
    streak = 0
    d = date.today()
    while d.isoformat() in dates:
        streak += 1
        d -= timedelta(days=1)
    return streak


def show_stats():
    stats = load_stats()
    streak = get_streak(stats)
    history = stats["history"]

    print("=" * 50)
    print("  🔥 SparkKeeper 火花统计")
    print("=" * 50)
    print(f"\n  连续打卡: {streak} 天")
    print(f"  累计发送: {stats.get('total_sent', 0)} 条")
    print(f"  累计失败: {stats.get('total_failed', 0)} 条")
    print(f"  记录天数: {len(history)} 天")

    # 最近 30 天打卡日历
    print("\n  最近 30 天:")
    today = date.today()
    dates_ok = {item["date"] for item in history if item["success"] > 0}
    dates_fail = {item["date"] for item in history if item["success"] == 0 and item["failed"] > 0}

    line1 = "  "
    line2 = "  "
    for i in range(29, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        if d in dates_ok:
            line1 += "🔥"
        elif d in dates_fail:
            line1 += "❌"
        else:
            line1 += "⬜"

    print(line1)
    print(f"  {'30天前':<20}{'今天':>10}")

    # 最近 7 天明细
    print("\n  最近 7 天明细:")
    recent = history[-7:] if len(history) >= 7 else history
    for item in recent:
        status = "✓" if item["success"] > 0 else "✗"
        print(f"    {item['date']}  {status}  成功{item['success']} 失败{item['failed']}")

    print()


# ==================== 开机自启动 ====================

def setup_autostart():
    """添加到 Windows 开机启动"""
    python_path = sys.executable
    script_path = str(SCRIPT_DIR / "douyin_spark.py")
    cmd = f'"{python_path}" "{script_path}"'

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, "SparkKeeper", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        print("✓ 已添加到开机启动项")
        print(f"  命令: {cmd}")
        print("  取消: python douyin_spark.py --no-autostart")
    except Exception as e:
        print(f"✗ 添加失败: {e}")


def remove_autostart():
    """从 Windows 开机启动中移除"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, "SparkKeeper")
        winreg.CloseKey(key)
        print("✓ 已从开机启动项移除")
    except FileNotFoundError:
        print("  SparkKeeper 不在开机启动项中")
    except Exception as e:
        print(f"✗ 移除失败: {e}")


# ==================== 火花倒计时 ====================

def check_spark_countdown():
    """检查距离火花熄灭还有多久，快到时弹通知"""
    last = get_last_run_date()
    if not last:
        return
    last_date = date.fromisoformat(last)
    today = date.today()
    days_since = (today - last_date).days

    if days_since >= 1:
        hours_left = max(0, 24 - (datetime.now().hour - 8))
        if hours_left <= 4 and days_since >= 1:
            notify("SparkKeeper ⚠️", f"火花快熄灭了！距上次续火花已过 {days_since} 天")


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

    # 随机消息 or 固定消息
    if config.get("use_random_message") and config.get("messages"):
        message = random.choice(config["messages"])
    else:
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
            # 每个好友可以发不同消息
            if config.get("use_random_message") and config.get("messages"):
                msg = random.choice(config["messages"])
            else:
                msg = message
            try:
                click_friend_by_index(coords, i)
                send_message(coords, msg)
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

        # 记录
        save_last_run_date()
        record_stats(success, len(failed))

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

    if "--stats" in sys.argv:
        show_stats()
        sys.exit(0)

    if "--autostart" in sys.argv:
        setup_autostart()
        sys.exit(0)

    if "--no-autostart" in sys.argv:
        remove_autostart()
        sys.exit(0)

    config = load_config()

    if not config.get("coords"):
        print("首次使用请先校准: python douyin_spark.py --setup")
        sys.exit(1)

    count = config.get("top_friends_count", 6)
    streak = get_streak(load_stats())
    print("SparkKeeper - 抖音自动续火花 🔥")
    print(f"  好友数: {count}")
    if config.get("use_random_message"):
        print(f"  消息池: {config.get('messages', ['🔥'])}")
    else:
        print(f"  消息: {config.get('message', '🔥')}")
    print(f"  定时: 每天 {config['send_hour']:02d}:{config['send_minute']:02d}")
    print(f"  连续打卡: {streak} 天 🔥")
    print("  Ctrl+C 退出\n")

    if "--now" in sys.argv:
        run_task()
        sys.exit(0)

    # 启动时检查火花倒计时
    check_spark_countdown()

    # 休眠补发
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
    # 每 10 分钟检查一次是否错过任务
    scheduler.add_job(
        lambda: run_task() if missed_today(load_config()) else None,
        "interval",
        minutes=10,
        id="missed_check",
    )
    # 每小时检查火花倒计时
    scheduler.add_job(
        check_spark_countdown,
        "interval",
        hours=1,
        id="countdown_check",
    )
    log.info(f"定时任务已启动，每天 {config['send_hour']:02d}:{config['send_minute']:02d} 执行")
    scheduler.start()