import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time
import tushare as ts
import plotly.graph_objects as go

# ==========================================
# 1. 核心兵符 (Kimi & Tushare)
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

pro = ts.pro_api(TUSHARE_TOKEN)
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=30.0)

# ==========================================
# 2. 沉浸式 UI
# ==========================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], .block-container { background: transparent !important; padding-top: 2rem !important; }
    header[data-testid="stHeader"], footer { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, span { color: #ffffff !important; }
    [data-testid="stSidebar"] { background: rgba(20, 20, 20, 0.6) !important; backdrop-filter: blur(15px) !important; border-right: 1px solid rgba(255,255,255,0.1) !important; }
    .glass-card { background: rgba(20, 20, 20, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 20px; }
    .stTextInput > div > div { background-color: rgba(0,0,0,0.7) !important; color: white !important; }
    div[data-testid="stChatMessageContent"] { background-color: rgba(40,44,52,0.9) !important; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，真·回测沙盘已加载！请于战情室下达策略指令。"}]
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "bt_result" not in st.session_state: st.session_state.bt_result = None

with st.sidebar:
    st.markdown("## 👑 小吕布量化")
    st.markdown("---")
    page = st.radio("导航菜单", ["🤖 AI 战情室", "📊 实盘战场", "⚡ 深度回测"], label_visibility="collapsed")

# ==========================================
# 🤖 AI 战情室
# ==========================================
if page == "🤖 AI 战情室":
    st.markdown('<div class="glass-card"><h3>🤖 AI 战情室</h3></div>', unsafe_allow_html=True)
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("请下令生成策略 (如: 写一个基于双均线的策略)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                bt = "`" * 3
                # 🔥 强化版提示词：加入了防止 pandas ambiguous 报错的严格军规
                sys_prompt = f"""你是量化专家。请给出Python代码并用 {bt}python 和 {bt} 包裹。
必须包含 `generate_signals(df)` 函数。
输入 df 列名为: ['trade_date', 'open', 'high', 'low', 'close', 'vol']。
在 df 中新增 'Signal' 列：1为买入，-1为卖出，0为观望。最后返回 df。
⚠️ 【极度重要军规】：
1. 在 pandas 计算多条件时，必须且只能使用 `&` (与) 和 `|` (或)，并给每个条件加括号！绝对禁止使用 `and` 或 `or`！
2. 请使用 `.shift(1)` 引用前一日数据，避免用到未来函数。"""
                try:
                    msg_box.markdown("🧠 *军师正在推演战术逻辑...*")
                    stream = client.chat.completions.create(model="moonshot-v1-8k", messages=[{"role": "system",
                                                                                               "content": sys_prompt}] + st.session_state.messages,
                                                            stream=True)
                    full_resp = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_resp += chunk.choices[0].delta.content
                            msg_box.markdown(full_resp + "▌")
                    msg_box.markdown(full_resp)

                    code_match = re.search(bt + r"(?:python)?\s*(.*?)" + bt, full_resp, re.DOTALL | re.IGNORECASE)
                    if code_match:
                        st.session_state.generated_code = code_match.group(1).strip()
                        st.toast("✅ 战术代码已装填！", icon="🚀")
                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"API 异常: {e}")
        st.rerun()

# ==========================================
# 📊 实盘战场
# ==========================================
elif page == "📊 实盘战场":
    st.markdown('<div class="glass-card"><h3>📊 实盘战场 (沙盒回测)</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])

    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        ts_code = st.text_input("🎯 股票代码 (如: 000001.SZ)", value="000001.SZ")

        if st.session_state.generated_code:
            st.success("🟢 策略已装填")
            if st.button("🚀 执行策略并研判买卖点", use_container_width=True, type="primary"):
                with st.spinner(f"正在调取 {ts_code} 真实历史战况..."):
                    try:
                        data = pro.daily(ts_code=ts_code, start_date='20240101')
                        if data.empty:
                            st.error("未获取到数据，请检查代码。")
                        else:
                            data = data.sort_values('trade_date').reset_index(drop=True)
                            data['trade_date'] = pd.to_datetime(data['trade_date'])

                            l_vars = {}
                            exec(st.session_state.generated_code, globals(), l_vars)
                            data = l_vars['generate_signals'](data)

                            data['Ret'] = data['close'].pct_change()
                            data['Pos'] = data['Signal'].replace(0, np.nan).ffill().fillna(0)
                            data['Strat_Ret'] = data['Pos'].shift(1) * data['Ret']
                            data['Cum_Prod'] = (1 + data['Strat_Ret'].fillna(0)).cumprod()

                            st.session_state.bt_result = {"df": data, "code": ts_code}
                    except Exception as e:
                        st.error(f"逻辑错误: {e}")
        else:
            st.warning("🟡 暂无策略，请前往战情室。")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            df = st.session_state.bt_result['df']
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)

            fig = go.Figure(data=[
                go.Candlestick(x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                               name='K线')])

            buys = df[df['Signal'] == 1]
            sells = df[df['Signal'] == -1]
            fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['low'] * 0.98, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='#00ff00'), name='买入点'))
            fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['high'] * 1.02, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='#ff0000'), name='卖出点'))

            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            total_ret = (df['Cum_Prod'].iloc[-1] - 1) * 100
            max_dd = ((df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min()) * 100
            win_days = len(df[df['Strat_Ret'] > 0])
            trade_days = len(df[df['Strat_Ret'] != 0])
            win_rate = (win_days / trade_days * 100) if trade_days > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("累计收益率", f"{total_ret:.2f}%")
            c2.metric("最大回撤", f"{max_dd:.2f}%")
            c3.metric("模拟胜率", f"{win_rate:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)

elif page == "⚡ 深度回测":
    st.markdown('<div class="glass-card"><h3>🚧 深度引擎正在校准中...</h3></div>', unsafe_allow_html=True)