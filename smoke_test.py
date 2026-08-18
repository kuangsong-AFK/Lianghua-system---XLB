# -*- coding: utf-8 -*-
"""小吕布量化 Pro - 模块级冒烟测试 (无 Streamlit 依赖页面渲染)

用法:
    .venv\\Scripts\\python.exe smoke_test.py
"""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "DL_Quant_System"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

PASS = []
FAIL = []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
        print(f"[PASS] {name}")
    except Exception as exc:
        FAIL.append((name, exc))
        print(f"[FAIL] {name}: {exc!r}")
        traceback.print_exc()


# ---------------------------------------------------------------- 1. 配置
from secure_config import get_secret

TUSHARE_TOKEN = get_secret("TUSHARE_TOKEN")


def t_secrets():
    assert TUSHARE_TOKEN, "TUSHARE_TOKEN 为空，请检查 .streamlit/secrets.toml"


check("secrets: TUSHARE_TOKEN 存在", t_secrets)

# ---------------------------------------------------------------- 2. 数据加载
import pandas as pd
import numpy as np
import tushare as ts
from data_loader import fetch_stock_data, load_local_stock_data, normalize_market_data, format_ts_code


def t_local_csv():
    df = load_local_stock_data("000001.SZ")
    assert df is not None and not df.empty, "本地 CSV 加载为空"
    norm = normalize_market_data(df)
    assert {"Open", "High", "Low", "Close", "Volume"}.issubset(norm.columns), f"规范化列缺失: {norm.columns.tolist()}"
    assert pd.api.types.is_datetime64_any_dtype(norm["trade_date"]), "trade_date 不是日期类型"


def t_format_code():
    assert format_ts_code("000001") == "000001.SZ"
    assert format_ts_code("600398") == "600398.SH"
    assert format_ts_code("430047") == "430047.BJ"


def t_fetch_with_token():
    df, source = fetch_stock_data("000001.SZ", adj="qfq", start_date="20240101",
                                  tushare_token=TUSHARE_TOKEN, tushare_module=ts)
    assert df is not None and not df.empty, "fetch_stock_data 返回空"
    assert {"Open", "High", "Low", "Close"}.issubset(df.columns)
    print(f"    -> source={source}, rows={len(df)}")


check("data: 本地 CSV 加载 + 规范化", t_local_csv)
check("data: 代码格式化", t_format_code)
check("data: fetch_stock_data (tushare/本地降级)", t_fetch_with_token)

# ---------------------------------------------------------------- 3. 策略沙盒
from strategy_sandbox import execute_strategy, validate_strategy_source, StrategySandboxError

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


def t_sandbox_ok():
    df = load_local_stock_data("000001.SZ")
    norm = normalize_market_data(df)
    out = execute_strategy(DEFAULT_STRATEGY, norm)
    assert out is not None and "Signal" in out.columns
    assert set(out["Signal"].unique()).issubset({-1, 0, 1})
    assert len(out) == len(norm)


def t_sandbox_bad_code():
    try:
        execute_strategy("import os; os.system('echo hacked')", pd.DataFrame())
        raise AssertionError("恶意代码竟然通过了沙盒")
    except StrategySandboxError:
        pass


def t_sandbox_no_signal():
    try:
        execute_strategy("def generate_signals(df):\n    return df", pd.DataFrame({"Close": [1, 2, 3]}))
        raise AssertionError("缺少 Signal 列应该报错")
    except StrategySandboxError:
        pass


def t_sandbox_wrong_return():
    try:
        execute_strategy("def generate_signals(df):\n    return None", pd.DataFrame({"Close": [1, 2, 3]}))
        raise AssertionError("返回 None 应该报错")
    except StrategySandboxError:
        pass


check("sandbox: 合法策略执行", t_sandbox_ok)
check("sandbox: 拦截恶意 import", t_sandbox_bad_code)
check("sandbox: 缺少 Signal 报错", t_sandbox_no_signal)
check("sandbox: 返回 None 报错", t_sandbox_wrong_return)

# ---------------------------------------------------------------- 4. 回测引擎
from backtester.engine import simple_backtest


def t_backtest():
    df = normalize_market_data(load_local_stock_data("000001.SZ"))
    df["MAIN_MA5"] = df["Close"].rolling(5).mean()
    df["MAIN_MA20"] = df["Close"].rolling(20).mean()
    df["Signal"] = np.where(df["MAIN_MA5"] > df["MAIN_MA20"], 1, np.where(df["MAIN_MA5"] < df["MAIN_MA20"], -1, 0))
    res, metrics = simple_backtest(df, signals=df["Signal"], commission=0.0003, slippage=0.0005, allow_short=False)
    assert res is not None and not res.empty
    for key in ("total_return", "annual_return", "max_drawdown", "sharpe", "win_rate", "trades"):
        assert key in metrics, f"指标缺 {key}"
    print(f"    -> total={metrics['total_return']:.4f}, sharpe={metrics['sharpe']:.3f}, trades={metrics['trades']}")


check("backtest: 双均线回测指标", t_backtest)

# ---------------------------------------------------------------- 5. 指标/图表辅助
def t_indicators():
    df = normalize_market_data(load_local_stock_data("000001.SZ"))
    if 'Close' in df.columns:
        df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()
        df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['SUB1_MACD_DIFF'] = exp1 - exp2
        df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()
        df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])
    assert "SUB1_MACD_HIST" in df.columns


check("indicators: 默认指标计算", t_indicators)

# ---------------------------------------------------------------- 6. 扩展模块导入
def t_extensions_import():
    import extensions
    assert extensions is not None
    assert extensions.PET_ROSTER, "PET_ROSTER 为空"
    assert callable(extensions.render_ide_page)
    assert callable(extensions.render_futures_backtest)
    assert callable(extensions.render_futures_sandbox)
    assert callable(extensions.render_new_features_page)


check("extensions: 模块导入与接口", t_extensions_import)

# ---------------------------------------------------------------- 7. 模板策略可执行
def t_strategy_templates():
    import strategy_templates
    import inspect
    df = normalize_market_data(load_local_stock_data("000001.SZ"))
    for name, func in inspect.getmembers(strategy_templates, inspect.isfunction):
        if name.startswith("strategy_"):
            # 与 extensions.render_ide_page 相同：把入口函数名重写为 generate_signals
            src = inspect.getsource(func).replace(f"def {name}(", "def generate_signals(", 1)
            out = execute_strategy(src, df)
            assert "Signal" in out.columns, f"{name} 未产出 Signal"
            print(f"    -> {name}: signals={out['Signal'].value_counts().to_dict()}")


check("templates: 4 个内置策略全部可执行", t_strategy_templates)

# ---------------------------------------------------------------- 汇总
print("\n" + "=" * 60)
print(f"总计: {len(PASS)} 通过, {len(FAIL)} 失败")
if FAIL:
    print("失败项:")
    for name, exc in FAIL:
        print(f"  - {name}: {exc!r}")
    sys.exit(1)
print("✅ 全部模块冒烟测试通过！")
