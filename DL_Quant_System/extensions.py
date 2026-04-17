# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：统一管理和路由所有的新增模块
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import pandas as pd
import numpy as np

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import re
from datetime import datetime

# 🔥 引入开源神兵 AkShare 🔥
try:
    import akshare as ak

    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

SUB_PATTERN = re.compile(r'^SUB(\d+)_')


def summon_global_3d_lulu():
    """终极寄生版：军用级雷达白名单，彻底无视上方骨骼包围盒与隐形空气墙"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path): return

    with st.spinner("正在为雷达加装白名单识别系统..."):
        with open(file_path, "rb") as f:
            glb_b64 = base64.b64encode(f.read()).decode("utf-8")

    html_code = f"""
    <script>
        const parentWin = window.parent;
        const parentDoc = parentWin.document;

        if (!parentWin.__LULU_INITIALIZED__) {{
            parentWin.__LULU_INITIALIZED__ = true;
            parentWin.__LULU_B64__ = "{glb_b64}";

            const loadScript = (src) => new Promise((res) => {{
                const s = parentDoc.createElement('script');
                s.src = src; s.onload = res; parentDoc.head.appendChild(s);
            }});

            const initLulu = async () => {{
                await loadScript("https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js");
                await loadScript("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js");

                const script = parentDoc.createElement('script');
                script.innerHTML = `
                    (function() {{
                        const THREE = window.THREE;
                        const win = window;
                        const doc = document;

                        let state = 'IDLE'; 
                        let danceTimer = 0;
                        let lastActivityTime = Date.now();
                        let idleActionState = 'NONE'; 
                        let idleActionTimer = 0;

                        const petSize = 280; 
                        const overflowLimit = 80; 

                        const petBox = doc.createElement('div');
                        petBox.id = 'lulu-global-pet';
                        petBox.style.cssText = "position: fixed; bottom: 20px; right: 20px; width: " + petSize + "px; height: " + petSize + "px; z-index: 9999999; cursor: grab; user-select: none; pointer-events: none; transition: transform 0.2s; touch-action: none;"; 
                        doc.body.appendChild(petBox);

                        const bubble = doc.createElement('div');
                        bubble.style.cssText = "position: absolute; top: 0px; left: 50%; transform: translateX(-50%); opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #ff8c00; color: #fff; padding: 8px 15px; border-radius: 12px; font-size: 14px; white-space: nowrap; transition: opacity 0.3s; pointer-events: none;";
                        petBox.appendChild(bubble);

                        const scene = new THREE.Scene();
                        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                        camera.position.set(0, 0.8, 5.5); 

                        const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: win.innerWidth > 768 }});
                        renderer.setSize(petSize, petSize);
                        renderer.setPixelRatio(win.devicePixelRatio ? Math.min(win.devicePixelRatio, 2) : 1);
                        renderer.outputEncoding = THREE.sRGBEncoding;
                        petBox.appendChild(renderer.domElement);

                        const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
                        scene.add(ambientLight);
                        const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
                        dirLight.position.set(5, 10, 5);
                        scene.add(dirLight);

                        let model, mixer;
                        let targetRotY = 0; 
                        let targetRotX = 0;
                        let clickableMeshes = [];

                        const loader = new THREE.GLTFLoader();
                        loader.load("data:application/octet-stream;base64," + win.__LULU_B64__, (gltf) => {{
                            model = gltf.scene;
                            model.position.set(0, -1.2, 0); 

                            model.traverse((child) => {{
                                if (child.isMesh) {{
                                    let isTrash = false;
                                    if (child.material) {{
                                        if (child.material.transparent && child.material.opacity < 0.1) isTrash = true;
                                        if (child.material.opacity === 0) isTrash = true;
                                    }}
                                    if (isTrash) {{ child.visible = false; }} 
                                    else {{ clickableMeshes.push(child); }}
                                }}
                            }});
                            scene.add(model);
                            if (gltf.animations.length > 0) {{
                                mixer = new THREE.AnimationMixer(model);
                                mixer.clipAction(gltf.animations[0]).play();
                            }}
                        }});

                        const raycaster = new THREE.Raycaster();
                        const mouseNDC = new THREE.Vector2();

                        const checkHit = (clientX, clientY) => {{
                            if (clickableMeshes.length === 0) return false;
                            const rect = renderer.domElement.getBoundingClientRect();
                            if (clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) {{ return false; }}
                            mouseNDC.x = ((clientX - rect.left) / petSize) * 2 - 1;
                            mouseNDC.y = -((clientY - rect.top) / petSize) * 2 + 1;
                            raycaster.setFromCamera(mouseNDC, camera);
                            const intersects = raycaster.intersectObjects(clickableMeshes, false);
                            return intersects.length > 0; 
                        }};

                        const updateLookAt = (clientX, clientY) => {{
                            lastActivityTime = Date.now();
                            if (state === 'IDLE' && idleActionState === 'NONE') {{
                                const mouseX = (clientX / win.innerWidth) * 2 - 1;
                                const mouseY = -(clientY / win.innerHeight) * 2 + 1;
                                targetRotY = mouseX * 0.8; targetRotX = -mouseY * 0.4;
                            }}
                        }};

                        const clock = new THREE.Clock();
                        function animate() {{
                            win.requestAnimationFrame(animate);
                            const delta = clock.getDelta();
                            const time = clock.getElapsedTime();
                            if (mixer) mixer.update(delta);
                            const now = Date.now();

                            if (state === 'IDLE' && idleActionState === 'NONE') {{
                                if (now - lastActivityTime > 30000) {{ 
                                    const actions = ['HOP', 'LOOK_AROUND', 'SPEAK'];
                                    const act = actions[Math.floor(Math.random() * actions.length)];
                                    idleActionState = act; idleActionTimer = 2.5; lastActivityTime = now; 
                                    if (act === 'SPEAK') {{
                                        doSpeak(["主公，您睡着了吗？🦦", "盯盘好累喔，发呆中...", "呼噜噜...💤"]);
                                        idleActionState = 'NONE'; 
                                    }}
                                }}
                            }}

                            if (model) {{
                                if (state === 'STRUGGLING') {{
                                    model.rotation.y = 0; model.rotation.x = 0;
                                    model.position.x = Math.sin(time * 50) * 0.05;
                                    model.rotation.z = Math.cos(time * 50) * 0.1;
                                    model.position.y = -1.2;
                                }} else if (state === 'DANCING') {{
                                    model.position.y = -1.2 + Math.abs(Math.sin(time * 10)) * 0.5;
                                    model.rotation.y += 0.2; model.rotation.x = 0; model.rotation.z = 0; model.position.x = 0;
                                    danceTimer -= delta;
                                    if (danceTimer <= 0) {{ state = 'IDLE'; model.position.y = -1.2; }}
                                }} else if (idleActionState === 'HOP') {{
                                    model.position.y = -1.2 + Math.abs(Math.sin(time * 15)) * 0.3;
                                    model.rotation.x = 0; model.rotation.y = 0;
                                    idleActionTimer -= delta;
                                    if (idleActionTimer <= 0) {{ idleActionState = 'NONE'; model.position.y = -1.2; }}
                                }} else if (idleActionState === 'LOOK_AROUND') {{
                                    model.rotation.y = Math.sin(time * 3) * 0.6; model.rotation.x = 0;
                                    idleActionTimer -= delta;
                                    if (idleActionTimer <= 0) {{ idleActionState = 'NONE'; model.rotation.y = targetRotY; }}
                                }} else {{
                                    model.position.y = -1.2 + Math.sin(time * 2) * 0.02;
                                    model.position.x = 0; model.rotation.z = 0;
                                    model.rotation.y += (targetRotY - model.rotation.y) * 0.1;
                                    model.rotation.x += (targetRotX - model.rotation.x) * 0.1;
                                }}
                            }}
                            renderer.render(scene, camera);
                        }}

                        let isDragging = false, initX, initY, startL, startT, isPossibleClick = false, isHolding = false, clickTimeout = null, lastTapTime = 0;
                        const getX = (e) => e.touches ? e.touches[0].clientX : e.clientX;
                        const getY = (e) => e.touches ? e.touches[0].clientY : e.clientY;

                        const doSpeak = (customTexts) => {{
                            const ts = customTexts || ["主公，我在这呢！🥰", "量化大赚！吃橘子！🍊", "点击我也不会晕的~🦦", "今天赚了多少呀？💸"];
                            bubble.innerText = ts[Math.floor(Math.random() * ts.length)]; bubble.style.opacity = '1';
                            setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                        }};

                        const doDance = () => {{
                            state = 'DANCING'; danceTimer = 3.0; lastActivityTime = Date.now();
                            bubble.innerText = "好耶！开心转圈圈！💃🕺"; bubble.style.opacity = '1';
                            setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                        }};

                        const startInteraction = (e) => {{
                            isHolding = true; initX = getX(e); initY = getY(e);
                            const r = petBox.getBoundingClientRect(); startL = r.left; startT = r.top;
                            isDragging = false; isPossibleClick = true; 
                            petBox.style.bottom = 'auto'; petBox.style.right = 'auto'; petBox.style.left = startL + 'px'; petBox.style.top = startT + 'px';
                        }};

                        win.addEventListener('mousemove', (e) => {{
                            if (isHolding) {{
                                const curX = getX(e); const curY = getY(e);
                                const moveDist = Math.sqrt(Math.pow(curX - initX, 2) + Math.pow(curY - initY, 2));
                                if (moveDist > 20) {{ 
                                    if (!isDragging) {{
                                        isDragging = true; isPossibleClick = false; state = 'STRUGGLING'; idleActionState = 'NONE';
                                        petBox.style.cursor = 'grabbing'; petBox.style.transform = 'scale(1.05)'; petBox.style.transition = 'none'; 
                                    }}
                                    let newLeft = startL + curX - initX; let newTop = startT + curY - initY;
                                    newLeft = Math.max(-overflowLimit, Math.min(newLeft, win.innerWidth - petSize + overflowLimit));
                                    newTop = Math.max(-overflowLimit, Math.min(newTop, win.innerHeight - petSize + overflowLimit));
                                    petBox.style.left = newLeft + 'px'; petBox.style.top = newTop + 'px';
                                    if(e.cancelable) e.preventDefault(); 
                                }}
                                return;
                            }}
                            updateLookAt(e.clientX, e.clientY);
                            if (checkHit(e.clientX, e.clientY)) {{
                                if (petBox.style.pointerEvents !== 'auto') {{ petBox.style.pointerEvents = 'auto'; petBox.style.cursor = 'grab'; }}
                            }} else {{
                                if (petBox.style.pointerEvents !== 'none') {{ petBox.style.pointerEvents = 'none'; }}
                            }}
                        }}, true);

                        const endInteraction = (e) => {{
                            if (!isHolding) return;
                            isHolding = false; petBox.style.transition = 'transform 0.2s'; petBox.style.cursor = 'grab'; petBox.style.transform = 'scale(1)'; lastActivityTime = Date.now();
                            if (isDragging) {{ isDragging = false; if (state !== 'DANCING') state = 'IDLE'; return; }}
                            if (isPossibleClick) {{
                                const currentTime = new Date().getTime(); const tapLength = currentTime - lastTapTime; clearTimeout(clickTimeout); 
                                if (tapLength < 350 && tapLength > 0) {{ doDance(); }} else {{ clickTimeout = setTimeout(() => {{ doSpeak(); }}, 300); }}
                                lastTapTime = currentTime;
                            }}
                        }};

                        petBox.addEventListener('mousedown', startInteraction); doc.addEventListener('mouseup', endInteraction); doc.addEventListener('mouseleave', endInteraction);

                        doc.addEventListener('touchstart', (e) => {{
                            if (checkHit(e.touches[0].clientX, e.touches[0].clientY)) {{
                                petBox.style.pointerEvents = 'auto'; startInteraction(e); e.stopPropagation();
                            }} else {{ petBox.style.pointerEvents = 'none'; }}
                        }}, {{ capture: true, passive: false }});

                        doc.addEventListener('touchmove', (e) => {{
                            if (isHolding) {{
                                const curX = getX(e); const curY = getY(e); const moveDist = Math.sqrt(Math.pow(curX - initX, 2) + Math.pow(curY - initY, 2));
                                if (moveDist > 20) {{ 
                                    if (!isDragging) {{
                                        isDragging = true; isPossibleClick = false; state = 'STRUGGLING'; idleActionState = 'NONE';
                                        petBox.style.cursor = 'grabbing'; petBox.style.transform = 'scale(1.05)'; petBox.style.transition = 'none'; 
                                    }}
                                    let newLeft = startL + curX - initX; let newTop = startT + curY - initY;
                                    newLeft = Math.max(-overflowLimit, Math.min(newLeft, win.innerWidth - petSize + overflowLimit));
                                    newTop = Math.max(-overflowLimit, Math.min(newTop, win.innerHeight - petSize + overflowLimit));
                                    petBox.style.left = newLeft + 'px'; petBox.style.top = newTop + 'px';
                                    e.stopPropagation(); if(e.cancelable) e.preventDefault(); 
                                }}
                            }} else {{ updateLookAt(e.touches[0].clientX, e.touches[0].clientY); }}
                        }}, {{ passive: false }});

                        doc.addEventListener('touchend', endInteraction); doc.addEventListener('touchcancel', endInteraction);
                        setTimeout(animate, 1500);
                    }})();
                `;
                parentDoc.body.appendChild(script);
            }};
            setTimeout(initLulu, 500); 
        }}
    </script>
    """
    components.html(html_code, height=0, width=0)


def render_new_features_page():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧩 扩展插件中心</h3></div>',
        unsafe_allow_html=True)
    st.info("💡 核心交互与 3D 桌宠已全部稳定运行！")


# ==========================================
# 辅助函数：AI 策略执行器与图表渲染器
# ==========================================
def safe_exec_fut_strategy(code, df):
    safe_code = code.replace("pandas.np", "np")
    l_vars = {}
    exec(safe_code, {"pd": pd, "np": np, "math": math}, l_vars)
    func_to_call = next((v for k, v in l_vars.items() if callable(v)), None)
    if not func_to_call: return df
    df_ai = func_to_call(df)
    sig_col = next((c for c in df_ai.columns if c.lower() == 'signal'), None)
    df_ai['Signal'] = df_ai[sig_col].fillna(0).apply(lambda x: 1 if x > 0.1 else (-1 if x < -0.1 else 0)).astype(
        int) if sig_col else 0
    return df_ai


def render_fut_charts(df):
    """
    🔥 终极原味复刻版：仅包含 K线、MA主图、成交量、MACD 等副图！
    """
    main_inds = [c for c in df.columns if c.startswith('MAIN_')]
    sub_groups = {}
    for c in df.columns:
        gid = SUB_PATTERN.match(c)
        if gid: sub_groups.setdefault(gid.group(1), []).append(c)

    rows = 2 + len(sub_groups)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.5, 0.15] + [0.35 / max(1, len(sub_groups))] * len(sub_groups))

    fig.add_trace(go.Candlestick(x=df['trade_date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 increasing_line_color='#FD1050', decreasing_line_color='#00FF00', name='K线'), row=1,
                  col=1)
    colors = ['#FFFF00', '#FF00FF', '#00FFFF', '#FFFFFF']
    for i, col in enumerate(main_inds): fig.add_trace(
        go.Scatter(x=df['trade_date'], y=df[col], name=col, line=dict(width=1.2, color=colors[i % 4])), row=1, col=1)

    if 'Signal' in df.columns:
        buys, sells = df[df['Signal'] == 1], df[df['Signal'] == -1]
        fig.add_trace(go.Scatter(x=buys['trade_date'], y=buys['Low'] * 0.95, mode='markers',
                                 marker=dict(symbol='triangle-up', size=14, color='#00FFFF'), name='买'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sells['trade_date'], y=sells['High'] * 1.05, mode='markers',
                                 marker=dict(symbol='triangle-down', size=14, color='#FF00FF'), name='卖'), row=1,
                      col=1)

    fig.add_trace(go.Bar(x=df['trade_date'], y=df.get('Volume', np.zeros(len(df))),
                         marker_color=np.where(df['Close'] >= df['Open'], '#FD1050', '#00FF00'), name='成交量'), row=2,
                  col=1)

    row_idx = 3
    for gid in sorted(sub_groups.keys(), key=int):
        for i, col in enumerate(sub_groups[gid]):
            if 'HIST' in col.upper():
                fig.add_trace(
                    go.Bar(x=df['trade_date'], y=df[col], marker_color=np.where(df[col] >= 0, '#FD1050', '#00FF00'),
                           name=col), row=row_idx, col=1)
            else:
                line_color = colors[i % 4]
                fig.add_trace(
                    go.Scatter(x=df['trade_date'], y=df[col], line=dict(width=1.5, color=line_color), name=col),
                    row=row_idx, col=1)
        row_idx += 1

    fig.update_layout(height=500 + len(sub_groups) * 150, template="none", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False, dragmode='pan', hovermode='x',
                      showlegend=False)
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    return fig


# ==========================================
# 🔥 核心引擎：期货全量审计 (AkShare 开源神兵版)
# ==========================================
def render_futures_backtest():
    if not HAS_AKSHARE:
        st.error("🚨 警告：检测到未装备 AkShare 引擎！\n\n主公，请立即在终端执行以下军令完成列装：\n`pip install akshare`")
        return

    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🔗 期货全量审计与归因分析</h3><p class="sub-text">已切换至全免费无限制的 AkShare 开源数据引擎。直接输入代码，自动拉取分钟与日线数据！</p></div>',
        unsafe_allow_html=True)

    if "fut_bt_run" not in st.session_state: st.session_state.fut_bt_run = False
    if "fut_bt_data" not in st.session_state: st.session_state.fut_bt_data = None
    if "fut_bt_metrics" not in st.session_state: st.session_state.fut_bt_metrics = None

    c1, c2 = st.columns([1, 3])
    with c1:
        with st.expander("🛠️ 不知道输入什么代码？点击查看帮助", expanded=False):
            st.markdown("""
            **直接输入品种代码 + 年月即可 (绝对无需后缀！)**
            - 纯碱主力: `SA2409`, `SA2501`
            - 螺纹钢: `RB2410`, `RB2501`
            - 铁矿石: `I2409`, `I2501`
            - 焦煤: `JM2409`
            - 玻璃: `FG2409`
            """)
        st.markdown("---")

        fut_code_input = st.text_input("🎯 期货合约代码", value="SA2409", placeholder="直接输入，如: SA2409")

        # AkShare 分钟线参数：'1', '5', '15', '30', '60'
        freq_mapping = {"日线 (Daily)": "D", "60分钟 (60min)": "60", "30分钟 (30min)": "30", "15分钟 (15min)": "15",
                        "5分钟 (5min)": "5", "1分钟 (1min)": "1"}
        freq_choice = st.selectbox("⏱️ 数据周期", list(freq_mapping.keys()), index=0)
        selected_freq = freq_mapping[freq_choice]

        span_mapping = {"近1个月": 0.08, "近3个月": 0.25, "近半年": 0.5, "近1年": 1, "近3年": 3, "近5年": 5}
        span_choice = st.selectbox("⏳ 回测时间跨度", list(span_mapping.keys()), index=3)
        start_year = int(datetime.now().year - span_mapping[span_choice])
        start_date_str = f"{start_year}0101"

        margin_input_str = st.text_input("⚖️ 保证金比例 (%)", value="", placeholder="留空默认 12%")
        multiplier_input_str = st.text_input("🔢 合约乘数 (吨/手)", value="", placeholder="留空自动匹配对应品种")

        if st.button("🚀 开始穿透回测", type="primary", use_container_width=True):
            if fut_code_input.strip() == "":
                st.error("主公，请先输入期货代码！")
            else:
                st.session_state.fut_bt_run = True
                st.session_state.fut_bt_data = None
                st.session_state.fut_bt_metrics = None

    with c2:
        if st.session_state.fut_bt_run and fut_code_input.strip() != "":
            with st.spinner(f"正在调取开源神兵 AkShare 获取 {fut_code_input} 的 {freq_choice} 数据..."):
                try:
                    # 剥离多余字符，AkShare 只要纯净的字母+数字
                    real_code = fut_code_input.upper().strip().split('.')[0]
                    df = None

                    # 1. 根据周期选择不同的 AkShare API
                    try:
                        if selected_freq == 'D':
                            df_temp = ak.futures_zh_daily_sina(symbol=real_code)
                            if df_temp is not None and not df_temp.empty:
                                df_temp['trade_date'] = pd.to_datetime(df_temp['date'])
                                df = df_temp
                        else:
                            df_temp = ak.futures_zh_minute_sina(symbol=real_code, period=selected_freq)
                            if df_temp is not None and not df_temp.empty:
                                df_temp['trade_date'] = pd.to_datetime(df_temp['datetime'])
                                df = df_temp
                    except Exception as e:
                        pass  # 下方容灾接管

                    # 2. 如果 AkShare 没有查到 (可能合约没上市)，触发容灾沙盘给导师演示
                    if df is None or df.empty:
                        st.warning(
                            f"⚠️ **触发容灾机制**：AkShare 接口未返回 `{real_code}` 的真实数据（可能合约尚未上市或输入错误）。\n\n系统已自动启动【底层沙盒模拟引擎】，为您瞬间生成逼真的 **{freq_choice}** 高频推演数据！")

                        base_p = 3000 if 'RB' in real_code else (800 if 'I' in real_code else 2000)
                        volatility = base_p * 0.0015

                        np.random.seed()
                        periods_num = 400
                        freq_pd = selected_freq.replace('m', 'T') if selected_freq != 'D' else 'D'
                        dates = pd.date_range(end=datetime.now(), periods=periods_num, freq=freq_pd)

                        closes = [base_p]
                        for _ in range(periods_num - 1): closes.append(closes[-1] + np.random.normal(0, volatility))

                        df = pd.DataFrame({'trade_date': dates})
                        df['close'] = closes
                        df['open'] = df['close'].shift(1).fillna(df['close'][0] + np.random.normal(0, volatility))
                        df['high'] = df[['open', 'close']].max(axis=1) + np.abs(
                            np.random.normal(0, volatility / 1.5, periods_num))
                        df['low'] = df[['open', 'close']].min(axis=1) - np.abs(
                            np.random.normal(0, volatility / 1.5, periods_num))
                        df['volume'] = np.abs(np.random.normal(15000, 5000, periods_num)).astype(int)
                    else:
                        # 对于查到的真实数据，按照用户选择的时间跨度进行切割
                        df = df[df['trade_date'] >= pd.to_datetime(start_date_str)].reset_index(drop=True)

                    if df.empty:
                        st.error("❌ 您选择的时间范围内没有数据。请尝试拉长【回测时间跨度】。")
                        st.session_state.fut_bt_run = False
                    else:
                        # 3. 智能判断乘数和保证金 (利用咱们的硬编码大字典保障速度)
                        # 列出所有常见品种的一手吨数
                        default_mult_map = {'SA': 20, 'RB': 10, 'I': 100, 'HC': 10, 'FG': 20, 'V': 5, 'P': 10, 'M': 10,
                                            'Y': 10, 'C': 10, 'CS': 10, 'JD': 10, 'CU': 5, 'AL': 5, 'ZN': 5, 'NI': 1,
                                            'AU': 1000, 'AG': 15, 'RU': 10, 'TA': 5, 'MA': 10, 'CF': 5, 'SR': 10,
                                            'OI': 10, 'RM': 10, 'ZC': 100, 'JM': 60, 'J': 100, 'UR': 20}
                        sym_match = re.match(r'^([A-Za-z]+)', real_code)
                        symbol_letter = sym_match.group(1).upper() if sym_match else 'SA'

                        api_mult = default_mult_map.get(symbol_letter, 10.0)
                        api_margin = 10.0  # AkShare没有方便的接口查保证金，默认基准10%

                        try:
                            final_margin_rate = float(margin_input_str) / 100.0 if margin_input_str.strip() else (
                                                                                                                             api_margin * 1.2) / 100.0
                        except:
                            final_margin_rate = (api_margin * 1.2) / 100.0

                        try:
                            final_mult = float(multiplier_input_str) if multiplier_input_str.strip() else api_mult
                        except:
                            final_mult = api_mult

                        st.success(
                            f"✅ 成功挂载：**{real_code}** ({freq_choice})！已应用底层查询乘数: **{final_mult}**, 智能计算保证金率: **{final_margin_rate * 100:.2f}%**")

                        # 4. 数据清洗统一战线
                        mapping_base = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close',
                                        'volume': 'Volume', 'vol': 'Volume'}
                        for l_case, c_case in mapping_base.items():
                            if l_case in df.columns: df[c_case] = df[l_case]

                        df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()
                        df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()

                        # 兼容股票策略，自动补全 MACD 副图指标
                        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                        df['SUB1_MACD_DIFF'] = exp1 - exp2
                        df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()
                        df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])

                        if st.session_state.get('generated_code'):
                            df_ai = safe_exec_fut_strategy(st.session_state.generated_code, df)
                            for col in df_ai.columns:
                                if col == 'Signal' or col.startswith(('MAIN_', 'SUB')): df[col] = df_ai[col]
                        else:
                            df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)

                        df['Ret'] = df['Close'].pct_change()
                        df['Pos'] = df.get('Signal', pd.Series([0] * len(df))).replace(0, np.nan).ffill().fillna(0)

                        df['Point_PnL'] = df['Close'].diff() * df['Pos'].shift(1).fillna(0)
                        init_cash, trade_lots = 1000000, 10
                        df['Total_PnL'] = df['Point_PnL'] * final_mult * trade_lots
                        df['Equity'] = init_cash + df['Total_PnL'].cumsum()
                        df['Margin_Used'] = df['Close'] * final_mult * final_margin_rate * trade_lots

                        final_equity = df['Equity'].iloc[-1]
                        total_return = (final_equity - init_cash) / init_cash
                        annual = (1 + total_return) ** (252 / max(1, len(df))) - 1 if not df.empty else 0
                        max_dd = (df['Equity'] / df['Equity'].cummax() - 1).min()
                        max_margin = df['Margin_Used'].max()

                        st.session_state.fut_bt_data = df
                        st.session_state.fut_bt_metrics = {"total": total_return, "annual": annual, "max_dd": max_dd,
                                                           "max_margin": max_margin, "init_cash": init_cash}

                except Exception as e:
                    st.error(f"系统运算发生熔断: {e}")
                    st.session_state.fut_bt_run = False

        if st.session_state.fut_bt_data is not None:
            m = st.session_state.fut_bt_metrics
            df = st.session_state.fut_bt_data

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(
                f'<div class="metric-box"><p>累计收益 (带杠杆)</p><h2 class="highlight-text">{m["total"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c2.markdown(
                f'<div class="metric-box"><p>期末总权益</p><h2 class="highlight-text">¥ {m["init_cash"] * (1 + m["total"]):,.0f}</h2></div>',
                unsafe_allow_html=True)
            c3.markdown(
                f'<div class="metric-box"><p>最大资金回撤</p><h2 class="danger-text">{m["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c4.markdown(
                f'<div class="metric-box"><p>最高保证金占用</p><h2 class="highlight-text">¥ {m["max_margin"]:,.0f}</h2></div>',
                unsafe_allow_html=True)

            st.markdown("<div style='clear: both; margin-bottom: 30px;'></div>", unsafe_allow_html=True)

            # 渲染那套完美统一的高端视觉图表
            st.plotly_chart(render_fut_charts(df), use_container_width=True, config={'scrollZoom': True})

        elif not st.session_state.fut_bt_run:
            st.markdown("""
            <div class="metric-box" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <p>等待主公下达指令</p>
                <h2 style="color: #cbd5e1;">点击 [开始穿透回测] 进行推演</h2>
                <p class="sub-text" style="margin-top: 10px;">AkShare 引擎已接管，自动突破高频数据封锁！</p>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# 🔥 新增功能：期货高频沙盘
# ==========================================
def render_futures_sandbox():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🌪️ 期货高频沙盘模拟推演</h3><p class="sub-text">Tick 级盘口模拟、毫秒级信号响应测试与动态滑点侦测。</p></div>',
        unsafe_allow_html=True)
    st.warning("⚠️ 高频警告：期货自带杠杆且波动剧烈，请确保您的‘止损熔断’脚本已装载且经过极寒测试。")

    c_left, c_right = st.columns([1, 2.5])
    with c_left:
        st.markdown("""
        <div class="glass-card" style="padding: 15px;">
            <h4 style="margin-top:0; color:#ff4b4b;">卖盘 (Ask)</h4>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖五</span><span>2512</span><span>124</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖四</span><span>2511</span><span>32</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖三</span><span>2510</span><span>15</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖二</span><span>2509</span><span>8</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖一</span><span>2508</span><span>45</span></div>
            <hr style="margin: 10px 0; border-color: rgba(255,255,255,0.1);">
            <h3 style="margin:0; text-align:center; color:#00ffcc; text-shadow: 0 0 10px rgba(0,255,204,0.5);">现价: 2507</h3>
            <hr style="margin: 10px 0; border-color: rgba(255,255,255,0.1);">
            <h4 style="margin-top:0; color:#00ffcc;">买盘 (Bid)</h4>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买一</span><span>2506</span><span>89</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买二</span><span>2505</span><span>12</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买三</span><span>2504</span><span>56</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买四</span><span>2503</span><span>105</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买五</span><span>2502</span><span>210</span></div>
        </div>
        """, unsafe_allow_html=True)

    with c_right:
        st.markdown("""
        <div class="metric-box" style="height: 380px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
            <p>高频推演</p>
            <h2 style="color: #00ffcc;">Tick 走势图及 DOM 深度图渲染区</h2>
            <p class="sub-text" style="margin-top: 10px;">(待后续接入 websocket 实时流数据)</p>
        </div>
        """, unsafe_allow_html=True)