# -*- coding: utf-8 -*-
"""小吕布量化 Pro - Streamlit AppTest 逐页冒烟测试

用法:
    .venv\\Scripts\\python.exe app_page_test.py

逐页切换左侧导航，检查每个页面渲染是否抛异常。
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "DL_Quant_System"))

from streamlit.testing.v1 import AppTest

APP_FILE = ROOT / "app.py"

PAGES = [
    "🏠 系统总览 (监控中控)",
    "🤖 AI 策略引擎 (LLM)",
    "💻 极客量化 IDE (代码编译)",
    "📈 深度静态全量回测",
    "⚡ 实时高频交易 (Live)",
    "🧠 深度学习预测矩阵",
    "🛡️ 论文审计日志",
    "🔗 期货全量审计 (归因)",
    "🌪️ 期货高频沙盘",
    "🔍 选股神器 (全市场扫描)",
    "🧩 扩展插件中心",
]

results = []


def run_page(name, extra=None, timeout=120):
    at = AppTest.from_file(str(APP_FILE), default_timeout=timeout)
    try:
        at.run()
        if at.exception:
            results.append((name, f"首屏异常: {[e.value for e in at.exception]}"))
            print(f"[FAIL] {name}: 首屏异常 {[e.value for e in at.exception]}")
            return at
        # 切换到目标页面
        radios = list(at.sidebar.radio)
        if not radios:
            results.append((name, "侧边栏找不到导航 radio"))
            print(f"[FAIL] {name}: 无导航 radio")
            return at
        nav = radios[-1]  # 最后一个 radio 是导航菜单
        nav.set_value(name)
        at.run()
        if at.exception:
            results.append((name, f"页面异常: {[e.value for e in at.exception]}"))
            print(f"[FAIL] {name}: 页面异常 {[e.value for e in at.exception]}")
        else:
            results.append((name, "OK"))
            print(f"[PASS] {name}")
        if extra:
            try:
                extra(at)
            except Exception as exc:
                results.append((name + " (交互)", str(exc)))
                print(f"[FAIL] {name} (交互): {exc!r}")
                traceback.print_exc()
            else:
                print(f"[PASS] {name} (交互)")
    except Exception as exc:
        results.append((name, f"AppTest 崩溃: {exc!r}"))
        print(f"[FAIL] {name}: AppTest 崩溃 {exc!r}")
        traceback.print_exc()
    return at


def interact_backtest(at):
    # PAGES[3]: 点击"启动全量归因回测"按钮（使用本地 CSV 000001）
    for btn in at.button:
        if "启动全量归因回测" in str(btn.label):
            btn.click()
            at.run()
            if at.exception:
                raise RuntimeError([e.value for e in at.exception])
            assert any("plotly_chart" == str(el.type) for el in at.get("plotly_chart")), "未找到回测图表"
            return
    raise RuntimeError("未找到回测按钮")


def interact_ide(at):
    # PAGES[2]: 点击"运行防爆沙盒测试"按钮
    for btn in at.button:
        if "运行防爆沙盒测试" in str(btn.label):
            btn.click()
            at.run()
            if at.exception:
                raise RuntimeError([e.value for e in at.exception])
            return
    raise RuntimeError("未找到沙盒测试按钮")


def interact_dl(at):
    # PAGES[5]: 深度学习页 - 用最少 epoch 跑一次训练
    sliders = list(at.slider)
    if len(sliders) >= 2:
        sliders[0].set_value(10)  # 滑窗长度
        sliders[1].set_value(10)  # epoch
    for btn in at.button:
        if "启动张量训练" in str(btn.label):
            btn.click()
            at.run()
            if at.exception:
                raise RuntimeError([e.value for e in at.exception])
            return
    raise RuntimeError("未找到张量训练按钮")


def interact_futures(at):
    # PAGES[8]: 期货回测页 - 输入 SA2409 并点击开始
    for ti in at.text_input:
        if "期货合约代码" in str(ti.label):
            ti.set_value("SA2409")
    for btn in at.button:
        if "开始穿透回测" in str(btn.label):
            btn.click()
            at.run()
            if at.exception:
                raise RuntimeError([e.value for e in at.exception])
            return
    raise RuntimeError("未找到期货回测按钮")


def interact_screener(at):
    # PAGES[9]: 选股神器 - 用经典双均线扫描本地样例
    for radio in at.radio:
        if "策略来源" in str(radio.label):
            radio.set_value("💡 经典双均线")
            at.run()
            break
    clicked = False
    for btn in at.button:
        if "开始全市场扫描" in str(btn.label):
            btn.click()
            clicked = True
            at.run()
            break
    if not clicked:
        raise RuntimeError("未找到扫描按钮")
    if at.exception:
        raise RuntimeError([e.value for e in at.exception])
    assert at.session_state["screen_results"] is not None, "扫描未产出结果"
    assert at.session_state["screen_stats"]["scanned"] > 0, "扫描数量为 0"


if __name__ == "__main__":
    # 页面渲染测试
    for page in PAGES:
        run_page(page)

    # 交互测试
    run_page("📈 深度静态全量回测", extra=interact_backtest)
    run_page("💻 极客量化 IDE (代码编译)", extra=interact_ide)
    run_page("🧠 深度学习预测矩阵", extra=interact_dl, timeout=600)
    run_page("🔗 期货全量审计 (归因)", extra=interact_futures, timeout=300)
    run_page("🔍 选股神器 (全市场扫描)", extra=interact_screener, timeout=300)

    print("\n" + "=" * 60)
    failed = [r for r in results if r[1] != "OK"]
    print(f"总计 {len(results)} 项, 失败 {len(failed)} 项")
    for name, msg in failed:
        print(f"  - {name}: {msg}")
    sys.exit(1 if failed else 0)
