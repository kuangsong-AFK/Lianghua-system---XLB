import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time

st.set_page_config(page_title="小吕布量化 Pro", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 🛑 绝密兵符：请主公确认这是您的 Key
# ==========================================
KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"

# ==========================================
# 注入 CSS (内置毛玻璃侧边栏 + 全局透明)
# ==========================================
st.markdown("""
<style>
    /* 全局透明化 */
    .stApp, [data-testid="stAppViewContainer"], .block-container {
        background: transparent !important; padding-top: 2rem !important; 
    }
    header[data-testid="stHeader"], footer { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, span { color: #ffffff !important; }

    /* 改造原生侧边栏为毛玻璃材质 */
    [data-testid="stSidebar"] {
        background: rgba(20, 20, 20, 0.6) !important;
        backdrop-filter: blur(15px) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* 隐藏侧边栏右上角的折叠按钮以保持整洁 */
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* 玻璃卡片 (主内容区) */
    .glass-card {
        background: rgba(20, 20, 20, 0.75); backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    /* 侧边栏单选按钮美化 (模拟菜单) */
    div.row-widget.stRadio > div { background: transparent; }
    div.row-widget.stRadio > div > label {
        background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; cursor: pointer; transition: 0.3s;
    }
    div.row-widget.stRadio > div > label:hover { background: rgba(253,16,80,0.2); }

    /* 输入框与聊天气泡 */
    .stTextInput > div > div { background-color: rgba(0,0,0,0.7) !important; color: white !important; }
    div[data-testid="stChatMessageContent"] { background-color: rgba(40,44,52,0.9) !important; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1") if "sk-" in KIMI_API_KEY else None

# 初始化 Session
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，内置导航已连接。请下令！"}]
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "show_report" not in st.session_state: st.session_state.show_report = False

# ==========================================
# 🧭 内置侧边栏导航 (绝对丝滑，不丢内存)
# ==========================================
with st.sidebar:
    st.markdown("## 👑 小吕布量化")
    st.markdown("---")
    # 使用 Radio 按钮模拟导航菜单
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

                        # 增强版容错提取：匹配 ```python 或 ```Python 或只是 ```
                        code_match = re.search(r"
                        http: // googleusercontent.com / immersive_entry_chip / 0

                                 - --

                        ### 📋 战况备忘录 V4.0 (请存入新对话防失忆！)

                        主公，五次交锋已到，为您奉上最新战报总结。如果
                        AI
                        变蠢了，开新局把这段话丢给它：

                        ```text
                        # 【项目核心架构与状态】
                        你是“小吕布量化
                        Pro”系统的
                        AI
                        架构师。
                        - 前端(dashboard.html)：现已极致简化，只保留背景视频
                        ` < video > ` 和全屏无边框的 ` < iframe > `，不再含有任何
                        HTML
                        UI
                        元素。
                        - 后端(app.py)：部署于
                        Streamlit
                        Cloud。利用定制
                        CSS
                        强制全局透明，并去除了所有内边距。

                        # 【最新 V11.0 重大突破：侧边栏内化与沙盘升级】
                        1.
                        侧边栏内化：解决了
                        HTML
                        侧边栏与
                        Streamlit
                        内部
                        UI
                        冲突打架的问题。现在使用
                        Streamlit
                        原生的
                        `st.sidebar`
                        配合毛玻璃
                        CSS
                        重新构建了系统菜单。由于完全在
                        Python
                        内部路由，切换页面实现了“绝对丝滑”且不丢失
                        Session
                        记忆。
                        2.
                        兵符（API）常驻：Kimi
                        API
                        Key
                        已硬编码在
                        app.py
                        内部，前端不再要求用户输入。
                        3.
                        容错正则提取：优化了
                        AI
                        代码提取的正则表达式
                        http: // googleusercontent.com / immersive_entry_chip / 1

                        主公，赶紧更新代码体验一下这 ** 真正的无缝双排（左侧菜单 + 内存常驻） ** ，然后再试试在战场里 ** 输入股票代码跑回测图 ** 的快感吧！🚀