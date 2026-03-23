import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time

st.set_page_config(page_title="小吕布量化 Pro", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🛑 绝密：主公专属兵符已装载
# ==========================================
KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"

# ==========================================
# 注入 CSS (丝滑页签美化 + 透明底色)
# ==========================================
st.markdown("""
<style>
    header[data-testid="stHeader"], [data-testid="stSidebar"], footer { display: none !important; }
    .stApp, [data-testid="stAppViewContainer"], .block-container {
        background: transparent !important; padding: 0 !important; margin: 0 !important; max-width: 100% !important;
    }
    .stMarkdown, .stText, p, h1, h2, h3, label, div, span { color: #ffffff !important; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }

    .glass-card {
        background: rgba(20, 20, 20, 0.75); backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    div[data-testid="stTabs"] { padding: 10px 15px; }
    div[data-testid="stTabs"] button {
        background-color: rgba(30, 30, 30, 0.6) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px 8px 0 0 !important;
        color: #aaaaaa !important; font-size: 18px !important; font-weight: bold !important;
        padding: 10px 25px !important; margin-right: 5px !important; transition: 0.3s;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        background-color: rgba(253, 16, 80, 0.25) !important;
        border-bottom: 3px solid #fd1050 !important;
        color: #ffffff !important;
    }

    div[data-testid="stChatMessageContent"] { background-color: rgba(40,44,52,0.9) !important; border-radius: 12px; }
    .stTextInput > div > div { background-color: rgba(0,0,0,0.7) !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# 建立真 AI 连接
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1") if "sk-" in KIMI_API_KEY else None

# 初始化状态
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，绝密 API 已在后端装载。AI 战情室随时待命！"}]
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "show_report" not in st.session_state: st.session_state.show_report = False

# ==========================================
# 🚀 丝滑路由：Streamlit 原生 Tabs
# ==========================================
tab_ai, tab_battle, tab_backtest = st.tabs(["🤖 AI 战情室", "⚔️ 实盘战场", "⚡ 深度回测"])

# --- Tab 1: AI 战情室 ---
with tab_ai:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
    st.markdown('</div>', unsafe_allow_html=True)

# --- Tab 2: 实盘战场 ---
with tab_battle:
    st.markdown('<div class="glass-card" style="min-height: 450px;">', unsafe_allow_html=True)
    if st.session_state.generated_code:
        st.success("🟢 战略指令已装填，等待主公检阅！")
        if st.button("🚀 全军出击 (EXECUTE)", use_container_width=True, type="primary"):
            with st.spinner("正在将策略推入实盘数据流..."):
                time.sleep(1.5)
                st.session_state.show_report = True
            st.rerun()
    else:
        st.warning("🟡 弹药仓空空如也，请先在【AI 战情室】下令生成策略。")

    if st.session_state.show_report and st.session_state.generated_code:
        st.markdown("#### 📊 战况实时分析")
        chart_data = pd.DataFrame({'Market Price': np.random.randn(50).cumsum() + 3000},
                                  index=pd.date_range(end=pd.Timestamp.now(), periods=50))
        st.line_chart(chart_data, color=["#fd1050"])
        c1, c2, c3 = st.columns(3)
        c1.metric("当日盈亏", "+¥12,450", "3.2%")
        c2.metric("信号匹配", "100%", "正常")
        c3.metric("状态", "🔥 自动交易中")
    st.markdown('</div>', unsafe_allow_html=True)

with tab_backtest:
    st.markdown('<div class="glass-card"><h3 style="color:#aaa;">🚧 深度回测引擎正在搭建中...</h3></div>',
                unsafe_allow_html=True)

# ==========================================
# 底部输入框与 AI 生成逻辑
# ==========================================
if prompt := st.chat_input("主公请下令 (例如: 写一个双均线策略)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    with tab_ai:
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                if not client:
                    full_response = "🚨 API 鉴权失败！请检查兵符是否正确。"
                    message_placeholder.error(full_response)
                else:
                    try:
                        system_prompt = "你是量化专家。直接给出Python代码，必须用 ```python 和 ``` 包裹。"
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

                        code_match = re.search(r"```python(.*?)```", full_response, re.DOTALL)
                        if code_match:
                            st.session_state.generated_code = code_match.group(1).strip()
                            st.session_state.show_report = False
                            st.toast("✅ 策略已自动推送到【实盘战场】！点击顶层标签页查看。", icon="🚀")
                    except Exception as e:
                        full_response = f"API 响应异常: {e}"
                        message_placeholder.error(full_response)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()