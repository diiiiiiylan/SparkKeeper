"""抖音续火花插件"""

import os
import random
import time
from core.engine import launch_app, click, type_text, press, notify
from core import stats
from plugins import BasePlugin


class DouyinSparkPlugin(BasePlugin):
    name = "抖音续火花"
    plugin_id = "douyin"
    icon = "🔥"
    description = "每天自动给置顶好友发消息续火花"

    def default_config(self):
        return {
            "messages": ["🔥", "早安", "续火花啦", "☀️", "今天也要开心"],
            "use_random": True,
            "friend_count": 6,
            "send_hour": 8,
            "send_minute": 0,
            "app_path": self._find_douyin(),
            "coords": None,
        }

    def config_fields(self):
        return [
            {"key": "friend_count", "label": "好友数量", "type": "int", "default": 6},
            {"key": "messages", "label": "消息池（逗号分隔）", "type": "list", "default": ["🔥"]},
            {"key": "use_random", "label": "随机发送", "type": "bool", "default": True},
            {"key": "send_hour", "label": "发送时间（时）", "type": "int", "default": 8},
            {"key": "send_minute", "label": "发送时间（分）", "type": "int", "default": 0},
            {"key": "app_path", "label": "抖音路径", "type": "str", "default": ""},
        ]

    def setup_steps(self):
        return [
            {"key": "private_msg_icon", "prompt": "把鼠标放到右上角「私信」图标上"},
            {"key": "first_friend", "prompt": "把鼠标放到第 1 个置顶好友上"},
            {"key": "second_friend", "prompt": "把鼠标放到第 2 个置顶好友上"},
            {"key": "input_box", "prompt": "把鼠标放到聊天输入框上"},
            {"key": "close_chat", "prompt": "把鼠标放到关闭会话按钮上"},
        ]

    def on_calibrated(self, coords):
        """校准完成后计算好友间距"""
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

        count = self.config.get("friend_count", 6)
        messages = self.config.get("messages", ["🔥"])
        use_random = self.config.get("use_random", True)

        log("启动抖音...")
        try:
            win = launch_app(
                self.config.get("app_path", ""),
                title_re=".*抖音.*",
                class_re=".*Douyin.*",
            )
        except Exception as e:
            log(f"❌ 启动失败: {e}")
            notify("SparkKeeper", f"抖音启动失败: {e}")
            return

        log("打开私信面板...")
        click(*coords["private_msg_icon"], delay=2)

        success = 0
        failed = []
        for i in range(count):
            msg = random.choice(messages) if use_random else messages[0]
            try:
                # 点击好友
                x = coords["first_friend"][0]
                y = coords["first_friend"][1] + i * coords.get("friend_height", 88)
                click(x, y, delay=1.5)
                log(f"  好友 {i+1}: 发送 {msg}")

                # 输入并发送
                click(*coords["input_box"], delay=0.5)
                type_text(msg)
                press("enter", delay=1)

                # 关闭聊天
                click(*coords["close_chat"], delay=1)
                success += 1
            except Exception as e:
                log(f"  好友 {i+1}: ❌ 失败 - {e}")
                failed.append(i + 1)
                try:
                    click(*coords["close_chat"], delay=0.5)
                except Exception:
                    pass
            time.sleep(0.5)

        # 收起私信
        click(*coords["private_msg_icon"], delay=0.5)

        # 记录统计
        stats.record(self.plugin_id, success, len(failed))

        log(f"✅ 完成: {success}/{count} 个好友")
        if failed:
            notify("SparkKeeper", f"第 {','.join(map(str, failed))} 个好友发送失败")

    def _find_douyin(self):
        for drive in "CDEFGH":
            for pf in ["Program Files", "Program Files (x86)"]:
                for sub in ["Douyin\\Douyin.exe", "ByteDance\\douyin\\Douyin.exe"]:
                    p = f"{drive}:\\{pf}\\{sub}"
                    if os.path.isfile(p):
                        return p
        return ""
