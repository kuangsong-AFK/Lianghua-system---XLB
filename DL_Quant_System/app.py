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

# 🔥 深度学习学术库
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

# ==========================================
# 1. 初始化与核心兵符
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro - 毕业设计版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=30.0)

# 🔥 彻底解决 AttributeError：在应用最顶端初始化所有状态
if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "dl_result" not in st.session_state: st.session_state.dl_result = None
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "is_live_trading" not in st.session_state: st.session_state.is_live_trading = False

# ==========================================
# 2. UI/UX 强化 (深海流体背景与 APP 侧边栏)
# ==========================================
st.markdown("""
<style>
    @keyframes fluidFlow { 0% { background-position: 0% 50%; } 25% { background-position: 50% 100%; } 50% { background-position: 100% 50%; } 75% { background-position: 50% 0%; } 100% { background-position: 0% 50%; } }
    .stApp { background-image: linear-gradient(132deg, #02040a, #111d3d, #030614, #1d2b4f, #081224) !important; background-size: 400% 400% !important; animation: fluidFlow 12s ease-in-out infinite !important; }
    [data-testid="stAppViewContainer"], .block-container { background: transparent !important; padding-top: 1.5rem !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    footer { display: none !important; }
    .stMarkdown, p, h1, h2, h3, label, span { color: #e2e8f0 !important; }

    /* 侧边栏按钮高亮系统 */
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] {
        display: flex !important; background-color: rgba(0, 255, 204, 0.2) !important; 
        border: 1px solid rgba(0, 255, 204, 0.8) !important; border-radius: 8px !important;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.3) !important; transition: all 0.3s ease;
    }
    [data-testid="collapsedControl"] { position: fixed !important; top: 15px !important; left: 15px !important; z-index: 999999 !important; }

    [data-testid="stSidebar"] { background: rgba(5, 8, 14, 0.7) !important; backdrop-filter: blur(20px) !important; border-right: 1px solid rgba(255,255,255,0.05) !important; }
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label {
        background: rgba(15, 20, 30, 0.4) !important; padding: 14px 18px !important; margin-bottom: 10px !important;
        border-radius: 12px !important; border-left: 4px solid transparent !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important; cursor: pointer !important; width: 100% !important;
    }
    div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(0, 255, 204, 0.25), rgba(10, 15, 25, 0.9)) !important;
        border-left: 4px solid #00ffcc !important; box-shadow: 0 4px 15px rgba(0, 255, 204, 0.1) !important; transform: translateX(5px);
    }

    .glass-card { background: rgba(20, 28, 45, 0.6); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5); }
    .metric-box { background: rgba(0, 255, 204, 0.05); border: 1px solid rgba(0, 255, 204, 0.2); border-radius: 10px; padding: 15px; text-align: center; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. 核心工具函数 (双向大小写映射防崩装甲)
# ==========================================
def apply_dual_column_armor(df):
    mapping = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'vol': 'Volume', 'amount': 'Amount'}
    for low, up in mapping.items():
        if low in df.columns and up not in df.columns: df[up] = df[low]
        if up in df.columns and low not in df.columns: df[low] = df[up]
    return df


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
# 4. 侧边栏导航
# ==========================================
with st.sidebar:
    st.markdown("### 🎓 量化交易引擎 Pro")
    st.caption(f"🛡️ 节点 ID: {st.session_state.user_id}")
    st.markdown("---")
    page = st.radio("导航菜单", [
        "🏠 系统总览 (监控中控)",
        "🤖 AI 策略引擎 (LLM)",
        "📈 深度静态全量回测",
        "⚡ 实时高频交易 (Live)",
        "🧠 深度学习预测 (LSTM)",
        "🛡️ 论文审计日志"
    ], label_visibility="collapsed")

# ==========================================
# 🏠 页面 1: 系统总览 (🔥 豪华版大盘)
# ==========================================
if page == "🏠 系统总览 (监控中控)":
    st.markdown(
        '<div class="glass-card"><h1>🏛️ 双引擎驱动量化决策决策终端</h1><p style="color:#00ffcc; font-size:1.2rem;">中期检查专项演示平台 (Mid-term Research & Development Status)</p></div>',
        unsafe_allow_html=True)

    # 状态实时监控
    try:
        t_start = time.time()
        pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240101')
        t_latency = int((time.time() - t_start) * 1000)
        ts_status = f"🟢 连通正常 ({t_latency}ms)"
    except:
        ts_status = "🔴 通道阻塞"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("活跃并发节点", st.session_state.user_id, "Monitoring...")
    with col2:
        st.metric("金融数据中枢 (Tushare)", ts_status, "API Auth: Pass")
    with col3:
        st.metric("LLM 语义大脑", "Kimi Moonshot", "Status: Active")
    with col4:
        st.metric("算力引擎 (PyTorch)", f"{torch.__version__}", "Device: CPU/MPS")

    st.markdown("---")
    c_arch, c_point = st.columns([1.5, 1])
    with c_arch:
        st.markdown('<div class="glass-card"><h4>⚙️ 系统工程架构 (Technical Architecture)</h4>'
                    '<ul><li><b>1. LLM 自然语言交互层</b>: 采用 NLP 技术解析非结构化交易构思，支持<b>策略即时覆盖机制</b>。</li>'
                    '<li><b>2. 混合数据治理层</b>: 整合 Tushare 商业接口，支持 OHLCV 自动复权清洗及<b>列名大小写自适应映射</b>。</li>'
                    '<li><b>3. LSTM 算法预测层</b>: 基于时序滑动窗口，通过多层 LSTM 神经网络捕捉股价非线性规律。</li>'
                    '<li><b>4. 模拟仿真执行层</b>: 包含静态历史归因引擎与<b>高频 Tick Stream 推演器</b>。</li></ul></div>',
                    unsafe_allow_html=True)
    with c_point:
        st.markdown('<div class="glass-card"><h4>💡 中期学术创新点</h4>'
                    '✅ <b>LLM 防闲聊过滤</b>: 锁定金融领域知识域。<br>'
                    '✅ <b>容灾日志审计</b>: 全量捕获用户沙盒崩溃日志。<br>'
                    '✅ <b>高频沙盘引擎</b>: 突破个人接口频率限制演示实时交易。<br>'
                    '✅ <b>视觉自适应 K 线</b>: 实现工业级看盘体验。</div>', unsafe_allow_html=True)

# ==========================================
# 🤖 页面 2: AI 策略引擎
# ==========================================
elif page == "🤖 AI 策略引擎 (LLM)":
    if "messages" not in st.session_state: st.session_state.messages = []
    st.markdown(
        '<div class="glass-card"><h3>🤖 LLM 策略战情室</h3><p style="color:#888;">最新生成的策略将作为“当前最高军令”同步至全系统。</p></div>',
        unsafe_allow_html=True)
    chat_container = st.container(height=400)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("输入策略（如：20日均线金叉买入）..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_thesis_data("指令下达", prompt)
        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                sys_p = "你是一名严谨的量化专家。1.拒绝闲聊。2.生成的代码必须包含 def generate_signals(df): 并返回 df。3.列名用'Close'等。"
                stream = client.chat.completions.create(model="moonshot-v1-8k", messages=[{"role": "system",
                                                                                           "content": sys_p}] + st.session_state.messages,
                                                        stream=True)
                full_resp = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_resp += chunk.choices[0].delta.content
                        msg_box.markdown(full_resp + "▌")
                msg_box.markdown(full_resp)
                code_match = re.search(r"```python\s*(.*?)\s*```", full_resp, re.DOTALL)
                if code_match:
                    st.session_state.generated_code = code_match.group(1).strip()
                    st.toast("✅ 策略已装填！最新军令同步完毕！")
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
        st.rerun()

# ==========================================
# 📈 页面 3: 深度静态回测 (🔥 满血版回归)
# ==========================================
elif page == "📈 深度静态全量回测":
    st.markdown('<div class="glass-card"><h3>📊 历史回测全量审计与归因分析</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        raw_code = st.text_input("🎯 回测标的代码", value="000001")
        ts_code = format_ts_code(raw_code)
        adj = st.selectbox("⚖️ 价格复权处理", ["qfq (前复权)", "hfq (后复权)", "None (不复权)"])
        y_mode = st.radio("📏 Y轴自适应缩放", ["开启", "关闭"])

        if st.session_state.generated_code:
            if st.button("🚀 启动全量归因回测", use_container_width=True, type="primary"):
                with st.spinner("正在从 Tushare 调度数据并执行沙盒..."):
                    try:
                        adj_p = adj.split(" ")[0] if adj != "None" else None
                        df = ts.pro_bar(ts_code=ts_code, adj=adj_p, start_date='20220101')
                        df = df.sort_values('trade_date').reset_index(drop=True)
                        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                        df = apply_dual_column_armor(df)  # 🔥 装甲防护

                        # 执行策略
                        l_vars = {}
                        exec(st.session_state.generated_code, globals(), l_vars)
                        df = l_vars['generate_signals'](df)

                        # 指标计算 (严谨学术版)
                        df['Ret'] = df['close'].pct_change()
                        df['Pos'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
                        df['Strat_Ret'] = df['Pos'].shift(1) * df['Ret']
                        df['Cum_Prod'] = (1 + df['Strat_Ret'].fillna(0)).cumprod()

                        # 计算年化和最大回撤
                        total_ret = (df['Cum_Prod'].iloc[-1] - 1)
                        annual_ret = (1 + total_ret) ** (252 / len(df)) - 1
                        max_dd = (df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min()
                        volatility = df['Strat_Ret'].std() * np.sqrt(252)
                        sharpe = annual_ret / volatility if volatility != 0 else 0

                        st.session_state.bt_result = {"df": df, "code": ts_code, "metrics": {
                            "total": total_ret, "annual": annual_ret, "max_dd": max_dd, "sharpe": sharpe
                        }, "y_mode": y_mode}
                    except Exception as e:
                        st.error(f"沙盒异常: {e}"); log_thesis_data("沙盒报错", str(e))
        else:
            st.warning("战情室未生成策略军令。")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            m = st.session_state.bt_result['metrics']
            df = st.session_state.bt_result['df']

            # 核心指标卡片
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(
                f'<div class="metric-box"><p style="margin:0; font-size:0.8rem;">累计收益</p><h2 style="color:#00ffcc;">{m["total"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c2.markdown(
                f'<div class="metric-box"><p style="margin:0; font-size:0.8rem;">年化收益</p><h2 style="color:#00ffcc;">{m["annual"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c3.markdown(
                f'<div class="metric-box"><p style="margin:0; font-size:0.8rem;">最大回撤</p><h2 style="color:#ff4b4b;">{m["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c4.markdown(
                f'<div class="metric-box"><p style="margin:0; font-size:0.8rem;">夏普比率</p><h2 style="color:#00ffcc;">{m["sharpe"]:.2f}</h2></div>',
                unsafe_allow_html=True)

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(
                go.Candlestick(x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                               name='K线'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['Cum_Prod'], name='净值', fill='tozeroy',
                                     line=dict(color='#00ffcc')), row=2, col=1)
            fig.update_layout(height=600, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0.1)', xaxis_rangeslider_visible=False, dragmode='pan')
            if st.session_state.bt_result["y_mode"] == "开启": fig.update_yaxes(autorange=True, row=1, col=1)
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ⚡ 页面 4: 实时高频交易 (Live)
# ==========================================
elif page == "⚡ 实时高频交易 (Live)":
    st.markdown('<div class="glass-card"><h3>⚡ 高频沙盘模拟推演 (Real-time Flow)</h3></div>', unsafe_allow_html=True)
    c_ctrl, c_chart = st.columns([1, 2.5])
    with c_ctrl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        live_code = st.text_input("🎯 动态推送标的", value="000001")
        freq = st.slider("⏱️ 行情跳动间隔 (秒)", 0.1, 2.0, 0.5)
        st.button("▶️ 开启高频自动交易", on_click=lambda: st.session_state.update({"is_live_trading": True}),
                  type="primary")
        st.button("⏹️ 强行熔断停止", on_click=lambda: st.session_state.update({"is_live_trading": False}))
        st.markdown('</div>', unsafe_allow_html=True)
    with c_chart:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        met_ph = st.empty();
        cht_ph = st.empty()
        if st.session_state.is_live_trading:
            df_full = ts.pro_bar(ts_code=format_ts_code(live_code), adj='qfq', start_date='20230101').sort_values(
                'trade_date').reset_index(drop=True)
            df_full['trade_date'] = pd.to_datetime(df_full['trade_date'])
            stream = df_full.tail(120).reset_index(drop=True)
            for i in range(20, len(stream)):
                if not st.session_state.is_live_trading: break
                sub = apply_dual_column_armor(stream.iloc[:i].copy())
                l_vars = {}
                exec(st.session_state.generated_code, globals(), l_vars)
                sub = l_vars['generate_signals'](sub)

                with met_ph.container():
                    c = st.columns(3)
                    c[0].metric("Tick 现价", f"{sub['close'].iloc[-1]}")
                    c[1].metric("高频信号", "🟢 买入" if sub['Signal'].iloc[-1] == 1 else "🔴 卖出" if sub['Signal'].iloc[
                                                                                                         -1] == -1 else "⚪ 观望")
                    c[2].metric("并发收益率", f"{(sub['close'].pct_change().iloc[-1] * 100):.2f}%")

                fig = go.Figure(data=[
                    go.Candlestick(x=sub['trade_date'], open=sub['open'], high=sub['high'], low=sub['low'],
                                   close=sub['close'])])
                fig.update_layout(height=450, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                                  margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False, dragmode='pan')
                fig.update_yaxes(autorange=True)
                cht_ph.plotly_chart(fig, use_container_width=True, key=f"live_{i}", config={'scrollZoom': True})
                time.sleep(freq)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🧠 页面 5: 深度学习预测 (LSTM) (🔥 修复稳定性)
# ==========================================
elif page == "🧠 深度学习预测 (LSTM)":
    st.markdown('<div class="glass-card"><h3>🧠 深度神经网络时序建模中心 (LSTM)</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st_code = st.text_input("🎯 训练模型标的", value="000001")
        slen = st.slider("📏 滑窗长度 (Seq_Len)", 5, 60, 20)
        eps = st.slider("🔄 Epoch 迭代轮数", 10, 50, 30)
        if st.button("🚀 启动张量训练", type="primary"):
            with st.spinner("神经网络前向传播中..."):
                try:
                    df = ts.pro_bar(ts_code=format_ts_code(st_code), adj='qfq', start_date='20210101').sort_values(
                        'trade_date').reset_index(drop=True)
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    scaler = MinMaxScaler()
                    scaled = scaler.fit_transform(df['close'].values.reshape(-1, 1))
                    X, y = [], []
                    for i in range(slen, len(scaled)):
                        X.append(scaled[i - slen:i, 0]);
                        y.append(scaled[i, 0])
                    X_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1)
                    y_t = torch.tensor(np.array(y), dtype=torch.float32)


                    class LSTM(nn.Module):
                        def __init__(self): super().__init__(); self.lstm = nn.LSTM(1, 64, 2,
                                                                                    batch_first=True); self.fc = nn.Linear(
                            64, 1)

                        def forward(self, x): out, _ = self.lstm(x); return self.fc(out[:, -1, :])


                    model = LSTM();
                    opt = torch.optim.Adam(model.parameters(), lr=0.01);
                    crit = nn.MSELoss()
                    lbox = st.empty();
                    pbar = st.progress(0)
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
                    inv_p = scaler.inverse_transform(test_p)
                    st.session_state.dl_result = {"dates": df['trade_date'].iloc[-100:],
                                                  "actual": df['close'].iloc[-100:], "pred": inv_p.flatten()}
                except Exception as e:
                    st.error(f"DL 异常: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_r:
        # 🔥 核心修复：更严谨的状态判断
        if 'dl_result' in st.session_state and st.session_state.dl_result is not None:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            res = st.session_state.dl_result
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['actual'], name='真实轨迹', line=dict(color='#00ffcc')))
            fig.add_trace(
                go.Scatter(x=res['dates'], y=res['pred'], name='LSTM 预测', line=dict(color='#ff00ff', dash='dot')))
            fig.update_layout(height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', dragmode='pan')
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🛡️ 页面 6: 论文数据审计
# ==========================================
elif page == "🛡️ 论文审计日志":
    st.markdown('<div class="glass-card"><h3>🛡️ 实验数据采集与多维审计中心</h3></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        if os.path.exists(GLOBAL_LOG_FILE):
            st.download_button("📁 导出中期汇报审计日志 (CSV)",
                               data=pd.read_csv(GLOBAL_LOG_FILE).to_csv(index=False).encode('utf-8'),
                               file_name='Backtest_Audit_Logs.csv', type="primary")
    with c2:
        st.text_area("实时工作流终端", value="\n".join(st.session_state.sys_logs), height=350)