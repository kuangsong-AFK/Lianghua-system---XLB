import streamlit as st
import pandas as pd
import numpy as np
import base64
import re
from openai import OpenAI
import os

# --- 引入 UI 神器 ---
try:
    import streamlit_antd_components as sac
    import streamlit_shadcn_ui as ui
    from streamlit_lightweight_charts_ntf import renderLightweightCharts
except ImportError:
    st.error("⚠️ 缺少关键装备！请在终端运行: pip install streamlit-antd-components streamlit-shadcn-ui")
    st.stop()

try:
    import main
except ImportError:
    st.error("缺少 main.py"); st.stop()

# -----------------------------------------------------------------------------
# 1. 启动配置
# -----------------------------------------------------------------------------
st.set_page_config(page_title="小吕布量化系统", layout="wide", initial_sidebar_state="expanded")
KIMI_API_KEY = "sk-hWbNgtl9DkMhL2r5bQ3g7Uinvs9XWV8vMrs5QUVX25Hy9wi4"
AI_AVATAR_PATH = "ai_avatar.png"

# --- 全局 CSS ---
st.markdown("""
<style>
    .stApp { background-color: #09090b; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    .stChatMessage .st-emotion-cache-p5msec { width: 3rem; height: 3rem; border-radius: 10px; }

    /* 自定义指标卡片 */
    .custom-metric-card {
        background-color: #18181b; border: 1px solid #27272a; border-radius: 0.5rem;
        padding: 1.5rem; position: relative; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: all 0.2s; display: flex; flex-direction: column; justify-content: center; height: 100px;
    }
    .custom-metric-card:hover { border-color: #3f3f46; }
    .metric-label { font-size: 0.875rem; font-weight: 500; color: #a1a1aa; margin-bottom: 0.5rem; }
    .metric-value { font-size: 1.5rem; font-weight: 600; letter-spacing: -0.025em; color: #f4f4f5; font-family: monospace; }

    /* 问号与提示框 */
    .metric-help {
        position: absolute; top: 0.75rem; right: 0.75rem; width: 1.2rem; height: 1.2rem;
        border-radius: 50%; background: #27272a; color: #71717a; font-size: 0.75rem;
        display: flex; align-items: center; justify-content: center; cursor: help; transition: all 0.2s;
    }
    .metric-help:hover { background: #3f3f46; color: #fff; }
    .metric-tooltip {
        visibility: hidden; width: 200px; background-color: #000; color: #e4e4e7; text-align: left;
        border-radius: 6px; padding: 10px; position: absolute; z-index: 100; bottom: 110%; right: -10px;
        opacity: 0; transition: opacity 0.3s; font-size: 0.75rem; line-height: 1.4;
        border: 1px solid #333; box-shadow: 0 4px 12px rgba(0,0,0,0.5); pointer-events: none;
    }
    .metric-help:hover .metric-tooltip { visibility: visible; opacity: 1; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 状态管理
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant",
                                  "content": "主公！研报系统已上线。\n\n在【实盘战场】运行策略后，点击 **【📜 导出精美研报】** 即可获取专业分析报告！🛡️"}]
if "last_code" not in st.session_state: st.session_state.last_code = None
if "report_data" not in st.session_state: st.session_state.report_data = {"df": None, "metrics": None, "years": 0,
                                                                          "error": None}
if "selected_indics_state" not in st.session_state: st.session_state.selected_indics_state = ["MACD"]

if "indicator_params" not in st.session_state:
    st.session_state.indicator_params = {
        'ma1': 5, 'ma2': 10, 'ma3': 20, 'ma4': 60,
        'macd_fast': 12, 'macd_slow': 26, 'macd_signal': 9,
        'rsi_period': 14,
        'kdj_n': 9, 'kdj_m1': 3, 'kdj_m2': 3,
        'bias1': 6, 'bias2': 12, 'bias3': 24
    }


# -----------------------------------------------------------------------------
# 3. 工具函数
# -----------------------------------------------------------------------------
def clean_data(df, col_name):
    if col_name not in df.columns: return []
    df_clean = df[['time', col_name]].dropna()
    df_clean.columns = ['time', 'value']
    return df_clean.to_dict('records')


def auto_detect_indicators(code_str):
    if not code_str: return
    s = code_str.lower()
    detected = {
        "MACD": 'macd' in s,
        "RSI": 'rsi' in s,
        "KDJ": 'kdj' in s or ('k' in s and 'd' in s),
        "BIAS": 'bias' in s
    }
    final_list = [k for k, v in detected.items() if v]
    if final_list: st.session_state.selected_indics_state = final_list


def encode_image(f): return base64.b64encode(f.getvalue()).decode('utf-8') if f else None


def metric_card(label, value, tooltip_text):
    html = f"""<div class="custom-metric-card"><div class="metric-help">?<div class="metric-tooltip">{tooltip_text}</div></div><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>"""
    st.markdown(html, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 4. 侧边栏
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🛡️ 小吕布 · Pro")
    menu = sac.menu([
        sac.MenuItem('AI 战情室', icon='robot', description='策略对话'),
        sac.MenuItem('实盘战场', icon='graph-up-arrow', description='图表与回测'),
    ], index=0, format_func='title', size='sm', color='indigo')
    st.divider()
    with st.container(border=True):
        st.caption("🎮 战场控制")
        input_code = st.text_input("标的代码", value="000001", placeholder="6位代码")
        mode = sac.segmented(
            [sac.SegmentedItem(label='AI 策略', icon='cpu'), sac.SegmentedItem(label='LSTM', icon='lightning')],
            align='center', size='sm', color='indigo')
        if mode == 'LSTM': train_epochs = st.slider("训练轮数", 5, 50, 10)
    col_reset, col_clear = st.columns(2)
    with col_reset:
        if ui.button("🗑️ 重置对话", variant="outline", key="btn_reset"):
            st.session_state.messages = [{"role": "assistant", "content": "方天画戟已擦亮，小吕布听候差遣！"}];
            st.session_state.last_code = None;
            st.rerun()


# -----------------------------------------------------------------------------
# 5. 参数设置
# -----------------------------------------------------------------------------
def render_settings_content():
    p = st.session_state.indicator_params
    with st.container():
        st.caption("📊 均线系统 (MA)")
        c1, c2 = st.columns(2)
        p['ma1'] = c1.number_input("MA 1", value=p['ma1'], min_value=1)
        p['ma2'] = c2.number_input("MA 2", value=p['ma2'], min_value=1)
        c3, c4 = st.columns(2)
        p['ma3'] = c3.number_input("MA 3", value=p['ma3'], min_value=1)
        p['ma4'] = c4.number_input("MA 4", value=p['ma4'], min_value=1)
        st.divider()
        st.caption("📈 MACD & RSI")
        c1, c2, c3 = st.columns(3)
        p['macd_fast'] = c1.number_input("Fast", value=p['macd_fast'])
        p['macd_slow'] = c2.number_input("Slow", value=p['macd_slow'])
        p['macd_signal'] = c3.number_input("Sig", value=p['macd_signal'])
        p['rsi_period'] = st.number_input("RSI 周期", value=p['rsi_period'])
        st.divider()
        st.caption("📉 KDJ & BIAS")
        c1, c2, c3 = st.columns(3)
        p['kdj_n'] = c1.number_input("KDJ N", value=p['kdj_n'])
        p['kdj_m1'] = c2.number_input("KDJ M1", value=p['kdj_m1'])
        p['kdj_m2'] = c3.number_input("KDJ M2", value=p['kdj_m2'])
        c4, c5, c6 = st.columns(3)
        p['bias1'] = c4.number_input("BIAS 1", value=p['bias1'])
        p['bias2'] = c5.number_input("BIAS 2", value=p['bias2'])
        p['bias3'] = c6.number_input("BIAS 3", value=p['bias3'])
    st.markdown("<br>", unsafe_allow_html=True)
    if ui.button("💾 保存配置", key="save_params_btn", className="w-full"): st.rerun()


if hasattr(st, 'dialog'):
    @st.dialog("⚙️ 军械库 (参数配置)", width="large")
    def open_settings_dialog():
        render_settings_content()
else:
    def open_settings_dialog():
        st.sidebar.warning("请升级 Streamlit")

# -----------------------------------------------------------------------------
# 6. 主界面
# -----------------------------------------------------------------------------
run_trigger = False

if menu == 'AI 战情室':
    chat_container = st.container(height=600)
    avatar_img = AI_AVATAR_PATH if os.path.exists(AI_AVATAR_PATH) else "🤖"
    for msg in st.session_state.messages:
        avatar = avatar_img if msg["role"] == "assistant" else None
        with chat_container.chat_message(msg["role"], avatar=avatar):
            if isinstance(msg["content"], list):
                for item in msg["content"]:
                    if item["type"] == "text":
                        st.markdown(item["text"])
                    elif item["type"] == "image_url":
                        st.image(item["image_url"]["url"], width=200)
            else:
                st.markdown(msg["content"])
    with st.container():
        c_up, c_in = st.columns([1, 8])
        with c_up: uploaded_file = st.file_uploader("传图", type=['png', 'jpg'], label_visibility="collapsed")
        with c_in: prompt = st.chat_input("主公请下令... (例如：当MA1上穿MA2时买入)")
    if prompt:
        user_content = [{"type": "text", "text": prompt}]
        with chat_container.chat_message("user"):
            st.markdown(prompt)
            if uploaded_file:
                st.image(uploaded_file, width=200);
                base64_img = encode_image(uploaded_file)
                user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}})
        st.session_state.messages.append({"role": "user", "content": user_content if uploaded_file else prompt})
        try:
            client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1")
            sys_prompt = """【角色】小吕布 (霸气)。【白名单】df['ma_1'], df['macd_dif']...【模板】\ncondition = (...)\ndf['signal'] = np.where(condition, 1, 0)"""
            api_msgs = [{"role": "system", "content": sys_prompt}]
            for m in st.session_state.messages:
                c = m["content"]
                if isinstance(c, list): c = next((i["text"] for i in c if i["type"] == "text"), "") + " [图片]"
                api_msgs.append({"role": m["role"], "content": c})
            with chat_container.chat_message("assistant", avatar=avatar_img):
                with st.spinner("小吕布正在擦拭方天画戟..."):
                    stream = client.chat.completions.create(model="moonshot-v1-128k", messages=api_msgs,
                                                            temperature=0.2, stream=True)
                    response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})
            code_m = re.findall(r'```python(.*?)```', response, re.DOTALL)
            if code_m:
                st.session_state.last_code = code_m[-1].strip()
                auto_detect_indicators(st.session_state.last_code)
                st.toast("策略已生成！请点击左侧【实盘战场】查看战果！", icon="⚔️")
        except Exception as e:
            st.error(f"AI Error: {e}")

elif menu == '实盘战场':
    c_info, c_act = st.columns([3, 1.5])
    with c_info:
        st.title(f"📈 {input_code} 战役复盘")
        if mode == "AI 策略" and st.session_state.last_code:
            st.caption("✅ 当前已装配 AI 锦囊策略")
        elif mode == "LSTM":
            st.caption(f"⚡ 深度学习模式 (训练 {train_epochs} 轮)")
    with c_act:
        c_run, c_set = st.columns([2, 1])
        with c_run:
            if ui.button("🚀 全军突击", variant="primary", key="run_strategy", className="w-full"): run_trigger = True
        with c_set:
            if ui.button("⚙️ 参数", variant="outline", key="open_settings", className="w-full"): open_settings_dialog()

    if run_trigger:
        with st.spinner('战鼓擂动，正在冲锋...'):
            st.session_state.report_data = {"df": None, "metrics": None, "years": 0, "error": None}
            try:
                params = st.session_state.indicator_params
                if mode == "LSTM":
                    res_df, metrics, years, error_msg = main.run_full_pipeline(input_code, epochs=train_epochs,
                                                                               params=params)
                else:
                    if not st.session_state.last_code: st.error("请先去【AI 战情室】生成策略！"); st.stop()
                    auto_detect_indicators(st.session_state.last_code)
                    res_df, metrics, years, error_msg = main.run_ai_strategy(input_code, st.session_state.last_code,
                                                                             params=params)
                st.session_state.report_data.update(
                    {"df": res_df, "metrics": metrics, "years": years, "error": error_msg})
            except Exception as e:
                st.session_state.report_data["error"] = str(e)

    data = st.session_state.report_data
    if data["error"]:
        ui.alert(title="军情告急", description=data["error"], key="alert_error")
    elif data["df"] is not None:
        df = data["df"].copy()
        if len(df) > 500: df = df.iloc[-500:].copy().reset_index(drop=True)
        if 'date' in df.columns:
            df['time'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        elif 'trade_date' in df.columns:
            df['time'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')

        num_cols = df.select_dtypes(include=[np.number]).columns
        df[num_cols] = df[num_cols].fillna(0).replace([np.inf, -np.inf], 0)

        m = data['metrics']
        cols = st.columns(4)
        with cols[0]:
            metric_card("胜率", f"{m.get('win_rate', 0):.2%}", "<b>胜率</b><br>盈利次数 ÷ 总交易次数。")
        with cols[1]:
            metric_card("累计收益", f"{(df['cum_strategy_return'].iloc[-1] - 1) * 100:+.2f}%",
                        "<b>累计收益</b><br>战利品总额。")
        with cols[2]:
            metric_card("夏普比率", f"{m.get('sharpe', 0):.2f}", "<b>夏普比率</b><br>风险收益比，>1 为优秀。")
        with cols[3]:
            metric_card("最大回撤", f"{m.get('max_drawdown', 0):.2%}", "<b>最大回撤</b><br>最惨败仗的亏损幅度。")

        # --- 战报导出按钮 ---
        if st.button("📜 导出精美研报 (HTML)", use_container_width=True):
            html_report = main.generate_strategy_report(df, m, input_code, st.session_state.last_code)
            # 生成下载链接
            b64_report = base64.b64encode(html_report.encode()).decode()
            href = f'<a href="data:text/html;base64,{b64_report}" download="{input_code}_研报.html" style="text-decoration:none; color:white; background:#d32f2f; padding:10px 20px; border-radius:8px; display:block; text-align:center;">👉 点击下载战报 (右键可打印PDF)</a>'
            st.markdown(href, unsafe_allow_html=True)

        st.markdown("### 🗺️ 沙盘推演")
        p = st.session_state.indicator_params
        selected_indicators = st.multiselect("侦察情报", ["MACD", "RSI", "KDJ", "BIAS"], key="selected_indics_state")
        candles = df[['time', 'open', 'high', 'low', 'close']].to_dict('records')
        line_series = []
        ma_configs = [('ma_1', p['ma1'], '#fff'), ('ma_2', p['ma2'], '#ff0'), ('ma_3', p['ma3'], '#f0f'),
                      ('ma_4', p['ma4'], '#0f0')]
        for col, period, color in ma_configs:
            if col in df.columns: line_series.append(
                {"data": clean_data(df, col), "options": {"color": color, "lineWidth": 1, "title": f"MA{period}"}})
        markers = []
        if 'signal' in df.columns:
            df['signal_val'] = pd.to_numeric(df['signal'], errors='coerce').fillna(0)
            df['action'] = df['signal_val'].diff()
            if len(df) > 0 and df.iloc[0]['signal_val'] == 1: df.at[0, 'action'] = 1
            for _, row in df[df['action'] == 1].iterrows(): markers.append(
                {"time": row['time'], "position": "belowBar", "color": "#FFD700", "shape": "arrowUp", "text": "BUY"})
            for _, row in df[df['action'] == -1].iterrows(): markers.append(
                {"time": row['time'], "position": "aboveBar", "color": "#00CED1", "shape": "arrowDown", "text": "SELL"})
        markers.sort(key=lambda x: x['time'])
        charts = []
        k_chart = {"chart": {"height": 450,
                             "layout": {"textColor": '#d1d4dc', "background": {"type": 'solid', "color": '#131722'}},
                             "grid": {"vertLines": {"color": "rgba(42, 46, 57, 0.2)"},
                                      "horzLines": {"color": "rgba(42, 46, 57, 0.2)"}},
                             "rightPriceScale": {"visible": True}, "timeScale": {"rightOffset": 5}}, "series": [
            {"type": 'Candlestick', "data": candles,
             "options": {"upColor": '#fd1050', "downColor": '#00f000', "borderUpColor": '#fd1050',
                         "borderDownColor": '#00f000', "wickUpColor": '#fd1050', "wickDownColor": '#00f000'},
             "markers": markers}]}
        for ls in line_series: k_chart["series"].append({"type": 'Line', "data": ls['data'], "options": ls['options']})
        charts.append(k_chart)

        # --- 🛡️ 核心修复：提前计算 vol_color，防止 KeyError ---
        df['vol_color'] = np.where(df['close'] >= df['open'], 'rgba(253, 16, 80, 0.5)', 'rgba(0, 240, 0, 0.5)')

        charts.append({"chart": {"height": 100, "layout": {"textColor": '#d1d4dc',
                                                           "background": {"type": 'solid', "color": '#131722'}},
                                 "grid": {"vertLines": {"color": "rgba(42, 46, 57, 0.2)"},
                                          "horzLines": {"color": "rgba(42, 46, 57, 0.2)"}},
                                 "rightPriceScale": {"visible": True}}, "series": [{"type": 'Histogram', "data": df[
            ['time', 'vol', 'vol_color']].rename(columns={'vol': 'value', 'vol_color': 'color'}).to_dict('records'),
                                                                                    "options": {"priceFormat": {
                                                                                        "type": 'volume'},
                                                                                                "title": "VOL"}}]})
        common_opts = {"height": 150,
                       "layout": {"textColor": '#d1d4dc', "background": {"type": 'solid', "color": '#131722'}},
                       "grid": {"vertLines": {"color": "rgba(42, 46, 57, 0.2)"},
                                "horzLines": {"color": "rgba(42, 46, 57, 0.2)"}}}
        if "MACD" in selected_indicators and 'macd_hist' in df.columns:
            df['macd_color'] = np.where(df['macd_hist'] >= 0, '#fd1050', '#00f000')
            charts.append({"chart": common_opts, "series": [{"type": 'Histogram',
                                                             "data": df[['time', 'macd_hist', 'macd_color']].rename(
                                                                 columns={'macd_hist': 'value',
                                                                          'macd_color': 'color'}).to_dict('records'),
                                                             "options": {"title": f"MACD"}},
                                                            {"type": 'Line', "data": clean_data(df, 'macd_dif'),
                                                             "options": {"color": "#fff", "lineWidth": 1}},
                                                            {"type": 'Line', "data": clean_data(df, 'macd_dea'),
                                                             "options": {"color": "#ff0", "lineWidth": 1}}]})
        if "RSI" in selected_indicators and 'rsi' in df.columns: charts.append({"chart": common_opts, "series": [
            {"type": 'Line', "data": clean_data(df, 'rsi'), "options": {"color": "#ffa726", "title": f"RSI"}}]})
        if "KDJ" in selected_indicators and 'k' in df.columns: charts.append({"chart": common_opts, "series": [
            {"type": 'Line', "data": clean_data(df, 'k'), "options": {"color": "#fff", "title": f"K"}},
            {"type": 'Line', "data": clean_data(df, 'd'), "options": {"color": "#ff0", "title": f"D"}},
            {"type": 'Line', "data": clean_data(df, 'j'), "options": {"color": "#f0f", "title": "J"}}]})
        if "BIAS" in selected_indicators and 'bias1' in df.columns: charts.append({"chart": common_opts, "series": [
            {"type": 'Line', "data": clean_data(df, 'bias1'),
             "options": {"color": "#fff", "title": f"BIAS{p['bias1']}"}},
            {"type": 'Line', "data": clean_data(df, 'bias2'),
             "options": {"color": "#ff0", "title": f"BIAS{p['bias2']}"}},
            {"type": 'Line', "data": clean_data(df, 'bias3'),
             "options": {"color": "#f0f", "title": f"BIAS{p['bias3']}"}}]})
        try:
            renderLightweightCharts(charts, "dashboard_view")
        except:
            st.error("渲染异常")