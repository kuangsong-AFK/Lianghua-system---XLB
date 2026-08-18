import os
from pathlib import Path


_ENV_LOADED = False
_ENV_VALUES = {}


def _load_env_files():
    """轻量 .env 加载（无第三方依赖），支持项目根目录与模块目录。"""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    module_dir = Path(__file__).resolve().parent
    candidates = [
        module_dir.parent / ".env",      # 项目根目录
        module_dir / ".env",             # DL_Quant_System 目录
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    _ENV_VALUES[key] = value
        except Exception:
            pass


def get_secret(*names, default=""):
    """Read a secret from Streamlit secrets first, then .env, then environment variables."""
    _load_env_files()
    for name in names:
        value = _read_streamlit_secret(name)
        if value:
            return value
        value = _ENV_VALUES.get(name, "")
        if value:
            return value
        value = os.getenv(name)
        if value:
            return value
    return default


def _read_streamlit_secret(name):
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    # 兜底：Streamlit 按启动目录(CWD)找 secrets.toml，如果用户从其他目录启动
    # 应用（CWD 不对），则直接按模块位置解析项目内的 secrets.toml 文件。
    module_dir = Path(__file__).resolve().parent
    for path in (
        module_dir.parent / ".streamlit" / "secrets.toml",   # 项目根目录
        module_dir / ".streamlit" / "secrets.toml",          # DL_Quant_System 目录
    ):
        try:
            if not path.exists():
                continue
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip() == name:
                    return value.strip().strip('"').strip("'")
        except Exception:
            continue
    return ""
