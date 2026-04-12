# ==========================================
# 文件名：quant_engine.py (底层核心兵器库)
# 功能：封装所有数据获取、指标计算、图表渲染、前端 CSS/JS 注入
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import re
import time
import math
import tushare as ts
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 预编译正则表达式
SUB_PATTERN = re.compile(r'^SUB(\d+)_')


# -----------------------------------
# 1. 核心计算与数据缓存模块
# -----------------------------------
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
def get_tushare_status(pro):
    try:
        t0 = time.time()
        pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240101')
        return f"🟢 Online ({int((time.time() - t0) * 1000)}ms)"
    except:
        return "🔴 Offline"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_and_clean_data(_pro, ts_code, adj, start_date):
    df = _pro.daily(ts_code=ts_code, start_date=start_date) if adj is None else ts.pro_bar(ts_code=ts_code, adj=adj,
                                                                                           start_date=start_date)
    if df is None or df.empty: return pd.DataFrame()
    df = df.sort_values('trade_date').reset_index(drop=True)
    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
    mapping_base = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'vol': 'Volume', 'amount': 'Amount'}
    for l_case, c_case in mapping_base.items():
        if l_case in df.columns: df[c_case] = df[l_case]
    if 'Volume' not in df.columns and 'vol' in df.columns: df['Volume'] = df['vol']
    return add_default_indicators(df)


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


def format_ts_code(raw):
    raw = str(raw).strip().upper()
    if len(raw) == 6 and raw.isdigit(): return f"{raw}.SH" if raw.startswith(('6', '9')) else f"{raw}.SZ"
    return raw


# -----------------------------------
# 2. Plotly 高级图表渲染模块
# -----------------------------------
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


# -----------------------------------
# 3. 前端核动力装甲 (CSS/JS 与水豚噜噜)
# -----------------------------------
def inject_frontend_core(anim_name, scroll_script):
    # 此处替换为您自己的 Base64 长字符串
    LULU_IDLE_IMG = "data:image/png;base64,请填入第一张图片Base64"
    LULU_DRAG_IMG = "data:image/png;base64,请填入第二张图片Base64"
    LULU_TALK_IMG = "data:image/png;base64,请填入第三张图片Base64"

    components.html(f"""
    <script>
        {scroll_script}
        let isUpdating = false;
        const idleImgSrc = "{LULU_IDLE_IMG}";
        const dragImgSrc = "{LULU_DRAG_IMG}";
        const talkImgSrc = "{LULU_TALK_IMG}";

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
                const fileInput = doc.querySelector('div[data-testid="stFileUploader"] input[type="file"]');

                if (chatInputOuter && fileInput) {{
                    const innerPill = chatInputOuter.querySelector('.stChatInputContainer') || chatInputOuter.firstElementChild; 

                    if (innerPill && !doc.getElementById('fake-attach-btn')) {{
                        innerPill.style.setProperty('position', 'relative', 'important');
                        const fakeBtn = doc.createElement('div');
                        fakeBtn.id = 'fake-attach-btn';
                        fakeBtn.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #8b9bb4; cursor: pointer; transition: 0.2s;"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>`;
                        fakeBtn.style.cssText = 'position: absolute !important; left: 16px !important; top: 50% !important; transform: translateY(-50%) !important; z-index: 9999 !important; display: flex; align-items: center; justify-content: center; width: 24px; height: 24px;';

                        fakeBtn.onclick = () => fileInput.click();
                        fakeBtn.onmouseover = () => {{ fakeBtn.style.opacity = '0.6'; }};
                        fakeBtn.onmouseout = () => {{ fakeBtn.style.opacity = '1'; }};
                        innerPill.appendChild(fakeBtn);

                        const textAreaWrap = innerPill.querySelector('[data-baseweb="textarea"]');
                        if(textAreaWrap) textAreaWrap.style.setProperty('padding-left', '40px', 'important');
                    }}
                }}

                if (!doc.getElementById('lulu-pet-container')) {{
                    const luluBox = doc.createElement('div');
                    luluBox.id = 'lulu-pet-container';
                    luluBox.style.cssText = `
                        position: fixed; bottom: 80px; right: 40px; z-index: 999999;
                        cursor: grab; user-select: none; -webkit-user-select: none; display: flex; flex-direction: column;
                        align-items: center; transition: transform 0.1s ease;
                    `;

                    luluBox.innerHTML = `
                        <div id="lulu-bubble" style="
                            opacity: 0; background: rgba(20, 28, 45, 0.9); border: 1px solid #00ffcc;
                            color: #e2e8f0; padding: 8px 12px; border-radius: 12px; font-size: 13px;
                            margin-bottom: 10px; white-space: nowrap; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
                            transition: opacity 0.3s ease; pointer-events: none;
                        ">主公，噜噜在呢~ 🦦</div>
                        <img id="lulu-img" src="${idleImgSrc}" style="width: 85px; height: auto; pointer-events: none; user-select: none; -webkit-user-drag: none;">
                    `;
                    doc.body.appendChild(luluBox);

                    const luluImgElement = doc.getElementById('lulu-img');
                    let isDragging = false, isClick = true;
                    let startX, startY, initLeft, initTop;

                    luluBox.addEventListener('mousedown', (e) => {{
                        isDragging = true; isClick = true;
                        startX = e.clientX; startY = e.clientY;
                        const rect = luluBox.getBoundingClientRect();
                        initLeft = rect.left; initTop = rect.top;

                        luluImgElement.src = dragImgSrc;
                        luluBox.style.bottom = 'auto'; luluBox.style.right = 'auto';
                        luluBox.style.left = initLeft + 'px'; luluBox.style.top = initTop + 'px';
                        luluBox.style.cursor = 'grabbing';
                        luluBox.style.transform = 'scale(1.1) rotate(-8deg)';
                    }});

                    doc.addEventListener('mousemove', (e) => {{
                        if (!isDragging) return;
                        const dx = e.clientX - startX; const dy = e.clientY - startY;
                        if (Math.abs(dx) > 5 || Math.abs(dy) > 5) isClick = false; 
                        luluBox.style.left = (initLeft + dx) + 'px';
                        luluBox.style.top = (initTop + dy) + 'px';
                    }});

                    doc.addEventListener('mouseup', () => {{
                        if (!isDragging) return;
                        isDragging = false;
                        luluBox.style.cursor = 'grab';
                        luluBox.style.transform = 'scale(1) rotate(0deg)';

                        if (!isClick) luluImgElement.src = idleImgSrc;

                        if (isClick) {{
                            luluImgElement.src = talkImgSrc;
                            const bubble = doc.getElementById('lulu-bubble');
                            const dialogues = ["主公，今天量化赚钱了吗？✨", "均线金叉了！冲冲冲！🚀", "噜噜看不懂代码，但噜噜陪着主公~❤️", "不要满仓！注意回撤呀主公！🛡️", "好困...想吃橘子...🍊", "正在调用 Kimi 脑细胞...🧠", "哇！这个策略好厉害的样子！😮"];
                            bubble.innerText = dialogues[Math.floor(Math.random() * dialogues.length)];
                            bubble.style.opacity = '1';
                            setTimeout(() => {{ 
                                bubble.style.opacity = '0'; 
                                luluImgElement.src = idleImgSrc;
                            }}, 3000);
                        }}
                    }});
                }}
                isUpdating = false;
            }});
        }};

        runGlobalEngine();
        const observer = new MutationObserver(runGlobalEngine);
        observer.observe(window.parent.document.body, {{ childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style'] }});
    </script>
    """, height=0, width=0)

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

        /* 隐身原生上传框 */
        div[data-testid="stFileUploader"] { position: absolute !important; top: -9999px !important; left: -9999px !important; opacity: 0.01 !important; z-index: -9999 !important; height: 1px !important; width: 1px !important; overflow: hidden !important; margin: 0 !important; padding: 0 !important; pointer-events: none !important; }

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