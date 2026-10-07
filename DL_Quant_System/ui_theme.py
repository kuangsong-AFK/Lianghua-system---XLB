# -*- coding: utf-8 -*-
"""UI 2.0 视觉主题层（小吕布量化 Pro）

独立于业务代码的全局视觉系统，在 app.py 顶部注入：
- 动态极光背景（多层渐变 + 缓慢漂移光斑 + 噪点质感）
- 星尘粒子画布（跟随光标的微光粒子 + 连线，尊重"减少动态"偏好）
- 玻璃拟态卡片（毛玻璃 + 悬停浮起 + 边框辉光）
- 按钮系统：渐变底色、悬停光扫、按压涟漪 + 缩放反馈、聚焦光环
- 导航/输入框/表格/进度条/滚动条/Toast 全套重绘
- 深色/浅色双主题（跟随 st.session_state.visual_theme 挂载的 data-custom-theme 属性）
"""

import streamlit as st
import streamlit.components.v1 as components

V2_CSS = """
<style>
/* ================= UI 2.0 · 小吕布量化 Pro ================= */

/* ---------- 0. 主题变量 ---------- */
.stApp[data-custom-theme='dark'] {
    --v2-accent: #38bdf8;
    --v2-accent2: #a78bfa;
    --v2-glow: rgba(56, 189, 248, 0.45);
    --v2-card: rgba(17, 24, 39, 0.60);
    --v2-card-brd: rgba(148, 163, 184, 0.16);
    --v2-text: #e2e8f0;
    --v2-muted: #94a3b8;
    --v2-input: rgba(30, 41, 59, 0.72);
    --v2-ripple: rgba(255, 255, 255, 0.35);
}
.stApp[data-custom-theme='light'], .stApp:not([data-custom-theme]) {
    --v2-accent: #3b82f6;
    --v2-accent2: #8b5cf6;
    --v2-glow: rgba(59, 130, 246, 0.30);
    --v2-card: rgba(255, 255, 255, 0.66);
    --v2-card-brd: rgba(30, 41, 59, 0.10);
    --v2-text: #1e293b;
    --v2-muted: #64748b;
    --v2-input: rgba(255, 255, 255, 0.88);
    --v2-ripple: rgba(59, 130, 246, 0.28);
}

/* ---------- 1. 动态极光背景 ---------- */
.stApp[data-custom-theme='dark'],
.stApp[data-custom-theme='dark'] [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(62% 46% at 12% 6%, rgba(56, 189, 248, 0.20), transparent 62%),
        radial-gradient(56% 44% at 88% 10%, rgba(167, 139, 250, 0.18), transparent 62%),
        radial-gradient(52% 42% at 80% 90%, rgba(34, 211, 238, 0.14), transparent 60%),
        radial-gradient(46% 38% at 18% 94%, rgba(244, 114, 182, 0.12), transparent 60%),
        linear-gradient(165deg, #04060d 0%, #0a1024 34%, #0c1330 64%, #060812 100%) !important;
    background-size: 100% 100% !important;
    background-attachment: fixed !important;
    animation: v2AuroraA 46s ease-in-out infinite alternate !important;
}
.stApp[data-custom-theme='light'],
.stApp[data-custom-theme='light'] [data-testid="stAppViewContainer"],
.stApp:not([data-custom-theme]),
.stApp:not([data-custom-theme]) [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(60% 46% at 12% 4%, rgba(59, 130, 246, 0.14), transparent 62%),
        radial-gradient(56% 44% at 88% 8%, rgba(139, 92, 246, 0.12), transparent 62%),
        radial-gradient(52% 42% at 82% 92%, rgba(14, 165, 233, 0.10), transparent 60%),
        radial-gradient(46% 38% at 16% 96%, rgba(236, 72, 153, 0.08), transparent 60%),
        linear-gradient(160deg, #f6f8fd 0%, #eef2fb 38%, #f3effd 68%, #f7f9fe 100%) !important;
    background-size: 100% 100% !important;
    background-attachment: fixed !important;
    animation: v2AuroraA 52s ease-in-out infinite alternate !important;
}

/* 漂移光斑（GPU 合成） */
.stApp[data-custom-theme]::before,
.stApp[data-custom-theme]::after {
    content: "";
    position: fixed;
    z-index: 0;
    pointer-events: none;
    border-radius: 50%;
    filter: blur(60px);
    mix-blend-mode: screen;
    will-change: transform;
}
.stApp[data-custom-theme='dark']::before {
    width: 48vw; height: 48vw; top: -16vw; left: -12vw;
    background: radial-gradient(circle, rgba(56, 189, 248, 0.34) 0%, rgba(56, 189, 248, 0.10) 36%, transparent 70%);
    animation: v2BlobA 26s ease-in-out infinite alternate;
}
.stApp[data-custom-theme='dark']::after {
    width: 44vw; height: 44vw; bottom: -18vw; right: -10vw;
    background: radial-gradient(circle, rgba(167, 139, 250, 0.30) 0%, rgba(167, 139, 250, 0.08) 36%, transparent 70%);
    animation: v2BlobB 32s ease-in-out infinite alternate;
}
.stApp[data-custom-theme='light']::before {
    width: 46vw; height: 46vw; top: -14vw; left: -10vw;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.18) 0%, rgba(59, 130, 246, 0.05) 36%, transparent 70%);
    animation: v2BlobA 30s ease-in-out infinite alternate;
}
.stApp[data-custom-theme='light']::after {
    width: 42vw; height: 42vw; bottom: -16vw; right: -8vw;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.16) 0%, rgba(139, 92, 246, 0.04) 36%, transparent 70%);
    animation: v2BlobB 36s ease-in-out infinite alternate;
}

@keyframes v2AuroraA {
    0% { background-position: 0% 0%, 100% 0%, 100% 100%, 0% 100%, 0 0; }
    50% { background-position: 6% 8%, 92% 6%, 94% 92%, 8% 94%, 0 0; }
    100% { background-position: 0% 14%, 88% 0%, 100% 88%, 2% 98%, 0 0; }
}
@keyframes v2BlobA {
    from { transform: translate(0, 0) scale(1); opacity: .8; }
    to { transform: translate(13vw, 10vh) scale(1.18); opacity: 1; }
}
@keyframes v2BlobB {
    from { transform: translate(0, 0) scale(1.1); opacity: .75; }
    to { transform: translate(-11vw, -9vh) scale(0.95); opacity: 1; }
}

/* ---------- 2. 玻璃卡片 ---------- */
.glass-card, .metric-box, [data-testid="stExpander"] {
    background: var(--v2-card) !important;
    backdrop-filter: blur(22px) saturate(170%) !important;
    -webkit-backdrop-filter: blur(22px) saturate(170%) !important;
    border: 1px solid var(--v2-card-brd) !important;
    border-radius: 22px !important;
    box-shadow: 0 18px 50px rgba(2, 6, 23, 0.22), inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease !important;
}
.glass-card:hover, .metric-box:hover {
    border-color: rgba(56, 189, 248, 0.35) !important;
    border-color: color-mix(in srgb, var(--v2-accent) 45%, transparent) !important;
    box-shadow: 0 24px 62px rgba(2, 6, 23, 0.32), 0 0 0 1px color-mix(in srgb, var(--v2-accent) 18%, transparent),
        inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    transform: translateY(-2px);
}
.stApp[data-custom-theme] .metric-box h2,
.stApp[data-custom-theme] .highlight-text {
    color: var(--v2-accent) !important;
    text-shadow: 0 0 20px var(--v2-glow);
}

/* ---------- 3. 按钮系统（光扫 + 按压反馈 + 涟漪） ---------- */
.stButton > button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button,
.stApp[data-custom-theme] button[kind="secondary"] {
    position: relative;
    overflow: hidden;
    border-radius: 14px !important;
    border: 1px solid rgba(56, 189, 248, 0.30) !important;
    border-color: color-mix(in srgb, var(--v2-accent) 36%, transparent) !important;
    background: linear-gradient(135deg,
        color-mix(in srgb, var(--v2-accent) 14%, transparent),
        color-mix(in srgb, var(--v2-accent2) 14%, transparent)) !important;
    color: var(--v2-text) !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    box-shadow: 0 4px 14px rgba(2, 6, 23, 0.18) !important;
    transition: transform 0.22s cubic-bezier(0.2, 0.8, 0.3, 1.2),
        box-shadow 0.22s ease, border-color 0.22s ease, filter 0.22s ease !important;
}
.stButton > button:hover, .stDownloadButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-2px);
    border-color: var(--v2-accent) !important;
    box-shadow: 0 10px 28px var(--v2-glow), 0 0 0 1px color-mix(in srgb, var(--v2-accent) 30%, transparent) !important;
    filter: brightness(1.06);
}
.stButton > button:active, .stDownloadButton button:active, [data-testid="stFormSubmitButton"] button:active,
.stApp[data-custom-theme] button[kind="primary"]:active {
    transform: translateY(1px) scale(0.97) !important;
    box-shadow: 0 2px 8px rgba(2, 6, 23, 0.28) !important;
    filter: brightness(0.9);
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
    background: linear-gradient(100deg, transparent, rgba(255, 255, 255, 0.28), transparent);
    transform: skewX(-22deg);
    transition: left 0.55s ease;
    pointer-events: none;
}
.stButton > button:hover::after, .stDownloadButton button:hover::after { left: 170%; }

/* 主按钮：渐变色 + 辉光 */
.stApp[data-custom-theme] button[kind="primary"],
.stApp[data-custom-theme] .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--v2-accent), var(--v2-accent2)) !important;
    background-size: 160% 160% !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: 0 6px 22px var(--v2-glow) !important;
    transition: transform 0.22s cubic-bezier(0.2, 0.8, 0.3, 1.2), box-shadow 0.25s ease,
        background-position 0.5s ease, filter 0.22s ease !important;
}
.stApp[data-custom-theme] button[kind="primary"]:hover,
.stApp[data-custom-theme] .stButton > button[kind="primary"]:hover {
    transform: translateY(-2px);
    background-position: 100% 50% !important;
    box-shadow: 0 14px 36px var(--v2-glow), 0 0 0 1px color-mix(in srgb, var(--v2-accent) 40%, transparent) !important;
    filter: brightness(1.08);
}

/* ---------- 4. 侧边栏与导航 ---------- */
.stApp[data-custom-theme] [data-testid="stSidebar"] {
    background: var(--v2-card) !important;
    border-right: 1px solid var(--v2-card-brd) !important;
    backdrop-filter: blur(26px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(26px) saturate(180%) !important;
    box-shadow: 12px 0 40px rgba(2, 6, 23, 0.18) !important;
}
.stApp[data-custom-theme] div[role="radiogroup"] > label {
    border-radius: 14px !important;
    margin-bottom: 8px !important;
    padding: 9px 12px !important;
    border: 1px solid transparent !important;
    transition: transform 0.22s ease, background 0.22s ease, box-shadow 0.22s ease !important;
    cursor: pointer;
}
.stApp[data-custom-theme] div[role="radiogroup"] > label:hover {
    transform: translateX(4px);
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
    border: 1px solid var(--v2-card-brd) !important;
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
    border: 1px solid var(--v2-card-brd) !important;
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
    animation: v2Shimmer 2.2s linear infinite !important;
}
@keyframes v2Shimmer { 0% { background-position: 0% 0; } 100% { background-position: 200% 0; } }

/* ---------- 8. 数据表 ---------- */
.stApp[data-custom-theme] [data-testid="stDataFrame"] {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid var(--v2-card-brd) !important;
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
    border: 1px solid var(--v2-card-brd) !important;
    border-left: 3px solid var(--v2-accent) !important;
    backdrop-filter: blur(16px);
    box-shadow: 0 12px 34px rgba(2, 6, 23, 0.4) !important;
}

/* ---------- 11. 标题与分隔线 ---------- */
.stApp[data-custom-theme='dark'] h1, .stApp[data-custom-theme='dark'] h2 {
    text-shadow: 0 0 26px rgba(56, 189, 248, 0.28);
}
.stApp[data-custom-theme] hr {
    border-color: color-mix(in srgb, var(--v2-accent) 22%, transparent) !important;
}

/* ---------- 12. 页面入场动效 ---------- */
.block-container {
    animation: v2PageIn 0.45s cubic-bezier(0.2, 0.8, 0.3, 1) both !important;
}
@keyframes v2PageIn {
    from { opacity: 0; transform: translateY(16px) scale(0.995); }
    to { opacity: 1; transform: none; }
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

V2_JS = """
<script>
(() => {
    const win = window.parent;
    if (!win || win.__V2_UI_BOOT__) return;
    win.__V2_UI_BOOT__ = true;
    const doc = win.document;
    const reduceMotion = win.matchMedia && win.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---------- 1. 光标光晕（缓动跟随） ---------- */
    const glow = doc.createElement('div');
    glow.style.cssText = 'position:fixed;width:360px;height:360px;border-radius:50%;pointer-events:none;z-index:2;'
        + 'background:radial-gradient(circle, rgba(56,189,248,0.13), rgba(139,92,246,0.07) 42%, transparent 70%);'
        + 'transform:translate(-50%,-50%);opacity:0;transition:opacity .45s ease;';
    doc.body.appendChild(glow);
    let tx = -9999, ty = -9999, cx = -9999, cy = -9999;
    win.addEventListener('mousemove', (e) => { tx = e.clientX; ty = e.clientY; glow.style.opacity = '1'; }, { passive: true });
    win.addEventListener('mouseleave', () => { glow.style.opacity = '0'; });
    (function follow() {
        cx += (tx - cx) * 0.12;
        cy += (ty - cy) * 0.12;
        glow.style.left = cx + 'px';
        glow.style.top = cy + 'px';
        requestAnimationFrame(follow);
    })();

    /* ---------- 2. 按钮涟漪 + 按压反馈 ---------- */
    const rippleKey = doc.createElement('style');
    rippleKey.textContent = '@keyframes v2ripple{to{transform:scale(1);opacity:0;}}';
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
            + 'background:radial-gradient(circle, rgba(255,255,255,0.4), transparent 65%);'
            + 'transform:scale(0);opacity:.9;animation:v2ripple .5s ease-out forwards;';
        if (!btn.style.position || btn.style.position === 'static') btn.style.position = 'relative';
        btn.appendChild(rip);
        setTimeout(() => { if (rip.parentNode) rip.parentNode.removeChild(rip); }, 560);
    }, { passive: true });

    /* ---------- 3. 星尘粒子画布 ---------- */
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
    """向页面注入 UI 2.0 样式与交互脚本（每页执行，脚本自带幂等守卫）。"""
    st.markdown(V2_CSS, unsafe_allow_html=True)
    components.html(V2_JS, height=0, width=0)
