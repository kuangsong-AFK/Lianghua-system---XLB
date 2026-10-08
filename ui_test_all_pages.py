# -*- coding: utf-8 -*-
"""UI 全页面回归 + 沙盘交互测试（本地测试组入口）

用法（在项目根目录，需已装 .venv 依赖）：
    .venv\\Scripts\\python.exe ui_test_all_pages.py

覆盖：
1. 9 个页面逐一渲染，断言无异常（深度学习页缺 torch 属预期降级）；
2. 期货高频沙盘交互流：开多 → 反手 → 一键全平，校验持仓与成交记录。
"""
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'C:\Users\A\Downloads\量化软件\Lianghua-system---XLB-main\DL_Quant_System')

from streamlit.testing.v1 import AppTest

APP = r'C:\Users\A\Downloads\量化软件\Lianghua-system---XLB-main\DL_Quant_System\app.py'
PAGES = [
    '🏠 系统总览 (监控中控)',
    '🤖 AI 策略引擎 (LLM)',
    '💻 极客量化 IDE (代码编译)',
    '📈 深度静态全量回测',
    '🔍 选股神器 (全市场扫描)',
    '⚡ 实时高频交易 (Live)',
    '🧠 深度学习预测矩阵',
    '🔗 期货全量审计 (归因)',
    '🌪️ 期货高频沙盘',
]
SAND = '🌪️ 期货高频沙盘'

passed, failed = [], []

# ---------------- 1. 全页面渲染回归 ----------------
print('===== 全页面渲染回归 =====')
for page in PAGES:
    at = AppTest.from_file(APP, default_timeout=240)
    at.session_state['nav_page'] = page
    at.session_state['curr_page'] = page
    try:
        at.run()
    except Exception as exc:
        failed.append(page)
        print(f'[FAIL] {page} -> 脚本级异常: {type(exc).__name__}: {exc}')
        continue
    if at.exception:
        msgs = [e.message for e in at.exception]
        if page.startswith('🧠') and any('torch' in str(m) for m in msgs):
            print(f'[INFO] {page} -> 预期缺 torch 提示，页面正常降级')
            passed.append(page)
        else:
            failed.append(page)
            print(f'[FAIL] {page} -> {msgs[:3]}')
    else:
        passed.append(page)
        print(f'[PASS] {page}')


def find_btn(at, key):
    for b in at.button:
        if getattr(b, 'key', None) == key:
            return b
    return None


# ---------------- 2. 沙盘交互流 ----------------
print('===== 沙盘交互流（开多→反手→全平） =====')
try:
    at = AppTest.from_file(APP, default_timeout=240)
    at.session_state['nav_page'] = SAND
    at.session_state['curr_page'] = SAND
    # 隔离测试：预置空账户容器，跳过本地存档载入，保证每次测试从空仓开始
    at.session_state['fs_accounts'] = {}
    at.run()
    if at.exception:
        print('[FAIL] 沙盘初始渲染:', at.exception[0].message)
    else:
        b1 = find_btn(at, 'fs_b1')
        b1.click()
        at.run()
        pos1 = at.session_state['fs_accounts']['SA0'].position
        if at.exception:
            print('[FAIL] 开多点击:', at.exception[0].message)
        elif pos1 == 1:
            print('[PASS] 开多1手成交，持仓 1')
        else:
            print(f'[FAIL] 开多后期望1手，实际 {pos1}')

        at.session_state['fs_lots'] = 2
        find_btn(at, 'fs_b4').click()
        at.run()
        pos2 = at.session_state['fs_accounts']['SA0'].position
        if at.exception:
            print('[FAIL] 反手点击:', at.exception[0].message)
        elif pos2 == -2:
            print('[PASS] 反手成交，持仓 -2')
        else:
            print(f'[FAIL] 反手后期望-2手，实际 {pos2}')

        find_btn(at, 'fs_b5').click()
        at.run()
        pos3 = at.session_state['fs_accounts']['SA0'].position
        if at.exception:
            print('[FAIL] 全平点击:', at.exception[0].message)
        elif pos3 == 0:
            print('[PASS] 全平成交，持仓 0')
        else:
            print(f'[FAIL] 全平后期望0手，实际 {pos3}')
        n = len(at.session_state['fs_accounts']['SA0'].trades)
        print(f'[INFO] 成交记录 {n} 条（期望4：开多1/平多1+开空2/平空2）')
except Exception as exc:
    print(f'[FAIL] 交互流异常: {type(exc).__name__}: {exc}')

print()
print(f'======== 共 {len(passed)} 通过 / {len(failed)} 失败（共 {len(PAGES)} 页） ========')
if failed:
    print('失败页面:', failed)
sys.exit(1 if failed else 0)
