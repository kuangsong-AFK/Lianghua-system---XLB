import os
import sys
import numpy as np
import pandas as pd
import tushare as ts
import traceback
import textwrap
import streamlit as st
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta

# --- 关键修正：援军必须先到场！---
# 将自定义模块的导入移到最上方，防止 NameError
try:
    from backtester.engine import simple_backtest
    from utils.feature_engineering import construct_features

    # 尝试导入 LSTM 模型，防报错
    try:
        from models.lstm_model import LSTMPredictor
    except ImportError:
        pass
except ImportError:
    print("⚠️ 警告：缺少 backtester 或 utils 模块，请检查目录结构！")

# 配置 Tushare Token
TS_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"
ts.set_token(TS_TOKEN)
pro = ts.pro_api()

# 设置绘图风格
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False


def format_stock_code(code):
    code = str(code).strip()
    if len(code) == 6 and code.isdigit():
        if code.startswith(('60', '68', '90')):
            return f"{code}.SH"
        elif code.startswith(('00', '30', '20')):
            return f"{code}.SZ"
        elif code.startswith(('43', '83', '87')):
            return f"{code}.BJ"
    return code


# --- 参数默认值 ---
DEFAULT_PARAMS = {
    'ma1': 5, 'ma2': 10, 'ma3': 20, 'ma4': 60,
    'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9,
    'rsi_period': 14,
    'kdj_n': 9, 'kdj_m1': 3, 'kdj_m2': 3,
    'bias1': 6, 'bias2': 12, 'bias3': 24
}


@st.cache_data(show_spinner=False)
def calculate_indicators(df, params=None):
    if params is None: params = DEFAULT_PARAMS
    for k, v in DEFAULT_PARAMS.items():
        if k not in params: params[k] = v

    df = df.copy()

    # 均线
    df['ma_1'] = df['close'].rolling(int(params['ma1'])).mean()
    df['ma_2'] = df['close'].rolling(int(params['ma2'])).mean()
    df['ma_3'] = df['close'].rolling(int(params['ma3'])).mean()
    df['ma_4'] = df['close'].rolling(int(params['ma4'])).mean()

    # MACD
    fast, slow, sig = int(params['macd_fast']), int(params['macd_slow']), int(params['macd_signal'])
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    df['macd_dif'] = ema_fast - ema_slow
    df['macd_dea'] = df['macd_dif'].ewm(span=sig, adjust=False).mean()
    df['macd_hist'] = (df['macd_dif'] - df['macd_dea']) * 2

    # RSI
    period = int(params['rsi_period'])
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # KDJ
    n, m1, m2 = int(params['kdj_n']), int(params['kdj_m1']), int(params['kdj_m2'])
    low_list = df['low'].rolling(n, min_periods=n).min()
    high_list = df['high'].rolling(n, min_periods=n).max()
    rsv = (df['close'] - low_list) / (high_list - low_list) * 100
    df['k'] = rsv.ewm(com=m1 - 1, adjust=False).mean()
    df['d'] = df['k'].ewm(com=m2 - 1, adjust=False).mean()
    df['j'] = 3 * df['k'] - 2 * df['d']

    # BIAS
    df['bias1'] = (df['close'] - df['close'].rolling(int(params['bias1'])).mean()) / df['close'].rolling(
        int(params['bias1'])).mean() * 100
    df['bias2'] = (df['close'] - df['close'].rolling(int(params['bias2'])).mean()) / df['close'].rolling(
        int(params['bias2'])).mean() * 100
    df['bias3'] = (df['close'] - df['close'].rolling(int(params['bias3'])).mean()) / df['close'].rolling(
        int(params['bias3'])).mean() * 100

    return df.fillna(0)


@st.cache_data(ttl=43200, show_spinner=False)
def download_data_with_retry(ts_code):
    end_date = datetime.now().strftime('%Y%m%d')
    start_20 = (datetime.now() - timedelta(days=20 * 365)).strftime('%Y%m%d')
    try:
        df = pro.daily(ts_code=ts_code, start_date=start_20, end_date=end_date)
        if df is not None and len(df) > 100:
            return df.sort_values('trade_date').reset_index(drop=True), 20
    except:
        pass
    start_5 = (datetime.now() - timedelta(days=5 * 365)).strftime('%Y%m%d')
    try:
        df = pro.daily(ts_code=ts_code, start_date=start_5, end_date=end_date)
        if df is not None and not df.empty:
            return df.sort_values('trade_date').reset_index(drop=True), 5
    except:
        pass
    return None, 0


# --- 核心：生成专业研报 HTML ---
def generate_strategy_report(df, metrics, code, strategy_code=""):
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='#f4f4f5')
    ax.set_facecolor('#ffffff')
    ax.plot(df.index, df['close'], label='Close Price', color='#333333', linewidth=1.5, alpha=0.8)

    buy_signals = df[df['buy_point'] == 1]
    sell_signals = df[df['buy_point'] == -1]

    if not buy_signals.empty:
        ax.scatter(buy_signals.index, buy_signals['low'] * 0.98, marker='^', color='#d32f2f', s=100, label='Buy',
                   zorder=5)
    if not sell_signals.empty:
        ax.scatter(sell_signals.index, sell_signals['high'] * 1.02, marker='v', color='#2e7d32', s=100, label='Sell',
                   zorder=5)

    ax.set_title(f"{code} Strategy Analysis Chart", fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.3)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    win_rate = metrics.get('win_rate', 0)
    total_return = (df['cum_strategy_return'].iloc[-1] - 1)
    sharpe = metrics.get('sharpe', 0)
    max_dd = metrics.get('max_drawdown', 0)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{code} 深度复盘报告</title>
        <style>
            body {{ font-family: 'Helvetica Neue', Helvetica, 'Microsoft YaHei', Arial, sans-serif; background-color: #f4f4f5; color: #333; margin: 0; padding: 40px; }}
            .container {{ max-width: 900px; margin: 0 auto; background: #fff; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; color: #18181b; letter-spacing: 1px; }}
            .header p {{ color: #71717a; margin-top: 10px; font-size: 0.9em; }}
            .metrics-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 40px; }}
            .metric-card {{ background: #fafafa; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #eee; }}
            .metric-value {{ display: block; font-size: 24px; font-weight: bold; margin-bottom: 5px; color: #000; }}
            .metric-label {{ font-size: 12px; color: #71717a; text-transform: uppercase; letter-spacing: 1px; }}
            .color-red {{ color: #ef4444; }} .color-green {{ color: #10b981; }}
            .chart-section {{ margin-bottom: 40px; text-align: center; }}
            .chart-img {{ max-width: 100%; border-radius: 8px; border: 1px solid #eee; }}
            .strategy-box {{ background: #27272a; color: #eee; padding: 20px; border-radius: 8px; font-family: monospace; font-size: 0.9em; margin-bottom: 40px; overflow-x: auto; }}
            .footer {{ text-align: center; margin-top: 50px; font-size: 0.8em; color: #a1a1aa; border-top: 1px solid #eee; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛡️ 小吕布量化 · 战役复盘报告</h1>
                <p>标的代码: {code} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            <div class="metrics-grid">
                <div class="metric-card"><span class="metric-value color-red">{win_rate:.2%}</span><span class="metric-label">胜率 (Win Rate)</span></div>
                <div class="metric-card"><span class="metric-value {'color-red' if total_return > 0 else 'color-green'}">{total_return * 100:+.2f}%</span><span class="metric-label">累计收益 (Return)</span></div>
                <div class="metric-card"><span class="metric-value">{sharpe:.2f}</span><span class="metric-label">夏普比率 (Sharpe)</span></div>
                <div class="metric-card"><span class="metric-value color-green">{max_dd:.2%}</span><span class="metric-label">最大回撤 (Drawdown)</span></div>
            </div>
            <div class="chart-section"><h3>📊 买卖点位回溯</h3><img src="data:image/png;base64,{img_str}" class="chart-img"></div>
            <div class="strategy-box"><h3>🧠 AI 策略逻辑</h3><pre>{strategy_code if strategy_code else "无策略代码"}</pre></div>
            <div class="footer"><p>Generated by Little Bu Quant System | Power to the Traders</p></div>
        </div>
    </body>
    </html>
    """
    return html_content


def run_full_pipeline(code, epochs=10, params=None):
    ts_code = format_stock_code(code)
    df_raw, years = download_data_with_retry(ts_code)
    if df_raw is None: return None, None, 0, "无法下载数据"

    try:
        df = calculate_indicators(df_raw, params)
        df_features = construct_features(df)
        predictor = LSTMPredictor(sequence_length=10)
        X, y = predictor.prepare_data(df_features)
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        predictor.build_model((X.shape[1], X.shape[2]))
        predictor.model.fit(X_train, y_train, epochs=epochs, batch_size=32, verbose=0)
        y_pred_prob = predictor.model.predict(X_test)
        signals = (y_pred_prob.flatten() > 0.5).astype(int)
        test_len = len(signals)
        df_test = df_features.iloc[-test_len:].copy()
        res_df, metrics = simple_backtest(df_test, signals=signals)
        res_df['signal'] = signals
        res_df['buy_point'] = (res_df['signal'].diff() == 1).astype(int)

        cols_to_copy = ['ma_1', 'ma_2', 'ma_3', 'ma_4', 'vol', 'macd_dif', 'macd_dea', 'macd_hist',
                        'k', 'd', 'j', 'rsi', 'bias1', 'bias2', 'bias3', 'date', 'trade_date']
        for col in cols_to_copy:
            if col in df.columns:
                try:
                    res_df[col] = df.loc[res_df.index, col]
                except:
                    pass
        return res_df, metrics, years, None
    except Exception as e:
        return None, None, 0, str(traceback.format_exc())


def run_ai_strategy(code, strategy_code, params=None):
    ts_code = format_stock_code(code)
    df_raw, years = download_data_with_retry(ts_code)
    if df_raw is None: return None, None, 0, "无法下载数据"

    df = calculate_indicators(df_raw, params)
    if 'trade_date' in df.columns: df = df.rename(columns={'trade_date': 'date'})

    try:
        # --- 影子分身 & 语义映射 ---
        ma_mapping = {'ma1': 'ma_1', 'ma2': 'ma_2', 'ma3': 'ma_3', 'ma4': 'ma_4'}
        for param_key, real_col in ma_mapping.items():
            if param_key in params:
                period = int(params[param_key])
                df[f'ma_{period}'] = df[real_col]
                df[f'ma{period}'] = df[real_col]

        df['ma_short'] = df['ma_1']
        df['ma_long'] = df['ma_2']
        df['short_ma'] = df['ma_1']
        df['long_ma'] = df['ma_2']
        df['fast_ma'] = df['ma_1']
        df['slow_ma'] = df['ma_2']
        df['ma_fast'] = df['ma_1']
        df['ma_slow'] = df['ma_2']

        df['macd'] = df['macd_dif']

        for col in ['open', 'high', 'low', 'close', 'vol', 'date']:
            if col in df.columns: df[col.capitalize()] = df[col]

            # --- 核心：防自杀备份 ---
        original_df = df.copy()

        strategy_code = textwrap.dedent(strategy_code).strip()
        scope = {'df': df, 'np': np, 'pd': pd, 'PARAMS': params}

        exec(strategy_code, scope)

        # --- 核心：防自杀回滚 ---
        current_df = scope.get('df')
        if current_df is None or not isinstance(current_df, pd.DataFrame):
            found_rescue = False
            for k, v in scope.items():
                if isinstance(v, pd.DataFrame) and len(v) == len(original_df):
                    scope['df'] = v
                    current_df = v
                    found_rescue = True
                    break
            if not found_rescue:
                scope['df'] = original_df
                current_df = original_df

        df_res = None

        # 1. 检查 df['signal']
        if 'signal' in current_df.columns:
            df_res = current_df

        # 2. 检查独立 signal 变量
        elif 'signal' in scope:
            val = scope['signal']
            if hasattr(val, '__len__') and len(val) == len(current_df):
                current_df['signal'] = val
                df_res = current_df

        # 3. 暴力搜救
        if df_res is None:
            potential_vars = ['condition', 'Condition', 'buy', 'Buy', 'signal_cond', 'c', 's', 'res', 'ans', 'flag',
                              'out']
            for v_name in potential_vars:
                if v_name in scope:
                    val = scope[v_name]
                    if hasattr(val, '__len__') and len(val) == len(current_df):
                        current_df['signal'] = np.where(val, 1, 0)
                        df_res = current_df
                        print(f"✅ 小吕布：已征用变量 '{v_name}' 作为信号！")
                        break

            if df_res is None:
                for k, v in scope.items():
                    if k in ['df', 'np', 'pd', 'PARAMS']: continue
                    if k.startswith('_'): continue
                    if hasattr(v, '__len__') and len(v) == len(current_df):
                        try:
                            sample = np.array(v)[:10]
                            if sample.dtype == bool or np.issubdtype(sample.dtype, np.number):
                                current_df['signal'] = np.where(v, 1, 0)
                                df_res = current_df
                                print(f"🔥 小吕布：绝境逢生！强行征用变量 '{k}'！")
                                break
                        except:
                            pass

        if df_res is None:
            return None, None, 0, f"小吕布：AI 生成代码执行后，df 被破坏且未找到任何替代信号。请重试！"

        try:
            df_res['signal'] = df_res['signal'].fillna(0).astype(int)
        except:
            s = df_res['signal'].astype(str).str.lower().str.strip()
            df_res['signal'] = np.where(s.str.contains(r'buy|hold|long|yes|true|1', regex=True), 1, 0)
            df_res['signal'] = df_res['signal'].astype(int)

        res_df, metrics = simple_backtest(df_res, signals=df_res['signal'])

        if len(res_df) == len(df_res):
            res_df['signal'] = df_res['signal'].values
            res_df['buy_point'] = (res_df['signal'].diff() == 1).astype(int)
            cols_to_copy = ['ma_1', 'ma_2', 'ma_3', 'ma_4', 'vol',
                            'macd_dif', 'macd_dea', 'macd_hist',
                            'k', 'd', 'j', 'rsi', 'bias1', 'bias2', 'bias3']
            for col in cols_to_copy:
                if col in df_res.columns:
                    res_df[col] = df_res[col].values
        else:
            res_df['signal'] = df_res['signal']

        return res_df, metrics, years, None
    except Exception as e:
        return None, None, 0, str(traceback.format_exc())