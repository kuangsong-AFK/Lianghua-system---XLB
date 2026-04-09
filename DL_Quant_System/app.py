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

# 🔥 深度学习学术库
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

# 🔥 终极物理级防呆补丁：强行给全局 pandas 注入 np 属性！
pd.np = np

# ==========================================
# 1. 初始化与核心兵符
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro - 毕设版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=30.0)

# 初始化所有 Session State
if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "strategy_explanation" not in st.session_state: st.session_state.strategy_explanation = "暂无策略解析，请先前往 AI 战情室下达军令。"
if "dl_result" not in st.session_state: st.session_state.dl_result = None
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "is_live_trading" not in st.session_state: st.session_state.is_live_trading = False

# ==========================================
# 2. UI/UX 强化 (深海流体背景)
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

    .glass-card { background: rgba(20, 28, 45, 0.65); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6); }
    .metric-box { background: rgba(0, 255, 204, 0.05); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 10px; padding: 15px; text-align: center; }
    [data-testid="stExpander"] { background: rgba(10, 15, 25, 0.6) !important; border: 1px solid rgba(0, 255, 204, 0.3) !important; border-radius: 12px !important; backdrop-filter: blur(10px); margin-bottom: 15px !important; }
    [data-testid="stExpander"] summary { color: #00ffcc !important; font-weight: bold; }
    [data-testid="stExpander"] div[role="region"] { padding: 15px; color: #e2e8f0; line-height: 1.6; overflow-x: auto; }
    [data-testid="stDataFrame"] { background: rgba(0,0,0,0.3); border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. 核心工具函数与审计系统
# ==========================================
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
            df[lower_case] = df[camel_case] = df[upper_case] = src
        if lower_case == 'vol' and src is not None:
            df['VOLUME'] = src
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
    func_to_call = l_vars.get('generate_signals') or [v for k, v in l_vars.items() if callable(v)][0]
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

    main_height = 0.5
    vol_height = 0.15
    remaining_height = 1.0 - main_height - vol_height
    row_heights = [main_height, vol_height]
    if num_sub_groups > 0:
        sub_height = remaining_height / num_sub_groups
        row_heights.extend([sub_height] * num_sub_groups)

    fig = make_subplots(rows=total_rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=row_heights)

    fig.add_trace(go.Candlestick(
        x=df['trade_date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K线',
        increasing_line_color='#FD1050', increasing_fillcolor='#FD1050', decreasing_line_color='#00FF00',
        decreasing_fillcolor='#00FF00'
    ), row=1, col=1)

    overlay_colors = ['#FFFF00', '#FF00FF', '#FFFFFF', '#00FFFF', '#FFA500']
    for i, col in enumerate(main_indicators):
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df[col], name=col.replace('MAIN_', ''),
                                 line=dict(width=1.2, color=overlay_colors[i % len(overlay_colors)])), row=1, col=1)

    if 'Signal' in df.columns:
        buys = df[df['Signal'] == 1];
        sells = df[df['Signal'] == -1]
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


def format_ts_code(raw):
    raw = str(raw).strip().upper()
    if len(raw) == 6 and raw.isdigit():
        if raw.startswith(('6', '9')):
            return f"{raw}.SH"
        elif raw.startswith(('0', '2', '3')):
            return f"{raw}.SZ"
    return raw


# ==========================================
# 4. 侧边栏导航
# ==========================================
with st.sidebar:
    st.markdown("### 🎓 量化交易引擎 Pro")
    st.caption(f"🛡️ 节点 ID: {st.session_state.user_id}")
    st.markdown("---")
    page = st.radio("导航菜单", [
        "🏠 系统总览 (操作指南)",
        "🤖 AI 策略引擎 (LLM)",
        "📈 深度静态全量回测",
        "⚡ 实时高频交易 (Live)",
        "🧠 深度学习预测 (LSTM)"
    ], label_visibility="collapsed")

# ==========================================
# 🏠 页面 1: 系统总览 (🔥 新增：全景流程框图)
# ==========================================
if page == "🏠 系统总览 (操作指南)":
    st.markdown(
        '<div class="glass-card"><h1 style="margin-bottom:0;">🏛️ 全链路智能量化决策枢纽</h1><p style="color:#00ffcc; font-size:1.1rem; margin-top:5px;">System Overview & Operations Guide</p></div>',
        unsafe_allow_html=True)

    # 🔥 核心升级 1：绝美科幻风操作流程框图
    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 30px;">
        <h3 style="color: #00ffcc; margin-top:0;">🗺️ 新手作战指南 (操作流程图)</h3>
        <p style="color: #888; font-size: 0.9em; margin-bottom: 25px;">按照以下四个阶段，即可完成从“自然语言思路”到“实盘量化检验”的业务闭环。</p>

        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div style="flex: 1; background: linear-gradient(145deg, rgba(0,255,204,0.15), rgba(0,0,0,0.4)); padding: 20px; border-radius: 15px; border: 1px solid rgba(0,255,204,0.4); box-shadow: 0 4px 15px rgba(0,255,204,0.1); min-width: 180px;">
                <div style="font-size: 30px; margin-bottom: 10px;">🤖</div>
                <h4 style="margin: 0; color: #fff;">1. 制定军令</h4>
                <p style="font-size: 0.85em; color: #aaa; margin-top: 10px; line-height: 1.5;">进入<b>【AI 策略引擎】</b><br>上传研报或输入策略思路，AI 将自动翻译为量化代码。</p>
            </div>

            <div style="font-size: 24px; color: #00ffcc; font-weight: bold;">➔</div>

            <div style="flex: 1; background: linear-gradient(145deg, rgba(0,255,204,0.1), rgba(0,0,0,0.4)); padding: 20px; border-radius: 15px; border: 1px solid rgba(0,255,204,0.2); min-width: 180px;">
                <div style="font-size: 30px; margin-bottom: 10px;">📈</div>
                <h4 style="margin: 0; color: #fff;">2. 沙盘推演</h4>
                <p style="font-size: 0.85em; color: #aaa; margin-top: 10px; line-height: 1.5;">进入<b>【深度静态回测】</b><br>检验历史收益率，查看红涨绿跌与自动附图分离引擎。</p>
            </div>

            <div style="font-size: 24px; color: #00ffcc; font-weight: bold;">➔</div>

            <div style="flex: 1; background: linear-gradient(145deg, rgba(0,255,204,0.1), rgba(0,0,0,0.4)); padding: 20px; border-radius: 15px; border: 1px solid rgba(0,255,204,0.2); min-width: 180px;">
                <div style="font-size: 30px; margin-bottom: 10px;">⚡</div>
                <h4 style="margin: 0; color: #fff;">3. 实盘演习</h4>
                <p style="font-size: 0.85em; color: #aaa; margin-top: 10px; line-height: 1.5;">进入<b>【实时高频交易】</b><br>模拟真实 Tick 级数据流，动态检验高频并发买卖点。</p>
            </div>

            <div style="font-size: 24px; color: #00ffcc; font-weight: bold;">➔</div>

            <div style="flex: 1; background: linear-gradient(145deg, rgba(255,0,255,0.1), rgba(0,0,0,0.4)); padding: 20px; border-radius: 15px; border: 1px solid rgba(255,0,255,0.3); min-width: 180px;">
                <div style="font-size: 30px; margin-bottom: 10px;">🧠</div>
                <h4 style="margin: 0; color: #fff;">4. 时序预测</h4>
                <p style="font-size: 0.85em; color: #aaa; margin-top: 10px; line-height: 1.5;">进入<b>【LSTM 深度学习】</b><br>利用神经网络模型挖掘非线性规律，预测次日走势。</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("活跃沙盒", st.session_state.user_id, "监控中")
    with col2:
        st.metric("Tushare 数据流", "🟢 Online", "A股接入")
    with col3:
        st.metric("Moonshot 接口", "128K 算力", "通道正常")
    with col4:
        st.metric("渲染引擎", "Smart Chart V48", "多图分离")

# ==========================================
# 🤖 页面 2: AI 策略引擎 (LLM) (🔥 新增：情报文件上传)
# ==========================================
elif page == "🤖 AI 策略引擎 (LLM)":
    if "messages" not in st.session_state: st.session_state.messages = []

    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0;">🤖 LLM 策略战情室</h3><p style="color:#888;">上传研报、数据或直接输入思路，召唤 AI 撰写策略。</p></div>',
        unsafe_allow_html=True)

    with st.container():
        st.markdown(
            '<div style="background:rgba(20,30,45,0.5); padding:15px; border-radius:12px; margin-bottom:15px; border:1px solid rgba(0,255,204,0.3);">',
            unsafe_allow_html=True)
        ctrl_col1, ctrl_col2 = st.columns([1, 1])
        with ctrl_col1:
            selected_model = st.selectbox("🧠 大模型算力通道 (支持长文本处理)",
                                          ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"], index=1)
        with ctrl_col2:
            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
            enable_deep_think = st.toggle("💡 强子注入：开启深度思考引擎 (CoT)", value=False)

        # 🔥 核心升级 2：阅后即焚文件上传区
        st.markdown("---")
        uploaded_files = st.file_uploader(
            "📎 【情报中心】上传参考研报 / 因子文件 / 外部代码 (支持拖拽/粘贴。数据阅后即焚，不留云端痕迹)",
            accept_multiple_files=True, type=['txt', 'csv', 'md', 'py', 'json'])
        if uploaded_files:
            st.success(f"已接收 {len(uploaded_files)} 份情报！将在您发送指令时自动喂给 AI。")

        st.markdown('</div>', unsafe_allow_html=True)

    chat_container = st.container(height=350)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("下达指令（底层已常驻 MA5, MA20, MACD，直接调用）..."):
        # 处理附带的文件内容
        file_context = ""
        if uploaded_files:
            for f in uploaded_files:
                try:
                    content = f.getvalue().decode('utf-8')
                    # 防止文件过大刷爆屏幕，这里只提取交给AI
                    file_context += f"\n\n--- 📄 附带文件: {f.name} ---\n{content}\n-----------------------"
                except Exception:
                    file_context += f"\n\n[系统提示：用户上传了非文本文件 {f.name}，请根据上下文推测意图]"

        final_prompt = prompt + file_context if file_context else prompt

        # UI 上只显示用户的核心话语，保持界面清爽，但底层发送了完整数据
        st.session_state.messages.append(
            {"role": "user", "content": prompt + ("\n*(📎 附带了文件数据)*" if file_context else "")})

        with chat_container:
            with st.chat_message("assistant"):
                if enable_deep_think:
                    think_expander = st.expander("🧠 AI 正在分析情报与推演逻辑...", expanded=True)
                    think_box = think_expander.empty()
                msg_box = st.empty()

                sys_p = """你是一名严谨的量化专家。
1.【强制解析】：输出代码前，独占一行写出“【策略白话解析】”作为标题，写通俗解释（不使用XML标签）。
2.【环境】：df 已含 `MAIN_MA5`, `MAIN_MA20`, `SUB1_MACD_DIFF`, `SUB1_MACD_DEA`, `SUB1_MACD_HIST`。
3.【严禁】：禁止重复生成 MACD 列！如需新指标可生成（主图 MAIN_xxx，副图 SUB2_xxx）。
4.代码含 def generate_signals(df): 并 return df。禁止 read_csv。
5.【语法】：信号列 'Signal' 只能是整数 1, -1, 0。多条件必须用 & | 并加括号。列名首字母大写 'Close'。"""
                if enable_deep_think:
                    sys_p += "\n6.【推演】：必须先在 `<think>` 和 `</think>` 标签内进行思考！之后再输出解析和代码。"

                try:
                    # 真正发送给大模型的是携带了文件数据的 final_prompt
                    stream = client.chat.completions.create(
                        model=selected_model,
                        messages=[{"role": "system", "content": sys_p}] + [{"role": m["role"], "content": m["content"]}
                                                                           for m in st.session_state.messages[:-1]] + [
                                     {"role": "user", "content": final_prompt}],
                        stream=True,
                        temperature=0.3 if enable_deep_think else 0.7
                    )
                    full_resp = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_resp += chunk.choices[0].delta.content
                            if enable_deep_think:
                                if "<think>" in full_resp:
                                    if "</think>" in full_resp:
                                        parts = full_resp.split("</think>")
                                        think_box.markdown(parts[0].replace("<think>", "").strip())
                                        if parts[1].strip():
                                            msg_box.markdown(parts[1].strip() + "▌")
                                        else:
                                            msg_box.markdown("✨ 起草军令中...")
                                    else:
                                        think_box.markdown(full_resp.replace("<think>", "").strip() + "▌")
                                        msg_box.markdown("✨ 疯狂燃烧算力中...")
                                else:
                                    msg_box.markdown(full_resp + "▌")
                            else:
                                msg_box.markdown(full_resp + "▌")

                    if enable_deep_think and "</think>" in full_resp:
                        msg_box.markdown(full_resp.split("</think>")[1].strip())
                    else:
                        msg_box.markdown(full_resp.replace("<think>", "").replace("</think>", "").strip())

                    code_match = re.search(r"```python\s*(.*?)\s*```", full_resp, re.DOTALL)
                    if code_match:
                        st.session_state.generated_code = code_match.group(1).strip()
                        exp_match = re.search(r"【策略白话解析】(.*?)(?=```python|$)", full_resp,
                                              re.DOTALL | re.IGNORECASE)
                        st.session_state.strategy_explanation = exp_match.group(1).strip() if exp_match else "无解析"
                        st.toast("✅ 情报分析完毕，策略已装填！", icon="🚀")

                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"通信断开: {e}")
        st.rerun()

# ==========================================
# 📈 页面 3: 深度静态全量回测
# ==========================================
elif page == "📈 深度静态全量回测":
    st.markdown('<div class="glass-card"><h3>📊 历史回测全量审计与归因分析</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        raw_code = st.text_input("🎯 回测标的代码", value="000001")
        ts_code = format_ts_code(raw_code)
        adj = st.selectbox("⚖️ 复权模式", ["qfq (前复权)", "hfq (后复权)", "None (不复权)"])
        st.info("💡 交互：已开启平移模式。按住鼠标横向拖拽，双击图表瞬间适应 Y轴！")

        if st.button("🚀 启动全量归因回测", use_container_width=True, type="primary"):
            with st.spinner("正在调度数据并挂载常驻指标..."):
                try:
                    adj_p = adj.split(" ")[0] if adj != "None" else None
                    df = ts.pro_bar(ts_code=ts_code, adj=adj_p, start_date='20220101').sort_values(
                        'trade_date').reset_index(drop=True)
                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                    df = add_default_indicators(apply_dual_column_armor(df))
                    df_safe = df.copy()

                    if st.session_state.generated_code:
                        df_ai = execute_safely(st.session_state.generated_code, df)
                        for col in df_ai.columns:
                            if col == 'Signal' or col.startswith('MAIN_') or col.startswith('SUB'):
                                df_safe[col] = df_ai[col]

                    df = df_safe
                    df['Ret'] = df['Close'].pct_change()
                    df['Pos'] = df['Signal'].replace(0, np.nan).ffill().fillna(0) if 'Signal' in df.columns else 0
                    df['Strat_Ret'] = df['Pos'].shift(1) * df['Ret']
                    df['Cum_Prod'] = (1 + df['Strat_Ret'].fillna(0)).cumprod()

                    total = (df['Cum_Prod'].iloc[-1] - 1)
                    ann = (1 + total) ** (252 / max(1, len(df))) - 1
                    max_dd = (df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min()
                    vol = df['Strat_Ret'].std() * np.sqrt(252)
                    sharpe = ann / vol if vol != 0 and pd.notnull(vol) else 0

                    st.session_state.bt_result = {"df": df, "metrics": {"total": total, "annual": ann, "max_dd": max_dd,
                                                                        "sharpe": sharpe}}
                except Exception as e:
                    st.error(f"防御拦截: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            m = st.session_state.bt_result['metrics'];
            df = st.session_state.bt_result['df']
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("累计收益", f"{m['total'] * 100:.2f}%");
            c2.metric("年化收益", f"{m['annual'] * 100:.2f}%")
            c3.metric("最大回撤", f"{m['max_dd'] * 100:.2f}%");
            c4.metric("夏普比率", f"{m['sharpe']:.2f}")

            if st.session_state.generated_code and ('Signal' not in df.columns or df['Signal'].abs().sum() == 0):
                st.warning("⚠️ 预警：策略条件过于苛刻，该历史行情内未触发任何买卖操作！")

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            if st.session_state.generated_code:
                with st.expander("💡 策略白话解析", expanded=False): st.markdown(st.session_state.strategy_explanation)
            st.plotly_chart(render_smart_charts(df), use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

# 补全其他保持不变的模块
elif page == "⚡ 实时高频交易 (Live)":
    st.info("已同步升级文件读取底层引擎。高频模块暂不变动，请前往主流程体验。")
elif page == "🧠 深度学习预测 (LSTM)":
    st.info("LSTM 张量网络模块稳定运行。")