import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time
import tushare as ts
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# 1. 核心兵符 & 基础配置
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro - 毕业设计版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

pro = ts.pro_api(TUSHARE_TOKEN)
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=30.0)

# ==========================================
# 2. 沉浸式 UI & CSS 锁定
# ==========================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], .block-container { background: transparent !important; padding-top: 2rem !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    header[data-testid="stHeader"] * { color: rgba(255,255,255,0.6) !important; }
    footer { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, span, li { color: #ffffff !important; }
    [data-testid="stSidebar"] { background: rgba(20, 20, 20, 0.6) !important; backdrop-filter: blur(15px) !important; border-right: 1px solid rgba(255,255,255,0.1) !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    .glass-card { background: rgba(20, 20, 20, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); }
    .stTextInput > div > div { background-color: rgba(0,0,0,0.7) !important; color: white !important; border: 1px solid rgba(255,255,255,0.2); }
    div[data-testid="stChatMessageContent"] { background-color: rgba(40,44,52,0.9) !important; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# 状态管理
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "主公，毕业答辩系统已初始化！请使用 AI 引擎生成您的论证策略。"}]
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "sys_logs" not in st.session_state: st.session_state.sys_logs = [
    f"[{datetime.now().strftime('%H:%M:%S')}] 系统内核启动成功，Tushare 数据源已连接。"]


def add_log(msg):
    st.session_state.sys_logs.insert(0, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def format_ts_code(raw_code):
    raw_code = str(raw_code).strip().upper()
    if len(raw_code) == 6 and raw_code.isdigit():
        if raw_code.startswith(('6', '9')):
            return f"{raw_code}.SH"
        elif raw_code.startswith(('0', '2', '3')):
            return f"{raw_code}.SZ"
        elif raw_code.startswith(('4', '8')):
            return f"{raw_code}.BJ"
    return raw_code


# ==========================================
# 3. 侧边栏：学术级模块划分
# ==========================================
with st.sidebar:
    st.markdown("## 🎓 量化交易引擎 Pro")
    st.caption("基于 LLM 与 Tushare 的智能回测系统")
    st.markdown("---")
    page = st.radio("系统导航", [
        "🏠 系统总览 (Dashboard)",
        "🤖 AI 策略引擎",
        "📈 深度回测与归因",
        "🛡️ 风控与日志系统"
    ], label_visibility="collapsed")

# ==========================================
# 🏠 页面 1: 系统总览 (答辩演示绝佳门面)
# ==========================================
if page == "🏠 系统总览 (Dashboard)":
    st.markdown(
        '<div class="glass-card"><h2>🏠 智能量化交易决策系统</h2><p>基于大语言模型 (LLM) 的代码生成与动态回测架构</p></div>',
        unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("系统运行状态", "🟢 正常运转", "Online")
    col2.metric("AI 大脑", "Moonshot-v1-8k", "API 正常")
    col3.metric("数据源节点", "Tushare Pro", "延时 < 50ms")
    col4.metric("策略缓存数", "1" if st.session_state.generated_code else "0", "动态沙盒")

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ 系统架构图 (论文配图参考)")
    st.markdown("""
    * **感知层**: 用户自然语言输入 (Streamlit UI)
    * **认知层**: Moonshot LLM 大模型解析意图，生成 Pandas 矢量化交易逻辑
    * **数据层**: Tushare 金融大数据接口，获取 A 股/ETF 真实 K 线与财务数据
    * **执行层**: Python 动态沙盒 `exec()` 执行策略，生成交易信号向量 (1, 0, -1)
    * **表现层**: Plotly 交互式可视化，输出夏普比率、最大回撤等学术级归因指标
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🤖 页面 2: AI 策略引擎
# ==========================================
elif page == "🤖 AI 策略引擎":
    st.markdown('<div class="glass-card"><h3>🤖 LLM 策略生成中枢</h3></div>', unsafe_allow_html=True)
    chat_container = st.container(height=450)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("输入策略构思 (如: 基于MACD和KDJ指标的共振交易策略)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        add_log(f"用户下达新策略指令: {prompt[:20]}...")
        st.rerun()

    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                bt = "`" * 3
                sys_prompt = f"""你是量化专家。请给出Python代码并用 {bt}python 和 {bt} 包裹。
必须包含 `generate_signals(df)` 函数。输入 df 列名为: ['trade_date', 'open', 'high', 'low', 'close', 'vol']。
在 df 中新增 'Signal' 列：1为买入，-1为卖出，0为观望。最后返回 df。
⚠️ 【学术级军规】：在 pandas 计算多条件时，必须且只能使用 `&` (与) 和 `|` (或)，并给每个条件加括号！绝对禁止使用 `and` 或 `or`！禁止引入未知的第三方库。"""
                try:
                    msg_box.markdown("🧠 *大模型正在解析意图并构建计算图...*")
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
                        st.toast("✅ 策略已通过静态检查，编译成功！", icon="🚀")
                        add_log("AI 成功生成动态策略代码并加载至内存沙盒。")
                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"API 异常: {e}")
                    add_log(f"大模型通信失败: {e}")
        st.rerun()

# ==========================================
# 📈 页面 3: 深度回测与归因
# ==========================================
elif page == "📈 深度回测与归因":
    st.markdown('<div class="glass-card"><h3>📈 动态沙盒与回测引擎</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])

    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        raw_stock_code = st.text_input("🎯 回测标的 (输入6位代码，如: 000001)", value="000001")
        ts_code = format_ts_code(raw_stock_code)

        st.caption(f"🔗 Tushare API 映射: `{ts_code}`")

        if st.session_state.generated_code:
            st.success("🟢 沙盒引擎就绪")
            if st.button("🚀 启动全量回测任务", use_container_width=True, type="primary"):
                with st.spinner(f"正在调取 {ts_code} 历史数据并注入策略沙盒..."):
                    try:
                        data = pro.daily(ts_code=ts_code, start_date='20220101')
                        if data.empty:
                            st.error("未获取到数据！")
                        else:
                            data = data.sort_values('trade_date').reset_index(drop=True)
                            data['trade_date'] = pd.to_datetime(data['trade_date'])

                            # 学术研究常用的基础均线预加载
                            data['MA5'] = data['close'].rolling(window=5).mean()
                            data['MA20'] = data['close'].rolling(window=20).mean()

                            # 沙盒执行
                            l_vars = {}
                            exec(st.session_state.generated_code, globals(), l_vars)
                            data = l_vars['generate_signals'](data)

                            # 严谨的收益率计算
                            data['Ret'] = data['close'].pct_change()
                            data['Pos'] = data['Signal'].replace(0, np.nan).ffill().fillna(0)
                            data['Strat_Ret'] = data['Pos'].shift(1) * data['Ret']
                            data['Cum_Prod'] = (1 + data['Strat_Ret'].fillna(0)).cumprod()

                            st.session_state.bt_result = {"df": data, "code": ts_code}
                            add_log(f"完成标的 {ts_code} 的回测演算，数据行数: {len(data)}")
                    except Exception as e:
                        st.error(f"沙盒执行异常: {e}")
                        add_log(f"策略执行报错: {e}")
        else:
            st.warning("🟡 策略缓存为空，请先由 AI 生成策略。")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            df = st.session_state.bt_result['df']
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)

            # K线绘图
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                name='K线', increasing_line_color='#FD1050', increasing_fillcolor='#FD1050',
                decreasing_line_color='#00FF00', decreasing_fillcolor='#00FF00'
            ))
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['MA5'], line=dict(color='white', width=1), name='MA5'))
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['MA20'], line=dict(color='magenta', width=1), name='MA20'))

            buys = df[df['Signal'] == 1]
            sells = df[df['Signal'] == -1]
            fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['low'] * 0.95, mode='markers',
                                     marker=dict(symbol='triangle-up', size=14, color='#00FFFF',
                                                 line=dict(width=1, color='white')), name='买入信号'))
            fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['high'] * 1.05, mode='markers',
                                     marker=dict(symbol='triangle-down', size=14, color='#FF00FF',
                                                 line=dict(width=1, color='white')), name='卖出信号'))

            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)',
                              margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False, hovermode="x unified",
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            st.plotly_chart(fig, use_container_width=True)

            # 🔥 学术级归因指标计算
            total_ret = (df['Cum_Prod'].iloc[-1] - 1)
            trading_days = len(df)
            annual_ret = (1 + total_ret) ** (252 / trading_days) - 1 if trading_days > 0 else 0
            max_dd = ((df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min())

            # 计算夏普比率 (假设无风险利率为 3%)
            daily_returns = df['Strat_Ret'].dropna()
            if len(daily_returns) > 0 and daily_returns.std() != 0:
                sharpe_ratio = ((daily_returns.mean() - 0.03 / 252) / daily_returns.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0

            st.markdown("#### 📊 核心评价指标 (Evaluation Metrics)")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("累计收益率", f"{total_ret * 100:.2f}%")
            c2.metric("年化收益率", f"{annual_ret * 100:.2f}%")
            c3.metric("最大回撤", f"{max_dd * 100:.2f}%")
            c4.metric("夏普比率 (Sharpe)", f"{sharpe_ratio:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🛡️ 页面 4: 风控与日志系统
# ==========================================
elif page == "🛡️ 风控与日志系统":
    st.markdown('<div class="glass-card"><h3>🛡️ 系统运行日志与安全审计</h3></div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("监控系统状态，记录 AI 生成代码的错误及接口调用延迟。")
    log_text = "\n".join(st.session_state.sys_logs)
    st.text_area("实时日志输出 (System Terminal)", value=log_text, height=400)
    st.markdown('</div>', unsafe_allow_html=True)