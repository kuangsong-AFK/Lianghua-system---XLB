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
# 🏠 页面 1: 系统总览
# ==========================================
if page == "🏠 系统总览 (监控大盘)":
    st.markdown(
        '<div class="glass-card"><h2>🎓 基于大模型与深度学习的双引擎量化决策系统</h2><p style="color:#00ffcc;">中期检查演示大盘</p></div>',
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
    st.markdown('<div class="glass-card"><h4>📋 研发进度与规范</h4>'
                '<li><b>最新军令覆盖</b>：AI 生成的所有策略将即时覆盖旧逻辑，确保回测一致性。</li>'
                '<li><b>后台大写对齐</b>：系统后台已全面适配 Close/Open/High/Low 命名标准。</li>'
                '<li><b>防干扰机制</b>：AI 军师已开启严格的领域知识过滤，谢绝一切生活闲聊。</li></div>',
                unsafe_allow_html=True)

# ==========================================
# 🤖 页面 2: AI 策略引擎 (🔥 策略覆盖+拒答闲聊)
# ==========================================
elif page == "🤖 AI 策略引擎 (LLM)":
    if "messages" not in st.session_state: st.session_state.messages = []
    st.markdown(
        '<div class="glass-card"><h3>🤖 LLM 策略生成中枢</h3><p style="color:#888;">输入策略构思，最新的生成结果将自动覆盖回测引擎中的旧策略。</p></div>',
        unsafe_allow_html=True)
    chat_container = st.container(height=450)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("请下达策略指令..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_thesis_data("对话请求", prompt)
        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                bt = "`" * 3
                sys_prompt = f"""你是一名只谈军务的量化专家。
1. **拒答闲聊**：若问题不属于金融、量化、编程、数学、AI范畴（如问候、讲笑话、聊日常），请统一冷酷回复：“主公，末将正全力监视量化前线，概不议论战场琐事，请速下达策略指令或询问学术知识。”
2. **强制函数**：策略必须严格包含 `def generate_signals(df):`。
3. **列名唯一性**：严禁使用小写 close/open，必须使用 'Open', 'High', 'Low', 'Close', 'Volume'。
4. **覆盖逻辑**：代码必须完整，因为新代码会直接覆盖旧逻辑。"""
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
                    code_match = re.search(bt + r"(?:python)?\s*(.*?)" + bt, full_resp, re.DOTALL | re.IGNORECASE)
                    if code_match:
                        # 🔥 物理覆盖：确保 Session 里的 code 是最新的
                        st.session_state.generated_code = code_match.group(1).strip()
                        st.toast("✅ 最新军令已传达，回测沙盒已更新！", icon="🛡️")
                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"API 异常: {e}")
        st.rerun()

# ==========================================
# 📈 页面 3: 深度静态回测 (🔥 全面大写化对齐)
# ==========================================
elif page == "📈 深度静态回测":
    st.markdown('<div class="glass-card"><h3>📈 静态全量沙盒与归因分析</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])
    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        raw_code = st.text_input("🎯 回测标的", value="000001")
        ts_code = format_ts_code(raw_code)
        if st.session_state.generated_code:
            if st.button("🚀 启动回测任务", use_container_width=True, type="primary"):
                with st.spinner("执行最新军令中..."):
                    try:
                        data = ts.pro_bar(ts_code=ts_code, adj='qfq', start_date='20230101').sort_values(
                            'trade_date').reset_index(drop=True)
                        data['trade_date'] = pd.to_datetime(data['trade_date'], format='%Y%m%d')
                        # 🔥 数据源对齐：同时提供大写，并强制后台计算也用大写
                        data['Open'], data['High'], data['Low'], data['Close'], data['Volume'] = data['open'], data[
                            'high'], data['low'], data['close'], data['vol']

                        l_vars = {}
                        exec(st.session_state.generated_code, globals(), l_vars)
                        if 'generate_signals' not in l_vars: raise ValueError(
                            "检测到 AI 漏写了 `generate_signals` 函数！")
                        data = l_vars['generate_signals'](data)

                        # 🔥 后台计算逻辑全面适配大写
                        data['Ret'] = data['Close'].pct_change()
                        data['Pos'] = data['Signal'].replace(0, np.nan).ffill().fillna(0)
                        data['Strat_Ret'] = data['Pos'].shift(1) * data['Ret']
                        data['Cum_Prod'] = (1 + data['Strat_Ret'].fillna(0)).cumprod()
                        st.session_state.bt_result = {"df": data, "code": ts_code}
                    except Exception as e:
                        st.error(f"沙盒异常: {e}")
        else:
            st.warning("🟡 无军令。请先去战情室生成策略。")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            df = st.session_state.bt_result['df']
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05)
            # 使用大写列绘图
            fig.add_trace(
                go.Candlestick(x=df['trade_date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                               name='K线'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['Cum_Prod'], name='净值', fill='tozeroy',
                                     line=dict(color='#00ffcc')), row=2, col=1)
            fig.update_layout(height=600, dragmode='pan', template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                              xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ⚡ 页面 4: 实时交易 (🔥 对齐逻辑)
# ==========================================
elif page == "⚡ 实时交易 (Live)":
    st.markdown('<div class="glass-card"><h3>⚡ 实时高频推演</h3></div>', unsafe_allow_html=True)
    c_ctrl, c_chart = st.columns([1, 2.5])
    with c_ctrl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        live_code = st.text_input("🎯 监控标的", value="000001")
        if st.session_state.generated_code:
            if st.button("▶️ 开启自动交易", type="primary",
                         use_container_width=True): st.session_state.is_live_trading = True
            if st.button("⏹️ 终止撤退", use_container_width=True): st.session_state.is_live_trading = False
        else:
            st.warning("🟡 无策略。")
        st.markdown('</div>', unsafe_allow_html=True)
    with c_chart:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        cht_ph = st.empty()
        if st.session_state.is_live_trading:
            df = ts.pro_bar(ts_code=format_ts_code(live_code), adj='qfq', start_date='20230101').sort_values(
                'trade_date').reset_index(drop=True)
            stream = df.tail(100).reset_index(drop=True)
            for i in range(20, len(stream)):
                if not st.session_state.is_live_trading: break
                sub = stream.iloc[:i].copy()
                sub['Open'], sub['High'], sub['Low'], sub['Close'], sub['Volume'] = sub['open'], sub['high'], sub[
                    'low'], sub['close'], sub['vol']
                l_vars = {}
                exec(st.session_state.generated_code, globals(), l_vars)
                sub = l_vars['generate_signals'](sub)
                fig = go.Figure(data=[
                    go.Candlestick(x=sub['trade_date'], open=sub['Open'], high=sub['High'], low=sub['Low'],
                                   close=sub['Close'])])
                fig.update_layout(height=400, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)',
                                  xaxis_rangeslider_visible=False)
                cht_ph.plotly_chart(fig, use_container_width=True, key=f"l_{i}")
                time.sleep(0.5)
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
        if st.button("🚀 启动训练", use_container_width=True, type="primary"):
            try:
                df = ts.pro_bar(ts_code=format_ts_code(st_code), adj='qfq', start_date='20210101').sort_values(
                    'trade_date').reset_index(drop=True)
                scaler = MinMaxScaler();
                scaled = scaler.fit_transform(df['close'].values.reshape(-1, 1))
                X = [];
                y = []
                for i in range(20, len(scaled)): X.append(scaled[i - 20:i, 0]); y.append(scaled[i, 0])
                X_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1);
                y_t = torch.tensor(np.array(y), dtype=torch.float32)


                class L(nn.Module):
                    def __init__(self): super().__init__(); self.l = nn.LSTM(1, 32, 2,
                                                                             batch_first=True); self.f = nn.Linear(32,
                                                                                                                   1)

                    def forward(self, x): o, _ = self.l(x); return self.f(o[:, -1, :])


                m = L();
                o = torch.optim.Adam(m.parameters(), lr=0.01);
                c = nn.MSELoss()
                lb = st.empty()
                for e in range(20):
                    m.train();
                    o.zero_grad();
                    p = m(X_t);
                    loss = c(p.squeeze(), y_t);
                    loss.backward();
                    o.step()
                    lb.code(f"Epoch {e + 1}/20, Loss: {loss.item():.6f}")
                m.eval();
                test_p = m(X_t[-100:]).detach().numpy()
                st.session_state.dl_result = {"dates": df['trade_date'].iloc[-100:], "actual": df['close'].iloc[-100:],
                                              "pred": scaler.inverse_transform(test_p).flatten()}
            except Exception as e:
                st.error(f"DL 异常: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_r:
        if st.session_state.dl_result:
            res = st.session_state.dl_result
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['actual'], name='真实'))
            fig.add_trace(go.Scatter(x=res['dates'], y=res['pred'], name='预测', line=dict(dash='dot')))
            fig.update_layout(height=400, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 🛡️ 页面 6: 论文数据与日志
# ==========================================
elif page == "🛡️ 论文数据与日志":
    st.markdown('<div class="glass-card"><h3>🛡️ 多维容灾日志</h3></div>', unsafe_allow_html=True)
    if os.path.exists(GLOBAL_LOG_FILE): st.download_button("📁 下载全局日志",
                                                           data=pd.read_csv(GLOBAL_LOG_FILE).to_csv(index=False).encode(
                                                               'utf-8'), file_name='Master.csv')
    st.text_area("Live Stream", value="\n".join(st.session_state.sys_logs), height=350)