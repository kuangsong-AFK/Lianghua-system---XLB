import streamlit as st
import pandas as pd
import numpy as np
import tushare as ts
from openai import OpenAI
import re
import time

# --- 1. 页面基础配置 ---
st.set_page_config(layout="wide", page_title="小吕布量化 Pro", initial_sidebar_state="collapsed")

# --- 2. 注入 CSS (保持原来的透明和玻璃化) ---
st.markdown("""
<style>
    .stApp { background: transparent !important; }
    header[data-testid="stHeader"], [data-testid="stSidebar"], section[data-testid="stSidebar"] { display: none !important; }
    * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important; }

    /* 玻璃容器样式 */
    .glass-container {
        background: rgba(30, 30, 30, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px; padding: 20px; margin-bottom: 20px;
    }

    /* 聊天与输入框美化 */
    div[data-testid="stChatMessageContent"] {
        background: rgba(60, 60, 60, 0.4) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px !important;
    }
    .stTextInput > div > div, .stTextArea > div > div {
        background-color: rgba(20, 20, 20, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 初始化核心变量 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""  # 存放 AI 生成的策略代码
if "last_stock" not in st.session_state:
    st.session_state.last_stock = "000001.SZ"

# --- 4. 配置真 AI (Kimi / Moonshot) ---
# 请务必在 Streamlit Cloud 的 Secrets 里配置 OPENAI_API_KEY
# 如果没有配置，这里会尝试从 Secrets 读取，读不到就报错
try:
    api_key = st.secrets.get("OPENAI_API_KEY", "your-key-here")
    base_url = "https://api.moonshot.cn/v1"  # Kimi 的官方接口地址
    client = OpenAI(api_key=api_key, base_url=base_url)
except Exception as e:
    st.error("⚠️ 未配置 API Key，AI 无法启动。请去 Streamlit 后台配置 Secrets。")
    client = None


# --- 5. 辅助函数：提取代码 ---
def extract_code(text):
    """从 AI 回复中提取 Python 代码块"""
    pattern = r"```python(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return matches[-1].strip()  # 返回最后一个代码块
    return ""


# --- 6. 核心路由逻辑 (替代 Tabs) ---
# 获取 URL 参数 ?page=xxx
query_params = st.query_params
current_page = query_params.get("page", "ai_chat")  # 默认显示 AI 战情室

# ==========================================
#           页面 1: 🤖 AI 战情室
# ==========================================
if current_page == "ai_chat":
    st.markdown("### 🤖 AI 战情室 (Kimi 驱动)")

    # 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 处理用户输入
    if prompt := st.chat_input("主公请下令 (例如: 写一个双均线策略，金叉买入死叉卖出)..."):
        # 1. 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. 调用真 AI
        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            if client:
                try:
                    # 系统提示词：强制要求生成 Python 代码
                    system_prompt = """
                    你是一个量化交易专家。用户会让你写策略。
                    请务必遵守：
                    1. 如果用户要求写策略，请生成标准的 Python 代码。
                    2. 代码必须包含一个 `run_strategy(data)` 函数。
                    3. 数据 `data` 是一个 DataFrame，包含 'close', 'open', 'high', 'low', 'vol' 列。
                    4. 返回一个 signals 列表 (1=买, -1=卖, 0=持有)。
                    5. 代码要用 ```python 包裹。
                    """

                    stream = client.chat.completions.create(
                        model="moonshot-v1-8k",  # 使用 Kimi 模型
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

                    # 3. 提取代码并保存到 Session (关键步骤！)
                    code = extract_code(full_response)
                    if code:
                        st.session_state.generated_code = code
                        st.toast("✅ 策略代码已生成并传送至实盘战场！", icon="🚀")

                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                except Exception as e:
                    st.error(f"AI 连接失败: {e}")
            else:
                st.error("请先配置 API Key")

# ==========================================
#           页面 2: 📊 实盘战场
# ==========================================
elif current_page == "battlefield":
    st.markdown("### 📊 实盘战场")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.subheader("📡 策略接收端")

        # 显示当前接收到的代码
        code_input = st.text_area(
            "当前加载的策略代码",
            value=st.session_state.generated_code,
            height=300,
            help="这里显示的是从 AI 战情室传送过来的代码，您也可以手动修改。"
        )

        # 如果修改了，同步回 session
        if code_input != st.session_state.generated_code:
            st.session_state.generated_code = code_input

        if st.button("🚀 执行策略", use_container_width=True):
            if not code_input:
                st.warning("⚠️ 暂无策略代码，请先去 AI 战情室生成！")
            else:
                try:
                    # 模拟数据 (实战时替换为 Tushare)
                    dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
                    data = pd.DataFrame({
                        'close': np.random.randn(100).cumsum() + 10,
                        'open': np.random.randn(100).cumsum() + 10,
                        'high': np.random.randn(100).cumsum() + 12,
                        'low': np.random.randn(100).cumsum() + 8,
                        'vol': np.random.randint(100, 1000, 100)
                    }, index=dates)

                    # 动态执行代码
                    local_vars = {}
                    exec(code_input, globals(), local_vars)

                    # 调用约定的函数
                    if 'run_strategy' in local_vars:
                        signals = local_vars['run_strategy'](data)
                        st.success("✅ 策略执行成功！信号已生成。")
                        # 这里可以画图显示信号...
                        st.line_chart(data['close'])
                    else:
                        st.error("❌ 代码中未找到 `run_strategy(data)` 函数，请让 AI 重写。")

                except Exception as e:
                    st.error(f"❌ 执行报错: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
#           页面 3: ⚡ 深度回测
# ==========================================
elif current_page == "backtest":
    st.markdown("### ⚡ 深度回测 (Backtrader)")
    st.info("🚧 回测模块正在建设中... 这里将集成 Backtrader 框架。")

# ==========================================
#           页面 4: 📂 数据复盘
# ==========================================
elif current_page == "data_review":
    st.markdown("### 📂 历史数据复盘")
    st.write("这里将显示历史交易记录和复盘分析。")

# 兜底
else:
    st.warning("未知页面")