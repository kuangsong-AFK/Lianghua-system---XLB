import streamlit as st
import pandas as pd
import numpy as np
# from openai import OpenAI # 暂时注释，避免没有 key 报错
import re

# ==========================================
# 1. 页面基础配置
# ==========================================
st.set_page_config(
    page_title="小吕布量化 Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. 注入终极去白边 + 深邃黑 CSS
# ==========================================
st.markdown("""
<style>
    /* 1. 全局重置：强制背景为深色，清除所有默认边距 */
    html, body, [class*="ViewContainer"], [class*="stApp"] {
        margin: 0 !important;
        padding: 0 !important;
        background: transparent !important;
        background-color: #0e1117 !important; /* 设定一个纯粹的深黑底色 */
    }

    /* 2. 核心：清除 Streamlit 主容器的内边距，消灭白边 */
    .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    /* 3. 隐藏所有干扰元素 (顶部栏、侧边栏、页脚、菜单) */
    header[data-testid="stHeader"],
    [data-testid="stSidebar"],
    footer,
    #MainMenu {
        display: none !important;
    }

    /* 4. 重新定义“玻璃容器”：祛除白雾，采用深邃质感 */
    .glass-container {
        /* 使用深黑色高不透明度背景，代替原来的浅色半透明 */
        background-color: rgba(20, 24, 32, 0.9) !important;
        /* 降低模糊度，使视觉更清晰 */
        backdrop-filter: blur(5px);
        /* 使用极细的深色边框，增加精致感 */
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px;
        padding: 20px;
        /* 给容器之间留一点空隙，避免太拥挤 */
        margin: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }

    /* 5. 全局字体强制为白色 */
    .stMarkdown, .stText, h1, h2, h3, p, label, span, div {
        color: #ffffff !important;
    }

    /* 6. 输入框美化：深色背景，融入主题 */
    .stTextInput > div > div, .stTextArea > div > div {
        background-color: rgba(30, 34, 42, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        border-radius: 8px;
    }

    /* 7. 聊天气泡美化：深色背景 */
    div[data-testid="stChatMessageContent"] {
        background-color: rgba(30, 34, 42, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border-radius: 12px;
    }

    /* 8. 图表背景透明，融入深色容器 */
    [data-testid="stVegaLiteChart"] {
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 初始化 Session State
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，视野已全开，白雾已散去！请下令。⚔️"}]
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""

# ==========================================
# 4. 配置 AI (暂时注释，方便调试 UI)
# ==========================================
client = None
# try:
#     api_key = st.secrets.get("OPENAI_API_KEY", "")
#     client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1") if api_key else None
# except: client = None

# ==========================================
# 5. 页面路由逻辑
# ==========================================
query_params = st.query_params
current_page = query_params.get("page", "battlefield")  # 默认先看实盘战场效果

if current_page == "ai_chat":
    # 使用一个容器包裹，稍微留点边距，避免文字贴屏幕太近
    with st.container():
        st.markdown("<div style='margin: 20px;'>", unsafe_allow_html=True)
        st.markdown("### 🤖 AI 战情室")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if prompt := st.chat_input("主公请下令..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                if not client:
                    # st.error("请配置 Secrets")
                    response = "AI 模块暂未连接，请检查配置。"  # 模拟回复
                    st.markdown(response)
                else:
                    # ... (AI 调用代码)
                    pass
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.markdown("</div>", unsafe_allow_html=True)

elif current_page == "battlefield":
    # 实盘战场布局
    col1, col2 = st.columns([1, 2])
    with col1:
        # 左侧代码区容器
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 📜 策略代码")
        st.text_area("代码编辑器", st.session_state.generated_code, height=300, label_visibility="collapsed")
        st.button("🚀 执行策略", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        # 右侧图表区容器
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 📈 市场追踪")
        # 模拟数据图表
        chart_data = pd.DataFrame({
            'Close Price': np.random.randn(100).cumsum() + 100,
            'MA20': np.random.randn(100).cumsum() + 95
        }, index=pd.date_range(end=pd.Timestamp.now(), periods=100))
        st.line_chart(chart_data, color=["#fd1050", "#2196f3"])
        st.markdown('</div>', unsafe_allow_html=True)