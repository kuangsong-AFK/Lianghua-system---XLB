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
# 2. 注入 CSS (使用 :root 变量强制透明)
# ==========================================
st.markdown("""
<style>
    /* 1. 【绝杀】直接修改 Streamlit 的根变量，强制背景透明 */
    :root {
        --background-color: transparent;
        --secondary-background-color: transparent;
    }

    /* 2. 确保主容器透明 */
    .stApp {
        background-color: transparent !important;
        background: transparent !important;
    }

    [data-testid="stAppViewContainer"] {
        background-color: transparent !important;
        background: transparent !important;
    }

    /* 3. 隐藏不需要的顶部和侧边栏 */
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }

    /* 4. 修复透明后的字体颜色 (强制白色) */
    .stMarkdown, .stText, h1, h2, h3, p, label {
        color: #ffffff !important;
    }

    /* 5. 玻璃容器 (稍微加深背景，保证文字可读) */
    .glass-container {
        background: rgba(20, 20, 20, 0.6); /* 60% 不透明度的黑 */
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px; 
        padding: 20px; 
        margin-bottom: 20px;
    }

    /* 6. 聊天气泡 */
    div[data-testid="stChatMessageContent"] {
        background: rgba(50, 50, 50, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white !important;
        border-radius: 10px !important;
    }

    /* 7. 输入框 */
    .stTextInput > div > div {
        background-color: rgba(30, 30, 30, 0.6) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 初始化 Session
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "主公，Kimi (Moonshot) 已就位！随时准备生成 Python 策略代码。⚔️"
    })
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""

# ==========================================
# 4. 配置 AI
# ==========================================
try:
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    base_url = "https://api.moonshot.cn/v1"
    if api_key:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = None
except Exception:
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
                st.error("🚨 密钥未配置！")
            else:
                try:
                    stream = client.chat.completions.create(
                        model="moonshot-v1-8k",
                        messages=[{"role": "system", "content": "生成 Python 量化代码, 包含 run_strategy(data)."},
                                  *st.session_state.messages],
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
        if st.button("🚀 执行策略", use_container_width=True): st.session_state.run_signal = True
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        if st.session_state.get("run_signal"):
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            try:
                dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
                data = pd.DataFrame({'close': np.random.randn(100).cumsum() + 100}, index=dates)
                local_vars = {}
                exec(code_input, globals(), local_vars)
                if 'run_strategy' in local_vars:
                    st.success("✅ 执行成功")
                    st.line_chart(data['close'], color="#fd1050")
            except Exception as e:
                st.error(f"❌ 错误: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "backtest":
    st.info("🚧 深度回测开发中...")
elif current_page == "data_review":
    st.info("📂 数据复盘开发中...")