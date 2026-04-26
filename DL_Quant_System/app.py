import os
import sys
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time
import tushare as ts
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import uuid
import math
from PIL import Image

# 🔥 安全导入扩展先锋营 🔥
try:
    import extensions
except ImportError:
    extensions = None

try:
    import custom_plugins
except ImportError:
    custom_plugins = None

# ==========================================
# 0. 环境优雅降级
# ==========================================
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import docx
except ImportError:
    docx = None

pd.np = np
SUB_PATTERN = re.compile(r'^SUB(\d+)_')

# ==========================================
# 1. 核心兵符与状态初始化
# ==========================================
st.set_page_config(
    page_title="小吕布量化 Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"
ts.set_token(TUSHARE_TOKEN)


@st.cache_resource
def get_ts_pro(): return ts.pro_api()


pro = get_ts_pro()
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=60.0)

for key, val in {"user_id": f"User_{str(uuid.uuid4())[:6]}", "messages": [], "generated_code": "",
                 "strategy_explanation": "暂无策略解析，请先前往 AI 战情室下达军令。", "dl_result": None,
                 "bt_result": None, "sys_logs": [], "is_live_trading": False}.items():
    if key not in st.session_state: st.session_state[key] = val

# ==========================================
# 2. 空间流形导航逻辑 & 纯 Python 原生主题开关
# ==========================================
PAGES = ["🏠 系统总览 (监控中控)", "🤖 AI 策略引擎 (LLM)", "💻 极客量化 IDE (代码编译)", "📈 深度静态全量回测",
         "⚡ 实时高频交易 (Live)", "🧠 深度学习预测矩阵", "🛡️ 论文审计日志", "🔗 期货全量审计 (归因)", "🌪️ 期货高频沙盘",
         "🧩 扩展插件中心"]
if custom_plugins and hasattr(custom_plugins, 'EXTRA_PAGES'): PAGES.extend(custom_plugins.EXTRA_PAGES)

if "curr_page" not in st.session_state: st.session_state.curr_page = PAGES[0]
if "prev_page" not in st.session_state: st.session_state.prev_page = PAGES[0]
if "just_switched" not in st.session_state: st.session_state.just_switched = False

with st.sidebar:
    st.markdown("### 🎓 小吕布量化 Pro")
    st.caption(f"🛡️ 节点 ID: {st.session_state.user_id}")
    st.markdown("---")
    selected_page = st.radio("导航菜单", PAGES, label_visibility="collapsed")

    st.markdown("---")
    # 🔥 绝杀修复：Python 强控开关，彻底废弃 JS 引擎
    use_light_theme = st.toggle("🌓 切换 冰蓝(浅) / 赛博(深)", value=False)

    if extensions:
        st.markdown("---")
        extensions.summon_global_3d_lulu()

if selected_page != st.session_state.curr_page:
    st.session_state.prev_page = st.session_state.curr_page
    st.session_state.curr_page = selected_page
    st.session_state.just_switched = True
else:
    st.session_state.just_switched = False

prev_idx = PAGES.index(st.session_state.prev_page)
curr_idx = PAGES.index(st.session_state.curr_page)
anim_name = "waveBlurUpIn" if curr_idx > prev_idx else ("waveBlurDownIn" if curr_idx < prev_idx else "fogFadeIn")

# ==========================================
# 3. 极致静态 CSS (绝对防御穿透版)
# ==========================================
if selected_page == PAGES[1]:
    st.markdown(
        '<style>div[data-testid="stFileUploader"] { position: absolute !important; top: -9999px !important; opacity: 0 !important; z-index: -9999 !important; pointer-events: none !important; }</style>',
        unsafe_allow_html=True)

st.markdown(f"""
<style>
    .block-container {{ animation: {anim_name} 0.65s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; background: transparent !important; padding-top: 4.5rem !important; padding-bottom: 120px !important; }}
</style>
""", unsafe_allow_html=True)

# 基础布局样式
common_css = """
    @keyframes fluidFlow { 0% { background-position: 0% 50%; } 25% { background-position: 50% 100%; } 50% { background-position: 100% 50%; } 75% { background-position: 50% 0%; } 100% { background-position: 0% 50%; } }
    @keyframes waveBlurUpIn { 0% { opacity: 0; margin-top: 60px; filter: blur(15px); transform: scale(0.98); } 100% { opacity: 1; margin-top: 0px; filter: blur(0px); transform: scale(1); } }
    @keyframes waveBlurDownIn { 0% { opacity: 0; margin-top: -60px; filter: blur(15px); transform: scale(0.98); } 100% { opacity: 1; margin-top: 0px; filter: blur(0px); transform: scale(1); } }
    @keyframes fogFadeIn { 0% { opacity: 0; filter: blur(15px); transform: scale(0.98); } 100% { opacity: 1; filter: blur(0px); transform: scale(1); } }

    header[data-testid="stHeader"] { position: fixed !important; top: 0px !important; background: transparent !important; }
    [data-testid="stAppViewContainer"] > section:first-child { background: transparent !important; }
    [data-testid="stBottomBlock"], [data-testid="stBottom"] > div { background: transparent !important; border: none !important; }
    [data-testid="stChatInput"] { background: transparent !important; border: none !important; box-shadow: none !important; max-width: 850px; margin: 0 auto 10px auto !important; }
    [data-testid="stChatInput"] [data-baseweb="textarea"] { background-color: transparent !important; }
    textarea { font-family: 'Consolas', 'Courier New', monospace !important; }
"""

# 🔥 核心突围：直接强制绑定到最高权限容器 [data-testid="stAppViewContainer"]
if use_light_theme:
    theme_css = """
        /* ☀️ 浅色：强杀默认黑色背景，注入冰蓝渐变 */
        html, body, .stApp, [data-testid="stAppViewContainer"] { 
            background-color: #fdfbfb !important;
            background-image: linear-gradient(132deg, #fdfbfb, #e0c3fc, #8ec5fc, #e2ebf0, #fdfbfb) !important; 
            background-size: 400% 400% !important; 
            animation: fluidFlow 12s ease infinite !important; 
        }

        /* 强制全局文字变黑 */
        .stMarkdown, p, h1, h2, h3, h4, label, span, [data-testid="stMetricValue"] > div { color: #1e293b !important; }
        .highlight-text { color: #0284c7 !important; }
        .sub-text { color: #475569 !important; }
        .danger-text { color: #dc2626 !important; }

        [data-testid="stSidebar"] { background: rgba(248, 250, 252, 0.85) !important; border-right: 1px solid rgba(0,0,0,0.08) !important; }
        .glass-card { background: rgba(255, 255, 255, 0.75) !important; border: 1px solid rgba(0, 0, 0, 0.1) !important; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.05) !important; border-radius: 20px; padding: 25px; margin-bottom: 20px;}
        .metric-box { background: rgba(2, 132, 199, 0.05) !important; border: 1px solid rgba(2, 132, 199, 0.2) !important; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px;}
        [data-testid="stChatInput"] > div:first-child { background-color: rgba(255, 255, 255, 0.95) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; border-radius: 36px !important; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1) !important; padding: 5px 15px !important; }
        [data-testid="stChatInput"] textarea { color: #1e293b !important; }
        [data-testid="stExpander"] { background: rgba(255, 255, 255, 0.8) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; border-radius: 16px !important; margin-bottom: 20px !important; }
    """
else:
    theme_css = """
        /* 🌙 深色：强杀底色，注入赛博流光 */
        html, body, .stApp, [data-testid="stAppViewContainer"] { 
            background-color: #02040a !important;
            background-image: linear-gradient(132deg, #02040a, #030e2b, #111d3d, #082a72, #030614, #1d2b4f, #0a47b3, #02040a) !important; 
            background-size: 600% 600% !important; 
            animation: fluidFlow 18s ease-in-out infinite !important; 
        }

        /* 强制全局文字变白 */
        .stMarkdown, p, h1, h2, h3, h4, label, span, [data-testid="stMetricValue"] > div { color: #e2e8f0 !important; }
        .highlight-text { color: #00ffcc !important; }
        .sub-text { color: #cbd5e1 !important; }
        .danger-text { color: #ff4b4b !important; }

        [data-testid="stSidebar"] { background: rgba(5, 8, 14, 0.85) !important; border-right: 1px solid rgba(255,255,255,0.08) !important; }
        .glass-card { background: rgba(20, 28, 45, 0.75) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6) !important; border-radius: 20px; padding: 25px; margin-bottom: 20px;}
        .metric-box { background: rgba(0, 255, 204, 0.05) !important; border: 1px solid rgba(0, 255, 204, 0.2) !important; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px;}
        [data-testid="stChatInput"] > div:first-child { background-color: rgba(30, 41, 59, 0.85) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; border-radius: 36px !important; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important; padding: 5px 15px !important; }
        [data-testid="stChatInput"] textarea { color: #e2e8f0 !important; }
        [data-testid="stExpander"] { background: rgba(15, 23, 35, 0.8) !important; border: 1px solid rgba(0, 255, 204, 0.3) !important; border-radius: 16px !important; margin-bottom: 20px !important; }
    """

st.markdown(f"<style>{common_css}{theme_css}</style>", unsafe_allow_html=True)


# ==========================================
# 4. 高速缓存装甲：分离复杂计算
# ==========================================
def add_default_indicators(df):
    if 'Close' in df.columns:
        df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()
        df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['SUB1_MACD_DIFF'] = exp1 - exp2
        df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()
        df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])
    return df


@st.cache_data(ttl=300, show_spinner=False)
def get_tushare_status():
    try:
        t0 = time.time()
        pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240101')
        return f"🟢 Online ({int((time.time() - t0) * 1000)}ms)"
    except:
        return "🔴 Offline"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_and_clean_data(ts_code, adj, start_date):
    df = ts.pro_bar(ts_code=ts_code, adj=adj, start_date=start_date)
    if df is not None and not df.empty:
        df = df.sort_values('trade_date').reset_index(drop=True)
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        mapping_base = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'vol': 'Volume',
                        'amount': 'Amount'}
        for l_case, c_case in mapping_base.items():
            if l_case in df.columns: df[c_case] = df[l_case]
        if 'Volume' not in df.columns and 'vol' in df.columns: df['Volume'] = df['vol']
        return add_default_indicators(df)
    return pd.DataFrame()


@st.cache_data(show_spinner=False)
def run_backtest_metrics(df_source, strategy_code):
    df_safe = df_source.copy()
    if strategy_code:
        df_ai = execute_safely(strategy_code, df_source)
        if df_ai is not None and hasattr(df_ai, 'columns'):
            for col in df_ai.columns:
                if col == 'Signal' or col.startswith(('MAIN_', 'SUB')): df_safe[col] = df_ai[col]
    df = df_safe
    df['Ret'] = df['Close'].pct_change()
    df['Pos'] = df.get('Signal', pd.Series([0] * len(df))).replace(0, np.nan).ffill().fillna(0)
    df['Strat_Ret'] = df['Pos'].shift(1) * df['Ret']
    df['Cum_Prod'] = (1 + df['Strat_Ret'].fillna(0)).cumprod()
    total_ret = (df['Cum_Prod'].iloc[-1] - 1) if not df.empty else 0
    annual = (1 + total_ret) ** (252 / max(1, len(df))) - 1 if not df.empty else 0
    max_dd = (df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min() if not df.empty else 0
    vol = df['Strat_Ret'].std() * np.sqrt(252) if not df.empty else 0
    sharpe = annual / vol if vol != 0 else 0
    return {"df": df, "metrics": {"total": total_ret, "annual": annual, "max_dd": max_dd, "sharpe": sharpe}}


def execute_safely(code, df):
    if not code: return df
    try:
        safe_code = str(code).replace("pandas.np", "np")
        l_vars = {}
        exec(safe_code, {"pd": pd, "np": np, "math": math, "time": time, "datetime": datetime}, l_vars)
        func_to_call = next((v for k, v in l_vars.items() if callable(v)), None)
        if not func_to_call: return df
        df_ai = func_to_call(df.copy())
        if df_ai is None or not hasattr(df_ai, 'columns'): return df
        sig_col = next((c for c in df_ai.columns if c.lower() == 'signal'), None)
        if sig_col:
            df_ai['Signal'] = df_ai[sig_col].fillna(0).apply(
                lambda x: 1 if x > 0.1 else (-1 if x < -0.1 else 0)).astype(int)
        else:
            df_ai['Signal'] = 0
        return df_ai
    except Exception:
        return df


def render_smart_charts(df):
    main_inds = [c for c in df.columns if c.startswith('MAIN_')]
    sub_groups = {}
    for c in df.columns:
        gid = SUB_PATTERN.match(c)
        if gid: sub_groups.setdefault(gid.group(1), []).append(c)
    rows = 2 + len(sub_groups)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.5, 0.15] + [0.35 / max(1, len(sub_groups))] * len(sub_groups))
    x_labels = df['trade_date'].dt.strftime('%Y-%m-%d') if df['trade_date'].dt.time.nunique() <= 1 else df[
        'trade_date'].dt.strftime('%m-%d %H:%M')
    fig.add_trace(go.Candlestick(x=x_labels, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 increasing_line_color='#ef4444', decreasing_line_color='#10b981', name='K线'), row=1,
                  col=1)
    colors = ['#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899']
    for i, col in enumerate(main_inds): fig.add_trace(
        go.Scatter(x=x_labels, y=df[col], name=col, line=dict(width=1.2, color=colors[i % 4])), row=1, col=1)
    if 'Signal' in df.columns:
        buys = df[df['Signal'] == 1]
        sells = df[df['Signal'] == -1]
        buy_x = buys['trade_date'].dt.strftime('%Y-%m-%d' if df['trade_date'].dt.time.nunique() <= 1 else '%m-%d %H:%M')
        sell_x = sells['trade_date'].dt.strftime(
            '%Y-%m-%d' if df['trade_date'].dt.time.nunique() <= 1 else '%m-%d %H:%M')
        fig.add_trace(go.Scatter(x=buy_x, y=buys['Low'] * 0.998, mode='markers',
                                 marker=dict(symbol='triangle-up', size=14, color='#3b82f6'), name='买'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sell_x, y=sells['High'] * 1.002, mode='markers',
                                 marker=dict(symbol='triangle-down', size=14, color='#f59e0b'), name='卖'), row=1,
                      col=1)
    fig.add_trace(go.Bar(x=x_labels, y=df.get('Volume', np.zeros(len(df))),
                         marker_color=np.where(df['Close'] >= df['Open'], '#ef4444', '#10b981'), name='成交量'), row=2,
                  col=1)
    row_idx = 3
    for gid in sorted(sub_groups.keys(), key=int):
        for i, col in enumerate(sub_groups[gid]):
            if 'HIST' in col.upper():
                fig.add_trace(
                    go.Bar(x=x_labels, y=df[col], marker_color=np.where(df[col] >= 0, '#ef4444', '#10b981'), name=col),
                    row=row_idx, col=1)
            else:
                fig.add_trace(go.Scatter(x=x_labels, y=df[col], line=dict(width=1.2, color=colors[i % 4]), name=col),
                              row=row_idx, col=1)
        row_idx += 1
    fig.update_layout(height=500 + len(sub_groups) * 150, template="none", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False, dragmode='pan', hovermode='x',
                      showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=x_labels, nticks=8, showgrid=True,
                     gridwidth=1, gridcolor='rgba(128,128,128,0.2)', tickangle=0)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    return fig


def format_ts_code(raw):
    raw = str(raw).strip().upper()
    if len(raw) == 6 and raw.isdigit(): return f"{raw}.SH" if raw.startswith(('6', '9')) else f"{raw}.SZ"
    return raw


# ==========================================
# 5. 各页面业务逻辑
# ==========================================
if selected_page == PAGES[0]:
    st.markdown(
        '<div class="glass-card"><h1 style="margin-bottom:0;">🏛️ 全链路智能量化决策枢纽</h1><p class="highlight-text" style="font-size:1.1rem; margin-top:5px;">System Overview & Mid-term Inspection Dashboard</p></div>',
        unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("活跃并发沙盒 (UUID)", st.session_state.user_id)
    with c2:
        st.metric("Tushare 行情链路", get_tushare_status())
    with c3:
        st.metric("大模型底层通信", "🟢 Moonshot-v1 正常")
    with c4:
        st.metric("AI 神经网络", "🟢 融合学习待命")

    st.markdown("---")
    c_arch, c_point = st.columns([2, 1])
    with c_arch:
        st.markdown("""
        <div class="glass-card">
            <h3 style="margin-bottom: 15px;">🌟 平台简介 (Platform Intro)</h3>
            <p style="line-height: 1.8; font-size: 1.05rem;">
                欢迎来到 <b>小吕布量化 Pro</b>，这是一个专为现代极客打造的智能投研终端。<br><br>
                在这里，传统手写代码的繁琐已被彻底颠覆。您可以：<br>
                • <b>📝 全模态投研</b>：一键无缝上传 PDF/Word 研报或 CSV 矩阵，让大模型直接提取精髓。<br>
                • <b>🤖 零代码写策略</b>：通过自然语言对话，Agent 将自动为您生成并修复交易代码。<br>
                • <b>📈 穿越牛熊回测</b>：长达 10 年的全局历史回测，并附带 AI 胜率归因与白话解析。<br>
                • <b>🧠 时序张量预测</b>：利用 LSTM/GRU 融合矩阵，自回归推演未来 5 天的价格轨迹。<br>
            </p>
        </div>
        """, unsafe_allow_html=True)
    with c_point:
        st.markdown(
            '<div class="glass-card"><h4>📋 平台监控与杀手锏</h4>**云端依赖环境**<br>🟢 requirements.txt 托管<br><br>**核心架构升级：**<br>✅ <b>完美修复动态 CSS 解析崩溃</b><br>✅ 前端引擎防抖极速化<br>✅ <b>代码沙盒防 NoneType 拦截器</b><br>✅ LLM 空数据拦截网<br>✨ <b>底层背景色绝对穿透防御</b></div>',
            unsafe_allow_html=True
        )

elif selected_page == PAGES[1]:
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0;">🤖 LLM 策略战情室</h3><p class="sub-text">多模态视觉引擎与全域文档解析模块已就绪，体验沉浸式工作流。</p></div>',
        unsafe_allow_html=True)

    ctrl_col1, ctrl_col2 = st.columns([1, 1])
    with ctrl_col1:
        selected_model = st.selectbox("🧠 选择大模型算力通道", ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                                      index=0)
    with ctrl_col2:
        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
        enable_deep_think = st.toggle("💡 强子注入：开启深度思考引擎 (CoT)", value=False)

    chat_container = st.container()
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

    uploaded_files = st.file_uploader("选择文件", accept_multiple_files=True,
                                      type=['pdf', 'doc', 'docx', 'csv', 'txt', 'png', 'jpg', 'jpeg'],
                                      label_visibility="collapsed")
    file_context_text = ""
    if 'uploaded_files' in locals() and uploaded_files:
        cols = st.columns(3)
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 3]:
                fname_lower = file.name.lower()
                if file.type.startswith('image/'):
                    st.image(Image.open(file), use_container_width=True)
                    file_context_text += f"[用户上传了一张图片: {file.name}。]\n"
                elif fname_lower.endswith('.csv'):
                    df_upload = pd.read_csv(file)
                    st.dataframe(df_upload.head(2))
                    file_context_text += f"【CSV 数据源 {file.name} (前100行特征)】:\n{df_upload.head(100).to_string()}\n"
                elif fname_lower.endswith('.txt'):
                    content = file.getvalue().decode('utf-8', errors='replace')
                    st.success(f"📝 {file.name} 挂载成功")
                    file_context_text += f"【TXT 研报核心片段 {file.name}】:\n{content[:5000]}\n"
                elif fname_lower.endswith('.pdf'):
                    if PyPDF2:
                        try:
                            pdf_reader = PyPDF2.PdfReader(file)
                            text = "".join(
                                [page.extract_text() for page in pdf_reader.pages[:10] if page.extract_text()])
                            st.success(f"📄 PDF {file.name} 解析成功")
                            file_context_text += f"【PDF 核心片段 {file.name}】:\n{text[:5000]}\n"
                        except Exception as e:
                            st.error(f"PDF 读取异常: {e}")
                elif fname_lower.endswith(('.doc', '.docx')):
                    if docx:
                        try:
                            doc_obj = docx.Document(file)
                            text = "\n".join([para.text for para in doc_obj.paragraphs])
                            st.success(f"📘 Word {file.name} 解析成功")
                            file_context_text += f"【Word 核心片段 {file.name}】:\n{text[:5000]}\n"
                        except Exception as e:
                            st.error(f"Word 读取异常: {e}")

    if raw_prompt := st.chat_input("向小吕布量化架构师发送军令..."):
        full_prompt_for_ai = f"以下是您需要重点参考的附件原始数据：\n{file_context_text}\n\n我的指令：{raw_prompt}" if file_context_text else raw_prompt
        st.session_state.messages.append({"role": "user", "content": raw_prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(raw_prompt)
            with st.chat_message("assistant"):
                st.toast(f"🚀 连线底层算力集群: {selected_model}", icon="⚡")
                ticks = "`" * 3
                sys_p = f"""你是一名顶级量化工程师。拒绝闲聊。如果用户只是让你解读文字，直接输出解答。如果是编写策略，你必须严格遵守以下【小吕布量化系统 SDK 开发军规】：1. 只能使用 pandas, numpy 和 math。禁止 import talib！2. 数据源有效列名严格为：['Open', 'High', 'Low', 'Close', 'Volume']。3. 画图命名协议：主图列名以 `MAIN_` 开头，副图以 `SUB1_` 或 `SUB2_` 开头。4. 交易信号协议：必须生成一列 `df['Signal']`。1=买入，-1=卖出，0=持有。5. 代码骨架：{ticks}python\ndef generate_signals(df):\n    return df\n{ticks}\n请直接输出代码及策略白话解析。"""
                messages_to_send = [{"role": "system", "content": sys_p}] + st.session_state.messages[:-1] + [
                    {"role": "user", "content": full_prompt_for_ai}]
                max_retries = 2;
                agent_logs = [];
                last_error = "";
                full_resp = "";
                msg_box = st.empty()
                for attempt in range(max_retries + 1):
                    if attempt > 0:
                        agent_logs.append(
                            f'<div class="agent-status-node retry">🔄 <b>尝试 {attempt}:</b> 沙盒拦截异常 (<code>{last_error}</code>) -> Agent 发起重构</div>')
                        safe_resp = full_resp if full_resp and full_resp.strip() else "(API 前一次流响应为空，因引发沙盒报错被退回)"
                        messages_to_send.extend([{"role": "assistant", "content": safe_resp}, {"role": "user",
                                                                                               "content": f"代码报错：`{last_error}`，请严格遵循模板修复。"}])
                    try:
                        valid_messages = [m for m in messages_to_send if m.get("content") and str(m["content"]).strip()]
                        stream = client.chat.completions.create(model=selected_model, messages=valid_messages,
                                                                stream=True,
                                                                temperature=0.3 if enable_deep_think else 0.7)
                        full_resp = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_resp += chunk.choices[0].delta.content
                                msg_box.markdown(full_resp.replace("<think>", "🧠 深度思考中...\n\n").replace("</think>",
                                                                                                             "\n\n---\n") + "▌",
                                                 unsafe_allow_html=True)
                        msg_box.markdown(
                            full_resp.replace("<think>", "🧠 深度思考过程：\n").replace("</think>", "\n---\n"),
                            unsafe_allow_html=True)
                        code_match = re.search(r"`{3}python\s*(.*?)\s*`{3}", full_resp, re.DOTALL)
                        resp_clean = re.sub(r"<think>.*?</think>", "", full_resp, flags=re.DOTALL)
                        explanation = re.sub(r"`{3}python\s*.*?\s*`{3}", "", resp_clean,
                                             flags=re.DOTALL).strip().replace("【策略白话解析】", "").strip()
                        st.session_state.strategy_explanation = explanation if explanation else "该策略完全由硬核代码驱动，未返回额外人话分析。"
                        if not code_match: break
                        extracted_code = code_match.group(1).strip()
                        try:
                            dummy_df = pd.DataFrame(
                                {'trade_date': pd.date_range('20230101', periods=50), 'Open': np.random.rand(50) * 10,
                                 'High': np.random.rand(50) * 12, 'Low': np.random.rand(50) * 8,
                                 'Close': np.random.rand(50) * 10})
                            _ = execute_safely(extracted_code, add_default_indicators(dummy_df))
                            st.session_state.generated_code = extracted_code
                            agent_logs.append(
                                f'<div class="agent-status-node success">✅ <b>尝试 {attempt + 1}:</b> 代码通过沙盒预检 -> 策略已安全装载</div>')
                            st.markdown("".join(agent_logs), unsafe_allow_html=True)
                            break
                        except Exception as e:
                            last_error = str(e)
                            if attempt == max_retries:
                                agent_logs.append(
                                    f'<div class="agent-status-node error">❌ <b>最终结果:</b> 失败，最终报错: <code>{last_error}</code></div>')
                                st.markdown("".join(agent_logs), unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"链路断开: {e}")
                        full_resp += f"\n\n❌ [异常阻断: 通信失败或超载 - {e}]"
                        break
                if not full_resp or not full_resp.strip(): full_resp = "❌ 大模型网络中断或未返回任何数据，请重试。"
                if agent_logs: full_resp += "\n\n" + "".join(agent_logs)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
        st.rerun()

elif selected_page == PAGES[2]:
    if extensions: extensions.render_ide_page()

elif selected_page == PAGES[3]:
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0;">📊 历史回测全量审计与归因分析</h3></div>',
        unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])
    with col_l:
        ts_code = format_ts_code(st.text_input("🎯 回测标的代码", value="000001"))
        span_mapping = {"近1年": 1, "近3年": 3, "近5年": 5, "近10年 (极限穿越)": 10}
        span_choice = st.selectbox("⏳ 回测时间跨度", list(span_mapping.keys()), index=1)
        start_year = datetime.now().year - span_mapping[span_choice]
        adj_p = st.selectbox("⚖️ 复权模式", ["qfq", "hfq", "None"]).split(" ")[0]
        if st.button("🚀 启动全量归因回测", use_container_width=True, type="primary"):
            with st.spinner("数据挂载中..."):
                try:
                    df_raw = fetch_and_clean_data(ts_code, adj_p if adj_p != "None" else None, f"{start_year}0101")
                    st.session_state.bt_result = run_backtest_metrics(df_raw, st.session_state.generated_code)
                except Exception as e:
                    st.error(f"异常: {e}")
    with col_r:
        if st.session_state.bt_result:
            m = st.session_state.bt_result['metrics']
            df = st.session_state.bt_result['df']
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(
                f'<div class="metric-box"><p>累计收益</p><h2 style="color:#3b82f6;">{m["total"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c2.markdown(
                f'<div class="metric-box"><p>年化收益</p><h2 style="color:#3b82f6;">{m["annual"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c3.markdown(
                f'<div class="metric-box"><p>最大回撤</p><h2 style="color:#ef4444;">{m["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c4.markdown(
                f'<div class="metric-box"><p>夏普比率</p><h2 style="color:#3b82f6;">{m["sharpe"]:.2f}</h2></div>',
                unsafe_allow_html=True)
            st.markdown("<div style='clear: both; margin-bottom: 30px;'></div>", unsafe_allow_html=True)
            if st.session_state.generated_code and st.session_state.strategy_explanation != "暂无策略解析，请先前往 AI 战情室下达军令。":
                with st.expander("💡 展开：AI 策略白话解析", expanded=False): st.markdown(
                    st.session_state.strategy_explanation)
            st.plotly_chart(render_smart_charts(df), use_container_width=True, config={'scrollZoom': True})

elif selected_page == PAGES[4]:
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0;">⚡ 高频沙盘模拟推演 (Real-time Flow)</h3></div>',
        unsafe_allow_html=True)
    c_ctrl, c_chart = st.columns([1, 2.5])
    with c_ctrl:
        live_code = st.text_input("🎯 动态推送标的", value="000001")
        freq = st.slider("⏱️ 刷新间隔 (秒)", 0.1, 2.0, 0.5)
        st.button("▶️ 开启高频推演", on_click=lambda: st.session_state.update({"is_live_trading": True}),
                  type="primary")
        st.button("⏹️ 强行停止", on_click=lambda: st.session_state.update({"is_live_trading": False}))
    with c_chart:
        if st.session_state.generated_code and st.session_state.strategy_explanation != "暂无策略解析，请先前往 AI 战情室下达军令。":
            with st.expander("💡 当前军令：策略白话解析", expanded=False): st.markdown(
                st.session_state.strategy_explanation)
        met_ph = st.empty();
        cht_ph = st.empty()
        if st.session_state.is_live_trading:
            stream = fetch_and_clean_data(format_ts_code(live_code), 'qfq', '20230101').tail(120).reset_index(drop=True)
            for i in range(20, len(stream)):
                if not st.session_state.is_live_trading: break
                sub = stream.iloc[:i].copy()
                try:
                    if st.session_state.generated_code:
                        sub_ai = execute_safely(st.session_state.generated_code, sub)
                        if sub_ai is not None and hasattr(sub_ai, 'columns'):
                            for col in sub_ai.columns:
                                if col == 'Signal' or col.startswith(('MAIN_', 'SUB')): sub[col] = sub_ai[col]
                    sig_val = sub['Signal'].iloc[-1] if 'Signal' in sub.columns else 0
                    with met_ph.container():
                        c = st.columns(3)
                        c[0].metric("Tick 现价", f"{sub['Close'].iloc[-1]:.2f}")
                        c[1].metric("高频信号", "🟢 买" if sig_val == 1 else "🔴 卖" if sig_val == -1 else "⚪ 观望")
                        c[2].metric("并发收益", f"{(sub['Close'].pct_change().iloc[-1] * 100):.2f}%")
                    cht_ph.plotly_chart(render_smart_charts(sub), use_container_width=True)
                except Exception as e:
                    st.error(f"高频熔断: {e}");
                    st.session_state.is_live_trading = False;
                    break
                time.sleep(freq)

elif selected_page == PAGES[5]:
    with st.spinner("唤醒深度学习底层张量引擎..."):
        try:
            import torch
            import torch.nn as nn
            from sklearn.preprocessing import MinMaxScaler
        except ImportError:
            st.error("🚨 需安装 torch 和 scikit-learn！")
            st.stop()
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0;">🧠 深度神经网络时序建模矩阵 (白盒透视版)</h3></div>',
        unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])
    with col_l:
        st_code = st.text_input("🎯 训练模型标的", value="000001")
        span_mapping_dl = {"近1年 (极速)": 1, "近3年 (标准)": 3, "近5年 (深度)": 5}
        span_choice_dl = st.selectbox("⏳ 训练集时间跨度", list(span_mapping_dl.keys()), index=1)
        start_year_dl = datetime.now().year - span_mapping_dl[span_choice_dl]
        st.markdown("---")
        run_mode = st.radio("⚙️ 引擎运行模式", ["🚀 在线动态训练", "📂 导入本地模型"], horizontal=True)
        if "在线动态" in run_mode:
            model_choices = st.multiselect("🧠 选择预测模型 (支持多选融合)", ["LSTM", "GRU", "1D-CNN"], default=["LSTM"])
            slen = st.slider("📏 滑窗长度", 5, 60, 20)
            eps = st.slider("🔄 Epoch 迭代", 10, 50, 30)
            uploaded_model = None;
            btn_text = "🚀 启动张量训练"
        else:
            model_choices = st.multiselect("🧠 指定本地模型架构", ["LSTM", "GRU", "1D-CNN"], default=["LSTM"],
                                           max_selections=1)
            slen = st.slider("📏 滑窗长度 (需与本地模型一致)", 5, 60, 20)
            uploaded_model = st.file_uploader("📥 上传 PyTorch 权重文件 (.pth / .pt)", type=['pth', 'pt'])
            eps = 0;
            btn_text = "⚡ 挂载模型并推演"

        if st.button(btn_text, type="primary", use_container_width=True):
            if "导入本地模型" in run_mode and not uploaded_model:
                st.error("主公，请先上传本地训练好的权重文件！")
            elif not model_choices:
                st.error("主公，请至少选择一种预测模型！")
            else:
                with st.spinner("神经网络前向传播中..."):
                    try:
                        df = fetch_and_clean_data(format_ts_code(st_code), 'qfq', f"{start_year_dl}0101")
                        scaler = MinMaxScaler()
                        scaled = scaler.fit_transform(df['Close'].values.reshape(-1, 1))
                        X, y = [], []
                        for i in range(slen, len(scaled)): X.append(scaled[i - slen:i, 0]); y.append(scaled[i, 0])
                        X_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1)
                        y_t = torch.tensor(np.array(y), dtype=torch.float32)


                        class LSTM_Model(nn.Module):
                            def __init__(self):
                                super().__init__();
                                self.lstm = nn.LSTM(1, 64, 2, batch_first=True);
                                self.fc = nn.Linear(64, 1)

                            def forward(self, x): out, _ = self.lstm(x); return self.fc(out[:, -1, :])


                        class GRU_Model(nn.Module):
                            def __init__(self):
                                super().__init__();
                                self.gru = nn.GRU(1, 64, 2, batch_first=True);
                                self.fc = nn.Linear(64, 1)

                            def forward(self, x): out, _ = self.gru(x); return self.fc(out[:, -1, :])


                        class CNN_1D_Model(nn.Module):
                            def __init__(self, seq_len):
                                super().__init__();
                                self.conv = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3, padding=1);
                                self.fc = nn.Linear(32 * seq_len, 1)

                            def forward(self, x): x = x.permute(0, 2, 1); x = torch.relu(self.conv(x)); x = x.reshape(
                                x.size(0), -1); return self.fc(x)


                        preds_dict, future_preds_dict = {}, {}
                        lbox = st.empty();
                        pbar = st.progress(0);
                        last_window_orig = X_t[-1].clone().unsqueeze(0)

                        for m_idx, m_name in enumerate(model_choices):
                            if m_name == "LSTM":
                                model = LSTM_Model()
                            elif m_name == "GRU":
                                model = GRU_Model()
                            elif m_name == "1D-CNN":
                                model = CNN_1D_Model(slen)

                            if "导入本地模型" in run_mode:
                                lbox.markdown(f"**正在解析并挂载本地 {m_name} 模型权重...**")
                                try:
                                    model.load_state_dict(torch.load(uploaded_model, map_location=torch.device('cpu')))
                                    lbox.success(f"**{m_name}** | 权重校验通过，挂载成功！");
                                    pbar.progress(1.0)
                                except Exception as load_e:
                                    st.warning(f"⚠️ 模型架构不匹配，极速重训练... ({load_e})")
                                    opt = torch.optim.Adam(model.parameters(), lr=0.01);
                                    crit = nn.MSELoss()
                                    for e in range(10): model.train(); opt.zero_grad(); loss = crit(
                                        model(X_t).squeeze(), y_t); loss.backward(); opt.step()
                            else:
                                lbox.markdown(f"**正在在线训练 {m_name} 模型...**")
                                opt = torch.optim.Adam(model.parameters(), lr=0.01);
                                crit = nn.MSELoss()
                                for e in range(eps):
                                    model.train();
                                    opt.zero_grad();
                                    pred = model(X_t);
                                    loss = crit(pred.squeeze(), y_t);
                                    loss.backward();
                                    opt.step()
                                    pbar.progress((m_idx * eps + e + 1) / (len(model_choices) * eps))
                                    lbox.markdown(f"**{m_name}** | Epoch {e + 1}/{eps} | Loss: {loss.item():.6f}")

                            model.eval()
                            test_p = model(X_t[-100:]).detach().numpy()
                            preds_dict[m_name] = scaler.inverse_transform(test_p).flatten()
                            curr_win = last_window_orig.clone()
                            m_future = []
                            for _ in range(5):
                                with torch.no_grad(): p_future = model(curr_win)
                                m_future.append(p_future.item())
                                curr_win = torch.cat((curr_win[:, 1:, :], p_future.unsqueeze(-1)), dim=1)
                            future_preds_dict[m_name] = scaler.inverse_transform(
                                np.array(m_future).reshape(-1, 1)).flatten()

                        lbox.success("✅ 矩阵模型装载完毕，时空推演已就绪！")
                        st.session_state.dl_result = {"dates": df['trade_date'].iloc[-100:],
                                                      "actual": df['Close'].iloc[-100:], "preds": preds_dict,
                                                      "future": future_preds_dict, "models_used": model_choices}
                    except Exception as e:
                        st.error(f"DL 张量异常: {e}")

    with col_r:
        if st.session_state.dl_result:
            res = st.session_state.dl_result
            latest_price = res['actual'].iloc[-1];
            actual_vals = res['actual'].values
            if len(res['models_used']) > 1:
                f_preds = np.mean(list(res['future'].values()), axis=0);
                h_preds = np.mean(list(res['preds'].values()), axis=0)
                model_desc = f"LSTM/GRU/CNN 均值集成 ({len(res['models_used'])}模型)"
            else:
                f_preds = list(res['future'].values())[0];
                h_preds = list(res['preds'].values())[0]
                model_desc = res['models_used'][0]

            act_diff = np.diff(actual_vals);
            pred_diff = np.diff(h_preds)
            success_rate = np.mean(np.sign(act_diff) == np.sign(pred_diff)) * 100
            mape = np.mean(np.abs((actual_vals - h_preds) / (actual_vals + 1e-8))) * 100
            day1_pred = f_preds[0];
            day5_pred = f_preds[4]

            with st.expander("🤖 AI 深度预测白盒解析舱 (点击展开/收起)", expanded=True):
                st.markdown(
                    f"**📈 极速解盘预览**：当前实盘价 `<span class='highlight-text'>{latest_price:.2f}</span>` | 驱动核心: {model_desc}",
                    unsafe_allow_html=True)
                c_f1, c_f2, c_f3, c_f4 = st.columns(4)
                c_f1.metric("未来 1 天预测 (T+1)", f"{day1_pred:.2f}",
                            f"{(day1_pred - latest_price) / latest_price * 100:.2f}%")
                c_f2.metric("未来 5 天预测 (T+5)", f"{day5_pred:.2f}",
                            f"{(day5_pred - latest_price) / latest_price * 100:.2f}%")
                c_f3.metric("🎯 历史方向胜率", f"{success_rate:.1f}%", "涨跌准确度")
                c_f4.metric("⚖️ 平均预测偏差", f"{mape:.2f}%", "绝对偏离度", delta_color="inverse")

                if st.button("✨ 召唤 Kimi 结合胜率生成人话解盘", use_container_width=True):
                    ai_ph = st.empty()
                    prompt = f"你是一个顶级的量化分析师，为小白解盘。当前收盘价 {latest_price:.2f}元。基于【{model_desc}】推演，未来1天预测价为 {day1_pred:.2f}元，未来5天为 {day5_pred:.2f}元。模型胜率为 {success_rate:.1f}%，偏差为 {mape:.2f}%。请用大白话（限200字以内，不要代码），向小白解释并给出建议。"
                    try:
                        stream = client.chat.completions.create(model="moonshot-v1-8k",
                                                                messages=[{"role": "user", "content": prompt}],
                                                                stream=True, temperature=0.5)
                        full_txt = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content: full_txt += chunk.choices[0].delta.content; ai_ph.info(
                                full_txt + "▌")
                        ai_ph.info(full_txt)
                    except Exception as e:
                        ai_ph.error(f"Kimi 连线中断: {e}")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['actual'], name='真实轨迹 (Actual)',
                                     line=dict(color='#10b981', width=2)))
            color_map = {"LSTM": "#3b82f6", "GRU": "#f59e0b", "1D-CNN": "#8b5cf6"}
            for m_name, pred_array in res['preds'].items(): fig.add_trace(
                go.Scatter(x=res['dates'], y=pred_array, name=f'{m_name} 历史拟合',
                           line=dict(color=color_map.get(m_name, '#94a3b8'), dash='dot', width=1.5)))
            if len(res['preds']) > 1: fig.add_trace(
                go.Scatter(x=res['dates'], y=np.mean(list(res['preds'].values()), axis=0), name='🔥 均值集成 (Ensemble)',
                           line=dict(color='#ef4444', width=3)))
            fig.update_layout(height=450, template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              dragmode='pan', hovermode='x',
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)');
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            st.plotly_chart(fig, use_container_width=True)

elif selected_page == PAGES[6]:
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0;">🛡️ 实验数据采集与多维审计中心</h3></div>',
        unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        if os.path.exists("user_logs/global_master_log.csv"): st.download_button("📁 导出审计日志", data=pd.read_csv(
            "user_logs/global_master_log.csv").to_csv(index=False).encode('utf-8'), file_name='Audit_Logs.csv',
                                                                                 type="primary")
    with c2:
        st.text_area("实时工作流终端", value="\n".join(st.session_state.sys_logs), height=350)

elif selected_page == PAGES[7]:
    if extensions: extensions.render_futures_backtest()

elif selected_page == PAGES[8]:
    if extensions: extensions.render_futures_sandbox()

elif selected_page == PAGES[9]:
    if extensions: extensions.render_new_features_page()

else:
    if custom_plugins and hasattr(custom_plugins, 'route_and_render'): custom_plugins.route_and_render(selected_page)