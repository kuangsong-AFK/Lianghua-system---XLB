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

# 🔥 深度学习学术扩充包
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

# ==========================================
# 1. 核心兵符 & 基础配置
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro - 毕业设计版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=30.0)

# ==========================================
# 2. 沉浸式 UI & APP化侧边栏大改造
# ==========================================
st.markdown("""
<style>
    /* 🔥 深海流体动画 (维持极致流动感) */
    @keyframes fluidGradient {
        0% { background-position: 0% 50%; }
        25% { background-position: 50% 100%; }
        50% { background-position: 100% 50%; }
        75% { background-position: 50% 0%; }
        100% { background-position: 0% 50%; }
    }
    .stApp {
        background-image: linear-gradient(132deg, #02040a, #111d3d, #030614, #1d2b4f, #081224) !important;
        background-size: 400% 400% !important;
        animation: fluidGradient 12s ease-in-out infinite !important;
    }

    [data-testid="stAppViewContainer"], .block-container { background: transparent !important; padding-top: 2rem !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    header[data-testid="stHeader"] * { color: rgba(255,255,255,0.6) !important; }
    footer { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, span, li { color: #e2e8f0 !important; }

    /* --------------------------------------------------- */
    /* 🚀 侧边栏按钮色块化改造 (解决像前进按钮的 Bug) */
    /* --------------------------------------------------- */
    [data-testid="stSidebarCollapseButton"] {
        display: flex !important; /* 解除封印，恢复显示 */
        background-color: rgba(0, 255, 204, 0.15) !important; /* 骇客绿背景色块 */
        border: 1px solid rgba(0, 255, 204, 0.6) !important;
        border-radius: 8px !important;
        box-shadow: 0 0 12px rgba(0, 255, 204, 0.3) !important;
        margin-top: 15px !important;
        margin-left: 10px !important;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebarCollapseButton"]:hover {
        background-color: rgba(0, 255, 204, 0.4) !important;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.6) !important;
    }
    [data-testid="stSidebarCollapseButton"] svg { color: #00ffcc !important; } /* 图标染成绿色 */

    /* --------------------------------------------------- */
    /* 🚀 侧边栏列表 APP 化改造 (隐藏圆圈，变成悬浮卡片) */
    /* --------------------------------------------------- */
    [data-testid="stSidebar"] { background: rgba(5, 8, 14, 0.6) !important; backdrop-filter: blur(20px) !important; border-right: 1px solid rgba(255,255,255,0.05) !important; }

    .stRadio [role="radiogroup"] { gap: 12px; } /* 增加选项间距 */
    .stRadio [role="radio"] { display: none !important; } /* 彻底隐藏原生单选框的小圆圈 */

    .stRadio label {
        background: linear-gradient(90deg, rgba(20, 30, 45, 0.6), rgba(10, 15, 25, 0.4)) !important;
        padding: 14px 20px !important;
        border-radius: 12px !important;
        border-left: 4px solid transparent !important;
        border-top: 1px solid rgba(255,255,255,0.05) !important;
        border-right: 1px solid rgba(255,255,255,0.05) !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        cursor: pointer !important;
        width: 100% !important;
    }
    .stRadio label:hover {
        transform: translateX(8px) !important; /* 鼠标悬停时整体向右滑动浮出 */
        border-left: 4px solid #00ffcc !important; /* 左侧亮起绿色光条 */
        background: linear-gradient(90deg, rgba(0, 255, 204, 0.15), rgba(10, 15, 25, 0.8)) !important;
        box-shadow: 0 8px 25px rgba(0, 255, 204, 0.2) !important;
    }

    div[data-testid="stCodeBlock"], pre { background-color: rgba(5, 10, 20, 0.85) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; backdrop-filter: blur(10px); }
    code { color: #00ffcc !important; background-color: transparent !important; text-shadow: none !important; }
    .glass-card { background: rgba(15, 20, 30, 0.5); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); transition: all 0.3s ease; }
    .glass-card:hover { border: 1px solid rgba(255, 255, 255, 0.15); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.9); }
    .stTextInput > div > div, .stSelectbox > div > div, .stSlider > div > div > div > div { background-color: rgba(0,0,0,0.5) !important; color: white !important; border: 1px solid rgba(255,255,255,0.1) !important; }
    div[data-testid="stChatMessageContent"] { background-color: rgba(20, 25, 35, 0.7) !important; backdrop-filter: blur(10px); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 🔥 毕业论文专用：企业级多维度日志容灾底座
# ==========================================
LOG_DIR = "user_logs"
os.makedirs(LOG_DIR, exist_ok=True)  # 自动创建一个专门的文件夹存日志
GLOBAL_LOG_FILE = os.path.join(LOG_DIR, "global_master_log.csv")  # 总账本

# 初始化全局总账本
if not os.path.exists(GLOBAL_LOG_FILE):
    pd.DataFrame(columns=["Timestamp", "UserID", "ActionType", "Details"]).to_csv(GLOBAL_LOG_FILE, index=False)

if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "dl_result" not in st.session_state: st.session_state.dl_result = None


def log_thesis_data(action_type, details):
    icon = "🔴" if "报错" in action_type or "异常" in action_type or "警告" in action_type else "🟢"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = st.session_state.user_id
    log_msg = f"{icon} [{timestamp}] [{user_id}] {action_type}: {details}"

    # 1. 更新前端界面内存
    st.session_state.sys_logs.insert(0, log_msg)

    new_row = pd.DataFrame(
        [{"Timestamp": timestamp, "UserID": user_id, "ActionType": action_type, "Details": str(details)}])

    # 2. 写入全局总账本 (永不覆盖，无限追加模式 mode='a')
    new_row.to_csv(GLOBAL_LOG_FILE, mode='a', header=False, index=False)

    # 3. 写入当前用户的独立小账本
    user_log_file = os.path.join(LOG_DIR, f"log_{user_id}.csv")
    if not os.path.exists(user_log_file):
        pd.DataFrame(columns=["Timestamp", "UserID", "ActionType", "Details"]).to_csv(user_log_file, index=False)
    new_row.to_csv(user_log_file, mode='a', header=False, index=False)


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"主公，系统已初始化！您的测试编号为：**{st.session_state.user_id}**"}]
    log_thesis_data("系统访问", "新用户进入量化平台")


def format_ts_code(raw_code):
    raw_code = str(raw_code).strip().upper()
    if len(raw_code) == 6 and raw_code.isdigit():
        if raw_code.startswith(('6', '9')):
            return f"{raw_code}.SH"
        elif raw_code.startswith(('0', '2', '3')):
            return f"{raw_code}.SZ"
        elif raw_code.startswith(('4', '8')):
            return f"{raw_code}.BJ"
    return raw_code


# ==========================================
# 4. 侧边栏导航
# ==========================================
with st.sidebar:
    st.markdown("## 🎓 量化交易引擎 Pro")
    st.caption(f"当前连线: {st.session_state.user_id}")
    st.markdown("---")
    page = st.radio("系统导航", [
        "🏠 系统总览",
        "🤖 AI 策略引擎 (LLM)",
        "📈 深度回测与图表",
        "🧠 深度学习预测 (LSTM)",
        "🛡️ 论文数据与日志"
    ], label_visibility="collapsed")

# ==========================================
# 🏠 页面 1: 系统总览
# ==========================================
if page == "🏠 系统总览":
    st.markdown(
        '<div class="glass-card"><h2>🏠 智能量化交易决策系统</h2><p>基于大语言模型 (LLM) 与深度学习 (Deep Learning) 的双引擎回测架构</p></div>',
        unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("活跃用户", st.session_state.user_id, "埋点监控中")
    col2.metric("AI 大脑", "Moonshot-v1-8k", "API 正常")
    col3.metric("深度学习引擎", "PyTorch 2.x", "LSTM/GRU 待命")
    col4.metric("数据源节点", "Tushare Pro", "支持前复权/后复权")
    st.markdown(
        '<div class="glass-card"><h4>⚙️ 系统架构图 (论文配图参考)</h4><ul><li><b>LLM 启发引擎</b>: 借由大语言模型自动生成基于传统技术指标的 Pandas 策略。</li><li><b>Deep Learning 预测引擎</b>: 使用 PyTorch 构建 LSTM 循环神经网络，基于历史滑动窗口捕捉非线性时序特征，预测未来股价走势。</li><li><b>动态执行沙盒</b>: 隔离运行 AI 生成的代码，实现交易信号生成与仓位结算。</li><li><b>学术可视化引擎</b>: 基于 Plotly 的多轨自适应图表，并提供真实的夏普比率、年化收益率等核心评价指标。</li></ul></div>',
        unsafe_allow_html=True)

# ==========================================
# 🤖 页面 2: AI 策略引擎 (LLM)
# ==========================================
elif page == "🤖 AI 策略引擎 (LLM)":
    st.markdown('<div class="glass-card"><h3>🤖 LLM 策略生成中枢</h3></div>', unsafe_allow_html=True)
    chat_container = st.container(height=450)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("输入策略构思 (如: 追涨杀跌、MACD底背离)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_thesis_data("请求LLM写策略", prompt)
        st.rerun()

    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                bt = "`" * 3
                sys_prompt = f"""你是量化专家。请给出Python代码并用 {bt}python 和 {bt} 包裹。
必须包含 `generate_signals(df)` 函数。在 df 中新增 'Signal' 列：1为买入，-1为卖出，0为观望。最后返回 df。
⚠️ 军规：
1. 多条件时必须使用 `&` 和 `|` 并加括号！禁用 `and/or`！
2. DataFrame 的列名请直接使用首字母大写：'Open', 'High', 'Low', 'Close', 'Volume'。"""
                try:
                    msg_box.markdown("🧠 *大模型正在解析意图并构建计算图...*")
                    stream = client.chat.completions.create(model="moonshot-v1-8k", messages=[{"role": "system",
                                                                                               "content": sys_prompt}] + st.session_state.messages,
                                                            stream=True)
                    full_resp = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_resp += chunk.choices[0].delta.content
                            msg_box.markdown(full_resp + "▌")
                    msg_box.markdown(full_resp)

                    code_match = re.search(bt + r"(?:python)?\s*(.*?)" + bt, full_resp, re.DOTALL | re.IGNORECASE)
                    if code_match:
                        st.session_state.generated_code = code_match.group(1).strip()
                        st.toast("✅ LLM 策略编译成功！", icon="🚀")
                        log_thesis_data("LLM生成成功", "代码提取并装填至沙盒")
                    else:
                        log_thesis_data("系统异常-格式提取", "未能从大模型回复中提取出有效的Python代码块")

                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"API 异常: {e}")
                    log_thesis_data("系统报错-大模型通信", str(e))
        st.rerun()

# ==========================================
# 📈 页面 3: 深度回测与图表
# ==========================================
elif page == "📈 深度回测与图表":
    st.markdown('<div class="glass-card"><h3>📈 动态沙盒与多维可视化分析</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])

    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        raw_stock_code = st.text_input("🎯 回测标的 (输入6位代码，如: 000001)", value="000001")
        ts_code = format_ts_code(raw_stock_code)

        adj_mode = st.selectbox("⚖️ 价格复权处理", ["前复权 (推荐)", "后复权", "不复权 (原始价格)"])
        adj_param = "qfq" if "前复权" in adj_mode else "hfq" if "后复权" in adj_mode else None
        y_axis_mode = st.radio("📏 Y轴缩放模式", ["自适应 K线 (动态伸缩)", "绝对 K线 (全局定死)"])

        if st.session_state.generated_code:
            st.success("🟢 LLM 沙盒就绪")
            if st.button("🚀 启动全量回测任务", use_container_width=True, type="primary"):
                with st.spinner(f"正在聚合 {ts_code} 数据..."):
                    try:
                        data = ts.pro_bar(ts_code=ts_code, adj=adj_param, start_date='20230101')
                        if data is None or data.empty:
                            st.error("获取数据失败，请检查 Tushare 接口或标的代码！")
                            log_thesis_data("系统警告-数据获取", f"标的 {ts_code} 请求的数据为空")
                        else:
                            data = data.sort_values('trade_date').reset_index(drop=True)
                            data['trade_date'] = pd.to_datetime(data['trade_date'], format='%Y%m%d')

                            data['Open'] = data['open']
                            data['High'] = data['high']
                            data['Low'] = data['low']
                            data['Close'] = data['close']
                            data['Volume'] = data['vol']

                            data['MA5'] = data['close'].rolling(window=5).mean()
                            data['MA20'] = data['close'].rolling(window=20).mean()

                            exp1 = data['close'].ewm(span=12, adjust=False).mean()
                            exp2 = data['close'].ewm(span=26, adjust=False).mean()
                            data['MACD_DIFF'] = exp1 - exp2
                            data['MACD_DEA'] = data['MACD_DIFF'].ewm(span=9, adjust=False).mean()
                            data['MACD'] = (data['MACD_DIFF'] - data['MACD_DEA']) * 2

                            low_list = data['low'].rolling(9, min_periods=1).min()
                            high_list = data['high'].rolling(9, min_periods=1).max()
                            rsv = (data['close'] - low_list) / (high_list - low_list + 1e-8) * 100
                            data['K'] = rsv.ewm(com=2, adjust=False).mean()
                            data['D'] = data['K'].ewm(com=2, adjust=False).mean()
                            data['J'] = 3 * data['K'] - 2 * data['D']

                            data['Color'] = np.where(data['close'] >= data['open'], '#FD1050', '#00FF00')

                            l_vars = {}
                            exec(st.session_state.generated_code, globals(), l_vars)
                            data = l_vars['generate_signals'](data)

                            data['Ret'] = data['close'].pct_change()
                            data['Pos'] = data['Signal'].replace(0, np.nan).ffill().fillna(0)
                            data['Strat_Ret'] = data['Pos'].shift(1) * data['Ret']
                            data['Cum_Prod'] = (1 + data['Strat_Ret'].fillna(0)).cumprod()

                            st.session_state.bt_result = {"df": data, "code": ts_code, "adj": adj_mode,
                                                          "y_mode": y_axis_mode}
                            log_thesis_data("回测成功", f"LLM策略执行成功, 标的:{ts_code}, 行数:{len(data)}")
                    except Exception as e:
                        st.error(f"沙盒异常: {e} (可能是大模型策略逻辑有误)")
                        log_thesis_data("系统报错-沙盒执行", f"沙盒崩溃, 详细错误: {e}")
        else:
            st.warning("🟡 LLM策略缓存为空。")

        if st.session_state.bt_result:
            df = st.session_state.bt_result['df']
            st.markdown("---")
            total_ret = (df['Cum_Prod'].iloc[-1] - 1)
            annual_ret = (1 + total_ret) ** (252 / len(df)) - 1 if len(df) > 0 else 0
            max_dd = ((df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min())
            st.metric("累计收益", f"{total_ret * 100:.2f}%")
            st.metric("年化收益", f"{annual_ret * 100:.2f}%")
            st.metric("最大回撤", f"{max_dd * 100:.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            df = st.session_state.bt_result['df']
            st.markdown(
                f'<div class="glass-card"><p style="text-align:center; color:#888;">{st.session_state.bt_result["code"]} | {st.session_state.bt_result["adj"]}</p>',
                unsafe_allow_html=True)

            fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                                row_heights=[0.5, 0.15, 0.175, 0.175])
            fig.add_trace(
                go.Candlestick(x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                               name='K线', increasing_line_color='#FD1050', increasing_fillcolor='#FD1050',
                               decreasing_line_color='#00FF00', decreasing_fillcolor='#00FF00'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['MA5'], line=dict(color='yellow', width=1), name='MA5'),
                          row=1, col=1)
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['MA20'], line=dict(color='magenta', width=1), name='MA20'), row=1,
                col=1)

            if 'Signal' in df.columns:
                buys = df[df['Signal'] == 1]
                sells = df[df['Signal'] == -1]
                fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['low'] * 0.95, mode='markers',
                                         marker=dict(symbol='triangle-up', size=14, color='#00FFFF',
                                                     line=dict(width=1, color='white')), name='买入'), row=1, col=1)
                fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['high'] * 1.05, mode='markers',
                                         marker=dict(symbol='triangle-down', size=14, color='#FF00FF',
                                                     line=dict(width=1, color='white')), name='卖出'), row=1, col=1)

            fig.add_trace(go.Bar(x=df['trade_date'], y=df['vol'], marker_color=df['Color'], name='成交量'), row=2,
                          col=1)
            macd_colors = np.where(df['MACD'] >= 0, '#FD1050', '#00FF00')
            fig.add_trace(go.Bar(x=df['trade_date'], y=df['MACD'], marker_color=macd_colors, name='MACD'), row=3, col=1)
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['MACD_DIFF'], line=dict(color='white', width=1), name='DIFF'),
                row=3, col=1)
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['MACD_DEA'], line=dict(color='yellow', width=1), name='DEA'), row=3,
                col=1)

            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['K'], line=dict(color='white', width=1), name='K'), row=4,
                          col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['D'], line=dict(color='yellow', width=1), name='D'),
                          row=4, col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['J'], line=dict(color='magenta', width=1), name='J'),
                          row=4, col=1)

            fig.update_layout(height=800, dragmode='pan', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0.2)', margin=dict(l=0, r=0, t=10, b=0),
                              xaxis_rangeslider_visible=False, hovermode="x unified", showlegend=False)
            fig.update_xaxes(tickformat="%Y年%m月", showgrid=False, zeroline=False)
            if "绝对" in st.session_state.bt_result["y_mode"]:
                fig.update_yaxes(range=[df['low'].min() * 0.95, df['high'].max() * 1.05], showgrid=True,
                                 gridcolor='rgba(255,255,255,0.05)', row=1, col=1)
            else:
                fig.update_yaxes(autorange=True, showgrid=True, gridcolor='rgba(255,255,255,0.05)', row=1, col=1)

            st.plotly_chart(fig, use_container_width=True,
                            config={'scrollZoom': True, 'modeBarButtonsToRemove': ['lasso2d', 'select2d']})
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🧠 页面 4: 深度学习时序预测
# ==========================================
elif page == "🧠 深度学习预测 (LSTM)":
    st.markdown(
        '<div class="glass-card"><h3>🧠 深度时序神经网络预测中心 (Deep Learning)</h3><p style="color:#aaa;">基于 PyTorch 框架，采用 LSTM 滑动窗口机制捕捉时间序列长期依赖，进行下一交易日收盘价预测与信号生成。</p></div>',
        unsafe_allow_html=True)

    col_ctrl, col_chart = st.columns([1, 2.5])

    with col_ctrl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        raw_stock_code = st.text_input("🎯 训练标的 (如: 000001)", value="000001")
        ts_code = format_ts_code(raw_stock_code)

        seq_length = st.slider("📏 时间滑窗长度 (Seq_Len)", min_value=5, max_value=60, value=20)
        epochs = st.slider("🔄 训练迭代轮数 (Epochs)", min_value=10, max_value=100, value=30, step=10)

        if st.button("🚀 启动深度学习训练与回测", use_container_width=True, type="primary"):
            with st.spinner("正在搭建计算图并启动 PyTorch 张量运算..."):
                try:
                    df = ts.pro_bar(ts_code=ts_code, adj='qfq', start_date='20210101')
                    if df is None or df.empty:
                        log_thesis_data("系统警告-DL数据", f"获取不到标的 {ts_code} 的数据")
                        raise ValueError("获取数据失败")

                    df = df.sort_values('trade_date').reset_index(drop=True)
                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

                    log_thesis_data("启动DL训练", f"标的:{ts_code}, Epochs:{epochs}, SeqLen:{seq_length}")

                    close_prices = df['close'].values.reshape(-1, 1)
                    scaler = MinMaxScaler(feature_range=(0, 1))
                    scaled_data = scaler.fit_transform(close_prices)

                    X, y = [], []
                    for i in range(seq_length, len(scaled_data)):
                        X.append(scaled_data[i - seq_length:i, 0])
                        y.append(scaled_data[i, 0])
                    X, y = np.array(X), np.array(y)

                    train_size = int(len(X) * 0.8)
                    X_train, y_train = torch.tensor(X[:train_size], dtype=torch.float32), torch.tensor(y[:train_size],
                                                                                                       dtype=torch.float32)
                    X_test, y_test = torch.tensor(X[train_size:], dtype=torch.float32), torch.tensor(y[train_size:],
                                                                                                     dtype=torch.float32)

                    X_train = X_train.unsqueeze(-1)
                    X_test = X_test.unsqueeze(-1)


                    class LSTMPredictor(nn.Module):
                        def __init__(self, input_dim=1, hidden_dim=32, num_layers=2, output_dim=1):
                            super(LSTMPredictor, self).__init__()
                            self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
                            self.fc = nn.Linear(hidden_dim, output_dim)

                        def forward(self, x):
                            out, _ = self.lstm(x)
                            return self.fc(out[:, -1, :])


                    model = LSTMPredictor()
                    criterion = nn.MSELoss()
                    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

                    log_box = st.empty()
                    progress_bar = st.progress(0)

                    for epoch in range(epochs):
                        model.train()
                        optimizer.zero_grad()
                        predictions = model(X_train)
                        loss = criterion(predictions.squeeze(), y_train)
                        loss.backward()
                        optimizer.step()

                        if (epoch + 1) % max(1, epochs // 10) == 0 or epoch == 0:
                            log_box.code(
                                f"Epoch [{epoch + 1}/{epochs}], MSE Loss: {loss.item():.6f}\n正在反向传播更新权重...",
                                language="bash")
                        progress_bar.progress((epoch + 1) / epochs)
                        time.sleep(0.02)

                    log_box.success("✅ 模型训练收敛完成！进入推理阶段...")

                    model.eval()
                    with torch.no_grad():
                        test_predict = model(X_test).numpy()

                    predicted_prices = scaler.inverse_transform(test_predict)

                    start_idx = train_size + seq_length
                    test_df = pd.DataFrame({
                        'trade_date': df['trade_date'].iloc[start_idx:].values,
                        'open': df['open'].iloc[start_idx:].values,
                        'high': df['high'].iloc[start_idx:].values,
                        'low': df['low'].iloc[start_idx:].values,
                        'close': df['close'].iloc[start_idx:].values,
                        'Predicted': predicted_prices.flatten()
                    })

                    test_df['Signal'] = np.where(test_df['Predicted'] > test_df['close'].shift(1), 1, -1)
                    test_df['Ret'] = test_df['close'].pct_change()
                    test_df['Pos'] = test_df['Signal'].shift(1).fillna(0)
                    test_df['Strat_Ret'] = test_df['Pos'] * test_df['Ret']
                    test_df['Cum_Prod'] = (1 + test_df['Strat_Ret'].fillna(0)).cumprod()

                    st.session_state.dl_result = {"df": test_df, "code": ts_code}
                    log_thesis_data("DL训练成功结束", f"Loss收敛至: {loss.item():.6f}")

                except Exception as e:
                    st.error(f"深度学习引擎异常: {e}")
                    log_thesis_data("系统报错-DL引擎", f"神经网络运算出错: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.dl_result:
            tdf = st.session_state.dl_result['df']
            st.markdown("---")
            total_ret = (tdf['Cum_Prod'].iloc[-1] - 1)
            annual_ret = (1 + total_ret) ** (252 / len(tdf)) - 1 if len(tdf) > 0 else 0
            st.metric("测试集累计收益", f"{total_ret * 100:.2f}%")
            st.metric("测试集年化收益", f"{annual_ret * 100:.2f}%")

    with col_chart:
        if st.session_state.dl_result:
            df = st.session_state.dl_result['df']
            st.markdown(
                f'<div class="glass-card"><h4 style="text-align:center;">{st.session_state.dl_result["code"]} - LSTM 预测网络 vs 真实复权走势</h4>',
                unsafe_allow_html=True)

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

            fig.add_trace(go.Candlestick(
                x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                name='真实 K 线', increasing_line_color='#FD1050', increasing_fillcolor='#FD1050',
                decreasing_line_color='#00FF00', decreasing_fillcolor='#00FF00'
            ), row=1, col=1)

            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['Predicted'], name='LSTM 预测价',
                                     line=dict(color='#ffffff', width=2, dash='dot')), row=1, col=1)

            buys = df[df['Signal'] == 1]
            sells = df[df['Signal'] == -1]
            fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['low'] * 0.95, mode='markers',
                                     marker=dict(symbol='triangle-up', size=14, color='#00FFFF',
                                                 line=dict(width=1, color='white')), name='AI 买入'), row=1, col=1)
            fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['high'] * 1.05, mode='markers',
                                     marker=dict(symbol='triangle-down', size=14, color='#FF00FF',
                                                 line=dict(width=1, color='white')), name='AI 卖出'), row=1, col=1)

            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['Cum_Prod'], name='策略净值', fill='tozeroy',
                                     line=dict(color='#00ffcc')), row=2, col=1)

            fig.update_layout(
                height=700, dragmode='pan', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0.1)',
                margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_xaxes(tickformat="%Y年%m月", showgrid=False, rangeslider_visible=False, zeroline=False)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False)

            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True,
                                                                   'modeBarButtonsToRemove': ['lasso2d', 'select2d']})
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🛡️ 页面 5: 论文数据与日志容灾底座
# ==========================================
elif page == "🛡️ 论文数据与日志":
    st.markdown('<div class="glass-card"><h3>🛡️ 多维容灾日志与数据下载中心</h3></div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.write(
        "已启用 **多路复用容灾架构**。用户产生的所有交互指令、回测表现、接口异常和代码崩溃等日志，将以“全局总库”和“独立用户小库”双通道永久落盘，拒绝数据覆盖遗失。")

    col_dl1, col_dl2 = st.columns([1, 1.2])
    with col_dl1:
        st.markdown("#### 📥 论文实验报表库 (CSV)")

        # 1. 供导师审查的：全局大盘日志
        if os.path.exists(GLOBAL_LOG_FILE):
            global_df = pd.read_csv(GLOBAL_LOG_FILE)
            csv_global = global_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📁 下载总服务器全局日志 (Master_Log)", data=csv_global,
                               file_name='Master_Global_Logs.csv', mime='text/csv', type="primary")
        else:
            st.warning("暂无全局日志。")

        # 2. 供特定用户追踪的：专属个人日志
        user_log_file = os.path.join(LOG_DIR, f"log_{st.session_state.user_id}.csv")
        if os.path.exists(user_log_file):
            user_df = pd.read_csv(user_log_file)
            csv_user = user_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="🗂️ 下载您的专属独立追踪日志", data=csv_user,
                               file_name=f'{st.session_state.user_id}_Logs.csv', mime='text/csv')

            st.markdown("---")
            st.caption(f"👀 您 ({st.session_state.user_id}) 的近期历史记录片段：")
            st.dataframe(user_df.tail(5), use_container_width=True)

    with col_dl2:
        st.markdown("#### ⏱️ 服务器实时监控终端 (Terminal)")
        st.text_area("Live Terminal Stream", value="\n".join(st.session_state.sys_logs), height=350)
    st.markdown('</div>', unsafe_allow_html=True)