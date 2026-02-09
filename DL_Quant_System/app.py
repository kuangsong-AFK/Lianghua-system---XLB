import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re

# 1. 基础配置
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# 2. 注入核弹级 CSS (强制剥离所有背景)
st.markdown("""
<style>
    /* 1. 从最底层 html/body 开始强制透明 */
    html, body, [class*="ViewContainer"], [class*="stApp"], header {
        background: transparent !important;
        background-color: transparent !important; /* 兼容性写法 */
        background-image: none !important;
    }

    /* 2. 针对 Streamlit 的根节点 */
    #root {
        background: transparent !important;
    }

    /* 3. 字体强制白色 (防止在深色背景看不清) */
    .stMarkdown, .stText, p, h1, h2, h3, h4, label, span {
        color: #ffffff !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.8); /* 加阴影让字悬浮 */
    }

    /* 4. 输入框美化 (半透明黑底) */
    .stTextInput > div > div, .stTextArea > div > div {
        background-color: rgba(0, 0, 0, 0.5) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }

    /* 5. 隐藏不需要的组件 */
    [data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }

    /* 6. 玻璃容器样式 */
    .glass-container {
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px; 
        padding: 20px; 
        margin-bottom: 20px;
    }

    /* 7. 聊天气泡 */
    div[data-testid="stChatMessageContent"] {
        background: rgba(40, 40, 40, 0.7) !important;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. 初始化 Session
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，幽灵模式已启动。系统透明化完成！⚔️"}]
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""

# 4. AI 配置
try:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1") if api_key else None
except:
    client = None

# 5. 页面路由
query_params = st.query_params
current_page = query_params.get("page", "ai_chat")

if current_page == "ai_chat":
    st.markdown("### 🤖 AI 战情室")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt := st.chat_input("主公请下令..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            if not client:
                st.error("请配置 Secrets")
            else:
                try:
                    stream = client.chat.completions.create(model="moonshot-v1-8k",
                                                            messages=[{"role": "system", "content": "Code."},
                                                                      *st.session_state.messages], stream=True)
                    response = st.write_stream(stream)
                    code = re.search(r"```python(.*?)```", str(response), re.DOTALL)
                    if code: st.session_state.generated_code = code.group(1).strip()
                except Exception as e:
                    st.error(str(e))
            st.session_state.messages.append({"role": "assistant", "content": "..."})

elif current_page == "battlefield":
    st.markdown("### 📊 实盘战场")
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.text_area("策略代码", st.session_state.generated_code, height=300)
        st.button("🚀 执行")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.line_chart(pd.DataFrame({'close': np.random.randn(100).cumsum()},
                                   index=pd.date_range(end=pd.Timestamp.now(), periods=100)))
        st.markdown('</div>', unsafe_allow_html=True)