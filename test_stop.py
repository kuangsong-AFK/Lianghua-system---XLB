# -*- coding: utf-8 -*-
"""停止机制专项测试：bg_runner 中断 + run_screen 中断保留部分结果"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "DL_Quant_System"))

from bg_runner import start_job, get_job, request_stop
from screener import run_screen, get_stock_universe, MARKET_LABELS
from secure_config import get_secret

TOKEN = get_secret("TUSHARE_TOKEN")

# 1. bg_runner：启动慢任务 → 中途请求停止 → 任务按标志退出
def _slow_worker(job):
    for i in range(200):
        if job["stop"]:
            job["status"] = "stopped"
            return
        job["progress"] = i / 200
        job["status"] = f"step {i}"
        time.sleep(0.03)

start_job("t_stop", _slow_worker)
time.sleep(0.4)
assert get_job("t_stop")["running"] is True, "任务应在运行中"
assert request_stop("t_stop") is True
time.sleep(0.8)
job = get_job("t_stop")
assert job["running"] is False and job["status"] == "stopped", f"停止失败: {job['status']}"
print("[PASS] bg_runner 停止机制")

# 2. run_screen：should_stop 在第一批完成后触发 → 返回部分结果且扫描数受限
import tushare as ts

DEFAULT_STRATEGY = """
def generate_signals(df):
    df = df.copy()
    df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()
    df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()
    df['Signal'] = 0
    df.loc[df['MAIN_MA5'] > df['MAIN_MA20'], 'Signal'] = 1
    df.loc[df['MAIN_MA5'] < df['MAIN_MA20'], 'Signal'] = -1
    return df
""".strip()

codes, _ = get_stock_universe(TOKEN, "LOCAL")
results, stats = run_screen(DEFAULT_STRATEGY, codes, "20240101", 3, TOKEN, ts,
                            max_workers=1, should_stop=lambda: True)
assert stats["scanned"] <= 1, f"停止后不应继续扫描, 实际 {stats['scanned']}"
print(f"[PASS] run_screen 中断（已扫 {stats['scanned']} 只后停止，保留 {len(results)} 条命中）")
print("✅ 停止机制专项测试通过")
