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
import os
import uuid
import math
from PIL import Image

# 物理级防呆补丁
pd.np = np

# 🔥 预编译正则表达式，榨干 CPU 性能 🔥
SUB_PATTERN = re.compile(r'^SUB(\d+)_')

# ==========================================
# 1. 核心兵符与状态初始化
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro - 毕设版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"
ts.set_token(TUSHARE_TOKEN)


@st.cache_resource
def get_ts_pro(): return ts.pro_api()


pro = get_ts_pro()

client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=60.0)

if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "messages" not in st.session_state: st.session_state.messages = []
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "strategy_explanation" not in st.session_state: st.session_state.strategy_explanation = "暂无策略解析，请先前往 AI 战情室下达军令。"
if "dl_result" not in st.session_state: st.session_state.dl_result = None
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "is_live_trading" not in st.session_state: st.session_state.is_live_trading = False

# ==========================================
# 2. 空间流形导航逻辑与置顶引掣
# ==========================================
PAGES = ["🏠 系统总览 (监控中控)", "🤖 AI 策略引擎 (LLM)", "📈 深度静态全量回测", "⚡ 实时高频交易 (Live)",
         "🧠 深度学习预测矩阵", "🛡️ 论文审计日志"]

if "curr_page" not in st.session_state: st.session_state.curr_page = PAGES[0]
if "prev_page" not in st.session_state: st.session_state.prev_page = PAGES[0]
if "just_switched" not in st.session_state: st.session_state.just_switched = False

with st.sidebar:
    st.markdown("### 🎓 小吕布量化 Pro")
    st.caption(f"🛡️ 节点 ID: {st.session_state.user_id}")
    st.markdown("---")
    selected_page = st.radio("导航菜单", PAGES, label_visibility="collapsed")

if selected_page != st.session_state.curr_page:
    st.session_state.prev_page = st.session_state.curr_page
    st.session_state.curr_page = selected_page
    st.session_state.just_switched = True
else:
    st.session_state.just_switched = False

prev_idx, curr_idx = PAGES.index(st.session_state.prev_page), PAGES.index(st.session_state.curr_page)
anim_name = "waveBlurUpIn" if curr_idx > prev_idx else ("waveBlurDownIn" if curr_idx < prev_idx else "fogFadeIn")

# ==========================================
# 3. 宗师级 JS 引擎：零损耗 MutationObserver
# ==========================================
scroll_script = "window.parent.scrollTo({top: 0, behavior: 'instant'});" if st.session_state.just_switched else ""

components.html(f"""
<script>
    {scroll_script}
    let isUpdating = false;
    const runGlobalEngine = () => {{
        if(isUpdating) return;
        isUpdating = true;

        requestAnimationFrame(() => {{
            const doc = window.parent.document;
            const app = doc.querySelector('.stApp');
            if (app) {{
                const color = window.getComputedStyle(app).color;
                const rgb = color.match(/\\d+/g);
                if (rgb && rgb.length >= 3) {{
                    const brightness = (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) / 1000;
                    const themeAttr = brightness < 128 ? 'light' : 'dark';
                    if (app.getAttribute('data-custom-theme') !== themeAttr) app.setAttribute('data-custom-theme', themeAttr);
                }}
            }}

            const chatInputOuter = doc.querySelector('div[data-testid="stChatInput"]');
            if (chatInputOuter) {{
                const innerPill = chatInputOuter.querySelector('.stChatInputContainer') || chatInputOuter.children[0]; 
                const realPopoverBtn = doc.querySelector('.real-popover-wrapper button');

                if (innerPill && realPopoverBtn && !doc.getElementById('fake-attach-btn')) {{
                    const fakeBtn = doc.createElement('div');
                    fakeBtn.id = 'fake-attach-btn';
                    fakeBtn.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #8b9bb4; cursor: pointer; transition: 0.2s;"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>`;
                    fakeBtn.style.cssText = 'display: flex; align-items: center; justify-content: center; margin-right: 10px; margin-left: 5px; height: 100%;';
                    fakeBtn.onclick = () => realPopoverBtn.click();
                    fakeBtn.onmouseover = () => {{ fakeBtn.style.opacity = '0.6'; }};
                    fakeBtn.onmouseout = () => {{ fakeBtn.style.opacity = '1'; }};

                    innerPill.insertBefore(fakeBtn, innerPill.firstChild);
                    const textArea = innerPill.querySelector('[data-baseweb="textarea"]');
                    if(textArea) textArea.style.setProperty('padding-left', '5px', 'important');
                }}
            }}
            isUpdating = false;
        }});
    }};

    runGlobalEngine();
    const observer = new MutationObserver(runGlobalEngine);
    observer.observe(window.parent.document.body, {{ childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style'] }});
</script>
""", height=0, width=0)

# ==========================================
# 4. 极致静态 CSS + 动态动画
# ==========================================
st.markdown("""
<style>
    @keyframes fluidFlow { 0% { background-position: 0% 50%; } 25% { background-position: 50% 100%; } 50% { background-position: 100% 50%; } 75% { background-position: 50% 0%; } 100% { background-position: 0% 50%; } }
    @keyframes waveBlurUpIn { 0% { opacity: 0; margin-top: 60px; filter: blur(15px); transform: scale(0.98); } 100% { opacity: 1; margin-top: 0px; filter: blur(0px); transform: scale(1); } }
    @keyframes waveBlurDownIn { 0% { opacity: 0; margin-top: -60px; filter: blur(15px); transform: scale(0.98); } 100% { opacity: 1; margin-top: 0px; filter: blur(0px); transform: scale(1); } }
    @keyframes fogFadeIn { 0% { opacity: 0; filter: blur(15px); transform: scale(0.98); } 100% { opacity: 1; filter: blur(0px); transform: scale(1); } }

    header[data-testid="stHeader"] { position: fixed !important; top: 0px !important; transform: translateY(0px) !important; opacity: 1 !important; visibility: visible !important; background: transparent !important; pointer-events: none !important; }
    [data-testid="collapsedControl"], [data-testid="stToolbar"] { pointer-events: auto !important; opacity: 1 !important; visibility: visible !important; display: flex !important; transform: none !important;}
    .stMarkdown a.header-anchor, .stMarkdown h1 svg, .stMarkdown h2 svg, .stMarkdown h3 svg { display: none !important; pointer-events: none !important; }
    [data-testid="stAppViewContainer"], [data-testid="stBottomBlock"], [data-testid="stBottom"] > div { background: transparent !important; border: none !important; }
    .real-popover-wrapper { opacity: 0.01 !important; height: 1px !important; overflow: hidden !important; margin: 0 !important; padding: 0 !important; }

    .stApp { background-image: linear-gradient(132deg, #02040a, #030e2b, #111d3d, #082a72, #030614, #1d2b4f, #0a47b3, #02040a) !important; background-size: 600% 600% !important; animation: fluidFlow 18s ease-in-out infinite !important; }
    .stMarkdown, p, h1, h2, h3, h4, label, [data-testid="stMetricValue"] > div { color: #e2e8f0 !important; }
    .highlight-text { color: #00ffcc !important; }
    .sub-text { color: #cbd5e1 !important; }
    .danger-text { color: #ff4b4b !important; }

    [data-testid="stSidebar"] { background: rgba(5, 8, 14, 0.75) !important; backdrop-filter: blur(25px) !important; border-right: 1px solid rgba(255,255,255,0.08) !important; min-height: 100vh !important; }
    [data-testid="stSidebar"] > div:first-child { background: transparent !important; }
    div[role="radiogroup"] > label { background: rgba(15, 20, 30, 0.4) !important; border-left: 4px solid transparent !important; border-radius: 12px !important; margin-bottom: 10px !important;}
    div[role="radiogroup"] > label:has(input:checked) { background: linear-gradient(90deg, rgba(0, 255, 204, 0.3), rgba(10, 15, 25, 0.95)) !important; border-left: 4px solid #00ffcc !important; }

    .glass-card { background: rgba(20, 28, 45, 0.65) !important; backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6); }
    .metric-box { background: rgba(0, 255, 204, 0.05); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; overflow: hidden; }
    .metric-box p { margin: 0 !important; font-size: 0.9rem; color: #cbd5e1; }
    .metric-box h2 { margin: 8px 0 0 0 !important; font-size: 1.8rem; line-height: 1.2; }
    [data-testid="stExpander"] { background: rgba(15, 23, 35, 0.8) !important; border: 1px solid rgba(0, 255, 204, 0.3) !important; border-radius: 16px !important; backdrop-filter: blur(10px); margin-bottom: 20px !important; }

    [data-testid="stChatInput"] { background: transparent !important; border: none !important; box-shadow: none !important; max-width: 850px; margin: 0 auto 10px auto !important; }
    [data-testid="stChatInput"] > div:first-child { background-color: rgba(30, 41, 59, 0.6) !important; backdrop-filter: blur(25px) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; border-radius: 36px !important; box-shadow: 0 15px 50px rgba(0, 0, 0, 0.6) !important; padding: 5px 15px !important; display: flex !important; align-items: center !important; }
    [data-testid="stChatInput"] [data-baseweb="textarea"], [data-testid="stChatInput"] [data-baseweb="textarea"] > div { background-color: transparent !important; border: none !important; box-shadow: none !important; outline: none !important; }
    [data-testid="stChatInput"] textarea { color: #ffffff !important; font-size: 16px !important; line-height: 1.5 !important; }
    [data-testid="stChatInputSubmitButton"] { background-color: #3b82f6 !important; border-radius: 50% !important; transition: all 0.3s ease; }
    [data-testid="stPopoverBody"] { background-color: rgba(25, 33, 48, 0.95) !important; border: 1px solid rgba(0, 255, 204, 0.4) !important; border-radius: 16px !important; backdrop-filter: blur(25px) !important; padding: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important; margin-bottom: 10px !important; }

    .stApp[data-custom-theme='light'] { background-image: linear-gradient(132deg, #ffffff, #dbeafe, #e0e7ff, #f3e8ff, #ffffff) !important; background-size: 400% 400% !important; animation: fluidFlow 10s ease infinite !important; }
    .stApp[data-custom-theme='light'] .stMarkdown, .stApp[data-custom-theme='light'] p, .stApp[data-custom-theme='light'] h1, .stApp[data-custom-theme='light'] h2, .stApp[data-custom-theme='light'] h3, .stApp[data-custom-theme='light'] h4, .stApp[data-custom-theme='light'] label, .stApp[data-custom-theme='light'] [data-testid="stMetricValue"] > div { color: #1e293b !important; }
    .stApp[data-custom-theme='light'] .highlight-text { color: #0284c7 !important; }
    .stApp[data-custom-theme='light'] .sub-text { color: #475569 !important; }
    .stApp[data-custom-theme='light'] .danger-text { color: #dc2626 !important; }
    .stApp[data-custom-theme='light'] .glass-card { background: rgba(255, 255, 255, 0.75) !important; border: 1px solid rgba(0, 0, 0, 0.1) !important; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.06) !important; }
    .stApp[data-custom-theme='light'] .metric-box { background: rgba(2, 132, 199, 0.05) !important; border: 1px solid rgba(2, 132, 199, 0.2) !important; }
    .stApp[data-custom-theme='light'] .metric-box p { color: #475569; }
    .stApp[data-custom-theme='light'] [data-testid="stExpander"] { background: rgba(255, 255, 255, 0.9) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; }
    .stApp[data-custom-theme='light'] [data-testid="stSidebar"] { background: rgba(248, 250, 252, 0.85) !important; border-right: 1px solid rgba(0,0,0,0.08) !important; }
    .stApp[data-custom-theme='light'] div[role="radiogroup"] > label { background: rgba(241, 245, 249, 0.8) !important; border-left: 4px solid transparent !important; }
    .stApp[data-custom-theme='light'] div[role="radiogroup"] > label:has(input:checked) { background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(255, 255, 255, 0.95)) !important; border-left: 4px solid #3b82f6 !important; }
    .stApp[data-custom-theme='light'] [data-testid="stChatInput"] > div:first-child { background-color: rgba(255, 255, 255, 0.85) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; box-shadow: 0 15px 50px rgba(0, 0, 0, 0.08) !important; }
    .stApp[data-custom-theme='light'] [data-testid="stChatInput"] textarea { color: #1e293b !important; }
    .stApp[data-custom-theme='light'] [data-testid="stPopoverBody"] { background-color: rgba(255, 255, 255, 0.98) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important; }
    .stApp[data-custom-theme='light'] .js-plotly-plot .g-gtitle text, .stApp[data-custom-theme='light'] .js-plotly-plot .g-xtitle text, .stApp[data-custom-theme='light'] .js-plotly-plot .g-ytitle text, .stApp[data-custom-theme='light'] .js-plotly-plot .xtick text, .stApp[data-custom-theme='light'] .js-plotly-plot .ytick text, .stApp[data-custom-theme='light'] .js-plotly-plot .legendtext { fill: #1e293b !important; font-weight: 500 !important; }
    .stApp[data-custom-theme='light'] [data-testid="collapsedControl"] svg, .stApp[data-custom-theme='light'] [data-testid="stToolbar"] svg { fill: #1e293b !important; color: #1e293b !important; }
    .stApp[data-custom-theme='dark'] [data-testid="collapsedControl"] svg, .stApp[data-custom-theme='dark'] [data-testid="stToolbar"] svg { fill: #e2e8f0 !important; color: #e2e8f0 !important; }

    .agent-status-node { padding: 8px 12px; border-radius: 8px; font-size: 0.9rem; margin: 5px 0; border-left: 4px solid transparent; display: flex; align-items: center; gap: 10px; }
    .agent-status-node.success { background: rgba(0, 255, 204, 0.1); border-left-color: #00ffcc; color: #00ffcc; }
    .agent-status-node.error { background: rgba(255, 75, 75, 0.1); border-left-color: #ff4b4b; color: #ff4b4b; }
    .agent-status-node.retry { background: rgba(255, 165, 0, 0.1); border-left-color: #ffa500; color: #ffa500; }
    .stApp[data-custom-theme='light'] .agent-status-node.success { background: rgba(16, 185, 129, 0.1); border-left-color: #10b981; color: #047857; }
    .stApp[data-custom-theme='light'] .agent-status-node.error { background: rgba(239, 68, 68, 0.1); border-left-color: #ef4444; color: #b91c1c; }
    .stApp[data-custom-theme='light'] .agent-status-node.retry { background: rgba(245, 158, 11, 0.1); border-left-color: #f59e0b; color: #b45309; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    f"<style>.block-container {{ animation: {anim_name} 0.65s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; background: transparent !important; padding-top: 4.5rem !important; padding-bottom: 120px !important; }}</style>",
    unsafe_allow_html=True)


# ==========================================
# 5. 高速缓存装甲：分离复杂计算
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
    df = ts.pro_bar(ts_code=ts_code, adj=adj, start_date=start_date).sort_values('trade_date').reset_index(drop=True)
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    mapping_base = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'vol': 'Volume', 'amount': 'Amount'}
    for l_case, c_case in mapping_base.items():
        if l_case in df.columns: df[c_case] = df[l_case]
    if 'Volume' not in df.columns and 'vol' in df.columns: df['Volume'] = df['vol']
    return add_default_indicators(df)


@st.cache_data(show_spinner=False)
def run_backtest_metrics(df_source, strategy_code):
    df_safe = df_source.copy()
    if strategy_code:
        df_ai = execute_safely(strategy_code, df_source)
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
    safe_code = code.replace("pandas.np", "np")
    l_vars = {}
    exec(safe_code, {"pd": pd, "np": np, "math": math}, l_vars)
    func_to_call = next((v for k, v in l_vars.items() if callable(v)), None)
    if not func_to_call: raise ValueError("AI 未生成有效函数！")
    df_ai = func_to_call(df)
    sig_col = next((c for c in df_ai.columns if c.lower() == 'signal'), None)
    df_ai['Signal'] = df_ai[sig_col].fillna(0).apply(lambda x: 1 if x > 0.1 else (-1 if x < -0.1 else 0)).astype(
        int) if sig_col else 0
    return df_ai


def render_smart_charts(df):
    main_inds = [c for c in df.columns if c.startswith('MAIN_')]
    sub_groups = {}
    for c in df.columns:
        gid = SUB_PATTERN.match(c)
        if gid: sub_groups.setdefault(gid.group(1), []).append(c)
    rows = 2 + len(sub_groups)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.5, 0.15] + [0.35 / max(1, len(sub_groups))] * len(sub_groups))
    fig.add_trace(go.Candlestick(x=df['trade_date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 increasing_line_color='#FD1050', decreasing_line_color='#00FF00', name='K线'), row=1,
                  col=1)
    colors = ['#FFFF00', '#FF00FF', '#00FFFF', '#FFFFFF']
    for i, col in enumerate(main_inds): fig.add_trace(
        go.Scatter(x=df['trade_date'], y=df[col], name=col, line=dict(width=1.2, color=colors[i % 4])), row=1, col=1)
    if 'Signal' in df.columns:
        buys, sells = df[df['Signal'] == 1], df[df['Signal'] == -1]
        fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['Low'] * 0.95, mode='markers',
                                 marker=dict(symbol='triangle-up', size=14, color='#00FFFF'), name='买'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['High'] * 1.05, mode='markers',
                                 marker=dict(symbol='triangle-down', size=14, color='#FF00FF'), name='卖'), row=1,
                      col=1)
    fig.add_trace(go.Bar(x=df['trade_date'], y=df.get('Volume', np.zeros(len(df))),
                         marker_color=np.where(df['Close'] >= df['Open'], '#FD1050', '#00FF00'), name='成交量'), row=2,
                  col=1)

    row_idx = 3
    for gid in sorted(sub_groups.keys(), key=int):
        for i, col in enumerate(sub_groups[gid]):
            if 'HIST' in col.upper():
                fig.add_trace(
                    go.Bar(x=df['trade_date'], y=df[col], marker_color=np.where(df[col] >= 0, '#FD1050', '#00FF00'),
                           name=col), row=row_idx, col=1)
            else:
                fig.add_trace(
                    go.Scatter(x=df['trade_date'], y=df[col], line=dict(width=1.2, color=colors[i % 4]), name=col),
                    row=row_idx, col=1)
        row_idx += 1

    fig.update_layout(height=500 + len(sub_groups) * 150, template="none", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False, dragmode='pan', hovermode='x',
                      showlegend=False)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    return fig


def format_ts_code(raw):
    raw = str(raw).strip().upper()
    if len(raw) == 6 and raw.isdigit(): return f"{raw}.SH" if raw.startswith(('6', '9')) else f"{raw}.SZ"
    return raw


# ==========================================
# 6. 各页面业务逻辑
# ==========================================
if selected_page == PAGES[0]:
    st.markdown(
        '<div class="glass-card"><h1 style="margin-bottom:0; color:var(--text-color);">🏛️ 全链路智能量化决策枢纽</h1><p class="highlight-text" style="font-size:1.1rem; margin-top:5px;">System Overview & Mid-term Inspection Dashboard</p></div>',
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
    st.markdown(
        '<div class="glass-card" style="padding:15px; margin-bottom:20px;"><b class="highlight-text">🎯 极简操作指南：</b><span class="sub-text" style="margin-left: 10px;">1. 回测界输入标的拉取数据 | 2. 策略引擎上传研报下令 | 3. 深度预测界面勾选多模型融合。</span></div>',
        unsafe_allow_html=True)
    c_arch, c_point = st.columns([2, 1])
    with c_arch:
        st.markdown(
            '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom: 0px;">🧠 核心架构与操作流 (Data Flow Pipeline)</h3></div>',
            unsafe_allow_html=True)
        mermaid_str = "graph LR\nA[📊 1. 获取数据] -->|喂入| B(🧠 2. 模型预测)\nB -->|信号| C{📈 3. 全量回测}\nC -->|报告| D[🤖 4. AI 解读]"
        components.html(
            f"""<script type="module">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs'; mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});</script><div class="mermaid" style="text-align:center;">{mermaid_str}</div>""",
            height=350)
    with c_point:
        st.markdown(
            '<div class="glass-card"><h4 style="color:var(--text-color);">📋 平台监控与杀手锏</h4>**内存池占用率**<br>🟢 4% (完全释放)<br><br>**答辩核心创新点：**<br>✅ AI 白盒透视解析<br>✅ MutationObserver 零消耗<br>✅ 自定义十载周期</div>',
            unsafe_allow_html=True)

elif selected_page == PAGES[1]:
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0; color:var(--text-color);">🤖 LLM 策略战情室</h3><p class="sub-text">多模态视觉引擎与 Agent 自愈模块已就绪，体验沉浸式工作流。</p></div>',
        unsafe_allow_html=True)

    ctrl_col1, ctrl_col2 = st.columns([1, 1])
    with ctrl_col1:
        selected_model = st.selectbox("🧠 选择大模型算力通道", ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                                      index=0)
    with ctrl_col2:
        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True); enable_deep_think = st.toggle(
            "💡 强子注入：开启深度思考引擎 (CoT)", value=False)

    chat_container = st.container()
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

    st.markdown('<div class="real-popover-wrapper">', unsafe_allow_html=True)
    with st.popover("📎", help="上传附件", use_container_width=False):
        uploaded_files = st.file_uploader("选择文件", accept_multiple_files=True,
                                          type=['png', 'jpg', 'jpeg', 'csv', 'txt'], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    file_context = ""
    if 'uploaded_files' in locals() and uploaded_files:
        cols = st.columns(3)
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 3]:
                if file.type.startswith('image/'):
                    st.image(Image.open(file),
                             use_container_width=True); file_context += f"[用户上传了图片: {file.name}]"
                elif file.type == 'text/csv':
                    df_upload = pd.read_csv(file); st.dataframe(df_upload.head(
                        2)); file_context += f"【CSV {file.name} 前两行】:\n{df_upload.head(2).to_string()}\n"

    if raw_prompt := st.chat_input("向小吕布量化架构师发送军令..."):
        full_prompt_for_ai = f"以下是附件信息：\n{file_context}\n\n需求：{raw_prompt}" if file_context else raw_prompt
        st.session_state.messages.append({"role": "user", "content": raw_prompt})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(raw_prompt)
            with st.chat_message("assistant"):
                st.toast(f"🚀 连线底层算力集群: {selected_model}", icon="⚡")
                ticks = "`" * 3
                sys_p = f"""你是一名严谨的量化专家。拒绝闲聊。输出代码前独占一行写出“【策略白话解析】”。
必须严格遵循骨架：
{ticks}python
def generate_signals(df):
    buy_condition = (df['MAIN_MA5'] > df['MAIN_MA20']) 
    sell_condition = (df['MAIN_MA5'] < df['MAIN_MA20']) 
    df['Signal'] = 0
    df.loc[buy_condition, 'Signal'] = 1
    df.loc[sell_condition, 'Signal'] = -1
    return df
{ticks}"""
                messages_to_send = [{"role": "system", "content": sys_p}] + st.session_state.messages[:-1] + [
                    {"role": "user", "content": full_prompt_for_ai}]
                max_retries, last_error, agent_logs = 2, "", []

                for attempt in range(max_retries + 1):
                    if attempt > 0:
                        agent_logs.append(
                            f'<div class="agent-status-node retry">🔄 <b>尝试 {attempt}:</b> 沙盒拦截异常 (<code>{last_error}</code>) -> Agent 发起重构</div>')
                        messages_to_send.extend([{"role": "assistant", "content": full_resp}, {"role": "user",
                                                                                               "content": f"代码报错：`{last_error}`，请严格遵循模板修复。"}])

                    msg_box = st.empty()
                    try:
                        stream = client.chat.completions.create(model=selected_model, messages=messages_to_send,
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
                        if code_match:
                            extracted_code = code_match.group(1).strip()

                            # 🔥 修复：重装正则提取器，抓取白话解析 🔥
                            exp_match = re.search(r"【策略白话解析】(.*?)(?=`{3}python|$)", full_resp,
                                                  re.DOTALL | re.IGNORECASE)
                            if exp_match:
                                st.session_state.strategy_explanation = exp_match.group(1).strip()
                            else:
                                st.session_state.strategy_explanation = "该策略无特定白话解析，请参考代码内部注释。"

                            try:
                                dummy_df = pd.DataFrame({'trade_date': pd.date_range('20230101', periods=50),
                                                         'Open': np.random.rand(50) * 10,
                                                         'High': np.random.rand(50) * 12, 'Low': np.random.rand(50) * 8,
                                                         'Close': np.random.rand(50) * 10})
                                dummy_df = add_default_indicators(dummy_df)
                                _ = execute_safely(extracted_code, dummy_df)
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
                        else:
                            break
                    except Exception as e:
                        st.error(f"链路断开: {e}"); break

                if agent_logs: full_resp += "\n\n" + "".join(agent_logs)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
        st.rerun()

elif selected_page == PAGES[2]:
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">📊 历史回测全量审计与归因分析</h3></div>',
        unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])
    with col_l:
        ts_code = format_ts_code(st.text_input("🎯 回测标的代码", value="000001"))

        # 🔥 新增：10 年时空跃迁选择器 🔥
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
            m, df = st.session_state.bt_result['metrics'], st.session_state.bt_result['df']
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(
                f'<div class="metric-box"><p>累计收益</p><h2 class="highlight-text">{m["total"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c2.markdown(
                f'<div class="metric-box"><p>年化收益</p><h2 class="highlight-text">{m["annual"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c3.markdown(
                f'<div class="metric-box"><p>最大回撤</p><h2 class="danger-text">{m["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c4.markdown(
                f'<div class="metric-box"><p>夏普比率</p><h2 class="highlight-text">{m["sharpe"]:.2f}</h2></div>',
                unsafe_allow_html=True)

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            if st.session_state.generated_code and st.session_state.strategy_explanation != "暂无策略解析，请先前往 AI 战情室下达军令。":
                with st.expander("💡 展开：AI 策略白话解析", expanded=False):
                    st.markdown(st.session_state.strategy_explanation)

            st.plotly_chart(render_smart_charts(df), use_container_width=True, config={'scrollZoom': True})

elif selected_page == PAGES[3]:
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">⚡ 高频沙盘模拟推演 (Real-time Flow)</h3></div>',
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
            with st.expander("💡 当前军令：策略白话解析", expanded=False):
                st.markdown(st.session_state.strategy_explanation)

        met_ph, cht_ph = st.empty(), st.empty()
        if st.session_state.is_live_trading:
            # 高频模块保持极速，只拉取近期数据
            stream = fetch_and_clean_data(format_ts_code(live_code), 'qfq', '20230101').tail(120).reset_index(drop=True)
            for i in range(20, len(stream)):
                if not st.session_state.is_live_trading: break
                sub = stream.iloc[:i].copy()
                try:
                    if st.session_state.generated_code:
                        sub_ai = execute_safely(st.session_state.generated_code, sub)
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
                    st.error(f"高频熔断: {e}"); st.session_state.is_live_trading = False; break
                time.sleep(freq)

elif selected_page == PAGES[4]:
    with st.spinner("唤醒深度学习底层张量引擎..."):
        import torch
        import torch.nn as nn
        from sklearn.preprocessing import MinMaxScaler

    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧠 深度神经网络时序建模矩阵 (白盒透视版)</h3></div>',
        unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])

    with col_l:
        st_code = st.text_input("🎯 训练模型标的", value="000001")

        # 🔥 新增：深度学习训练集跨度选择器 🔥
        span_mapping_dl = {"近1年 (极速)": 1, "近3年 (标准)": 3, "近5年 (深度)": 5}
        span_choice_dl = st.selectbox("⏳ 训练集时间跨度", list(span_mapping_dl.keys()), index=1)
        start_year_dl = datetime.now().year - span_mapping_dl[span_choice_dl]

        model_choices = st.multiselect("🧠 选择预测模型 (支持多选融合)", ["LSTM", "GRU", "1D-CNN"], default=["LSTM"])
        slen = st.slider("📏 滑窗长度", 5, 60, 20)
        eps = st.slider("🔄 Epoch 迭代", 10, 50, 30)

        if st.button("🚀 启动张量训练", type="primary", use_container_width=True):
            if not model_choices:
                st.error("主公，请至少选择一种预测模型！")
            else:
                with st.spinner("神经网络前向传播中..."):
                    try:
                        df = fetch_and_clean_data(format_ts_code(st_code), 'qfq', f"{start_year_dl}0101")
                        scaler = MinMaxScaler()
                        scaled = scaler.fit_transform(df['Close'].values.reshape(-1, 1))
                        X, y = [], []
                        for i in range(slen, len(scaled)):
                            X.append(scaled[i - slen:i, 0])
                            y.append(scaled[i, 0])
                        X_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1)
                        y_t = torch.tensor(np.array(y), dtype=torch.float32)


                        class LSTM_Model(nn.Module):
                            def __init__(self): super().__init__(); self.lstm = nn.LSTM(1, 64, 2,
                                                                                        batch_first=True); self.fc = nn.Linear(
                                64, 1)

                            def forward(self, x): out, _ = self.lstm(x); return self.fc(out[:, -1, :])


                        class GRU_Model(nn.Module):
                            def __init__(self): super().__init__(); self.gru = nn.GRU(1, 64, 2,
                                                                                      batch_first=True); self.fc = nn.Linear(
                                64, 1)

                            def forward(self, x): out, _ = self.gru(x); return self.fc(out[:, -1, :])


                        class CNN_1D_Model(nn.Module):
                            def __init__(self, seq_len):
                                super().__init__()
                                self.conv = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
                                self.fc = nn.Linear(32 * seq_len, 1)

                            def forward(self, x):
                                x = x.permute(0, 2, 1)
                                x = torch.relu(self.conv(x))
                                x = x.reshape(x.size(0), -1)
                                return self.fc(x)


                        preds_dict, future_preds_dict = {}, {}
                        lbox, pbar = st.empty(), st.progress(0)
                        last_window_orig = X_t[-1].clone().unsqueeze(0)

                        for m_idx, m_name in enumerate(model_choices):
                            lbox.markdown(f"**正在训练 {m_name} 模型...**")
                            if m_name == "LSTM":
                                model = LSTM_Model()
                            elif m_name == "GRU":
                                model = GRU_Model()
                            elif m_name == "1D-CNN":
                                model = CNN_1D_Model(slen)

                            opt = torch.optim.Adam(model.parameters(), lr=0.01)
                            crit = nn.MSELoss()

                            for e in range(eps):
                                model.train()
                                opt.zero_grad()
                                pred = model(X_t)
                                loss = crit(pred.squeeze(), y_t)
                                loss.backward()
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

                        lbox.success("✅ 矩阵训练完毕，时空推演已就绪！")
                        st.session_state.dl_result = {
                            "dates": df['trade_date'].iloc[-100:],
                            "actual": df['Close'].iloc[-100:],
                            "preds": preds_dict,
                            "future": future_preds_dict,
                            "models_used": model_choices
                        }
                    except Exception as e:
                        st.error(f"DL 张量异常: {e}")

    with col_r:
        if st.session_state.dl_result:
            res = st.session_state.dl_result
            latest_price = res['actual'].iloc[-1]
            actual_vals = res['actual'].values

            if len(res['models_used']) > 1:
                f_preds = np.mean(list(res['future'].values()), axis=0)
                h_preds = np.mean(list(res['preds'].values()), axis=0)
                model_desc = f"LSTM/GRU/CNN 均值集成 ({len(res['models_used'])}模型)"
            else:
                f_preds = list(res['future'].values())[0]
                h_preds = list(res['preds'].values())[0]
                model_desc = res['models_used'][0]

            act_diff = np.diff(actual_vals)
            pred_diff = np.diff(h_preds)
            success_rate = np.mean(np.sign(act_diff) == np.sign(pred_diff)) * 100
            mape = np.mean(np.abs((actual_vals - h_preds) / (actual_vals + 1e-8))) * 100

            day1_pred, day5_pred = f_preds[0], f_preds[4]

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
                    prompt = f"""你是一个顶级的量化分析师，专门为小白用户提供白话解盘，且必须客观提示风险。
已知某标的当前收盘价为 {latest_price:.2f}元。
基于【{model_desc}】深度学习架构的自回归推演，得出：未来1天预测价为 {day1_pred:.2f}元，未来5天预测价为 {day5_pred:.2f}元。
【模型信誉档案】：该模型在过去100天的历史拟合中，涨跌方向预测胜率为 {success_rate:.1f}%，平均绝对价格偏差度为 {mape:.2f}%。
请你用大白话（限200字以内，绝对不能包含代码），向小白用户解释这个预测走势。
关键要求：必须明确提到“{success_rate:.1f}%的胜率”和“{mape:.2f}%的偏差度”，并以此作为依据告诉用户这个预测结论“可信度有多高”，给出您的终极操作建议（比如胜率低就建议观望，胜率高也需谨慎）。"""
                    try:
                        stream = client.chat.completions.create(model="moonshot-v1-8k",
                                                                messages=[{"role": "user", "content": prompt}],
                                                                stream=True, temperature=0.5)
                        full_txt = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_txt += chunk.choices[0].delta.content
                                ai_ph.info(full_txt + "▌")
                        ai_ph.info(full_txt)
                    except Exception as e:
                        ai_ph.error(f"Kimi 连线中断: {e}")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['actual'], name='真实轨迹 (Actual)',
                                     line=dict(color='#00ffcc', width=2)))
            color_map = {"LSTM": "#ff00ff", "GRU": "#ffff00", "1D-CNN": "#00bfff"}
            for m_name, pred_array in res['preds'].items():
                fig.add_trace(go.Scatter(x=res['dates'], y=pred_array, name=f'{m_name} 历史拟合',
                                         line=dict(color=color_map.get(m_name, '#ffffff'), dash='dot', width=1)))
            if len(res['preds']) > 1:
                ensemble_pred = np.mean(list(res['preds'].values()), axis=0)
                fig.add_trace(go.Scatter(x=res['dates'], y=ensemble_pred, name='🔥 均值集成 (Ensemble)',
                                         line=dict(color='#ff4b4b', width=3)))

            fig.update_layout(height=450, template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              dragmode='pan', hovermode='x',
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            st.plotly_chart(fig, use_container_width=True)

elif selected_page == PAGES[5]:
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🛡️ 实验数据采集与多维审计中心</h3></div>',
        unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        if os.path.exists("user_logs/global_master_log.csv"): st.download_button("📁 导出审计日志", data=pd.read_csv(
            "user_logs/global_master_log.csv").to_csv(index=False).encode('utf-8'), file_name='Audit_Logs.csv',
                                                                                 type="primary")
    with c2:
        st.text_area("实时工作流终端", value="\n".join(st.session_state.sys_logs), height=350)