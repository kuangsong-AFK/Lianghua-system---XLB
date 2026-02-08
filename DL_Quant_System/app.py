import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import os
import time

# --- 1. 页面基础配置 (必须是第一行) ---
st.set_page_config(
    page_title="小吕布量化 Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"  # 默认收起侧边栏
)

# --- 2. 注入 iOS 液态玻璃风格 CSS (核心美化) ---
st.markdown("""
<style>
    /* 1. 核心：让背景全透明，透出外部 HTML 的液态光晕 */
    .stApp {
        background: transparent !important;
    }

    /* 2. 隐藏 Streamlit 原生的顶部条和侧边栏汉堡按钮 */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    [data-testid="stSidebar"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* 3. 字体优化 - 使用系统级无衬线字体 */
    * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* 4. 磨砂玻璃容器 (用于包裹图表、数据表) */
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
    .stChatMessage {
        background-color: transparent !important;
    }
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

    /* 8. Tabs 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255,255,255,0.05);
        border-radius: 8px;
        color: white;
        border: none;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(253, 16, 80, 0.2) !important;
        color: #fd1050 !important;
        border: 1px solid #fd1050 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 初始化 Session State (记忆功能) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 默认的第一句问候
    st.session_state.messages.append({
        "role": "assistant",
        "content": "主公，小吕布已就位！今日市场风云变幻，我们先看哪个板块？⚔️"
    })


# --- 4. 模拟数据获取函数 (防止 Tushare 报错导致崩溃) ---
def get_mock_data(code):
    """生成模拟的 K 线数据，保证界面有东西看"""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=100)
    data = pd.DataFrame({
        'Date': dates,
        'Close': np.random.randn(100).cumsum() + 100,
        'Volume': np.random.randint(1000, 5000, 100)
    })
    data.set_index('Date', inplace=True)
    return data


# --- 5. 页面布局：使用 Tabs 代替侧边栏 ---
# 这里定义了三个主战场，点击顶部标签切换
tab1, tab2, tab3 = st.tabs(["🤖 AI 战情室", "📊 实盘战场", "⚡ 深度回测"])

# ==========================================
#              Tab 1: AI 战情室
# ==========================================
with tab1:
    st.markdown("### 💬 策略对话")

    # 显示历史消息
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 处理用户输入
    if prompt := st.chat_input("主公请下令 (例如: 分析一下 000001 的趋势)..."):
        # 1. 显示用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. AI 思考中...
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            # --- 这里模拟 AI 回复 (如果您有 Key，请替换为真实 OpenAI 调用) ---
            # 模拟打字机效果
            simulated_response = f"主公，您询问的【{prompt}】正在分析中...\n\n根据系统监测，该标的目前处于多头排列。MACD 金叉向上，RSI 指标位于 55 区间，量能温和放大。建议关注 5日均线 的支撑力度。⚔️"

            for chunk in simulated_response:
                full_response += chunk
                time.sleep(0.02)  # 模拟打字速度
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

        # 3. 保存 AI 回复
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# ==========================================
#              Tab 2: 实盘战场
# ==========================================
with tab2:
    st.markdown("### 📈 市场概览")

    # 顶部控制栏 (玻璃容器)
    with st.container():
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            stock_code = st.text_input("标的代码", "000001.SZ")
        with col2:
            st.write("")  # 占位
            st.write("")
            if st.button("开始扫描", use_container_width=True):
                st.success(f"正在扫描 {stock_code} ...")
        st.markdown('</div>', unsafe_allow_html=True)

    # 图表显示区
    st.markdown("#### K线趋势")
    data = get_mock_data(stock_code)

    # 使用 Streamlit 原生图表，配合透明背景 CSS
    st.line_chart(data['Close'], color="#fd1050")

    # 数据统计卡片
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("当前价格", "12.56", "+0.32%")
    c2.metric("MA5", "12.40", "支撑强")
    c3.metric("主力资金", "1.2亿", "净流入")
    c4.metric("AI 建议", "买入", "信号确立")

# ==========================================
#              Tab 3: 深度回测
# ==========================================
with tab3:
    st.markdown("### ⚡ 策略回测系统")

    col1, col2 = st.columns(2)
    with col1:
        strategy = st.selectbox("选择策略模型", ["双均线策略", "RSI超卖反转", "海龟交易法则", "LSTM深度学习预测"])
        cash = st.number_input("初始资金", value=100000)
    with col2:
        start_date = st.date_input("开始日期")
        end_date = st.date_input("结束日期")

    if st.button("🚀 启动回测引擎", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i in range(101):
            status_text.text(f"正在回放历史数据... {i}%")
            progress_bar.progress(i)
            time.sleep(0.01)

        st.balloons()
        st.success(f"【{strategy}】回测完成！年化收益率：+28.5%")

        # 显示回测结果图表
        chart_data = pd.DataFrame(
            np.random.randn(50, 2).cumsum(axis=0),
            columns=["策略收益", "基准收益"]
        )
        st.area_chart(chart_data, color=["#fd1050", "#408cff"])