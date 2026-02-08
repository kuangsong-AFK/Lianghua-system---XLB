import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time

# ==========================================
# 1. 页面基础配置 (必须是第一行)
# ==========================================
st.set_page_config(
    page_title="小吕布量化 Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. 注入“幽灵模式” CSS (配合外部 iOS 外壳)
# ==========================================
st.markdown("""
<style>
    /* 1. 让背景全透明 */
    .stApp { background: transparent !important; }

    /* 2. 隐藏原生组件 */
    header[data-testid="stHeader"], [data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }

    /* 3. 全局字体 */
    * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important; }

    /* 4. 玻璃容器 */
    .glass-container {
        background: rgba(30, 30, 30, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px; padding: 20px; margin-bottom: 20px;
    }

    /* 5. 聊天气泡 */
    div[data-testid="stChatMessageContent"] {
        background: rgba(60, 60, 60, 0.4) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px !important;
        color: #e0e0e0 !important;
    }

    /* 6. 输入框 */
    .stTextInput > div > div, .stTextArea > div > div {
        background-color: rgba(20, 20, 20, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }

    /* 7. 按钮 */
    .stButton > button {
        background: linear-gradient(135deg, rgba(253, 16, 80, 0.6), rgba(255, 94, 98, 0.6)) !important;
        color: white !important;
        font-weight: 600 !important;
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
# 4. 配置 Kimi AI (从 Secrets 读取)
# ==========================================
try:
    # 这里的代码会自动去 Streamlit 后台找您刚才填的 Key，绝对安全！
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    base_url = "https://api.moonshot.cn/v1"  # Kimi 官方接口

    if api_key:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = None
except Exception:
    client = None

# ==========================================
# 5. 核心逻辑：路由控制
# ==========================================
# 获取 URL 参数 ?page=xxx
query_params = st.query_params
current_page = query_params.get("page", "ai_chat")

# --- 🤖 AI 战情室 ---
if current_page == "ai_chat":
    st.markdown("### 🤖 AI 战情室 (Kimi 驱动)")

    # 1. 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 2. 用户输入
    if prompt := st.chat_input("主公请下令 (例如: 写一个双均线策略)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 回复
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            if not client:
                st.error("🚨 密钥未配置！请去 Streamlit Cloud -> Settings -> Secrets 填入您的 Kimi Key。")
                full_response = "请配置密钥。"
            else:
                try:
                    # 系统提示词：强制 Kimi 写 Python
                    system_prompt = """
                    你是一个量化交易专家。用户会让你写策略。
                    1. 必须生成 Python 代码，包含 run_strategy(data) 函数。
                    2. data 包含 'close' 列。
                    3. 代码用 ```python 包裹。
                    """

                    stream = client.chat.completions.create(
                        model="moonshot-v1-8k",  # 指定 Kimi 模型
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *st.session_state.messages
                        ],
                        stream=True
                    )

                    full_response = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")

                    message_placeholder.markdown(full_response)

                    # 提取代码
                    code_match = re.search(r"```python(.*?)```", full_response, re.DOTALL)
                    if code_match:
                        st.session_state.generated_code = code_match.group(1).strip()
                        st.toast("✅ 策略代码已传送至实盘战场！", icon="🚀")

                except Exception as e:
                    full_response = f"Kimi 连接失败: {str(e)}"
                    st.error(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

# --- 📊 实盘战场 ---
elif current_page == "battlefield":
    st.markdown("### 📊 实盘战场")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.subheader("📡 策略代码")
        code_input = st.text_area("AI 生成代码", value=st.session_state.generated_code, height=300)

        # 同步修改
        if code_input != st.session_state.generated_code:
            st.session_state.generated_code = code_input

        if st.button("🚀 执行策略", use_container_width=True):
            st.session_state.run_signal = True
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if st.session_state.get("run_signal"):
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            try:
                # 模拟数据
                dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
                data = pd.DataFrame({'close': np.random.randn(100).cumsum() + 100}, index=dates)

                # 执行代码
                local_vars = {}
                exec(code_input, globals(), local_vars)

                if 'run_strategy' in local_vars:
                    st.success("✅ 策略执行成功！")
                    st.line_chart(data['close'], color="#fd1050")
                else:
                    st.warning("⚠️ 未找到 run_strategy 函数")
            except Exception as e:
                st.error(f"❌ 执行报错: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

# --- 其他页面 ---
elif current_page == "backtest":
    st.info("🚧 深度回测开发中...")
elif current_page == "data_review":
    st.info("📂 数据复盘开发中...")
else:
    st.warning("等待指令...")