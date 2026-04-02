import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time
import tushare as ts
import plotly.graph_objects as go

# ==========================================
# 1. 核心配置与兵符装填
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro", layout="wide", initial_sidebar_state="expanded")

# 🛑 绝密兵符
KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

# 初始化数据接口
pro = ts.pro_api(TUSHARE_TOKEN)
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=30.0)

# ==========================================
# 2. 注入沉浸式 CSS
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

# 初始化内存
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，真·实盘回测沙盘已加载！请于战情室下达策略指令。"}]
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "bt_result" not in st.session_state: st.session_state.bt_result = None

# ==========================================
# 3. 导航与侧边栏
# ==========================================
with st.sidebar:
    st.markdown("## 👑 小吕布量化 Pro")
    st.markdown("---")
    page = st.radio("系统导航", ["🤖 AI 战情室", "📊 实盘战场", "⚡ 深度回测"], label_visibility="collapsed")

# ==========================================
# 🤖 AI 战情室 (策略生成)
# ==========================================
if page == "🤖 AI 战情室":
    st.markdown('<div class="glass-card"><h3>🤖 AI 战情室 (Kimi × Tushare)</h3></div>', unsafe_allow_html=True)
    chat_container = st.container(height=500)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("主公请下令 (例如: 写一个双均线策略，10日和30日)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                msg_box.markdown("🧠 *军师正在推演战术逻辑...*")
                bt = "`" * 3
                sys_prompt = f"""你是量化专家。请给出Python代码并用 {bt}python 和 {bt} 包裹。
必须包含 `generate_signals(df)` 函数。
输入 df 列名为: ['trade_date', 'open', 'high', 'low', 'close', 'vol']。
在 df 中新增 'Signal' 列：1为买入点，-1为卖出点，0为观望。
最后返回整个 df。"""
                try:
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
                        st.toast("✅ 策略已同步至战场！", icon="🚀")
                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"通讯异常: {e}")
        st.rerun()

# ==========================================
# 📊 实盘战场 (执行与 K线可视化)
# ==========================================
elif page == "📊 实盘战场":
    st.markdown('<div class="glass-card"><h3>📊 实盘战场 (Tushare 数据源)</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])

    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        ts_code = st.text_input("🎯 股票代码 (如: 000001.SZ)", value="000001.SZ")

        if st.session_state.generated_code:
            st.success("🟢 策略指令已装填")
            if st.button("🚀 执行策略并研判买卖点", use_container_width=True, type="primary"):
                with st.spinner(f"正在调取 {ts_code} 历史战况..."):
                    try:
                        # 1. 抓取数据 (从2024年至今)
                        data = pro.daily(ts_code=ts_code, start_date='20240101')
                        if data.empty:
                            st.error("未获取到数据，请检查代码后缀。")
                        else:
                            data = data.sort_values('trade_date').reset_index(drop=True)
                            data['trade_date'] = pd.to_datetime(data['trade_date'])

                            # 2. 运行沙盒执行 AI 代码
                            l_vars = {}
                            exec(st.session_state.generated_code, globals(), l_vars)
                            data = l_vars['generate_signals'](data)

                            # 3. 计算金融分析指标
                            data['Ret'] = data['close'].pct_change()
                            # 简单模拟持仓逻辑
                            data['Pos'] = data['Signal'].replace(0, np.nan).ffill().fillna(0)
                            data['Strat_Ret'] = data['Pos'].shift(1) * data['Ret']
                            data['Cum_Prod'] = (1 + data['Strat_Ret'].fillna(0)).cumprod()

                            st.session_state.bt_result = {"df": data, "code": ts_code}
                    except Exception as e:
                        st.error(f"执行报错: {e}")
        else:
            st.warning("🟡 暂无策略。请先前往战情室。")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            df = st.session_state.bt_result['df']
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)

            # 🔥 绘制交互式 K 线图
            fig = go.Figure(data=[
                go.Candlestick(x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                               name='K线')])

            # 标注买入和卖出点
            buys = df[df['Signal'] == 1]
            sells = df[df['Signal'] == -1]
            fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['low'] * 0.98, mode='markers',
                                     marker=dict(symbol='triangle-up', size=12, color='#00ff00'), name='买入点'))
            fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['high'] * 1.02, mode='markers',
                                     marker=dict(symbol='triangle-down', size=12, color='#ff0000'), name='卖出点'))

            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # 指标面板 (胜率、最大回撤等)
            total_ret = (df['Cum_Prod'].iloc[-1] - 1) * 100
            max_dd = ((df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min()) * 100
            # 简单胜率计算：盈利交易日占比
            win_rate = (len(df[df['Strat_Ret'] > 0]) / len(df[df['Strat_Ret'] != 0]) * 100) if len(
                df[df['Strat_Ret'] != 0]) > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("累计收益率", f"{total_ret:.2f}%")
            c2.metric("最大回撤", f"{max_drawdown:.2f}%" if 'max_drawdown' in locals() else f"{max_dd:.2f}%")
            c3.metric("模拟胜率", f"{win_rate:.2f}%")
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 4. 深度回测
# ==========================================
elif page == "⚡ 深度回测":
    st.markdown('<div class="glass-card"><h3>🚧 深度回测引擎扩建中...</h3></div>', unsafe_allow_html=True)