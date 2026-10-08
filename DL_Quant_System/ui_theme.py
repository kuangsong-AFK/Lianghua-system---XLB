# -*- coding: utf-8 -*-
"""UI 3.0 视觉主题层 —— 液态玻璃（Liquid Glass）

设计语言参考 GitHub 开源项目 rdev/liquid-glass-react（Apple Liquid Glass 效果）。
该项目用 WebGL 着色器实现边缘折射/色差/弹性变形；本模块用 CSS + JS 复刻同等视觉语言：

- 液态玻璃卡片：霜化磨砂（blur+saturate）、渐变"棱光"描边（双 background 技法）、
  顶部高光缘线、光标跟随折射光斑（JS 缓动）、悬停色差边缘、弹性回弹动画
- 液态背景：多层高饱和色团 + 旋转色轮层（@property 角度动画）+ 光斑色相漂移 + 星尘粒子
- 液态按钮：玻璃渐变填充 + 渐变描边 + 光扫 + 涟漪 + 弹性按压
- 深色/浅色双主题；所有脚本带幂等守卫
"""

import streamlit as st
import streamlit.components.v1 as components

V3_CSS = """
<style>
/* ================= UI 3.0 · 液态玻璃 Liquid Glass ================= */

/* ---------- 0. 主题变量 ---------- */
.stApp[data-custom-theme='dark'] {
    --v2-accent: #38bdf8;
    --v2-accent2: #a78bfa;
    --v2-glow: rgba(56, 189, 248, 0.5);
    --v2-text: #e2e8f0;
    --v2-muted: #94a3b8;
    --v2-input: rgba(30, 41, 59, 0.72);
    --v2-ripple: rgba(255, 255, 255, 0.35);
    /* 液态玻璃 */
    --lg-fill: rgba(13, 20, 38, 0.52);
    --lg-rim: linear-gradient(135deg, rgba(255, 255, 255, 0.55), rgba(255, 255, 255, 0.10) 32%,
        rgba(56, 189, 248, 0.38) 68%, rgba(167, 139, 250, 0.5) 100%);
    --lg-btn-fill: rgba(56, 189, 248, 0.10);
    --lg-sheen: rgba(255, 255, 255, 0.17);
}
.stApp[data-custom-theme='light'], .stApp:not([data-custom-theme]) {
    --v2-accent: #3b82f6;
    --v2-accent2: #8b5cf6;
    --v2-glow: rgba(59, 130, 246, 0.32);
    --v2-text: #1e293b;
    --v2-muted: #64748b;
    --v2-input: rgba(255, 255, 255, 0.88);
    --v2-ripple: rgba(59, 130, 246, 0.28);
    --lg-fill: rgba(255, 255, 255, 0.5);
    --lg-rim: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.22) 34%,
        rgba(59, 130, 246, 0.42) 70%, rgba(139, 92, 246, 0.42) 100%);
    --lg-btn-fill: rgba(59, 130, 246, 0.08);
    --lg-sheen: rgba(255, 255, 255, 0.55);
}

/* ---------- 1. 液态背景（色轮旋转 + 高饱和色团 + 极光漂移） ---------- */
@property --v2-spin {
    syntax: '<angle>';
    initial-value: 0deg;
    inherits: false;
}
.stApp[data-custom-theme='dark'],
.stApp[data-custom-theme='dark'] [data-testid="stAppViewContainer"] {
    background:
        conic-gradient(from var(--v2-spin, 0deg) at 50% 46%,
            rgba(56, 189, 248, 0.12), rgba(167, 139, 250, 0.12), rgba(236, 72, 153, 0.09),
            rgba(34, 211, 238, 0.12), rgba(56, 189, 248, 0.12)),
        radial-gradient(62% 48% at 12% 4%, rgba(56, 189, 248, 0.32), transparent 62%),
        radial-gradient(56% 46% at 88% 8%, rgba(167, 139, 250, 0.30), transparent 62%),
        radial-gradient(52% 44% at 82% 92%, rgba(34, 211, 238, 0.24), transparent 60%),
        radial-gradient(46% 40% at 16% 96%, rgba(244, 114, 182, 0.20), transparent 60%),
        linear-gradient(165deg, #04060d 0%, #0a1024 34%, #0c1330 64%, #060812 100%) !important;
    background-size: 100% 100% !important;
    background-attachment: fixed !important;
    animation: v3AuroraA 40s ease-in-out infinite alternate, v3Spin 70s linear infinite !important;
}
.stApp[data-custom-theme='light'],
.stApp[data-custom-theme='light'] [data-testid="stAppViewContainer"],
.stApp:not([data-custom-theme]),
.stApp:not([data-custom-theme]) [data-testid="stAppViewContainer"] {
    background:
        conic-gradient(from var(--v2-spin, 0deg) at 50% 46%,
            rgba(59, 130, 246, 0.10), rgba(139, 92, 246, 0.10), rgba(236, 72, 153, 0.07),
            rgba(14, 165, 233, 0.10), rgba(59, 130, 246, 0.10)),
        radial-gradient(60% 48% at 12% 4%, rgba(59, 130, 246, 0.24), transparent 62%),
        radial-gradient(56% 46% at 88% 8%, rgba(139, 92, 246, 0.22), transparent 62%),
        radial-gradient(52% 44% at 82% 92%, rgba(14, 165, 233, 0.18), transparent 60%),
        radial-gradient(46% 40% at 16% 96%, rgba(236, 72, 153, 0.14), transparent 60%),
        linear-gradient(160deg, #f6f8fd 0%, #eef2fb 38%, #f3effd 68%, #f7f9fe 100%) !important;
    background-size: 100% 100% !important;
    background-attachment: fixed !important;
    animation: v3AuroraA 44s ease-in-out infinite alternate, v3Spin 80s linear infinite !important;
}

/* 光斑：色相漂移 + 大范围游走 */
.stApp[data-custom-theme]::before,
.stApp[data-custom-theme]::after {
    content: "";
    position: fixed;
    z-index: 0;
    pointer-events: none;
    border-radius: 50%;
    mix-blend-mode: screen;
    will-change: transform, filter;
}
.stApp[data-custom-theme='dark']::before {
    width: 50vw; height: 50vw; top: -17vw; left: -13vw;
    background: radial-gradient(circle, rgba(56, 189, 248, 0.5) 0%, rgba(56, 189, 248, 0.14) 36%, transparent 70%);
    animation: v3BlobA 24s ease-in-out infinite alternate, v3Hue 15s linear infinite alternate;
}
.stApp[data-custom-theme='dark']::after {
    width: 46vw; height: 46vw; bottom: -19vw; right: -11vw;
    background: radial-gradient(circle, rgba(167, 139, 250, 0.46) 0%, rgba(167, 139, 250, 0.12) 36%, transparent 70%);
    animation: v3BlobB 30s ease-in-out infinite alternate, v3Hue 21s linear infinite alternate;
}
.stApp[data-custom-theme='light']::before {
    width: 48vw; height: 48vw; top: -15vw; left: -11vw;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.28) 0%, rgba(59, 130, 246, 0.08) 36%, transparent 70%);
    animation: v3BlobA 28s ease-in-out infinite alternate, v3Hue 18s linear infinite alternate;
}
.stApp[data-custom-theme='light']::after {
    width: 44vw; height: 44vw; bottom: -17vw; right: -9vw;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.24) 0%, rgba(139, 92, 246, 0.07) 36%, transparent 70%);
    animation: v3BlobB 34s ease-in-out infinite alternate, v3Hue 24s linear infinite alternate;
}

@keyframes v3AuroraA {
    0% { background-position: 50% 46%, 0% 0%, 100% 0%, 100% 100%, 0% 100%, 0 0; }
    50% { background-position: 50% 46%, 6% 8%, 92% 6%, 94% 92%, 8% 94%, 0 0; }
    100% { background-position: 50% 46%, 0% 14%, 88% 0%, 100% 88%, 2% 98%, 0 0; }
}
@keyframes v3Spin { to { --v2-spin: 360deg; } }
@keyframes v3BlobA {
    from { transform: translate(0, 0) scale(1); }
    to { transform: translate(14vw, 11vh) scale(1.2); }
}
@keyframes v3BlobB {
    from { transform: translate(0, 0) scale(1.12); }
    to { transform: translate(-12vw, -10vh) scale(0.94); }
}
@keyframes v3Hue {
    from { filter: blur(60px) hue-rotate(0deg); }
    to { filter: blur(60px) hue-rotate(70deg); }
}

/* ---------- 2. 液态玻璃卡片 ---------- */
.glass-card, .metric-box {
    position: relative;
    border-radius: 24px !important;
    border: 1px solid transparent !important;
    background:
        linear-gradient(var(--lg-fill), var(--lg-fill)) padding-box,
        var(--lg-rim) border-box !important;
    backdrop-filter: blur(14px) saturate(150%) !important;
    -webkit-backdrop-filter: blur(14px) saturate(150%) !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.24),
        inset 0 -1px 0 rgba(255, 255, 255, 0.05),
        0 20px 55px rgba(2, 6, 23, 0.26) !important;
    transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1),
        box-shadow 0.3s ease !important;
}
.glass-card:hover, .metric-box:hover {
    transform: translateY(-3px) scale(1.012);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.34),
        0 28px 70px rgba(2, 6, 23, 0.4),
        0 0 36px var(--v2-glow) !important;
}
.glass-card:active, .metric-box:active {
    transform: translateY(-1px) scale(0.985);
    transition-duration: 0.12s !important;
}

/* 棱光色差边缘（hover 时红/青微光，模拟折射色差） */
.glass-card::before, .metric-box::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    pointer-events: none;
    box-shadow:
        inset 1.5px 0 0 rgba(255, 96, 130, 0.16),
        inset -1.5px 0 0 rgba(96, 200, 255, 0.16);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.glass-card:hover::before, .metric-box:hover::before { opacity: 1; }

/* 光标折射光斑（--mx/--my 由 JS 缓动注入） */
.glass-card::after, .metric-box::after {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: radial-gradient(430px circle at var(--mx, 50%) var(--my, 50%),
        var(--lg-sheen), rgba(255, 255, 255, 0.03) 45%, transparent 66%);
    opacity: 0;
    transition: opacity 0.35s ease;
    pointer-events: none;
}
.glass-card:hover::after, .metric-box:hover::after { opacity: 1; }

/* 指标卡数值辉光 */
.stApp[data-custom-theme] .metric-box h2,
.stApp[data-custom-theme] .highlight-text {
    color: var(--v2-accent) !important;
    text-shadow: 0 0 22px var(--v2-glow);
}

/* 高频刷新区用纯色卡（无 backdrop-filter，避免每秒重建带动周边背景虚化闪烁） */
.glass-flat {
    background: var(--lg-fill) !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}

/* ---------- 3. 液态玻璃按钮（光扫 + 涟漪 + 弹性按压） ---------- */
.stButton > button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button,
.stApp[data-custom-theme] button[kind="secondary"] {
    position: relative;
    overflow: hidden;
    border-radius: 14px !important;
    border: 1px solid transparent !important;
    background:
        linear-gradient(var(--lg-btn-fill), var(--lg-btn-fill)) padding-box,
        linear-gradient(135deg, rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.08) 35%,
            color-mix(in srgb, var(--v2-accent) 45%, transparent)) border-box !important;
    /* 按钮不做背景采样（backdrop-filter 会在页面刷新时引发发虚/点击丢失） */
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    color: var(--v2-text) !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    box-shadow: 0 4px 14px rgba(2, 6, 23, 0.18) !important;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
        box-shadow 0.25s ease, filter 0.25s ease !important;
}
.stButton > button:hover, .stDownloadButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 12px 30px var(--v2-glow), 0 0 0 1px color-mix(in srgb, var(--v2-accent) 32%, transparent) !important;
    filter: brightness(1.07);
}
.stButton > button:active, .stDownloadButton button:active, [data-testid="stFormSubmitButton"] button:active,
.stApp[data-custom-theme] button[kind="primary"]:active {
    transform: translateY(1px) scale(0.94) !important;
    box-shadow: 0 2px 8px rgba(2, 6, 23, 0.28) !important;
    filter: brightness(0.9);
    transition-duration: 0.1s !important;
}
.stButton > button:focus-visible, .stDownloadButton button:focus-visible,
.stApp[data-custom-theme] button[kind="primary"]:focus-visible {
    outline: 2px solid var(--v2-accent) !important;
    outline-offset: 2px;
}
.stButton > button::after, .stDownloadButton button::after {
    content: "";
    position: absolute;
    top: 0; left: -160%;
    width: 55%; height: 100%;
    background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transform: skewX(-22deg);
    transition: left 0.55s ease;
    pointer-events: none;
}
.stButton > button:hover::after, .stDownloadButton button:hover::after { left: 170%; }

/* 主按钮 */
.stApp[data-custom-theme] button[kind="primary"],
.stApp[data-custom-theme] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--v2-accent), var(--v2-accent2)) !important;
    background-size: 160% 160% !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 6px 22px var(--v2-glow) !important;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.25s ease,
        background-position 0.5s ease, filter 0.25s ease !important;
}
.stApp[data-custom-theme] button[kind="primary"]:hover,
.stApp[data-custom-theme] .stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) scale(1.02);
    background-position: 100% 50% !important;
    box-shadow: 0 14px 36px var(--v2-glow), 0 0 0 1px color-mix(in srgb, var(--v2-accent) 40%, transparent) !important;
    filter: brightness(1.08);
}

/* ---------- 4. 侧边栏与导航 ---------- */
.stApp[data-custom-theme] [data-testid="stSidebar"] {
    background: var(--lg-fill) !important;
    border-right: 1px solid transparent !important;
    border-image: linear-gradient(180deg, rgba(255, 255, 255, 0.4), transparent 40%, transparent 60%, rgba(56, 189, 248, 0.3)) 1 !important;
    backdrop-filter: blur(16px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(160%) !important;
    box-shadow: 12px 0 44px rgba(2, 6, 23, 0.2) !important;
}
.stApp[data-custom-theme] div[role="radiogroup"] > label {
    border-radius: 14px !important;
    margin-bottom: 8px !important;
    padding: 9px 12px !important;
    border: 1px solid transparent !important;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.22s ease,
        box-shadow 0.22s ease !important;
    cursor: pointer;
}
.stApp[data-custom-theme] div[role="radiogroup"] > label:hover {
    transform: translateX(5px) scale(1.02);
    background: color-mix(in srgb, var(--v2-accent) 8%, transparent) !important;
}
.stApp[data-custom-theme] div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(90deg,
        color-mix(in srgb, var(--v2-accent) 22%, transparent),
        color-mix(in srgb, var(--v2-accent2) 8%, transparent)) !important;
    border-left: 3px solid var(--v2-accent) !important;
    box-shadow: 0 4px 18px var(--v2-glow) !important;
}

/* ---------- 5. 输入框 / 下拉 / 文本域 ---------- */
.stApp[data-custom-theme] input,
.stApp[data-custom-theme] textarea,
.stApp[data-custom-theme] [data-baseweb="select"] > div,
.stApp[data-custom-theme] [data-baseweb="input"] > div {
    background: var(--v2-input) !important;
    border: 1px solid color-mix(in srgb, var(--v2-accent) 22%, transparent) !important;
    border-radius: 14px !important;
    color: var(--v2-text) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}
.stApp[data-custom-theme] input:focus,
.stApp[data-custom-theme] textarea:focus,
.stApp[data-custom-theme] [data-baseweb="select"] > div:focus-within,
.stApp[data-custom-theme] [data-baseweb="input"] > div:focus-within {
    border-color: var(--v2-accent) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--v2-accent) 22%, transparent) !important;
}

/* ---------- 6. 对话输入 ---------- */
.stApp[data-custom-theme] [data-testid="stChatInput"] > div:first-child {
    border-radius: 999px !important;
    border: 1px solid color-mix(in srgb, var(--v2-accent) 25%, transparent) !important;
    background: var(--v2-input) !important;
    transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
}
.stApp[data-custom-theme] [data-testid="stChatInput"] > div:first-child:focus-within {
    border-color: var(--v2-accent) !important;
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--v2-accent) 20%, transparent),
        0 10px 32px var(--v2-glow) !important;
}

/* ---------- 7. 进度条流光 ---------- */
.stApp[data-custom-theme] [data-testid="stProgress"] > div > div > div {
    background: linear-gradient(90deg, var(--v2-accent), var(--v2-accent2), var(--v2-accent)) !important;
    background-size: 200% 100% !important;
    animation: v3Shimmer 2.2s linear infinite !important;
}
@keyframes v3Shimmer { 0% { background-position: 0% 0; } 100% { background-position: 200% 0; } }

/* ---------- 8. 数据表 ---------- */
.stApp[data-custom-theme] [data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid color-mix(in srgb, var(--v2-accent) 24%, transparent) !important;
    box-shadow: 0 10px 30px rgba(2, 6, 23, 0.14) !important;
}
.stApp[data-custom-theme] [data-testid="stDataFrame"] [role="columnheader"] {
    background: color-mix(in srgb, var(--v2-accent) 10%, transparent) !important;
    color: var(--v2-text) !important;
    font-weight: 600;
}

/* ---------- 9. 滚动条 ---------- */
.stApp[data-custom-theme] ::-webkit-scrollbar { width: 9px; height: 9px; }
.stApp[data-custom-theme] ::-webkit-scrollbar-track { background: transparent; }
.stApp[data-custom-theme] ::-webkit-scrollbar-thumb {
    background: color-mix(in srgb, var(--v2-accent) 35%, transparent);
    border-radius: 99px;
    border: 2px solid transparent;
    background-clip: padding-box;
}
.stApp[data-custom-theme] ::-webkit-scrollbar-thumb:hover {
    background: color-mix(in srgb, var(--v2-accent) 60%, transparent);
    background-clip: padding-box;
    border: 2px solid transparent;
}

/* ---------- 10. Toast / 提示 ---------- */
.stApp[data-custom-theme] [data-testid="stToast"] {
    border-radius: 14px !important;
    border: 1px solid color-mix(in srgb, var(--v2-accent) 30%, transparent) !important;
    border-left: 3px solid var(--v2-accent) !important;
    box-shadow: 0 12px 34px rgba(2, 6, 23, 0.4) !important;
}

/* ---------- 11. 标题与分隔线 ---------- */
.stApp[data-custom-theme='dark'] h1, .stApp[data-custom-theme='dark'] h2 {
    text-shadow: 0 0 26px rgba(56, 189, 248, 0.3);
}
.stApp[data-custom-theme] hr {
    border-color: color-mix(in srgb, var(--v2-accent) 22%, transparent) !important;
}

/* ---------- 12. 局部刷新反馈（整页不做入场动画，避免每次刷新全屏虚化） ---------- */
.block-container {
    animation: none !important;
    transform: none !important;
    opacity: 1 !important;
}
/* LIVE 呼吸灯：行情刷新状态指示 */
.live-dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 10px #10b981;
    margin-right: 6px;
    vertical-align: middle;
    animation: v3Pulse 1.6s ease-in-out infinite;
}
.live-dot.paused {
    background: #94a3b8;
    box-shadow: 0 0 6px rgba(148, 163, 184, 0.5);
    animation: none;
}
@keyframes v3Pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(0.7); }
}
/* 数据卡片内容更新的轻微闪烁（配合局部刷新） */
@keyframes v3FlashIn {
    from { filter: brightness(1.6); }
    to { filter: brightness(1); }
}

/* ---------- 13. 降低动态偏好 ---------- */
@media (prefers-reduced-motion: reduce) {
    .stApp[data-custom-theme], .stApp[data-custom-theme]::before, .stApp[data-custom-theme]::after,
    .block-container, [data-testid="stProgress"] > div > div > div {
        animation: none !important;
    }
    .glass-card, .metric-box, .stButton > button { transition: none !important; }
}
</style>
"""

V3_JS = """
<script>
(() => {
    const win = window.parent;
    if (!win || win.__V3_UI_BOOT__) return;
    win.__V3_UI_BOOT__ = true;
    const doc = win.document;
    const reduceMotion = win.matchMedia && win.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------- 1. 按钮涟漪 + 按压反馈 ---------- */
    const rippleKey = doc.createElement('style');
    rippleKey.textContent = '@keyframes v3ripple{to{transform:scale(1);opacity:0;}}';
    doc.head.appendChild(rippleKey);
    doc.addEventListener('pointerdown', (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;
        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height) * 2.2;
        const rip = doc.createElement('span');
        rip.style.cssText = 'position:absolute;border-radius:50%;pointer-events:none;z-index:0;'
            + 'width:' + size + 'px;height:' + size + 'px;'
            + 'left:' + (e.clientX - rect.left - size / 2) + 'px;'
            + 'top:' + (e.clientY - rect.top - size / 2) + 'px;'
            + 'background:radial-gradient(circle, rgba(255,255,255,0.42), transparent 65%);'
            + 'transform:scale(0);opacity:.9;animation:v3ripple .5s ease-out forwards;';
        if (!btn.style.position || btn.style.position === 'static') btn.style.position = 'relative';
        btn.appendChild(rip);
        setTimeout(() => { if (rip.parentNode) rip.parentNode.removeChild(rip); }, 560);
    }, { passive: true });

    /* ---------- 3. 液态玻璃：光标折射光斑（--mx/--my 缓动注入） ---------- */
    const CARD_SEL = '.glass-card, .metric-box';
    const glassState = new WeakMap();
    let glassList = [];
    const gatherGlass = () => {
        glassList = Array.prototype.slice.call(doc.querySelectorAll(CARD_SEL));
        for (const el of glassList) {
            if (!glassState.has(el)) glassState.set(el, { cx: 0, cy: 0, tx: 0, ty: 0 });
        }
    };
    gatherGlass();
    setInterval(gatherGlass, 2500);
    doc.addEventListener('mousemove', (e) => {
        for (const el of glassList) {
            const st = glassState.get(el);
            if (!st) continue;
            const r = el.getBoundingClientRect();
            if (!r.width || !r.height) continue;
            const px = e.clientX - r.left, py = e.clientY - r.top;
            if (px >= -30 && px <= r.width + 30 && py >= -30 && py <= r.height + 30) {
                st.tx = px; st.ty = py;
            }
        }
    }, { passive: true });
    (function glassLoop() {
        for (const el of glassList) {
            const st = glassState.get(el);
            if (!st) continue;
            st.cx += (st.tx - st.cx) * 0.14;
            st.cy += (st.ty - st.cy) * 0.14;
            el.style.setProperty('--mx', st.cx + 'px');
            el.style.setProperty('--my', st.cy + 'px');
        }
        requestAnimationFrame(glassLoop);
    })();

    /* ---------- 4. 星尘粒子画布 ---------- */
    if (!reduceMotion) {
        const cv = doc.createElement('canvas');
        cv.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;z-index:1;pointer-events:none;';
        doc.body.appendChild(cv);
        const ctx = cv.getContext('2d');
        let W = 0, H = 0;
        const dpr = Math.min(win.devicePixelRatio || 1, 1.5);
        const N = 42;
        let pts = [];
        const isDark = () => {
            const app = doc.querySelector('.stApp');
            return app && app.getAttribute('data-custom-theme') !== 'light';
        };
        const palette = () => isDark()
            ? [[56, 189, 248], [167, 139, 250], [34, 211, 238]]
            : [[59, 130, 246], [139, 92, 246], [14, 165, 233]];
        const resize = () => {
            W = win.innerWidth; H = win.innerHeight;
            cv.width = W * dpr; cv.height = H * dpr;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        };
        const init = () => {
            pts = [];
            for (let i = 0; i < N; i++) {
                pts.push({
                    x: Math.random() * W, y: Math.random() * H,
                    vx: (Math.random() - 0.5) * 0.32, vy: (Math.random() - 0.5) * 0.32,
                    r: Math.random() * 1.6 + 0.6, c: i % 3,
                });
            }
        };
        resize(); init();
        win.addEventListener('resize', () => { resize(); init(); });
        let mx = -99999, my = -99999;
        win.addEventListener('mousemove', (e) => { mx = e.clientX; my = e.clientY; }, { passive: true });
        const tick = () => {
            ctx.clearRect(0, 0, W, H);
            const pal = palette();
            for (const p of pts) {
                p.x += p.vx; p.y += p.vy;
                if (p.x < -12) p.x = W + 12; if (p.x > W + 12) p.x = -12;
                if (p.y < -12) p.y = H + 12; if (p.y > H + 12) p.y = -12;
                const dx = p.x - mx, dy = p.y - my;
                const d2 = dx * dx + dy * dy;
                if (d2 < 15000) {
                    const d = Math.sqrt(d2) || 1;
                    const f = (122 - d) / 122 * 0.55;
                    p.x += dx / d * f; p.y += dy / d * f;
                }
                const col = pal[p.c];
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(' + col[0] + ',' + col[1] + ',' + col[2] + ',0.45)';
                ctx.fill();
            }
            for (let i = 0; i < pts.length; i++) {
                for (let j = i + 1; j < pts.length; j++) {
                    const a = pts[i], b = pts[j];
                    const dx = a.x - b.x, dy = a.y - b.y;
                    const d2 = dx * dx + dy * dy;
                    if (d2 < 11000) {
                        const col = pal[0];
                        ctx.strokeStyle = 'rgba(' + col[0] + ',' + col[1] + ',' + col[2] + ',' + (0.13 * (1 - d2 / 11000)) + ')';
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(a.x, a.y);
                        ctx.lineTo(b.x, b.y);
                        ctx.stroke();
                    }
                }
            }
            requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    }
})();
</script>
"""


def inject_ui_v2():
    """向页面注入 UI 3.0 液态玻璃样式与交互脚本（每页执行，脚本自带幂等守卫）。"""
    st.markdown(V3_CSS, unsafe_allow_html=True)
    components.html(V3_JS, height=0, width=0)
