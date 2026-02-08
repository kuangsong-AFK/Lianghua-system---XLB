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
    initial_sidebar_state="collapsed"  # 强制收起侧边栏
)

# ==========================================
# 2. 注入“幽灵模式” CSS (配合外部 iOS 外壳)
# ==========================================
st.markdown("""
<style>
    /* 1. 让背景全透明，透出外部 HTML 的炫彩背景 */
    .stApp {
        background: transparent !important;
    }

    /* 2. 彻底隐藏 Streamlit 原生的顶部条和侧边栏 (防止重合) */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    [data-testid="stSidebar"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* 3. 字体优化 */
    * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* 4. 玻璃容器 (用于包裹图表、代码框) */
    .glass-container {
        background: rgba(30, 30, 30, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* 5. 聊天气泡美化 */
    div[data-testid="stChatMessageContent"] {
        background: rgba(60, 60, 60, 0.4) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px !important;
        color: #e0e0e0 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    /* 6. 输入框玻璃化 */
    .stTextInput > div > div, .stTextArea > div > div {
        background-color: rgba(20, 20, 20, 0.3) !important;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: white !important;
    }

    /* 7. 按钮高级渐变 */
    .stButton > button {
        background: linear-gradient(135deg, rgba(253, 16, 80, 0.6), rgba(255, 94, 98, 0.6)) !important;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(253, 16, 80, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 初始化 Session State (记忆功能)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "主公，Kimi 已就位！请下令生成策略代码。⚔️"
    })

if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""  # 存放 AI 生成的策略代码

# ==========================================
# 4. 配置 AI (Kimi / Moonshot)
# ==========================================
# 尝试从 Streamlit Secrets 获取 Key，如果没有配置则提示
try:
    # ⚠️ 请确保在 Streamlit 后台配置了 OPENAI_API_KEY
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    base_url = "https://api.moonshot.cn/v1"  # Kimi 官方接口

    if api_key:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = None
except Exception:
    client = None

# ==========================================
# 5. 核心逻辑：路由控制 (替代 Tabs)
# ==========================================
# 获取 URL 参数 ?page=xxx (由 dashboard.html 控制)
query_params = st.query_params
current_page = query_params.get("page", "ai_chat")  # 默认显示 AI 战情室

# ==========================================
# 页面 1: 🤖 AI 战情室
# ==========================================
if current_page == "ai_chat":
    st.markdown("### 🤖 AI 战情室 (Kimi 驱动)")

    # 1. 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 2. 处理用户输入
    if prompt := st.chat_input("主公请下令 (例如: 写一个双均线策略)..."):
        # 显示用户输入
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI 思考与回复
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            if not client:
                st.error("⚠️ 未配置 API Key。请去 Streamlit Cloud -> Settings -> Secrets 配置 OPENAI_API_KEY。")
                full_response = "请配置密钥后重试。"
            else:
                try:
                    # 系统提示词：强制生成 Python 代码
                    system_prompt = """
                    你是一个量化交易专家。用户会让你写策略。
                    请务必遵守：
                    1. 生成标准的 Python 代码。
                    2. 代码必须包含一个 `run_strategy(data)` 函数。
                    3. 数据 `data` 是一个 DataFrame，包含 'close' 列。
                    4. 返回一个 signals 列表或绘图指令。
                    5. 代码用 ```python 包裹。
                    """

                    stream = client.chat.completions.create(
                        model="moonshot-v1-8k",
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

                    # --- 核心功能：提取代码 ---
                    # 使用正则提取 ```python ... ``` 之间的内容
                    code_match = re.search(r"```python(.*?)```", full_response, re.DOTALL)
                    if code_match:
                        extracted_code = code_match.group(1).strip()
                        st.session_state.generated_code = extracted_code
                        st.toast("✅ 策略代码已生成并传送至实盘战场！", icon="🚀")

                except Exception as e:
                    full_response = f"AI 连接出错: {str(e)}"
                    st.error(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

# ==========================================
# 页面 2: 📊 实盘战场
# ==========================================
elif current_page == "battlefield":
    st.markdown("### 📊 实盘战场")

    col1, col2 = st.columns([1, 2])

    # 左侧：代码接收区
    with col1:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.subheader("📡 策略代码")

        # 显示从 AI 战情室传过来的代码
        code_input = st.text_area(
            "AI 生成的策略",
            value=st.session_state.generated_code,
            height=300,
            help="这是 AI 写的代码，您可以手动修改。"
        )
        # 同步修改
        if code_input != st.session_state.generated_code:
            st.session_state.generated_code = code_input

        if st.button("🚀 执行策略", use_container_width=True):
            st.session_state.run_signal = True
        else:
            st.session_state.run_signal = False

        st.markdown('</div>', unsafe_allow_html=True)

    # 右侧：执行结果区
    with col2:
        if st.session_state.get("run_signal", False):
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            st.subheader("📈 执行结果")

            if not code_input:
                st.warning("⚠️ 暂无策略代码，请先去 AI 战情室生成！")
            else:
                try:
                    # 1. 生成模拟数据 (实战可换成 Tushare)
                    dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
                    data = pd.DataFrame({
                        'close': np.random.randn(100).cumsum() + 100
                    }, index=dates)

                    # 2. 动态执行代码
                    local_vars = {}
                    exec(code_input, globals(), local_vars)

                    # 3. 尝试调用约定的函数
                    if 'run_strategy' in local_vars:
                        st.success("✅ 策略函数 `run_strategy` 调用成功！")
                        # 假设函数返回信号或数据
                        result = local_vars['run_strategy'](data)

                        # 简单的可视化
                        st.line_chart(data['close'], color="#fd1050")
                        st.caption("策略基准：模拟收盘价走势")
                    else:
                        st.warning("⚠️ 代码执行完毕，但未找到 `run_strategy` 函数。")

                except Exception as e:
                    st.error(f"❌ 代码执行报错: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # 默认显示占位图
            st.info("👈 请在左侧点击【执行策略】")

# ==========================================
# 页面 3: ⚡ 深度回测
# ==========================================
elif current_page == "backtest":
    st.markdown("### ⚡ 深度回测系统")
    st.info("🚧 Backtrader 回测引擎正在接入中...")

# ==========================================
# 页面 4: 📂 数据复盘
# ==========================================
elif current_page == "data_review":
    st.markdown("### 📂 历史数据复盘")
    st.write("这里将显示历史交易记录。")

# ==========================================
# 兜底逻辑
# ==========================================
else:
    st.warning("正在等待指令...")