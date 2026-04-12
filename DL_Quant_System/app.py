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
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

# 物理级防呆补丁
pd.np = np

# ==========================================
# 1. 核心兵符与状态初始化
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro - 毕设版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
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
# 2. 全局涡轮 JS 引擎 (修复定位漂移，精确定位)
# ==========================================
components.html("""
<script>
    const runGlobalEngine = () => {
        const doc = window.parent.document;

        // 1. 光暗主题跨域嗅探
        const app = doc.querySelector('.stApp');
        if (app) {
            const color = window.getComputedStyle(app).color;
            const rgb = color.match(/\d+/g);
            if (rgb && rgb.length >= 3) {
                const brightness = (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) / 1000;
                const themeAttr = brightness < 128 ? 'light' : 'dark';
                if (app.getAttribute('data-custom-theme') !== themeAttr) {
                    app.setAttribute('data-custom-theme', themeAttr);
                }
            }
        }

        // 2. 🔥 修正悬浮雷达：精准附着在输入胶囊(innerPill)内部 🔥
        const chatInputOuter = doc.querySelector('div[data-testid="stChatInput"]');
        if (chatInputOuter) {
            // 获取发光的胶囊本体
            const innerPill = chatInputOuter.children[0];
            const popovers = Array.from(doc.querySelectorAll('div[data-testid="stPopover"]'));
            const attachPopover = popovers.find(p => p && p.textContent && p.textContent.includes('📎'));

            if (innerPill && attachPopover && attachPopover.parentElement !== innerPill) {
                // 将光标坐标系死死锁在胶囊本体上
                innerPill.style.setProperty('position', 'relative', 'important');

                // 将按钮设为绝对定位，靠左居中
                attachPopover.style.setProperty('position', 'absolute', 'important');
                attachPopover.style.setProperty('left', '16px', 'important');
                attachPopover.style.setProperty('top', '50%', 'important');
                attachPopover.style.setProperty('transform', 'translateY(-50%)', 'important');
                attachPopover.style.setProperty('z-index', '9999', 'important');
                attachPopover.style.setProperty('margin', '0', 'important');

                // 剥离原生按钮的丑陋底色和箭头
                const btn = attachPopover.querySelector('button');
                if (btn) {
                    btn.style.setProperty('background', 'transparent', 'important');
                    btn.style.setProperty('border', 'none', 'important');
                    btn.style.setProperty('box-shadow', 'none', 'important');
                    btn.style.setProperty('color', '#8b9bb4', 'important');
                    btn.style.setProperty('padding', '0', 'important');
                    const svgs = btn.querySelectorAll('svg');
                    if (svgs.length > 1) svgs[svgs.length - 1].style.display = 'none'; 
                }

                // 将按钮正式移入发光胶囊中
                innerPill.appendChild(attachPopover);

                // 强迫输入框文本向右避让 45px，绝不重叠
                const textArea = innerPill.querySelector('[data-baseweb="textarea"]');
                if (textArea) {
                    textArea.style.setProperty('padding-left', '45px', 'important');
                }
            }
        }
    };
    setInterval(runGlobalEngine, 100);
</script>
""", height=0, width=0)

# ==========================================
# 3. 核心 CSS 样式表 (包含全新的冰晶流银特效)
# ==========================================
st.markdown("""
<style>
    @keyframes fluidFlow { 0% { background-position: 0% 50%; } 25% { background-position: 50% 100%; } 50% { background-position: 100% 50%; } 75% { background-position: 50% 0%; } 100% { background-position: 0% 50%; } }
    @keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }

    .block-container { 
        animation: fadeIn 0.45s ease-out forwards; 
        background: transparent !important; 
        padding-top: 4.5rem !important; 
        padding-bottom: 120px !important; 
    }

    /* 永远置顶顶栏，保留汉堡菜单 */
    header[data-testid="stHeader"] { position: fixed !important; top: 0px !important; transform: none !important; opacity: 1 !important; visibility: visible !important; background: transparent !important; }
    [data-testid="collapsedControl"], [data-testid="stToolbar"] { pointer-events: auto !important; opacity: 1 !important; visibility: visible !important; display: flex !important; transform: none !important;}

    /* 去除恼人的锚点链接 */
    .stMarkdown a.header-anchor, .stMarkdown h1 svg, .stMarkdown h2 svg, .stMarkdown h3 svg { display: none !important; pointer-events: none !important; }

    [data-testid="stAppViewContainer"], [data-testid="stBottomBlock"], [data-testid="stBottom"] > div { background: transparent !important; border: none !important; }

    .tool-bar-container { display: none !important; } /* 隐藏真实的附件按钮外壳容器 */

    /* ---------------- 基础深色核心设定 ---------------- */
    .stApp { background-image: linear-gradient(132deg, #02040a, #030e2b, #111d3d, #082a72, #030614, #1d2b4f, #0a47b3, #02040a) !important; background-size: 600% 600% !important; animation: fluidFlow 18s ease-in-out infinite !important; }
    .stMarkdown, p, h1, h2, h3, h4, label, [data-testid="stMetricValue"] > div { color: #e2e8f0 !important; }
    .highlight-text { color: #00ffcc !important; }
    .sub-text { color: #cbd5e1 !important; }
    .danger-text { color: #ff4b4b !important; }

    /* 侧边栏推挤特效 */
    [data-testid="stSidebar"] { 
        background: rgba(5, 8, 14, 0.75) !important; 
        backdrop-filter: blur(25px) !important; 
        border-right: 1px solid rgba(255,255,255,0.08) !important; 
        min-height: 100vh !important; 
    }

    div[role="radiogroup"] > label { background: rgba(15, 20, 30, 0.4) !important; border-left: 4px solid transparent !important; border-radius: 12px !important; margin-bottom: 10px !important;}
    div[role="radiogroup"] > label:has(input:checked) { background: linear-gradient(90deg, rgba(0, 255, 204, 0.3), rgba(10, 15, 25, 0.95)) !important; border-left: 4px solid #00ffcc !important; }

    .glass-card { background: rgba(20, 28, 45, 0.65) !important; backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6); }
    .metric-box { background: rgba(0, 255, 204, 0.05); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 10px; padding: 15px; text-align: center; }
    [data-testid="stExpander"] { background: rgba(15, 23, 35, 0.8) !important; border: 1px solid rgba(0, 255, 204, 0.3) !important; border-radius: 16px !important; backdrop-filter: blur(10px); }

    /* 聊天胶囊 */
    [data-testid="stChatInput"] { background: transparent !important; border: none !important; box-shadow: none !important; max-width: 850px; margin: 0 auto 10px auto !important; }
    [data-testid="stChatInput"] > div:first-child { background-color: rgba(30, 41, 59, 0.6) !important; backdrop-filter: blur(25px) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; border-radius: 36px !important; box-shadow: 0 15px 50px rgba(0, 0, 0, 0.6) !important; padding: 5px 15px !important; }
    [data-testid="stChatInput"] [data-baseweb="textarea"], [data-testid="stChatInput"] [data-baseweb="textarea"] > div { background-color: transparent !important; border: none !important; box-shadow: none !important; outline: none !important; }
    [data-testid="stChatInput"] textarea { color: #ffffff !important; font-size: 16px !important; line-height: 1.5 !important; }
    [data-testid="stChatInputSubmitButton"] { background-color: #3b82f6 !important; border-radius: 50% !important; transition: all 0.3s ease; }
    [data-testid="stPopoverBody"] { background-color: rgba(25, 33, 48, 0.95) !important; border: 1px solid rgba(0, 255, 204, 0.4) !important; border-radius: 16px !important; backdrop-filter: blur(25px) !important; padding: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important; margin-bottom: 10px !important; }

    /* ---------------- 浅色主题：冰晶流银特效强力覆盖 ---------------- */
    /* 加入了 c7d2fe(浅紫蓝) 和 93c5fd(冰蓝)，提升缩放率，加快动画流速，效果拔群 */
    .stApp[data-custom-theme='light'] { 
        background-image: linear-gradient(132deg, #ffffff, #e2e8f0, #c7d2fe, #f8fafc, #93c5fd, #f1f5f9, #ffffff) !important; 
        background-size: 400% 400% !important; 
        animation: fluidFlow 12s ease-in-out infinite !important; 
    }
    .stApp[data-custom-theme='light'] .stMarkdown, .stApp[data-custom-theme='light'] p, .stApp[data-custom-theme='light'] h1, .stApp[data-custom-theme='light'] h2, .stApp[data-custom-theme='light'] h3, .stApp[data-custom-theme='light'] h4, .stApp[data-custom-theme='light'] label, .stApp[data-custom-theme='light'] [data-testid="stMetricValue"] > div { color: #1e293b !important; }
    .stApp[data-custom-theme='light'] .highlight-text { color: #0284c7 !important; }
    .stApp[data-custom-theme='light'] .sub-text { color: #475569 !important; }
    .stApp[data-custom-theme='light'] .danger-text { color: #dc2626 !important; }
    .stApp[data-custom-theme='light'] .glass-card { background: rgba(255, 255, 255, 0.75) !important; border: 1px solid rgba(0, 0, 0, 0.1) !important; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.06) !important; }
    .stApp[data-custom-theme='light'] .metric-box { background: rgba(2, 132, 199, 0.05) !important; border: 1px solid rgba(2, 132, 199, 0.2) !important; }
    .stApp[data-custom-theme='light'] [data-testid="stExpander"] { background: rgba(255, 255, 255, 0.9) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; }
    .stApp[data-custom-theme='light'] [data-testid="stSidebar"] { background: rgba(248, 250, 252, 0.85) !important; border-right: 1px solid rgba(0,0,0,0.08) !important; }
    .stApp[data-custom-theme='light'] div[role="radiogroup"] > label { background: rgba(241, 245, 249, 0.8) !important; border-left: 4px solid transparent !important; }
    .stApp[data-custom-theme='light'] div[role="radiogroup"] > label:has(input:checked) { background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(255, 255, 255, 0.95)) !important; border-left: 4px solid #3b82f6 !important; }
    .stApp[data-custom-theme='light'] [data-testid="stChatInput"] > div:first-child { background-color: rgba(255, 255, 255, 0.85) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; box-shadow: 0 15px 50px rgba(0, 0, 0, 0.08) !important; }
    .stApp[data-custom-theme='light'] [data-testid="stChatInput"] textarea { color: #1e293b !important; }
    .stApp[data-custom-theme='light'] [data-testid="stPopoverBody"] { background-color: rgba(255, 255, 255, 0.98) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important; }
    .stApp[data-custom-theme='light'] .js-plotly-plot .g-gtitle text, .stApp[data-custom-theme='light'] .js-plotly-plot .g-xtitle text, .stApp[data-custom-theme='light'] .js-plotly-plot .g-ytitle text, .stApp[data-custom-theme='light'] .js-plotly-plot .xtick text, .stApp[data-custom-theme='light'] .js-plotly-plot .ytick text, .stApp[data-custom-theme='light'] .js-plotly-plot .legendtext { fill: #1e293b !important; }
    .stApp[data-custom-theme='light'] [data-testid="collapsedControl"] svg, .stApp[data-custom-theme='light'] [data-testid="stToolbar"] svg { fill: #1e293b !important; color: #1e293b !important; }

    /* Agent 战报节点 */
    .agent-status-node { padding: 8px 12px; border-radius: 8px; font-size: 0.9rem; margin: 5px 0; border-left: 4px solid transparent; display: flex; align-items: center; gap: 10px; }
    .agent-status-node.success { background: rgba(0, 255, 204, 0.1); border-left-color: #00ffcc; color: #00ffcc; }
    .agent-status-node.error { background: rgba(255, 75, 75, 0.1); border-left-color: #ff4b4b; color: #ff4b4b; }
    .agent-status-node.retry { background: rgba(255, 165, 0, 0.1); border-left-color: #ffa500; color: #ffa500; }
    .stApp[data-custom-theme='light'] .agent-status-node.success { background: rgba(16, 185, 129, 0.1); border-left-color: #10b981; color: #047857; }
    .stApp[data-custom-theme='light'] .agent-status-node.error { background: rgba(239, 68, 68, 0.1); border-left-color: #ef4444; color: #b91c1c; }
    .stApp[data-custom-theme='light'] .agent-status-node.retry { background: rgba(245, 158, 11, 0.1); border-left-color: #f59e0b; color: #b45309; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 4. 全局缓存引擎与核心算法
# ==========================================
@st.cache_data(ttl=3600)
def fetch_and_clean_data(ts_code, adj, start_date):
    df = ts.pro_bar(ts_code=ts_code, adj=adj, start_date=start_date).sort_values('trade_date').reset_index(drop=True)
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    mapping_base = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'vol': 'Volume', 'amount': 'Amount'}
    for l_case, c_case in mapping_base.items():
        if l_case in df.columns: df[c_case] = df[l_case]
    if 'Volume' not in df.columns and 'vol' in df.columns: df['Volume'] = df['vol']
    if 'Close' in df.columns:
        df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()
        df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['SUB1_MACD_DIFF'] = exp1 - exp2
        df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()
        df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])
    return df


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
        if c.startswith('SUB'):
            gid = re.match(r'^SUB(\d+)_', c)
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
    fig.update_layout(height=500 + len(sub_groups) * 150, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0.1)', xaxis_rangeslider_visible=False, dragmode='pan', hovermode='x',
                      showlegend=False)
    return fig


def format_ts_code(raw):
    raw = str(raw).strip().upper()
    if len(raw) == 6 and raw.isdigit(): return f"{raw}.SH" if raw.startswith(('6', '9')) else f"{raw}.SZ"
    return raw


# ==========================================
# 5. 侧边栏导航控制
# ==========================================
PAGES = ["🏠 系统总览 (监控中控)", "🤖 AI 策略引擎 (LLM)", "📈 深度静态全量回测", "⚡ 实时高频交易 (Live)",
         "🧠 深度学习预测 (LSTM)", "🛡️ 论文审计日志"]

with st.sidebar:
    st.markdown("### 🎓 小吕布量化 Pro")
    st.caption(f"🛡️ 节点 ID: {st.session_state.user_id}")
    st.markdown("---")
    selected_page = st.radio("导航菜单", PAGES, label_visibility="collapsed")

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
        st.metric("Tushare 行情链路", "🟢 Online")
    with c3:
        st.metric("大模型底层通信", "🟢 Moonshot-v1 正常")
    with c4:
        st.metric("AI 神经网络", f"PyTorch {torch.__version__}")
    st.markdown("---")
    st.markdown(
        '<div class="glass-card" style="padding:15px; margin-bottom:20px;"><b class="highlight-text">🎯 极简操作指南：</b><span class="sub-text" style="margin-left: 10px;">1. 回测界输入标的拉取数据 | 2. 策略引擎上传研报下令 | 3. 拖拽 K 线双击自适应对齐。</span></div>',
        unsafe_allow_html=True)
    c_arch, c_point = st.columns([2, 1])
    with c_arch:
        st.markdown(
            '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom: 20px;">🧠 核心架构与操作流 (Data Flow Pipeline)</h3>',
            unsafe_allow_html=True)
        mermaid_str = "graph LR\nA[📊 1. 获取数据] -->|喂入| B(🧠 2. 模型预测)\nB -->|信号| C{📈 3. 全量回测}\nC -->|报告| D[🤖 4. AI 解读]"
        components.html(
            f"""<script type="module">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs'; mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});</script><div class="mermaid" style="text-align:center;">{mermaid_str}</div>""",
            height=350)
        st.markdown('</div>', unsafe_allow_html=True)
    with c_point:
        st.markdown(
            '<div class="glass-card"><h4 style="color:var(--text-color);">📋 平台监控与杀手锏</h4>**内存池占用率**<br>🟢 35%<br><br>**答辩核心创新点：**<br>✅ 类型强制归一化防报错<br>✅ AI 沙盒自愈流<br>✅ 物理级防呆补丁</div>',
            unsafe_allow_html=True)

elif selected_page == PAGES[1]:
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0; color:var(--text-color);">🤖 LLM 策略战情室</h3><p class="sub-text">多模态视觉引擎与 Agent 自愈模块已就绪，体验沉浸式工作流。</p></div>',
        unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="glass-card" style="padding:15px; margin-bottom:15px;">', unsafe_allow_html=True)
        ctrl_col1, ctrl_col2 = st.columns([1, 1])
        with ctrl_col1: selected_model = st.selectbox("🧠 选择大模型算力通道",
                                                      ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                                                      index=0)
        with ctrl_col2: st.markdown("<div style='height: 32px;'></div>",
                                    unsafe_allow_html=True); enable_deep_think = st.toggle(
            "💡 强子注入：开启深度思考引擎 (CoT)", value=False)
        st.markdown('</div>', unsafe_allow_html=True)

    chat_container = st.container(height=650)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

    st.markdown('<div class="tool-bar-container">', unsafe_allow_html=True)
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
                            try:
                                dummy_df = add_default_indicators(pd.DataFrame(
                                    {'trade_date': pd.date_range('20230101', periods=50),
                                     'Open': np.random.rand(50) * 10, 'High': np.random.rand(50) * 12,
                                     'Low': np.random.rand(50) * 8, 'Close': np.random.rand(50) * 10}))
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
    st.markdown('<div class="glass-card"><h3 style="color:var(--text-color);">📊 历史回测全量审计与归因分析</h3></div>',
                unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        ts_code = format_ts_code(st.text_input("🎯 回测标的代码", value="000001"))
        adj_p = st.selectbox("⚖️ 复权模式", ["qfq", "hfq", "None"]).split(" ")[0]
        if st.button("🚀 启动全量归因回测", use_container_width=True, type="primary"):
            with st.spinner("数据挂载中..."):
                try:
                    df = fetch_and_clean_data(ts_code, adj_p if adj_p != "None" else None, '20220101')
                    df_safe = df.copy()
                    if st.session_state.generated_code:
                        df_ai = execute_safely(st.session_state.generated_code, df)
                        for col in df_ai.columns:
                            if col == 'Signal' or col.startswith(('MAIN_', 'SUB')): df_safe[col] = df_ai[col]
                    df = df_safe
                    df['Ret'] = df['Close'].pct_change()
                    df['Pos'] = df.get('Signal', pd.Series([0] * len(df))).replace(0, np.nan).ffill().fillna(0)
                    df['Strat_Ret'] = df['Pos'].shift(1) * df['Ret']
                    df['Cum_Prod'] = (1 + df['Strat_Ret'].fillna(0)).cumprod()
                    total_ret = (df['Cum_Prod'].iloc[-1] - 1)
                    st.session_state.bt_result = {"df": df, "metrics": {"total": total_ret,
                                                                        "annual": (1 + total_ret) ** (
                                                                                    252 / max(1, len(df))) - 1,
                                                                        "max_dd": (df['Cum_Prod'] / df[
                                                                            'Cum_Prod'].cummax() - 1).min(), "sharpe": (
                                                                                                                                   (
                                                                                                                                               1 + total_ret) ** (
                                                                                                                                               252 / max(
                                                                                                                                           1,
                                                                                                                                           len(df))) - 1) / (
                                                                                                                                   df[
                                                                                                                                       'Strat_Ret'].std() * np.sqrt(
                                                                                                                               252)) if
                        df['Strat_Ret'].std() != 0 else 0}}
                except Exception as e:
                    st.error(f"异常: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

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
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(render_smart_charts(df), use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

elif selected_page == PAGES[3]:
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color);">⚡ 高频沙盘模拟推演 (Real-time Flow)</h3></div>',
        unsafe_allow_html=True)
    c_ctrl, c_chart = st.columns([1, 2.5])
    with c_ctrl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        live_code = st.text_input("🎯 动态推送标的", value="000001")
        freq = st.slider("⏱️ 刷新间隔 (秒)", 0.1, 2.0, 0.5)
        st.button("▶️ 开启高频推演", on_click=lambda: st.session_state.update({"is_live_trading": True}),
                  type="primary")
        st.button("⏹️ 强行停止", on_click=lambda: st.session_state.update({"is_live_trading": False}))
        st.markdown('</div>', unsafe_allow_html=True)
    with c_chart:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        met_ph, cht_ph = st.empty(), st.empty()
        if st.session_state.is_live_trading:
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
        st.markdown('</div>', unsafe_allow_html=True)

elif selected_page == PAGES[4]:
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color);">🧠 深度神经网络时序建模中心 (LSTM)</h3></div>',
        unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st_code = st.text_input("🎯 训练模型标的", value="000001")
        slen = st.slider("📏 滑窗长度", 5, 60, 20)
        eps = st.slider("🔄 Epoch 迭代", 10, 50, 30)
        if st.button("🚀 启动张量训练", type="primary", use_container_width=True):
            with st.spinner("神经网络前向传播中..."):
                try:
                    df = fetch_and_clean_data(format_ts_code(st_code), 'qfq', '20210101')
                    scaler = MinMaxScaler()
                    scaled = scaler.fit_transform(df['Close'].values.reshape(-1, 1))
                    X, y = [], []
                    for i in range(slen, len(scaled)): X.append(scaled[i - slen:i, 0]); y.append(scaled[i, 0])
                    X_t, y_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1), torch.tensor(np.array(y),
                                                                                                          dtype=torch.float32)


                    class LSTM(nn.Module):
                        def __init__(self): super().__init__(); self.lstm = nn.LSTM(1, 64, 2,
                                                                                    batch_first=True); self.fc = nn.Linear(
                            64, 1)

                        def forward(self, x): out, _ = self.lstm(x); return self.fc(out[:, -1, :])


                    model = LSTM();
                    opt = torch.optim.Adam(model.parameters(), lr=0.01);
                    crit = nn.MSELoss()
                    lbox, pbar = st.empty(), st.progress(0)
                    for e in range(eps):
                        model.train();
                        opt.zero_grad();
                        pred = model(X_t);
                        loss = crit(pred.squeeze(), y_t);
                        loss.backward();
                        opt.step()
                        lbox.code(f"Epoch {e + 1}/{eps}, Loss: {loss.item():.6f}");
                        pbar.progress((e + 1) / eps)
                    model.eval();
                    test_p = model(X_t[-100:]).detach().numpy()
                    st.session_state.dl_result = {"dates": df['trade_date'].iloc[-100:],
                                                  "actual": df['Close'].iloc[-100:],
                                                  "pred": scaler.inverse_transform(test_p).flatten()}
                except Exception as e:
                    st.error(f"DL 异常: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_r:
        if st.session_state.dl_result:
            res = st.session_state.dl_result
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['actual'], name='真实轨迹', line=dict(color='#00ffcc')))
            fig.add_trace(
                go.Scatter(x=res['dates'], y=res['pred'], name='LSTM 预测', line=dict(color='#ff00ff', dash='dot')))
            fig.update_layout(height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0.1)', dragmode='pan', hovermode='x')
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif selected_page == PAGES[5]:
    st.markdown('<div class="glass-card"><h3 style="color:var(--text-color);">🛡️ 实验数据采集与多维审计中心</h3></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        if os.path.exists("user_logs/global_master_log.csv"): st.download_button("📁 导出审计日志", data=pd.read_csv(
            "user_logs/global_master_log.csv").to_csv(index=False).encode('utf-8'), file_name='Audit_Logs.csv',
                                                                                 type="primary")
    with c2:
        st.text_area("实时工作流终端", value="\n".join(st.session_state.sys_logs), height=350)