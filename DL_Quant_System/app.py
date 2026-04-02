import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="小吕布量化 Pro", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 🛑 绝密兵符
# ==========================================
KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"

# ==========================================
# 注入 CSS (保持透明沉浸感)
# ==========================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], .block-container {
        background: transparent !important; padding-top: 2rem !important; 
    }
    header[data-testid="stHeader"], footer { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, span { color: #ffffff !important; }

    [data-testid="stSidebar"] {
        background: rgba(20, 20, 20, 0.6) !important;
        backdrop-filter: blur(15px) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    .glass-card {
        background: rgba(20, 20, 20, 0.75); backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    div.row-widget.stRadio > div { background: transparent; }
    div.row-widget.stRadio > div > label {
        background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; cursor: pointer; transition: 0.3s;
    }
    div.row-widget.stRadio > div > label:hover { background: rgba(253,16,80,0.2); }

    .stTextInput > div > div { background-color: rgba(0,0,0,0.7) !important; color: white !important; }
    div[data-testid="stChatMessageContent"] { background-color: rgba(40,44,52,0.9) !important; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1",
                timeout=30.0) if "sk-" in KIMI_API_KEY else None

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "主公，真·实盘回测沙盘已加载！请下令生成策略（例如：写一个双均线策略）。"}]
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "backtest_result" not in st.session_state: st.session_state.backtest_result = None

# ==========================================
# 🧭 内置侧边栏导航
# ==========================================
with st.sidebar:
    st.markdown("## 👑 小吕布量化")
    st.markdown("---")
    current_page = st.radio("系统导航", ["🤖 AI 战情室", "📊 实盘战场", "⚡ 深度回测"], label_visibility="collapsed")

# ==========================================
# 🤖 页面 1: AI 战情室
# ==========================================
if current_page == "🤖 AI 战情室":
    st.markdown('<div class="glass-card"><h3>🤖 AI 战情室 (Kimi 驱动)</h3></div>', unsafe_allow_html=True)

    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("主公请下令 (例如: 写一个MACD量化策略)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                if not client:
                    msg_box.error("🚨 API 连接失败！请检查兵符。")
                    st.session_state.messages.pop()
                else:
                    try:
                        msg_box.markdown("🧠 *军师正在推演战术 (请求 Kimi API...)*")
                        bt = "`" * 3

                        # 🔥 核心：严格限制 AI 的输出格式，确保代码能在沙盒中运行
                        system_prompt = f"""你是顶级量化专家。请务必给出Python代码，且代码用 {bt}python 和 {bt} 包裹。
请必须编写一个名为 `generate_signals(df)` 的函数。
输入 `df` 是包含 'Open', 'High', 'Low', 'Close', 'Volume' 列的 pandas DataFrame。
请在 `df` 中新增一列 'Signal'，当满足买入条件时设为 1，满足卖出条件时设为 -1，无动作设为 0。
最后必须 return df。只返回代码，不要解释！"""

                        stream = client.chat.completions.create(
                            model="moonshot-v1-8k",
                            messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
                            stream=True
                        )

                        full_response = ""
                        for chunk in stream:
                            if chunk.choices and len(chunk.choices) > 0:
                                delta = chunk.choices[0].delta.content
                                if delta:
                                    full_response += delta
                                    msg_box.markdown(full_response + "▌")

                        if not full_response:
                            msg_box.error("🚨 军师沉默了，请重试。")
                            st.session_state.messages.pop()
                        else:
                            msg_box.markdown(full_response)
                            code_pattern = bt + r"(?:python|Python)?\s*(.*?)" + bt
                            code_match = re.search(code_pattern, full_response, re.DOTALL | re.IGNORECASE)

                            if code_match:
                                st.session_state.generated_code = code_match.group(1).strip()
                                st.session_state.backtest_result = None  # 清空上次回测
                                st.toast("✅ 策略代码已就绪！请前往【实盘战场】执行。", icon="🚀")
                            else:
                                st.warning("⚠️ 未提取到代码，请让 AI 重新输出。")

                            st.session_state.messages.append({"role": "assistant", "content": full_response})
                    except Exception as e:
                        msg_box.error(f"📡 API 异常: {e}")
                        st.session_state.messages.pop()
        st.rerun()

# ==========================================
# 📊 页面 2: 实盘战场 (真机沙盒 + K线图)
# ==========================================
elif current_page == "📊 实盘战场":
    st.markdown('<div class="glass-card"><h3>⚔️ 实盘指控中心</h3></div>', unsafe_allow_html=True)

    col_ctrl, col_chart = st.columns([1, 2.5])

    with col_ctrl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        # 支持美股代码如 AAPL, TSLA, 甚至加密货币 BTC-USD
        target_stock = st.text_input("🎯 目标标的 (雅虎财经代码, 例如 AAPL)", value="AAPL")

        if st.session_state.generated_code:
            st.success("🟢 策略已装填")
            with st.expander("👀 策略源码"):
                st.code(st.session_state.generated_code, language='python')

            if st.button("🚀 执行历史回测", use_container_width=True, type="primary"):
                with st.spinner(f"正在拉取 {target_stock} 近一年历史数据并运行沙盒..."):
                    try:
                        # 1. 获取真实数据
                        df = yf.Ticker(target_stock).history(period="1y")
                        if df.empty:
                            st.error(f"拉取 {target_stock} 数据失败，请检查代码是否正确。")
                        else:
                            df.reset_index(inplace=True)
                            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)  # 清理时区

                            # 2. 建立安全沙盒执行 AI 代码
                            local_vars = {}
                            exec(st.session_state.generated_code, globals(), local_vars)

                            if 'generate_signals' not in local_vars:
                                st.error("AI 没按要求生成 `generate_signals` 函数，请回战情室重写。")
                            else:
                                # 3. 运行策略函数
                                df = local_vars['generate_signals'](df)

                                # 4. 计算金融指标
                                if 'Signal' not in df.columns:
                                    df['Signal'] = 0

                                # 将离散的 Signal 转换为持续的 Position (1多头，0空仓)
                                df['Position'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
                                df['Daily_Return'] = df['Close'].pct_change()
                                # 策略收益 = 昨日持仓 * 今日涨跌幅
                                df['Strategy_Return'] = df['Position'].shift(1) * df['Daily_Return']

                                df['Cumulative_Market'] = (1 + df['Daily_Return']).cumprod()
                                df['Cumulative_Strategy'] = (1 + df['Strategy_Return']).cumprod()

                                # 保存结果到 session
                                st.session_state.backtest_result = {
                                    "df": df,
                                    "ticker": target_stock
                                }
                    except Exception as e:
                        st.error(f"策略执行报错：{e} (可能是 AI 写的代码有 Bug，请让它修改)")
        else:
            st.warning("🟡 暂无策略代码。请先去【AI 战情室】下令。")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_chart:
        if st.session_state.backtest_result:
            df = st.session_state.backtest_result['df']
            ticker = st.session_state.backtest_result['ticker']

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f"#### 📈 {ticker} 策略实盘图谱")

            # 🔥 绘制专业 K 线图与买卖点
            fig = go.Figure()

            # K 线
            fig.add_trace(
                go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                               name='K线'))

            # 标出买卖点
            buy_signals = df[df['Signal'] == 1]
            sell_signals = df[df['Signal'] == -1]

            fig.add_trace(go.Scatter(x=buy_signals['Date'], y=buy_signals['Low'] * 0.98, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='lime'), name='买入'))
            fig.add_trace(go.Scatter(x=sell_signals['Date'], y=sell_signals['High'] * 1.02, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='red'), name='卖出'))

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)

            # 计算核心指标
            total_strategy_return = (df['Cumulative_Strategy'].iloc[-1] - 1) if not pd.isna(
                df['Cumulative_Strategy'].iloc[-1]) else 0
            total_market_return = (df['Cumulative_Market'].iloc[-1] - 1) if not pd.isna(
                df['Cumulative_Market'].iloc[-1]) else 0

            winning_days = len(df[df['Strategy_Return'] > 0])
            trading_days = len(df[df['Strategy_Return'] != 0])
            win_rate = winning_days / trading_days if trading_days > 0 else 0

            roll_max = df['Cumulative_Strategy'].cummax()
            drawdown = df['Cumulative_Strategy'] / roll_max - 1
            max_drawdown = drawdown.min()

            c1, c2, c3 = st.columns(3)
            c1.metric("策略总收益", f"{total_strategy_return * 100:.2f}%",
                      f"{total_strategy_return - total_market_return:.2%}")
            c2.metric("交易日胜率", f"{win_rate * 100:.2f}%")
            c3.metric("最大回撤", f"{max_drawdown * 100:.2f}%")

            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ⚡ 页面 3: 深度回测
# ==========================================
elif current_page == "⚡ 深度回测":
    st.markdown('<div class="glass-card"><h3>🚧 深度回测引擎扩建中...</h3></div>', unsafe_allow_html=True)