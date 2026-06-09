import numpy as np
import pandas as pd


def simple_backtest(
    df,
    predictions=None,
    signals=None,
    commission=0.0003,
    slippage=0.0005,
    allow_short=False,
):
    """
    Vectorized backtest for daily bars.

    Signal semantics:
    - allow_short=False: 1 opens/keeps long, -1 exits to cash, 0 keeps previous state.
    - allow_short=True: 1 long, -1 short, 0 keeps previous state.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame(), _empty_metrics()

    test_df = df.copy().reset_index(drop=True)
    close_col = _find_col(test_df, "close", "Close")
    high_col = _find_col(test_df, "high", "High")
    low_col = _find_col(test_df, "low", "Low")
    if close_col is None:
        raise ValueError("backtest requires a close/Close column")

    if predictions is not None:
        test_df = test_df.tail(len(predictions)).copy().reset_index(drop=True)
        raw_signal = pd.Series(np.where(np.asarray(predictions).reshape(-1) > 1.0, 1, -1), index=test_df.index)
        test_df["pred_change"] = np.asarray(predictions).reshape(-1)
    elif signals is not None:
        raw_signal = pd.Series(signals, index=test_df.index).fillna(0)
        test_df["pred_change"] = 0
    else:
        raise ValueError("must provide predictions or signals")

    raw_signal = raw_signal.apply(_normalize_signal).astype(int)
    test_df["signal"] = raw_signal
    test_df["Signal"] = raw_signal
    test_df["position"] = _signals_to_position(raw_signal, allow_short=allow_short)

    returns = _daily_returns(test_df, close_col)
    test_df["market_return"] = returns
    test_df["trade_size"] = test_df["position"].diff().abs().fillna(test_df["position"].abs())
    test_df["cost"] = test_df["trade_size"] * (commission + slippage)
    test_df["strategy_return"] = test_df["position"].shift(1).fillna(0) * returns - test_df["cost"]
    test_df["cum_market_return"] = (1 + returns.fillna(0)).cumprod()
    test_df["cum_strategy_return"] = (1 + test_df["strategy_return"].fillna(0)).cumprod()
    test_df["Cum_Prod"] = test_df["cum_strategy_return"]
    test_df["Ret"] = returns
    test_df["Pos"] = test_df["position"]
    test_df["Strat_Ret"] = test_df["strategy_return"]

    low = test_df[low_col] if low_col else test_df[close_col]
    high = test_df[high_col] if high_col else test_df[close_col]
    prev_pos = test_df["position"].shift(1).fillna(0)
    test_df["buy_point"] = np.where((test_df["position"] > prev_pos) & (test_df["position"] > 0), low * 0.98, np.nan)
    test_df["sell_point"] = np.where((test_df["position"] < prev_pos) & (prev_pos > 0), high * 1.02, np.nan)

    metrics = _metrics(test_df, close_col)
    return test_df, metrics


def _signals_to_position(signal, allow_short):
    position = []
    current = 0
    for raw in signal:
        sig = _normalize_signal(raw)
        if allow_short:
            if sig != 0:
                current = sig
        else:
            if sig > 0:
                current = 1
            elif sig < 0:
                current = 0
        position.append(current)
    return pd.Series(position, index=signal.index, dtype=float)


def _daily_returns(df, close_col):
    pct_col = _find_col(df, "pct_chg", "Pct_Chg")
    if pct_col is not None:
        return pd.to_numeric(df[pct_col], errors="coerce").fillna(0) / 100.0
    return pd.to_numeric(df[close_col], errors="coerce").pct_change().fillna(0)


def _metrics(df, close_col):
    returns = df["strategy_return"].fillna(0)
    cumulative = df["cum_strategy_return"].fillna(1)
    total_return = cumulative.iloc[-1] - 1 if len(cumulative) else 0
    annual_return = (1 + total_return) ** (252 / max(1, len(df))) - 1 if total_return > -1 else -1
    vol = returns.std() * np.sqrt(252)
    sharpe = (annual_return - 0.03) / vol if vol and not np.isnan(vol) else 0
    peak = cumulative.cummax()
    max_drawdown = ((cumulative - peak) / peak).min() if len(cumulative) else 0
    trade_returns = _completed_trade_returns(df, close_col)
    wins = [value for value in trade_returns if value > 0]
    win_rate = len(wins) / len(trade_returns) if trade_returns else 0
    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "win_rate": win_rate,
        "trades": len(trade_returns),
        "exposure": float((df["position"].abs() > 0).mean()) if len(df) else 0,
        "turnover": float(df["trade_size"].sum()) if "trade_size" in df else 0,
    }


def _completed_trade_returns(df, close_col):
    prices = pd.to_numeric(df[close_col], errors="coerce")
    trades = []
    entry_price = None
    entry_side = 0
    prev_pos = 0
    for idx, pos in enumerate(df["position"]):
        if prev_pos == 0 and pos != 0:
            entry_price = prices.iloc[idx]
            entry_side = pos
        elif prev_pos != 0 and pos != prev_pos and entry_price and entry_price > 0:
            exit_price = prices.iloc[idx]
            if entry_side > 0:
                trades.append(exit_price / entry_price - 1)
            else:
                trades.append(entry_price / exit_price - 1)
            entry_price = prices.iloc[idx] if pos != 0 else None
            entry_side = pos
        prev_pos = pos
    return trades


def _normalize_signal(value):
    try:
        value = float(value)
    except Exception:
        text = str(value).lower().strip()
        if any(token in text for token in ("buy", "long", "true", "yes", "1")):
            return 1
        if any(token in text for token in ("sell", "short", "-1")):
            return -1
        return 0
    if value > 0.1:
        return 1
    if value < -0.1:
        return -1
    return 0


def _find_col(df, *names):
    for name in names:
        if name in df.columns:
            return name
    lower_map = {str(col).lower(): col for col in df.columns}
    for name in names:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


def _empty_metrics():
    return {
        "total_return": 0,
        "annual_return": 0,
        "max_drawdown": 0,
        "sharpe": 0,
        "win_rate": 0,
        "trades": 0,
        "exposure": 0,
        "turnover": 0,
    }
