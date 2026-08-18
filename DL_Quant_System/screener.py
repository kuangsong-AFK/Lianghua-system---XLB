# -*- coding: utf-8 -*-
"""选股神器核心引擎

按策略代码的买点（Signal == 1）在股票池中扫描：
- 股票池：Tushare stock_basic（沪深主板/创业板/科创板/北交所/全市场）或本地样例
- 行情：复用 data_loader.fetch_stock_data（tushare 优先，本地 CSV 兜底）
- 信号：与 AI 战情室/回测完全一致 —— prepare_strategy_source + execute_strategy
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import streamlit as st

from data_loader import fetch_stock_data, format_ts_code

# 🔧 兼容云端"新旧文件混合"部署：沙盒模块可能还是旧版（缺 prepare_strategy_source）
try:
    import strategy_sandbox as _sandbox
except Exception:
    _sandbox = None
execute_strategy = getattr(_sandbox, "execute_strategy", None)
prepare_strategy_source = getattr(_sandbox, "prepare_strategy_source", None)
if prepare_strategy_source is None:
    import re as _re

    def prepare_strategy_source(source):
        safe_code = str(source).replace("pandas.np", "np")
        _m = _re.search(r"`{3}(?:python)?\s*(.*?)\s*`{3}", safe_code, _re.DOTALL | _re.IGNORECASE)
        if _m:
            safe_code = _m.group(1).strip()
        return "\n".join(
            line for line in safe_code.splitlines()
            if not line.strip().startswith(("import ", "from "))
        ).strip()

# 扫描范围 key -> (标签, stock_basic 过滤逻辑说明)
MARKET_LABELS = {
    "LOCAL": "本地样例 (秒出)",
    "SH": "沪深主板",
    "CYB": "创业板",
    "KCB": "科创板",
    "BJ": "北交所",
    "ALL": "全市场 A股 (约5400只, 耗时较长)",
}


@st.cache_data(ttl=300, show_spinner=False)
def _local_sample_codes():
    """从 DL_Quant_System/data 目录动态收集本地样例标的。"""
    data_dir = Path(__file__).resolve().parent / "data"
    codes = []
    for p in sorted(data_dir.glob("*.csv")):
        code = format_ts_code(p.stem)
        if code and code not in codes:
            codes.append(code)
    return codes


@st.cache_data(ttl=1800, show_spinner=False)
def get_stock_universe(tushare_token, market="LOCAL"):
    """返回 (代码列表, {代码: 名称})。market 取值见 MARKET_LABELS。

    注意：只用简单类型做缓存参数（不传 tushare 模块对象）。
    """
    if market == "LOCAL":
        codes = _local_sample_codes()
        return codes, {}
    if not tushare_token:
        return [], {}
    try:
        import tushare

        df = tushare.pro_api(tushare_token).stock_basic(exchange="", list_status="L",
                                                         fields="ts_code,name,list_date")
        if df is None or df.empty:
            return [], {}
        if market == "CYB":
            df = df[df["ts_code"].str.startswith(("300", "301"))]
        elif market == "KCB":
            df = df[df["ts_code"].str.startswith(("688", "689"))]
        elif market == "BJ":
            df = df[df["ts_code"].str.startswith(("43", "83", "87", "92"))]
        elif market == "SH":
            df = df[df["ts_code"].str.startswith(("600", "601", "603", "605", "000", "001", "002", "003"))]
        names = dict(zip(df["ts_code"].astype(str), df["name"].astype(str)))
        return [str(c) for c in df["ts_code"]], names
    except Exception:
        return [], {}


def _scan_one(args):
    ts_code, strategy_code, start_date, lookback, tushare_token, tushare_module = args
    df, source = fetch_stock_data(
        ts_code,
        adj="qfq",
        start_date=start_date,
        tushare_token=tushare_token,
        tushare_module=tushare_module,
    )
    if df is None or df.empty:
        return {"code": ts_code, "status": "no_data", "source": source}
    if execute_strategy is None:
        return {"code": ts_code, "status": "strategy_error"}
    try:
        res = execute_strategy(prepare_strategy_source(strategy_code), df)
    except Exception:
        return {"code": ts_code, "status": "strategy_error"}
    if "Signal" not in res.columns:
        return {"code": ts_code, "status": "strategy_error"}
    tail = res.tail(lookback)
    buy_rows = tail[tail["Signal"] == 1]
    if buy_rows.empty:
        return {"code": ts_code, "status": "no_buy", "source": source}
    last_buy_idx = buy_rows.index[-1]
    buy_date = res.loc[last_buy_idx, "trade_date"] if "trade_date" in res.columns else None
    close = float(res["Close"].iloc[-1])
    pct5 = float(res["Close"].pct_change(5).iloc[-1] * 100) if len(res) > 5 else 0.0
    return {
        "code": ts_code,
        "status": "buy",
        "source": source,
        "close": close,
        "buy_date": str(buy_date)[:10] if buy_date is not None else "",
        "pct5": pct5,
        "rows": len(res),
    }


def run_screen(strategy_code, universe_codes, start_date, lookback,
               tushare_token, tushare_module, max_workers=3,
               progress_cb=None, log_cb=None, should_stop=None):
    """多线程扫描股票池，返回 (命中买点列表, 统计信息)。

    should_stop: 可选回调，返回 True 时立即停止提交新任务并中断等待
    （已完成的股票结果保留在 results 中）。
    """
    results = []
    scanned = failed = no_data = strategy_err = 0
    total = len(universe_codes)
    args_list = [
        (code, strategy_code, start_date, lookback, tushare_token, tushare_module)
        for code in universe_codes
    ]
    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as ex:
        futures = {ex.submit(_scan_one, a): a[0] for a in args_list}
        for i, fut in enumerate(as_completed(futures), 1):
            code = futures[fut]
            try:
                r = fut.result()
            except Exception:
                failed += 1
                r = None
            else:
                scanned += 1
                if r["status"] == "buy":
                    results.append(r)
                elif r["status"] == "no_data":
                    no_data += 1
                elif r["status"] == "strategy_error":
                    strategy_err += 1
            if progress_cb:
                progress_cb(i, total, code)
            if log_cb:
                log_cb(code, r)
            if should_stop and should_stop():
                for f in futures:
                    f.cancel()
                break
    results.sort(key=lambda r: (r.get("pct5") or 0), reverse=True)
    stats = {
        "scanned": scanned,
        "failed": failed,
        "no_data": no_data,
        "strategy_errors": strategy_err,
        "total": total,
    }
    return results, stats
