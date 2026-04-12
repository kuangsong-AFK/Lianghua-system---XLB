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

# ==========================================
# 0. 环境优雅降级 (完全静默)
# ==========================================
try:
    import PyPDF2
except:
    PyPDF2 = None
try:
    import docx
except:
    docx = None

pd.np = np
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

for key, default in {
    "messages": [], "generated_code": "", "sys_logs": [],
    "is_live_trading": False, "dl_result": None, "bt_result": None,
    "strategy_explanation": "暂无策略解析，请先下达军令。",
    "curr_page": "🏠 系统总览 (监控中控)", "prev_page": "🏠 系统总览 (监控中控)"
}.items():
    if key not in st.session_state: st.session_state[key] = default
if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"

# ==========================================
# 2. 极致前端引擎 (防崩溃 Emoji 版噜噜)
# ==========================================
PAGES = ["🏠 系统总览 (监控中控)", "🤖 AI 策略引擎 (LLM)", "📈 深度静态全量回测", "⚡ 实时高频交易 (Live)",
         "🧠 深度学习预测矩阵", "🛡️ 论文审计日志"]
prev_idx, curr_idx = PAGES.index(st.session_state.prev_page), PAGES.index(st.session_state.curr_page)
anim_name = "waveBlurUpIn" if curr_idx > prev_idx else ("waveBlurDownIn" if curr_idx < prev_idx else "fogFadeIn")

# 🔥 修复2：height=1 防止被框架强杀，加上 display:none 隐藏本体 🔥
components.html(f"""
<script>
    let isUpdating = false;

    const runGlobalEngine = () => {{
        if(isUpdating) return;
        isUpdating = true;
        requestAnimationFrame(() => {{
            const doc = window.parent.document;
            const app = doc.querySelector('.stApp');

            // 1. 主题检测
            if (app) {{
                const color = window.getComputedStyle(app).color;
                if(color) {{
                    const rgb = color.match(/\\d+/g);
                    if (rgb && rgb.length >= 3) {{
                        const brightness = (parseInt(rgb[0]) * 299 + parseInt(rgb[1]) * 587 + parseInt(rgb[2]) * 114) / 1000;
                        app.setAttribute('data-custom-theme', brightness > 128 ? 'dark' : 'light');
                    }}
                }}
            }}

            // 2. 📎 按钮物理锁死
            const chatInputOuter = doc.querySelector('div[data-testid="stChatInput"]');
            const fileInput = doc.querySelector('div[data-testid="stFileUploader"] input[type="file"]');
            if (chatInputOuter && fileInput) {{
                const innerPill = chatInputOuter.querySelector('.stChatInputContainer') || chatInputOuter.firstElementChild; 
                if (innerPill && !doc.getElementById('fake-attach-btn')) {{
                    innerPill.style.position = 'relative';
                    const fakeBtn = doc.createElement('div');
                    fakeBtn.id = 'fake-attach-btn';
                    fakeBtn.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #8b9bb4; cursor: pointer;"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>`;
                    fakeBtn.style.cssText = 'position: absolute !important; left: 16px !important; top: 50% !important; transform: translateY(-50%) !important; z-index: 9999; display: flex; align-items: center; justify-content: center; width: 24px; height: 24px;';
                    fakeBtn.onclick = () => fileInput.click();
                    innerPill.appendChild(fakeBtn);
                    innerPill.querySelector('textarea').style.paddingLeft = '45px';
                }}
            }}

            // 3. 噜噜渲染 (Emoji 防断裂版)
            if (!doc.getElementById('lulu-pet-container')) {{
                const luluBox = doc.createElement('div');
                luluBox.id = 'lulu-pet-container';
                luluBox.style.cssText = 'position: fixed; bottom: 80px; right: 40px; z-index: 999999; cursor: grab; display: flex; flex-direction: column; align-items: center; transition: 0.1s; user-select: none;';
                luluBox.innerHTML = `
                    <div id="lulu-bubble" style="opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #00ffcc; color: #fff; padding: 8px 12px; border-radius: 12px; font-size: 13px; margin-bottom: 5px; white-space: nowrap; transition: 0.3s; pointer-events: none; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">主公，噜噜在呢~</div>
                    <div id="lulu-img" style="font-size: 70px; line-height: 1; filter: drop-shadow(0px 10px 10px rgba(0,0,0,0.4));">🦦</div>
                `;
                doc.body.appendChild(luluBox);

                let isDragging = false, startX, startY, initLeft, initTop, isClick = true;
                luluBox.onmousedown = (e) => {{
                    isDragging = true; isClick = true;
                    startX = e.clientX; startY = e.clientY;
                    const rect = luluBox.getBoundingClientRect();
                    initLeft = rect.left; initTop = rect.top;
                    luluBox.style.bottom = 'auto'; luluBox.style.right = 'auto';
                    luluBox.style.left = initLeft + 'px'; luluBox.style.top = initTop + 'px';
                    luluBox.style.transform = 'scale(1.1) rotate(-10deg)';
                    doc.getElementById('lulu-img').innerText = '😱'; // 抓起震惊
                }};
                doc.onmousemove = (e) => {{
                    if (!isDragging) return;
                    isClick = false;
                    luluBox.style.left = (initLeft + e.clientX - startX) + 'px';
                    luluBox.style.top = (initTop + e.clientY - startY) + 'px';
                }};
                doc.onmouseup = () => {{
                    if (!isDragging) return;
                    isDragging = false;
                    luluBox.style.transform = 'scale(1) rotate(0deg)';
                    const img = doc.getElementById('lulu-img');
                    if (!isClick) img.innerText = '🦦'; // 放下恢复
                    if (isClick) {{
                        img.innerText = '✨'; // 点击星星眼
                        const b = doc.getElementById('lulu-bubble');
                        const ts = ["均线金叉了！冲冲冲！🚀", "想吃橘子了...🍊", "噜噜在陪你喔~❤️", "正在调集Kimi算力...🧠"];
                        b.innerText = ts[Math.floor(Math.random()*ts.length)];
                        b.style.opacity = '1';
                        setTimeout(() => {{ b.style.opacity = '0'; img.innerText = '🦦'; }}, 3000);
                    }}
                }};
            }}
            isUpdating = false;
        }});
    }};
    runGlobalEngine();
    new MutationObserver(runGlobalEngine).observe(window.parent.document.body, {{ childList: true, subtree: true }});
</script>
<style>
    @keyframes fluidFlow {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
    .stApp {{ background-image: linear-gradient(132deg, #02040a, #030e2b, #082a72, #030614) !important; background-size: 400% 400% !important; animation: fluidFlow 15s ease infinite !important; }}
    .glass-card {{ background: rgba(20, 28, 45, 0.65) !important; backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; margin-bottom: 20px; }}
    .metric-box {{ background: rgba(0, 255, 204, 0.05); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; }}
    div[data-testid="stFileUploader"] {{ position: absolute !important; top: -9999px !important; opacity: 0 !important; }}
</style>
""", height=1, width=1)  # 🔥 增大体积并隐藏，防止被强杀 🔥

st.markdown(
    f"<style>.block-container {{ animation: {anim_name} 0.7s ease-out; padding-bottom: 100px !important; }} div[title='streamlit_html'] {{ display: none !important; }}</style>",
    unsafe_allow_html=True)


# ==========================================
# 3. 后勤计算引擎 (Data & Execution)
# ==========================================
def add_default_indicators(df):
    if 'Close' in df.columns:
        df['MAIN_MA5'] = df['Close'].rolling(5).mean()
        df['MAIN_MA20'] = df['Close'].rolling(20).mean()
        diff = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
        dea = diff.ewm(span=9).mean()
        df['SUB1_MACD_HIST'] = 2 * (diff - dea)
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_and_clean_data(ts_code, adj, start_date):
    try:
        df = ts.pro_bar(ts_code=ts_code, adj=adj, start_date=start_date)
    except:
        df = pro.daily(ts_code=ts_code, start_date=start_date)
    if df is None or df.empty: return pd.DataFrame()
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date').reset_index(drop=True)
    for c in ['open', 'high', 'low', 'close', 'vol']: df[c.capitalize()] = df.get(c, df.get(c.capitalize()))
    return add_default_indicators(df)


def execute_safely(code, df):
    l_vars = {}
    exec(code.replace("pandas.np", "np"), {"pd": pd, "np": np, "math": math}, l_vars)
    func = next((v for v in l_vars.values() if callable(v)), None)
    if not func: raise ValueError("无可用策略函数")
    df_ai = func(df.copy())
    df_ai['Signal'] = df_ai.get('Signal', pd.Series([0] * len(df_ai))).fillna(0).astype(int)
    return df_ai


def run_backtest_metrics(df_source, code):
    df = execute_safely(code, df_source) if code else df_source.copy()
    df['Ret'] = df['Close'].pct_change()
    df['Pos'] = df.get('Signal', 0).replace(0, np.nan).ffill().fillna(0)
    df['Strat_Ret'] = df['Pos'].shift(1) * df['Ret']
    df['Cum_Prod'] = (1 + df['Strat_Ret'].fillna(0)).cumprod()
    total = df['Cum_Prod'].iloc[-1] - 1 if not df.empty else 0
    annual = (1 + total) ** (252 / max(1, len(df))) - 1 if not df.empty else 0
    max_dd = (df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min() if not df.empty else 0
    return {"df": df, "metrics": {"total": total, "annual": annual, "max_dd": max_dd, "sharpe": 0}}


def format_ts_code(c): return f"{c}.SH" if c.startswith(('6', '9')) else f"{c}.SZ"


def render_smart_charts(df):
    m_inds = [c for c in df.columns if c.startswith('MAIN_')]
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(
        go.Candlestick(x=df['trade_date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1,
        col=1)
    for c in m_inds: fig.add_trace(go.Scatter(x=df['trade_date'], y=df[c], name=c), row=1, col=1)
    fig.add_trace(go.Bar(x=df['trade_date'], y=df.get('Volume', np.zeros(len(df)))), row=2, col=1)
    fig.update_layout(height=600, template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      xaxis_rangeslider_visible=False, showlegend=False)
    fig.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    return fig


# ==========================================
# 4. 业务页面渲染
# ==========================================
with st.sidebar:
    selected_page = st.radio("导航菜单", PAGES, label_visibility="collapsed")
    if selected_page != st.session_state.curr_page:
        st.session_state.prev_page = st.session_state.curr_page
        st.session_state.curr_page = selected_page
        st.rerun()

if selected_page == PAGES[0]:
    st.markdown('<div class="glass-card"><h1>🏛️ 小吕布量化 Pro 决策枢纽</h1></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("活跃沙盒", st.session_state.user_id)
    c2.metric("行情链路", "🟢 Online")
    c3.metric("AI 核心", "🟢 Moonshot")
    c4.metric("守护灵", "🦦 水豚噜噜")
    st.markdown(
        """<div class="glass-card"><h3 style="margin-top:0;">🌟 平台核心简介</h3>• <b>📝 全模态投研直通：</b>点击左下角 📎 一键投喂。<br>• <b>🤖 语义化策略生成：</b>Agent 自动修复并回测。<br>• <b>📊 十载周期归因：</b>长达 10 年的历史回测。</div>""",
        unsafe_allow_html=True)

elif selected_page == PAGES[1]:
    st.markdown('<div class="glass-card"><h3 style="margin:0;">🤖 LLM 策略战情室</h3></div>', unsafe_allow_html=True)
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload", accept_multiple_files=True, type=['pdf', 'docx', 'csv', 'txt', 'png', 'jpg'],
                                label_visibility="collapsed")
    file_context = ""
    if uploaded:
        for f in uploaded:
            if f.name.endswith('.csv'):
                file_context += f"【CSV】\n{pd.read_csv(f).head(5).to_string()}\n"
            elif f.name.endswith('.txt'):
                file_context += f"【TXT】\n{f.getvalue().decode('utf-8')[:1000]}\n"

    if prompt := st.chat_input("下达指令..."):
        full_p = f"参考数据：\n{file_context}\n指令：{prompt}" if file_context else prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            msg_ph = st.empty();
            full_resp = ""
            try:
                stream = client.chat.completions.create(model="moonshot-v1-8k", messages=[
                    {"role": "system", "content": "写策略代码请用 def generate_signals(df) 骨架。"},
                    {"role": "user", "content": full_p}], stream=True)
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_resp += chunk.choices[0].delta.content
                        msg_ph.markdown(full_resp + "▌")
                msg_ph.markdown(full_resp)
                code_m = re.search(r"```python\s*(.*?)\s*```", full_resp, re.DOTALL)
                if code_m: st.session_state.generated_code = code_m.group(1).strip()
                st.session_state.strategy_explanation = re.sub(r"```python.*?```", "", full_resp,
                                                               flags=re.DOTALL).strip()
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
            except Exception as e:
                st.error(f"通讯受阻: {e}")
        st.rerun()

elif selected_page == PAGES[2]:
    st.markdown('<div class="glass-card"><h3>📊 历史周期回测</h3></div>', unsafe_allow_html=True)
    c_l, c_r = st.columns([1, 3])
    with c_l:
        code_input = st.text_input("代码", "000001.SZ")
        if st.button("启动回测", type="primary", use_container_width=True):
            with st.spinner("回测中..."):
                try:
                    df = fetch_and_clean_data(code_input, 'qfq', '20200101')
                    st.session_state.bt_result = run_backtest_metrics(df, st.session_state.generated_code)
                except Exception as e:
                    st.error(f"错误: {e}")
    with c_r:
        if st.session_state.bt_result is not None:
            res = st.session_state.bt_result
            c1, c2 = st.columns(2)
            c1.markdown(f'<div class="metric-box"><p>累计收益</p><h2>{res["metrics"]["total"] * 100:.2f}%</h2></div>',
                        unsafe_allow_html=True)
            c2.markdown(
                f'<div class="metric-box"><p>最大回撤</p><h2 style="color:#ff4b4b;">{res["metrics"]["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            st.plotly_chart(render_smart_charts(res['df']), use_container_width=True)

elif selected_page == PAGES[5]:
    st.markdown('<div class="glass-card"><h3>🛡️ 实验日志</h3></div>', unsafe_allow_html=True)
    st.text_area("实时日志", value="\n".join(st.session_state.sys_logs), height=400)