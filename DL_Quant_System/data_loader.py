from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
LOCAL_DATA_DIRS = (
    BASE_DIR / "data",
    BASE_DIR.parent / "data",
    BASE_DIR / "utils" / "data",
)


def format_ts_code(raw):
    raw = str(raw).strip().upper()
    if len(raw) == 6 and raw.isdigit():
        if raw.startswith(("6", "9")):
            return f"{raw}.SH"
        if raw.startswith(("0", "3", "2")):
            return f"{raw}.SZ"
        if raw.startswith(("4", "8")):
            return f"{raw}.BJ"
    return raw


def fetch_stock_data(ts_code, adj=None, start_date=None, tushare_token="", tushare_module=None):
    ts_code = format_ts_code(ts_code)
    if tushare_token and tushare_module is not None:
        try:
            df = tushare_module.pro_bar(ts_code=ts_code, adj=adj, start_date=start_date)
            if df is not None and not df.empty:
                return normalize_market_data(df), "tushare"
        except Exception:
            pass
    local_df = load_local_stock_data(ts_code, start_date=start_date)
    if local_df is not None and not local_df.empty:
        return normalize_market_data(local_df), "local"
    return pd.DataFrame(), "empty"


def load_local_stock_data(ts_code, start_date=None):
    ts_code = format_ts_code(ts_code)
    candidates = _candidate_names(ts_code)
    for data_dir in LOCAL_DATA_DIRS:
        for name in candidates:
            path = data_dir / name
            if path.exists():
                df = pd.read_csv(path)
                if start_date and "trade_date" in df.columns:
                    date_str = str(start_date).replace("-", "")
                    df = df[pd.to_datetime(df["trade_date"].astype(str), errors="coerce") >= pd.to_datetime(date_str)]
                return df.reset_index(drop=True)
    return pd.DataFrame()


def normalize_market_data(df):
    if df is None or df.empty:
        return pd.DataFrame()
    result = df.copy()
    if "trade_date" in result.columns:
        parsed = pd.to_datetime(result["trade_date"].astype(str), format="%Y%m%d", errors="coerce")
        fallback = pd.to_datetime(result["trade_date"], errors="coerce")
        result["trade_date"] = parsed.fillna(fallback)
        result = result.sort_values("trade_date").reset_index(drop=True)

    mapping = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "vol": "Volume",
        "volume": "Volume",
        "amount": "Amount",
    }
    for lower, upper in mapping.items():
        if lower in result.columns and upper not in result.columns:
            result[upper] = result[lower]
        if upper in result.columns and lower not in result.columns:
            result[lower] = result[upper]

    if "pct_chg" not in result.columns and "Close" in result.columns:
        result["pct_chg"] = result["Close"].pct_change().fillna(0) * 100

    return result


def _candidate_names(ts_code):
    base = ts_code.upper()
    stem = base.split(".")[0]
    names = {f"{base}.csv", f"{base.lower()}.csv", f"{stem}.csv"}
    if "." in base:
        left, right = base.split(".", 1)
        names.add(f"{left}.{right.lower()}.csv")
        names.add(f"{left}.{right.upper()}.csv")
    return sorted(names)
