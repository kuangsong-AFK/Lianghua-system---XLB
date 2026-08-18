# -*- coding: utf-8 -*-
"""策略存档室：按名称保存/载入 IDE 策略代码（密码保护，JSON 本地存储）

- 保存密码固定为 688688（按需求）
- 存储文件：DL_Quant_System/saved_strategies.json（已加入 .gitignore）
- 注意：Streamlit Cloud 的容器文件系统在重新部署后会被重置，
  建议重要策略定期点击「导出备份」下载到本地。
"""
import json
import os
from datetime import datetime
from pathlib import Path

PASSWORD = "688688"
DEFAULT_STORE = Path(__file__).resolve().parent / "saved_strategies.json"


def _store_path():
    env = os.getenv("STRATEGY_STORE_PATH", "")
    return Path(env) if env else DEFAULT_STORE


def _load():
    path = _store_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data):
    _store_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_strategy(name, password, code):
    """保存策略。成功返回 None，失败返回错误提示。"""
    name = (name or "").strip()
    if not name:
        return "请先输入策略名称"
    if str(password or "") != PASSWORD:
        return "保存密码错误（提示：密码为 688688）"
    if not code or not str(code).strip():
        return "代码内容为空，无法保存"
    data = _load()
    existed = name in data
    data[name] = {
        "code": str(code),
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _save(data)
    return None


def list_strategies():
    return sorted(_load().keys())


def get_strategy(name, password):
    """读取策略。返回 (代码, 错误提示)。"""
    if str(password or "") != PASSWORD:
        return None, "密码错误（提示：密码为 688688）"
    data = _load()
    if name not in data:
        return None, f"未找到策略「{name}」"
    return data[name].get("code", ""), None


def export_json():
    return json.dumps(_load(), ensure_ascii=False, indent=2)


def import_json(text):
    """导入备份 JSON，合并到本地存档。成功返回 True。"""
    try:
        incoming = json.loads(str(text))
        if not isinstance(incoming, dict):
            return False
        merged = _load()
        merged.update(incoming)
        _save(merged)
        return True
    except Exception:
        return False
