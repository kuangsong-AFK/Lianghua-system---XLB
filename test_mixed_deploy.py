# -*- coding: utf-8 -*-
"""混合部署回归测试：模拟云端"新旧文件混合"状态

- strategy_sandbox.py 用旧版（没有 prepare_strategy_source）
- ai_prompts.py 缺失
验证 app.py / screener.py 的降级逻辑让应用照常工作。
"""
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def wait_job(key, timeout=180):
    from bg_runner import get_job
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = get_job(key)
        if job and not job["running"]:
            return job
        time.sleep(0.2)
    raise RuntimeError(f"后台任务 {key} 超时未完成")

OLD_SANDBOX = '''import ast
import concurrent.futures
import math
import time
from datetime import datetime

import numpy as np
import pandas as pd


class StrategySandboxError(Exception):
    pass


FORBIDDEN_NODES = (ast.Import, ast.ImportFrom, ast.ClassDef, ast.Global, ast.Nonlocal,
                   ast.With, ast.AsyncWith, ast.Try, ast.Raise, ast.Delete, ast.For,
                   ast.AsyncFor, ast.While, ast.Lambda, ast.Await, ast.Yield, ast.YieldFrom)
FORBIDDEN_CALLS = {"__import__", "compile", "delattr", "dir", "eval", "exec", "getattr",
                   "globals", "hasattr", "help", "input", "locals", "memoryview", "open",
                   "print", "setattr", "super", "type", "vars"}
FORBIDDEN_NAMES = FORBIDDEN_CALLS | {"breakpoint", "exit", "quit"}
SAFE_BUILTINS = {"abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
                 "enumerate": enumerate, "float": float, "int": int, "len": len,
                 "list": list, "max": max, "min": min, "pow": pow, "range": range,
                 "round": round, "set": set, "slice": slice, "sorted": sorted,
                 "str": str, "sum": sum, "tuple": tuple, "zip": zip}


def validate_strategy_source(source):
    try:
        tree = ast.parse(str(source))
    except SyntaxError as exc:
        raise StrategySandboxError(f"strategy syntax error: {exc}") from exc
    body = [node for node in tree.body if not _is_docstring_expr(node)]
    if not body or not all(isinstance(node, ast.FunctionDef) for node in body):
        raise StrategySandboxError("strategy may only contain function definitions")
    functions = {node.name: node for node in body}
    func = functions.get("generate_signals")
    if func is None:
        raise StrategySandboxError("strategy entrypoint must be generate_signals(df)")
    if any(node.decorator_list for node in body):
        raise StrategySandboxError("strategy decorators are not allowed")
    if any(node.name.startswith("__") for node in body):
        raise StrategySandboxError("double-underscore function names are not allowed")
    if len(func.args.args) != 1 or func.args.args[0].arg != "df":
        raise StrategySandboxError("generate_signals must accept one argument named df")
    if func.args.vararg or func.args.kwarg or func.args.defaults or func.args.kw_defaults:
        raise StrategySandboxError("generate_signals must not use extra args or defaults")
    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            raise StrategySandboxError(f"{type(node).__name__} is not allowed in strategy code")
        if isinstance(node, ast.Name):
            if node.id.startswith("__") or node.id in FORBIDDEN_NAMES:
                raise StrategySandboxError(f"name {node.id!r} is not allowed")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in FORBIDDEN_CALLS:
                raise StrategySandboxError(f"attribute {node.attr!r} is not allowed")
        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in FORBIDDEN_CALLS or call_name.startswith("__"):
                raise StrategySandboxError(f"call {call_name!r} is not allowed")
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "__" in node.value:
            raise StrategySandboxError("double-underscore strings are not allowed")
    return tree


def execute_strategy(source, df, timeout_seconds=2.0):
    tree = validate_strategy_source(source)
    namespace = {"__builtins__": SAFE_BUILTINS, "datetime": datetime, "math": math,
                 "np": np, "pd": pd, "time": time}
    exec(compile(tree, "<strategy>", "exec"), namespace, namespace)
    func = namespace.get("generate_signals")
    if not callable(func):
        raise StrategySandboxError("generate_signals(df) was not created")
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func, df.copy())
    try:
        result = future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError as exc:
        future.cancel()
        executor.shutdown(wait=False, cancel_futures=True)
        raise StrategySandboxError("strategy execution timed out") from exc
    finally:
        if future.done():
            executor.shutdown(wait=False, cancel_futures=True)
    if result is None or not isinstance(result, pd.DataFrame):
        raise StrategySandboxError("generate_signals(df) must return a pandas DataFrame")
    if len(result) != len(df):
        raise StrategySandboxError("returned DataFrame must keep the same row count")
    return normalize_strategy_result(result)


def normalize_strategy_result(df):
    result = df.copy()
    sig_col = next((col for col in result.columns if str(col).lower() == "signal"), None)
    if sig_col is None:
        raise StrategySandboxError("strategy must create a Signal column")
    signal = result[sig_col].fillna(0)
    if not np.issubdtype(signal.dtype, np.number):
        text_signal = signal.astype(str).str.lower().str.strip()
        signal = np.select([text_signal.str.contains(r"buy|long|true|yes|1", regex=True),
                            text_signal.str.contains(r"sell|short|-1", regex=True)], [1, -1], default=0)
    result["Signal"] = pd.Series(signal, index=result.index).apply(
        lambda value: 1 if float(value) > 0.1 else (-1 if float(value) < -0.1 else 0)).astype(int)
    return result


def _is_docstring_expr(node):
    return isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str)


def _call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
'''

tmp = Path(tempfile.mkdtemp(prefix="mixeddeploy_"))
proj = tmp / "proj"
shutil.copytree(ROOT / "DL_Quant_System", proj / "DL_Quant_System", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
shutil.copytree(ROOT / "data", proj / "data")
(proj / ".streamlit").mkdir()
shutil.copy(ROOT / ".streamlit" / "config.toml", proj / ".streamlit" / "config.toml")
# 根 app.py 包装器
(proj / "app.py").write_text(
    "import runpy\nimport sys\nimport traceback\nfrom pathlib import Path\n"
    "import streamlit as st\n"
    "ROOT = Path(__file__).resolve().parent\n"
    "APP_DIR = ROOT / 'DL_Quant_System'\n"
    "if str(APP_DIR) not in sys.path:\n    sys.path.insert(0, str(APP_DIR))\n"
    "try:\n    runpy.run_path(str(APP_DIR / 'app.py'), run_name='__main__')\n"
    "except Exception as exc:\n    st.error('启动失败')\n    st.exception(exc)\n",
    encoding="utf-8",
)
# 替换为旧版沙盒（无 prepare_strategy_source）
(proj / "DL_Quant_System" / "strategy_sandbox.py").write_text(OLD_SANDBOX, encoding="utf-8")
# 删除 ai_prompts.py（模拟新文件缺失）
(proj / "DL_Quant_System" / "ai_prompts.py").unlink()
# 把 screener.py 降级为旧版（无 should_stop 参数与中断逻辑），
# 精确复现云端混合部署的 run_screen() unexpected keyword 报错场景
scr = (proj / "DL_Quant_System" / "screener.py").read_text(encoding="utf-8")
scr = scr.replace("progress_cb=None, log_cb=None, should_stop=None):", "progress_cb=None, log_cb=None):")
scr = scr.replace("""            if should_stop and should_stop():
                for f in futures:
                    f.cancel()
                break
""", "")
(proj / "DL_Quant_System" / "screener.py").write_text(scr, encoding="utf-8")
print("已模拟: 旧沙盒 + 缺 ai_prompts + 旧 screener")

os.chdir(str(proj))
sys.path.insert(0, str(proj))
sys.path.insert(0, str(proj / "DL_Quant_System"))

from streamlit.testing.v1 import AppTest

at = AppTest.from_file(str(proj / "app.py"), default_timeout=120)
at.run()
assert not at.exception, [e.value for e in at.exception]
print("[PASS] 混合部署首屏")

# 回测交互（走 execute_safely -> 降级 prepare_strategy_source + 旧版 execute_strategy）
nav = list(at.sidebar.radio)[-1]
nav.set_value("📈 深度静态全量回测")
at.run()
clicked = False
for btn in at.button:
    if "启动全量归因回测" in str(btn.label):
        btn.click()
        at.run()
        clicked = True
        break
assert clicked, "未找到回测按钮"
assert not at.exception, [e.value for e in at.exception]
wait_job("bt_job")
at.run()
assert not at.exception, [e.value for e in at.exception]
assert at.session_state["bt_result"] is not None, "回测未产出"
print("[PASS] 混合部署回测交互（降级沙盒路径）")

# 选股交互（screener 降级路径）
nav = list(at.sidebar.radio)[-1]
nav.set_value("🔍 选股神器 (全市场扫描)")
at.run()
for radio in at.radio:
    if "策略来源" in str(radio.label):
        radio.set_value("💡 经典双均线")
        at.run()
        break
clicked = False
for btn in at.button:
    if "开始全市场扫描" in str(btn.label):
        btn.click()
        at.run()
        clicked = True
        break
assert clicked, "未找到扫描按钮"
assert not at.exception, [e.value for e in at.exception]
wait_job("screen_job")
at.run()
assert not at.exception, [e.value for e in at.exception]
stats = at.session_state["screen_stats"]
print(f"[PASS] 混合部署选股交互: {stats}")
assert stats["scanned"] > 0

shutil.rmtree(tmp, ignore_errors=True)
print("✅ 混合部署降级测试全部通过")
