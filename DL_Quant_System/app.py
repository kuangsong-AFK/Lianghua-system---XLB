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
# 2. 沉浸式 UI (深海流体)
# ==========================================
st.markdown("""
<style>
    @keyframes fluidGradient { 0% { background-position: 0% 50%; } 25% { background-position: 50% 100%; } 50% { background-position: 100% 50%; } 75% { background-position: 50% 0%; } 100% { background-position: 0% 50%; } }
    .stApp { background-image: linear-gradient(132deg, #02040a, #111d3d, #030614, #1d2b4f, #081224) !important; background-size: 400% 400% !important; animation: fluidGradient 12s ease-in-out infinite !important; }
    [data-testid="stAppViewContainer"], .block-container { background: transparent !important; padding-top: 2rem !important; }
    header[data-testid="stHeader"] { background: transparent !important; }
    footer { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, span, li { color: #e2e8f0 !important; }

    /* 侧边栏按钮 */
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] {
        display: flex !important; background-color: rgba(0, 255, 204, 0.15) !important; 
        border: 1px solid rgba(0, 255, 204, 0.6) !important; border-radius: 8px !important;
        box-shadow: 0 0 12px rgba(0, 255, 204, 0.3) !important; margin-top: 15px !important; margin-left: 10px !important;
        transition: all 0.3s ease; z-index: 999999 !important;
    }
    [data-testid="collapsedControl"] { position: fixed !important; top: 15px !important; left: 15px !important; }

    [data-testid="stSidebar"] { background: rgba(5, 8, 14, 0.6) !important; backdrop-filter: blur(20px) !important; border-right: 1px solid rgba(255,255,255,0.05) !important; }
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div[role="radiogroup"] > label {
        background: rgba(15, 20, 30, 0.4) !important; padding: 14px 20px !important; margin-bottom: 8px !important;
        border-radius: 12px !important; border-left: 4px solid transparent !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important; cursor: pointer !important; width: 100% !important;
    }
    div[role="radiogroup"] > label:has(input:checked) {
        transform: translateX(8px) !important; background: linear-gradient(90deg, rgba(0, 255, 204, 0.2), rgba(10, 15, 25, 0.8)) !important;
        border-left: 4px solid #00ffcc !important; box-shadow: 0 4px 15px rgba(0, 255, 204, 0.1) !important;
    }

    .glass-card { background: rgba(15, 20, 30, 0.5); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); }
    .stTextInput > div > div, .stSelectbox > div > div, .stSlider > div > div > div > div { background-color: rgba(0,0,0,0.5) !important; color: white !important; border: 1px solid rgba(255,255,255,0.1) !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 毕业论文专用：多维度日志系统
# ==========================================
LOG_DIR = "user_logs"
os.makedirs(LOG_DIR, exist_ok=True)
GLOBAL_LOG_FILE = os.path.join(LOG_DIR, "global_master_log.csv")
if not os.path.exists(GLOBAL_LOG_FILE): pd.DataFrame(columns=["Timestamp", "UserID", "ActionType", "Details"]).to_csv(
    GLOBAL_LOG_FILE, index=False)

if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "is_live_trading" not in st.session_state: st.session_state.is_live_trading = False


def log_thesis_data(action_type, details):
    icon = "🔴" if "报错" in action_type or "异常" in action_type else "🟢"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"{icon} [{timestamp}] [{st.session_state.user_id}] {action_type}: {details}"
    st.session_state.sys_logs.insert(0, log_msg)
    new_row = pd.DataFrame([{"Timestamp": timestamp, "UserID": st.session_state.user_id, "ActionType": action_type,
                             "Details": str(details)}])
    new_row.to_csv(GLOBAL_LOG_FILE, mode='a', header=False, index=False)


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
    st.caption(f"连线终端: {st.session_state.user_id}")
    st.markdown("---")
    page = st.radio("系统导航", [
        "🏠 系统总览 (监控大盘)",
        "🤖 AI 策略引擎 (LLM)",
        "📈 深度静态回测",
        "⚡ 实时高频交易 (Live)",
        "🧠 深度学习预测 (LSTM)",
        "🛡️ 论文数据与日志"
    ], label_visibility="collapsed")

# ==========================================
# 🏠 页面 1: 系统总览 (中期检查大盘)
# ==========================================
if page == "🏠 系统总览 (监控大盘)":
    st.markdown(
        '<div class="glass-card"><h2>🎓 基于大模型与深度学习的双引擎量化决策系统</h2><p style="color:#00ffcc;">中期检查演示大盘 (Mid-term Inspection Dashboard)</p></div>',
        unsafe_allow_html=True)
    try:
        start_t = time.time()
        pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240101')
        tushare_status = f"🟢 连通正常 ({int((time.time() - start_t) * 1000)} ms)"
    except:
        tushare_status = "🔴 连接阻断"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("活跃并发节点", st.session_state.user_id)
    c2.metric("金融数据中枢", tushare_status)
    c3.metric("LLM 策略大脑", "Moonshot-v1")
    c4.metric("算力引擎", f"PyTorch {torch.__version__}")

    st.markdown("---")
    cl, cr = st.columns([1.5, 1])
    with cl:
        st.markdown('<div class="glass-card"><h4>⚙️ 系统架构图解析</h4>'
                    '<ul><li><b>🧠 认知层</b>: 通过自然语言生成并即时覆盖最新策略代码。</li>'
                    '<li><b>📊 数据层</b>: Tushare 商业接口驱动，支持动态复权修正。</li>'
                    '<li><b>🔮 深度学习</b>: PyTorch 实现 LSTM 时间滑窗预测。</li>'
                    '<li><b>⚡ 高频推演</b>: Tick Stream Simulator 模拟实时买卖信号捕获。</li></ul></div>',
                    unsafe_allow_html=True)
    with cr:
        st.markdown('<div class="glass-card"><h4>📋 研发进度节点</h4>'
                    '- [x] LLM 策略沙盒 (带最新策略自动覆盖逻辑)<br>'
                    '- [x] Tushare 接口全线贯通与测速<br>'
                    '- [x] LSTM 训练可视化与价格预测曲线<br>'
                    '- [x] 动态流体暗黑 UI 与 APP 级交互<br>'
                    '- [x] **领域知识过滤与拒绝闲聊机制**</div>', unsafe_allow_html=True)

# ==========================================
# 🤖 页面 2: AI 策略引擎 (🔥 注入军法规范)
# ==========================================
elif page == "🤖 AI 策略引擎 (LLM)":
    if "messages" not in st.session_state: st.session_state.messages = []

    st.markdown(
        '<div class="glass-card"><h3>🤖 LLM 策略生成中枢</h3><p style="color:#888;">最新的策略将自动装填并覆盖旧策略。</p></div>',
        unsafe_allow_html=True)
    chat_container = st.container(height=450)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("输入策略构思 (或询问金融量化知识)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_thesis_data("对话请求", prompt)

        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                bt = "`" * 3
                # 🔥 终极 System Prompt：拒绝闲聊 + 强制规范
                sys_prompt = f"""你是一名严谨的量化交易专家。
1. **领域限制**：你只回答与金融、股票、量化交易、Python编程、数学模型相关的问题。
2. **拒绝闲聊**：如果用户的问题与上述无关（如闲聊、生活百科、娱乐等），请礼貌回复：“主公，末将目前正全身心守卫量化疆土，不议战场之外的琐事，请下达交易指令。”
3. **策略规范**：当生成策略时，必须包含 `def generate_signals(df):` 函数。在 df 中新增 'Signal' 列。
4. **覆盖逻辑**：每次生成的代码必须是完整可运行的独立版本。
列名必须使用：'Open', 'High', 'Low', 'Close', 'Volume'。"""

                try:
                    stream = client.chat.completions.create(model="moonshot-v1-8k", messages=[{"role": "system",
                                                                                               "content": sys_prompt}] + st.session_state.messages,
                                                            stream=True)
                    full_resp = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_resp += chunk.choices[0].delta.content
                            msg_box.markdown(full_resp + "▌")
                    msg_box.markdown(full_resp)

                    # 🔥 提取代码并实时覆盖 Session State
                    code_match = re.search(bt + r"(?:python)?\s*(.*?)" + bt, full_resp, re.DOTALL | re.IGNORECASE)
                    if code_match:
                        st.session_state.generated_code = code_match.group(1).strip()
                        st.toast("✅ 策略已装填，最新军令已下达！", icon="🚀")
                        log_thesis_data("策略覆盖", "最新代码已装载")

                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"API 异常: {e}")
        st.rerun()

# ==========================================
# 📈 页面 3: 深度静态回测 (🔥 执行最新策略)
# ==========================================
elif page == "📈 深度静态回测":
    st.markdown('<div class="glass-card"><h3>📈 静态全量沙盒与归因分析</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        raw_code = st.text_input("🎯 回测标的", value="000001")
        ts_code = format_ts_code(raw_code)
        adj_mode = st.selectbox("⚖️ 价格复权处理", ["qfq", "hfq", "None"])
        y_axis = st.radio("📏 Y轴模式", ["自适应", "绝对"])

        if st.session_state.generated_code:
            if st.button("🚀 启动回测", use_container_width=True, type="primary"):
                with st.spinner("正在加载最新军令执行任务..."):
                    try:
                        data = ts.pro_bar(ts_code=ts_code, adj=adj_mode if adj_mode != "None" else None,
                                          start_date='20230101')
                        data = data.sort_values('trade_date').reset_index(drop=True)
                        data['trade_date'] = pd.to_datetime(data['trade_date'], format='%Y%m%d')
                        data['Open'], data['High'], data['Low'], data['Close'], data['Volume'] = data['open'], data[
                            'high'], data['low'], data['close'], data['vol']

                        l_vars = {}
                        exec(st.session_state.generated_code, globals(), l_vars)
                        if 'generate_signals' not in l_vars: raise ValueError("AI 缺失 generate_signals 函数")
                        data = l_vars['generate_signals'](data)

                        data['Ret'] = data['close'].pct_change()
                        data['Pos'] = data['Signal'].replace(0, np.nan).ffill().fillna(0)
                        data['Strat_Ret'] = data['Pos'].shift(1) * data['Ret']
                        data['Cum_Prod'] = (1 + data['Strat_Ret'].fillna(0)).cumprod()
                        st.session_state.bt_result = {"df": data, "code": ts_code, "y_mode": y_axis}
                    except Exception as e:
                        st.error(f"沙盒异常: {e}")
        else:
            st.warning("🟡 请先去 AI 战情室生成策略！")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            df = st.session_state.bt_result['df']
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05)
            fig.add_trace(
                go.Candlestick(x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                               name='K线'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['Cum_Prod'], name='净值', fill='tozeroy'), row=2, col=1)
            fig.update_layout(height=600, dragmode='pan', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0.2)', margin=dict(l=0, r=0, t=0, b=0),
                              xaxis_rangeslider_visible=False)
            if "自适应" in st.session_state.bt_result["y_mode"]: fig.update_yaxes(autorange=True, row=1, col=1)
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ⚡ 页面 4: 实时高频交易 (Live)
# ==========================================
elif page == "⚡ 实时高频交易 (Live)":
    st.markdown('<div class="glass-card"><h3>⚡ 实时高频推演系统 (Tick Stream)</h3></div>', unsafe_allow_html=True)
    c_ctrl, c_chart = st.columns([1, 2.5])
    with c_ctrl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        live_code = st.text_input("🎯 监控标的", value="000001")
        freq = st.slider("⏱️ 刷新间隔 (秒)", 0.1, 2.0, 0.5)
        if st.session_state.generated_code:
            if st.button("▶️ 开启自动交易", type="primary",
                         use_container_width=True): st.session_state.is_live_trading = True
            if st.button("⏹️ 终止撤退", use_container_width=True): st.session_state.is_live_trading = False
        else:
            st.warning("🟡 无有效策略。")
        st.markdown('</div>', unsafe_allow_html=True)
    with c_chart:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        met_ph = st.empty()
        cht_ph = st.empty()
        if st.session_state.is_live_trading:
            full_df = ts.pro_bar(ts_code=format_ts_code(live_code), adj='qfq', start_date='20230101').sort_values(
                'trade_date').reset_index(drop=True)
            full_df['trade_date'] = pd.to_datetime(full_df['trade_date'], format='%Y%m%d')
            stream = full_df.tail(100).reset_index(drop=True)
            for i in range(20, len(stream)):
                if not st.session_state.is_live_trading: break
                sub = stream.iloc[:i].copy()
                sub['Open'], sub['High'], sub['Low'], sub['Close'], sub['Volume'] = sub['open'], sub['high'], sub[
                    'low'], sub['close'], sub['vol']
                l_vars = {}
                exec(st.session_state.generated_code, globals(), l_vars)
                sub = l_vars['generate_signals'](sub)

                # 简单计算收益
                sub['Ret'] = sub['close'].pct_change()
                sub['Cum'] = (1 + (sub['Signal'].shift(1).fillna(0) * sub['Ret'].fillna(0))).cumprod()

                with met_ph.container():
                    cols = st.columns(3)
                    cols[0].metric("最新价", f"{sub['close'].iloc[-1]}")
                    cols[1].metric("实时信号",
                                   "🟢买入" if sub['Signal'].iloc[-1] == 1 else "🔴卖出" if sub['Signal'].iloc[
                                                                                              -1] == -1 else "⚪观望")
                    cols[2].metric("动态净值", f"{sub['Cum'].iloc[-1]:.4f}")

                fig = go.Figure(data=[
                    go.Candlestick(x=sub['trade_date'], open=sub['open'], high=sub['high'], low=sub['low'],
                                   close=sub['close'])])
                fig.update_layout(height=400, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                                  margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False, dragmode='pan')
                cht_ph.plotly_chart(fig, use_container_width=True, key=f"live_{i}", config={'scrollZoom': True})
                time.sleep(freq)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🧠 页面 5: 深度学习预测 (LSTM)
# ==========================================
elif page == "🧠 深度学习预测 (LSTM)":
    st.markdown('<div class="glass-card"><h3>🧠 深度时序预测中心 (PyTorch)</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st_code = st.text_input("🎯 训练标的", value="000001")
        ts_c = format_ts_code(st_code)
        slen = st.slider("📏 滑窗长度", 5, 60, 20)
        eps = st.slider("🔄 迭代轮数", 10, 50, 20)
        if st.button("🚀 启动 DL 训练", use_container_width=True, type="primary"):
            with st.spinner("PyTorch 张量运算中..."):
                try:
                    df = ts.pro_bar(ts_code=ts_c, adj='qfq', start_date='20210101').sort_values(
                        'trade_date').reset_index(drop=True)
                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                    scaler = MinMaxScaler()
                    scaled = scaler.fit_transform(df['close'].values.reshape(-1, 1))
                    X, y = [], []
                    for i in range(slen, len(scaled)):
                        X.append(scaled[i - slen:i, 0])
                        y.append(scaled[i, 0])
                    X_t, y_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1), torch.tensor(np.array(y),
                                                                                                          dtype=torch.float32)


                    class LSTM(nn.Module):
                        def __init__(self): super().__init__(); self.lstm = nn.LSTM(1, 32, 2,
                                                                                    batch_first=True); self.fc = nn.Linear(
                            32, 1)

                        def forward(self, x): out, _ = self.lstm(x); return self.fc(out[:, -1, :])


                    model = LSTM();
                    opt = torch.optim.Adam(model.parameters(), lr=0.01);
                    crit = nn.MSELoss()
                    lbox = st.empty()
                    for e in range(eps):
                        model.train();
                        opt.zero_grad();
                        pred = model(X_t);
                        loss = crit(pred.squeeze(), y_t);
                        loss.backward();
                        opt.step()
                        lbox.code(f"Epoch {e + 1}/{eps}, Loss: {loss.item():.6f}")

                    model.eval();
                    test_p = model(X_t[-100:]).detach().numpy()
                    inv_p = scaler.inverse_transform(test_p)
                    st.session_state.dl_result = {"dates": df['trade_date'].iloc[-100:],
                                                  "actual": df['close'].iloc[-100:], "pred": inv_p.flatten()}
                except Exception as e:
                    st.error(f"DL 异常: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_r:
        if st.session_state.dl_result:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            res = st.session_state.dl_result
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['actual'], name='真实价', line=dict(color='#00ffcc')))
            fig.add_trace(
                go.Scatter(x=res['dates'], y=res['pred'], name='LSTM 预测', line=dict(color='#ff00ff', dash='dot')))
            fig.update_layout(height=500, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', dragmode='pan')
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🛡️ 页面 6: 论文数据与日志
# ==========================================
elif page == "🛡️ 论文数据与日志":
    st.markdown('<div class="glass-card"><h3>🛡️ 多维容灾日志底座</h3></div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.markdown("#### 📥 数据导出")
        if os.path.exists(GLOBAL_LOG_FILE): st.download_button("📁 下载全局日志",
                                                               data=pd.read_csv(GLOBAL_LOG_FILE).to_csv(
                                                                   index=False).encode('utf-8'),
                                                               file_name='Master_Log.csv')
    with c2:
        st.markdown("#### ⏱️ 实时监控")
        st.text_area("Stream", value="\n".join(st.session_state.sys_logs), height=350)