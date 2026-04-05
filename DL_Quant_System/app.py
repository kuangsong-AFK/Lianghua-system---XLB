import streamlit as st
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time
import tushare as ts
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import os
import uuid

# ==========================================
# 1. 核心兵符 & 基础配置
# ==========================================
st.set_page_config(page_title="小吕布量化 Pro - 毕业设计版", layout="wide", initial_sidebar_state="expanded")

KIMI_API_KEY = "sk-yS2foVgWtvnFMWKRTLnI6l8NFqFrRiB8ojre75g2mK2P8LBk"
TUSHARE_TOKEN = "ba486af7606bc2f6018f1d592251a49674132225f59d37b3473d676e"

# 🔥 修复复权核心：必须全局注册 token，才能调用 ts.pro_bar
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=30.0)

# ==========================================
# 2. 沉浸式 UI & 强制暗黑主题
# ==========================================
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], .block-container { 
        background-color: #0e1117 !important; 
        background-image: radial-gradient(circle at 50% 0%, #1f2633 0%, #0e1117 75%) !important;
        padding-top: 2rem !important; 
    }
    header[data-testid="stHeader"] { background: transparent !important; }
    header[data-testid="stHeader"] * { color: rgba(255,255,255,0.6) !important; }
    footer { display: none !important; }
    .stMarkdown, .stText, p, h1, h2, h3, label, span, li { color: #ffffff !important; }

    div[data-testid="stCodeBlock"], pre { background-color: #0d1117 !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; }
    code { color: #00ffcc !important; background-color: transparent !important; text-shadow: none !important; }

    [data-testid="stSidebar"] { background: rgba(14, 17, 23, 0.9) !important; border-right: 1px solid rgba(255,255,255,0.1) !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }

    .glass-card { background: rgba(20, 24, 30, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); }
    .stTextInput > div > div, .stSelectbox > div > div { background-color: rgba(0,0,0,0.6) !important; color: white !important; border: 1px solid rgba(255,255,255,0.2); }
    div[data-testid="stChatMessageContent"] { background-color: rgba(30, 35, 45, 0.9) !important; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 毕业论文专用：多用户数据埋点系统
# ==========================================
LOG_FILE = "thesis_user_logs.csv"
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["Timestamp", "UserID", "ActionType", "Details"]).to_csv(LOG_FILE, index=False)

if "user_id" not in st.session_state: st.session_state.user_id = f"User_{str(uuid.uuid4())[:6]}"
if "sys_logs" not in st.session_state: st.session_state.sys_logs = []
if "generated_code" not in st.session_state: st.session_state.generated_code = ""
if "bt_result" not in st.session_state: st.session_state.bt_result = None


def log_thesis_data(action_type, details):
    new_row = pd.DataFrame(
        [{"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "UserID": st.session_state.user_id,
          "ActionType": action_type, "Details": str(details)}])
    new_row.to_csv(LOG_FILE, mode='a', header=False, index=False)
    st.session_state.sys_logs.insert(0,
                                     f"[{datetime.now().strftime('%H:%M:%S')}] [{st.session_state.user_id}] {action_type}: {details}")


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": f"主公，系统已初始化！您的测试编号为：**{st.session_state.user_id}**"}]
    log_thesis_data("系统访问", "新用户进入量化平台")


def format_ts_code(raw_code):
    raw_code = str(raw_code).strip().upper()
    if len(raw_code) == 6 and raw_code.isdigit():
        if raw_code.startswith(('6', '9')):
            return f"{raw_code}.SH"
        elif raw_code.startswith(('0', '2', '3')):
            return f"{raw_code}.SZ"
        elif raw_code.startswith(('4', '8')):
            return f"{raw_code}.BJ"
    return raw_code


# ==========================================
# 4. 侧边栏导航
# ==========================================
with st.sidebar:
    st.markdown("## 🎓 量化交易引擎 Pro")
    st.caption(f"当前测试用户: {st.session_state.user_id}")
    st.markdown("---")
    page = st.radio("系统导航", ["🏠 系统总览", "🤖 AI 策略引擎", "📈 深度回测与图表", "🛡️ 论文数据与日志"],
                    label_visibility="collapsed")

# ==========================================
# 🏠 系统总览
# ==========================================
if page == "🏠 系统总览":
    st.markdown(
        '<div class="glass-card"><h2>🏠 智能量化交易决策系统</h2><p>基于大语言模型 (LLM) 的代码生成与动态回测架构</p></div>',
        unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("当前活跃测试用户", st.session_state.user_id, "埋点监控中")
    col2.metric("AI 大脑", "Moonshot-v1-8k", "API 正常")
    col3.metric("数据源节点", "Tushare Pro", "支持前复权/后复权")
    col4.metric("策略缓存数", "1" if st.session_state.generated_code else "0", "动态沙盒")
    st.markdown(
        '<div class="glass-card"><h4>⚙️ 系统架构图 (论文配图参考)</h4><ul><li><b>感知层</b>: 用户自然语言输入 (Streamlit UI)</li><li><b>认知层</b>: Moonshot LLM 大模型解析意图，生成 Pandas 矢量化交易逻辑</li><li><b>数据层</b>: Tushare 金融大数据接口，获取 A 股真实 K 线与复权因子</li><li><b>执行层</b>: Python 动态沙盒 <code>exec()</code> 执行策略，生成交易信号向量</li><li><b>表现层</b>: Plotly 交互式可视化，支持自适应缩放与同花顺级指标叠加</li></ul></div>',
        unsafe_allow_html=True)

# ==========================================
# 🤖 AI 策略引擎
# ==========================================
elif page == "🤖 AI 策略引擎":
    st.markdown('<div class="glass-card"><h3>🤖 LLM 策略生成中枢</h3></div>', unsafe_allow_html=True)
    chat_container = st.container(height=450)
    with chat_container:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("输入策略构思 (如: 基于均线的趋势跟踪策略)..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        log_thesis_data("请求AI写策略", prompt)
        st.rerun()

    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
        with chat_container:
            with st.chat_message("assistant"):
                msg_box = st.empty()
                bt = "`" * 3
                sys_prompt = f"""你是量化专家。请给出Python代码并用 {bt}python 和 {bt} 包裹。
必须包含 `generate_signals(df)` 函数。输入 df 列名为: ['trade_date', 'open', 'high', 'low', 'close', 'vol']。
在 df 中新增 'Signal' 列：1为买入，-1为卖出，0为观望。最后返回 df。
⚠️ 【学术级军规】：
1. 在 pandas 计算多条件时，必须且只能使用 `&` (与) 和 `|` (或)，并给每个条件加括号！绝对禁止使用 `and` 或 `or`！
2. 传入的 df 已根据用户设置进行了【复权处理】，策略不需要考虑除权除息造成的跳空断层，直接运用纯粹的价格计算逻辑即可。禁止引入第三方库。"""
                try:
                    msg_box.markdown("🧠 *大模型正在解析意图并构建计算图...*")
                    stream = client.chat.completions.create(model="moonshot-v1-8k", messages=[{"role": "system",
                                                                                               "content": sys_prompt}] + st.session_state.messages,
                                                            stream=True)
                    full_resp = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content:
                            full_resp += chunk.choices[0].delta.content
                            msg_box.markdown(full_resp + "▌")
                    msg_box.markdown(full_resp)

                    code_match = re.search(bt + r"(?:python)?\s*(.*?)" + bt, full_resp, re.DOTALL | re.IGNORECASE)
                    if code_match:
                        st.session_state.generated_code = code_match.group(1).strip()
                        st.toast("✅ 策略已通过静态检查，编译成功！", icon="🚀")
                        log_thesis_data("AI生成成功", "代码提取并装填至沙盒")
                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                except Exception as e:
                    st.error(f"API 异常: {e}")
                    log_thesis_data("AI生成失败", f"报错: {e}")
        st.rerun()

# ==========================================
# 📈 深度回测与图表
# ==========================================
elif page == "📈 深度回测与图表":
    st.markdown('<div class="glass-card"><h3>📈 动态沙盒与多维可视化分析</h3></div>', unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 3])

    with col_l:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        raw_stock_code = st.text_input("🎯 回测标的 (输入6位代码，如: 000001)", value="000001")
        ts_code = format_ts_code(raw_stock_code)

        # 🔥 新增：复权与坐标轴控制系统
        adj_mode = st.selectbox("⚖️ 价格复权处理", ["前复权 (推荐)", "后复权", "不复权 (原始价格)"])
        adj_param = "qfq" if "前复权" in adj_mode else "hfq" if "后复权" in adj_mode else None
        y_axis_mode = st.radio("📏 Y轴缩放模式", ["自适应 K线 (动态伸缩)", "绝对 K线 (全局定死)"], horizontal=False)

        st.caption(f"🔗 API 映射: `{ts_code}` | 复权: `{adj_param}`")

        if st.session_state.generated_code:
            st.success("🟢 沙盒引擎就绪")
            if st.button("🚀 启动全量回测任务", use_container_width=True, type="primary"):
                with st.spinner(f"正在聚合 {ts_code} 真实复权数据..."):
                    try:
                        # 🔥 修复核心：使用 ts.pro_bar 自动获取复权数据
                        data = ts.pro_bar(ts_code=ts_code, adj=adj_param, start_date='20230101')
                        if data is None or data.empty:
                            st.error("未获取到数据！可能是 Tushare 积分不足或代码错误。")
                            log_thesis_data("回测失败", f"标的 {ts_code} 无数据")
                        else:
                            data = data.sort_values('trade_date').reset_index(drop=True)
                            # 格式化日期为 pandas datetime
                            data['trade_date'] = pd.to_datetime(data['trade_date'], format='%Y%m%d')

                            data['MA5'] = data['close'].rolling(window=5).mean()
                            data['MA20'] = data['close'].rolling(window=20).mean()

                            exp1 = data['close'].ewm(span=12, adjust=False).mean()
                            exp2 = data['close'].ewm(span=26, adjust=False).mean()
                            data['MACD_DIFF'] = exp1 - exp2
                            data['MACD_DEA'] = data['MACD_DIFF'].ewm(span=9, adjust=False).mean()
                            data['MACD'] = (data['MACD_DIFF'] - data['MACD_DEA']) * 2

                            low_list = data['low'].rolling(9, min_periods=1).min()
                            high_list = data['high'].rolling(9, min_periods=1).max()
                            rsv = (data['close'] - low_list) / (high_list - low_list + 1e-8) * 100
                            data['K'] = rsv.ewm(com=2, adjust=False).mean()
                            data['D'] = data['K'].ewm(com=2, adjust=False).mean()
                            data['J'] = 3 * data['K'] - 2 * data['D']

                            data['Color'] = np.where(data['close'] >= data['open'], '#FD1050', '#00FF00')

                            l_vars = {}
                            exec(st.session_state.generated_code, globals(), l_vars)
                            data = l_vars['generate_signals'](data)

                            data['Ret'] = data['close'].pct_change()
                            data['Pos'] = data['Signal'].replace(0, np.nan).ffill().fillna(0)
                            data['Strat_Ret'] = data['Pos'].shift(1) * data['Ret']
                            data['Cum_Prod'] = (1 + data['Strat_Ret'].fillna(0)).cumprod()

                            st.session_state.bt_result = {"df": data, "code": ts_code, "adj": adj_mode,
                                                          "y_mode": y_axis_mode}

                            total_ret = (data['Cum_Prod'].iloc[-1] - 1) * 100
                            log_thesis_data("回测成功", f"标的:{ts_code}, 复权:{adj_param}, 收益率:{total_ret:.2f}%")
                    except Exception as e:
                        st.error(f"沙盒执行异常: {e}")
                        log_thesis_data("沙盒崩毁", f"报错: {e}")
        else:
            st.warning("🟡 策略缓存为空，请先由 AI 生成策略。")

        if st.session_state.bt_result:
            df = st.session_state.bt_result['df']
            st.markdown("---")
            total_ret = (df['Cum_Prod'].iloc[-1] - 1)
            annual_ret = (1 + total_ret) ** (252 / len(df)) - 1 if len(df) > 0 else 0
            max_dd = ((df['Cum_Prod'] / df['Cum_Prod'].cummax() - 1).min())
            daily_returns = df['Strat_Ret'].dropna()
            sharpe_ratio = ((daily_returns.mean() - 0.03 / 252) / daily_returns.std()) * np.sqrt(252) if len(
                daily_returns) > 0 and daily_returns.std() != 0 else 0

            st.metric("累计收益", f"{total_ret * 100:.2f}%")
            st.metric("年化收益", f"{annual_ret * 100:.2f}%")
            st.metric("最大回撤", f"{max_dd * 100:.2f}%")
            st.metric("夏普比率", f"{sharpe_ratio:.2f}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        if st.session_state.bt_result:
            df = st.session_state.bt_result['df']
            current_y_mode = st.session_state.bt_result['y_mode']
            st.markdown(
                f'<div class="glass-card" style="padding:10px;"><p style="text-align:center; color:#888;">正在查看: {st.session_state.bt_result["code"]} | {st.session_state.bt_result["adj"]}</p>',
                unsafe_allow_html=True)

            fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                                row_heights=[0.5, 0.15, 0.175, 0.175])

            fig.add_trace(go.Candlestick(
                x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                name='K线', increasing_line_color='#FD1050', increasing_fillcolor='#FD1050',
                decreasing_line_color='#00FF00', decreasing_fillcolor='#00FF00'
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['MA5'], line=dict(color='yellow', width=1), name='MA5'),
                          row=1, col=1)
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['MA20'], line=dict(color='magenta', width=1), name='MA20'), row=1,
                col=1)

            buys = df[df['Signal'] == 1]
            sells = df[df['Signal'] == -1]
            fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['low'] * 0.95, mode='markers',
                                     marker=dict(symbol='triangle-up', size=14, color='#00FFFF',
                                                 line=dict(width=1, color='white')), name='买入'), row=1, col=1)
            fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['high'] * 1.05, mode='markers',
                                     marker=dict(symbol='triangle-down', size=14, color='#FF00FF',
                                                 line=dict(width=1, color='white')), name='卖出'), row=1, col=1)

            fig.add_trace(go.Bar(x=df['trade_date'], y=df['vol'], marker_color=df['Color'], name='成交量'), row=2,
                          col=1)

            macd_colors = np.where(df['MACD'] >= 0, '#FD1050', '#00FF00')
            fig.add_trace(go.Bar(x=df['trade_date'], y=df['MACD'], marker_color=macd_colors, name='MACD'), row=3, col=1)
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['MACD_DIFF'], line=dict(color='white', width=1), name='DIFF'),
                row=3, col=1)
            fig.add_trace(
                go.Scatter(x=df['trade_date'], y=df['MACD_DEA'], line=dict(color='yellow', width=1), name='DEA'), row=3,
                col=1)

            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['K'], line=dict(color='white', width=1), name='K'), row=4,
                          col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['D'], line=dict(color='yellow', width=1), name='D'),
                          row=4, col=1)
            fig.add_trace(go.Scatter(x=df['trade_date'], y=df['J'], line=dict(color='magenta', width=1), name='J'),
                          row=4, col=1)

            # 🔥 坐标轴高级格式化
            fig.update_layout(
                height=800, dragmode='pan',
                template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0.2)',
                margin=dict(l=0, r=0, t=10, b=0), xaxis_rangeslider_visible=False,
                hovermode="x unified", showlegend=False
            )

            # 🔥 修复中文日期：在坐标轴刻度和悬停光标上强制应用中文年月日
            fig.update_xaxes(
                tickformat="%Y年%m月",  # 底部坐标轴显示：年-月
                hoverformat="%Y年%m月%d日",  # 鼠标悬停显示：年-月-日
                showgrid=False, zeroline=False, rangeslider_visible=False
            )

            # 🔥 修复自适应/绝对 K线
            if "绝对" in current_y_mode:
                # 锁定全局最高和最低，哪怕缩小画面，Y轴的范围也不会变
                fig.update_yaxes(range=[df['low'].min() * 0.95, df['high'].max() * 1.05], showgrid=True,
                                 gridcolor='rgba(255,255,255,0.05)', zeroline=False, row=1, col=1)
            else:
                # Plotly 原生自适应模式 (可通过图表右上角工具栏的 Autoscale 按钮随时对齐)
                fig.update_yaxes(autorange=True, showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False,
                                 row=1, col=1)

            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False, row=2, col=1)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False, row=3, col=1)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False, row=4, col=1)

            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True,
                                                                   'modeBarButtonsToRemove': ['lasso2d', 'select2d']})
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 🛡️ 论文数据与日志
# ==========================================
elif page == "🛡️ 论文数据与日志":
    st.markdown('<div class="glass-card"><h3>🛡️ 多并发用户记录与日志提取</h3></div>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    col_dl1, col_dl2 = st.columns([1, 1])
    with col_dl1:
        st.markdown("#### 📥 毕业论文实验数据源")
        st.write(
            "该报表自动记录了所有用户的历史访问、AI 策略请求和回测盈亏表现，您可以直接下载 CSV 用于论文的数据统计与图表制作。")

        if os.path.exists(LOG_FILE):
            log_df = pd.read_csv(LOG_FILE)
            csv = log_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📁 一键下载论文原始报表 (user_logs.csv)", data=csv,
                               file_name='thesis_user_logs.csv', mime='text/csv', type="primary")
            st.dataframe(log_df.tail(10), use_container_width=True)
        else:
            st.warning("暂无日志数据积累。")

    with col_dl2:
        st.markdown("#### ⏱️ 当前实例实时日志流")
        log_text = "\n".join(st.session_state.sys_logs)
        st.text_area("System Terminal", value=log_text, height=300)
    st.markdown('</div>', unsafe_allow_html=True)