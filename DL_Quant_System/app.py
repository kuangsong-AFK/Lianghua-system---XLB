import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time

# ==========================================
# 1. 页面配置
# ==========================================
st.set_page_config(
    page_title="小吕布量化 Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. 注入 CSS (手动白字 + 暴力透明)
# ==========================================
st.markdown("""
<style>
    /* 1. 【核弹级】移除所有背景色 */
    .stApp, [data-testid="stAppViewContainer"], header, [data-testid="stHeader"] {
        background: transparent !important;
        background-color: rgba(0,0,0,0) !important;
    }

    /* 2. 【关键】因为去掉了 dark 模式，我们要手动把字变白 */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText {
        color: #ffffff !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5); /* 加一点阴影让字更清楚 */
    }

    /* 3. 输入框文字颜色 */
    .stTextInput input, .stTextArea textarea {
        color: #ffffff !important;
    }

    /* 4. 隐藏侧边栏和顶栏 */
    [data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }

    /* 5. 玻璃容器 */
    .glass-container {
        background: rgba(0, 0, 0, 0.5); /* 半透明黑底 */
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px; 
        padding: 20px; 
        margin-bottom: 20px;
    }

    /* 6. 聊天气泡 */
    div[data-testid="stChatMessageContent"] {
        background: rgba(40, 40, 40, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 初始化 Session
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "主公，系统已就位。⚔️"})
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""

# ==========================================
# 4. 配置 AI
# ==========================================
try:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    base_url = "https://api.moonshot.cn/v1"
    client = OpenAI(api_key=api_key, base_url=base_url) if api_key else None
except:
    client = None

# ==========================================
# 5. 页面逻辑
# ==========================================
query_params = st.query_params
current_page = query_params.get("page", "ai_chat")

if current_page == "ai_chat":
    st.markdown("### 🤖 AI 战情室")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("主公请下令..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            if not client:
                st.error("🚨 请配置 Secrets")
            else:
                try:
                    stream = client.chat.completions.create(
                        model="moonshot-v1-8k",
                        messages=[{"role": "system", "content": "Python量化代码."}, *st.session_state.messages],
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
                        st.toast("✅ 代码已传送", icon="🚀")
                except Exception as e:
                    st.error(str(e))
            st.session_state.messages.append({"role": "assistant", "content": full_response})

elif current_page == "battlefield":
    st.markdown("### 📊 实盘战场")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        code_input = st.text_area("策略代码", value=st.session_state.generated_code, height=300)
        if code_input != st.session_state.generated_code: st.session_state.generated_code = code_input
        if st.button("🚀 执行", use_container_width=True): st.session_state.run_signal = True
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        if st.session_state.get("run_signal"):
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
            st.line_chart(pd.DataFrame({'close': np.random.randn(100).cumsum() + 100}, index=dates), color="#fd1050")
            st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "backtest":
    st.info("🚧 开发中...")
elif current_page == "data_review":
    st.info("📂 开发中...")