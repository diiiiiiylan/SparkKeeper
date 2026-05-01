"""SparkKeeper core - 通用自动化引擎"""

import time
import ctypes
import subprocess
import pyautogui
import pyperclip
from pywinauto import Application, findwindows


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


def find_window(title_re=None, class_re=None):
    """查找窗口"""
    try:
        handles = []
        if title_re:
            handles = findwindows.find_windows(title_re=title_re, visible_only=True)
        if not handles and class_re:
            handles = findwindows.find_windows(class_name_re=class_re)
        if handles:
            return Application(backend="uia").connect(handle=handles[0])
    except Exception:
        pass
    return None


def activate_window(app):
    """激活并置顶窗口"""
    win = app.top_window()
    if win.is_minimized():
        win.restore()
    win.set_focus()
    try:
        ctypes.windll.user32.SetForegroundWindow(win.handle)
        ctypes.windll.user32.BringWindowToTop(win.handle)
    except Exception:
        pass
    time.sleep(1)
    return win


def launch_app(exe_path, title_re=None, class_re=None, timeout=25):
    """启动应用并等待窗口出现"""
    app = find_window(title_re, class_re)
    if app:
        return activate_window(app)

    subprocess.Popen(exe_path)
    time.sleep(5)
    for _ in range(timeout // 2):
        app = find_window(title_re, class_re)
        if app:
            return activate_window(app)
        time.sleep(2)
    raise RuntimeError(f"无法启动应用: {exe_path}")


def type_text(text):
    """通过剪贴板输入文字（支持中文）"""
    pyperclip.copy(text)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)


def click(x, y, delay=1.0):
    """点击坐标"""
    pyautogui.click(x, y)
    time.sleep(delay)


def press(key, delay=0.5):
    """按键"""
    pyautogui.press(key)
    time.sleep(delay)


def notify(title, msg):
    """Windows 系统通知"""
    try:
        ps = (
            '[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;'
            '$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(0);'
            f'$t.GetElementsByTagName("text").Item(0).AppendChild($t.CreateTextNode("{title}: {msg}")) > $null;'
            '$n = [Windows.UI.Notifications.ToastNotification]::new($t);'
            '[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("SparkKeeper").Show($n)'
        )
        subprocess.Popen(["powershell", "-Command", ps], creationflags=0x08000000)
    except Exception:
        try:
            ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)
        except Exception:
            pass
