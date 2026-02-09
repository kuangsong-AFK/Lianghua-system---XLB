import streamlit as st
import pandas as pd
import numpy as np
# from openai import OpenAI # 暂时注释，避免没有 key 报错
import re
import time

# ==========================================
# 1. 页面配置 (布局全开)
# ==========================================
st.set_page_config(
    page_title="小吕布量化 Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# 2. 注入核弹级 CSS (透明 + 无边框 + 底部输入框优化)
# ==========================================
st.markdown("""
<style>
    /* 1. 【核心】强制背景透明 (修正之前的错误) */
    .stApp, [data-testid="stAppViewContainer"], header, .block-container {
        background: transparent !important;
        background-color: transparent !important;
    }

    /* 2. 【核心】暴力清除所有白边 */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    /* 3. 隐藏干扰元素 */
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    footer { display: none !important; }
    #MainMenu { display: none !important; }

    /* 4. 全局字体白色 */
    .stMarkdown, .stText, h1, h2, h3, h4, p, label, span, div {
        color: #ffffff !important;
    }

    /* 5. 玻璃容器 (去除雾蒙蒙，使用深色半透明) */
    .glass-card {
        background: rgba(20, 20, 20, 0.85); /* 深色背景，不发白 */
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px; 
        padding: 20px; 
        margin: 20px; /* 容器自己留点边，不贴屏幕 */
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    /* 6. 状态指示器样式 */
    .status-box {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
    }
    .status-ready { background: rgba(39, 174, 96, 0.3); border: 1px solid #27ae60; color: #2ecc71 !important; }
    .status-wait { background: rgba(230, 126, 34, 0.3); border: 1px solid #d35400; color: #f39c12 !important; }

    /* 7. 输入框美化 */
    .stTextInput > div > div {
        background-color: rgba(0, 0, 0, 0.7) !important;
        color: white !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }

    /* 8. 聊天气泡 */
    div[data-testid="stChatMessageContent"] {
        background-color: rgba(40, 44, 52, 0.9) !important;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 初始化 Session
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，AI 战情室已就位！请下令生成策略。"}]
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""  # 存放生成的代码
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = None  # 存放回测结果

# ==========================================
# 4. 路由逻辑
# ==========================================
query_params = st.query_params
current_page = query_params.get("page", "ai_chat")

# ------------------------------------------
# 页面 1: 🤖 AI 战情室
# ------------------------------------------
if current_page == "ai_chat":
    # 使用 container 包裹聊天记录，留出顶部空间
    chat_container = st.container()

    with chat_container:
        st.markdown("<div style='padding: 20px;'>", unsafe_allow_html=True)  # 增加内边距
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        st.markdown("</div>", unsafe_allow_html=True)
        # 增加一个巨大的空底，防止最后一条消息被输入框挡住
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)

    # 固定底部的输入框 (Streamlit 默认就是固定的)
    if prompt := st.chat_input("主公请下令 (例如: 写一个双均线策略)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            # 模拟 AI 生成 (您后续接回 Kimi)
            response = f"主公，正在生成关于【{prompt}】的量化策略..."
            st.markdown(response)

            # 模拟生成代码 (实际中这里是 AI 的输出)
            fake_code = """
def run_strategy(data):
    return data['close'] > data['close'].rolling(20).mean()
"""
            st.session_state.generated_code = fake_code
            st.toast("✅ 策略代码已生成并装填至实盘战场！", icon="🚀")

            st.session_state.messages.append(
                {"role": "assistant", "content": "策略代码已生成！请前往【实盘战场】下令出击。"})
            # 强制刷新一下让 toast 显示
            time.sleep(1)
            st.rerun()

# ------------------------------------------
# 页面 2: 📊 实盘战场 (重构版)
# ------------------------------------------
elif current_page == "battlefield":
    # 居中显示的大容器
    col_spacer1, col_main, col_spacer2 = st.columns([1, 8, 1])

    with col_main:
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)  # 顶部留空

        # 1. 状态显示区
        if st.session_state.generated_code:
            st.markdown("""
            <div class="glass-card">
                <div class="status-box status-ready">
                    🟢 战术指令已就绪 (AI Strategy Loaded)
                </div>
                <div style="color: #ccc; font-size: 14px; margin-bottom: 10px;">
                    AI 军师已完成策略部署，等待主公最后确认。
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 2. 全军出击按钮
            if st.button("🚀 全军出击 (Execute)", use_container_width=True, type="primary"):
                with st.spinner("正在进行实盘数据演算..."):
                    time.sleep(1.5)  # 模拟计算
                    st.session_state.analysis_report = True
                st.rerun()

        else:
            st.markdown("""
            <div class="glass-card">
                <div class="status-box status-wait">
                    🟡 等待指令 (Waiting for Strategy)
                </div>
                <div style="color: #ccc;">
                    请先前往 <b style="color:#fd1050">AI 战情室</b> 生成策略代码。
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 3. 实盘分析战报 (执行后显示)
        if st.session_state.get("analysis_report"):
            st.markdown("""
            <div class="glass-card">
                <h3 style="border-bottom: 2px solid #fd1050; padding-bottom: 10px;">⚔️ 实盘分析战报</h3>
                <p style="color: #aaa; margin-top: 10px;">策略执行完毕，最新市场数据如下：</p>
            </div>
            """, unsafe_allow_html=True)

            # 渲染图表 (在玻璃卡片内)
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            chart_data = pd.DataFrame({
                'Close': np.random.randn(100).cumsum() + 100,
                'Signal': np.random.randint(0, 2, 100) * 10
            }, index=pd.date_range(end=pd.Timestamp.now(), periods=100))
            st.line_chart(chart_data, color=["#fd1050", "#00ccff"])

            cols = st.columns(3)
            cols[0].metric("预期收益", "+12.5%", "2.1%")
            cols[1].metric("最大回撤", "-3.2%", "0.5%")
            cols[2].metric("夏普比率", "1.85", "0.1")
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------
# 其他页面
# ------------------------------------------
elif current_page == "backtest":
    st.info("⚡ 深度回测开发中...")
elif current_page == "data_review":
    st.info("📂 数据复盘开发中...")