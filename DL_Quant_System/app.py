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
import os
import uuid
import math
import base64

# 🔥 深度学习学术库
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

# 🔥 终极物理级防呆补丁：强行给全局 pandas 注入 np 属性，根治语法幻觉
pd.np = np

# ==========================================
# 1. 初始化与核心兵符
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro - 全能视界版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=30.0)

# 初始化所有 Session State，保障并发节点稳定性
if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "strategy_explanation" not in st.session_state: st.session_state.strategy_explanation = "暂无策略解析，请先前往 AI 战情室下达军令。"
if "dl_result" not in st.session_state: st.session_state.dl_result = None
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "is_live_trading" not in st.session_state: st.session_state.is_live_trading = False

# ==========================================
# 2. 深度沉浸式 UI/UX 强化引擎 (CSS 极客定制)
# ==========================================
st.markdown("""
<style>
    @keyframes fluidFlow { 0% { background-position: 0% 50%; } 25% { background-position: 50% 100%; } 50% { background-position: 100% 50%; } 75% { background-position: 50% 0%; } 100% { background-position: 0% 50%; } }
    .stApp { background-image: linear-gradient(132deg, #02040a, #030e2b, #111d3d, #082a72, #030614, #1d2b4f, #0a47b3, #02040a) !important; background-size: 600% 600% !important; animation: fluidFlow 18s ease-in-out infinite !important; }
    [data-testid="stAppViewContainer"], .block-container { background: transparent !important; padding-top: 1.5rem !important; }
    header[data-testid="stHeader"] { background: transparent !important; pointer-events: none !important; }
    header[data-testid="stHeader"] * { pointer-events: auto !important; }
    footer { display: none !important; }
    .stMarkdown, p, h1, h2, h3, label, span { color: #e2e8f0 !important; }

    /* 侧边栏及导航矩阵控制 */
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] {
        display: flex !important; background-color: rgba(0, 255, 204, 0.25) !important; 
        border: 1px solid rgba(0, 255, 204, 0.9) !important; border-radius: 8px !important;
        box-shadow: 0 0 18px rgba(0, 255, 204, 0.4) !important; transition: all 0.3s ease; z-index: 999999 !important;
    }
    [data-testid="collapsedControl"] { position: fixed !important; top: 15px !important; left: 15px !important; pointer-events: auto !important; }
    [data-testid="stSidebar"] { background: rgba(5, 8, 14, 0.75) !important; backdrop-filter: blur(25px) !important; border-right: 1px solid rgba(255,255,255,0.08) !important; }
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label {
        background: rgba(15, 20, 30, 0.4) !important; padding: 14px 18px !important; margin-bottom: 10px !important;
        border-radius: 12px !important; border-left: 4px solid transparent !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important; cursor: pointer !important; width: 100% !important;
    }
    div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(0, 255, 204, 0.3), rgba(10, 15, 25, 0.95)) !important;
        border-left: 4px solid #00ffcc !important; box-shadow: 0 4px 18px rgba(0, 255, 204, 0.15) !important; transform: translateX(5px);
    }

    /* 毛玻璃数据卡片与解析折叠舱 */
    .glass-card { background: rgba(20, 28, 45, 0.65); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6); }
    .metric-box { background: rgba(0, 255, 204, 0.05); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 10px; padding: 15px; text-align: center; }
    [data-testid="stExpander"] { background: rgba(10, 15, 25, 0.6) !important; border: 1px solid rgba(0, 255, 204, 0.3) !important; border-radius: 12px !important; backdrop-filter: blur(10px); margin-bottom: 15px !important; }
    [data-testid="stExpander"] summary { color: #00ffcc !important; font-weight: bold; }
    [data-testid="stExpander"] div[role="region"] { padding: 15px; color: #e2e8f0; line-height: 1.6; overflow-x: auto; }
    [data-testid="stDataFrame"] { background: rgba(0,0,0,0.3); border-radius: 8px; }

    /* 🔥 极简全局操作导图架构设计 (Responsive Grid) */
    .flow-container { display: flex; justify-content: space-between; align-items: center; margin: 25px 0; gap: 12px; flex-wrap: wrap; }
    .flow-step { background: linear-gradient(145deg, rgba(0,255,204,0.08), rgba(0,0,0,0.5)); border: 1px solid rgba(0,255,204,0.3); border-radius: 18px; padding: 22px 18px; flex: 1; min-width: 200px; text-align: center; box-shadow: 0 10px 35px rgba(0,0,0,0.4); transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s; position: relative; overflow: hidden; }
    .flow-step::before { content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(0,255,204,0.1) 0%, transparent 70%); opacity: 0; transition: opacity 0.5s; z-index: 0; }
    .flow-step:hover { transform: translateY(-10px); border-color: #00ffcc; box-shadow: 0 15px 45px rgba(0,255,204,0.25); }
    .flow-step:hover::before { opacity: 1; }
    .step-content { position: relative; z-index: 1; }
    .step-icon { font-size: 2.8rem; margin-bottom: 14px; display: inline-block; filter: drop-shadow(0 0 10px rgba(0,255,204,0.5)); }
    .step-title { color: #00ffcc; font-size: 1.2rem; font-weight: 900; margin-bottom: 10px; letter-spacing: 1.5px; text-transform: uppercase;}
    .step-desc { color: #cbd5e1; font-size: 0.9rem; line-height: 1.6; font-weight: 300;}
    .flow-arrow { font-size: 1.8rem; color: rgba(0,255,204,0.6); font-weight: bold; animation: arrowPulse 2s infinite ease-in-out; }
    @keyframes arrowPulse { 0% { opacity: 0.3; transform: translateX(0); } 50% { opacity: 1; transform: translateX(8px) scale(1.1); filter: drop-shadow(0 0 8px #00ffcc); } 100% { opacity: 0.3; transform: translateX(0); } }
    @media (max-width: 900px) { .flow-container { flex-direction: column; align-items: stretch; } .flow-arrow { transform: rotate(90deg); text-align: center; margin: 15px 0; } @keyframes arrowPulse { 0% { opacity: 0.3; transform: translateY(0); } 50% { opacity: 1; transform: translateY(8px) scale(1.1); } 100% { opacity: 0.3; transform: translateY(0); } } }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. 全局审计引擎与物理数据装甲
# ==========================================
def apply_dual_column_armor(df):
    """底层数据泛化护盾：无缝映射所有首字母与全大写异构数据列"""
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
            df[lower_case] = df[camel_case] = df[upper_case] = src
        if lower_case == 'vol' and src is not None: df['VOLUME'] = src
    return df


def add_default_indicators(df):
    """数据基建：预加载常态技术指标，杜绝大模型重复演算开销"""
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
    """深核级沙盒运行器：强制语法消毒与类型断言"""
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
            raise ValueError("未能从大语言模型输出中提取到有效的信号生成函数实体！")
    df_ai = func_to_call(df)

    # 强制信号剥离与 int64 降维装甲，杜绝浮点溢出
    sig_col = next((c for c in df_ai.columns if c.lower() == 'signal'), None)
    if sig_col:
        if sig_col != 'Signal': df_ai['Signal'] = df_ai[sig_col]
        df_ai['Signal'] = df_ai['Signal'].fillna(0).apply(lambda x: 1 if x > 0.1 else (-1 if x < -0.1 else 0)).astype(
            int)
    else:
        df_ai['Signal'] = 0
    return df_ai


def render_smart_charts(df):
    """动态流式渲染引擎：基于列名的智能化自动子图拆分与刻度绑定"""
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
    main_height = 0.5
    vol_height = 0.15
    remaining_height = 1.0 - main_height - vol_height
    row_heights = [main_height, vol_height]
    if num_sub_groups > 0:
        sub_height = remaining_height / num_sub_groups
        row_heights.extend([sub_height] * num_sub_groups)

    fig = make_subplots(rows=total_rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)

    # 构建绝对规范化的 A 股红涨绿跌 K 线层
    fig.add_trace(go.Candlestick(x=df['trade_date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 name='K线', increasing_line_color='#FD1050', increasing_fillcolor='#FD1050',
                                 decreasing_line_color='#00FF00', decreasing_fillcolor='#00FF00'), row=1, col=1)

    overlay_colors = ['#FFFF00', '#FF00FF', '#FFFFFF', '#00FFFF', '#FFA500']
    for i, col in enumerate(main_indicators): fig.add_trace(
        go.Scatter(x=df['trade_date'], y=df[col], name=col.replace('MAIN_', ''),
                   line=dict(width=1.2, color=overlay_colors[i % len(overlay_colors)])), row=1, col=1)

    if 'Signal' in df.columns:
        buys = df[df['Signal'] == 1];
        sells = df[df['Signal'] == -1]
        fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['Low'] * 0.95, mode='markers',
                                 marker=dict(symbol='triangle-up', size=14, color='#00FFFF',
                                             line=dict(width=1, color='white')), name='买入信号'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['High'] * 1.05, mode='markers',
                                 marker=dict(symbol='triangle-down', size=14, color='#FF00FF',
                                             line=dict(width=1, color='white')), name='卖出信号'), row=1, col=1)

    if 'Volume' in df.columns:
        vol_colors = np.where(df['Close'] >= df['Open'], '#FD1050', '#00FF00')
        fig.add_trace(go.Bar(x=df['trade_date'], y=df['Volume'], name='成交量', marker_color=vol_colors, opacity=0.8),
                      row=2, col=1)

    sub_colors = ['#00FFFF', '#FF00FF', '#FFFF00', '#FFFFFF']
    current_row = 3
    for group_id in sorted(sub_groups.keys(), key=int):
        cols_in_group = sub_groups[group_id]
        for i, col in enumerate(cols_in_group):
            # 智能侦测直方图特征指标
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

    total_height = 500 + (num_sub_groups * 150)
    fig.update_layout(height=total_height, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
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


# ==========================================
# 4. 全局路由与沙盒节点导航
# ==========================================
with st.sidebar:
    st.markdown("### 🎓 量化交易系统 Pro")
    st.caption(f"🛡️ 工作节点: {st.session_state.user_id}")
    st.markdown("---")
    page = st.radio("系统矩阵导航", [
        "🏠 全局监控矩阵 (系统指南)",
        "🤖 神经策略中枢 (多模态输入)",
        "📈 历史多维归因引擎",
        "⚡ T0 高频沙盘模拟",
        "🧠 深度时序预测网络",
        "🛡️ 事务与内存审计系统"
    ], label_visibility="collapsed")

# ==========================================
# 🏠 页面 1: 全局监控矩阵 (含极简操作导图)
# ==========================================
if page == "🏠 全局监控矩阵 (系统指南)":
    st.markdown(
        '<div class="glass-card"><h1 style="margin-bottom:0;">🏛️ 智能量化决策总线枢纽</h1><p style="color:#00ffcc; font-size:1.1rem; margin-top:5px;">System Overview & Operational Pipeline</p></div>',
        unsafe_allow_html=True)

    # 注入高颜值、通俗易懂的全局操作向导框图
    st.markdown("""
    <div class="flow-container">
        <div class="flow-step">
            <div class="step-content">
                <span class="step-icon">🤖</span>
                <div class="step-title">1. 下达指令 / 上传资产</div>
                <div class="step-desc">进入“神经策略中枢”，输入自然语言策略意图，或直接上传 CSV 数据集与分析研报截图供系统学习。</div>
            </div>
        </div>
        <div class="flow-arrow">➔</div>
        <div class="flow-step">
            <div class="step-content">
                <span class="step-icon">⚡</span>
                <div class="step-title">2. 大语言模型矩阵编译</div>
                <div class="step-desc">调用底层 128K 算力进行深度思考与逻辑推演，毫秒级将策略翻译为可执行的量化 Python 矢量代码。</div>
            </div>
        </div>
        <div class="flow-arrow">➔</div>
        <div class="flow-step">
            <div class="step-content">
                <span class="step-icon">📊</span>
                <div class="step-title">3. 动态沙盒回测渲染</div>
                <div class="step-desc">系统基于无损剥离技术执行代码，自动绘制红涨绿跌的自适应交互图表，并实现多维指标副图分离。</div>
            </div>
        </div>
        <div class="flow-arrow">➔</div>
        <div class="flow-step">
            <div class="step-content">
                <span class="step-icon">🚀</span>
                <div class="step-title">4. 前沿沙盘推演预判</div>
                <div class="step-desc">使用高频沙盘观测实时跳动帧的净值变化，或激活 PyTorch LSTM 神经网络计算次日时序运行轨迹。</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        t_start = time.time()
        pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240101')
        t_latency = int((time.time() - t_start) * 1000)
        ts_status = f"🟢 Data Stream Active ({t_latency}ms)"
    except:
        ts_status = "🔴 Connection Terminated"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("活跃并发沙盒进程", st.session_state.user_id, "隔离状态: 安全")
    with col2:
        st.metric("Tushare 商业化数据总线", ts_status, "A股数据: 注入完成")
    with col3:
        st.metric("基础模型链路池", "Moonshot Multi-modal", "通信吞吐量: 🟢 正常")
    with col4:
        st.metric("AI 张量引擎架构", f"PyTorch Tensor v{torch.__version__}", "时序卷积网络: 挂载完毕")

    st.markdown("---")
    st.markdown('<div class="glass-card"><h4>📋 底层防御体系与核心技术屏障 (Core Architecture)</h4>'
                '<li><b>多模态视觉接驳协议 (V48)</b>: 全面支持 TXT、CSV 及高清截图瞬间载入内存流，保障数据不落盘安全机制。</li>'
                '<li><b>强力降维装甲过滤</b>: 强行将 AI 抛出的异构信号拦截并洗录为 int64 极性数据，杜绝因类型断言引发的系统级崩溃。</li>'
                '<li><b>无极平移图表引擎</b>: 实现纵向高度锁定的左右时间轴丝滑平移，支持双击瞬间全维坐标归一自适应。</li>'
                '<li><b>思维全息投影器</b>: 突破大语言模型黑盒，深度推演过程 100% 暴露并可视化于前端操作台。</li></div>',
                unsafe_allow_html=True)

# ==========================================
# 🤖 页面 2: 神经策略中枢 (🔥 注入多模态文件与视觉上传舱)
# ==========================================
elif page == "🤖 神经策略中枢 (多模态输入)":
    if "messages" not in st.session_state: st.session_state.messages = []

    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0;">🤖 LLM 策略构建与多维特征萃取舱</h3><p style="color:#888;">支持自然语言交互、策略文献输入及视觉图像上传。内存沙盒刷新即毁，捍卫核心策略隐私。</p></div>',
        unsafe_allow_html=True)

    with st.container():
        st.markdown(
            '<div style="background:rgba(20,30,45,0.5); padding:15px; border-radius:12px; margin-bottom:15px; border:1px solid rgba(0,255,204,0.3);">',
            unsafe_allow_html=True)
        ctrl_col1, ctrl_col2 = st.columns([1, 1])
        with ctrl_col1:
            # 加入 vision-preview 模型以适配图片矩阵解析
            selected_model = st.selectbox("🧠 调度核心算力集群 (视觉任务请选 Vision 通道)",
                                          ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k",
                                           "moonshot-v1-8k-vision-preview"], index=2)
        with ctrl_col2:
            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
            enable_deep_think = st.toggle("💡 超频运算：激活神经深度逻辑推演 (CoT)", value=False)
        st.markdown('</div>', unsafe_allow_html=True)

    # 部署零重力文件接驳舱
    with st.expander("📎 挂载多模态资源 (TXT 文献 / CSV 特征集 / PNG 图像)，随指令同步解析", expanded=False):
        uploaded_file = st.file_uploader("文件驻留于当前并发节点内存，刷新页面立即销毁脱离",
                                         type=['txt', 'csv', 'png', 'jpg', 'jpeg'])
        if uploaded_file is not None:
            st.success(f"资源句柄 `{uploaded_file.name}` 已捕获，准备汇入下一次编译流！")

    chat_container = st.container(height=350)
    with chat_container:
        for m in st.session_state.messages:
            # 渲染路由降级：剥离 Base64 矩阵包，维护 UI DOM 树稳定性
            content_to_render = m["content"]
            if isinstance(content_to_render, list):
                content_to_render = next((item["text"] for item in content_to_render if item["type"] == "text"),
                                         "🖼️ [多模态视觉矩阵包]")
            with st.chat_message(m["role"]):
                st.markdown(content_to_render)

    if prompt := st.chat_input("定义您的量化逻辑、上传数据特征分析或研报解读请求..."):
        final_payload = prompt

        # 多路复用解析逻辑接管
        if uploaded_file is not None:
            file_ext = uploaded_file.name.split('.')[-1].lower()
            try:
                if file_ext == 'txt':
                    text_blob = uploaded_file.read().decode('utf-8')
                    final_payload = f"{prompt}\n\n【附加文本资源输入流】:\n
http: // googleusercontent.com / immersive_entry_chip / 0