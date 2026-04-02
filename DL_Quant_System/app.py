import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time
import tushare as ts
import plotly.graph_objects as go

st.set_page_config(page_title="小吕布量化 Pro", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 🛑 绝密兵符：Tushare & Kimi 双持
# ==========================================
KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

# 初始化 Tushare 接口
pro = ts.pro_api(TUSHARE_TOKEN)

# ==========================================
# 注入沉浸式 CSS
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

    .glass-card {
        background: rgba(20, 20, 20, 0.75); backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 20px;
    }

    div.row-widget.stRadio > div > label {
        background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; cursor: pointer;
    }
    .stTextInput > div > div { background-color: rgba(0,0,0,0.7) !important; color: white !important; }
    div[data-testid="stChatMessageContent"] { background-color: rgba(40,44,52,0.9) !important; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1",
                timeout=30.0) if "sk-" in KIMI_API_KEY else None

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，Tushare 数据链已接通！请下令生成策略。"}]
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "backtest_result" not in st.session_state: st.session_state.backtest_result = None

# ==========================================
# 🧭 侧边栏
# ==========================================
with st.sidebar:
    st.markdown("## 👑 小吕布量化")
    st.markdown("---")
    current_page = st.radio("导航", ["🤖 AI 战情室", "📊 实盘战场", "⚡ 深度回测"], label_visibility="collapsed")

# ==========================================
# 🤖 AI 战情室
# ==========================================
if current_page == "🤖 AI 战情室":
    st.markdown('<div class="glass-card"><h3>🤖 AI 战情室 (Kimi × Tushare)</h3></div>', unsafe_allow_html=True)
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("主公请下令 (如: 帮我写一个基于5日均线的趋势策略)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                try:
                    msg_box.markdown("🧠 *军师正在基于 Tushare 规范推演战术...*")
                    bt = "`" * 3
                    system_prompt = f"""你是顶级量化专家。请给出Python代码并用 {bt}python 和 {bt} 包裹。
必须包含 `generate_signals(df)` 函数。
输入 df 列名为: ['trade_date', 'open', 'high', 'low', 'close', 'vol']。
在 df 中新增 'Signal' 列：1为买入，-1为卖出，0为观望。
只需返回代码。"""
                    stream = client.chat.completions.create(model="moonshot-v1-8k", messages=[{"role": "system",
                                                                                               "content": system_prompt}] + st.session_state.messages,
                                                            stream=True)
                    full_response = ""
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            msg_box.markdown(full_response + "▌")
                    msg_box.markdown(full_response)

                    code_match = re.search(bt + r"(?:python)?\s*(.*?)" + bt, full_response, re.DOTALL | re.IGNORECASE)
                    if code_match:
                        st.session_state.generated_code = code_match.group(1).strip()
                        st.toast("🚀 策略已装填至战场！", icon="✅")
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"API 异常: {e}")
        st.rerun()

# ==========================================
# 📊 实盘战场 (Tushare 驱动)
# ==========================================
elif current_page == "📊 实盘战场":
    st.markdown('<div class="glass-card"><h3>⚔️ Tushare 实盘分析</h3></div>', unsafe_allow_html=True)
    col_ctrl, col_chart = st.columns([1, 2.5])

    with col_ctrl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        # Tushare 格式通常是 000001.SZ 或 600000.SH
        ts_code = st.text_input("🎯 股票代码 (如: 000001.SZ)", value="000001.SZ")

        if st.session_state.generated_code:
            st.success("🟢 策略已就绪")
            if st.button("🚀 执行策略并标出买卖点", use_container_width=True, type="primary"):
                with st.spinner(f"正在通过 Tushare 获取 {ts_code} 数据..."):
                    try:
                        # 拉取最近一年的日线数据
                        df = pro.daily(ts_code=ts_code, start_date='20250101')
                        if df.empty:
                            st.error("未获取到数据，请检查代码格式是否正确 (需带后缀.SZ或.SH)")
                        else:
                            df = df.sort_values('trade_date').reset_index(drop=True)
                            # 数据清洗
                            df['trade_date'] = pd.to_datetime(df['trade_date'])

                            # 执行沙盒代码
                            local_vars = {}
                            exec(st.session_state.generated_code, globals(), local_vars)
                            df = local_vars['generate_signals'](df)

                            # 计算指标
                            df['Position'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
                            df['Strategy_Return'] = df['Position'].shift(1) * df['close'].pct_change()
                            df['Cum_Strategy'] = (1 + df['Strategy_Return'].fillna(0)).cumprod()

                            st.session_state.backtest_result = {"df": df, "code": ts_code}
                    except Exception as e:
                        st.error(f"执行失败: {e}")
        else:
            st.warning("👈 请先在战情室生成策略")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_chart:
        if st.session_state.backtest_result:
            res_df = st.session_state.backtest_result['df']
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)

            # Plotly K线图
            fig = go.Figure()
            fig.add_trace(
                go.Candlestick(x=res_df['trade_date'], open=res_df['open'], high=res_df['high'], low=res_df['low'],
                               close=res_df['close'], name='K线'))

            # 标注买卖点
            buys = res_df[res_df['Signal'] == 1]
            sells = res_df[res_df['Signal'] == -1]
            fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['low'] * 0.98, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='#00ff00'), name='买点'))
            fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['high'] * 1.02, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='#ff0000'), name='卖点'))

            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # 金融指标
            total_ret = (res_df['Cum_Strategy'].iloc[-1] - 1) * 100
            max_dd = ((res_df['Cum_Strategy'] / res_df['Cum_Strategy'].cummax() - 1).min()) * 100
            st.columns(3)[0].metric("累计收益", f"{total_ret:.2f}%")
            st.columns(3)[1].metric("最大回撤", f"{max_dd:.2f}%")
            st.columns(3)[2].metric("交易标的", st.session_state.backtest_result['code'])
            st.markdown('</div>', unsafe_allow_html=True)a