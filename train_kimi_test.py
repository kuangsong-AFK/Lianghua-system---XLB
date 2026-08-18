# -*- coding: utf-8 -*-
"""AI 战情室批量质检：10 类策略指令 → Kimi 生成 → 沙盒预检 → 自动修复循环

模拟 App 真实链路：
- 系统提示词：ai_prompts.build_system_prompt()
- 代码提取：与 app.execute_safely 相同的 ```python 围栏提取 + import 剔除
- 预检数据：与 App 相同的 dummy_df（含 Open/High/Low/Close，无 Volume）
- 重试反馈：ai_prompts.build_retry_user_message()，最多 3 次尝试
"""
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "DL_Quant_System"))

import numpy as np
import pandas as pd
from openai import OpenAI
from ai_prompts import build_system_prompt, build_retry_user_message
from strategy_sandbox import execute_strategy, StrategySandboxError
from secure_config import get_secret

KIMI_API_KEY = get_secret("KIMI_API_KEY", "MOONSHOT_API_KEY")
MODEL = "kimi-k3"

FENCE_RE = re.compile(r"`{3}(?:python)?\s*(.*?)\s*`{3}", re.DOTALL | re.IGNORECASE)

PROMPTS = [
    "写一个双均线策略：MA5 上穿 MA20 买入，下穿卖出",
    "写一个 MACD 金叉买入、死叉卖出的策略",
    "写一个 RSI 策略：RSI 低于 30 买入，高于 70 卖出",
    "写一个 KDJ 策略：J 值低于 20 买入，高于 80 卖出",
    "写一个布林带策略：价格突破上轨买入，跌破下轨卖出",
    "写一个唐奇安通道突破策略：突破 20 日新高买入，跌破 10 日新低卖出",
    "写一个均线多头排列策略：MA5>MA10>MA20 时买入，空头排列时卖出",
    "写一个量价齐升策略：成交量放大且价格上穿 20 日均线时买入",
    "写一个带止损的双均线策略：买入后若价格从持仓期间最高点回撤 5% 就卖出",
    "写一个缠论分型策略：出现底分型买入，顶分型卖出",
]


def make_dummy_df():
    return pd.DataFrame(
        {'trade_date': pd.date_range('20230101', periods=50), 'Open': np.random.rand(50) * 10,
         'High': np.random.rand(50) * 12, 'Low': np.random.rand(50) * 8,
         'Close': np.random.rand(50) * 10})


def extract_and_clean(full_resp):
    """与 app.execute_safely 相同的提取/清洗逻辑。"""
    match = FENCE_RE.search(full_resp)
    if not match:
        raise StrategySandboxError("no python code block in response")
    safe_code = match.group(1).strip()
    safe_code = "\n".join(
        line for line in safe_code.splitlines()
        if not line.strip().startswith(("import ", "from "))
    ).strip()
    return safe_code


def run_prompt(client, prompt, verbose=False):
    messages = [{"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": prompt}]
    last_error = ""
    full_resp = ""
    for attempt in range(3):
        try:
            if attempt > 0:
                messages.append({"role": "assistant", "content": full_resp or "(空响应)"})
                messages.append({"role": "user", "content": build_retry_user_message(last_error)})
            r = client.chat.completions.create(model=MODEL, messages=messages, temperature=1)
            full_resp = r.choices[0].message.content or ""
            code = extract_and_clean(full_resp)
            execute_strategy(code, make_dummy_df())
            return {"ok": True, "attempts": attempt + 1, "error": ""}
        except Exception as exc:
            last_error = str(exc)
            if verbose:
                print(f"    attempt {attempt + 1} failed: {last_error[:120]}")
    return {"ok": False, "attempts": 3, "error": last_error}


def main():
    client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=300.0)
    results = []
    for i, prompt in enumerate(PROMPTS, 1):
        print(f"\n[{i}/{len(PROMPTS)}] {prompt}")
        t0 = time.time()
        res = run_prompt(client, prompt, verbose=True)
        res["prompt"] = prompt
        results.append(res)
        tag = "PASS" if res["ok"] else "FAIL"
        print(f"  -> {tag} (尝试 {res['attempts']} 次, 耗时 {time.time() - t0:.1f}s)")
        time.sleep(1)

    passed = [r for r in results if r["ok"]]
    failed = [r for r in results if not r["ok"]]
    print("\n" + "=" * 60)
    print(f"总计 {len(results)} 条指令, 通过 {len(passed)}, 失败 {len(failed)}")
    if failed:
        print("失败明细:")
        for r in failed:
            print(f"  - {r['prompt']}")
            print(f"    最终报错: {r['error'][:200]}")
    # 错误分类统计（首轮失败原因按沙盒报错归类）
    print("\n完成。")
    sys.exit(0 if not failed else 2)


if __name__ == "__main__":
    main()
