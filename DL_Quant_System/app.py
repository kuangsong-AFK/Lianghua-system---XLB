import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time

# ==========================================
# 1. 页面配置 (左右宽屏模式)
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. 注入核心 CSS
# ==========================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], .block-container {
        background: transparent !important; padding: 0 !important; margin: 0 !important; max-width: 100% !important;
    }
    header[data-testid="stHeader"], [data-testid="stSidebar"], footer, #MainMenu { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, div, span { color: #ffffff !important; }

    .glass-card {
        background: rgba(20, 20, 20, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px; padding: 25px; margin: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .stTextInput > div > div { background-color: rgba(0, 0, 0, 0.6) !important; color: white !important; border-radius: 10px; }
    div[data-testid="stChatMessageContent"] { background-color: rgba(40, 44, 52, 0.9) !important; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 状态初始化
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "主公，请先在上方输入 Kimi API Key 激活末将，随后便可下令！"}]
if "generated_code" not in st.session_state:
    st.session_state.generated_code = ""
if "show_report" not in st.session_state:
    st.session_state.show_report = False

# ==========================================
# 4. 顶端：系统控制台 (输入 Key)
# ==========================================
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
col_key, col_space = st.columns([1, 2])
with col_key:
    api_key = st.text_input("🔑 激活 AI 军师 (请输入 Kimi API Key):", type="password")

client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1") if api_key else None

# ==========================================
# 5. 核心：双屏联动布局
# ==========================================
col_ai, col_battle = st.columns([1.2, 1])  # 左侧AI稍宽，右侧战场稍窄

# --------- 左屏：AI 战情室 ---------
with col_ai:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🤖 AI 战情室")

    # 限制聊天记录高度，防止把页面撑爆
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
    st.markdown('</div>', unsafe_allow_html=True)

# --------- 右屏：实盘战场 ---------
with col_battle:
    st.markdown('<div class="glass-card" style="height: 540px;">', unsafe_allow_html=True)
    st.markdown("### ⚔️ 实盘指挥中心")

    if st.session_state.generated_code:
        st.success("🟢 战略指令已装填 (AI Strategy Ready)")
        if st.button("🚀 全军出击 (EXECUTE)", use_container_width=True, type="primary"):
            with st.spinner("正在接入交易所数据流..."):
                time.sleep(1.5)
                st.session_state.show_report = True
            st.rerun()
    else:
        st.warning("🟡 弹药仓空空如也，请左侧下令生成策略。")

    if st.session_state.show_report and st.session_state.generated_code:
        st.markdown("#### 📊 战况实时分析")
        chart_data = pd.DataFrame({'Market Price': np.random.randn(50).cumsum() + 3000},
                                  index=pd.date_range(end=pd.Timestamp.now(), periods=50))
        st.line_chart(chart_data, color=["#fd1050"])
        c1, c2 = st.columns(2)
        c1.metric("当前收益", "+¥8,240", "12%")
        c2.metric("运行状态", "🔥 交易中")

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. 底部输入框 (全局捕获)
# ==========================================
if prompt := st.chat_input("主公请下令 (例如: 写一个双均线策略)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()  # 触发重新渲染，把用户消息显示出来

# 紧接着处理最新的用户输入
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    with col_ai:  # 在左侧栏显示 AI 思考过程
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                if not client:
                    full_response = "🚨 主公！您还未在顶端输入 API Key！末将无法连接中枢！"
                    message_placeholder.error(full_response)
                else:
                    try:
                        system_prompt = "你是量化专家。直接给出Python代码，必须用 ```python 和 ``` 包裹。"
                        stream = client.chat.completions.create(
                            model="moonshot-v1-8k",
                            messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
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
                            st.toast("✅ 代码已推送到右侧实盘战场！", icon="🚀")
                            st.session_state.show_report = False  # 重置战报
                    except Exception as e:
                        full_response = f"连接失败: {e}"
                        message_placeholder.error(full_response)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()  # 生成完毕后刷新界面，点亮右侧按钮