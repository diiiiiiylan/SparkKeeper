"""
SparkKeeper - GUI 主程序
双击 start.bat 或 python app.py 启动
"""

import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import pyautogui

from core.scheduler import TaskScheduler
from core import stats
from plugins.douyin import DouyinSparkPlugin
from plugins.wechat import WechatPlugin

# 注册所有插件
ALL_PLUGINS = [DouyinSparkPlugin, WechatPlugin]

BG = "#1e1e2e"
FG = "#cdd6f4"
ACCENT = "#f38ba8"
CARD = "#313244"
BTN_BG = "#45475a"
BTN_ACTIVE = "#585b70"
OK_COLOR = "#a6e3a1"
WARN_COLOR = "#f9e2af"


class SparkKeeperApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SparkKeeper 🔥")
        self.root.geometry("780x520")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.plugins = [cls() for cls in ALL_PLUGINS]
        self.current_plugin = self.plugins[0]
        self.scheduler = TaskScheduler()
        self.scheduler.start()
        self.active_jobs = set()
        self.config_widgets = {}

        self._build_ui()
        self._select_plugin(0)

    # ==================== UI 构建 ====================

    def _build_ui(self):
        # 左侧 App 列表
        left = tk.Frame(self.root, bg=CARD, width=180)
        left.pack(side="left", fill="y", padx=(10, 0), pady=10)
        left.pack_propagate(False)

        tk.Label(left, text="应用列表", bg=CARD, fg=FG,
                 font=("Microsoft YaHei", 11, "bold")).pack(pady=(12, 8))

        self.plugin_buttons = []
        for i, p in enumerate(self.plugins):
            btn = tk.Button(
                left, text=f"{p.icon} {p.name}", anchor="w",
                bg=BTN_BG, fg=FG, relief="flat", font=("Microsoft YaHei", 10),
                activebackground=BTN_ACTIVE, activeforeground=FG, cursor="hand2",
                command=lambda idx=i: self._select_plugin(idx),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self.plugin_buttons.append(btn)

        # 右侧主面板
        right = tk.Frame(self.root, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # 标题行
        self.title_label = tk.Label(
            right, text="", bg=BG, fg=FG,
            font=("Microsoft YaHei", 14, "bold"), anchor="w",
        )
        self.title_label.pack(fill="x")

        self.desc_label = tk.Label(
            right, text="", bg=BG, fg="#a6adc8",
            font=("Microsoft YaHei", 9), anchor="w",
        )
        self.desc_label.pack(fill="x", pady=(0, 8))

        # 配置区
        self.config_frame = tk.Frame(right, bg=CARD)
        self.config_frame.pack(fill="x", pady=(0, 8))

        # 按钮行
        btn_frame = tk.Frame(right, bg=BG)
        btn_frame.pack(fill="x", pady=(0, 8))

        self.btn_calibrate = tk.Button(
            btn_frame, text="🎯 校准", bg="#89b4fa", fg="#1e1e2e",
            font=("Microsoft YaHei", 10), relief="flat", cursor="hand2",
            command=self._calibrate,
        )
        self.btn_calibrate.pack(side="left", padx=(0, 6))

        self.btn_run = tk.Button(
            btn_frame, text="▶ 立即执行", bg=OK_COLOR, fg="#1e1e2e",
            font=("Microsoft YaHei", 10), relief="flat", cursor="hand2",
            command=self._run_now,
        )
        self.btn_run.pack(side="left", padx=(0, 6))

        self.btn_schedule = tk.Button(
            btn_frame, text="⏰ 启动定时", bg=WARN_COLOR, fg="#1e1e2e",
            font=("Microsoft YaHei", 10), relief="flat", cursor="hand2",
            command=self._toggle_schedule,
        )
        self.btn_schedule.pack(side="left", padx=(0, 6))

        self.btn_save = tk.Button(
            btn_frame, text="💾 保存配置", bg=BTN_BG, fg=FG,
            font=("Microsoft YaHei", 10), relief="flat", cursor="hand2",
            command=self._save_config,
        )
        self.btn_save.pack(side="left")

        # 日志区
        self.log_text = scrolledtext.ScrolledText(
            right, bg="#181825", fg=FG, font=("Consolas", 9),
            height=10, relief="flat", state="disabled",
        )
        self.log_text.pack(fill="both", expand=True, pady=(0, 8))

        # 底部状态栏
        status_frame = tk.Frame(right, bg=CARD, height=30)
        status_frame.pack(fill="x")
        self.status_label = tk.Label(
            status_frame, text="", bg=CARD, fg="#a6adc8",
            font=("Microsoft YaHei", 9), anchor="w",
        )
        self.status_label.pack(fill="x", padx=8, pady=4)

    # ==================== 插件切换 ====================

    def _select_plugin(self, idx):
        self.current_plugin = self.plugins[idx]
        p = self.current_plugin

        # 高亮按钮
        for i, btn in enumerate(self.plugin_buttons):
            btn.configure(bg=ACCENT if i == idx else BTN_BG,
                          fg="#1e1e2e" if i == idx else FG)

        self.title_label.config(text=f"{p.icon} {p.name}")
        self.desc_label.config(text=p.description)

        self._render_config()
        self._update_status()

        # 更新定时按钮状态
        if p.plugin_id in self.active_jobs:
            self.btn_schedule.config(text="⏹ 停止定时", bg=ACCENT)
        else:
            self.btn_schedule.config(text="⏰ 启动定时", bg=WARN_COLOR)

    def _render_config(self):
        for w in self.config_frame.winfo_children():
            w.destroy()
        self.config_widgets = {}

        p = self.current_plugin
        fields = p.config_fields()

        for i, field in enumerate(fields):
            row = tk.Frame(self.config_frame, bg=CARD)
            row.pack(fill="x", padx=10, pady=3)

            tk.Label(row, text=field["label"], bg=CARD, fg=FG,
                     font=("Microsoft YaHei", 9), width=18, anchor="w").pack(side="left")

            val = p.config.get(field["key"], field["default"])

            if field["type"] == "bool":
                var = tk.BooleanVar(value=val)
                cb = ttk.Checkbutton(row, variable=var)
                cb.pack(side="left")
                self.config_widgets[field["key"]] = var
            elif field["type"] == "list":
                var = tk.StringVar(value=",".join(val) if isinstance(val, list) else str(val))
                entry = tk.Entry(row, textvariable=var, bg="#181825", fg=FG,
                                 insertbackground=FG, relief="flat", font=("Microsoft YaHei", 9))
                entry.pack(side="left", fill="x", expand=True)
                self.config_widgets[field["key"]] = var
            else:
                var = tk.StringVar(value=str(val))
                entry = tk.Entry(row, textvariable=var, bg="#181825", fg=FG,
                                 insertbackground=FG, relief="flat", font=("Microsoft YaHei", 9))
                entry.pack(side="left", fill="x", expand=True)
                self.config_widgets[field["key"]] = var

    def _update_status(self):
        p = self.current_plugin
        streak = stats.get_streak(p.plugin_id)
        total = stats.load_stats(p.plugin_id).get("total_sent", 0)
        cal = stats.get_calendar(p.plugin_id, 14)
        cal_str = "".join("🔥" if c == "ok" else "❌" if c == "fail" else "⬜" for c in cal)
        calibrated = "✅ 已校准" if p.is_calibrated() else "❌ 未校准"
        scheduled = "⏰ 定时中" if p.plugin_id in self.active_jobs else ""
        self.status_label.config(
            text=f"{calibrated}  |  连续 {streak} 天  |  累计 {total} 条  |  {cal_str}  {scheduled}"
        )

    # ==================== 操作 ====================

    def _log(self, msg):
        self.log_text.config(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _save_config(self):
        p = self.current_plugin
        for field in p.config_fields():
            key = field["key"]
            var = self.config_widgets.get(key)
            if not var:
                continue
            val = var.get()
            if field["type"] == "int":
                try:
                    val = int(val)
                except ValueError:
                    val = field["default"]
            elif field["type"] == "bool":
                val = bool(val)
            elif field["type"] == "list":
                val = [s.strip() for s in str(val).split(",") if s.strip()]
            p.config[key] = val
        p.save_config()
        self._log("💾 配置已保存")
        self._update_status()

    def _run_now(self):
        self._save_config()
        p = self.current_plugin
        if not p.is_calibrated():
            self._log("❌ 请先校准")
            return
        self._log(f"▶ 开始执行 {p.name}...")
        self.btn_run.config(state="disabled")

        def task():
            try:
                p.run(log_callback=lambda msg: self.root.after(0, self._log, msg))
            except Exception as e:
                self.root.after(0, self._log, f"❌ 执行出错: {e}")
            self.root.after(0, lambda: self.btn_run.config(state="normal"))
            self.root.after(0, self._update_status)

        threading.Thread(target=task, daemon=True).start()

    def _toggle_schedule(self):
        p = self.current_plugin
        pid = p.plugin_id

        if pid in self.active_jobs:
            self.scheduler.remove_job(pid)
            self.active_jobs.discard(pid)
            self.btn_schedule.config(text="⏰ 启动定时", bg=WARN_COLOR)
            self._log(f"⏹ 已停止 {p.name} 定时任务")
        else:
            self._save_config()
            if not p.is_calibrated():
                self._log("❌ 请先校准")
                return
            h = p.config.get("send_hour", 8)
            m = p.config.get("send_minute", 0)

            def job():
                self.root.after(0, self._log, f"⏰ 定时触发 {p.name}")
                p.run(log_callback=lambda msg: self.root.after(0, self._log, msg))
                self.root.after(0, self._update_status)

            self.scheduler.add_daily_job(pid, job, h, m)
            self.active_jobs.add(pid)
            self.btn_schedule.config(text="⏹ 停止定时", bg=ACCENT)
            self._log(f"⏰ 已启动 {p.name} 定时任务: 每天 {h:02d}:{m:02d}")

        self._update_status()

    def _calibrate(self):
        p = self.current_plugin
        steps = p.setup_steps()
        if not steps:
            self._log("该插件不需要校准")
            return

        self._log(f"🎯 开始校准 {p.name}（共 {len(steps)} 步）")
        self._log("   每步把鼠标放到指定位置，然后按 F8 确认")

        coords = {}
        self._calibrate_step(p, steps, 0, coords)

    def _calibrate_step(self, plugin, steps, idx, coords):
        if idx >= len(steps):
            # 校准完成
            if hasattr(plugin, "on_calibrated"):
                plugin.on_calibrated(coords)
            else:
                plugin.config["coords"] = coords
                plugin.save_config()
            self._log("✅ 校准完成！")
            self._update_status()
            return

        step = steps[idx]
        self._log(f"  [{idx+1}/{len(steps)}] {step['prompt']}，然后按 F8")

        def on_f8(event):
            pos = pyautogui.position()
            coords[step["key"]] = [pos.x, pos.y]
            self._log(f"       ✓ ({pos.x}, {pos.y})")
            self.root.unbind("<F8>")

            # 第一步校准完后自动点击打开（抖音私信等）
            if idx == 0 and step["key"] == "private_msg_icon":
                pyautogui.click(pos.x, pos.y)
                import time
                time.sleep(2)
            # 校准前两个好友后自动点击第一个打开聊天
            if idx == 1 and step["key"] == "first_friend":
                self._first_friend_pos = [pos.x, pos.y]
            if idx == 2 and step["key"] == "second_friend":
                if hasattr(self, "_first_friend_pos"):
                    pyautogui.click(*self._first_friend_pos)
                    import time
                    time.sleep(1.5)

            self._calibrate_step(plugin, steps, idx + 1, coords)

        self.root.bind("<F8>", on_f8)

    def run(self):
        self.root.mainloop()
        self.scheduler.stop()


if __name__ == "__main__":
    app = SparkKeeperApp()
    app.run()
