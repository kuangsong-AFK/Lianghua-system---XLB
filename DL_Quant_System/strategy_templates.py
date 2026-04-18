import numpy as np
import pandas as pd


# ==========================================
# 策略一：阿波罗趋势增强 (Apollo Trend Pro)
# 逻辑：EMA趋势双确认 + ATR波动率过滤 + 量价齐升验证
# ==========================================
def strategy_apollo(df):
    # 1. 基础指标计算 (主图显示)
    df['MAIN_EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['MAIN_EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()

    # 2. 波动率风控 (副图1显示)
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift(1)).abs()
    low_close = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['SUB1_ATR'] = tr.rolling(window=14).mean()

    # 3. 能量潮 (副图2显示)
    df['SUB2_OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()

    # 核心逻辑：
    # 做多：EMA金叉 + OBV向上(量价配合) + 当前波幅 > 1.5倍平均波幅(真实突破)
    # 做空：EMA死叉 + OBV向下 + 当前波幅 > 1.5倍平均波幅
    df['Signal'] = 0
    condition_long = (df['MAIN_EMA12'] > df['MAIN_EMA26']) & \
                     (df['SUB2_OBV'] > df['SUB2_OBV'].shift(1)) & \
                     (tr > df['SUB1_ATR'] * 1.5)

    condition_short = (df['MAIN_EMA12'] < df['MAIN_EMA26']) & \
                      (df['SUB2_OBV'] < df['SUB2_OBV'].shift(1)) & \
                      (tr > df['SUB1_ATR'] * 1.5)

    df.loc[condition_long, 'Signal'] = 1
    df.loc[condition_short, 'Signal'] = -1
    return df


# ==========================================
# 策略二：R-Breaker 极速日内 (日内交易之王)
# 逻辑：基于昨日价格生成6个关键价位，捕捉日内趋势突破与反转
# ==========================================
def strategy_r_breaker(df):
    # 仅适用于日内高频或分钟线
    high = df['High'].shift(1)
    low = df['Low'].shift(1)
    close = df['Close'].shift(1)

    pivot = (high + low + close) / 3
    # 关键支撑压力位 (主图显示)
    df['MAIN_B_Setup'] = pivot + (high - low)  # 突破买入价
    df['MAIN_S_Setup'] = pivot - (high - low)  # 突破卖出价
    df['MAIN_S_Enter'] = 2 * pivot - low  # 反转卖出价
    df['MAIN_B_Enter'] = 2 * pivot - high  # 反转买入价

    # 信号逻辑
    df['Signal'] = 0
    # 趋势突破逻辑
    df.loc[df['Close'] > df['MAIN_B_Setup'], 'Signal'] = 1
    df.loc[df['Close'] < df['MAIN_S_Setup'], 'Signal'] = -1

    # 反转逻辑 (简单演示版)
    df.loc[(df['High'] > df['MAIN_S_Enter']) & (df['Close'] < df['MAIN_S_Enter']), 'Signal'] = -1
    df.loc[(df['Low'] < df['MAIN_B_Enter']) & (df['Close'] > df['MAIN_B_Enter']), 'Signal'] = 1

    return df


# ==========================================
# 策略三：斯巴达统计套利 (Statistical Arbitrage)
# 逻辑：利用布林带宽度(BBW)识别挤压，捕捉波动率回归带来的确定性机会
# ==========================================
def strategy_spartan(df):
    # 1. 布林带系统 (主图)
    df['MAIN_MID'] = df['Close'].rolling(20).mean()
    std = df['Close'].rolling(20).std()
    df['MAIN_UP'] = df['MAIN_MID'] + 2 * std
    df['MAIN_DN'] = df['MAIN_MID'] - 2 * std

    # 2. 波动率挤压指标 (副图1)
    df['SUB1_BB_WIDTH'] = (df['MAIN_UP'] - df['MAIN_DN']) / df['MAIN_MID']

    # 信号逻辑：
    # 当带宽 BB_WIDTH 处于极低水平(收口)后的强力张口突破，是最稳定的
    df['Signal'] = 0
    width_threshold = df['SUB1_BB_WIDTH'].rolling(100).quantile(0.2)  # 取过去100天最窄的20%时间

    # 宽带收窄后的向上/下突破
    df.loc[(df['SUB1_BB_WIDTH'].shift(1) < width_threshold) & (df['Close'] > df['MAIN_UP']), 'Signal'] = 1
    df.loc[(df['SUB1_BB_WIDTH'].shift(1) < width_threshold) & (df['Close'] < df['MAIN_DN']), 'Signal'] = -1

    return df