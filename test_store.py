# -*- coding: utf-8 -*-
"""策略存档室测试：模块单元测试 + IDE 页面保存/载入端到端"""
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "DL_Quant_System"))

STORE_TMP = Path(tempfile.mkdtemp(prefix="storetest_")) / "saved_strategies.json"
os.environ["STRATEGY_STORE_PATH"] = str(STORE_TMP)

# ---------- 1. 模块单元测试 ----------
from strategy_store import (save_strategy, list_strategies, get_strategy,
                            export_json, import_json, PASSWORD)

assert PASSWORD == "688688", "密码常量应为 688688"
assert save_strategy("", "688688", "code") is not None, "空名称应报错"
assert save_strategy("策略A", "wrong", "code") is not None, "密码错误应报错"
assert save_strategy("策略A", "688688", "def generate_signals(df):\n    return df") is None
assert "策略A" in list_strategies()
code, err = get_strategy("策略A", "688688")
assert err is None and "generate_signals" in code, "读取失败"
assert get_strategy("策略A", "bad")[1] is not None, "读取密码错误应报错"
assert save_strategy("策略A", "688688", "v2") is None
assert get_strategy("策略A", "688688")[0] == "v2", "覆盖保存失败"
assert import_json(export_json()) is True
assert import_json("not json{{{") is False
print("[PASS] 存档模块单元测试")

# ---------- 2. IDE 页面保存/载入端到端 ----------
os.chdir(ROOT)
from streamlit.testing.v1 import AppTest

at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
at.run()
assert not at.exception, [e.value for e in at.exception]
nav = list(at.sidebar.radio)[-1]
nav.set_value("💻 极客量化 IDE (代码编译)")
at.run()
assert not at.exception, [e.value for e in at.exception]

# 设置策略名称并点击保存
for ti in at.text_input:
    if "策略名称" in str(ti.label):
        ti.set_value("测试策略甲")
for btn in at.button:
    if "保存当前代码" in str(btn.label):
        btn.click()
        at.run()
        break
assert not at.exception, [e.value for e in at.exception]
data = json.loads(STORE_TMP.read_text(encoding="utf-8"))
assert "测试策略甲" in data, "存档文件未写入"
saved_code = data["测试策略甲"]["code"]
assert "def generate_signals" in saved_code, "保存的代码内容不对"
print("[PASS] IDE 保存端到端")

# 先清空编辑器内容，验证载入能恢复
for btn in at.button:
    if "同步保存至全局引擎" in str(btn.label):
        btn.click()
        at.run()
        break
# 选择已保存策略并载入
for sel in at.selectbox:
    if "已保存策略" in str(sel.label):
        sel.set_value("测试策略甲")
        at.run()
        break
for btn in at.button:
    if "载入所选策略" in str(btn.label):
        btn.click()
        at.run()
        break
assert not at.exception, [e.value for e in at.exception]
loaded = at.session_state["generated_code"]
assert loaded == saved_code, "载入的代码与保存的不一致"
print("[PASS] IDE 载入端到端")
print("✅ 策略存档室测试全部通过")
