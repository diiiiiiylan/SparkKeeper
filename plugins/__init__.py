"""SparkKeeper 插件基类"""

import json
from pathlib import Path

CONFIGS_DIR = Path(__file__).parent.parent / "configs"


class BasePlugin:
    name = ""           # 显示名称
    plugin_id = ""      # 唯一标识，用于配置文件名
    icon = ""           # emoji 图标
    description = ""    # 简短描述

    def __init__(self):
        CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
        self.config_path = CONFIGS_DIR / f"{self.plugin_id}.json"
        self.config = self.load_config()

    def default_config(self):
        """子类重写，返回默认配置 dict"""
        return {}

    def config_fields(self):
        """子类重写，返回 GUI 可编辑字段列表
        每项: {"key": str, "label": str, "type": "str"|"int"|"bool"|"list", "default": any}
        """
        return []

    def setup_steps(self):
        """子类重写，返回校准步骤列表
        每项: {"key": str, "prompt": str}
        校准时 GUI 会依次提示用户把鼠标放到对应位置
        """
        return []

    def run(self, log_callback=None):
        """子类重写，执行主任务。log_callback(msg) 用于输出日志到 GUI"""
        raise NotImplementedError

    def load_config(self):
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        cfg = self.default_config()
        self.save_config(cfg)
        return cfg

    def save_config(self, config=None):
        if config:
            self.config = config
        self.config_path.write_text(
            json.dumps(self.config, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    def is_calibrated(self):
        return bool(self.config.get("coords"))
