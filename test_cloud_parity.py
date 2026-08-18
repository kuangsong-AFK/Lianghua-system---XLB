# -*- coding: utf-8 -*-
"""云端同款环境全量回归测试

模拟 Streamlit Cloud 的部署形态：
- 仓库里没有 .streamlit/secrets.toml（密钥被 gitignore）
- 只安装 requirements.txt（无 torch/sklearn/akshare）
- 用 Python 3.11 运行（runtime.txt）

测试内容：全部 11 个页面渲染 + 回测/IDE/选股神器交互。
DL 与期货页面在云端没有 torch/akshare，应优雅降级（显示提示而非崩溃）。
"""
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "DL_Quant_System"))


def wait_job(key, timeout=180):
    from bg_runner import get_job
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = get_job(key)
        if job and not job["running"]:
            return job
        time.sleep(0.2)
    raise RuntimeError(f"后台任务 {key} 超时未完成")

SECRET_FILES = [
    ROOT / ".streamlit" / "secrets.toml",
    ROOT / "DL_Quant_System" / ".streamlit" / "secrets.toml",
]

PAGES = [
    "🏠 系统总览 (监控中控)",
    "🤖 AI 策略引擎 (LLM)",
    "💻 极客量化 IDE (代码编译)",
    "📈 深度静态全量回测",
    "🔍 选股神器 (全市场扫描)",
    "⚡ 实时高频交易 (Live)",
    "🧠 深度学习预测矩阵",
    "🔗 期货全量审计 (归因)",
    "🌪️ 期货高频沙盘",
]

results = []


def hide_secrets():
    for f in SECRET_FILES:
        if f.exists():
            shutil.move(str(f), str(f) + ".bak")


def restore_secrets():
    for f in SECRET_FILES:
        bak = Path(str(f) + ".bak")
        if bak.exists():
            shutil.move(str(bak), str(f))


def run():
    from streamlit.testing.v1 import AppTest

    def switch(at, page):
        nav = list(at.sidebar.radio)[-1]
        nav.set_value(page)
        at.run()

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.run()
    if at.exception:
        results.append(("首屏", [e.value for e in at.exception]))
        print("[FAIL] 首屏异常", [e.value for e in at.exception])
        return
    print("[PASS] 首屏")
    for page in PAGES:
        switch(at, page)
        if at.exception:
            results.append((page, [e.value for e in at.exception]))
            print(f"[FAIL] {page}: {[e.value for e in at.exception]}")
        else:
            results.append((page, "OK"))
            print(f"[PASS] {page}")

    # 回测交互（无密钥 → 本地 CSV 降级路径；后台异步执行需轮询等待）
    switch(at, "📈 深度静态全量回测")
    for btn in at.button:
        if "启动全量归因回测" in str(btn.label):
            btn.click()
            at.run()
            break
    if at.exception:
        results.append(("回测交互", [e.value for e in at.exception]))
        print("[FAIL] 回测交互", [e.value for e in at.exception])
    else:
        wait_job("bt_job")
        at.run()
        if at.exception:
            results.append(("回测交互", [e.value for e in at.exception]))
            print("[FAIL] 回测交互", [e.value for e in at.exception])
        elif at.session_state["bt_result"] is None:
            results.append(("回测交互", "回测未产出结果"))
            print("[FAIL] 回测交互: 回测未产出结果")
        else:
            results.append(("回测交互", "OK"))
            print("[PASS] 回测交互")

    # IDE 交互
    switch(at, "💻 极客量化 IDE (代码编译)")
    for btn in at.button:
        if "运行防爆沙盒测试" in str(btn.label):
            btn.click()
            at.run()
            break
    if at.exception:
        results.append(("IDE交互", [e.value for e in at.exception]))
        print("[FAIL] IDE交互", [e.value for e in at.exception])
    else:
        results.append(("IDE交互", "OK"))
        print("[PASS] IDE交互")

    # 选股神器交互（本地样例 + 经典双均线）
    switch(at, "🔍 选股神器 (全市场扫描)")
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
    if at.exception:
        results.append(("选股交互", [e.value for e in at.exception]))
        print("[FAIL] 选股交互", [e.value for e in at.exception])
    elif not clicked:
        results.append(("选股交互", "未找到扫描按钮"))
        print("[FAIL] 选股交互: 未找到扫描按钮")
    else:
        wait_job("screen_job")
        at.run()
        if at.exception:
            results.append(("选股交互", [e.value for e in at.exception]))
            print("[FAIL] 选股交互", [e.value for e in at.exception])
        else:
            stats = at.session_state["screen_stats"]
            print(f"      选股统计: {stats}")
            results.append(("选股交互", "OK"))
            print("[PASS] 选股交互")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "no-secrets"
    print(f"=== 云端同款回归 (模式: {mode}) ===")
    tmp = tempfile.mkdtemp(prefix="cloudparity_")
    os.chdir(tmp)  # 离开项目目录，模拟云端 CWD
    if mode == "no-secrets":
        hide_secrets()
    try:
        run()
    finally:
        if mode == "no-secrets":
            restore_secrets()
    failed = [r for r in results if r[1] != "OK"]
    print("\n" + "=" * 60)
    print(f"总计 {len(results)} 项, 失败 {len(failed)} 项")
    for name, msg in failed:
        print(f"  - {name}: {msg}")
    sys.exit(1 if failed else 0)
