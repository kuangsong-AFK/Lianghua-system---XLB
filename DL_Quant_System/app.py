import streamlit as st
import pandas as pd
import numpy as np
import time
import re

# ==========================================
# 1. 基础配置
# ==========================================
st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. 注入 CSS (强制透明 + 无边框 + 隐藏代码框)
# ==========================================
st.markdown("""
<style>
    /* 1. 全局透明 & 去除边距 */
    .stApp, [data-testid="stAppViewContainer"], .block-container {
        background: transparent !important;
        background-color: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    /* 2. 隐藏原生组件 */
    header[data-testid="stHeader"], [data-testid="stSidebar"], footer, #MainMenu {
        display: none !important;
    }

    /* 3. 全局字体白色 */
    .stMarkdown, .stText, p, h1, h2, h3, label, div, span {
        color: #ffffff !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.6);
    }

    /* 4. 玻璃卡片容器 */
    .glass-card {
        background: rgba(20, 20, 20, 0.85);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px; 
        padding: 30px; 
        margin: 20px auto;
        max-width: 90%;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }

    /* 5. 状态条样式 */
    .status-bar {
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .status-success { background: rgba(46, 204, 113, 0.2); border: 1px solid #2ecc71; color: #2ecc71 !important; }
    .status-warn { background: rgba(241, 196, 15, 0.2); border: 1px solid #f1c40f; color: #f1c40f !important; }

    /* 6. 输入框美化 */
    .stTextInput > div > div {
        background-color: rgba(30, 30, 30, 0.8) !important;
        color: white !important;
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 初始化状态
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "主公，AI 战情室已就绪。请下令！"}]
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""
if "show_report" not in st.session_state:
    st.session_state.show_report = False

# ==========================================
# 4. 页面路由
# ==========================================
query_params = st.query_params
current_page = query_params.get("page", "ai_chat")

# ------------------------------------------
# 页面: AI 战情室 (固定底部对话框)
# ------------------------------------------
if current_page == "ai_chat":
    # 聊天记录显示区
    with st.container():
        # 给顶部留点空隙，给底部留出输入框的位置
        st.markdown("<div style='padding-top: 20px; padding-bottom: 100px;'>", unsafe_allow_html=True)
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        st.markdown("</div>", unsafe_allow_html=True)

    # 输入框 (Streamlit 自动固定在底部)
    if prompt := st.chat_input("主公请下令 (例如: 写一个双均线策略)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            st.markdown(f"正在分析【{prompt}】并生成策略代码...")
            time.sleep(1)  # 模拟 AI 思考

            # 模拟生成代码 (存入 Session，不直接显示)
            st.session_state.generated_code = "print('Strategy Executed')"
            st.session_state.show_report = False  # 重置战报状态

            msg = "✅ 策略代码已生成！已自动装填至【实盘战场】。请前往指挥。"
            st.markdown(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})

            # 弹窗提示
            st.toast("🚀 代码已装填，请前往实盘战场！")

# ------------------------------------------
# 页面: 实盘战场 (无代码框版)
# ------------------------------------------
elif current_page == "battlefield":
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)  # 顶部留空

    # 使用玻璃卡片容器
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### ⚔️ 实盘指挥中心")

    # 逻辑判断：是否有代码
    if st.session_state.generated_code:
        # 状态 1: 有代码，待执行
        st.markdown("""
        <div class="status-bar status-success">
            <span>🟢 战术指令已就绪 (AI Strategy Loaded)</span>
        </div>
        """, unsafe_allow_html=True)

        st.write("AI 军师已完成代码部署，全军等待出击指令。")

        # 全军出击按钮
        if st.button("🚀 全军出击 (Execute Strategy)", use_container_width=True, type="primary"):
            with st.spinner("正在连接交易所接口..."):
                time.sleep(1.5)
                st.session_state.show_report = True
            st.rerun()

    else:
        # 状态 2: 无代码
        st.markdown("""
        <div class="status-bar status-warn">
            <span>🟡 等待指令 (Waiting for Strategy)</span>
        </div>
        """, unsafe_allow_html=True)
        st.write("目前尚无作战计划。请前往 **AI 战情室** 生成策略。")

    st.markdown('</div>', unsafe_allow_html=True)

    # 战报显示 (点击按钮后出现)
    if st.session_state.show_report:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📊 实盘分析战报")

        # 模拟图表
        chart_data = pd.DataFrame({
            'Price': np.random.randn(100).cumsum() + 100,
            'MA20': np.random.randn(100).cumsum() + 95
        }, index=pd.date_range(end=pd.Timestamp.now(), periods=100))

        st.line_chart(chart_data, color=["#fd1050", "#2196f3"])

        # 关键指标
        c1, c2, c3 = st.columns(3)
        c1.metric("当日盈亏", "+¥12,450", "3.2%")
        c2.metric("持仓风险率", "15.4%", "-2%")
        c3.metric("执行耗时", "0.45s")

        st.markdown('</div>', unsafe_allow_html=True)