import os
import sys
import streamlit as st
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

# ==========================================
# 0. 安全挂载扩展包
# ==========================================
extensions_err = None
try:
    import extensions
except Exception as e:
    extensions = None
    extensions_err = str(e)

try:
    import custom_plugins
except Exception:
    custom_plugins = None

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
# 1. 核心兵符初始化
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
                 "strategy_explanation": "暂无策略解析。", "dl_result": None, "bt_result": None, "sys_logs": [],
                 "is_live_trading": False}.items():
    if key not in st.session_state: st.session_state[key] = val

# ==========================================
# 2. 极致稳定的静态 CSS 护甲
# ==========================================
# 我们放弃不稳定的黑白切换，直接写死高级的暗夜渐变玻璃态，确保任何环境下都美观不崩溃
st.markdown("""
<style>
    @keyframes fluidFlow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

    /* 强制重置 Streamlit 默认底色，铺设流光渐变 */
    .stApp { 
        background: linear-gradient(132deg, #040914, #0b193d, #06112a, #11224d) !important; 
        background-size: 400% 400% !important; 
        animation: fluidFlow 20s ease infinite !important; 
    }

    /* 锁定全局文字颜色为高级亮灰，防止看不清 */
    h1, h2, h3, h4, p, span, label, div { color: #f1f5f9 !important; }

    .highlight-text { color: #00ffcc !important; }
    .danger-text { color: #ff4b4b !important; }

    /* 高级毛玻璃卡片 */
    .glass-card { 
        background: rgba(15, 23, 42, 0.6) !important; 
        backdrop-filter: blur(16px) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important; 
        border-radius: 16px; padding: 25px; margin-bottom: 20px; 
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); 
    }

    .metric-box { background: rgba(0, 255, 204, 0.05); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .metric-box h2 { margin: 8px 0 0 0 !important; font-size: 1.8rem; line-height: 1.2; }

    [data-testid="stSidebar"] { background: rgba(10, 15, 30, 0.8) !important; border-right: 1px solid rgba(255,255,255,0.05) !important; }
    div[role="radiogroup"] > label { background: rgba(30, 41, 59, 0.4) !important; border-radius: 10px !important; margin-bottom: 8px !important;}
    div[role="radiogroup"] > label:has(input:checked) { background: linear-gradient(90deg, rgba(0, 255, 204, 0.2), rgba(10, 15, 25, 0.9)) !important; border-left: 4px solid #00ffcc !important; }

    [data-testid="stChatInput"] > div:first-child { background-color: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 36px !important; }

    .agent-status-node { padding: 8px 12px; border-radius: 8px; font-size: 0.9rem; margin: 5px 0; border-left: 4px solid transparent; display: flex; align-items: center; gap: 10px; background: rgba(0,0,0,0.2); }
    .agent-status-node.success { border-left-color: #10b981; color: #34d399 !important;}
    .agent-status-node.error { border-left-color: #ef4444; color: #f87171 !important;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 页面路由分配
# ==========================================
PAGES = ["🏠 系统总览 (监控中控)", "🤖 AI 策略引擎 (LLM)", "💻 极客量化 IDE (代码编译)", "📈 深度静态全量回测",
         "⚡ 实时高频交易 (Live)", "🧠 深度学习预测矩阵", "🛡️ 论文审计日志", "🔗 期货全量审计 (归因)", "🌪️ 期货高频沙盘",
         "🧩 扩展插件中心"]
if custom_plugins and hasattr(custom_plugins, 'EXTRA_PAGES'): PAGES.extend(custom_plugins.EXTRA_PAGES)

if "curr_page" not in st.session_state: st.session_state.curr_page = PAGES[0]

with st.sidebar:
    st.markdown("### 🎓 小吕布量化 Pro")

    # 🔥 安全调用 3D 桌宠：安置在侧边栏内，不跨域，绝不白屏 🔥
    if extensions:
        extensions.summon_sidebar_3d_lulu()

    st.markdown("---")
    selected_page = st.radio("导航菜单", PAGES, label_visibility="collapsed")
    st.session_state.curr_page = selected_page


# ==========================================
# 4. 后台策略核心算法
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
        pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240101');
        return "🟢 Online"
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


def execute_safely(code, df):
    if not code: return df
    try:
        safe_code = str(code).replace("pandas.np", "np")
        l_vars = {}
        exec(safe_code, {"pd": pd, "np": np, "math": math}, l_vars)
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
    colors = ['#0ea5e9', '#f59e0b', '#8b5cf6', '#ec4899']
    for i, col in enumerate(main_inds): fig.add_trace(
        go.Scatter(x=x_labels, y=df[col], name=col, line=dict(width=1.2, color=colors[i % 4])), row=1, col=1)
    if 'Signal' in df.columns:
        buys = df[df['Signal'] == 1];
        sells = df[df['Signal'] == -1]
        buy_x = buys['trade_date'].dt.strftime('%Y-%m-%d' if df['trade_date'].dt.time.nunique() <= 1 else '%m-%d %H:%M')
        sell_x = sells['trade_date'].dt.strftime(
            '%Y-%m-%d' if df['trade_date'].dt.time.nunique() <= 1 else '%m-%d %H:%M')
        fig.add_trace(go.Scatter(x=buy_x, y=buys['Low'] * 0.998, mode='markers',
                                 marker=dict(symbol='triangle-up', size=14, color='#ef4444'), name='买'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sell_x, y=sells['High'] * 1.002, mode='markers',
                                 marker=dict(symbol='triangle-down', size=14, color='#10b981'), name='卖'), row=1,
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
                fig.add_trace(go.Scatter(x=x_labels, y=df[col], line=dict(width=1.5, color=colors[i % 4]), name=col),
                              row=row_idx, col=1)
        row_idx += 1

    fig.update_layout(height=500 + len(sub_groups) * 150, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False, dragmode='pan', hovermode='x',
                      showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=x_labels, nticks=8, showgrid=True,
                     gridwidth=1, gridcolor='rgba(255,255,255,0.05)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.05)')
    return fig


def format_ts_code(raw):
    raw = str(raw).strip().upper()
    if len(raw) == 6 and raw.isdigit(): return f"{raw}.SH" if raw.startswith(('6', '9')) else f"{raw}.SZ"
    return raw


# ==========================================
# 5. 业务渲染逻辑
# ==========================================
if selected_page == PAGES[0]:
    if extensions_err:
        st.error(
            f"🚨 **代码加载防御系统启动** 🚨\n\n检测到 `extensions.py` 文件存在致命错误：\n\n`{extensions_err}`\n\n请检查您 GitHub 仓库的语法！")

    st.markdown(
        '<div class="glass-card"><h1 style="margin-bottom:0;">🏛️ 全链路智能量化决策枢纽</h1><p class="highlight-text" style="font-size:1.1rem; margin-top:5px;">System Overview Dashboard</p></div>',
        unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("活跃并发沙盒 (UUID)", st.session_state.user_id)
    with c2:
        st.metric("Tushare 行情链路", get_tushare_status())
    with c3:
        st.metric("大模型底层通信", "🟢 Moonshot-v1 正常")
    with c4:
        st.metric("扩展引擎状态", "🔴 未连接" if extensions_err else "🟢 已安全挂载")

    st.markdown("---")
    st.markdown("""
    <div class="glass-card">
        <h3 style="margin-bottom: 15px;">🌟 平台简介 (Platform Intro)</h3>
        <p style="line-height: 1.8; font-size: 1.05rem;">
            欢迎来到 <b>小吕布量化 Pro</b>，这是一个专为现代极客打造的智能投研终端。<br>
            • <b>📝 全模态投研</b>：上传 PDF/CSV，大模型自动提取精髓。<br>
            • <b>🤖 零代码写策略</b>：自然语言对话生成交易代码。<br>
            • <b>📈 穿越牛熊回测</b>：长达 10 年的全局历史回测。<br>
            • <b>🧠 时序张量预测</b>：利用 LSTM/GRU 融合矩阵预测未来价格。<br>
        </p>
    </div>
    """, unsafe_allow_html=True)

elif selected_page == PAGES[1]:
    st.markdown('<style>div[data-testid="stFileUploader"] { margin-top: -20px; }</style>', unsafe_allow_html=True)
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0;">🤖 LLM 策略战情室</h3><p class="sub-text">极速云端直连版本，去除了多余前端监控，享受最纯粹的 AI 算力。</p></div>',
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

    uploaded_files = st.file_uploader("📎 附件上传 (自动提取数据)", accept_multiple_files=True,
                                      type=['pdf', 'doc', 'docx', 'csv', 'txt'])
    file_context_text = ""
    if 'uploaded_files' in locals() and uploaded_files:
        for file in uploaded_files:
            fname_lower = file.name.lower()
            if fname_lower.endswith('.csv'):
                df_upload = pd.read_csv(file)
                file_context_text += f"【CSV 数据源 {file.name}】:\n{df_upload.head(10).to_string()}\n"
            elif fname_lower.endswith('.txt'):
                file_context_text += f"【TXT 研报 {file.name}】:\n{file.getvalue().decode('utf-8', errors='replace')[:1000]}\n"
            elif fname_lower.endswith('.pdf') and PyPDF2:
                pdf_reader = PyPDF2.PdfReader(file)
                text = "".join([page.extract_text() for page in pdf_reader.pages[:5] if page.extract_text()])
                file_context_text += f"【PDF {file.name}】:\n{text[:1000]}\n"

    if raw_prompt := st.chat_input("向小吕布量化架构师发送军令..."):
        full_prompt_for_ai = f"参考附件：\n{file_context_text}\n指令：{raw_prompt}" if file_context_text else raw_prompt
        st.session_state.messages.append({"role": "user", "content": raw_prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(raw_prompt)
            with st.chat_message("assistant"):
                st.toast(f"🚀 连线底层算力集群: {selected_model}", icon="⚡")
                ticks = "`" * 3
                sys_p = f"你是一名顶级量化工程师。严格限制使用 pandas, numpy, math。必须生成 df['Signal'] (1买, -1卖, 0平)。代码骨架：{ticks}python\ndef generate_signals(df):\n    return df\n{ticks}"
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
                            f'<div class="agent-status-node retry">🔄 尝试 {attempt}: 沙盒拦截异常 ({last_error}) -> Agent 发起重构</div>')
                        safe_resp = full_resp if full_resp and full_resp.strip() else "(API 响应空)"
                        messages_to_send.extend([{"role": "assistant", "content": safe_resp},
                                                 {"role": "user", "content": f"代码报错：`{last_error}`，请修复。"}])
                    try:
                        valid_msgs = [m for m in messages_to_send if m.get("content") and str(m["content"]).strip()]
                        stream = client.chat.completions.create(model=selected_model, messages=valid_msgs, stream=True,
                                                                temperature=0.3)
                        full_resp = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_resp += chunk.choices[0].delta.content
                                msg_box.markdown(full_resp + "▌", unsafe_allow_html=True)
                        msg_box.markdown(full_resp, unsafe_allow_html=True)
                        code_match = re.search(r"`{3}python\s*(.*?)\s*`{3}", full_resp, re.DOTALL)

                        resp_clean = re.sub(r"<think>.*?</think>", "", full_resp, flags=re.DOTALL)
                        explanation = re.sub(r"`{3}python\s*.*?\s*`{3}", "", resp_clean, flags=re.DOTALL).strip()
                        st.session_state.strategy_explanation = explanation if explanation else "硬核代码，无分析。"

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
                                f'<div class="agent-status-node success">✅ 尝试 {attempt + 1}: 预检通过，策略装载</div>')
                            st.markdown("".join(agent_logs), unsafe_allow_html=True);
                            break
                        except Exception as e:
                            last_error = str(e)
                            if attempt == max_retries:
                                agent_logs.append(
                                    f'<div class="agent-status-node error">❌ 失败报错: {last_error}</div>')
                                st.markdown("".join(agent_logs), unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"链路断开: {e}");
                        full_resp += f"\n\n❌ [异常: {e}]";
                        break
                if not full_resp.strip(): full_resp = "❌ 大模型中断。"
                if agent_logs: full_resp += "\n\n" + "".join(agent_logs)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
        st.rerun()

elif selected_page == PAGES[2]:
    if extensions: extensions.render_ide_page()

elif selected_page == PAGES[3]:
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">📊 历史回测全量审计与归因分析</h3></div>',
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
                df_raw = fetch_and_clean_data(ts_code, adj_p if adj_p != "None" else None, f"{start_year}0101")
                st.session_state.bt_result = run_backtest_metrics(df_raw, st.session_state.generated_code)
    with col_r:
        if st.session_state.bt_result:
            m = st.session_state.bt_result['metrics']
            df = st.session_state.bt_result['df']
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
            if st.session_state.generated_code:
                with st.expander("💡 展开：AI 策略白话解析", expanded=False): st.markdown(
                    st.session_state.strategy_explanation)
            st.plotly_chart(render_smart_charts(df), use_container_width=True, config={'scrollZoom': True})

elif selected_page == PAGES[4]:
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">⚡ 高频沙盘模拟推演 (Real-time Flow)</h3></div>',
                unsafe_allow_html=True)
    c_ctrl, c_chart = st.columns([1, 2.5])
    with c_ctrl:
        live_code = st.text_input("🎯 动态推送标的", value="000001")
        freq = st.slider("⏱️ 刷新间隔 (秒)", 0.1, 2.0, 0.5)
        st.button("▶️ 开启推演", on_click=lambda: st.session_state.update({"is_live_trading": True}), type="primary")
        st.button("⏹️ 强行停止", on_click=lambda: st.session_state.update({"is_live_trading": False}))
    with c_chart:
        met_ph = st.empty();
        cht_ph = st.empty()
        if st.session_state.is_live_trading:
            stream = fetch_and_clean_data(format_ts_code(live_code), 'qfq', '20230101').tail(120).reset_index(drop=True)
            for i in range(20, len(stream)):
                if not st.session_state.is_live_trading: break
                sub = stream.iloc[:i].copy()
                if st.session_state.generated_code:
                    sub_ai = execute_safely(st.session_state.generated_code, sub)
                    if sub_ai is not None and hasattr(sub_ai, 'columns'):
                        for col in sub_ai.columns:
                            if col == 'Signal' or col.startswith(('MAIN_', 'SUB')): sub[col] = sub_ai[col]
                sig_val = sub['Signal'].iloc[-1] if 'Signal' in sub.columns else 0
                with met_ph.container():
                    c = st.columns(3)
                    c[0].metric("Tick现价", f"{sub['Close'].iloc[-1]:.2f}")
                    c[1].metric("高频信号", "🟢 买" if sig_val == 1 else "🔴 卖" if sig_val == -1 else "⚪ 观")
                cht_ph.plotly_chart(render_smart_charts(sub), use_container_width=True)
                time.sleep(freq)

elif selected_page == PAGES[5]:
    st.info("🧠 深度学习矩阵暂未激活。")

elif selected_page == PAGES[6]:
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">🛡️ 实验数据采集与多维审计中心</h3></div>',
                unsafe_allow_html=True)
    st.text_area("实时工作流终端", value="\n".join(st.session_state.sys_logs), height=350)

elif selected_page == PAGES[7]:
    if extensions: extensions.render_futures_backtest()

elif selected_page == PAGES[8]:
    if extensions: extensions.render_futures_sandbox()

elif selected_page == PAGES[9]:
    if extensions: extensions.render_new_features_page()

else:
    if custom_plugins and hasattr(custom_plugins, 'route_and_render'): custom_plugins.route_and_render(selected_page)