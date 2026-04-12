# ==========================================
# 文件名：app.py (清爽前台 UI 调度中心)
# ==========================================
import streamlit as st
from quant_engine import *  # 召唤模块化引擎
import os
import sys
import uuid
import re
import time
from datetime import datetime
from PIL import Image
from openai import OpenAI
import tushare as ts

# 环境变量静默导入
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import docx
except ImportError:
    docx = None

# 1. 核心兵符与状态初始化
st.set_page_config(page_title="小吕布量化 Pro - 毕设版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"
ts.set_token(TUSHARE_TOKEN)


# 🔥 补天修复：加回丢失的 Tushare 接口初始化兵符 🔥
@st.cache_resource
def get_ts_pro():
    return ts.pro_api()


pro = get_ts_pro()
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=60.0)

if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "messages" not in st.session_state: st.session_state.messages = []
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "strategy_explanation" not in st.session_state: st.session_state.strategy_explanation = "暂无策略解析，请先前往 AI 战情室下达军令。"
if "dl_result" not in st.session_state: st.session_state.dl_result = None
if "bt_result" not in st.session_state: st.session_state.bt_result = None
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "is_live_trading" not in st.session_state: st.session_state.is_live_trading = False

# 2. 空间流形导航逻辑
PAGES = ["🏠 系统总览 (监控中控)", "🤖 AI 策略引擎 (LLM)", "📈 深度静态全量回测", "⚡ 实时高频交易 (Live)",
         "🧠 深度学习预测矩阵", "🛡️ 论文审计日志"]

if "curr_page" not in st.session_state: st.session_state.curr_page = PAGES[0]
if "prev_page" not in st.session_state: st.session_state.prev_page = PAGES[0]

with st.sidebar:
    st.markdown("### 🎓 小吕布量化 Pro")
    st.caption(f"🛡️ 节点 ID: {st.session_state.user_id}")
    st.markdown("---")
    selected_page = st.radio("导航菜单", PAGES, label_visibility="collapsed")

if selected_page != st.session_state.curr_page:
    st.session_state.prev_page = st.session_state.curr_page
    st.session_state.curr_page = selected_page
    st.session_state.just_switched = True
else:
    st.session_state.just_switched = False

prev_idx, curr_idx = PAGES.index(st.session_state.prev_page), PAGES.index(st.session_state.curr_page)
anim_name = "waveBlurUpIn" if curr_idx > prev_idx else ("waveBlurDownIn" if curr_idx < prev_idx else "fogFadeIn")
scroll_script = "window.parent.scrollTo({top: 0, behavior: 'instant'});" if st.session_state.just_switched else ""

# 3. 唤醒量化前端装甲（在 quant_engine.py 中执行，包含水豚噜噜）
inject_frontend_core(anim_name, scroll_script)

# ==========================================
# 4. 各页面精简业务逻辑
# ==========================================
if selected_page == PAGES[0]:
    st.markdown(
        '<div class="glass-card"><h1 style="margin-bottom:0; color:var(--text-color);">🏛️ 全链路智能量化决策枢纽</h1><p class="highlight-text" style="font-size:1.1rem; margin-top:5px;">System Overview & Mid-term Inspection Dashboard</p></div>',
        unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("活跃并发沙盒 (UUID)", st.session_state.user_id)
    with c2:
        st.metric("Tushare 行情链路", get_tushare_status(pro))
    with c3:
        st.metric("大模型底层通信", "🟢 Moonshot-v1 正常")
    with c4:
        st.metric("AI 神经网络", "🟢 融合学习待命")
    st.markdown("---")

    c_arch, c_point = st.columns([2, 1])
    with c_arch:
        st.markdown("""
        <div class="glass-card">
            <h3 style="color:var(--text-color); margin-bottom: 15px;">🌟 平台简介 (Platform Intro)</h3>
            <p style="color:var(--text-color); line-height: 1.8; font-size: 1.05rem;">
                欢迎来到 <b>小吕布量化 Pro</b>，这是一个专为现代极客打造的智能投研终端。<br><br>
                在这里，传统手写代码的繁琐已被彻底颠覆。您可以：<br>
                • <b>📝 全模态投研</b>：一键无缝上传 PDF/Word 研报或 CSV 矩阵，让大模型直接提取精髓。<br>
                • <b>🤖 零代码写策略</b>：通过自然语言对话，Agent 将自动为您生成并修复交易代码。<br>
                • <b>📈 穿越牛熊回测</b>：长达 10 年的全局历史回测，并附带 AI 胜率归因与白话解析。<br>
                • <b>🧠 时序张量预测</b>：利用 LSTM/GRU 融合矩阵，自回归推演未来 5 天的价格轨迹。<br>
            </p>
        </div>
        """, unsafe_allow_html=True)
    with c_point:
        st.markdown(
            '<div class="glass-card"><h4 style="color:var(--text-color);">📋 平台监控与杀手锏</h4>**云端依赖环境**<br>🟢 静默降级护盾运行中<br><br>**答辩核心创新点：**<br>✅ 核心算法模块化剥离<br>✅ 水豚噜噜完全体<br>✅ 全栈代码级防崩溃</div>',
            unsafe_allow_html=True)

elif selected_page == PAGES[1]:
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0; color:var(--text-color);">🤖 LLM 策略战情室</h3><p class="sub-text">多模态视觉引擎与全域文档解析模块已就绪，体验沉浸式工作流。</p></div>',
        unsafe_allow_html=True)

    ctrl_col1, ctrl_col2 = st.columns([1, 1])
    with ctrl_col1:
        selected_model = st.selectbox("🧠 选择大模型算力通道", ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
                                      index=0)
    with ctrl_col2:
        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True); enable_deep_think = st.toggle(
            "💡 强子注入：开启深度思考引擎 (CoT)", value=False)

    chat_container = st.container()
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

    uploaded_files = st.file_uploader("选择文件", accept_multiple_files=True,
                                      type=['pdf', 'doc', 'docx', 'csv', 'txt', 'png', 'jpg', 'jpeg'],
                                      label_visibility="collapsed")

    file_context_text = ""
    if 'uploaded_files' in locals() and uploaded_files:
        cols = st.columns(3)
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 3]:
                fname_lower = file.name.lower()
                if file.type.startswith('image/'):
                    st.image(Image.open(file), use_container_width=True)
                    file_context_text += f"[用户上传了一张图片: {file.name}。]\n"
                elif fname_lower.endswith('.csv'):
                    df_upload = pd.read_csv(file)
                    st.dataframe(df_upload.head(2))
                    file_context_text += f"【CSV 数据源 {file.name} (前100行特征)】:\n{df_upload.head(100).to_string()}\n"
                elif fname_lower.endswith('.txt'):
                    content = file.getvalue().decode('utf-8', errors='replace')
                    st.success(f"📝 {file.name} 挂载成功")
                    file_context_text += f"【TXT 研报核心片段 {file.name}】:\n{content[:5000]}\n"
                elif fname_lower.endswith('.pdf'):
                    if PyPDF2:
                        try:
                            pdf_reader = PyPDF2.PdfReader(file)
                            text = "".join(
                                [page.extract_text() for page in pdf_reader.pages[:10] if page.extract_text()])
                            st.success(f"📄 PDF {file.name} 解析成功")
                            file_context_text += f"【PDF 核心片段 {file.name}】:\n{text[:5000]}\n"
                        except Exception as e:
                            st.error(f"PDF 读取异常: {e}")
                    else:
                        file_context_text += f"[系统缺少 PyPDF2 库，物理静默跳过 {file.name} 的读取]\n"
                elif fname_lower.endswith(('.doc', '.docx')):
                    if docx:
                        try:
                            doc_obj = docx.Document(file)
                            text = "\n".join([para.text for para in doc_obj.paragraphs])
                            st.success(f"📘 Word {file.name} 解析成功")
                            file_context_text += f"【Word 核心片段 {file.name}】:\n{text[:5000]}\n"
                        except Exception as e:
                            st.error(f"Word 读取异常: {e}")
                    else:
                        file_context_text += f"[系统缺少 python-docx 库，物理静默跳过 {file.name} 的读取]\n"

    if raw_prompt := st.chat_input("向小吕布量化架构师发送军令..."):
        full_prompt_for_ai = f"以下是重点参考数据：\n{file_context_text}\n\n指令：{raw_prompt}" if file_context_text else raw_prompt
        st.session_state.messages.append({"role": "user", "content": raw_prompt})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(raw_prompt)
            with st.chat_message("assistant"):
                st.toast(f"🚀 连线算力集群: {selected_model}", icon="⚡")
                ticks = "`" * 3
                sys_p = f"""你是一严谨的量化专家。拒绝闲聊。如果是写策略，必须遵循骨架：\n{ticks}python\ndef generate_signals(df):\n    df['Signal'] = 0\n    return df\n{ticks}"""
                messages_to_send = [{"role": "system", "content": sys_p}] + st.session_state.messages[:-1] + [
                    {"role": "user", "content": full_prompt_for_ai}]
                max_retries, agent_logs = 2, []
                last_error = ""
                full_resp = ""
                msg_box = st.empty()

                for attempt in range(max_retries + 1):
                    if attempt > 0:
                        agent_logs.append(
                            f'<div class="agent-status-node retry">🔄 沙盒拦截异常 (<code>{last_error}</code>) -> Agent 重构</div>')
                        messages_to_send.extend([{"role": "assistant", "content": full_resp},
                                                 {"role": "user", "content": f"报错：`{last_error}`，修复。"}])

                    try:
                        stream = client.chat.completions.create(model=selected_model, messages=messages_to_send,
                                                                stream=True,
                                                                temperature=0.3 if enable_deep_think else 0.7)
                        full_resp = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_resp += chunk.choices[0].delta.content
                                msg_box.markdown(full_resp.replace("<think>", "🧠 深度思考...\n\n").replace("</think>",
                                                                                                           "\n\n---\n") + "▌",
                                                 unsafe_allow_html=True)
                        msg_box.markdown(full_resp.replace("<think>", "🧠 思考过程：\n").replace("</think>", "\n---\n"),
                                         unsafe_allow_html=True)

                        code_match = re.search(r"`{3}python\s*(.*?)\s*`{3}", full_resp, re.DOTALL)
                        resp_clean = re.sub(r"<think>.*?</think>", "", full_resp, flags=re.DOTALL)
                        explanation = re.sub(r"`{3}python\s*.*?\s*`{3}", "", resp_clean, flags=re.DOTALL).strip()
                        explanation = explanation.replace("【策略白话解析】", "").strip()

                        if explanation:
                            st.session_state.strategy_explanation = explanation
                        else:
                            st.session_state.strategy_explanation = "该策略无白话解析。"

                        if not code_match: break

                        extracted_code = code_match.group(1).strip()
                        try:
                            dummy_df = pd.DataFrame(
                                {'trade_date': pd.date_range('20230101', periods=50), 'Open': np.random.rand(50) * 10,
                                 'High': np.random.rand(50) * 12, 'Low': np.random.rand(50) * 8,
                                 'Close': np.random.rand(50) * 10})
                            dummy_df = add_default_indicators(dummy_df)
                            _ = execute_safely(extracted_code, dummy_df)
                            st.session_state.generated_code = extracted_code
                            agent_logs.append(f'<div class="agent-status-node success">✅ 代码沙盒预检通过</div>')
                            st.markdown("".join(agent_logs), unsafe_allow_html=True)
                            break
                        except Exception as e:
                            last_error = str(e)
                            if attempt == max_retries:
                                agent_logs.append(
                                    f'<div class="agent-status-node error">❌ 最终失败: <code>{last_error}</code></div>')
                                st.markdown("".join(agent_logs), unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"链路断开: {e}")
                        full_resp += f"\n\n❌ [异常阻断: {e}]"
                        break

                if agent_logs: full_resp += "\n\n" + "".join(agent_logs)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
        st.rerun()

elif selected_page == PAGES[2]:
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">📊 历史回测全量审计与归因分析</h3></div>',
        unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])
    with col_l:
        ts_code = format_ts_code(st.text_input("🎯 回测标的代码", value="000001"))
        span_mapping = {"近1年": 1, "近3年": 3, "近5年": 5, "近10年 (极限穿越)": 10}
        span_choice = st.selectbox("⏳ 回测时间跨度", list(span_mapping.keys()), index=1)
        start_year = datetime.now().year - span_mapping[span_choice]
        adj_p = st.selectbox("⚖️ 复权模式", ["qfq", "hfq", "None"]).split(" ")[0]
        if st.button("🚀 启动全量归因回测", use_container_width=True, type="primary"):
            with st.spinner("数据挂载中..."):
                try:
                    df_raw = fetch_and_clean_data(pro, ts_code, adj_p if adj_p != "None" else None, f"{start_year}0101")
                    st.session_state.bt_result = run_backtest_metrics(df_raw, st.session_state.generated_code)
                except Exception as e:
                    st.error(f"异常: {e}")

    with col_r:
        if st.session_state.bt_result:
            m, df = st.session_state.bt_result['metrics'], st.session_state.bt_result['df']
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(
                f'<div class="metric-box"><p>累计收益</p><h2 class="highlight-text">{m["total"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c2.markdown(
                f'<div class="metric-box"><p>年化收益</p><h2 class="highlight-text">{m["annual"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c3.markdown(
                f'<div class="metric-box"><p>最大回撤</p><h2 class="danger-text">{m["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c4.markdown(
                f'<div class="metric-box"><p>夏普比率</p><h2 class="highlight-text">{m["sharpe"]:.2f}</h2></div>',
                unsafe_allow_html=True)

            st.markdown("<div style='clear: both; margin-bottom: 30px;'></div>", unsafe_allow_html=True)
            if st.session_state.generated_code and st.session_state.strategy_explanation != "暂无策略解析，请先前往 AI 战情室下达军令。":
                with st.expander("💡 展开：AI 策略白话解析", expanded=False):
                    st.markdown(st.session_state.strategy_explanation)
            st.plotly_chart(render_smart_charts(df), use_container_width=True, config={'scrollZoom': True})

elif selected_page == PAGES[3]:
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">⚡ 高频沙盘模拟推演 (Real-time Flow)</h3></div>',
        unsafe_allow_html=True)
    c_ctrl, c_chart = st.columns([1, 2.5])
    with c_ctrl:
        live_code = st.text_input("🎯 动态推送标的", value="000001")
        freq = st.slider("⏱️ 刷新间隔 (秒)", 0.1, 2.0, 0.5)
        st.button("▶️ 开启高频推演", on_click=lambda: st.session_state.update({"is_live_trading": True}),
                  type="primary")
        st.button("⏹️ 强行停止", on_click=lambda: st.session_state.update({"is_live_trading": False}))
    with c_chart:
        if st.session_state.generated_code and st.session_state.strategy_explanation != "暂无策略解析，请先前往 AI 战情室下达军令。":
            with st.expander("💡 当前军令：策略白话解析", expanded=False):
                st.markdown(st.session_state.strategy_explanation)

        met_ph, cht_ph = st.empty(), st.empty()
        if st.session_state.is_live_trading:
            stream = fetch_and_clean_data(pro, format_ts_code(live_code), 'qfq', '20230101').tail(120).reset_index(
                drop=True)
            for i in range(20, len(stream)):
                if not st.session_state.is_live_trading: break
                sub = stream.iloc[:i].copy()
                try:
                    if st.session_state.generated_code:
                        sub_ai = execute_safely(st.session_state.generated_code, sub)
                        for col in sub_ai.columns:
                            if col == 'Signal' or col.startswith(('MAIN_', 'SUB')): sub[col] = sub_ai[col]
                    sig_val = sub['Signal'].iloc[-1] if 'Signal' in sub.columns else 0
                    with met_ph.container():
                        c = st.columns(3)
                        c[0].metric("Tick 现价", f"{sub['Close'].iloc[-1]:.2f}")
                        c[1].metric("高频信号", "🟢 买" if sig_val == 1 else "🔴 卖" if sig_val == -1 else "⚪ 观望")
                        c[2].metric("并发收益", f"{(sub['Close'].pct_change().iloc[-1] * 100):.2f}%")
                    cht_ph.plotly_chart(render_smart_charts(sub), use_container_width=True)
                except Exception as e:
                    st.error(f"高频熔断: {e}"); st.session_state.is_live_trading = False; break
                time.sleep(freq)

elif selected_page == PAGES[4]:
    with st.spinner("唤醒深度学习底层张量引擎..."):
        import torch
        import torch.nn as nn
        from sklearn.preprocessing import MinMaxScaler

    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧠 深度神经网络时序建模矩阵 (白盒透视版)</h3></div>',
        unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])

    with col_l:
        st_code = st.text_input("🎯 训练模型标的", value="000001")
        span_mapping_dl = {"近1年 (极速)": 1, "近3年 (标准)": 3, "近5年 (深度)": 5}
        span_choice_dl = st.selectbox("⏳ 训练集时间跨度", list(span_mapping_dl.keys()), index=1)
        start_year_dl = datetime.now().year - span_mapping_dl[span_choice_dl]

        model_choices = st.multiselect("🧠 选择预测模型 (支持多选融合)", ["LSTM", "GRU", "1D-CNN"], default=["LSTM"])
        slen = st.slider("📏 滑窗长度", 5, 60, 20)
        eps = st.slider("🔄 Epoch 迭代", 10, 50, 30)

        if st.button("🚀 启动张量训练", type="primary", use_container_width=True):
            if not model_choices:
                st.error("主公，请至少选择一种预测模型！")
            else:
                with st.spinner("神经网络前向传播中..."):
                    try:
                        df = fetch_and_clean_data(pro, format_ts_code(st_code), 'qfq', f"{start_year_dl}0101")
                        scaler = MinMaxScaler()
                        scaled = scaler.fit_transform(df['Close'].values.reshape(-1, 1))
                        X, y = [], []
                        for i in range(slen, len(scaled)):
                            X.append(scaled[i - slen:i, 0])
                            y.append(scaled[i, 0])
                        X_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1)
                        y_t = torch.tensor(np.array(y), dtype=torch.float32)


                        class LSTM_Model(nn.Module):
                            def __init__(self): super().__init__(); self.lstm = nn.LSTM(1, 64, 2,
                                                                                        batch_first=True); self.fc = nn.Linear(
                                64, 1)

                            def forward(self, x): out, _ = self.lstm(x); return self.fc(out[:, -1, :])


                        class GRU_Model(nn.Module):
                            def __init__(self): super().__init__(); self.gru = nn.GRU(1, 64, 2,
                                                                                      batch_first=True); self.fc = nn.Linear(
                                64, 1)

                            def forward(self, x): out, _ = self.gru(x); return self.fc(out[:, -1, :])


                        class CNN_1D_Model(nn.Module):
                            def __init__(self, seq_len):
                                super().__init__()
                                self.conv = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
                                self.fc = nn.Linear(32 * seq_len, 1)

                            def forward(self, x):
                                x = x.permute(0, 2, 1)
                                x = torch.relu(self.conv(x))
                                x = x.reshape(x.size(0), -1)
                                return self.fc(x)


                        preds_dict, future_preds_dict = {}, {}
                        lbox, pbar = st.empty(), st.progress(0)
                        last_window_orig = X_t[-1].clone().unsqueeze(0)

                        for m_idx, m_name in enumerate(model_choices):
                            lbox.markdown(f"**正在训练 {m_name} 模型...**")
                            if m_name == "LSTM":
                                model = LSTM_Model()
                            elif m_name == "GRU":
                                model = GRU_Model()
                            elif m_name == "1D-CNN":
                                model = CNN_1D_Model(slen)

                            opt = torch.optim.Adam(model.parameters(), lr=0.01)
                            crit = nn.MSELoss()

                            for e in range(eps):
                                model.train()
                                opt.zero_grad()
                                pred = model(X_t)
                                loss = crit(pred.squeeze(), y_t)
                                loss.backward()
                                opt.step()
                                pbar.progress((m_idx * eps + e + 1) / (len(model_choices) * eps))
                                lbox.markdown(f"**{m_name}** | Epoch {e + 1}/{eps} | Loss: {loss.item():.6f}")

                            model.eval()
                            test_p = model(X_t[-100:]).detach().numpy()
                            preds_dict[m_name] = scaler.inverse_transform(test_p).flatten()

                            curr_win = last_window_orig.clone()
                            m_future = []
                            for _ in range(5):
                                with torch.no_grad(): p_future = model(curr_win)
                                m_future.append(p_future.item())
                                curr_win = torch.cat((curr_win[:, 1:, :], p_future.unsqueeze(-1)), dim=1)
                            future_preds_dict[m_name] = scaler.inverse_transform(
                                np.array(m_future).reshape(-1, 1)).flatten()

                        lbox.success("✅ 矩阵训练完毕，时空推演已就绪！")
                        st.session_state.dl_result = {
                            "dates": df['trade_date'].iloc[-100:],
                            "actual": df['Close'].iloc[-100:],
                            "preds": preds_dict,
                            "future": future_preds_dict,
                            "models_used": model_choices
                        }
                    except Exception as e:
                        st.error(f"DL 张量异常: {e}")

    with col_r:
        if st.session_state.dl_result:
            res = st.session_state.dl_result
            latest_price = res['actual'].iloc[-1]
            actual_vals = res['actual'].values

            if len(res['models_used']) > 1:
                f_preds = np.mean(list(res['future'].values()), axis=0)
                h_preds = np.mean(list(res['preds'].values()), axis=0)
                model_desc = f"LSTM/GRU/CNN 均值集成 ({len(res['models_used'])}模型)"
            else:
                f_preds = list(res['future'].values())[0]
                h_preds = list(res['preds'].values())[0]
                model_desc = res['models_used'][0]

            act_diff = np.diff(actual_vals)
            pred_diff = np.diff(h_preds)
            success_rate = np.mean(np.sign(act_diff) == np.sign(pred_diff)) * 100
            mape = np.mean(np.abs((actual_vals - h_preds) / (actual_vals + 1e-8))) * 100
            day1_pred, day5_pred = f_preds[0], f_preds[4]

            with st.expander("🤖 AI 深度预测白盒解析舱 (点击展开/收起)", expanded=True):
                st.markdown(
                    f"**📈 极速解盘预览**：当前实盘价 `<span class='highlight-text'>{latest_price:.2f}</span>` | 驱动核心: {model_desc}",
                    unsafe_allow_html=True)
                c_f1, c_f2, c_f3, c_f4 = st.columns(4)
                c_f1.metric("未来 1 天预测 (T+1)", f"{day1_pred:.2f}",
                            f"{(day1_pred - latest_price) / latest_price * 100:.2f}%")
                c_f2.metric("未来 5 天预测 (T+5)", f"{day5_pred:.2f}",
                            f"{(day5_pred - latest_price) / latest_price * 100:.2f}%")
                c_f3.metric("🎯 历史方向胜率", f"{success_rate:.1f}%", "涨跌准确度")
                c_f4.metric("⚖️ 平均预测偏差", f"{mape:.2f}%", "绝对偏离度", delta_color="inverse")

                if st.button("✨ 召唤 Kimi 结合胜率生成人话解盘", use_container_width=True):
                    ai_ph = st.empty()
                    prompt = f"""量化分析师白话解盘：当前收盘价 {latest_price:.2f}元。模型预测1天后 {day1_pred:.2f}元，5天后 {day5_pred:.2f}元。历史胜率 {success_rate:.1f}%，平均偏差度 {mape:.2f}%。请用200字内通俗语言解释趋势，并据此给出风险建议。"""
                    try:
                        stream = client.chat.completions.create(model="moonshot-v1-8k",
                                                                messages=[{"role": "user", "content": prompt}],
                                                                stream=True, temperature=0.5)
                        full_txt = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_txt += chunk.choices[0].delta.content
                                ai_ph.info(full_txt + "▌")
                        ai_ph.info(full_txt)
                    except Exception as e:
                        ai_ph.error(f"连线中断: {e}")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=res['dates'], y=res['actual'], name='真实轨迹', line=dict(color='#00ffcc', width=2)))
            color_map = {"LSTM": "#ff00ff", "GRU": "#ffff00", "1D-CNN": "#00bfff"}
            for m_name, pred_array in res['preds'].items():
                fig.add_trace(go.Scatter(x=res['dates'], y=pred_array, name=f'{m_name} 历史拟合',
                                         line=dict(color=color_map.get(m_name, '#ffffff'), dash='dot', width=1)))
            if len(res['preds']) > 1:
                ensemble_pred = np.mean(list(res['preds'].values()), axis=0)
                fig.add_trace(
                    go.Scatter(x=res['dates'], y=ensemble_pred, name='🔥 均值集成', line=dict(color='#ff4b4b', width=3)))

            fig.update_layout(height=450, template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              dragmode='pan', hovermode='x',
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            st.plotly_chart(fig, use_container_width=True)

elif selected_page == PAGES[5]:
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🛡️ 实验数据采集与多维审计中心</h3></div>',
        unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.2])
    with c1:
        if os.path.exists("user_logs/global_master_log.csv"): st.download_button("📁 导出审计日志", data=pd.read_csv(
            "user_logs/global_master_log.csv").to_csv(index=False).encode('utf-8'), file_name='Audit_Logs.csv',
                                                                                 type="primary")
    with c2:
        st.text_area("实时工作流终端", value="\n".join(st.session_state.sys_logs), height=350)