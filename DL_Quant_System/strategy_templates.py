import pandas as pd
import numpy as np


# ==============================================================================
# ☯️ 策略一：简易缠论核心 (分型与动能背离)
# 流派：形态学 + 动力学左侧抄底/摸顶
# 逻辑：严格定义顶底分型，结合 MACD 红绿柱面积衰竭（背离），捕捉局部绝对高低点。
# ==============================================================================
def strategy_chanlun(df):
    # 1. 动力学指标：MACD 及柱状图 (副图 1 显示)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['SUB1_MACD_DIFF'] = exp1 - exp2
    df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()
    df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])

    # 2. 形态学指标：严格顶底分型探测 (避免未来函数，判定前一根 K 线为分型中枢)
    # 底分型：前一根K线最低价低于当前和前两根
    is_bot_frac = (df['Low'].shift(1) < df['Low']) & (df['Low'].shift(1) < df['Low'].shift(2))
    # 顶分型：前一根K线最高价高于当前和前两根
    is_top_frac = (df['High'].shift(1) > df['High']) & (df['High'].shift(1) > df['High'].shift(2))

    # 辅助画线：在主图上延伸顶底分型的关键阻力/支撑位
    df['MAIN_BOT_LINE'] = np.where(is_bot_frac, df['Low'].shift(1), np.nan)
    df['MAIN_TOP_LINE'] = np.where(is_top_frac, df['High'].shift(1), np.nan)
    df['MAIN_BOT_LINE'] = pd.Series(df['MAIN_BOT_LINE']).ffill()
    df['MAIN_TOP_LINE'] = pd.Series(df['MAIN_TOP_LINE']).ffill()

    # 3. 生成缠论级别买卖信号
    df['Signal'] = 0
    # 一买/二买：出现底分型 + 价格处于20日均线下方(超跌) + MACD绿柱缩短(动能衰竭/背离)
    buy_cond = is_bot_frac & (df['Close'] < df['Close'].rolling(20).mean()) & (
                df['SUB1_MACD_HIST'] > df['SUB1_MACD_HIST'].shift(1))
    # 一卖/二卖：出现顶分型 + 价格处于20日均线上方(超涨) + MACD红柱缩短(动能衰竭/背离)
    sell_cond = is_top_frac & (df['Close'] > df['Close'].rolling(20).mean()) & (
                df['SUB1_MACD_HIST'] < df['SUB1_MACD_HIST'].shift(1))

    df.loc[buy_cond, 'Signal'] = 1
    df.loc[sell_cond, 'Signal'] = -1
    return df


# ==============================================================================
# 🐢 策略二：海龟交易法则 (唐奇安通道增强版)
# 流派：极右侧趋势跟踪 (胜率中等，盈亏比极大)
# 逻辑：突破20日最高点做多，跌破10日最低点止损，利用 ATR 监控波动率。
# ==============================================================================
def strategy_turtle(df):
    # 1. 唐奇安通道计算 (主图显示)
    # 上轨：过去20个周期的最高价；下轨：过去10个周期的最低价
    df['MAIN_UPPER_20'] = df['High'].shift(1).rolling(20).max()
    df['MAIN_LOWER_10'] = df['Low'].shift(1).rolling(10).min()

    # 2. 真实波幅 ATR (副图 1 显示，海龟交易用来衡量市场活跃度)
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift(1)).abs()
    tr3 = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['SUB1_ATR'] = tr.rolling(14).mean()

    # 3. 生成趋势买卖信号
    df['Signal'] = 0
    # 收盘价突破20周期最高点，启动无脑做多！
    df.loc[df['Close'] > df['MAIN_UPPER_20'], 'Signal'] = 1
    # 收盘价跌破10周期最低点，趋势终结，无情平多/反手做空！
    df.loc[df['Close'] < df['MAIN_LOWER_10'], 'Signal'] = -1

    # 【核心滤网】：防止信号在震荡市连续闪烁，进行持仓状态合并
    df['Signal'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
    # 取差分，使得图表上只在真正开平仓的那一根K线显示箭头
    df['Signal'] = df['Signal'].diff().fillna(0)
    df['Signal'] = np.sign(df['Signal'])
    return df


# ==============================================================================
# 🚀 策略三：TTM Squeeze (波动率挤压爆发策略)
# 流派：约翰·卡特经典突破策略
# 逻辑：当布林带(BB)收窄并完全钻进肯特纳通道(KC)内部时，说明波动率极度萎缩(挤压)。
#      一旦挤压解除(BB穿出KC)且动量指向上方，代表将有爆炸性主升浪。
# ==============================================================================
def strategy_ttm_squeeze(df):
    # 1. 布林带 Bollinger Bands (主图显示)
    df['MAIN_BB_MID'] = df['Close'].rolling(20).mean()
    std = df['Close'].rolling(20).std()
    df['MAIN_BB_UP'] = df['MAIN_BB_MID'] + 2 * std
    df['MAIN_BB_DN'] = df['MAIN_BB_MID'] - 2 * std

    # 2. 肯特纳通道 Keltner Channels (基于 ATR)
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift(1)).abs()
    tr3 = (df['Low'] - df['Close'].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(20).mean()
    # 注意：为了让图表不至于太乱，肯特纳通道隐式计算，不输出到 MAIN_
    kc_up = df['MAIN_BB_MID'] + 1.5 * atr
    kc_dn = df['MAIN_BB_MID'] - 1.5 * atr

    # 3. 挤压信号 Squeeze (副图 1 显示)
    # 当布林带上下轨都在肯特纳通道内时，Squeeze 成立 (=1)，否则为 0
    df['SUB1_SQUEEZE'] = np.where((df['MAIN_BB_UP'] < kc_up) & (df['MAIN_BB_DN'] > kc_dn), 1, 0)

    # 4. 动量指标 Momentum (副图 2 显示)
    # 简化的线性动量：当前收盘价与20日均线的差值
    df['SUB2_MOMENTUM'] = df['Close'] - df['MAIN_BB_MID']
    df['SUB2_MOM_HIST'] = df['SUB2_MOMENTUM']  # 渲染成红绿柱状图

    # 5. 交易信号
    df['Signal'] = 0
    # Squeeze 解除(由1变0，即波动率开始放大) 且 动量为正 -> 火箭发射，做多！
    sqz_fire = (df['SUB1_SQUEEZE'].shift(1) == 1) & (df['SUB1_SQUEEZE'] == 0)
    df.loc[sqz_fire & (df['SUB2_MOMENTUM'] > 0), 'Signal'] = 1
    # Squeeze 解除 且 动量为负 -> 瀑布大跌，做空！
    df.loc[sqz_fire & (df['SUB2_MOMENTUM'] < 0), 'Signal'] = -1
    return df


# ==============================================================================
# 🤖 策略四：自适应统计学 RSI (Adaptive RSI)
# 流派：量化高频/短线震荡做波段
# 逻辑：传统的 RSI 超买超卖线是死板的 70 和 30，容易在单边市钝化亏大钱。
#      此策略将 Bollinger Bands 套用在 RSI 上，生成随波动率动态变化的超买超卖阈值。
# ==============================================================================
def strategy_adaptive_rsi(df):
    # 1. 基础 EMA 趋势过滤 (主图显示)
    df['MAIN_EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # 2. 计算标准 14 日 RSI (副图 1 显示)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['SUB1_RSI'] = 100 - (100 / (1 + rs))

    # 3. 计算自适应动态超买超卖轨 (在副图 1 叠加)
    rsi_ma = df['SUB1_RSI'].rolling(50).mean()
    rsi_std = df['SUB1_RSI'].rolling(50).std()

    # 动态阈值线
    df['SUB1_OB_LEVEL'] = rsi_ma + 2 * rsi_std  # 动态超买线 (OverBought)
    df['SUB1_OS_LEVEL'] = rsi_ma - 2 * rsi_std  # 动态超卖线 (OverSold)

    df['Signal'] = 0

    # 终极多头逻辑：
    # ① 大级别趋势向上 (Close > EMA50)
    # ② 短线被过度砸盘，RSI 跌穿动态下轨后，重新拐头向上穿回轨内 (确认止跌)
    buy_cond = (df['Close'] > df['MAIN_EMA50']) & \
               (df['SUB1_RSI'].shift(1) < df['SUB1_OS_LEVEL'].shift(1)) & \
               (df['SUB1_RSI'] > df['SUB1_OS_LEVEL'])

    # 终极空头逻辑：
    # ① 大级别趋势向下 (Close < EMA50)
    # ② 短线过度亢奋，RSI 冲破动态上轨后，拐头跌回轨内 (确认见顶)
    sell_cond = (df['Close'] < df['MAIN_EMA50']) & \
                (df['SUB1_RSI'].shift(1) > df['SUB1_OB_LEVEL'].shift(1)) & \
                (df['SUB1_RSI'] < df['SUB1_OB_LEVEL'])

    df.loc[buy_cond, 'Signal'] = 1
    df.loc[sell_cond, 'Signal'] = -1
    return df