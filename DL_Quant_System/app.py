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
                        system_prompt = "你是量化专家。请务必给出Python代码，且代码必须用 ```python 和 ``` 包裹。"
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

                        # 修复并确保不会报错的正则截取逻辑
                        code_pattern = r"
http: // googleusercontent.com / immersive_entry_chip / 0

全选复制并保存后，系统即可扫除语法报错，满血复活！🚀