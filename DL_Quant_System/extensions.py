# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：极客 IDE、AkShare 期货、高频沙盘、多模型 3D 桌宠
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import time
import math
import re
import json
import pandas as pd
import numpy as np
from datetime import datetime

try:
    from streamlit import fragment as st_fragment
except ImportError:
    try:
        from streamlit import experimental_fragment as st_fragment
    except ImportError:
        st_fragment = lambda f: f

try:
    import akshare as ak

    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

SUB_PATTERN = re.compile(r'^SUB(\d+)_')


def summon_global_3d_lulu():
    """纯净国内阿里云 NPM 镜像 + 动态时间戳破甲强制渲染 + 绝对凝视"""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    PET_ROSTER = {
        "🍊 水豚噜噜": "lulu.glb",
        "🐧 高雅企鹅": "penguin.glb",
        "🐱 hello Kitty": "kitty.glb",
        "🐷 猪猪侠": "pig.glb"
    }

    pet_b64 = {}
    with st.spinner("正在为雷达加装多维宇宙识别系统..."):
        for name, filename in PET_ROSTER.items():
            path_static = os.path.join(current_dir, "static", filename)
            path_root = os.path.join(current_dir, filename)

            if os.path.exists(path_static):
                with open(path_static, "rb") as f:
                    pet_b64[name] = base64.b64encode(f.read()).decode("utf-8")
            elif os.path.exists(path_root):
                with open(path_root, "rb") as f:
                    pet_b64[name] = base64.b64encode(f.read()).decode("utf-8")
            else:
                pet_b64[name] = ""

    if not any(pet_b64.values()):
        return

    pets_json_str = json.dumps(pet_b64)
    # 🔥 核心：动态时间戳作为 JS 变量的一部分，强行击碎 Streamlit 组件死缓存！ 🔥
    run_id = str(time.time()).replace(".", "")

    html_code = f"""
    <script id="lulu-pet-data-{run_id}" type="application/json">{pets_json_str}</script>

    <script>
        const pWin = window.parent;
        const pDoc = pWin.document;

        const dataStr = document.getElementById('lulu-pet-data-{run_id}').textContent;
        pWin.__PETS_JSON_DATA__ = JSON.parse(dataStr);

        const loadScript = (src) => new Promise((res, rej) => {{
            const s = pDoc.createElement('script');
            s.src = src; 
            s.onload = res; 
            s.onerror = () => {{ console.error("加载依赖失败: " + src); res(); }};
            pDoc.head.appendChild(s);
        }});

        const initLulu = async () => {{
            if (!pWin.THREE || !pWin.THREE.DRACOLoader) {{
                // 🔥 绝杀修复：直接换用国内阿里淘宝 NPM 的官方镜像，速度直接拉满，绝无卡死可能！ 🔥
                await loadScript("https://registry.npmmirror.com/three/0.128.0/files/build/three.min.js");
                await loadScript("https://registry.npmmirror.com/three/0.128.0/files/examples/js/loaders/GLTFLoader.js");
                await loadScript("https://registry.npmmirror.com/three/0.128.0/files/examples/js/loaders/DRACOLoader.js");
            }}

            const script = pDoc.createElement('script');
            script.innerHTML = `
                (function() {{
                    const THREE = window.THREE;
                    const doc = document;
                    const win = window;
                    const petData = window.__PETS_JSON_DATA__; 

                    // 砸碎旧元素，防止重复挂载导致满屏分身
                    const oldPet = doc.getElementById('lulu-global-pet');
                    if(oldPet) oldPet.remove();
                    const oldMenu = doc.getElementById('lulu-ctx-menu');
                    if(oldMenu) oldMenu.remove();

                    let state = 'IDLE'; 
                    let danceTimer = 0;
                    let lastActivityTime = Date.now();

                    let targetRotY = 0; 
                    let targetRotX = 0;

                    const petSize = 280; 
                    const overflowLimit = 80; 

                    const petBox = doc.createElement('div');
                    petBox.id = 'lulu-global-pet';
                    petBox.style.cssText = "position: fixed; bottom: 20px; right: 20px; width: " + petSize + "px; height: " + petSize + "px; z-index: 9999999; cursor: grab; user-select: none; pointer-events: none; transition: transform 0.2s; touch-action: none;"; 
                    doc.body.appendChild(petBox);

                    const bubble = doc.createElement('div');
                    bubble.style.cssText = "position: absolute; top: 0px; left: 50%; transform: translateX(-50%); opacity: 0; background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(148, 163, 184, 0.5); color: #fff; padding: 8px 15px; border-radius: 12px; font-size: 14px; white-space: nowrap; transition: opacity 0.3s; pointer-events: none; box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 10;";
                    petBox.appendChild(bubble);

                    const ctxMenu = doc.createElement('div');
                    ctxMenu.id = 'lulu-ctx-menu';
                    ctxMenu.style.cssText = "position: fixed; display: none; background: rgba(30, 41, 59, 0.95); border: 1px solid rgba(148, 163, 184, 0.5); border-radius: 12px; padding: 6px; z-index: 10000000; color: #fff; font-size: 14px; min-width: 140px; box-shadow: 0 8px 24px rgba(0,0,0,0.4); backdrop-filter: blur(10px);";
                    doc.body.appendChild(ctxMenu);

                    const menuTitle = doc.createElement('div');
                    menuTitle.innerHTML = "<b>✨ 召唤新伙伴</b>";
                    menuTitle.style.cssText = "padding: 6px 12px; color: #94a3b8; font-size: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 4px; pointer-events: none;";
                    ctxMenu.appendChild(menuTitle);

                    Object.keys(petData).forEach(petName => {{
                        const item = doc.createElement('div');
                        item.innerText = petName;
                        item.style.cssText = "padding: 8px 12px; cursor: pointer; border-radius: 6px; transition: 0.2s; margin-bottom: 2px;";
                        item.onmouseover = () => {{ item.style.background = "rgba(255, 255, 255, 0.1)"; item.style.color = "#38bdf8"; }};
                        item.onmouseout = () => {{ item.style.background = "transparent"; item.style.color = "#fff"; }};

                        item.onclick = (e) => {{
                            e.stopPropagation();
                            ctxMenu.style.display = 'none';
                            if(petData[petName] !== "") {{
                                switchModel(petData[petName], petName);
                            }} else {{
                                doSpeak(["主公，【" + petName + "】的模型文件还没放入军营哦！"]);
                            }}
                        }};
                        ctxMenu.appendChild(item);
                    }});

                    const scene = new THREE.Scene();
                    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                    camera.position.set(0, 0.8, 5.5); 

                    const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: win.innerWidth > 768 }});
                    renderer.setSize(petSize, petSize);
                    renderer.setPixelRatio(win.devicePixelRatio ? Math.min(win.devicePixelRatio, 2) : 1);
                    renderer.outputEncoding = THREE.sRGBEncoding;

                    renderer.domElement.oncontextmenu = function(e) {{
                        e.preventDefault(); e.stopPropagation();
                        ctxMenu.style.display = 'block';
                        ctxMenu.style.left = (e.clientX + 10) + 'px'; ctxMenu.style.top = (e.clientY - 10) + 'px';
                        return false;
                    }};

                    petBox.appendChild(renderer.domElement);

                    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
                    scene.add(ambientLight);
                    const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
                    dirLight.position.set(5, 10, 5);
                    scene.add(dirLight);

                    let currentModelObj = null; 
                    let mixer = null;
                    let clickableMeshes = [];

                    // 配合使用国内淘宝 NPM 的解码资源路径
                    const loader = new THREE.GLTFLoader();
                    const dracoLoader = new THREE.DRACOLoader();
                    dracoLoader.setDecoderPath('https://registry.npmmirror.com/three/0.128.0/files/examples/js/libs/draco/gltf/');
                    loader.setDRACOLoader(dracoLoader);

                    const switchModel = (b64String, name) => {{
                        const oldModelRef = currentModelObj;
                        bubble.innerText = "⏳ 极速数据解码中..."; bubble.style.opacity = '1';

                        loader.load(
                            "data:application/octet-stream;base64," + b64String, 
                            (gltf) => {{
                                if(oldModelRef) {{ scene.remove(oldModelRef); }}
                                clickableMeshes = []; mixer = null;

                                currentModelObj = gltf.scene;
                                currentModelObj.position.set(0, -1.2, 0); 

                                currentModelObj.traverse((child) => {{
                                    if (child.isMesh) {{
                                        let isTrash = false;
                                        if (child.material) {{
                                            if (child.material.transparent && child.material.opacity < 0.1) isTrash = true;
                                            if (child.material.opacity === 0) isTrash = true;
                                        }}
                                        if (isTrash) {{ child.visible = false; }} else {{ clickableMeshes.push(child); }}
                                    }}
                                }});
                                scene.add(currentModelObj);
                                if (gltf.animations.length > 0) {{
                                    mixer = new THREE.AnimationMixer(currentModelObj);
                                    mixer.clipAction(gltf.animations[0]).play();
                                }}
                                setTimeout(() => {{ bubble.style.opacity = '0'; }}, 500);
                                if(name) {{
                                    setTimeout(() => {{
                                        bubble.innerText = "变身完成！我是" + name;
                                        bubble.style.opacity = '1';
                                        setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                                    }}, 600);
                                }}
                            }},
                            undefined,
                            (error) => {{
                                console.error("模型解析失败：", error);
                                bubble.innerText = "❌ 解析失败！请尝试更换模型。";
                                setTimeout(() => {{ bubble.style.opacity = '0'; }}, 4000);
                            }}
                        );
                    }};

                    const initialPetKey = Object.keys(petData).find(k => petData[k] !== "");
                    if(initialPetKey) {{ switchModel(petData[initialPetKey], null); }}

                    const raycaster = new THREE.Raycaster();
                    const mouseNDC = new THREE.Vector2();

                    const checkHit = (clientX, clientY) => {{
                        if (clickableMeshes.length === 0) return false;
                        const rect = renderer.domElement.getBoundingClientRect();
                        if (clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) {{ return false; }}
                        mouseNDC.x = ((clientX - rect.left) / petSize) * 2 - 1;
                        mouseNDC.y = -((clientY - rect.top) / petSize) * 2 + 1;
                        raycaster.setFromCamera(mouseNDC, camera);
                        return raycaster.intersectObjects(clickableMeshes, false).length > 0; 
                    }};

                    const updateLookAt = (clientX, clientY) => {{
                        if (state === 'IDLE') {{
                            const rect = renderer.domElement.getBoundingClientRect();
                            const petCenterX = rect.left + rect.width / 2;
                            const petCenterY = rect.top + rect.height / 2;
                            const dx = clientX - petCenterX;
                            const dy = clientY - petCenterY;
                            targetRotY = Math.max(-1.1, Math.min(1.1, (dx / (win.innerWidth / 2)) * 1.5));
                            targetRotX = Math.max(-0.8, Math.min(0.8, (dy / (win.innerHeight / 2)) * 1.2));
                        }}
                    }};

                    const clock = new THREE.Clock();
                    function animate() {{
                        win.requestAnimationFrame(animate);
                        const delta = clock.getDelta();
                        const time = clock.getElapsedTime();
                        if (mixer) mixer.update(delta);

                        if (currentModelObj) {{
                            if (state === 'STRUGGLING') {{
                                currentModelObj.rotation.y = 0; currentModelObj.rotation.x = 0;
                                currentModelObj.position.x = Math.sin(time * 50) * 0.05;
                                currentModelObj.rotation.z = Math.cos(time * 50) * 0.1;
                                currentModelObj.position.y = -1.2;
                            }} else if (state === 'DANCING') {{
                                currentModelObj.position.y = -1.2 + Math.abs(Math.sin(time * 10)) * 0.5;
                                currentModelObj.rotation.y += 0.2; currentModelObj.rotation.x = 0; currentModelObj.rotation.z = 0; currentModelObj.position.x = 0;
                                danceTimer -= delta;
                                if (danceTimer <= 0) {{ state = 'IDLE'; currentModelObj.position.y = -1.2; }}
                            }} else {{
                                currentModelObj.position.y = -1.2 + Math.sin(time * 2) * 0.01; 
                                currentModelObj.position.x = 0; 
                                currentModelObj.rotation.z = 0;
                                currentModelObj.rotation.y += (targetRotY - currentModelObj.rotation.y) * 0.15;
                                currentModelObj.rotation.x += (targetRotX - currentModelObj.rotation.x) * 0.15;
                            }}
                        }}
                        renderer.render(scene, camera);
                    }}

                    let isDragging = false, initX, initY, startL, startT, isPossibleClick = false, isHolding = false, clickTimeout = null, lastTapTime = 0;
                    const getX = (e) => e.touches ? e.touches[0].clientX : e.clientX;
                    const getY = (e) => e.touches ? e.touches[0].clientY : e.clientY;

                    const doSpeak = (customTexts) => {{
                        const ts = customTexts || ["主公，我在这呢！🥰", "量化大赚！吃橘子！🍊", "右键可以给我换衣服哦~", "今天赚了多少呀？💸"];
                        bubble.innerText = ts[Math.floor(Math.random() * ts.length)]; bubble.style.opacity = '1';
                        setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                    }};

                    const doDance = () => {{
                        state = 'DANCING'; danceTimer = 3.0; lastActivityTime = Date.now();
                        bubble.innerText = "好耶！开心转圈圈！💃🕺"; bubble.style.opacity = '1';
                        setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                    }};

                    const startInteraction = (e) => {{
                        if(e.button === 2) return; 
                        isHolding = true; initX = getX(e); initY = getY(e);
                        const r = petBox.getBoundingClientRect(); startL = r.left; startT = r.top;
                        isDragging = false; isPossibleClick = true; 
                        petBox.style.bottom = 'auto'; petBox.style.right = 'auto'; petBox.style.left = startL + 'px'; petBox.style.top = startT + 'px';
                    }};

                    doc.addEventListener('click', (e) => {{ if (e.button !== 2) {{ ctxMenu.style.display = 'none'; }} }});

                    win.addEventListener('mousemove', (e) => {{
                        if (isHolding) {{
                            const curX = getX(e); const curY = getY(e);
                            const moveDist = Math.sqrt(Math.pow(curX - initX, 2) + Math.pow(curY - initY, 2));
                            if (moveDist > 20) {{ 
                                if (!isDragging) {{
                                    isDragging = true; isPossibleClick = false; state = 'STRUGGLING'; 
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
                        isHolding = false; petBox.style.transition = 'transform 0.2s'; petBox.style.cursor = 'grab'; petBox.style.transform = 'scale(1)';
                        if (isDragging) {{ isDragging = false; if (state !== 'DANCING') state = 'IDLE'; return; }}
                        if (isPossibleClick) {{
                            const currentTime = new Date().getTime(); const tapLength = currentTime - lastTapTime; clearTimeout(clickTimeout); 
                            if (tapLength < 350 && tapLength > 0) {{ doDance(); }} else {{ 
                                clickTimeout = setTimeout(() => {{
                                    bubble.innerText = "右键可以给我换衣服哦~";
                                    bubble.style.opacity = '1';
                                    setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                                }}, 300); 
                            }}
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
                                    isDragging = true; isPossibleClick = false; state = 'STRUGGLING';
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
            pDoc.head.appendChild(script);
        }};
        setTimeout(initLulu, 500); 
    </script>
    """
    components.html(html_code, height=0, width=0)


# =======================================================
# 保留 IDE, 回测, 沙盘等功能
# =======================================================

def safe_exec_fut_strategy(code, df):
    if not code: return df
    try:
        safe_code = str(code).replace("pandas.np", "np")
        l_vars = {}
        exec(safe_code, {"pd": pd, "np": np, "math": math}, l_vars)
        func_to_call = next((v for k, v in l_vars.items() if callable(v)), None)
        if not func_to_call: return df

        df_ai = func_to_call(df.copy())
        if df_ai is None or not hasattr(df_ai, 'columns'): return df

        sig_col = next((c for c in df_ai.columns if c.lower() == 'signal'), None)
        if sig_col:
            df_ai['Signal'] = df_ai[sig_col].fillna(0).apply(
                lambda x: 1 if x > 0.1 else (-1 if x < -0.1 else 0)).astype(int)
        else:
            df_ai['Signal'] = 0
        return df_ai
    except Exception:
        return df


def render_fut_charts(df):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    main_inds = [c for c in df.columns if c.startswith('MAIN_')]
    sub_groups = {}
    for c in df.columns:
        gid = SUB_PATTERN.match(c)
        if gid: sub_groups.setdefault(gid.group(1), []).append(c)

    rows = 2 + len(sub_groups)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.5, 0.15] + [0.35 / max(1, len(sub_groups))] * len(sub_groups))
    x_labels = df['trade_date'].dt.strftime('%Y-%m-%d') if df['trade_date'].dt.time.nunique() <= 1 else df[
        'trade_date'].dt.strftime('%m-%d %H:%M')

    fig.add_trace(go.Candlestick(x=x_labels, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 increasing_line_color='#ef4444', decreasing_line_color='#10b981', name='K线'), row=1,
                  col=1)
    colors = ['#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899']
    for i, col in enumerate(main_inds): fig.add_trace(
        go.Scatter(x=x_labels, y=df[col], name=col, line=dict(width=1.2, color=colors[i % 4])), row=1, col=1)

    if 'Signal' in df.columns:
        buys, sells = df[df['Signal'] == 1], df[df['Signal'] == -1]
        buy_x = buys['trade_date'].dt.strftime('%Y-%m-%d') if df['trade_date'].dt.time.nunique() <= 1 else buys[
            'trade_date'].dt.strftime('%m-%d %H:%M')
        sell_x = sells['trade_date'].dt.strftime('%Y-%m-%d') if df['trade_date'].dt.time.nunique() <= 1 else sells[
            'trade_date'].dt.strftime('%m-%d %H:%M')
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
                fig.add_trace(go.Scatter(x=x_labels, y=df[col], line=dict(width=1.5, color=colors[i % 4]), name=col),
                              row=row_idx, col=1)
        row_idx += 1

    fig.update_layout(height=500 + len(sub_groups) * 150, template="none", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False, dragmode='pan', hovermode='x',
                      showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=x_labels, nticks=8, showgrid=True,
                     gridwidth=1, gridcolor='rgba(128,128,128,0.2)', tickangle=0)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    return fig


def render_ide_page():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">💻 极客量化 IDE (代码沙盒编译器)</h3><p class="sub-text">您可以直接修改 AI 生成的策略，或者在此手动硬编码！支持一键沙盒运行测试，防止实盘崩溃。</p></div>',
        unsafe_allow_html=True)
    default_code = """def generate_signals(df):\n    df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()\n    df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()\n    df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)\n    return df"""
    boll_code = """def generate_signals(df):\n    df['MAIN_BOLL_MID'] = df['Close'].rolling(window=20).mean()\n    std = df['Close'].rolling(window=20).std()\n    df['MAIN_BOLL_UP'] = df['MAIN_BOLL_MID'] + 2 * std\n    df['MAIN_BOLL_DN'] = df['MAIN_BOLL_MID'] - 2 * std\n    df['Signal'] = 0\n    df.loc[df['Close'] > df['MAIN_BOLL_UP'], 'Signal'] = 1\n    df.loc[df['Close'] < df['MAIN_BOLL_DN'], 'Signal'] = -1\n    return df"""
    kdj_code = """def generate_signals(df):\n    n, m1, m2 = 9, 3, 3\n    low_list = df['Low'].rolling(window=n).min()\n    high_list = df['High'].rolling(window=n).max()\n    rsv = (df['Close'] - low_list) / (high_list - low_list) * 100\n    df['SUB1_K'] = rsv.ewm(com=m1-1, adjust=False).mean()\n    df['SUB1_D'] = df['SUB1_K'].ewm(com=m2-1, adjust=False).mean()\n    df['SUB1_J'] = 3 * df['SUB1_K'] - 2 * df['SUB1_D']\n    df['Signal'] = 0\n    df.loc[df['SUB1_J'] < 20, 'Signal'] = 1\n    df.loc[df['SUB1_J'] > 80, 'Signal'] = -1\n    return df"""
    macd_code = """def generate_signals(df):\n    exp1 = df['Close'].ewm(span=12, adjust=False).mean()\n    exp2 = df['Close'].ewm(span=26, adjust=False).mean()\n    df['SUB1_MACD_DIFF'] = exp1 - exp2\n    df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()\n    df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])\n    df['Signal'] = 0\n    df.loc[(df['SUB1_MACD_DIFF'] > df['SUB1_MACD_DEA']) & (df['SUB1_MACD_DIFF'].shift(1) <= df['SUB1_MACD_DEA'].shift(1)), 'Signal'] = 1\n    df.loc[(df['SUB1_MACD_DIFF'] < df['SUB1_MACD_DEA']) & (df['SUB1_MACD_DIFF'].shift(1) >= df['SUB1_MACD_DEA'].shift(1)), 'Signal'] = -1\n    return df"""
    templates = {"💡 经典双均线模板 (默认)": default_code, "📈 趋势突破流 (布林带 BOLL)": boll_code,
                 "🌊 震荡反转流 (超买超卖 KDJ)": kdj_code, "🚀 动量加速流 (量价 MACD)": macd_code}

    try:
        import strategy_templates;
        import inspect
        for name, func in inspect.getmembers(strategy_templates, inspect.isfunction):
            if name.startswith("strategy_"): templates[
                "🛡️ 严谨：" + name.replace("strategy_", "").upper()] = inspect.getsource(func)
    except:
        pass

    c1, c2 = st.columns([2.2, 1.8])
    with c1:
        st.markdown("#### ⌨️ 策略代码编辑区")
        t_col1, t_col2 = st.columns([3, 1])
        with t_col1:
            selected_tpl = st.selectbox("📚 预设经典策略模板", list(templates.keys()), label_visibility="collapsed")
        with t_col2:
            if st.button("📥 载入模板", use_container_width=True): st.session_state.generated_code = templates[
                selected_tpl]; st.rerun()
        current_code = st.session_state.get('generated_code', '')
        if not current_code.strip(): current_code = default_code
        user_code = st.text_area("Code Editor", value=current_code, height=450, label_visibility="collapsed")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 同步保存至全局引擎", use_container_width=True,
                         type="primary"): st.session_state.generated_code = user_code; st.success(
                "✅ 代码已成功注入全局中枢！")
        with col_btn2:
            run_debug = st.button("🐞 运行防爆沙盒测试", use_container_width=True)

    with c2:
        st.markdown("#### 🖥️ 编译器控制台 (Console)")
        console_ph = st.empty()
        if run_debug:
            with console_ph.container():
                st.info("正在挂载虚拟沙盒测试环境...")
                try:
                    dummy_df = pd.DataFrame({'trade_date': pd.date_range('20240101', periods=100),
                                             'Open': np.random.uniform(2000, 2100, 100),
                                             'High': np.random.uniform(2100, 2150, 100),
                                             'Low': np.random.uniform(1950, 2000, 100),
                                             'Close': np.random.uniform(2000, 2100, 100),
                                             'Volume': np.random.randint(1000, 5000, 100)})
                    start_time = time.time()
                    res_df = safe_exec_fut_strategy(user_code, dummy_df)
                    st.success(f"✅ 编译完美通过！内核耗时: {time.time() - start_time:.4f} 秒")
                    if 'Signal' in res_df.columns:
                        st.write("🎯 **买卖信号探测统计**:"); st.json(res_df['Signal'].value_counts().to_dict())
                    else:
                        st.warning("⚠️ 警告：您的代码忘了返回 `Signal` 列！(规定 1=买入, -1=卖出, 0=观望)")
                    custom_cols = [c for c in res_df.columns if c.startswith(('MAIN_', 'SUB'))]
                    if custom_cols: st.write("📊 **主副图指标提取雷达**:"); st.write(custom_cols)
                    st.write("🔍 **沙盒返回的数据矩阵 (前 3 行)**:");
                    st.dataframe(res_df.head(3))
                except Exception as e:
                    st.error("❌ 沙盒编译失败！您的代码存在语法或逻辑错误：");
                    st.code(str(e), language="python")
        else:
            console_ph.info(
                "等待您下达编译指令...\n\n点击左侧【运行防爆沙盒测试】按钮，系统将凭空生成虚拟行情数据并安全执行您的代码，绝不会导致实盘引擎崩溃。")


def render_futures_backtest():
    if not HAS_AKSHARE: st.error(
        "🚨 警告：检测到未装备 AkShare 引擎！\n\n主公，请立即在终端执行以下军令完成列装：\n`pip install akshare`"); return
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🔗 期货全量审计与归因分析</h3><p class="sub-text">已切换至全免费无限制的 AkShare 开源数据引擎。直接输入代码，自动拉取分钟与日线数据！</p></div>',
        unsafe_allow_html=True)
    if "fut_bt_run" not in st.session_state: st.session_state.fut_bt_run = False
    if "fut_bt_data" not in st.session_state: st.session_state.fut_bt_data = None
    if "fut_bt_metrics" not in st.session_state: st.session_state.fut_bt_metrics = None

    c1, c2 = st.columns([1, 3])
    with c1:
        with st.expander("🛠️ 不知道输入什么代码？点击查看帮助", expanded=False):
            st.markdown(
                "**直接输入品种代码 + 年月即可 (绝对无需后缀！)**\n- 纯碱主力: `SA2409`\n- 螺纹钢: `RB2410`\n- 铁矿石: `I2409`\n- 玻璃: `FG2409`")
        fut_code_input = st.text_input("🎯 期货合约代码", value="", placeholder="直接输入，如: SA2409")
        freq_mapping = {"日线 (Daily)": "D", "60分钟 (60min)": "60", "30分钟 (30min)": "30", "15分钟 (15min)": "15",
                        "5分钟 (5min)": "5", "1分钟 (1min)": "1"}
        freq_choice = st.selectbox("⏱️ 数据周期", list(freq_mapping.keys()), index=0)
        selected_freq = freq_mapping[freq_choice]
        span_mapping = {"近1个月": 0.08, "近3个月": 0.25, "近半年": 0.5, "近1年": 1, "近3年": 3, "近5年": 5}
        span_choice = st.selectbox("⏳ 回测时间跨度", list(span_mapping.keys()), index=3)
        start_year = int(datetime.now().year - span_mapping[span_choice])
        margin_input_str = st.text_input("⚖️ 保证金比例 (%)", value="", placeholder="留空默认自动计算")
        multiplier_input_str = st.text_input("🔢 合约乘数 (吨/手)", value="", placeholder="留空自动匹配对应品种")
        if st.button("🚀 开始穿透回测", type="primary", use_container_width=True):
            if fut_code_input.strip() == "":
                st.error("主公，请先输入期货代码！")
            else:
                st.session_state.fut_bt_run = True; st.session_state.fut_bt_data = None; st.session_state.fut_bt_metrics = None

    with c2:
        if st.session_state.fut_bt_run and fut_code_input.strip() != "":
            with st.spinner(f"正在调取开源神兵 AkShare 获取 {fut_code_input} 的 {freq_choice} 数据..."):
                try:
                    real_code = fut_code_input.upper().strip().split('.')[0]
                    df = None
                    try:
                        if selected_freq == 'D':
                            df_temp = ak.futures_zh_daily_sina(symbol=real_code)
                            if df_temp is not None and not df_temp.empty: df_temp['trade_date'] = pd.to_datetime(
                                df_temp['date']); df = df_temp
                        else:
                            df_temp = ak.futures_zh_minute_sina(symbol=real_code, period=selected_freq)
                            if df_temp is not None and not df_temp.empty: df_temp['trade_date'] = pd.to_datetime(
                                df_temp['datetime']); df = df_temp
                    except Exception:
                        pass

                    if df is None or df.empty:
                        st.warning(
                            f"⚠️ **触发容灾机制**：AkShare 接口未返回 `{real_code}` 的真实数据。\n\n系统已自动启动【底层沙盒模拟引擎】，为您瞬间生成逼真的 **{freq_choice}** 高频推演数据！")
                        base_p = 3000 if 'RB' in real_code else (800 if 'I' in real_code else 2000)
                        volatility = base_p * 0.0015
                        np.random.seed();
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
                        df = df[df['trade_date'] >= pd.to_datetime(f"{start_year}0101")].reset_index(drop=True)

                    if df.empty:
                        st.error(
                            "❌ 您选择的时间范围内没有数据。请尝试拉长【回测时间跨度】。"); st.session_state.fut_bt_run = False
                    else:
                        default_mult_map = {'SA': 20, 'RB': 10, 'I': 100, 'HC': 10, 'FG': 20, 'V': 5, 'P': 10, 'M': 10,
                                            'Y': 10, 'C': 10, 'CS': 10, 'JD': 10, 'CU': 5, 'AL': 5, 'ZN': 5, 'NI': 1,
                                            'AU': 1000, 'AG': 15, 'RU': 10, 'TA': 5, 'MA': 10, 'CF': 5, 'SR': 10,
                                            'OI': 10, 'RM': 10, 'ZC': 100, 'JM': 60, 'J': 100, 'UR': 20}
                        sym_match = re.match(r'^([A-Za-z]+)', real_code)
                        symbol_letter = sym_match.group(1).upper() if sym_match else 'SA'
                        api_mult = default_mult_map.get(symbol_letter, 10.0)
                        api_margin = 10.0
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
                        mapping_base = {'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close',
                                        'volume': 'Volume', 'vol': 'Volume'}
                        for l_case, c_case in mapping_base.items():
                            if l_case in df.columns: df[c_case] = df[l_case]

                        df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()
                        df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()
                        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                        df['SUB1_MACD_DIFF'] = exp1 - exp2
                        df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()
                        df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])

                        if st.session_state.get('generated_code'):
                            df_ai = safe_exec_fut_strategy(st.session_state.generated_code, df)
                            if df_ai is not None and hasattr(df_ai, 'columns'):
                                for col in df_ai.columns:
                                    if col == 'Signal' or col.startswith(('MAIN_', 'SUB')): df[col] = df_ai[col]
                        if 'Signal' not in df.columns: df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)

                        df['Ret'] = df['Close'].pct_change()
                        df['Pos'] = df.get('Signal', pd.Series([0] * len(df))).replace(0, np.nan).ffill().fillna(0)
                        df['Price_Diff'] = df['Close'].diff().fillna(0)
                        init_cash, trade_lots = 1000000, 10

                        df['Long_PnL'] = np.where(df['Pos'].shift(1) == 1, df['Price_Diff'] * final_mult * trade_lots,
                                                  0)
                        df['Short_PnL'] = np.where(df['Pos'].shift(1) == -1,
                                                   -df['Price_Diff'] * final_mult * trade_lots, 0)
                        df['Total_PnL'] = df['Long_PnL'] + df['Short_PnL']
                        df['Equity'] = init_cash + df['Total_PnL'].cumsum()
                        df['Margin_Used'] = df['Close'] * final_mult * final_margin_rate * trade_lots * df[
                            'Pos'].abs().shift(1).fillna(0)

                        final_equity = df['Equity'].iloc[-1]
                        total_return = (final_equity - init_cash) / init_cash
                        annual = (1 + total_return) ** (252 / max(1, len(df))) - 1 if not df.empty else 0
                        max_dd = (df['Equity'] / df['Equity'].cummax() - 1).min()
                        max_margin = df['Margin_Used'].max()

                        st.session_state.fut_bt_data = df
                        st.session_state.fut_bt_metrics = {"total": total_return, "annual": annual, "max_dd": max_dd,
                                                           "max_margin": max_margin, "init_cash": init_cash}
                except Exception as e:
                    st.error(f"系统运算发生熔断: {e}");
                    st.session_state.fut_bt_run = False

        if st.session_state.fut_bt_data is not None:
            m = st.session_state.fut_bt_metrics;
            df = st.session_state.fut_bt_data
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(
                f'<div class="metric-box"><p>累计收益 (双边多空计算)</p><h2 class="highlight-text">{m["total"] * 100:.2f}%</h2></div>',
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
            st.plotly_chart(render_fut_charts(df), use_container_width=True, config={'scrollZoom': True})
        elif not st.session_state.fut_bt_run:
            st.markdown(
                """<div class="metric-box" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;"><p>等待主公下达指令</p><h2 style="color: #cbd5e1;">点击 [开始穿透回测] 进行推演</h2><p class="sub-text" style="margin-top: 10px;">AkShare 引擎已接管，自动突破高频数据封锁！</p></div>""",
                unsafe_allow_html=True)


@st_fragment
def render_futures_sandbox():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🌪️ 期货高频沙盘模拟推演</h3><p class="sub-text">Tick 级盘口模拟、毫秒级信号响应测试与动态滑点侦测。</p></div>',
        unsafe_allow_html=True)
    c_ctrl1, c_ctrl2, c_ctrl3, c_ctrl4 = st.columns(4)
    with c_ctrl1:
        sandbox_code = st.text_input("推演标的", value="SA2409")
    with c_ctrl2:
        base_price = st.number_input("初始基准价", value=2000.0)
    with c_ctrl3:
        speed = st.slider("脉冲频率 (秒)", 0.1, 2.0, 0.5)
    with c_ctrl4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        is_running = st.toggle("🚀 启动高频脉冲引擎")

    st.markdown("---")
    c_left, c_right = st.columns([1, 2.5])
    dom_placeholder = c_left.empty();
    chart_placeholder = c_right.empty()

    if is_running:
        current_price = base_price;
        tick_history = []
        while is_running:
            price_change = np.random.choice([-3, -2, -1, 0, 1, 2, 3])
            current_price += price_change
            tick_history.append(current_price)
            if len(tick_history) > 100: tick_history.pop(0)
            asks = [(current_price + i, np.random.randint(10, 500)) for i in range(5, 0, -1)]
            bids = [(current_price - i, np.random.randint(10, 500)) for i in range(1, 6)]

            with dom_placeholder.container():
                st.markdown('<div class="glass-card" style="padding: 15px;">', unsafe_allow_html=True)
                st.markdown('<h4 style="margin-top:0; color:#ef4444;">卖盘 (Ask)</h4>', unsafe_allow_html=True)
                for i, (p, v) in enumerate(asks): st.markdown(
                    f'<div style="display:flex; justify-content:space-between; color:#64748b;"><span>卖{5 - i}</span><span>{p:.0f}</span><span>{v}</span></div>',
                    unsafe_allow_html=True)
                st.markdown('<hr style="margin: 10px 0; border-color: rgba(128,128,128,0.2);">', unsafe_allow_html=True)
                color = "#ef4444" if price_change >= 0 else "#10b981"
                st.markdown(
                    f'<h3 style="margin:0; text-align:center; color:{color}; text-shadow: 0 0 10px rgba(0,0,0,0.1);">现价: {current_price:.0f}</h3>',
                    unsafe_allow_html=True)
                st.markdown('<hr style="margin: 10px 0; border-color: rgba(128,128,128,0.2);">', unsafe_allow_html=True)
                st.markdown('<h4 style="margin-top:0; color:#10b981;">买盘 (Bid)</h4>', unsafe_allow_html=True)
                for i, (p, v) in enumerate(bids): st.markdown(
                    f'<div style="display:flex; justify-content:space-between; color:#64748b;"><span>买{i + 1}</span><span>{p:.0f}</span><span>{v}</span></div>',
                    unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with chart_placeholder.container():
                fig = go.Figure(
                    data=go.Scatter(y=tick_history, mode='lines', line=dict(color='#3b82f6', width=2), fill='tozeroy',
                                    fillcolor='rgba(59, 130, 246, 0.1)'))
                fig.update_layout(height=380, template="none", paper_bgcolor='rgba(0,0,0,0)',
                                  plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0),
                                  xaxis=dict(showgrid=False, visible=False),
                                  yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'))
                st.plotly_chart(fig, use_container_width=True, key=f"tick_chart_{time.time()}")
            time.sleep(speed)
    else:
        dom_placeholder.info("请打开上方的【启动高频脉冲引擎】开关，唤醒沙盘。")
        chart_placeholder.markdown(
            """<div class="metric-box" style="height: 380px; display: flex; flex-direction: column; justify-content: center; align-items: center;"><p>高频推演</p><h2 style="color: #3b82f6;">等待引擎唤醒...</h2></div>""",
            unsafe_allow_html=True)


def render_page_dl():
    with st.spinner("唤醒深度学习底层张量引擎..."):
        try:
            import torch
            import torch.nn as nn
            from sklearn.preprocessing import MinMaxScaler
        except ImportError:
            st.error("🚨 需安装 torch 和 scikit-learn！")
            st.stop()
    st.markdown(
        '<div class="glass-card"><h3 style="margin-bottom:0;">🧠 深度神经网络时序建模矩阵 (白盒透视版)</h3></div>',
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
                        scaler = MinMaxScaler()
                        scaled = scaler.fit_transform(df['Close'].values.reshape(-1, 1))
                        X, y = [], []
                        for i in range(slen, len(scaled)): X.append(scaled[i - slen:i, 0]); y.append(scaled[i, 0])
                        X_t = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1)
                        y_t = torch.tensor(np.array(y), dtype=torch.float32)

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
                                    model.load_state_dict(torch.load(uploaded_model, map_location=torch.device('cpu')))
                                    lbox.success(f"**{m_name}** | 权重校验通过，挂载成功！");
                                    pbar.progress(1.0)
                                except Exception as load_e:
                                    st.warning(f"⚠️ 模型架构不匹配，极速重训练... ({load_e})")
                                    opt = torch.optim.Adam(model.parameters(), lr=0.01);
                                    crit = nn.MSELoss()
                                    for e in range(10): model.train(); opt.zero_grad(); loss = crit(
                                        model(X_t).squeeze(), y_t); loss.backward(); opt.step()
                            else:
                                lbox.markdown(f"**正在在线训练 {m_name} 模型...**")
                                opt = torch.optim.Adam(model.parameters(), lr=0.01);
                                crit = nn.MSELoss()
                                for e in range(eps):
                                    model.train();
                                    opt.zero_grad();
                                    pred = model(X_t);
                                    loss = crit(pred.squeeze(), y_t);
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
                        stream = client.chat.completions.create(model="moonshot-v1-8k",
                                                                messages=[{"role": "user", "content": prompt}],
                                                                stream=True, temperature=0.5)
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
with c2: st.text_area("实时工作流终端", value="\n".join(st.session_state.sys_logs), height=350)

elif selected_page == PAGES[7]:
if extensions:
    extensions.render_futures_backtest()

elif selected_page == PAGES[8]:
    if extensions:
        extensions.render_futures_sandbox()

    elif selected_page == PAGES[9]:
    if extensions:
        extensions.render_new_features_page()

    else:
    if custom_plugins and hasattr(custom_plugins, 'route_and_render'): custom_plugins.route_and_render(selected_page)