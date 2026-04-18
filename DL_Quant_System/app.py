import os, sys, uuid, math, re, time
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import tushare as ts
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from PIL import Image
from openai import OpenAI

# ==========================================
# 0. 扩展引掣与环境安全加载
# ==========================================
try:
    import extensions
except ImportError:
    extensions = None
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

st.set_page_config(page_title="小吕布量化 Pro - 毕设版", layout="wide", initial_sidebar_state="expanded")
ts.set_token("ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e")
pro = st.cache_resource(ts.pro_api)()
client = OpenAI(api_key="sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk", base_url="https://api.moonshot.cn/v1",
                timeout=60.0)

# ==========================================
# 1. 状态机与路由初始化
# ==========================================
default_states = {
    "user_id": f"User_{str(uuid.uuid4())[:6]}", "messages": [], "generated_code": "",
    "strategy_explanation": "暂无策略解析，请先前往 AI 战情室下达军令。", "dl_result": None,
    "bt_result": None, "sys_logs": [], "is_live_trading": False,
    "curr_page": "🏠 系统总览 (监控中控)", "prev_page": "🏠 系统总览 (监控中控)", "just_switched": False
}
for k, v in default_states.items():
    if k not in st.session_state: st.session_state[k] = v

PAGES = ["🏠 系统总览 (监控中控)", "🤖 AI 策略引擎 (LLM)", "💻 极客量化 IDE (代码编译)", "📈 深度静态全量回测",
         "⚡ 实时高频交易 (Live)", "🧠 深度学习预测矩阵", "🛡️ 论文审计日志", "🔗 期货全量审计 (归因)", "🌪️ 期货高频沙盘",
         "🧩 扩展插件中心"]

with st.sidebar:
    st.markdown(f"### 🎓 小吕布量化 Pro\n<small>🛡️ 节点 ID: {st.session_state.user_id}</small>\n---",
                unsafe_allow_html=True)
    selected_page = st.radio("导航菜单", PAGES, label_visibility="collapsed")

if selected_page != st.session_state.curr_page:
    st.session_state.prev_page, st.session_state.curr_page, st.session_state.just_switched = st.session_state.curr_page, selected_page, True
else:
    st.session_state.just_switched = False

anim_name = "waveBlurUpIn" if PAGES.index(st.session_state.curr_page) > PAGES.index(
    st.session_state.prev_page) else "waveBlurDownIn"

# ==========================================
# 2. UI/UX 底层注入引擎 (带防重发锁)
# ==========================================
scroll_script = "window.parent.scrollTo({top: 0, behavior: 'instant'});" if st.session_state.just_switched else ""

if "core_ui_injected" not in st.session_state:
    components.html(f"""
    <script>
        {scroll_script}
        let isUpdating = false;
        const runGlobalEngine = () => {{
            if(isUpdating) return; isUpdating = true;
            requestAnimationFrame(() => {{
                const app = window.parent.document.querySelector('.stApp');
                if (app) {{
                    const rgb = window.getComputedStyle(app).color.match(/\\d+/g);
                    if (rgb && rgb.length >= 3) {{
                        const themeAttr = ((rgb[0]*299 + rgb[1]*587 + rgb[2]*114)/1000) < 128 ? 'light' : 'dark';
                        if (app.getAttribute('data-custom-theme') !== themeAttr) app.setAttribute('data-custom-theme', themeAttr);
                    }}
                }}
                const chatWrap = window.parent.document.querySelector('div[data-testid="stChatInput"]');
                const fileIn = window.parent.document.querySelector('div[data-testid="stFileUploader"] input[type="file"]');
                if (chatWrap && fileIn) {{
                    const pill = chatWrap.querySelector('.stChatInputContainer') || chatWrap.firstElementChild;
                    if (pill && !window.parent.document.getElementById('fake-btn')) {{
                        pill.style.position = 'relative';
                        const btn = window.parent.document.createElement('div'); btn.id = 'fake-btn';
                        btn.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"></path></svg>`;
                        btn.style.cssText = 'position: absolute; left: 16px; top: 50%; transform: translateY(-50%); z-index: 9999; color: #8b9bb4; cursor: pointer;';
                        btn.onclick = () => fileIn.click(); pill.appendChild(btn);
                        const txt = pill.querySelector('[data-baseweb="textarea"]'); if(txt) txt.style.paddingLeft = '40px';
                    }}
                }}
                isUpdating = false;
            }});
        }};
        runGlobalEngine();
        new MutationObserver(runGlobalEngine).observe(window.parent.document.body, {{ childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style'] }});
    </script>
    """, height=0, width=0)
    st.session_state.core_ui_injected = True

if extensions and "lulu_injected" not in st.session_state:
    extensions.summon_global_3d_lulu();
    st.session_state.lulu_injected = True

st.markdown(f"""
<style>
    @keyframes waveBlurUpIn {{ 0% {{ opacity: 0; margin-top: 60px; filter: blur(15px); }} 100% {{ opacity: 1; margin-top: 0px; filter: blur(0px); }} }}
    @keyframes waveBlurDownIn {{ 0% {{ opacity: 0; margin-top: -60px; filter: blur(15px); }} 100% {{ opacity: 1; margin-top: 0px; filter: blur(0px); }} }}
    .block-container {{ animation: {anim_name} 0.65s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; background: transparent !important; padding-top: 4.5rem !important; padding-bottom: 120px !important; }}
    header[data-testid="stHeader"] {{ background: transparent !important; pointer-events: none !important; }}
    [data-testid="collapsedControl"], [data-testid="stToolbar"] {{ pointer-events: auto !important; }}
    div[data-testid="stFileUploader"] {{ position: absolute !important; top: -9999px !important; opacity: 0 !important; pointer-events: none !important; }}
    .stApp {{ background-image: linear-gradient(132deg, #02040a, #030e2b, #111d3d, #082a72, #030614, #1d2b4f, #0a47b3, #02040a) !important; background-size: 600% 600% !important; }}
    .stMarkdown, p, h1, h2, h3, h4, label, [data-testid="stMetricValue"] > div {{ color: #e2e8f0 !important; }}
    .highlight-text {{ color: #00ffcc !important; }} .sub-text {{ color: #cbd5e1 !important; }} .danger-text {{ color: #ff4b4b !important; }}
    [data-testid="stSidebar"] {{ background: rgba(5, 8, 14, 0.75) !important; backdrop-filter: blur(25px) !important; border-right: 1px solid rgba(255,255,255,0.08) !important; }}
    div[role="radiogroup"] > label {{ background: rgba(15, 20, 30, 0.4) !important; border-left: 4px solid transparent !important; border-radius: 12px !important; margin-bottom: 10px !important;}}
    div[role="radiogroup"] > label:has(input:checked) {{ background: linear-gradient(90deg, rgba(0, 255, 204, 0.3), rgba(10, 15, 25, 0.95)) !important; border-left: 4px solid #00ffcc !important; }}
    .glass-card {{ background: rgba(20, 28, 45, 0.65); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; margin-bottom: 20px; }}
    .metric-box {{ background: rgba(0, 255, 204, 0.05); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; }}
    .metric-box p {{ margin: 0; font-size: 0.9rem; color: #cbd5e1; }} .metric-box h2 {{ margin: 8px 0 0 0; font-size: 1.8rem; }}
    [data-testid="stChatInput"] {{ max-width: 850px; margin: 0 auto 10px auto !important; background: transparent !important; border: none !important; }}
    [data-testid="stChatInput"] > div:first-child {{ background: rgba(30, 41, 59, 0.6) !important; backdrop-filter: blur(25px) !important; border-radius: 36px !important; }}
    textarea {{ font-family: 'Consolas', monospace !important; color: #fff !important; }}
    .stApp[data-custom-theme='light'] {{ background-image: linear-gradient(132deg, #ffffff, #dbeafe, #e0e7ff, #f3e8ff, #ffffff) !important; }}
    .stApp[data-custom-theme='light'] .stMarkdown, .stApp[data-custom-theme='light'] p, .stApp[data-custom-theme='light'] h1, .stApp[data-custom-theme='light'] h3, .stApp[data-custom-theme='light'] label {{ color: #1e293b !important; }}
    .stApp[data-custom-theme='light'] .glass-card {{ background: rgba(255, 255, 255, 0.75); border: 1px solid rgba(0,0,0,0.1); }}
    .agent-status-node {{ padding: 8px 12px; border-radius: 8px; font-size: 0.9rem; margin: 5px 0; border-left: 4px solid transparent; }}
    .agent-status-node.success {{ background: rgba(0, 255, 204, 0.1); border-left-color: #00ffcc; color: #00ffcc; }}
    .agent-status-node.error {{ background: rgba(255, 75, 75, 0.1); border-left-color: #ff4b4b; color: #ff4b4b; }}
    .agent-status-node.retry {{ background: rgba(255, 165, 0, 0.1); border-left-color: #ffa500; color: #ffa500; }}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. 核心计算引擎 (抽象解耦版)
# ==========================================
def add_default_indicators(df):
    if 'Close' in df.columns:
        df['MAIN_MA5'], df['MAIN_MA20'] = df['Close'].rolling(5).mean(), df['Close'].rolling(20).mean()
        df['SUB1_MACD_DIFF'] = df['Close'].ewm(span=12).mean() - df['Close'].ewm(span=26).mean()
        df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9).mean()
        df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])
    return df


@st.cache_data(ttl=300, show_spinner=False)
def get_tushare_status():
    try:
        pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240101'); return "🟢 Online"
    except:
        return "🔴 Offline"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_and_clean_data(ts_code, adj, start_date):
    df = ts.pro_bar(ts_code=ts_code, adj=adj, start_date=start_date)
    if df is not None and not df.empty:
        df = df.sort_values('trade_date').reset_index(drop=True)
        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'vol': 'Volume',
                           'amount': 'Amount'}, inplace=True, errors='ignore')
        return add_default_indicators(df)
    return pd.DataFrame()


def execute_safely(code, df):
    l_vars = {}
    exec(code.replace("pandas.np", "np"), {"pd": pd, "np": np, "math": math}, l_vars)
    func = next((v for k, v in l_vars.items() if callable(v)), None)
    if not func: raise ValueError("AI 未生成有效函数！")
    df_ai = func(df)
    if 'Signal' in df_ai: df_ai['Signal'] = np.sign(df_ai['Signal'].fillna(0).round(1)).astype(int)
    return df_ai


def render_smart_charts(df):
    main_inds, sub_groups = [c for c in df.columns if c.startswith('MAIN_')], {}
    for c in df.columns:
        if m := SUB_PATTERN.match(c): sub_groups.setdefault(m.group(1), []).append(c)

    fig = make_subplots(rows=2 + len(sub_groups), cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.5, 0.15] + [0.35 / max(1, len(sub_groups))] * len(sub_groups))
    x_labels = df['trade_date'].dt.strftime('%Y-%m-%d' if df['trade_date'].dt.time.nunique() <= 1 else '%m-%d %H:%M')

    fig.add_trace(
        go.Candlestick(x=x_labels, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K线'),
        row=1, col=1)
    colors = ['#FFFF00', '#FF00FF', '#00FFFF', '#FFFFFF']
    for i, c in enumerate(main_inds): fig.add_trace(
        go.Scatter(x=x_labels, y=df[c], name=c, line=dict(color=colors[i % 4], width=1.2)), row=1, col=1)

    if 'Signal' in df.columns:
        # 🔥 优化：向量化绘制买卖点，代码骤减 🔥
        for sig, name, c, sym, off in [(1, '买', '#00FFFF', 'triangle-up', 0.95),
                                       (-1, '卖', '#FF00FF', 'triangle-down', 1.05)]:
            mask = df['Signal'] == sig
            fig.add_trace(
                go.Scatter(x=x_labels[mask], y=df.loc[mask, 'Low' if sig == 1 else 'High'] * off, mode='markers',
                           marker=dict(symbol=sym, size=14, color=c), name=name), row=1, col=1)

    fig.add_trace(go.Bar(x=x_labels, y=df.get('Volume', np.zeros(len(df))),
                         marker_color=np.where(df['Close'] >= df['Open'], '#FD1050', '#00FF00')), row=2, col=1)

    for idx, gid in enumerate(sorted(sub_groups.keys(), key=int)):
        for i, c in enumerate(sub_groups[gid]):
            trace = go.Bar(x=x_labels, y=df[c], marker_color=np.where(df[c] >= 0, '#FD1050',
                                                                      '#00FF00')) if 'HIST' in c.upper() else go.Scatter(
                x=x_labels, y=df[c], line=dict(color=colors[i % 4]))
            fig.add_trace(trace, row=3 + idx, col=1)

    fig.update_layout(height=500 + len(sub_groups) * 150, template="none", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=x_labels, nticks=8, showgrid=True,
                     gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    return fig


# ==========================================
# 4. 各页面业务路由
# ==========================================
if selected_page == PAGES[0]:
    st.markdown(
        '<div class="glass-card"><h1 style="margin-bottom:0;">🏛️ 全链路智能量化决策枢纽</h1><p class="highlight-text">System Overview</p></div>',
        unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("并发沙盒 UUID", st.session_state.user_id)
    c2.metric("Tushare 链路", get_tushare_status())
    c3.metric("LLM 算力通信", "🟢 Moonshot-v1")
    c4.metric("AI 神经网络", "🟢 待命")
    st.markdown("---")
    st.markdown(
        """<div class="glass-card"><h3>🌟 平台简介</h3><p>欢迎来到 <b>小吕布量化 Pro</b>。<br>• <b>全模态投研</b>：研报矩阵直读。<br>• <b>零代码策略</b>：大模型全自动生成。<br>• <b>时序张量预测</b>：深度学习自回归推演。<br>• <b>高频沙盘</b>：极速盘口与归因引擎。</p></div>""",
        unsafe_allow_html=True)

elif selected_page == PAGES[1]:
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">🤖 LLM 策略战情室</h3></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    model_sel = c1.selectbox("选择算力通道", ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"])
    c2.markdown("<div style='height:32px;'></div>", unsafe_allow_html=True);
    enable_cot = c2.toggle("💡 开启深度思考引擎 (CoT)")

    chat_box = st.container()
    for m in st.session_state.messages:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

    upl_files = st.file_uploader("Files", accept_multiple_files=True, label_visibility="collapsed")


    # 🔥 优化：将繁杂的 if-else 抽离为解析逻辑包 🔥
    def parse_file(f):
        ext = f.name.lower().split('.')[-1]
        if f.type.startswith('image/'): return f"[图片: {f.name}]\n"
        if ext == 'csv': return f"【CSV】:\n{pd.read_csv(f).head(50).to_string()}\n"
        if ext == 'txt': return f"【TXT】:\n{f.getvalue().decode('utf-8', errors='replace')[:5000]}\n"
        if ext == 'pdf' and PyPDF2: return f"【PDF】:\n{''.join([p.extract_text() for p in PyPDF2.PdfReader(f).pages[:10]])[:5000]}\n"
        if ext in ['doc',
                   'docx'] and docx: return f"【Word】:\n{chr(10).join([p.text for p in docx.Document(f).paragraphs])[:5000]}\n"
        return ""


    ctx_text = "".join([parse_file(f) for f in upl_files]) if upl_files else ""

    if raw_prompt := st.chat_input("向小吕布架构师发送军令..."):
        full_prompt = f"参考附件:\n{ctx_text}\n\n指令:{raw_prompt}" if ctx_text else raw_prompt
        st.session_state.messages.append({"role": "user", "content": raw_prompt})

        with chat_box.chat_message("user"):
            st.markdown(raw_prompt)
        with chat_box.chat_message("assistant"):
            sys_p = "你是一名顶级量化工程师。严格遵循：只用 pandas/numpy/math。主图指标用 MAIN_ 开头，副图用 SUB1_ 等。必须生成 df['Signal']。直接输出包含 def generate_signals(df): 的代码和解析。"
            msgs = [{"role": "system", "content": sys_p}] + st.session_state.messages[:-1] + [
                {"role": "user", "content": full_prompt}]

            log_str, last_err, full_resp, msg_ph = [], "", "", st.empty()

            for att in range(3):
                if att > 0:
                    log_str.append(
                        f'<div class="agent-status-node retry">🔄 尝试 {att}: 沙盒拦截 ({last_err}) -> 重构</div>')
                    msgs.extend([{"role": "assistant", "content": full_resp},
                                 {"role": "user", "content": f"报错 `{last_err}`，请修复。"}])
                try:
                    stream = client.chat.completions.create(model=model_sel, messages=msgs, stream=True,
                                                            temperature=0.3 if enable_cot else 0.7)
                    full_resp = ""
                    for c in stream:
                        if c.choices[0].delta.content:
                            full_resp += c.choices[0].delta.content
                            msg_ph.markdown(
                                full_resp.replace("<think>", "🧠 思考中...\n\n").replace("</think>", "\n\n---\n") + "▌",
                                unsafe_allow_html=True)

                    msg_ph.markdown(full_resp.replace("<think>", "🧠 思考过程：\n").replace("</think>", "\n---\n"),
                                    unsafe_allow_html=True)

                    code_match = re.search(r"`{3}python\s*(.*?)\s*`{3}", full_resp, re.DOTALL)
                    exp = re.sub(r"<think>.*?</think>|`{3}python\s*.*?\s*`{3}", "", full_resp, flags=re.DOTALL).replace(
                        "【策略白话解析】", "").strip()
                    st.session_state.strategy_explanation = exp if exp else "纯代码驱动，无额外解析。"

                    if not code_match: break
                    code = code_match.group(1).strip()

                    # 沙盒预检
                    dummy = add_default_indicators(pd.DataFrame(
                        {'trade_date': pd.date_range('2023', periods=50), 'Open': np.random.rand(50) * 10,
                         'High': np.random.rand(50) * 12, 'Low': np.random.rand(50) * 8,
                         'Close': np.random.rand(50) * 10}))
                    execute_safely(code, dummy)

                    st.session_state.generated_code = code
                    log_str.append(f'<div class="agent-status-node success">✅ 尝试 {att + 1}: 通过预检，装载成功</div>')
                    break
                except Exception as e:
                    last_err = str(e)
                    if att == 2: log_str.append(f'<div class="agent-status-node error">❌ 失败: {last_err}</div>')

            res_str = full_resp + "\n\n" + "".join(log_str)
            st.markdown("".join(log_str), unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": res_str})
        st.rerun()

elif selected_page == PAGES[2]:
    if extensions:
        extensions.render_ide_page()
    else:
        st.error("请检查 extensions.py")

elif selected_page == PAGES[3]:
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">📊 静态全量回测</h3></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1, 3])
    with c1:
        ts_code = format_ts_code(st.text_input("标的", value="000001"))
        yr = datetime.now().year - {"近1年": 1, "近3年": 3, "近5年": 5, "近10年": 10}[
            st.selectbox("跨度", ["近1年", "近3年", "近5年", "近10年"], index=1)]
        if st.button("🚀 启动回测", type="primary", use_container_width=True):
            df_raw = fetch_and_clean_data(ts_code, "qfq", f"{yr}0101")
            st.session_state.bt_result = run_backtest_metrics(df_raw, st.session_state.generated_code)
    with c2:
        if res := st.session_state.bt_result:
            m = res['metrics']
            cols = st.columns(4)
            cols[0].markdown(f'<div class="metric-box"><p>累计收益</p><h2>{m["total"] * 100:.2f}%</h2></div>',
                             unsafe_allow_html=True)
            cols[1].markdown(f'<div class="metric-box"><p>年化</p><h2>{m["annual"] * 100:.2f}%</h2></div>',
                             unsafe_allow_html=True)
            cols[2].markdown(
                f'<div class="metric-box"><p>最大回撤</p><h2 class="danger-text">{m["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            cols[3].markdown(f'<div class="metric-box"><p>夏普</p><h2>{m["sharpe"]:.2f}</h2></div>',
                             unsafe_allow_html=True)
            with st.expander("💡 策略解析"): st.markdown(st.session_state.strategy_explanation)
            st.plotly_chart(render_smart_charts(res['df']), use_container_width=True)

elif selected_page == PAGES[4]:
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">⚡ 实时交易 Flow</h3></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2.5])
    with c1:
        live_code = st.text_input("标的", "000001")
        freq = st.slider("频率(s)", 0.1, 2.0, 0.5)
        st.button("▶️ 开启推演", on_click=lambda: st.session_state.update({"is_live_trading": True}), type="primary")
        st.button("⏹️ 停止", on_click=lambda: st.session_state.update({"is_live_trading": False}))
    with c2:
        met_ph, cht_ph = st.empty(), st.empty()
        if st.session_state.is_live_trading:
            df = fetch_and_clean_data(format_ts_code(live_code), 'qfq', '20230101').tail(120).reset_index(drop=True)
            for i in range(20, len(df)):
                if not st.session_state.is_live_trading: break
                sub = df.iloc[:i].copy()
                if st.session_state.generated_code:
                    try:
                        ai_res = execute_safely(st.session_state.generated_code, sub)
                        for col in ai_res: if
                        col == 'Signal' or col.startswith(('MAIN_', 'SUB')): sub[col] = ai_res[col]
                    except:
                        pass
                sig = sub.get('Signal', pd.Series([0])).iloc[-1]
                with met_ph.container():
                    cx = st.columns(3)
                    cx[0].metric("现价", f"{sub['Close'].iloc[-1]:.2f}")
                    cx[1].metric("信号", "买" if sig == 1 else "卖" if sig == -1 else "观望")
                    cx[2].metric("收益", f"{sub['Close'].pct_change().iloc[-1] * 100:.2f}%")
                cht_ph.plotly_chart(render_smart_charts(sub), use_container_width=True)
                time.sleep(freq)

elif selected_page == PAGES[5]:
    import torch, torch.nn as nn
    from sklearn.preprocessing import MinMaxScaler

    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">🧠 深度时序矩阵</h3></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2.5])
    with c1:
        st_code = st.text_input("标的", "000001")
        yrs = {"近1年": 1, "近3年": 3, "近5年": 5}[st.selectbox("跨度", ["近1年", "近3年", "近5年"], index=1)]
        models = st.multiselect("模型", ["LSTM", "GRU", "1D-CNN"], default=["LSTM"])
        slen, eps = st.slider("滑窗", 5, 60, 20), st.slider("Epoch", 10, 50, 30)

        if st.button("🚀 启动张量", type="primary", use_container_width=True) and models:
            # 🔥 优化：将三大散装模型重构成【多态工厂聚合类】🔥
            class TSModel(nn.Module):
                def __init__(self, m_type):
                    super().__init__();
                    self.m_type = m_type
                    if m_type == "1D-CNN":
                        self.conv = nn.Conv1d(1, 32, 3, 1); self.fc = nn.Linear(32 * slen, 1)
                    else:
                        self.rnn = getattr(nn, m_type)(1, 64, 2, batch_first=True); self.fc = nn.Linear(64, 1)

                def forward(self, x):
                    if self.m_type == "1D-CNN": return self.fc(
                        torch.relu(self.conv(x.permute(0, 2, 1))).reshape(x.size(0), -1))
                    return self.fc(self.rnn(x)[0][:, -1, :])


            df = fetch_and_clean_data(format_ts_code(st_code), 'qfq', f"{datetime.now().year - yrs}0101")
            sc = MinMaxScaler();
            s_val = sc.fit_transform(df['Close'].values.reshape(-1, 1))
            X, y = [s_val[i - slen:i, 0] for i in range(slen, len(s_val))], [s_val[i, 0] for i in
                                                                             range(slen, len(s_val))]
            Xt, yt = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1), torch.tensor(np.array(y),
                                                                                                dtype=torch.float32)

            p_dict, f_dict, lbox, pbar = {}, {}, st.empty(), st.progress(0)
            for i, m_name in enumerate(models):
                lbox.markdown(f"**训练 {m_name}...**")
                net, opt, crit = TSModel(m_name.replace("1D-", "")), torch.optim.Adam(
                    TSModel(m_name.replace("1D-", "")).parameters(), 0.01), nn.MSELoss()
                for e in range(eps):
                    net.train();
                    opt.zero_grad();
                    loss = crit(net(Xt).squeeze(), yt);
                    loss.backward();
                    opt.step()
                    pbar.progress((i * eps + e + 1) / (len(models) * eps))
                net.eval()
                p_dict[m_name] = sc.inverse_transform(net(Xt[-100:]).detach().numpy()).flatten()

                win, fut = Xt[-1].clone().unsqueeze(0), []
                for _ in range(5):
                    with torch.no_grad(): p = net(win)
                    fut.append(p.item());
                    win = torch.cat((win[:, 1:, :], p.unsqueeze(-1)), 1)
                f_dict[m_name] = sc.inverse_transform(np.array(fut).reshape(-1, 1)).flatten()

            st.session_state.dl_result = {"dates": df['trade_date'].iloc[-100:], "act": df['Close'].iloc[-100:],
                                          "preds": p_dict, "fut": f_dict, "mods": models}
            lbox.success("✅ 推演就绪")

    with c2:
        if res := st.session_state.dl_result:
            act = res['act'].values
            f_mean = np.mean(list(res['fut'].values()), axis=0) if len(res['mods']) > 1 else list(res['fut'].values())[
                0]
            p_mean = np.mean(list(res['preds'].values()), axis=0) if len(res['mods']) > 1 else \
            list(res['preds'].values())[0]
            sr = np.mean(np.sign(np.diff(act)) == np.sign(np.diff(p_mean))) * 100

            c_f = st.columns(4)
            c_f[0].metric("T+1预测", f"{f_mean[0]:.2f}", f"{(f_mean[0] - act[-1]) / act[-1] * 100:.2f}%")
            c_f[1].metric("T+5预测", f"{f_mean[4]:.2f}", f"{(f_mean[4] - act[-1]) / act[-1] * 100:.2f}%")
            c_f[2].metric("方向胜率", f"{sr:.1f}%")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=act, name='真实', line=dict(color='#00ffcc', width=2)))
            for k, v in res['preds'].items(): fig.add_trace(
                go.Scatter(x=res['dates'], y=v, name=k, line=dict(dash='dot')))
            if len(res['mods']) > 1: fig.add_trace(
                go.Scatter(x=res['dates'], y=p_mean, name='集成', line=dict(color='#ff4b4b', width=3)))
            fig.update_layout(height=450, template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              legend=dict(orientation="h", y=1.02))
            st.plotly_chart(fig, use_container_width=True)

elif selected_page == PAGES[6]:
    st.markdown('<div class="glass-card"><h3>🛡️ 审计中心</h3></div>', unsafe_allow_html=True)
    st.text_area("终端日志", "\n".join(st.session_state.sys_logs), height=350)

elif selected_page == PAGES[7]:
    if extensions:
        extensions.render_futures_backtest()
    else:
        st.error("检查 extensions.py")

elif selected_page == PAGES[8]:
    if extensions:
        extensions.render_futures_sandbox()
    else:
        st.error("检查 extensions.py")

elif selected_page == PAGES[9]:
    if extensions: extensions.render_new_features_page()