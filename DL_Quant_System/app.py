import os
import sys
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
from openai import OpenAI
import re
import time
import tushare as ts
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import uuid
import math
from PIL import Image
from backtester.engine import simple_backtest
from data_loader import fetch_stock_data, format_ts_code as normalize_ts_code
from secure_config import get_secret
from strategy_sandbox import execute_strategy, prepare_strategy_source
from ai_prompts import build_system_prompt, build_retry_user_message

# 🔥 安全导入扩展先锋营 🔥
try:
    import extensions
except ImportError:
    extensions = None

try:
    import custom_plugins
except ImportError:
    custom_plugins = None

# ==========================================
# 0. 环境优雅降级
# ==========================================
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import docx
except ImportError:
    docx = None

pd.np = np
SUB_PATTERN = re.compile(r'^SUB(\d+)_')
MODEL_OPTIONS = {
    "kimi-k3 (最新旗舰 · 默认)": "kimi-k3",
    "kimi-k2.6": "kimi-k2.6",
    "moonshot-v1-8k": "moonshot-v1-8k",
    "moonshot-v1-32k": "moonshot-v1-32k",
    "moonshot-v1-128k": "moonshot-v1-128k",
}
DEFAULT_BACKTEST_STRATEGY = """
def generate_signals(df):
    df = df.copy()
    df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()
    df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()
    df['Signal'] = 0
    df.loc[df['MAIN_MA5'] > df['MAIN_MA20'], 'Signal'] = 1
    df.loc[df['MAIN_MA5'] < df['MAIN_MA20'], 'Signal'] = -1
    return df
""".strip()

# ==========================================
# 1. 核心兵符与状态初始化
# ==========================================
st.set_page_config(
    page_title="小吕布量化 Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

KIMI_API_KEY = get_secret("KIMI_API_KEY", "MOONSHOT_API_KEY")
TUSHARE_TOKEN = get_secret("TUSHARE_TOKEN")
if TUSHARE_TOKEN:
    try:
        ts.set_token(TUSHARE_TOKEN)
    except Exception:
        pass


@st.cache_resource
def get_ts_pro():
    return ts.pro_api(TUSHARE_TOKEN) if TUSHARE_TOKEN else None


pro = get_ts_pro()
client = OpenAI(api_key=KIMI_API_KEY, base_url="https://api.moonshot.cn/v1", timeout=300.0) if KIMI_API_KEY else None

for key, val in {"user_id": f"User_{str(uuid.uuid4())[:6]}", "messages": [], "generated_code": "",
                 "strategy_explanation": "暂无策略解析，请先前往 AI 战情室下达军令。", "dl_result": None,
                 "bt_result": None, "sys_logs": [], "is_live_trading": False}.items():
    if key not in st.session_state: st.session_state[key] = val

# ==========================================
# 2. 空间流形导航逻辑
# ==========================================
PAGES = ["🏠 系统总览 (监控中控)", "🤖 AI 策略引擎 (LLM)", "💻 极客量化 IDE (代码编译)", "📈 深度静态全量回测",
         "⚡ 实时高频交易 (Live)", "🧠 深度学习预测矩阵", "🛡️ 论文审计日志", "🔗 期货全量审计 (归因)", "🌪️ 期货高频沙盘",
         "🔍 选股神器 (全市场扫描)", "🧩 扩展插件中心"]
if custom_plugins and hasattr(custom_plugins, 'EXTRA_PAGES'): PAGES.extend(custom_plugins.EXTRA_PAGES)

if st.session_state.get("curr_page") not in PAGES:
    st.session_state.curr_page = PAGES[0]
if st.session_state.get("prev_page") not in PAGES:
    st.session_state.prev_page = st.session_state.curr_page
if "just_switched" not in st.session_state: st.session_state.just_switched = False

with st.sidebar:
    st.markdown("### 🎓 小吕布量化 Pro")
    st.caption(f"🛡️ 节点 ID: {st.session_state.user_id}")
    st.markdown("---")
    theme_options = {"自动": "auto", "浅色": "light", "深色": "dark"}
    current_theme = st.session_state.get("visual_theme", "auto")
    current_label = next((label for label, value in theme_options.items() if value == current_theme), "自动")
    theme_label = st.radio(
        "外观",
        list(theme_options.keys()),
        index=list(theme_options.keys()).index(current_label),
        horizontal=True,
    )
    st.session_state.visual_theme = theme_options[theme_label]
    st.markdown("---")
    selected_page = st.radio(
        "导航菜单",
        PAGES,
        index=PAGES.index(st.session_state.curr_page),
        label_visibility="collapsed",
    )

    if extensions:
        st.markdown("---")
        enable_pet = st.toggle(
            "开启 3D 桌宠",
            value=False,
            key="enable_3d_pet",
            help="默认关闭以加快 Streamlit Cloud 首屏加载。",
        )
        if enable_pet:
            pet_names = list(getattr(extensions, "PET_ROSTER", {}).keys())
            active_pet = st.selectbox("桌宠角色", pet_names, label_visibility="collapsed") if pet_names else None
            extensions.summon_global_3d_lulu(active_pet)

if selected_page != st.session_state.curr_page:
    st.session_state.prev_page = st.session_state.curr_page
    st.session_state.curr_page = selected_page
    st.session_state.just_switched = True
else:
    st.session_state.just_switched = False

if st.session_state.curr_page not in PAGES:
    st.session_state.curr_page = PAGES[0]
if st.session_state.prev_page not in PAGES:
    st.session_state.prev_page = st.session_state.curr_page

# ==========================================
# 3. 永生级 JS 探针：持续监听主题变化，且绝不消亡
# ==========================================
theme_mode = st.session_state.get("visual_theme", "auto")
pet_enabled_js = "true" if st.session_state.get("enable_3d_pet", False) else "false"
components.html("""
<script>
(() => {
    const win = window.parent;
    const doc = win.document;
    const desiredTheme = "__THEME_MODE__";
    const petEnabled = __PET_ENABLED__;
    win.__LULU_THEME_MODE = desiredTheme;

    const resolveTheme = () => {
        const mode = win.__LULU_THEME_MODE || desiredTheme;
        if (mode === "light" || mode === "dark") return mode;
        return win.matchMedia && win.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    };

    const applyTheme = () => {
        const app = doc.querySelector(".stApp");
        if (!app) return;
        const theme = resolveTheme();
        app.setAttribute("data-custom-theme", theme);
        doc.documentElement.setAttribute("data-custom-theme", theme);
    };
    win.__LULU_APPLY_THEME = applyTheme;

    const removeLegacyPet = () => {
        if (petEnabled) return;
        ["lulu-global-pet", "lulu-ctx-menu"].forEach((id) => {
            const el = doc.getElementById(id);
            if (el) el.remove();
        });
        delete win.__PETS_JSON_DATA__;
    };

    const attachFileButton = () => {
        const chatInputOuter = doc.querySelector('div[data-testid="stChatInput"]');
        const fileInput = doc.querySelector('div[data-testid="stFileUploader"] input[type="file"]');
        if (!chatInputOuter || !fileInput || doc.getElementById("fake-attach-btn")) return;

        const innerPill = chatInputOuter.querySelector(".stChatInputContainer") || chatInputOuter.firstElementChild;
        if (!innerPill) return;

        innerPill.style.setProperty("position", "relative", "important");
        const fakeBtn = doc.createElement("button");
        fakeBtn.id = "fake-attach-btn";
        fakeBtn.type = "button";
        fakeBtn.setAttribute("aria-label", "上传附件");
        fakeBtn.innerHTML = "＋";
        fakeBtn.style.cssText = "position:absolute!important;left:14px!important;top:50%!important;transform:translateY(-50%)!important;z-index:20!important;width:28px!important;height:28px!important;border:0!important;border-radius:999px!important;background:rgba(120,120,128,.16)!important;color:var(--text-color,#111)!important;font-size:20px!important;line-height:26px!important;cursor:pointer!important;";
        fakeBtn.onclick = () => fileInput.click();
        innerPill.appendChild(fakeBtn);

        const textAreaWrap = innerPill.querySelector('[data-baseweb="textarea"]');
        if (textAreaWrap) textAreaWrap.style.setProperty("padding-left", "42px", "important");
    };

    applyTheme();
    removeLegacyPet();
    let tries = 0;
    const settle = () => {
        attachFileButton();
        if (++tries < 10) win.setTimeout(settle, 250);
    };
    settle();

    if (!win.__LULU_THEME_MEDIA_BOUND && win.matchMedia) {
        win.__LULU_THEME_MEDIA_BOUND = true;
        win.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
            if (typeof win.__LULU_APPLY_THEME === "function") win.__LULU_APPLY_THEME();
        });
    }
})();
</script>
""".replace("__THEME_MODE__", theme_mode).replace("__PET_ENABLED__", pet_enabled_js), height=0, width=0)

# ==========================================
# 4. 极致静态 CSS (双主题分离，修复毛玻璃缺失 BUG)
# ==========================================
if selected_page == PAGES[1]:
    st.markdown(
        '<style>div[data-testid="stFileUploader"] { position: absolute !important; top: -9999px !important; opacity: 0 !important; z-index: -9999 !important; pointer-events: none !important; }</style>',
        unsafe_allow_html=True)

st.markdown(f"""
<style>
    .block-container {{ animation: none !important; background: transparent !important; padding-top: 2.2rem !important; padding-bottom: 5.5rem !important; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* ================= 公共基础属性（结构与动画，永不丢失） ================= */
    @keyframes fluidFlow { 0% { background-position: 0% 50%; } 25% { background-position: 50% 100%; } 50% { background-position: 100% 50%; } 75% { background-position: 50% 0%; } 100% { background-position: 0% 50%; } }
    @keyframes waveBlurUpIn { 0% { opacity: 0; margin-top: 60px; filter: blur(15px); transform: scale(0.98); } 100% { opacity: 1; margin-top: 0px; filter: blur(0px); transform: scale(1); } }
    @keyframes waveBlurDownIn { 0% { opacity: 0; margin-top: -60px; filter: blur(15px); transform: scale(0.98); } 100% { opacity: 1; margin-top: 0px; filter: blur(0px); transform: scale(1); } }
    @keyframes fogFadeIn { 0% { opacity: 0; filter: blur(15px); transform: scale(0.98); } 100% { opacity: 1; filter: blur(0px); transform: scale(1); } }

    /* 🔥 绝对刺杀幽灵高度！防止桌宠 iframe 挤占主内容区顶部 */
    iframe[title="streamlit.components.v1.html"] { height: 0px !important; width: 0px !important; border: none !important; margin: 0 !important; padding: 0 !important; }

    header[data-testid="stHeader"], [data-testid="stAppViewContainer"] > section:first-child, [data-testid="stBottomBlock"], [data-testid="stBottom"] > div { background: transparent !important; border: none !important; }
    textarea { font-family: 'Consolas', 'Courier New', monospace !important; }
    [data-testid="stChatInput"] { background: transparent !important; border: none !important; box-shadow: none !important; max-width: 850px; margin: 0 auto 10px auto !important; }
    [data-testid="stChatInput"] [data-baseweb="textarea"] { background-color: transparent !important; }

    /* 🔥 核心修复：把毛玻璃的骨架抽离为公共类！ */
    .glass-card {
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .metric-box {
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    div[role="radiogroup"] > label { border-radius: 12px !important; margin-bottom: 10px !important; transition: all 0.3s ease;}
    [data-testid="stChatInput"] > div:first-child { border-radius: 36px !important; padding: 5px 15px !important; transition: all 0.3s ease; display: flex !important; align-items: center !important;}
    [data-testid="stExpander"] { border-radius: 16px !important; backdrop-filter: blur(10px); margin-bottom: 20px !important; transition: all 0.3s ease;}

    .agent-status-node { padding: 8px 12px; border-radius: 8px; font-size: 0.9rem; margin: 5px 0; border-left: 4px solid transparent; display: flex; align-items: center; gap: 10px; background: rgba(128,128,128,0.1); }
    .agent-status-node.success { border-left-color: #10b981; }
    .agent-status-node.error { border-left-color: #ef4444; }
    .agent-status-node.retry { border-left-color: #f59e0b; }

    /* ================= 🌙 深色主题 (Dark 专属上色) ================= */
    .stApp[data-custom-theme='dark'], .stApp[data-custom-theme='dark'] [data-testid="stAppViewContainer"] {
        background-color: #02040a !important;
        background-image: linear-gradient(132deg, #02040a, #030e2b, #111d3d, #082a72, #030614, #1d2b4f, #0a47b3, #02040a) !important;
        background-size: 100% 100% !important; animation: none !important;
    }
    .stApp[data-custom-theme='dark'] .stMarkdown, .stApp[data-custom-theme='dark'] p, .stApp[data-custom-theme='dark'] h1, .stApp[data-custom-theme='dark'] h2, .stApp[data-custom-theme='dark'] h3, .stApp[data-custom-theme='dark'] h4, .stApp[data-custom-theme='dark'] label, .stApp[data-custom-theme='dark'] [data-testid="stMetricValue"] > div { color: #e2e8f0 !important; }
    .stApp[data-custom-theme='dark'] .highlight-text { color: #00ffcc !important; }
    .stApp[data-custom-theme='dark'] .sub-text { color: #cbd5e1 !important; }
    .stApp[data-custom-theme='dark'] .danger-text { color: #ff4b4b !important; }

    .stApp[data-custom-theme='dark'] [data-testid="stSidebar"] { background: rgba(5, 8, 14, 0.85) !important; border-right: 1px solid rgba(255,255,255,0.08) !important; }
    .stApp[data-custom-theme='dark'] .glass-card { background: rgba(20, 28, 45, 0.75) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6) !important; }
    .stApp[data-custom-theme='dark'] .metric-box { background: rgba(0, 255, 204, 0.05) !important; border: 1px solid rgba(0, 255, 204, 0.2) !important; }
    .stApp[data-custom-theme='dark'] .metric-box p { color: #cbd5e1 !important; }
    .stApp[data-custom-theme='dark'] .metric-box h2 { color: #e2e8f0 !important; }

    .stApp[data-custom-theme='dark'] div[role="radiogroup"] > label { background: rgba(15, 20, 30, 0.4) !important; border-left: 4px solid transparent !important; }
    .stApp[data-custom-theme='dark'] div[role="radiogroup"] > label:has(input:checked) { background: linear-gradient(90deg, rgba(0, 255, 204, 0.3), rgba(10, 15, 25, 0.95)) !important; border-left: 4px solid #00ffcc !important; }
    .stApp[data-custom-theme='dark'] [data-testid="stChatInput"] > div:first-child { background-color: rgba(30, 41, 59, 0.85) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5) !important; }
    .stApp[data-custom-theme='dark'] [data-testid="stChatInput"] textarea { color: #e2e8f0 !important; }
    .stApp[data-custom-theme='dark'] [data-testid="stExpander"] { background: rgba(15, 23, 35, 0.8) !important; border: 1px solid rgba(0, 255, 204, 0.3) !important; }


    /* ================= ☀️ 浅色主题 (Light 专属上色) ================= */
    .stApp[data-custom-theme='light'], .stApp[data-custom-theme='light'] [data-testid="stAppViewContainer"] {
        background-color: #fdfbfb !important;
        background-image: linear-gradient(132deg, #fdfbfb, #e0c3fc, #8ec5fc, #e2ebf0, #fdfbfb) !important;
        background-size: 100% 100% !important; animation: none !important;
    }
    .stApp[data-custom-theme='light'] .stMarkdown, .stApp[data-custom-theme='light'] p, .stApp[data-custom-theme='light'] h1, .stApp[data-custom-theme='light'] h2, .stApp[data-custom-theme='light'] h3, .stApp[data-custom-theme='light'] h4, .stApp[data-custom-theme='light'] label, .stApp[data-custom-theme='light'] [data-testid="stMetricValue"] > div { color: #1e293b !important; }
    .stApp[data-custom-theme='light'] .highlight-text { color: #0284c7 !important; }
    .stApp[data-custom-theme='light'] .sub-text { color: #475569 !important; }
    .stApp[data-custom-theme='light'] .danger-text { color: #dc2626 !important; }

    .stApp[data-custom-theme='light'] [data-testid="stSidebar"] { background: rgba(248, 250, 252, 0.85) !important; border-right: 1px solid rgba(0,0,0,0.08) !important; }
    .stApp[data-custom-theme='light'] .glass-card { background: rgba(255, 255, 255, 0.6) !important; border: 1px solid rgba(0, 0, 0, 0.1) !important; box-shadow: 0 12px 48px rgba(0, 0, 0, 0.05) !important; }
    .stApp[data-custom-theme='light'] .metric-box { background: rgba(2, 132, 199, 0.05) !important; border: 1px solid rgba(2, 132, 199, 0.2) !important; }
    .stApp[data-custom-theme='light'] .metric-box p { color: #475569 !important; }
    .stApp[data-custom-theme='light'] .metric-box h2 { color: #1e293b !important; }

    .stApp[data-custom-theme='light'] div[role="radiogroup"] > label { background: rgba(241, 245, 249, 0.6) !important; border-left: 4px solid transparent !important; }
    .stApp[data-custom-theme='light'] div[role="radiogroup"] > label:has(input:checked) { background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), rgba(255, 255, 255, 0.95)) !important; border-left: 4px solid #3b82f6 !important; }
    .stApp[data-custom-theme='light'] [data-testid="stChatInput"] > div:first-child { background-color: rgba(255, 255, 255, 0.9) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1) !important; }
    .stApp[data-custom-theme='light'] [data-testid="stChatInput"] textarea { color: #1e293b !important; }
    .stApp[data-custom-theme='light'] [data-testid="stExpander"] { background: rgba(255, 255, 255, 0.7) !important; border: 1px solid rgba(0, 0, 0, 0.15) !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* iOS 26 Liquid Glass override: lighter paint, fewer continuous animations. */
    @keyframes iosContentIn {
        from { opacity: 0; transform: translateY(10px) scale(0.996); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }

    .stApp[data-custom-theme='light'] {
        --text-color: #1d1d1f;
        --ios-muted: #6e6e73;
        --ios-surface: rgba(255, 255, 255, 0.66);
        --ios-surface-strong: rgba(255, 255, 255, 0.86);
        --ios-surface-soft: rgba(255, 255, 255, 0.42);
        --ios-border: rgba(60, 60, 67, 0.18);
        --ios-border-strong: rgba(60, 60, 67, 0.28);
        --ios-accent: #0a84ff;
        --ios-danger: #ff3b30;
        --ios-shadow: 0 18px 55px rgba(0, 0, 0, 0.10);
        --ios-shadow-soft: 0 8px 26px rgba(0, 0, 0, 0.08);
        background:
            radial-gradient(circle at 16% -10%, rgba(10, 132, 255, 0.16), transparent 28%),
            radial-gradient(circle at 92% 10%, rgba(52, 199, 89, 0.10), transparent 24%),
            linear-gradient(180deg, #fbfbfd 0%, #f2f3f7 48%, #e9ebf0 100%) !important;
        animation: none !important;
    }

    .stApp[data-custom-theme='dark'] {
        --text-color: #f5f5f7;
        --ios-muted: #a1a1a6;
        --ios-surface: rgba(28, 28, 30, 0.70);
        --ios-surface-strong: rgba(44, 44, 46, 0.86);
        --ios-surface-soft: rgba(255, 255, 255, 0.08);
        --ios-border: rgba(255, 255, 255, 0.16);
        --ios-border-strong: rgba(255, 255, 255, 0.24);
        --ios-accent: #0a84ff;
        --ios-danger: #ff453a;
        --ios-shadow: 0 22px 65px rgba(0, 0, 0, 0.42);
        --ios-shadow-soft: 0 10px 30px rgba(0, 0, 0, 0.34);
        background:
            radial-gradient(circle at 16% -10%, rgba(10, 132, 255, 0.18), transparent 28%),
            radial-gradient(circle at 90% 8%, rgba(48, 209, 88, 0.08), transparent 24%),
            linear-gradient(180deg, #050506 0%, #111113 54%, #000000 100%) !important;
        animation: none !important;
    }

    .stApp[data-custom-theme] [data-testid="stAppViewContainer"] {
        background: transparent !important;
        animation: none !important;
    }

    .block-container {
        max-width: 1240px !important;
        padding-top: 2.2rem !important;
        padding-bottom: 5.5rem !important;
        animation: iosContentIn 0.28s ease-out both !important;
    }

    .stApp[data-custom-theme] [data-testid="stSidebar"] {
        background: var(--ios-surface) !important;
        border-right: 1px solid var(--ios-border) !important;
        box-shadow: var(--ios-shadow-soft) !important;
        backdrop-filter: blur(26px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(26px) saturate(180%) !important;
    }

    .stApp[data-custom-theme] .glass-card,
    .stApp[data-custom-theme] .metric-box,
    .stApp[data-custom-theme] [data-testid="stExpander"] {
        background: var(--ios-surface) !important;
        border: 1px solid var(--ios-border) !important;
        box-shadow: var(--ios-shadow) !important;
        backdrop-filter: blur(24px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(24px) saturate(180%) !important;
    }

    .glass-card {
        border-radius: 26px !important;
        padding: 22px 24px !important;
    }

    .metric-box {
        border-radius: 22px !important;
        padding: 16px !important;
    }

    .stApp[data-custom-theme] h1,
    .stApp[data-custom-theme] h2,
    .stApp[data-custom-theme] h3,
    .stApp[data-custom-theme] h4,
    .stApp[data-custom-theme] p,
    .stApp[data-custom-theme] label,
    .stApp[data-custom-theme] .stMarkdown {
        color: var(--text-color) !important;
        letter-spacing: 0 !important;
    }

    .stApp[data-custom-theme] .sub-text,
    .stApp[data-custom-theme] .metric-box p,
    .stApp[data-custom-theme] small,
    .stApp[data-custom-theme] [data-testid="stCaptionContainer"] {
        color: var(--ios-muted) !important;
    }

    .stApp[data-custom-theme] .highlight-text,
    .stApp[data-custom-theme] .metric-box h2 {
        color: var(--ios-accent) !important;
    }

    .stApp[data-custom-theme] .danger-text {
        color: var(--ios-danger) !important;
    }

    .stApp[data-custom-theme] div[role="radiogroup"] > label {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-left: 1px solid transparent !important;
        border-radius: 18px !important;
        margin-bottom: 8px !important;
        padding: 8px 10px !important;
    }

    .stApp[data-custom-theme] div[role="radiogroup"] > label:has(input:checked) {
        background: var(--ios-surface-strong) !important;
        border: 1px solid var(--ios-border-strong) !important;
        box-shadow: var(--ios-shadow-soft) !important;
    }

    .stApp[data-custom-theme] input,
    .stApp[data-custom-theme] textarea,
    .stApp[data-custom-theme] [data-baseweb="select"] > div,
    .stApp[data-custom-theme] [data-baseweb="input"] > div,
    .stApp[data-custom-theme] [data-testid="stChatInput"] > div:first-child {
        background: var(--ios-surface-strong) !important;
        border: 1px solid var(--ios-border) !important;
        border-radius: 18px !important;
        color: var(--text-color) !important;
        box-shadow: none !important;
    }

    .stApp[data-custom-theme] [data-testid="stChatInput"] > div:first-child {
        border-radius: 999px !important;
        box-shadow: var(--ios-shadow-soft) !important;
    }

    .stApp[data-custom-theme] button[kind="primary"],
    .stApp[data-custom-theme] .stButton > button {
        border-radius: 999px !important;
        border: 1px solid var(--ios-border) !important;
        background: var(--ios-surface-strong) !important;
        color: var(--text-color) !important;
        box-shadow: var(--ios-shadow-soft) !important;
        transition: transform 0.16s ease, background 0.16s ease, box-shadow 0.16s ease !important;
    }

    .stApp[data-custom-theme] button[kind="primary"],
    .stApp[data-custom-theme] .stButton > button[kind="primary"] {
        background: var(--ios-accent) !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.22) !important;
    }

    .stApp[data-custom-theme] .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 32px rgba(10, 132, 255, 0.22) !important;
    }

    .stApp[data-custom-theme] [data-testid="stDataFrame"],
    .stApp[data-custom-theme] [data-testid="stTable"] {
        border-radius: 20px !important;
        overflow: hidden !important;
        border: 1px solid var(--ios-border) !important;
        box-shadow: var(--ios-shadow-soft) !important;
    }

    @media (max-width: 760px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1.2rem !important;
        }
        .glass-card {
            border-radius: 22px !important;
            padding: 18px !important;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .block-container,
        .stApp[data-custom-theme] * {
            animation: none !important;
            transition: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* Final performance and visual override. This intentionally wins over older theme CSS. */
    .stApp[data-custom-theme='light'],
    .stApp:not([data-custom-theme]),
    .stApp[data-custom-theme='light'] [data-testid="stAppViewContainer"] {
        background: #f5f5f7 !important;
        background-image:
            radial-gradient(circle at 18% 0%, rgba(10, 132, 255, 0.10), transparent 28%),
            radial-gradient(circle at 88% 8%, rgba(175, 82, 222, 0.08), transparent 24%) !important;
    }

    .stApp[data-custom-theme='dark'],
    .stApp[data-custom-theme='dark'] [data-testid="stAppViewContainer"] {
        background: #000000 !important;
        background-image:
            radial-gradient(circle at 20% 0%, rgba(10, 132, 255, 0.18), transparent 30%),
            radial-gradient(circle at 86% 6%, rgba(94, 92, 230, 0.12), transparent 25%) !important;
    }

    @media (prefers-color-scheme: dark) {
        .stApp:not([data-custom-theme]),
        .stApp:not([data-custom-theme]) [data-testid="stAppViewContainer"] {
            background: #000000 !important;
            background-image:
                radial-gradient(circle at 20% 0%, rgba(10, 132, 255, 0.18), transparent 30%),
                radial-gradient(circle at 86% 6%, rgba(94, 92, 230, 0.12), transparent 25%) !important;
        }
    }

    .stApp[data-custom-theme] *,
    .stApp[data-custom-theme] *::before,
    .stApp[data-custom-theme] *::after {
        animation: none !important;
        scroll-behavior: auto !important;
    }

    .stApp[data-custom-theme] .glass-card,
    .stApp[data-custom-theme] .metric-box,
    .stApp[data-custom-theme] [data-testid="stExpander"] {
        backdrop-filter: blur(14px) saturate(150%) !important;
        -webkit-backdrop-filter: blur(14px) saturate(150%) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.10) !important;
    }

    .stApp[data-custom-theme='dark'] .glass-card,
    .stApp[data-custom-theme='dark'] .metric-box,
    .stApp[data-custom-theme='dark'] [data-testid="stExpander"] {
        box-shadow: 0 12px 34px rgba(0, 0, 0, 0.36) !important;
    }

    .stApp[data-custom-theme] [data-testid="stSidebar"] {
        backdrop-filter: blur(16px) saturate(150%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(150%) !important;
    }

    .block-container {
        opacity: 1 !important;
        transform: none !important;
        animation: none !important;
        padding-top: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 5. 高速缓存装甲：分离复杂计算
# ==========================================
def add_default_indicators(df):
    if 'Close' in df.columns:
        df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()
        df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['SUB1_MACD_DIFF'] = exp1 - exp2
        df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()
        df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])
    return df


@st.cache_data(ttl=300, show_spinner=False)
def get_tushare_status():
    if pro is None:
        return "Local CSV mode"
    return "🟢 Token ready"


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_and_clean_data(ts_code, adj, start_date):
    df, _source = fetch_stock_data(
        ts_code,
        adj=adj,
        start_date=start_date,
        tushare_token=TUSHARE_TOKEN,
        tushare_module=ts,
    )
    if df is not None and not df.empty:
        return add_default_indicators(df)
    return pd.DataFrame()


def _hash_market_frame(df):
    if df is None or df.empty:
        return ("empty",)
    close_col = "Close" if "Close" in df.columns else ("close" if "close" in df.columns else None)
    date_col = "trade_date" if "trade_date" in df.columns else None
    first_date = str(df[date_col].iloc[0]) if date_col else ""
    last_date = str(df[date_col].iloc[-1]) if date_col else ""
    first_close = float(df[close_col].iloc[0]) if close_col else 0.0
    last_close = float(df[close_col].iloc[-1]) if close_col else 0.0
    return (len(df), tuple(map(str, df.columns)), first_date, last_date, round(first_close, 6), round(last_close, 6))


@st.cache_data(show_spinner=False, hash_funcs={pd.DataFrame: _hash_market_frame})
def run_backtest_metrics(df_source, strategy_code):
    if df_source is None or df_source.empty:
        return {"df": pd.DataFrame(), "metrics": {"total": 0, "annual": 0, "max_dd": 0, "sharpe": 0, "trades": 0}}
    df_safe = df_source.copy()
    strategy_status = "default"
    strategy_error = ""
    code_to_run = strategy_code.strip() if isinstance(strategy_code, str) else ""
    if not code_to_run:
        code_to_run = DEFAULT_BACKTEST_STRATEGY
    else:
        strategy_status = "custom"

    try:
        df_ai = execute_safely(code_to_run, df_source)
    except Exception as exc:
        strategy_status = "fallback"
        strategy_error = str(exc)
        df_ai = execute_safely(DEFAULT_BACKTEST_STRATEGY, df_source)

    if df_ai is not None and hasattr(df_ai, 'columns'):
        for col in df_ai.columns:
            if col == 'Signal' or col.startswith(('MAIN_', 'SUB')): df_safe[col] = df_ai[col]
    signals = df_safe["Signal"] if "Signal" in df_safe.columns else pd.Series([0] * len(df_safe), index=df_safe.index)
    df, raw_metrics = simple_backtest(
        df_safe,
        signals=signals,
        commission=0.0003,
        slippage=0.0005,
        allow_short=False,
    )
    metrics = {
        "total": raw_metrics.get("total_return", 0),
        "annual": raw_metrics.get("annual_return", 0),
        "max_dd": raw_metrics.get("max_drawdown", 0),
        "sharpe": raw_metrics.get("sharpe", 0),
        "trades": raw_metrics.get("trades", 0),
        "win_rate": raw_metrics.get("win_rate", 0),
    }
    return {"df": df, "metrics": metrics, "strategy_status": strategy_status, "strategy_error": strategy_error}


def execute_safely(code, df):
    if not code: return df
    return execute_strategy(prepare_strategy_source(code), df)


def render_smart_charts(df):
    if df is None or df.empty:
        fig = go.Figure()
        fig.update_layout(
            height=420,
            template="none",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text="No market data", showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")],
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig
    if "trade_date" not in df.columns:
        df = df.copy()
        df["trade_date"] = pd.RangeIndex(len(df))
    else:
        df = df.copy()
        df["trade_date"] = pd.to_datetime(df["trade_date"], errors="coerce")
        if df["trade_date"].isna().all():
            df["trade_date"] = pd.RangeIndex(len(df))
    required_price_cols = {"Open", "High", "Low", "Close"}
    if not required_price_cols.issubset(df.columns):
        fig = go.Figure()
        fig.update_layout(
            height=420,
            template="none",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text="Missing OHLC columns", showarrow=False, x=0.5, y=0.5, xref="paper", yref="paper")],
            margin=dict(l=10, r=10, t=10, b=10),
        )
        return fig
    main_inds = [c for c in df.columns if c.startswith('MAIN_')]
    sub_groups = {}
    for c in df.columns:
        gid = SUB_PATTERN.match(c)
        if gid: sub_groups.setdefault(gid.group(1), []).append(c)
    rows = 2 + len(sub_groups)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.5, 0.15] + [0.35 / max(1, len(sub_groups))] * len(sub_groups))
    is_time_axis = pd.api.types.is_datetime64_any_dtype(df['trade_date'])
    if is_time_axis:
        time_fmt = '%Y-%m-%d' if df['trade_date'].dt.time.nunique() <= 1 else '%m-%d %H:%M'
        x_labels = df['trade_date'].dt.strftime(time_fmt)
    else:
        time_fmt = None
        x_labels = df['trade_date'].astype(str)
    fig.add_trace(go.Candlestick(x=x_labels, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 increasing_line_color='#ef4444', decreasing_line_color='#10b981', name='K线'), row=1,
                  col=1)
    colors = ['#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899']
    for i, col in enumerate(main_inds): fig.add_trace(
        go.Scatter(x=x_labels, y=df[col], name=col, line=dict(width=1.2, color=colors[i % 4])), row=1, col=1)
    if 'Signal' in df.columns:
        buys = df[df['Signal'] == 1]
        sells = df[df['Signal'] == -1]
        buy_x = buys['trade_date'].dt.strftime(time_fmt) if is_time_axis else buys['trade_date'].astype(str)
        sell_x = sells['trade_date'].dt.strftime(time_fmt) if is_time_axis else sells['trade_date'].astype(str)
        fig.add_trace(go.Scatter(x=buy_x, y=buys['Low'] * 0.998, mode='markers',
                                 marker=dict(symbol='triangle-up', size=14, color='#3b82f6'), name='买'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sell_x, y=sells['High'] * 1.002, mode='markers',
                                 marker=dict(symbol='triangle-down', size=14, color='#f59e0b'), name='卖'), row=1,
                      col=1)
    fig.add_trace(go.Bar(x=x_labels, y=df.get('Volume', np.zeros(len(df))),
                         marker_color=np.where(df['Close'] >= df['Open'], '#ef4444', '#10b981'), name='成交量'), row=2,
                  col=1)
    row_idx = 3
    for gid in sorted(sub_groups.keys(), key=int):
        for i, col in enumerate(sub_groups[gid]):
            if 'HIST' in col.upper():
                fig.add_trace(
                    go.Bar(x=x_labels, y=df[col], marker_color=np.where(df[col] >= 0, '#ef4444', '#10b981'), name=col),
                    row=row_idx, col=1)
            else:
                fig.add_trace(go.Scatter(x=x_labels, y=df[col], line=dict(width=1.2, color=colors[i % 4]), name=col),
                              row=row_idx, col=1)
        row_idx += 1
    fig.update_layout(height=500 + len(sub_groups) * 150, template="none", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False, dragmode='pan', hovermode='x',
                      showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=x_labels, nticks=8, showgrid=True,
                     gridwidth=1, gridcolor='rgba(128,128,128,0.2)', tickangle=0)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    return fig


def format_ts_code(raw):
    return normalize_ts_code(raw)


# ==========================================
# 6. 各页面业务逻辑
# ==========================================
if selected_page == PAGES[0]:
    st.markdown(
        '<div class="glass-card"><h1 style="margin-bottom:0; color:var(--text-color);">🏛️ 全链路智能量化决策枢纽</h1><p class="highlight-text" style="font-size:1.1rem; margin-top:5px;">System Overview & Mid-term Inspection Dashboard</p></div>',
        unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("活跃并发沙盒 (UUID)", st.session_state.user_id)
    with c2:
        st.metric("Tushare 行情链路", get_tushare_status())
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
            '<div class="glass-card"><h4 style="color:var(--text-color);">📋 平台监控与杀手锏</h4>**云端依赖环境**<br>🟢 requirements.txt 托管<br><br>**核心架构升级：**<br>✨ <b>完美修复毛玻璃丢失及主题切换失败 Bug！</b><br>✅ 前端引擎防抖极速化<br>✅ <b>代码沙盒防 NoneType 拦截器</b><br>✅ 粉碎 iframe 幽灵占位防溢出</div>',
            unsafe_allow_html=True
        )

elif selected_page == PAGES[1]:
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0; color:var(--text-color);">🤖 LLM 策略战情室</h3><p class="sub-text">多模态视觉引擎与全域文档解析模块已就绪，体验沉浸式工作流。</p></div>',
        unsafe_allow_html=True)

    ctrl_col1, ctrl_col2 = st.columns([1, 1])
    with ctrl_col1:
        selected_model = MODEL_OPTIONS[st.selectbox("🧠 选择大模型算力通道", list(MODEL_OPTIONS.keys()), index=0)]
    with ctrl_col2:
        st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
        enable_deep_think = st.toggle("💡 强子注入：开启深度思考引擎 (CoT)", value=False)

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
                elif fname_lower.endswith(('.doc', '.docx')):
                    if docx:
                        try:
                            doc_obj = docx.Document(file)
                            text = "\n".join([para.text for para in doc_obj.paragraphs])
                            st.success(f"📘 Word {file.name} 解析成功")
                            file_context_text += f"【Word 核心片段 {file.name}】:\n{text[:5000]}\n"
                        except Exception as e:
                            st.error(f"Word 读取异常: {e}")

    if raw_prompt := st.chat_input("向小吕布量化架构师发送军令..."):
        full_prompt_for_ai = f"以下是您需要重点参考的附件原始数据：\n{file_context_text}\n\n我的指令：{raw_prompt}" if file_context_text else raw_prompt
        st.session_state.messages.append({"role": "user", "content": raw_prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(raw_prompt)
            with st.chat_message("assistant"):
                st.toast(f"🚀 连线底层算力集群: {selected_model}", icon="⚡")
                sys_p = build_system_prompt()
                messages_to_send = [{"role": "system", "content": sys_p}] + st.session_state.messages[:-1] + [
                    {"role": "user", "content": full_prompt_for_ai}]
                max_retries = 2;
                agent_logs = [];
                last_error = "";
                full_resp = "";
                msg_box = st.empty()
                for attempt in range(max_retries + 1):
                    if attempt > 0:
                        agent_logs.append(
                            f'<div class="agent-status-node retry">🔄 <b>尝试 {attempt}:</b> 沙盒拦截异常 (<code>{last_error}</code>) -> Agent 发起重构</div>')
                        safe_resp = full_resp if full_resp and full_resp.strip() else "(API 前一次流响应为空，因引发沙盒报错被退回)"
                        messages_to_send.extend([{"role": "assistant", "content": safe_resp}, {"role": "user",
                                                                                               "content": build_retry_user_message(last_error)}])
                    try:
                        if client is None:
                            raise RuntimeError("Missing KIMI_API_KEY or MOONSHOT_API_KEY")
                        valid_messages = [m for m in messages_to_send if m.get("content") and str(m["content"]).strip()]
                        # 🔧 kimi-k3 是推理模型，只允许 temperature=1（传其他值会 400），故对 K3 不传 temperature
                        create_kwargs = {"model": selected_model, "messages": valid_messages, "stream": True}
                        if selected_model != "kimi-k3":
                            create_kwargs["temperature"] = 0.3 if enable_deep_think else 0.7
                        stream = client.chat.completions.create(**create_kwargs)
                        full_resp = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content:
                                full_resp += chunk.choices[0].delta.content
                                msg_box.markdown(full_resp.replace("<think>", "🧠 深度思考中...\n\n").replace("</think>",
                                                                                                             "\n\n---\n") + "▌",
                                                 unsafe_allow_html=True)
                        msg_box.markdown(
                            full_resp.replace("<think>", "🧠 深度思考过程：\n").replace("</think>", "\n---\n"),
                            unsafe_allow_html=True)
                        code_match = re.search(r"`{3}python\s*(.*?)\s*`{3}", full_resp, re.DOTALL)
                        resp_clean = re.sub(r"<think>.*?</think>", "", full_resp, flags=re.DOTALL)
                        explanation = re.sub(r"`{3}python\s*.*?\s*`{3}", "", resp_clean,
                                             flags=re.DOTALL).strip().replace("【策略白话解析】", "").strip()
                        st.session_state.strategy_explanation = explanation if explanation else "该策略完全由硬核代码驱动，未返回额外人话分析。"
                        if not code_match: break
                        extracted_code = code_match.group(1).strip()
                        try:
                            dummy_df = pd.DataFrame(
                                {'trade_date': pd.date_range('20230101', periods=50), 'Open': np.random.rand(50) * 10,
                                 'High': np.random.rand(50) * 12, 'Low': np.random.rand(50) * 8,
                                 'Close': np.random.rand(50) * 10})
                            _ = execute_safely(extracted_code, add_default_indicators(dummy_df))
                            st.session_state.generated_code = extracted_code
                            agent_logs.append(
                                f'<div class="agent-status-node success">✅ <b>尝试 {attempt + 1}:</b> 代码通过沙盒预检 -> 策略已安全装载</div>')
                            st.markdown("".join(agent_logs), unsafe_allow_html=True)
                            break
                        except Exception as e:
                            last_error = str(e)
                            if attempt == max_retries:
                                agent_logs.append(
                                    f'<div class="agent-status-node error">❌ <b>最终结果:</b> 失败，最终报错: <code>{last_error}</code></div>')
                                st.markdown("".join(agent_logs), unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"链路断开: {e}")
                        full_resp += f"\n\n❌ [异常阻断: 通信失败或超载 - {e}]"
                        break
                if not full_resp or not full_resp.strip(): full_resp = "❌ 大模型网络中断或未返回任何数据，请重试。"
                if agent_logs: full_resp += "\n\n" + "".join(agent_logs)
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
        st.rerun()

elif selected_page == PAGES[2]:
    if extensions: extensions.render_ide_page()

elif selected_page == PAGES[3]:
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
                    df_raw = fetch_and_clean_data(ts_code, adj_p if adj_p != "None" else None, f"{start_year}0101")
                    st.session_state.bt_result = run_backtest_metrics(df_raw, st.session_state.generated_code)
                except Exception as e:
                    st.error(f"异常: {e}")
    with col_r:
        if st.session_state.bt_result:
            m = st.session_state.bt_result['metrics']
            df = st.session_state.bt_result['df']
            if st.session_state.bt_result.get("strategy_status") == "fallback":
                st.warning(
                    "当前保存的策略代码不符合 generate_signals(df) 沙盒规范，"
                    f"已自动改用内置双均线策略完成本次回测。原始错误：{st.session_state.bt_result.get('strategy_error', '')}"
                )
            elif st.session_state.bt_result.get("strategy_status") == "default":
                st.info("本次未检测到已保存 AI/IDE 策略，已使用内置双均线策略完成回测。")
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(
                f'<div class="metric-box"><p>累计收益</p><h2 style="color:#3b82f6;">{m["total"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c2.markdown(
                f'<div class="metric-box"><p>年化收益</p><h2 style="color:#3b82f6;">{m["annual"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c3.markdown(
                f'<div class="metric-box"><p>最大回撤</p><h2 style="color:#ef4444;">{m["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c4.markdown(
                f'<div class="metric-box"><p>夏普比率</p><h2 style="color:#3b82f6;">{m["sharpe"]:.2f}</h2></div>',
                unsafe_allow_html=True)
            st.markdown("<div style='clear: both; margin-bottom: 30px;'></div>", unsafe_allow_html=True)
            if st.session_state.generated_code and st.session_state.strategy_explanation != "暂无策略解析，请先前往 AI 战情室下达军令。":
                with st.expander("💡 展开：AI 策略白话解析", expanded=False): st.markdown(
                    st.session_state.strategy_explanation)
            st.plotly_chart(render_smart_charts(df), use_container_width=True, config={'scrollZoom': True})

elif selected_page == PAGES[4]:
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
            with st.expander("💡 当前军令：策略白话解析", expanded=False): st.markdown(
                st.session_state.strategy_explanation)
        met_ph = st.empty();
        cht_ph = st.empty()
        if st.session_state.is_live_trading:
            stream = fetch_and_clean_data(format_ts_code(live_code), 'qfq', '20230101').tail(120).reset_index(drop=True)
            for i in range(20, len(stream)):
                if not st.session_state.is_live_trading: break
                sub = stream.iloc[:i].copy()
                try:
                    if st.session_state.generated_code:
                        sub_ai = execute_safely(st.session_state.generated_code, sub)
                        if sub_ai is not None and hasattr(sub_ai, 'columns'):
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
                    st.error(f"高频熔断: {e}");
                    st.session_state.is_live_trading = False;
                    break
                time.sleep(freq)

elif selected_page == PAGES[5]:
    with st.spinner("唤醒深度学习底层张量引擎..."):
        try:
            import torch
            import torch.nn as nn
            from sklearn.preprocessing import MinMaxScaler
        except ImportError:
            st.error("🚨 需安装 torch 和 scikit-learn！")
            st.stop()
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧠 深度神经网络时序建模矩阵 (白盒透视版)</h3></div>',
        unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 2.5])
    with col_l:
        st_code = st.text_input("🎯 训练模型标的", value="000001")
        span_mapping_dl = {"近1年 (极速)": 1, "近3年 (标准)": 3, "近5年 (深度)": 5}
        span_choice_dl = st.selectbox("⏳ 训练集时间跨度", list(span_mapping_dl.keys()), index=1)
        start_year_dl = datetime.now().year - span_mapping_dl[span_choice_dl]
        st.markdown("---")
        run_mode = st.radio("⚙️ 引擎运行模式", ["🚀 在线动态训练", "📂 导入本地模型"], horizontal=True)
        if "在线动态" in run_mode:
            model_choices = st.multiselect("🧠 选择预测模型 (支持多选融合)", ["LSTM", "GRU", "1D-CNN"], default=["LSTM"])
            slen = st.slider("📏 滑窗长度", 5, 60, 20)
            eps = st.slider("🔄 Epoch 迭代", 10, 50, 30)
            uploaded_model = None;
            btn_text = "🚀 启动张量训练"
        else:
            model_choices = st.multiselect("🧠 指定本地模型架构", ["LSTM", "GRU", "1D-CNN"], default=["LSTM"],
                                           max_selections=1)
            slen = st.slider("📏 滑窗长度 (需与本地模型一致)", 5, 60, 20)
            uploaded_model = st.file_uploader("📥 上传 PyTorch 权重文件 (.pth / .pt)", type=['pth', 'pt'])
            eps = 0;
            btn_text = "⚡ 挂载模型并推演"

        if st.button(btn_text, type="primary", use_container_width=True):
            if "导入本地模型" in run_mode and not uploaded_model:
                st.error("主公，请先上传本地训练好的权重文件！")
            elif not model_choices:
                st.error("主公，请至少选择一种预测模型！")
            else:
                with st.spinner("神经网络前向传播中..."):
                    try:
                        df = fetch_and_clean_data(format_ts_code(st_code), 'qfq', f"{start_year_dl}0101")
                        if df is None or df.empty or "Close" not in df.columns:
                            raise ValueError("market data is empty; configure TUSHARE_TOKEN or keep a local CSV sample")
                        if len(df) <= slen + 5:
                            raise ValueError(f"not enough rows for sequence length {slen}; got {len(df)} rows")
                        prices = df['Close'].values.reshape(-1, 1)
                        split_idx = min(len(prices) - 1, max(slen + 1, int(len(prices) * 0.8)))
                        scaler = MinMaxScaler()
                        scaler.fit(prices[:split_idx])
                        scaled = scaler.transform(prices)
                        X, y = [], []
                        for i in range(slen, len(scaled)): X.append(scaled[i - slen:i, 0]); y.append(scaled[i, 0])
                        X_arr = np.array(X)
                        y_arr = np.array(y)
                        if len(X_arr) == 0:
                            raise ValueError("not enough rows to build model windows")
                        train_count = min(len(X_arr), max(1, split_idx - slen))
                        X_train_t = torch.tensor(X_arr[:train_count], dtype=torch.float32).unsqueeze(-1)
                        y_train_t = torch.tensor(y_arr[:train_count], dtype=torch.float32)
                        X_t = torch.tensor(X_arr, dtype=torch.float32).unsqueeze(-1)
                        y_t = torch.tensor(y_arr, dtype=torch.float32)


                        class LSTM_Model(nn.Module):
                            def __init__(self):
                                super().__init__();
                                self.lstm = nn.LSTM(1, 64, 2, batch_first=True);
                                self.fc = nn.Linear(64, 1)

                            def forward(self, x): out, _ = self.lstm(x); return self.fc(out[:, -1, :])


                        class GRU_Model(nn.Module):
                            def __init__(self):
                                super().__init__();
                                self.gru = nn.GRU(1, 64, 2, batch_first=True);
                                self.fc = nn.Linear(64, 1)

                            def forward(self, x): out, _ = self.gru(x); return self.fc(out[:, -1, :])


                        class CNN_1D_Model(nn.Module):
                            def __init__(self, seq_len):
                                super().__init__();
                                self.conv = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3, padding=1);
                                self.fc = nn.Linear(32 * seq_len, 1)

                            def forward(self, x): x = x.permute(0, 2, 1); x = torch.relu(self.conv(x)); x = x.reshape(
                                x.size(0), -1); return self.fc(x)


                        preds_dict, future_preds_dict = {}, {}
                        lbox = st.empty();
                        pbar = st.progress(0);
                        last_window_orig = X_t[-1].clone().unsqueeze(0)

                        for m_idx, m_name in enumerate(model_choices):
                            if m_name == "LSTM":
                                model = LSTM_Model()
                            elif m_name == "GRU":
                                model = GRU_Model()
                            elif m_name == "1D-CNN":
                                model = CNN_1D_Model(slen)

                            if "导入本地模型" in run_mode:
                                lbox.markdown(f"**正在解析并挂载本地 {m_name} 模型权重...**")
                                try:
                                    model.load_state_dict(torch.load(uploaded_model, map_location=torch.device('cpu'), weights_only=True))
                                    lbox.success(f"**{m_name}** | 权重校验通过，挂载成功！");
                                    pbar.progress(1.0)
                                except Exception as load_e:
                                    st.warning(f"⚠️ 模型架构不匹配，极速重训练... ({load_e})")
                                    opt = torch.optim.Adam(model.parameters(), lr=0.01);
                                    crit = nn.MSELoss()
                                    for e in range(10): model.train(); opt.zero_grad(); loss = crit(
                                        model(X_train_t).squeeze(), y_train_t); loss.backward(); opt.step()
                            else:
                                lbox.markdown(f"**正在在线训练 {m_name} 模型...**")
                                opt = torch.optim.Adam(model.parameters(), lr=0.01);
                                crit = nn.MSELoss()
                                for e in range(eps):
                                    model.train();
                                    opt.zero_grad();
                                    pred = model(X_train_t);
                                    loss = crit(pred.squeeze(), y_train_t);
                                    loss.backward();
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

                        lbox.success("✅ 矩阵模型装载完毕，时空推演已就绪！")
                        st.session_state.dl_result = {"dates": df['trade_date'].iloc[-100:],
                                                      "actual": df['Close'].iloc[-100:], "preds": preds_dict,
                                                      "future": future_preds_dict, "models_used": model_choices}
                    except Exception as e:
                        st.error(f"DL 张量异常: {e}")

    with col_r:
        if st.session_state.dl_result:
            res = st.session_state.dl_result
            latest_price = res['actual'].iloc[-1];
            actual_vals = res['actual'].values
            if len(res['models_used']) > 1:
                f_preds = np.mean(list(res['future'].values()), axis=0);
                h_preds = np.mean(list(res['preds'].values()), axis=0)
                model_desc = f"LSTM/GRU/CNN 均值集成 ({len(res['models_used'])}模型)"
            else:
                f_preds = list(res['future'].values())[0];
                h_preds = list(res['preds'].values())[0]
                model_desc = res['models_used'][0]

            act_diff = np.diff(actual_vals);
            pred_diff = np.diff(h_preds)
            success_rate = np.mean(np.sign(act_diff) == np.sign(pred_diff)) * 100
            mape = np.mean(np.abs((actual_vals - h_preds) / (actual_vals + 1e-8))) * 100
            day1_pred = f_preds[0];
            day5_pred = f_preds[4]

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
                    prompt = f"你是一个顶级的量化分析师，为小白解盘。当前收盘价 {latest_price:.2f}元。基于【{model_desc}】推演，未来1天预测价为 {day1_pred:.2f}元，未来5天为 {day5_pred:.2f}元。模型胜率为 {success_rate:.1f}%，偏差为 {mape:.2f}%。请用大白话（限200字以内，不要代码），向小白解释并给出建议。"
                    try:
                        if client is None:
                            raise RuntimeError("Missing KIMI_API_KEY or MOONSHOT_API_KEY")
                        stream = client.chat.completions.create(model="kimi-k3",
                                                                messages=[{"role": "user", "content": prompt}],
                                                                stream=True)
                        full_txt = ""
                        for chunk in stream:
                            if chunk.choices[0].delta.content: full_txt += chunk.choices[0].delta.content; ai_ph.info(
                                full_txt + "▌")
                        ai_ph.info(full_txt)
                    except Exception as e:
                        ai_ph.error(f"Kimi 连线中断: {e}")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['dates'], y=res['actual'], name='真实轨迹 (Actual)',
                                     line=dict(color='#10b981', width=2)))
            color_map = {"LSTM": "#3b82f6", "GRU": "#f59e0b", "1D-CNN": "#8b5cf6"}
            for m_name, pred_array in res['preds'].items(): fig.add_trace(
                go.Scatter(x=res['dates'], y=pred_array, name=f'{m_name} 历史拟合',
                           line=dict(color=color_map.get(m_name, '#94a3b8'), dash='dot', width=1.5)))
            if len(res['preds']) > 1: fig.add_trace(
                go.Scatter(x=res['dates'], y=np.mean(list(res['preds'].values()), axis=0), name='🔥 均值集成 (Ensemble)',
                           line=dict(color='#ef4444', width=3)))
            fig.update_layout(height=450, template="none", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              dragmode='pan', hovermode='x',
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)');
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
            st.plotly_chart(fig, use_container_width=True)

elif selected_page == PAGES[6]:
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

elif selected_page == PAGES[7]:
    if extensions: extensions.render_futures_backtest()

elif selected_page == PAGES[8]:
    if extensions: extensions.render_futures_sandbox()

elif selected_page == PAGES[9]:
    from screener import get_stock_universe, run_screen, MARKET_LABELS

    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🔍 选股神器 (全市场扫描)</h3>'
        '<p class="sub-text">用当前策略代码的买点条件扫描整个市场 —— 哪只股票今天出现买点，就把它捞出来。策略代码不用改，直接复用 AI/IDE 里那份。</p></div>',
        unsafe_allow_html=True)

    # 1. 策略来源
    src_choice = st.radio(
        "🧬 策略来源",
        ["全局已保存策略 (AI/IDE)", "🏔️ 主升浪模型", "💡 经典双均线"],
        horizontal=True,
    )
    if src_choice == "🏔️ 主升浪模型":
        zsl = getattr(extensions, "ZHU_SHENG_LANG_CODE", "") if extensions else ""
        active_code = zsl or st.session_state.generated_code or DEFAULT_BACKTEST_STRATEGY
    elif src_choice == "💡 经典双均线":
        active_code = DEFAULT_BACKTEST_STRATEGY
    else:
        active_code = st.session_state.generated_code

    with st.expander("🧬 查看/修改当前策略代码（扫描即用它找买点）", expanded=False):
        active_code = st.text_area(
            "策略代码", value=active_code if active_code else DEFAULT_BACKTEST_STRATEGY,
            height=280, label_visibility="collapsed")

    if not active_code or not active_code.strip():
        st.warning("还没有策略代码。请先到 AI 战情室生成策略、或在 IDE 里载入模板，再回来扫描。")
    else:
        col_l, col_r = st.columns([1, 2.4])
        with col_l:
            universe_label = st.selectbox("🌐 扫描范围", list(MARKET_LABELS.values()), index=0)
            market_key = {v: k for k, v in MARKET_LABELS.items()}[universe_label]
            lookback_label = st.selectbox("⏱️ 买点新鲜度", ["仅最新一天", "近 3 日内", "近 5 日内"], index=1)
            lookback_days = {"仅最新一天": 1, "近 3 日内": 3, "近 5 日内": 5}[lookback_label]
            span_years = {"近1年": 1, "近2年": 2, "近3年": 3}[
                st.selectbox("📅 数据深度", ["近1年", "近2年", "近3年"], index=1)]
            workers = st.slider("⚙️ 并发线程", 1, 6, 3,
                                help="全市场扫描建议 3~4；网络慢或触发限流时降到 1~2。")
            do_scan = st.button("🚀 开始全市场扫描", type="primary", use_container_width=True)
            st.caption("⚠️ 全市场约 5400 只，耗时可能 20 分钟以上；建议先用本地样例/板块测试。")

        with col_r:
            if do_scan:
                codes, names = get_stock_universe(TUSHARE_TOKEN, ts, market_key)
                if not codes:
                    st.error("没有可扫描的标的：TUSHARE_TOKEN 未配置或接口异常。请改用「本地样例」。")
                else:
                    prog = st.progress(0.0)
                    status_line = st.empty()
                    start_date = f"{datetime.now().year - span_years}0101"

                    def _cb(done, total, code):
                        prog.progress(done / max(1, total))
                        status_line.caption(f"🔭 扫描中 {done}/{total} … 刚完成: {code}")

                    with st.spinner(f"正在扫描 {len(codes)} 只标的..."):
                        results, stats = run_screen(
                            active_code, codes, start_date, lookback_days,
                            TUSHARE_TOKEN, ts, max_workers=workers, progress_cb=_cb)
                    st.session_state.screen_results = results
                    st.session_state.screen_stats = stats
                    st.session_state.screen_names = names

            if st.session_state.get("screen_results") is not None:
                res = st.session_state.screen_results
                stats = st.session_state.screen_stats
                st.success(
                    f"✅ 扫描完成：共 {stats['total']} 只 | 命中买点 {len(res)} 只 | "
                    f"无数据 {stats['no_data']} | 接口失败 {stats['failed']} | 策略报错 {stats['strategy_errors']}")
                if not res:
                    st.info("本次没有股票满足策略买点条件。可放宽「买点新鲜度」或换数据深度再试。")
                else:
                    names = st.session_state.screen_names
                    table = pd.DataFrame([{
                        "代码": r["code"],
                        "名称": names.get(r["code"], ""),
                        "买点日期": r["buy_date"],
                        "最新收盘": round(r["close"], 2),
                        "近5日涨跌%": round(r.get("pct5") or 0, 2),
                        "数据行数": r.get("rows", 0),
                    } for r in res])
                    st.dataframe(table, use_container_width=True, hide_index=True)

                    picked = st.selectbox(
                        "📈 查看个股买点K线",
                        [f"{r['code']} {names.get(r['code'], '')}" for r in res])
                    if picked:
                        pick_code = picked.split()[0]
                        df_chart = fetch_and_clean_data(pick_code, 'qfq', f"{datetime.now().year - 2}0101")
                        if df_chart is not None and not df_chart.empty:
                            try:
                                df_ai = execute_safely(active_code, df_chart)
                                if df_ai is not None and hasattr(df_ai, 'columns'):
                                    for col in df_ai.columns:
                                        if col == 'Signal' or col.startswith(('MAIN_', 'SUB')):
                                            df_chart[col] = df_ai[col]
                            except Exception:
                                pass
                            st.plotly_chart(render_smart_charts(df_chart), use_container_width=True,
                                            config={'scrollZoom': True})
            elif not do_scan:
                st.markdown(
                    """<div class="metric-box" style="height: 300px; display: flex; flex-direction: column; justify-content: center; align-items: center;"><p>等待主公下达扫描指令</p><h2 style="color: #3b82f6;">点击 [开始全市场扫描]</h2><p class="sub-text" style="margin-top: 10px;">命中买点的股票会自动列出，支持查看K线与买点标记</p></div>""",
                    unsafe_allow_html=True)

elif selected_page == PAGES[10]:
    if extensions: extensions.render_new_features_page()

else:
    if custom_plugins and hasattr(custom_plugins, 'route_and_render'): custom_plugins.route_and_render(selected_page)
