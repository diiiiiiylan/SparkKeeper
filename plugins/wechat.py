"""微信自动发消息插件（示例）"""

import os
import random
import time
from core.engine import launch_app, click, type_text, press, notify
from core import stats
from plugins import BasePlugin


class WechatPlugin(BasePlugin):
    name = "微信自动消息"
    plugin_id = "wechat"
    icon = "💬"
    description = "每天自动给置顶好友发消息"

    def default_config(self):
        return {
            "messages": ["早安", "🌞", "今天也要加油"],
            "use_random": True,
            "friend_count": 3,
            "send_hour": 8,
            "send_minute": 30,
            "app_path": self._find_wechat(),
            "coords": None,
        }

    def config_fields(self):
        return [
            {"key": "friend_count", "label": "好友数量", "type": "int", "default": 3},
            {"key": "messages", "label": "消息池（逗号分隔）", "type": "list", "default": ["早安"]},
            {"key": "use_random", "label": "随机发送", "type": "bool", "default": True},
            {"key": "send_hour", "label": "发送时间（时）", "type": "int", "default": 8},
            {"key": "send_minute", "label": "发送时间（分）", "type": "int", "default": 30},
            {"key": "app_path", "label": "微信路径", "type": "str", "default": ""},
        ]

    def setup_steps(self):
        return [
            {"key": "first_friend", "prompt": "把鼠标放到第 1 个置顶好友上"},
            {"key": "second_friend", "prompt": "把鼠标放到第 2 个置顶好友上"},
            {"key": "input_box", "prompt": "把鼠标放到聊天输入框上"},
        ]

    def on_calibrated(self, coords):
        if "first_friend" in coords and "second_friend" in coords:
            coords["friend_height"] = coords["second_friend"][1] - coords["first_friend"][1]
        self.config["coords"] = coords
        self.save_config()

    def run(self, log_callback=None):
        def log(msg):
            if log_callback:
                log_callback(msg)

        coords = self.config.get("coords")
        if not coords:
            log("❌ 未校准，请先点击「校准」按钮")
            return

        count = self.config.get("friend_count", 3)
        messages = self.config.get("messages", ["早安"])
        use_random = self.config.get("use_random", True)

        log("启动微信...")
        try:
            win = launch_app(
                self.config.get("app_path", ""),
                title_re=".*微信.*",
                class_re=".*WeChatMainWndForPC.*",
            )
        except Exception as e:
            log(f"❌ 启动失败: {e}")
            return

        success = 0
        for i in range(count):
            msg = random.choice(messages) if use_random else messages[0]
            try:
                x = coords["first_friend"][0]
                y = coords["first_friend"][1] + i * coords.get("friend_height", 65)
                click(x, y, delay=1)
                log(f"  好友 {i+1}: 发送 {msg}")

                click(*coords["input_box"], delay=0.5)
                type_text(msg)
                press("enter", delay=1)
                success += 1
            except Exception as e:
                log(f"  好友 {i+1}: ❌ 失败 - {e}")
            time.sleep(0.5)

        stats.record(self.plugin_id, success, count - success)
        log(f"✅ 完成: {success}/{count} 个好友")

    def _find_wechat(self):
        for drive in "CDEFGH":
            for pf in ["Program Files", "Program Files (x86)"]:
                p = f"{drive}:\\{pf}\\Tencent\\WeChat\\WeChat.exe"
                if os.path.isfile(p):
                    return p
        return ""
