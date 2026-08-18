# -*- coding: utf-8 -*-
"""端到端测试：AI 战情室 真实调用 Kimi API 生成策略并沙盒预检（异步实时生成）"""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)  # 保证 st.secrets 按项目根目录解析
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "DL_Quant_System"))

from streamlit.testing.v1 import AppTest
from bg_runner import get_job

APP_FILE = ROOT / "app.py"
AI_PAGE = "🤖 AI 策略引擎 (LLM)"

at = AppTest.from_file(str(APP_FILE), default_timeout=300)
at.run()
assert not at.exception, [e.value for e in at.exception]

# 切换到 AI 战情室
nav = list(at.sidebar.radio)[-1]
nav.set_value(AI_PAGE)
at.run()
assert not at.exception, [e.value for e in at.exception]

# 通过聊天框发送军令（后台异步生成）
assert len(at.chat_input) >= 1, "未找到 chat_input"
at.chat_input[0].set_value("请用双均线策略写一个 generate_signals 交易策略，MA5 上穿 MA20 买入，下穿卖出").run()
assert not at.exception, [e.value for e in at.exception]

# 轮询等待 chat_job 完成（K3 推理较慢）
deadline = time.time() + 300
last_text_len = -1
while time.time() < deadline:
    job = get_job("chat_job")
    if job and not job["running"]:
        break
    if job and len(job.get("text") or "") != last_text_len:
        last_text_len = len(job.get("text") or "")
        print(f"  ... 实时生成中，已输出 {last_text_len} 字")
    time.sleep(1.0)
else:
    print("FAIL: chat_job 超时未完成")
    sys.exit(1)

at.run()  # 渲染最终结果
assert not at.exception, [e.value for e in at.exception]

code = at.session_state["generated_code"]
msgs = at.session_state["messages"]
print("generated_code 是否装载:", bool(code) and "def generate_signals" in code)
print("对话消息条数:", len(msgs))
for m in msgs:
    print(f"--- [{m['role']}] ---")
    print(str(m["content"])[:400])

if not code or "def generate_signals" not in code:
    print("FAIL: 未生成有效策略代码")
    sys.exit(1)

# 再用生成的代码跑一次完整回测（注意：聊天流程最后 st.rerun 会重建元素树，需重新获取导航元素）
BT_PAGE = "📈 深度静态全量回测"
nav = list(at.sidebar.radio)[-1]
nav.set_value(BT_PAGE)
at.run()
for btn in at.button:
    if "启动全量归因回测" in str(btn.label):
        btn.click()
        at.run()
        break
assert not at.exception, [e.value for e in at.exception]
from bg_runner import get_job as gj
deadline = time.time() + 180
while time.time() < deadline:
    job = gj("bt_job")
    if job and not job["running"]:
        break
    time.sleep(0.3)
at.run()
assert not at.exception, [e.value for e in at.exception]
bt = at.session_state["bt_result"]
if bt and bt.get("metrics"):
    m = bt["metrics"]
    print(f"AI策略回测: 累计收益 {m['total']*100:.2f}%, 夏普 {m['sharpe']:.2f}, 交易 {m['trades']} 次, 状态 {bt.get('strategy_status')}")
else:
    print("FAIL: 回测未产出结果")
    sys.exit(1)

print("✅ AI 战情室端到端测试通过（Kimi 实时生成 → 沙盒预检 → 全量回测）")
