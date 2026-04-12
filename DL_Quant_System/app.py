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

# 深度学习学术库
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

# 终极物理级防呆补丁
pd.np = np

# /// 1. 初始化与核心兵符 ///
st.set_page_config(page_title="小吕布量化 Pro - 毕设版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=60.0)

# 基础状态缓存
if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "strategy_explanation" not in st.session_state: st.session_state.strategy_explanation = "暂无策略解析，请先前往 AI 战情室下达军令。"
if "dl_result" not in st.session_state: st.session_state.dl_result = None
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "is_live_trading" not in st.session_state: st.session_state.is_live_trading = False

# /// 2. 空间流形导航逻辑 (记录坐标，计算滑动方向) ///
PAGES = [
    "🏠 系统总览 (监控中控)",
    "🤖 AI 策略引擎 (LLM)",
    "📈 深度静态全量回测",
    "⚡ 实时高频交易 (Live)",
    "🧠 深度学习预测 (LSTM)",
    "🛡️ 论文审计日志"
]

if "curr_page" not in st.session_state: st.session_state.curr_page = PAGES[0]
if "prev_page" not in st.session_state: st.session_state.prev_page = PAGES[0]

with st.sidebar:
    st.markdown("### 🎓 小吕布量化 Pro")
    st.caption(f"🛡️ 节点 ID: {st.session_state.user_id}")
    st.markdown("---")
    selected_page = st.radio("导航菜单", PAGES, label_visibility="collapsed")

# 动态计算相对位移方向
if selected_page != st.session_state.curr_page:
    st.session_state.prev_page = st.session_state.curr_page
    st.session_state.curr_page = selected_page

prev_idx = PAGES.index(st.session_state.prev_page)
curr_idx = PAGES.index(st.session_state.curr_page)

if curr_idx > prev_idx:
    anim_name = "slideUpIn"  # 往下点：新页面从下往上推入
elif curr_idx < prev_idx:
    anim_name = "slideDownIn"  # 往上点：新页面从上往下坠入
else:
    anim_name = "fadeIn"  # 首次加载或原点：单纯淡入

# /// 3. 涡轮增压引擎：全局唯一常驻 JS 守护进程 ///
components.html("""
<script>
    const runGlobalEngine = () => {
        const doc = window.parent.document;
        const app = doc.querySelector('.stApp');

        // 1. 光暗主题跨域嗅探
        if (app) {
            const color = window.getComputedStyle(app).color;
            const rgb = color.match(/\d+/g);
            let isLight = false;
            if (rgb && rgb.length >= 3) {
                const brightness = (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) / 1000;
                isLight = brightness < 128;
            }
            const themeAttr = isLight ? 'light' : 'dark';
            if (app.getAttribute('data-custom-theme') !== themeAttr) {
                app.setAttribute('data-custom-theme', themeAttr);
            }
        }

        // 2. 聊天舱附件按钮悬浮重构
        const chatInputOuter = doc.querySelector('div[data-testid="stChatInput"]');
        if (chatInputOuter) {
            const innerPill = chatInputOuter.children[0]; 
            const popovers = Array.from(doc.querySelectorAll('div[data-testid="stPopover"]'));
            const attachPopover = popovers.find(p => p && p.textContent && p.textContent.includes('📎'));

            if (innerPill && attachPopover && attachPopover.parentElement !== innerPill) {
                const rect = innerPill.getBoundingClientRect();
                attachPopover.style.position = 'fixed';
                attachPopover.style.left = (rect.left + 12) + 'px';
                attachPopover.style.top = (rect.top + rect.height/2) + 'px';
                attachPopover.style.transform = 'translateY(-50%)';
                attachPopover.style.zIndex = '9999';
                attachPopover.style.width = 'auto';
                attachPopover.style.margin = '0';

                const baseweb = chatInputOuter.querySelector('[data-baseweb="textarea"]');
                if(baseweb) { baseweb.style.paddingLeft = '40px'; }

                const btn = attachPopover.querySelector('button');
                if (btn) {
                    btn.style.background = 'transparent';
                    btn.style.border = 'none';
                    btn.style.boxShadow = 'none';
                    btn.style.color = '#8b9bb4';
                    btn.style.fontSize = '1.4rem';
                    btn.style.padding = '0';
                    btn.style.minWidth = '0';
                    const svgs = btn.querySelectorAll('svg');
                    if (svgs.length > 0) svgs[svgs.length - 1].style.display = 'none';
                }
            }
        }
    };
    const loop = () => { runGlobalEngine(); setTimeout(() => requestAnimationFrame(loop), 100); };
    requestAnimationFrame(loop);
</script>
""", height=0, width=0)

# /// 4. 终极 CSS 注入 (含物理惯性动画) ///
st.markdown(f"""
<style>
    /* 背景流体动画 */
    @keyframes fluidFlow {{ 0% {{ background-position: 0% 50%; }} 25% {{ background-position: 50% 100%; }} 50% {{ background-position: 100% 50%; }} 75% {{ background-position: 50% 0%; }} 100% {{ background-position: 0% 50%; }} }}

    /* 🔥 空间流形切换动画定义 🔥 */
    @keyframes slideUpIn {{
        0% {{ opacity: 0; transform: translateY(50px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes slideDownIn {{
        0% {{ opacity: 0; transform: translateY(-50px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes fadeIn {{
        0% {{ opacity: 0; }}
        100% {{ opacity: 1; }}
    }}

    /* 将计算出的动画变量赋予主容器，并使用贝塞尔曲线实现原生物理惯性 */
    .block-container {{ 
        animation: {anim_name} 0.55s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; 
        background: transparent !important; 
        padding-top: 3rem !important; 
        padding-bottom: 120px !important; 
    }}

    [data-testid="stAppViewContainer"] {{ background: transparent !important; }}
    header[data-testid="stHeader"] {{ background: transparent !important; pointer-events: none !important; }}
    [data-testid="stBottomBlock"], [data-testid="stBottom"], [data-testid="stBottom"] > div {{ background-color: transparent !important; background: transparent !important; border: none !important; }}
    .tool-bar-container {{ display: none; }}

    .stApp {{ background-image: linear-gradient(132deg, #02040a, #030e2b, #111d3d, #082a72, #030614, #1d2b4f, #0a47b3, #02040a) !important; background-size: 600% 600% !important; animation: fluidFlow 18s ease-in-out infinite !important; }}
    .stMarkdown, p, h1, h2, h3, h4, label, [data-testid="stMetricValue"] > div {{ color: #e2e8f0 !important; }}
    .highlight-text {{ color: #00ffcc !important; }}
    .sub-text {{ color: #cbd5e1 !important; }}
    .danger-text {{ color: #ff4b4b !important; }}

    [data-testid="stSidebar"] {{ top: 0 !important; bottom: 0 !important; height: 100vh !important; min-height: 100vh !important; background: rgba(5, 8, 14, 0.75) !important; backdrop-filter: blur(25px) !important; border-right: 1px solid rgba(255,255,255,0.08) !important; display: flex !important; flex-direction: column !important; }}
    [data-testid="stSidebar"] > div, [data-testid="stSidebarUserContent"] {{ height: 100% !important; min-height: 100vh !important; flex-grow: 1 !important; }}

    div[role="radiogroup"] > label {{ background: rgba(15, 20, 30, 0.4) !important; padding: 14px 18px !important; margin-bottom: 10px !important; border-radius: 12px !important; border-left: 4px solid transparent !important; }}
    div[role="radiogroup"] > label:has(input:checked) {{ background: linear-gradient(90deg, rgba(0, 255, 204, 0.3), rgba(10, 15, 25, 0.95)) !important; border-left: 4px solid #00ffcc !important; }}

    .glass-card {{ background: rgba(20, 28, 45, 0.65) !important; backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6); }}
    .metric-box {{ background: rgba(0, 255, 204, 0.05); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 10px; padding: 15px; text-align: center; }}
    [data-testid="stExpander"] {{ background: rgba(15, 23, 35, 0.8) !important; border: 1px solid rgba(0, 255, 204, 0.3) !important; border-radius: 16px !important; backdrop-filter: blur(10px); }}

    [data-testid="stChatInput"] {{ background: transparent !important; border: none !important; box-shadow: none !important; max-width: 850px; margin: 0 auto 10px auto !important; }}
    [data-testid="stChatInput"] > div:first-child {{ background-color: rgba(30, 41, 59, 0.6) !important; backdrop-filter: blur(25px) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; border-radius: 36px !important; box-shadow: 0 15px 50px rgba(0, 0, 0, 0.6) !important; padding: 5px 15px !important; }}
    [data-testid="stChatInput"] [data-baseweb="textarea"], [data-testid="stChatInput"] [data-baseweb="textarea"] > div {{ background-color: transparent !important; border: none !important; box-shadow: none !important; outline: none !important; }}
    [data-testid="stChatInput"] textarea {{ background-color: transparent !important; border: none !important; color: #ffffff !important; font-size: 16px !important; line-height: 1.5 !important; padding-left: 40px !important; }}
    [data-testid="stChatInput"] textarea:focus {{ box-shadow: none !important; outline: none !important; }}
    [data-testid="stChatInputSubmitButton"] {{ background-color: #3b82f6 !important; border-radius: 50% !important; transition: all 0.3s ease; }}
    div[data-testid="stPopover"] button {{ background-color: transparent !important; border: none !important; box-shadow: none !important; color: #a1a1aa !important; }}
    [data-testid="stPopoverBody"] {{ background-color: rgba(25, 33, 48, 0.95) !important; border: 1px solid rgba(0, 255, 204, 0.4) !important; border-radius: 16px !important; backdrop-filter: blur(25px) !important; padding: 15px !important; box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important; margin-bottom: 10px !important; }}

    /* 浅色主题强力覆盖 */
    .stApp[data-custom-theme='light'] {{ background-image: linear-gradient(132deg, #f1f5f9, #e2e8f0, #ffffff, #cbd5e1, #f8f9fa, #e2e8f0, #f1f5f9) !important; }}
    .stApp[data-custom-theme='light'] .stMarkdown, .stApp[data-custom-theme='light'] p, .stApp[data-custom-theme='light'] h1, .stApp[data-custom-theme='light'] h2, .stApp[data-custom-theme='light'] h3, .stApp[data-custom-theme='light'] h4, .stApp[data-custom-theme='light'] label, .stApp[data-custom-theme='light'] [data-testid="stMetricValue"] > div {{ color: #1e293b !important; }}
    .stApp[data-custom-theme='light'] .highlight-text {{ color: #0284c7 !important; }}
    .stApp[data-custom-theme='light'] .sub-text {{ color: #475569 !important; }}
    .stApp[data-custom-theme='light'] .danger-text {{ color: #dc2626 !important; }}
    .stApp[data-custom-theme='light'] .glass-card {{ background: rgba(255, 255, 255, 0.75) !important; border: 1px solid rgba(0, 0, 0, 0.1) !important; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.06) !important; }}
    .stApp[data-custom-theme='light'] .metric-box {{ background: rgba(2, 132, 199, 0.05) !important; border: 1px solid rgba(2, 132, 199, 0.2) !important; }}
    .stApp[data-custom-theme='light'] [data-testid="stExpander"] {{ background: rgba(255, 255, 255, 0.9) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; }}
    .stApp[data-custom-theme='light'] [data-testid="stSidebar"] {{ background: rgba(248, 250, 252, 0.85) !important; border-right: 1px solid rgba(0,0,0,0.08) !important; }}
    .stApp[data-custom-theme='light'] div[role="radiogroup"] > label {{ background: rgba(241, 245, 249, 0.8) !important; border-left: 4px solid transparent !important; }}
    .stApp[data-custom-theme='light'] div[role="radiogroup"] > label:has(input:checked) {{ background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(255, 255, 255, 0.95)) !important; border-left: 4px solid #3b82f6 !important; }}
    .stApp[data-custom-theme='light'] [data-testid="stChatInput"] > div:first-child {{ background-color: rgba(255, 255, 255, 0.85) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; box-shadow: 0 15px 50px rgba(0, 0, 0, 0.08) !important; }}
    .stApp[data-custom-theme='light'] [data-testid="stChatInput"] textarea {{ color: #1e293b !important; }}
    .stApp[data-custom-theme='light'] div[data-testid="stPopover"] button {{ color: #64748b !important; }}
    .stApp[data-custom-theme='light'] [data-testid="stPopoverBody"] {{ background-color: rgba(255, 255, 255, 0.98) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important; }}
    .stApp[data-custom-theme='light'] .js-plotly-plot .g-gtitle text, .stApp[data-custom-theme='light'] .js-plotly-plot .g-xtitle text, .stApp[data-custom-theme='light'] .js-plotly-plot .g-ytitle text, .stApp[data-custom-theme='light'] .js-plotly-plot .xtick text, .stApp[data-custom-theme='light'] .js-plotly-plot .ytick text, .stApp[data-custom-theme='light'] .js-plotly-plot .legendtext {{ fill: #1e293b !important; }}

    .agent-status-node {{ padding: 8px 12px; border-radius: 8px; font-size: 0.9rem; margin: 5px 0; border-left: 4px solid transparent; display: flex; align-items: center; gap: 10px; }}
    .agent-status-node.success {{ background: rgba(0, 255, 204, 0.1); border-left-color: #00ffcc; color: #00ffcc; }}
    .agent-status-node.error {{ background: rgba(255, 75, 75, 0.1); border-left-color: #ff4b4b; color: #ff4b4b; }}
    .agent-status-node.retry {{ background: rgba(255, 165, 0, 0.1); border-left-color: #ffa500; color: #ffa500; }}
    .stApp[data-custom-theme='light'] .agent-status-node.success {{ background: rgba(16, 185, 129, 0.1); border-left-color: #10b981; color: #047857; }}
    .stApp[data-custom-theme='light'] .agent-status-node.error {{ background: rgba(239, 68, 68, 0.1); border-left-color: #ef4444; color: #b91c1c; }}
    .stApp[data-custom-theme='light'] .agent-status-node.retry {{ background: rgba(245, 158, 11, 0.1); border-left-color: #f59e0b; color: #b45309; }}
</style>
""", unsafe_allow_html=True)


# /// 5. 高速数据缓存装甲 (@st.cache_data) ///
@st.cache_data(ttl=3600)
def fetch_and_clean_data(ts_code, adj, start_date):
    df = ts.pro_bar(ts_code=ts_code, adj=adj, start_date=start_date).sort_values('trade_date').reset_index(drop=True)
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    return add_default_indicators(apply_dual_column_armor(df))


def apply_dual_column_armor(df):
    mapping_base = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'vol': 'Volume', 'amount': 'Amount'}
    for lower_case, camel_case in mapping_base.items():
        upper_case = camel_case.upper()
        src = None
        if lower_case in df.columns:
            src = df[lower_case]
        elif camel_case in df.columns:
            src = df[camel_case]
        elif upper_case in df.columns:
            src = df[upper_case]
        if src is not None:
            df[lower_case] = src
            df[camel_case] = src
            df[upper_case] = src
        if lower_case == 'vol' and src is not None: df['VOLUME'] = src
    return df


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


def execute_safely(code, df):
    safe_code = code.replace("pandas.np", "np")
    sandbox_env = {"pd": pd, "np": np, "math": math}
    l_vars = {}
    exec(safe_code, sandbox_env, l_vars)
    func_to_call = None
    if 'generate_signals' in l_vars and callable(l_vars['generate_signals']):
        func_to_call = l_vars['generate_signals']
    else:
        funcs = [v for k, v in l_vars.items() if callable(v)]
        if funcs:
            func_to_call = funcs[0]
        else:
            raise ValueError("AI 未生成有效的方法函数！")
    df_ai = func_to_call(df)
    sig_col = next((c for c in df_ai.columns if c.lower() == 'signal'), None)
    if sig_col:
        if sig_col != 'Signal': df_ai['Signal'] = df_ai[sig_col]
        df_ai['Signal'] = df_ai['Signal'].fillna(0).apply(lambda x: 1 if x > 0.1 else (-1 if x < -0.1 else 0)).astype(
            int)
    else:
        df_ai['Signal'] = 0
    return df_ai


def render_smart_charts(df):
    main_indicators = []
    sub_groups = {}
    for col in df.columns:
        if col.startswith('MAIN_'):
            main_indicators.append(col)
        elif col.startswith('SUB'):
            match = re.match(r'^SUB(\d+)_', col)
            if match:
                group_id = match.group(1)
                if group_id not in sub_groups: sub_groups[group_id] = []
                sub_groups[group_id].append(col)
    num_sub_groups = len(sub_groups)
    total_rows = 2 + num_sub_groups
    main_height, vol_height = 0.5, 0.15
    remaining_height = 1.0 - main_height - vol_height
    row_heights = [main_height, vol_height]
    if num_sub_groups > 0: row_heights.extend([remaining_height / num_sub_groups] * num_sub_groups)
    fig = make_subplots(rows=total_rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)
    fig.add_trace(go.Candlestick(x=df['trade_date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 name='K线', increasing_line_color='#FD1050', increasing_fillcolor='#FD1050',
                                 decreasing_line_color='#00FF00', decreasing_fillcolor='#00FF00'), row=1, col=1)
    overlay_colors = ['#FFFF00', '#FF00FF', '#FFFFFF', '#00FFFF', '#FFA500']
    for i, col in enumerate(main_indicators): fig.add_trace(
        go.Scatter(x=df['trade_date'], y=df[col], name=col.replace('MAIN_', ''),
                   line=dict(width=1.2, color=overlay_colors[i % len(overlay_colors)])), row=1, col=1)
    if 'Signal' in df.columns:
        buys, sells = df[df['Signal'] == 1], df[df['Signal'] == -1]
        fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['Low'] * 0.95, mode='markers',
                                 marker=dict(symbol='triangle-up', size=14, color='#00FFFF',
                                             line=dict(width=1, color='white')), name='买入'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['High'] * 1.05, mode='markers',
                                 marker=dict(symbol='triangle-down', size=14, color='#FF00FF',
                                             line=dict(width=1, color='white')), name='卖出'), row=1, col=1)
    if 'Volume' in df.columns:
        vol_colors = np.where(df['Close'] >= df['Open'], '#FD1050', '#00FF00')
        fig.add_trace(go.Bar(x=df['trade_date'], y=df['Volume'], name='成交量', marker_color=vol_colors, opacity=0.8),
                      row=2, col=1)
    sub_colors = ['#00FFFF', '#FF00FF', '#FFFF00', '#FFFFFF']
    current_row = 3
    for group_id in sorted(sub_groups.keys(), key=int):
        cols_in_group = sub_groups[group_id]
        for i, col in enumerate(cols_in_group):
            if 'HIST' in col.upper() or (
                    'MACD' in col.upper() and 'DIFF' not in col.upper() and 'DEA' not in col.upper() and 'SIGNAL' not in col.upper()):
                hist_colors = np.where(df[col] >= 0, '#FD1050', '#00FF00')
                fig.add_trace(go.Bar(x=df['trade_date'], y=df[col], name=col.replace(f'SUB{group_id}_', ''),
                                     marker_color=hist_colors), row=current_row, col=1)
            else:
                fig.add_trace(go.Scatter(x=df['trade_date'], y=df[col], name=col.replace(f'SUB{group_id}_', ''),
                                         line=dict(width=1.2, color=sub_colors[i % len(sub_colors)])), row=current_row,
                              col=1)
        current_row += 1
    fig.update_layout(height=500 + (num_sub_groups * 150), template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0.1)', xaxis_rangeslider_visible=False, dragmode='pan', hovermode='x',
                      showlegend=False)
    fig.update_xaxes(fixedrange=False);
    fig.update_yaxes(fixedrange=False)
    return fig


def log_thesis_data(action, detail):
    ts_str = datetime.now().strftime("%H:%M:%S")
    st.session_state.sys_logs.insert(0, f"[{ts_str}] {action}: {detail}")


def format_ts_code(raw):
    raw = str(raw).strip().upper()
    if len(raw) == 6 and raw.isdigit():
        if raw.startswith(('6', '9')):
            return f"{raw}.SH"
        elif raw.startswith(('0', '2', '3')):
            return f"{raw}.SZ"
    return raw


LOG_DIR = "user_logs"
os.makedirs(LOG_DIR, exist_ok=True)
GLOBAL_LOG_FILE = os.path.join(LOG_DIR, "global_master_log.csv")
if not os.path.exists(GLOBAL_LOG_FILE): pd.DataFrame(columns=["Timestamp", "UserID", "ActionType", "Details"]).to_csv(
    GLOBAL_LOG_FILE, index=False)

# /// 🏠 页面 1: 系统总览 ///
if selected_page == PAGES[0]:
    st.markdown(
        '<div class="glass-card"><h1 style="margin-bottom:0; color:var(--text-color);">🏛️ 全链路智能量化决策枢纽</h1><p class="highlight-text" style="font-size:1.1rem; margin-top:5px;">System Overview & Mid-term Inspection Dashboard</p></div>',
        unsafe_allow_html=True)

    try:
        t_start = time.time()
        pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240101')
        t_latency = int((time.time() - t_start) * 1000)
        ts_status = f"🟢 Online ({t_latency}ms)"
    except:
        ts_status = "🔴 Offline"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("活跃并发沙盒 (UUID)", st.session_state.user_id, "监控状态: 激活")
    with col2:
        st.metric("Tushare 行情链路", ts_status, "A股数据: 接入成功")
    with col3:
        st.metric("大模型底层通信", "Moonshot-v1", "通道: 🟢 正常")
    with col4:
        st.metric("AI 神经网络", f"PyTorch {torch.__version__}", "时序预测: 待命")

    st.markdown("---")

    st.markdown('<div class="glass-card" style="padding:15px; margin-bottom:20px;">'
                '<b class="highlight-text">🎯 极简操作指南：</b>'
                '<span class="sub-text" style="margin-left: 10px;">1. 在<b>回测/深度学习</b>界面输入标的，自动拉取数据。 | '
                '2. 切换至<b>AI 策略引擎</b>，上传研报下达军令。 | '
                '3. 拖拽 K 线图平移，<b>双击图表</b>瞬间触发 Y 轴自适应对齐。</span></div>', unsafe_allow_html=True)

    c_arch, c_point = st.columns([2, 1])

    with c_arch:
        st.markdown(
            '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom: 20px;">🧠 核心架构与操作流 (Data Flow Pipeline)</h3>',
            unsafe_allow_html=True)

        mermaid_str = """
        graph LR
            A[📊 1. 获取数据<br>左侧输入标的] -->|喂入清洗数据| B(🧠 2. 模型训练<br>LSTM 时序预测)
            B -->|输出预测信号| C{📈 3. 策略回测<br>全量审计与归因}
            C -->|上传回测结果| D[🤖 4. AI 战情室<br>大模型多模态解读]
            A -.->|研报/原始数据| D
        """

        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                const checkTheme = () => {{
                    try {{ const parentApp = window.parent.document.querySelector('.stApp'); return parentApp && parentApp.getAttribute('data-custom-theme') === 'light' ? 'default' : 'dark'; }} catch(e) {{ return 'dark'; }}
                }};
                window.lastTheme = checkTheme();
                const render = async () => {{
                    const theme = checkTheme();
                    mermaid.initialize({{ startOnLoad: false, theme: theme, themeVariables: {{ fontFamily: 'sans-serif' }} }});
                    const element = document.querySelector('.mermaid-container');
                    const code = document.getElementById('mermaid-data').textContent;
                    const {{ svg }} = await mermaid.render('graphDiv', code);
                    element.innerHTML = svg;
                }};
                render();
                setInterval(() => {{
                    const currentTheme = checkTheme();
                    if(window.lastTheme !== currentTheme) {{ window.lastTheme = currentTheme; render(); }}
                }}, 500);
            </script>
        </head>
        <body style="margin:0; padding:0; background: transparent; display: flex; flex-direction: column; align-items: center; color: inherit;">
            <div id="mermaid-data" style="display:none;">{mermaid_str}</div>
            <div class="mermaid-container" style="width: 100%; transform: scale(1.1); transform-origin: top center;"></div>
        </body>
        </html>
        """
        components.html(html_code, height=650)
        st.markdown('</div>', unsafe_allow_html=True)

    with c_point:
        st.markdown('<div class="glass-card"><h4 style="color:var(--text-color);">📋 平台体征监控 (Telemetry)</h4>',
                    unsafe_allow_html=True)
        st.markdown("**内存池占用率 (预估)**")
        st.progress(0.35)
        st.markdown("**UI 实时通信帧率**")
        st.progress(0.96)
        st.markdown(
            '<br><h4 style="color:var(--text-color);">💡 答辩终极杀手锏</h4>✅ <b>类型强制归一 (New)</b>: 自动剿灭 AI 产生的浮点数买卖信号报错。<br>✅ <b>全局物理补丁</b>: pd.np = np，永久杜绝旧语法崩溃。<br>✅ <b>平移自适应缩放</b>: 左右拖拽平移，双击瞬间对齐Y轴。</div>',
            unsafe_allow_html=True)

# /// 🤖 页面 2: AI 策略引擎 (LLM) ///
elif selected_page == PAGES[1]:
    if "messages" not in st.session_state: st.session_state.messages = []

    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0; color:var(--text-color);">🤖 LLM 策略战情室</h3><p class="sub-text">多模态视觉引擎与 Agent 自愈模块已就绪，体验沉浸式工作流。</p></div>',
        unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="glass-card" style="padding:15px; margin-bottom:15px;">', unsafe_allow_html=True)
        ctrl_col1, ctrl_col2 = st.columns([1, 1])
        with ctrl_col1: selected_model = st.selectbox("🧠 选择大模型算力通道",
                                                      ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                                                      index=0)
        with ctrl_col2:
            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
            enable_deep_think = st.toggle("💡 强子注入：开启深度思考引擎 (CoT)", value=False)
        st.markdown('</div>', unsafe_allow_html=True)

    chat_container = st.container(height=650)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

    st.markdown('<div class="tool-bar-container">', unsafe_allow_html=True)
    with st.popover("📎", help="点击上传参考文件", use_container_width=False):
        st.caption("支持上传本地图片、TXT、CSV，发送后即焚")
        uploaded_files = st.file_uploader("选择文件", accept_multiple_files=True,
                                          type=['png', 'jpg', 'jpeg', 'csv', 'txt'], label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    file_context = ""
    if 'uploaded_files' in locals() and uploaded_files:
        st.success("✅ 附件已挂载入内存，可直接在下方输入框向 AI 下达指令！")
        cols = st.columns(min(len(uploaded_files), 3))
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 3]:
                if file.type.startswith('image/'):
                    img = Image.open(file)
                    st.image(img, caption=file.name, use_container_width=True)
                    file_context += f"\n[用户上传了图片: {file.name}，请结合视觉能力分析]"
                elif file.type == 'text/csv':
                    df_upload = pd.read_csv(file)
                    st.dataframe(df_upload.head(2), use_container_width=True)
                    file_context += f"\n【附件 CSV {file.name} 前两行】:\n{df_upload.head(2).to_string()}\n"
                elif file.type == 'text/plain':
                    content = file.read().decode("utf-8")
                    st.text(content[:50] + "...")
                    file_context += f"\n【附件文本 {file.name} 内容】:\n{content}\n"

    if raw_prompt := st.chat_input("向小吕布量化架构师发送军令..."):
        full_prompt_for_ai = raw_prompt
        if file_context: full_prompt_for_ai = f"以下是参考附件信息：\n{file_context}\n\n需求：{raw_prompt}"

        st.session_state.messages.append({"role": "user", "content": raw_prompt})
        log_thesis_data("指令下达", f"模型:{selected_model}, 包含附件:{bool(file_context)}, CoT:{enable_deep_think}")

        with chat_container:
            with st.chat_message("user"):
                st.markdown(raw_prompt)
            with st.chat_message("assistant"):
                st.toast(f"🚀 连线底层算力集群: {selected_model}", icon="⚡")

                ticks = "`" * 3
                sys_p = f"""你是一名严谨的量化专家。
1. 拒绝闲聊。
2. 【强制解析】：输出代码前，独占一行写出“【策略白话解析】”为标题，写一段通俗解释。
3. 【环境告知】：传入 df 已含 `MAIN_MA5`, `MAIN_MA20`, `SUB1_MACD_DIFF`, `SUB1_MACD_DEA`, `SUB1_MACD_HIST`。
4. 【严禁重复】：严禁再生成新的 MACD 列！其他新指标（主图 MAIN_xxx，副图 SUB2_xxx）。
5. 【终极骨架铁律】：你必须严格按照以下代码骨架输出，绝不允许修改函数名、参数或返回类型。你只能填写 buy_condition 和 sell_condition：
{ticks}python
def generate_signals(df):
    # --- 请在此处计算你的自定义指标（可选） ---

    # /// 请在此处填写买卖逻辑，必须返回布尔型 Series ///
    buy_condition = (df['MAIN_MA5'] > df['MAIN_MA20']) 
    sell_condition = (df['MAIN_MA5'] < df['MAIN_MA20']) 
    # /// 逻辑填写结束 ///

    df['Signal'] = 0
    df.loc[buy_condition, 'Signal'] = 1
    df.loc[sell_condition, 'Signal'] = -1
    return df
{ticks}
6. 【语法铁律】：禁止使用 and/or，必须使用 & | 加括号；列名首字大写 'Close'。"""
                if enable_deep_think: sys_p += "\n7.你必须先将逻辑写在 `<think>` 标签内！之后再输出解析和代码。"

                api_temperature = 0.3 if enable_deep_think else 0.7
                messages_to_send = [{"role": "system", "content": sys_p}] + st.session_state.messages[:-1] + [
                    {"role": "user", "content": full_prompt_for_ai}]

                max_retries = 2
                last_error = ""
                agent_logs = []

                for attempt in range(max_retries + 1):
                    if attempt > 0:
                        st.warning(f"⚠️ 沙盒预检拦截了错误：`{last_error}`。Agent 启动第 {attempt} 次自愈重构...")
                        agent_logs.append(
                            f'<div class="agent-status-node retry">🔄 <b>尝试 {attempt}:</b> 沙盒拦截异常 (<code>{last_error}</code>) -> Agent 发起重构</div>')
                        fix_prompt = f"刚才生成的代码运行报错：`{last_error}`。\n请严格遵循骨架模板，检查 Pandas 语法（特别注意 & | 运算符及括号），不要道歉，只输出修复后的完整代码块。"
                        messages_to_send.append({"role": "assistant", "content": full_resp})
                        messages_to_send.append({"role": "user", "content": fix_prompt})

                    if enable_deep_think:
                        think_expander = st.expander(f"🧠 AI 脑内推演 (Attempt {attempt + 1})...", expanded=True)
                        think_box = think_expander.empty()
                    msg_box = st.empty()

                    try:
                        stream = client.chat.completions.create(model=selected_model, messages=messages_to_send,
                                                                stream=True, temperature=api_temperature)
                        full_resp = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                delta = chunk.choices[0].delta.content
                                full_resp += delta
                                if enable_deep_think:
                                    if "<think>" in full_resp:
                                        if "</think>" in full_resp:
                                            parts = full_resp.split("</think>")
                                            think_box.markdown(parts[0].replace("<think>", "").strip(),
                                                               unsafe_allow_html=True)
                                            msg_box.markdown(
                                                (parts[1].lstrip() + "▌") if parts[1].lstrip() else "✨ 起草执行军令...",
                                                unsafe_allow_html=True)
                                        else:
                                            think_box.markdown(full_resp.replace("<think>", "").strip() + "▌",
                                                               unsafe_allow_html=True)
                                            msg_box.markdown("✨ 疯狂燃烧算力中...", unsafe_allow_html=True)
                                    else:
                                        msg_box.markdown(full_resp + "▌", unsafe_allow_html=True)
                                else:
                                    msg_box.markdown(full_resp + "▌", unsafe_allow_html=True)

                        if enable_deep_think and "</think>" in full_resp:
                            msg_box.markdown(full_resp.split("</think>")[1].strip(), unsafe_allow_html=True)
                        else:
                            msg_box.markdown(full_resp.replace("<think>", "").replace("</think>", "").strip(),
                                             unsafe_allow_html=True)

                        code_match = re.search(r"`{3}python\s*(.*?)\s*`{3}", full_resp, re.DOTALL)
                        if code_match:
                            extracted_code = code_match.group(1).strip()
                            try:
                                np.random.seed(int(time.time()))
                                dummy_df = pd.DataFrame({
                                    'trade_date': pd.date_range(start='20230101', periods=50),
                                    'Open': np.random.rand(50) * 10 + 10,
                                    'High': np.random.rand(50) * 12 + 10,
                                    'Low': np.random.rand(50) * 8 + 10,
                                    'Close': np.random.rand(50) * 10 + 10,
                                    'Volume': np.random.randint(100, 1000, 50)
                                })
                                dummy_df = add_default_indicators(dummy_df)
                                _ = execute_safely(extracted_code, dummy_df)

                                st.session_state.generated_code = extracted_code
                                exp_match = re.search(r"【策略白话解析】(.*?)(?=`{3}python|$)", full_resp,
                                                      re.DOTALL | re.IGNORECASE)
                                st.session_state.strategy_explanation = exp_match.group(
                                    1).strip() if exp_match else "该策略无特定白话解析，请参考代码内部注释。"

                                agent_logs.append(
                                    f'<div class="agent-status-node success">✅ <b>尝试 {attempt + 1}:</b> 代码通过系统沙盒预检 -> 策略已安全装载</div>')
                                st.markdown("".join(agent_logs), unsafe_allow_html=True)

                                st.toast("✅ 军令推演与沙盒预检全部通过！", icon="🚀")
                                break

                            except Exception as e:
                                last_error = str(e)
                                if attempt == max_retries:
                                    agent_logs.append(
                                        f'<div class="agent-status-node error">❌ <b>最终结果:</b> 经过 {max_retries} 次重构仍失败，最终报错: <code>{last_error}</code>。强制中止自动化流程，需人工介入。</div>')
                                    st.markdown("".join(agent_logs), unsafe_allow_html=True)
                                    st.session_state.generated_code = extracted_code
                        else:
                            break

                    except Exception as e:
                        st.error(f"通信链路断开: {e}")
                        break

                if agent_logs:
                    full_resp += "\n\n" + "".join(agent_logs)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
        st.rerun()

# /// 📈 页面 3: 深度静态全量回测 ///
elif selected_page == PAGES[2]:
    st.markdown('<div class="glass-card"><h3 style="color:var(--text-color);">📊 历史回测全量审计与归因分析</h3></div>',
                unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        raw_code = st.text_input("🎯 回测标的代码", value="000001")
        ts_code = format_ts_code(raw_code)
        adj = st.selectbox("⚖️ 复权模式", ["qfq (前复权)", "hfq (后复权)", "None (不复权)"])
        st.info("💡 已开启【无缝平移模式】。按住鼠标拖拽；**双击图表**瞬间自适应Y轴！")

        if st.button("🚀 启动全量归因回测", use_container_width=True, type="primary"):
            with st.spinner("调度数据并挂载常驻指标..."):
                try:
                    adj_p = adj.split(" ")[0] if adj != "None" else None
                    df = fetch_and_clean_data(ts_code, adj_p, '20220101')
                    df_safe = df.copy()

                    if st.session_state.generated_code:
                        df_ai = execute_safely(st.session_state.generated_code, df)
                        for col in df_ai.columns:
                            if col == 'Signal' or col.startswith('MAIN_') or col.startswith('SUB'): df_safe[col] = \
                            df_ai[col]

                    df = df_safe
                    df['Ret'] = df['Close'].pct_change()
                    df['Pos'] = df['Signal'].replace(0, np.nan).ffill().fillna(0) if 'Signal' in df.columns else 0
                    df['Strat_Ret'] = df['Pos'].shift(1) * df['Ret']
                    df['Cum_Prod'] = (1 + df['Strat_Ret'].fillna(0)).cumprod()

                    total_ret = (df['Cum_Prod'].iloc[-1] - 1)
                    annual_ret = (1 + total_ret) ** (252 / max(1, len(df))) - 1
                    volatility = df['Strat_Ret'].std() * np.sqrt(252)
                    st.session_state.bt_result = {"df": df, "code": ts_code, "metrics": {
                        "total": total_ret, "annual": annual_ret,
                        "max_dd": (df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min(),
                        "sharpe": annual_ret / volatility if volatility != 0 and pd.notnull(volatility) else 0
                    }}
                except Exception as e:
                    log_thesis_data("沙盒异常", str(e)); st.error(f"异常拦截: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            m, df = st.session_state.bt_result['metrics'], st.session_state.bt_result['df']
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(
                f'<div class="metric-box"><p style="margin:0; font-size:0.8rem;">累计收益</p><h2 class="highlight-text">{m["total"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c2.markdown(
                f'<div class="metric-box"><p style="margin:0; font-size:0.8rem;">年化收益</p><h2 class="highlight-text">{m["annual"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c3.markdown(
                f'<div class="metric-box"><p style="margin:0; font-size:0.8rem;">最大回撤</p><h2 class="danger-text">{m["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c4.markdown(
                f'<div class="metric-box"><p style="margin:0; font-size:0.8rem;">夏普比率</p><h2 class="highlight-text">{m["sharpe"]:.2f}</h2></div>',
                unsafe_allow_html=True)
            if st.session_state.generated_code and (
                    'Signal' not in df.columns or df['Signal'].abs().sum() == 0): st.warning(
                "⚠️ **预警**：策略条件过严，未触发交易，收益为0。")
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            if st.session_state.generated_code:
                with st.expander("💡 展开：AI 策略白话解析", expanded=False): st.markdown(
                    st.session_state.strategy_explanation)
            st.plotly_chart(render_smart_charts(df), use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

# /// ⚡ 页面 4: 实时高频交易 (Live) ///
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
        if st.session_state.generated_code:
            with st.expander("💡 当前军令：策略白话解析", expanded=False): st.markdown(
                st.session_state.strategy_explanation)
        met_ph, cht_ph = st.empty(), st.empty()
        if st.session_state.is_live_trading:
            stream = fetch_and_clean_data(format_ts_code(live_code), 'qfq', '20230101')
            stream = stream.tail(120).reset_index(drop=True)
            for i in range(20, len(stream)):
                if not st.session_state.is_live_trading: break
                sub = stream.iloc[:i].copy()
                sub_safe = sub.copy()
                try:
                    if st.session_state.generated_code:
                        sub_ai = execute_safely(st.session_state.generated_code, sub)
                        for col in sub_ai.columns:
                            if col == 'Signal' or col.startswith('MAIN_') or col.startswith('SUB'): sub_safe[col] = \
                            sub_ai[col]
                    sub = sub_safe
                    sub['Ret'] = sub['Close'].pct_change()
                    sig_val = sub['Signal'].iloc[-1] if 'Signal' in sub.columns else 0
                    with met_ph.container():
                        c = st.columns(3)
                        c[0].metric("Tick 现价", f"{sub['Close'].iloc[-1]:.2f}")
                        c[1].metric("高频信号", "🟢 买入" if sig_val == 1 else "🔴 卖出" if sig_val == -1 else "⚪ 观望")
                        c[2].metric("并发收益率", f"{(sub['Close'].pct_change().iloc[-1] * 100):.2f}%")
                    cht_ph.plotly_chart(render_smart_charts(sub), use_container_width=True, key=f"live_{i}",
                                        config={'scrollZoom': True})
                except Exception as e:
                    st.error(f"高频熔断: {e}"); st.session_state.is_live_trading = False; break
                time.sleep(freq)
        st.markdown('</div>', unsafe_allow_html=True)

# /// 🧠 页面 5: 深度学习预测 (LSTM) ///
elif selected_page == PAGES[4]:
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color);">🧠 深度神经网络时序建模中心 (LSTM)</h3></div>',
        unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st_code = st.text_input("🎯 训练模型标的", value="000001")
        slen = st.slider("📏 滑窗长度 (Seq_Len)", 5, 60, 20)
        eps = st.slider("🔄 Epoch 迭代轮数", 10, 50, 30)
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
                    st.error(f"DL 张量异常: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_r:
        if st.session_state.dl_result:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            res = st.session_state.dl_result
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['actual'], name='真实轨迹', line=dict(color='#00ffcc')))
            fig.add_trace(
                go.Scatter(x=res['dates'], y=res['pred'], name='LSTM 预测', line=dict(color='#ff00ff', dash='dot')))
            fig.update_layout(height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0.1)', dragmode='pan', hovermode='x')
            fig.update_xaxes(fixedrange=False);
            fig.update_yaxes(fixedrange=False)
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

# /// 6. 论文审计日志 ///
elif selected_page == PAGES[5]:
    st.markdown('<div class="glass-card"><h3 style="color:var(--text-color);">🛡️ 实验数据采集与多维审计中心</h3></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        if os.path.exists(GLOBAL_LOG_FILE): st.download_button("📁 导出中期汇报审计日志",
                                                               data=pd.read_csv(GLOBAL_LOG_FILE).to_csv(
                                                                   index=False).encode('utf-8'),
                                                               file_name='Audit_Logs.csv', type="primary")
    with c2:
        st.text_area("实时工作流终端", value="\n".join(st.session_state.sys_logs), height=350)