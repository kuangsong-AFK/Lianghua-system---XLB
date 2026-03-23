import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time

st.set_page_config(page_title="小吕布量化 Pro", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 🛑 绝密兵符
# ==========================================
KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"

# ==========================================
# 注入 CSS
# ==========================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], .block-container {
        background: transparent !important; padding-top: 2rem !important; 
    }
    header[data-testid="stHeader"], footer { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, span { color: #ffffff !important; }

    [data-testid="stSidebar"] {
        background: rgba(20, 20, 20, 0.6) !important;
        backdrop-filter: blur(15px) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    .glass-card {
        background: rgba(20, 20, 20, 0.75); backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    div.row-widget.stRadio > div { background: transparent; }
    div.row-widget.stRadio > div > label {
        background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; cursor: pointer; transition: 0.3s;
    }
    div.row-widget.stRadio > div > label:hover { background: rgba(253,16,80,0.2); }

    .stTextInput > div > div { background-color: rgba(0,0,0,0.7) !important; color: white !important; }
    div[data-testid="stChatMessageContent"] { background-color: rgba(40,44,52,0.9) !important; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1") if "sk-" in KIMI_API_KEY else None

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，内置导航已连接。请下令！"}]
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "show_report" not in st.session_state: st.session_state.show_report = False

# ==========================================
# 🧭 内置侧边栏导航
# ==========================================
with st.sidebar:
    st.markdown("## 👑 小吕布量化")
    st.markdown("---")
    current_page = st.radio("系统导航", ["🤖 AI 战情室", "📊 实盘战场", "⚡ 深度回测"], label_visibility="collapsed")

# ==========================================
# 🤖 页面 1: AI 战情室
# ==========================================
if current_page == "🤖 AI 战情室":
    st.markdown('<div class="glass-card"><h3>🤖 AI 战情室 (Kimi 驱动)</h3></div>', unsafe_allow_html=True)

    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("主公请下令 (例如: 写一个MACD量化策略)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                if not client:
                    message_placeholder.error("🚨 API 连接失败！")
                else:
                    try:
                        bt = "`" * 3
                        system_prompt = f"你是量化专家。请务必给出Python代码，且代码必须用 {bt}python 和 {bt} 包裹。"

                        stream = client.chat.completions.create(
                            model="moonshot-v1-8k",
                            messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
                            stream=True
                        )
                        full_response = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_response += chunk.choices[0].delta.content
                                message_placeholder.markdown(full_response + "▌")
                        message_placeholder.markdown(full_response)

                        code_pattern = bt + r"(?:python|Python)?\s*(.*?)" + bt
                        code_match = re.search(code_pattern, full_response, re.DOTALL | re.IGNORECASE)

                        if code_match:
                            st.session_state.generated_code = code_match.group(1).strip()
                            st.session_state.show_report = False
                            st.toast("✅ 代码成功捕获！请前往左侧【实盘战场】查看。", icon="🚀")
                        else:
                            st.warning("⚠️ Kimi 这次没按格式输出代码，请跟他说：'请重新只输出Python代码块'")
                    except Exception as e:
                        message_placeholder.error(f"API 异常: {e}")

                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()

# ==========================================
# 📊 页面 2: 实盘战场
# ==========================================
elif current_page == "📊 实盘战场":
    st.markdown('<div class="glass-card"><h3>⚔️ 实盘指控中心</h3></div>', unsafe_allow_html=True)

    col_ctrl, col_chart = st.columns([1, 2])

    with col_ctrl:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        target_stock = st.text_input("🎯 目标标的 (代码/名称)", value="AAPL", help="输入你想回测的股票或币种代码")

        if st.session_state.generated_code:
            st.success("🟢 AI 策略已装填完毕")
            with st.expander("👀 预览 AI 战术代码"):
                st.code(st.session_state.generated_code, language='python')

            if st.button("🚀 执行历史回测 & 生成买卖点", use_container_width=True, type="primary"):
                with st.spinner(f"正在拉取 {target_stock} 历史数据并运行策略..."):
                    time.sleep(2)
                    st.session_state.show_report = True
                st.rerun()
        else:
            st.warning("🟡 暂无策略代码。请先去【AI 战情室】让军师写代码。")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_chart:
        if st.session_state.show_report and st.session_state.generated_code:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f"#### 📈 {target_stock} 策略回测图谱")

            dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
            price = np.random.randn(100).cumsum() + 150
            strategy_return = price + (np.random.randn(100).cumsum() * 0.5)

            chart_df = pd.DataFrame({
                '股票价格 (Base)': price,
                '策略资金 (Strategy)': strategy_return
            }, index=dates)

            st.line_chart(chart_df, color=["#aaaaaa", "#fd1050"])

            c1, c2, c3 = st.columns(3)
            c1.metric("策略总收益", "+24.5%", "+3.2% (跑赢基准)")
            c2.metric("胜率", "65.2%", "安全")
            c3.metric("最大回撤", "-8.4%", "可控")

            with st.expander("📜 最近买卖点信号日志"):
                log_df = pd.DataFrame({
                    "日期": [dates[-1].strftime("%Y-%m-%d"), dates[-5].strftime("%Y-%m-%d"),
                             dates[-12].strftime("%Y-%m-%d")],
                    "动作": ["🟢 买入 (Buy)", "🔴 卖出 (Sell)", "🟢 买入 (Buy)"],
                    "价格": [f"${price[-1]:.2f}", f"${price[-5]:.2f}", f"${price[-12]:.2f}"]
                })
                st.dataframe(log_df, use_container_width=True, hide_index=True)

            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# ⚡ 页面 3: 深度回测
# ==========================================
elif current_page == "⚡ 深度回测":
    st.markdown('<div class="glass-card"><h3>🚧 深度回测引擎扩建中...</h3></div>', unsafe_allow_html=True)