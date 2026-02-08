import pandas as pd
import numpy as np


def simple_backtest(df, predictions=None, signals=None):
    """
    通用回测引擎：支持 LSTM 预测值 或 AI 生成的信号
    :param df: 数据框
    :param predictions: LSTM 的预测值 (可选)
    :param signals: AI 生成的 0/1 信号序列 (可选)
    """
    # 必须拷贝一份，防止修改原始数据
    test_df = df.copy()

    # 模式 A: 基于 LSTM 预测值 (原有逻辑)
    if predictions is not None:
        # 截取对应长度
        test_df = test_df.tail(len(predictions)).copy()
        test_df['pred_change'] = predictions
        # 策略：预测涨幅 > 1.0% 买入
        test_df['signal'] = np.where(test_df['pred_change'] > 1.0, 1, 0)

    # 模式 B: 直接使用 AI 生成的信号 (新增逻辑)
    elif signals is not None:
        test_df['signal'] = signals
        # 填充 AI 策略可能产生的空值
        test_df['signal'] = test_df['signal'].fillna(0)
        # 确保也是只回测最后一部分数据（比如最近一年），或者全量回测
        # 这里默认全量回测 AI 策略
        test_df['pred_change'] = 0  # AI 模式下没有预测值，置0

    else:
        raise ValueError("必须提供 predictions 或 signals")

    # --- 统一的回测计算逻辑 ---

    # 标记买入点：信号 0 -> 1
    test_df['buy_point'] = np.where(
        (test_df['signal'] == 1) & (test_df['signal'].shift(1) == 0),
        test_df['low'] * 0.98,
        np.nan
    )

    # 标记卖出点：信号 1 -> 0 (可选，为了显示更清晰)
    test_df['sell_point'] = np.where(
        (test_df['signal'] == 0) & (test_df['signal'].shift(1) == 1),
        test_df['high'] * 1.02,
        np.nan
    )

    # 计算策略收益
    # 注意：这里简化处理，假设次日以收盘价买入/计算收益，实际可用 pct_chg
    test_df['strategy_return'] = test_df['signal'].shift(1) * (test_df['pct_chg'] / 100)
    test_df['strategy_return'] = test_df['strategy_return'].fillna(0)

    test_df['cum_market_return'] = (1 + test_df['pct_chg'] / 100).cumprod()
    test_df['cum_strategy_return'] = (1 + test_df['strategy_return']).cumprod()

    # --- 学术指标计算 ---
    returns = test_df['strategy_return']
    # 夏普比率
    sharpe = (returns.mean() * 252 - 0.03) / (returns.std() * np.sqrt(252)) if returns.std() != 0 else 0

    # 最大回撤
    cumulative = test_df['cum_strategy_return']
    peak = cumulative.expanding(min_periods=1).max()
    max_drawdown = ((cumulative - peak) / peak).min()

    # 胜率 (仅统计开仓交易)
    # 简单估算：只要持仓日的收益 > 0 就算赢
    holding_days = test_df[test_df['signal'].shift(1) == 1]
    if len(holding_days) > 0:
        win_rate = len(holding_days[holding_days['pct_chg'] > 0]) / len(holding_days)
    else:
        win_rate = 0

    metrics = {
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate
    }

    return test_df, metrics