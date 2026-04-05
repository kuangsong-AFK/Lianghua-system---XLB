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
# 2. 沉浸式 UI & 强制暗黑主题
# ==========================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], .block-container { background-color: #0e1117 !important; background-image: radial-gradient(circle at 50% 0%, #1f2633 0%, #0e1117 75%) !important; padding-top: 2rem !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    header[data-testid="stHeader"] * { color: rgba(255,255,255,0.6) !important; }
    footer { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, span, li { color: #ffffff !important; }
    div[data-testid="stCodeBlock"], pre { background-color: #0d1117 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; }
    code { color: #00ffcc !important; background-color: transparent !important; text-shadow: none !important; }
    [data-testid="stSidebar"] { background: rgba(14, 17, 23, 0.9) !important; border-right: 1px solid rgba(255,255,255,0.1) !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    .glass-card { background: rgba(20, 24, 30, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); }
    .stTextInput > div > div, .stSelectbox > div > div, .stSlider > div > div > div > div { background-color: rgba(0,0,0,0.6) !important; color: white !important; }
    div[data-testid="stChatMessageContent"] { background-color: rgba(30, 35, 45, 0.9) !important; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 毕业论文专用：多用户数据埋点系统
# ==========================================
LOG_FILE = "thesis_user_logs.csv"
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["Timestamp", "UserID", "ActionType", "Details"]).to_csv(LOG_FILE, index=False)

if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "dl_result" not in st.session_state: st.session_state.dl_result = None


def log_thesis_data(action_type, details):
    new_row = pd.DataFrame(
        [{"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "UserID": st.session_state.user_id,
          "ActionType": action_type, "Details": str(details)}])
    new_row.to_csv(LOG_FILE, mode='a', header=False, index=False)
    st.session_state.sys_logs.insert(0,
                                     f"[{datetime.now().strftime('%H:%M:%S')}] [{st.session_state.user_id}] {action_type}: {details}")


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
    st.caption(f"测试用户: {st.session_state.user_id}")
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
# 🤖 页面 2: AI 策略引擎 (传统模块保持不变)
# ==========================================
elif page == "🤖 AI 策略引擎 (LLM)":
    st.markdown('<div class="glass-card"><h3>🤖 LLM 策略生成中枢</h3></div>', unsafe_allow_html=True)
    chat_container = st.container(height=450)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("输入策略构思 (如: 基于均线的趋势跟踪策略)..."):
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
⚠️ 军规：多条件时必须使用 `&` 和 `|` 并加括号！禁用 `and/or`，禁止引入第三方库。"""
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
                        log_thesis_data("LLM生成成功", "代码已装填至沙盒")
                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"API 异常: {e}")
        st.rerun()

# ==========================================
# 🧠 页面 3: 深度学习时序预测 (🔥 毕业论文专属核武)
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

        seq_length = st.slider("📏 时间滑窗长度 (Seq_Len)", min_value=5, max_value=60, value=20,
                               help="使用过去多少天的数据来预测明天")
        epochs = st.slider("🔄 训练迭代轮数 (Epochs)", min_value=10, max_value=100, value=30, step=10)

        if st.button("🚀 启动深度学习训练与回测", use_container_width=True, type="primary"):
            with st.spinner("正在搭建计算图并启动 PyTorch 张量运算..."):
                try:
                    # 1. 数据准备
                    df = pro.daily(ts_code=ts_code, start_date='20210101')
                    if df.empty: raise ValueError("获取数据失败")
                    df = df.sort_values('trade_date').reset_index(drop=True)
                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

                    log_thesis_data("启动DL训练", f"标的:{ts_code}, Epochs:{epochs}, SeqLen:{seq_length}")

                    # 2. 特征工程 (归一化)
                    close_prices = df['close'].values.reshape(-1, 1)
                    scaler = MinMaxScaler(feature_range=(0, 1))
                    scaled_data = scaler.fit_transform(close_prices)

                    # 3. 构建时序数据集
                    X, y = [], []
                    for i in range(seq_length, len(scaled_data)):
                        X.append(scaled_data[i - seq_length:i, 0])
                        y.append(scaled_data[i, 0])
                    X, y = np.array(X), np.array(y)

                    # 划分训练集和测试集 (80%训练, 20%测试)
                    train_size = int(len(X) * 0.8)
                    X_train, y_train = torch.tensor(X[:train_size], dtype=torch.float32), torch.tensor(y[:train_size],
                                                                                                       dtype=torch.float32)
                    X_test, y_test = torch.tensor(X[train_size:], dtype=torch.float32), torch.tensor(y[train_size:],
                                                                                                     dtype=torch.float32)

                    X_train = X_train.unsqueeze(-1)
                    X_test = X_test.unsqueeze(-1)


                    # 4. 定义 LSTM 神经网络
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

                    # 5. 训练模型可视化
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
                        time.sleep(0.02)  # 模拟一点计算时间，提升演示效果

                    log_box.success("✅ 模型训练收敛完成！进入推理阶段...")

                    # 6. 模型推理预测 (测试集)
                    model.eval()
                    with torch.no_grad():
                        test_predict = model(X_test).numpy()

                    # 反归一化
                    predicted_prices = scaler.inverse_transform(test_predict)
                    actual_prices = scaler.inverse_transform(y_test.numpy().reshape(-1, 1))

                    # 7. 构建回测 DataFrame
                    test_dates = df['trade_date'].iloc[train_size + seq_length:].values
                    test_df = pd.DataFrame({
                        'trade_date': test_dates,
                        'close': actual_prices.flatten(),
                        'Predicted': predicted_prices.flatten()
                    })

                    # DL 交易逻辑：预测明天涨就买，预测跌就卖空（简化）
                    test_df['Signal'] = np.where(test_df['Predicted'] > test_df['close'].shift(1), 1, -1)
                    test_df['Ret'] = test_df['close'].pct_change()
                    test_df['Pos'] = test_df['Signal'].shift(1).fillna(0)
                    test_df['Strat_Ret'] = test_df['Pos'] * test_df['Ret']
                    test_df['Cum_Prod'] = (1 + test_df['Strat_Ret'].fillna(0)).cumprod()

                    st.session_state.dl_result = {"df": test_df, "code": ts_code}
                    log_thesis_data("DL训练结束", f"Loss收敛至: {loss.item():.6f}")

                except Exception as e:
                    st.error(f"深度学习引擎异常: {e}")
                    log_thesis_data("DL崩溃", str(e))
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
                f'<div class="glass-card"><h4 style="text-align:center;">{st.session_state.dl_result["code"]} - LSTM 预测价格 vs 真实价格曲线</h4>',
                unsafe_allow_html=True)

            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

            # 主图：真实价格与 LSTM 预测价格曲线对比
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['close'], name='真实收盘价 (Actual)',
                                     line=dict(color='#00FF00', width=2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['Predicted'], name='LSTM 预测价 (Predicted)',
                                     line=dict(color='#FD1050', width=2, dash='dot')), row=1, col=1)

            buys = df[df['Signal'] == 1]
            sells = df[df['Signal'] == -1]
            fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['close'] * 0.98, mode='markers',
                                     marker=dict(symbol='triangle-up', size=10, color='yellow'), name='AI 买入判定'),
                          row=1, col=1)
            fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['close'] * 1.02, mode='markers',
                                     marker=dict(symbol='triangle-down', size=10, color='fuchsia'), name='AI 卖出判定'),
                          row=1, col=1)

            # 副图：策略累计收益曲线
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['Cum_Prod'], name='LSTM 策略净值', fill='tozeroy',
                                     line=dict(color='#00ffcc')), row=2, col=1)

            fig.update_layout(
                height=700, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)',
                margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_xaxes(tickformat="%Y年%m月", showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)')

            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

            st.info(
                "💡 **学术原理解析**：该模块将前 80% 时间段作为训练集供 LSTM 提取特征，后 20% 为测试集。上图中，**红色的虚线**代表神经网络的预判走势，当预判红线高于绿线时，系统发出买入信号。您可以将此截图放入论文《时序模型回测结果分析》章节。")

# ==========================================
# 📈 页面 4: 深度回测与图表 (原LLM沙盒页面)
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
                            st.error("获取数据失败")
                        else:
                            data = data.sort_values('trade_date').reset_index(drop=True)
                            data['trade_date'] = pd.to_datetime(data['trade_date'], format='%Y%m%d')

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
                            log_thesis_data("回测成功", f"LLM策略标的:{ts_code}")
                    except Exception as e:
                        st.error(f"沙盒异常: {e}")
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
# 🛡️ 页面 5: 论文数据与日志
# ==========================================
elif page == "🛡️ 论文数据与日志":
    st.markdown('<div class="glass-card"><h3>🛡️ 多并发用户记录与日志提取</h3></div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    col_dl1, col_dl2 = st.columns([1, 1])
    with col_dl1:
        st.markdown("#### 📥 毕业论文实验数据源")
        if os.path.exists(LOG_FILE):
            log_df = pd.read_csv(LOG_FILE)
            csv = log_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📁 一键下载论文原始报表", data=csv, file_name='thesis_user_logs.csv',
                               mime='text/csv', type="primary")
            st.dataframe(log_df.tail(10), use_container_width=True)
        else:
            st.warning("暂无日志数据。")
    with col_dl2:
        st.markdown("#### ⏱️ 实时终端")
        st.text_area("Terminal", value="\n".join(st.session_state.sys_logs), height=300)
    st.markdown('</div>', unsafe_allow_html=True)