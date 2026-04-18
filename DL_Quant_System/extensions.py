# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：极客 IDE、AkShare 期货、高频沙盘
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import time
import traceback
import math
import re
import json
import pandas as pd
import numpy as np
from datetime import datetime

# 🔥 提速核武 3：安全兼容版 Fragment 装饰器，实现沙盘无闪烁局部刷新 🔥
try:
    from streamlit import fragment as st_fragment
except ImportError:
    try:
        from streamlit import experimental_fragment as st_fragment
    except ImportError:
        # 如果用户的 Streamlit 版本太低，则降级为普通函数，确保代码绝不报错
        st_fragment = lambda f: f

# 引入开源神兵 AkShare
try:
    import akshare as ak

    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

SUB_PATTERN = re.compile(r'^SUB(\d+)_')


def summon_global_3d_lulu():
    """终极寄生版：支持多模型切换、右键自定义菜单屏蔽原生下载"""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # ====================================================================
    # 🔥 预留空间：主公，以后有新模型，只需要加在这个字典里，并把文件放进来！🔥
    # ====================================================================
    PET_ROSTER = {
        "🍊 水豚噜噜": "lulu.glb",
        "🐧 极客企鹅": "penguin.glb",
        "🤖 量化机甲 (预留)": "robot.glb",
        "🐱 招财猫 (预留)": "cat.glb"
    }

    pet_b64_data = {}
    has_any_pet = False

    with st.spinner("正在为雷达加装白名单与多维宇宙识别系统..."):
        for pet_name, file_name in PET_ROSTER.items():
            file_path = os.path.join(current_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    pet_b64_data[pet_name] = base64.b64encode(f.read()).decode("utf-8")
                    has_any_pet = True
            else:
                pet_b64_data[pet_name] = ""  # 找不到文件就置空，菜单里点它会有提示

    if not has_any_pet:
        return

    # 将字典转为 JSON 字符串，准备注入 JS
    pets_json_str = json.dumps(pet_b64_data)

    # 为了防止 f-string 中的大括号与 JS 冲突，我们使用 replace 的方式注入 HTML
    html_template = """
    <script>
        const parentWin = window.parent;
        const parentDoc = parentWin.document;

        if (!parentWin.__LULU_INITIALIZED__) {
            parentWin.__LULU_INITIALIZED__ = true;

            // 注入模型数据字典
            const modelsData = __PETS_JSON_DATA__;

            const loadScript = (src) => new Promise((res) => {
                const s = parentDoc.createElement('script');
                s.src = src; s.onload = res; parentDoc.head.appendChild(s);
            });

            const initLulu = async () => {
                await loadScript("https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js");
                await loadScript("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js");

                const script = parentDoc.createElement('script');
                script.innerHTML = `
                    (function() {
                        const THREE = window.THREE;
                        const win = window;
                        const doc = document;
                        const petData = window.parent.__PETS_JSON_DATA__ || ${JSON.stringify(modelsData)};

                        let state = 'IDLE'; 
                        let danceTimer = 0;
                        let lastActivityTime = Date.now();
                        let idleActionState = 'NONE'; 
                        let idleActionTimer = 0;

                        const petSize = 280; 
                        const overflowLimit = 80; 

                        // -------------------- UI 容器构建 --------------------
                        const petBox = doc.createElement('div');
                        petBox.id = 'lulu-global-pet';
                        petBox.style.cssText = "position: fixed; bottom: 20px; right: 20px; width: " + petSize + "px; height: " + petSize + "px; z-index: 9999999; cursor: grab; user-select: none; pointer-events: none; transition: transform 0.2s; touch-action: none;"; 
                        doc.body.appendChild(petBox);

                        const bubble = doc.createElement('div');
                        bubble.style.cssText = "position: absolute; top: 0px; left: 50%; transform: translateX(-50%); opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #00ffcc; color: #fff; padding: 8px 15px; border-radius: 12px; font-size: 14px; white-space: nowrap; transition: opacity 0.3s; pointer-events: none; box-shadow: 0 4px 12px rgba(0,255,204,0.3); z-index: 10;";
                        petBox.appendChild(bubble);

                        // -------------------- 自定义右键菜单构建 --------------------
                        const ctxMenu = doc.createElement('div');
                        ctxMenu.style.cssText = "position: fixed; display: none; background: rgba(15, 23, 35, 0.95); border: 1px solid rgba(0, 255, 204, 0.5); border-radius: 12px; padding: 6px; z-index: 10000000; color: #fff; font-size: 14px; min-width: 140px; box-shadow: 0 8px 24px rgba(0,0,0,0.8); backdrop-filter: blur(10px);";
                        doc.body.appendChild(ctxMenu);

                        const menuTitle = doc.createElement('div');
                        menuTitle.innerHTML = "<b>✨ 召唤伙伴</b>";
                        menuTitle.style.cssText = "padding: 6px 12px; color: #8b9bb4; font-size: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 4px; pointer-events: none;";
                        ctxMenu.appendChild(menuTitle);

                        Object.keys(petData).forEach(petName => {
                            const item = doc.createElement('div');
                            item.innerText = petName;
                            item.style.cssText = "padding: 8px 12px; cursor: pointer; border-radius: 6px; transition: 0.2s; margin-bottom: 2px;";
                            item.onmouseover = () => { item.style.background = "rgba(0, 255, 204, 0.2)"; item.style.color = "#00ffcc"; };
                            item.onmouseout = () => { item.style.background = "transparent"; item.style.color = "#fff"; };

                            item.onclick = (e) => {
                                e.stopPropagation();
                                ctxMenu.style.display = 'none';
                                if(petData[petName] !== "") {
                                    switchModel(petData[petName], petName);
                                } else {
                                    doSpeak(["主公，【" + petName + "】的模型文件还没放入军营哦！"]);
                                }
                            };
                            ctxMenu.appendChild(item);
                        });

                        // -------------------- 3D 场景初始化 --------------------
                        const scene = new THREE.Scene();
                        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                        camera.position.set(0, 0.8, 5.5); 

                        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: win.innerWidth > 768 });
                        renderer.setSize(petSize, petSize);
                        renderer.setPixelRatio(win.devicePixelRatio ? Math.min(win.devicePixelRatio, 2) : 1);
                        renderer.outputEncoding = THREE.sRGBEncoding;
                        petBox.appendChild(renderer.domElement);

                        const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
                        scene.add(ambientLight);
                        const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
                        dirLight.position.set(5, 10, 5);
                        scene.add(dirLight);

                        let currentModelObj = null; 
                        let mixer = null;
                        let targetRotY = 0; 
                        let targetRotX = 0;
                        let clickableMeshes = [];

                        const loader = new THREE.GLTFLoader();

                        // 🔥 无缝切换模型的核心函数 🔥
                        const switchModel = (b64String, name) => {
                            if(currentModelObj) {
                                scene.remove(currentModelObj);
                                clickableMeshes = [];
                                mixer = null;
                            }
                            loader.load("data:application/octet-stream;base64," + b64String, (gltf) => {
                                currentModelObj = gltf.scene;
                                currentModelObj.position.set(0, -1.2, 0); 

                                currentModelObj.traverse((child) => {
                                    if (child.isMesh) {
                                        let isTrash = false;
                                        if (child.material) {
                                            if (child.material.transparent && child.material.opacity < 0.1) isTrash = true;
                                            if (child.material.opacity === 0) isTrash = true;
                                        }
                                        if (isTrash) { child.visible = false; } 
                                        else { clickableMeshes.push(child); }
                                    }
                                });
                                scene.add(currentModelObj);
                                if (gltf.animations.length > 0) {
                                    mixer = new THREE.AnimationMixer(currentModelObj);
                                    mixer.clipAction(gltf.animations[0]).play();
                                }
                                if(name) doSpeak(["变身完成！我是" + name + " 😎"]);
                            });
                        };

                        // 首次启动：自动加载字典里第一个有数据的模型
                        const initialPetKey = Object.keys(petData).find(k => petData[k] !== "");
                        if(initialPetKey) {
                            switchModel(petData[initialPetKey], null);
                        }

                        // -------------------- 交互逻辑与射线检测 --------------------
                        const raycaster = new THREE.Raycaster();
                        const mouseNDC = new THREE.Vector2();

                        const checkHit = (clientX, clientY) => {
                            if (clickableMeshes.length === 0) return false;
                            const rect = renderer.domElement.getBoundingClientRect();
                            if (clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) { return false; }
                            mouseNDC.x = ((clientX - rect.left) / petSize) * 2 - 1;
                            mouseNDC.y = -((clientY - rect.top) / petSize) * 2 + 1;
                            raycaster.setFromCamera(mouseNDC, camera);
                            const intersects = raycaster.intersectObjects(clickableMeshes, false);
                            return intersects.length > 0; 
                        };

                        const updateLookAt = (clientX, clientY) => {
                            lastActivityTime = Date.now();
                            if (state === 'IDLE' && idleActionState === 'NONE') {
                                const mouseX = (clientX / win.innerWidth) * 2 - 1;
                                const mouseY = -(clientY / win.innerHeight) * 2 + 1;
                                targetRotY = mouseX * 0.8; targetRotX = -mouseY * 0.4;
                            }
                        };

                        const clock = new THREE.Clock();
                        function animate() {
                            win.requestAnimationFrame(animate);
                            const delta = clock.getDelta();
                            const time = clock.getElapsedTime();
                            if (mixer) mixer.update(delta);
                            const now = Date.now();

                            if (state === 'IDLE' && idleActionState === 'NONE') {
                                if (now - lastActivityTime > 30000) { 
                                    const actions = ['HOP', 'LOOK_AROUND', 'SPEAK'];
                                    const act = actions[Math.floor(Math.random() * actions.length)];
                                    idleActionState = act; idleActionTimer = 2.5; lastActivityTime = now; 
                                    if (act === 'SPEAK') {
                                        doSpeak(["主公，您睡着了吗？🦦", "盯盘好累喔，发呆中...", "呼噜噜...💤"]);
                                        idleActionState = 'NONE'; 
                                    }
                                }
                            }

                            if (currentModelObj) {
                                if (state === 'STRUGGLING') {
                                    currentModelObj.rotation.y = 0; currentModelObj.rotation.x = 0;
                                    currentModelObj.position.x = Math.sin(time * 50) * 0.05;
                                    currentModelObj.rotation.z = Math.cos(time * 50) * 0.1;
                                    currentModelObj.position.y = -1.2;
                                } else if (state === 'DANCING') {
                                    currentModelObj.position.y = -1.2 + Math.abs(Math.sin(time * 10)) * 0.5;
                                    currentModelObj.rotation.y += 0.2; currentModelObj.rotation.x = 0; currentModelObj.rotation.z = 0; currentModelObj.position.x = 0;
                                    danceTimer -= delta;
                                    if (danceTimer <= 0) { state = 'IDLE'; currentModelObj.position.y = -1.2; }
                                } else if (idleActionState === 'HOP') {
                                    currentModelObj.position.y = -1.2 + Math.abs(Math.sin(time * 15)) * 0.3;
                                    currentModelObj.rotation.x = 0; currentModelObj.rotation.y = 0;
                                    idleActionTimer -= delta;
                                    if (idleActionTimer <= 0) { idleActionState = 'NONE'; currentModelObj.position.y = -1.2; }
                                } else if (idleActionState === 'LOOK_AROUND') {
                                    currentModelObj.rotation.y = Math.sin(time * 3) * 0.6; currentModelObj.rotation.x = 0;
                                    idleActionTimer -= delta;
                                    if (idleActionTimer <= 0) { idleActionState = 'NONE'; currentModelObj.rotation.y = targetRotY; }
                                } else {
                                    currentModelObj.position.y = -1.2 + Math.sin(time * 2) * 0.02;
                                    currentModelObj.position.x = 0; currentModelObj.rotation.z = 0;
                                    currentModelObj.rotation.y += (targetRotY - currentModelObj.rotation.y) * 0.1;
                                    currentModelObj.rotation.x += (targetRotX - currentModelObj.rotation.x) * 0.1;
                                }
                            }
                            renderer.render(scene, camera);
                        }

                        let isDragging = false, initX, initY, startL, startT, isPossibleClick = false, isHolding = false, clickTimeout = null, lastTapTime = 0;
                        const getX = (e) => e.touches ? e.touches[0].clientX : e.clientX;
                        const getY = (e) => e.touches ? e.touches[0].clientY : e.clientY;

                        const doSpeak = (customTexts) => {
                            const ts = customTexts || ["主公，我在这呢！🥰", "量化大赚！吃橘子！🍊", "右键可以给我换衣服哦~", "今天赚了多少呀？💸"];
                            bubble.innerText = ts[Math.floor(Math.random() * ts.length)]; bubble.style.opacity = '1';
                            setTimeout(() => { bubble.style.opacity = '0'; }, 3000);
                        };

                        const doDance = () => {
                            state = 'DANCING'; danceTimer = 3.0; lastActivityTime = Date.now();
                            bubble.innerText = "好耶！开心转圈圈！💃🕺"; bubble.style.opacity = '1';
                            setTimeout(() => { bubble.style.opacity = '0'; }, 3000);
                        };

                        const startInteraction = (e) => {
                            if(e.button === 2) return; // 🔥 拦截右键，禁止右键拖拽 🔥
                            isHolding = true; initX = getX(e); initY = getY(e);
                            const r = petBox.getBoundingClientRect(); startL = r.left; startT = r.top;
                            isDragging = false; isPossibleClick = true; 
                            petBox.style.bottom = 'auto'; petBox.style.right = 'auto'; petBox.style.left = startL + 'px'; petBox.style.top = startT + 'px';
                        };

                        // 🔥 绑定自定义右键菜单事件，彻底屏蔽原生浏览器菜单 🔥
                        petBox.addEventListener('contextmenu', (e) => {
                            e.preventDefault(); 
                            ctxMenu.style.display = 'block';
                            ctxMenu.style.left = (e.clientX + 10) + 'px';
                            ctxMenu.style.top = (e.clientY - 10) + 'px';
                        });

                        // 点击其他空白处关闭菜单
                        doc.addEventListener('click', (e) => {
                            if (e.button !== 2) { ctxMenu.style.display = 'none'; }
                        });

                        win.addEventListener('mousemove', (e) => {
                            if (isHolding) {
                                const curX = getX(e); const curY = getY(e);
                                const moveDist = Math.sqrt(Math.pow(curX - initX, 2) + Math.pow(curY - initY, 2));
                                if (moveDist > 20) { 
                                    if (!isDragging) {
                                        isDragging = true; isPossibleClick = false; state = 'STRUGGLING'; idleActionState = 'NONE';
                                        petBox.style.cursor = 'grabbing'; petBox.style.transform = 'scale(1.05)'; petBox.style.transition = 'none'; 
                                    }
                                    let newLeft = startL + curX - initX; let newTop = startT + curY - initY;
                                    newLeft = Math.max(-overflowLimit, Math.min(newLeft, win.innerWidth - petSize + overflowLimit));
                                    newTop = Math.max(-overflowLimit, Math.min(newTop, win.innerHeight - petSize + overflowLimit));
                                    petBox.style.left = newLeft + 'px'; petBox.style.top = newTop + 'px';
                                    if(e.cancelable) e.preventDefault(); 
                                }
                                return;
                            }
                            updateLookAt(e.clientX, e.clientY);
                            if (checkHit(e.clientX, e.clientY)) {
                                if (petBox.style.pointerEvents !== 'auto') { petBox.style.pointerEvents = 'auto'; petBox.style.cursor = 'grab'; }
                            } else {
                                if (petBox.style.pointerEvents !== 'none') { petBox.style.pointerEvents = 'none'; }
                            }
                        }, true);

                        const endInteraction = (e) => {
                            if (!isHolding) return;
                            isHolding = false; petBox.style.transition = 'transform 0.2s'; petBox.style.cursor = 'grab'; petBox.style.transform = 'scale(1)'; lastActivityTime = Date.now();
                            if (isDragging) { isDragging = false; if (state !== 'DANCING') state = 'IDLE'; return; }
                            if (isPossibleClick) {
                                const currentTime = new Date().getTime(); const tapLength = currentTime - lastTapTime; clearTimeout(clickTimeout); 
                                if (tapLength < 350 && tapLength > 0) { doDance(); } else { clickTimeout = setTimeout(() => { doSpeak(); }, 300); }
                                lastTapTime = currentTime;
                            }
                        };

                        petBox.addEventListener('mousedown', startInteraction); doc.addEventListener('mouseup', endInteraction); doc.addEventListener('mouseleave', endInteraction);

                        doc.addEventListener('touchstart', (e) => {
                            if (checkHit(e.touches[0].clientX, e.touches[0].clientY)) {
                                petBox.style.pointerEvents = 'auto'; startInteraction(e); e.stopPropagation();
                            } else { petBox.style.pointerEvents = 'none'; }
                        }, { capture: true, passive: false });

                        doc.addEventListener('touchmove', (e) => {
                            if (isHolding) {
                                const curX = getX(e); const curY = getY(e); const moveDist = Math.sqrt(Math.pow(curX - initX, 2) + Math.pow(curY - initY, 2));
                                if (moveDist > 20) { 
                                    if (!isDragging) {
                                        isDragging = true; isPossibleClick = false; state = 'STRUGGLING'; idleActionState = 'NONE';
                                        petBox.style.cursor = 'grabbing'; petBox.style.transform = 'scale(1.05)'; petBox.style.transition = 'none'; 
                                    }
                                    let newLeft = startL + curX - initX; let newTop = startT + curY - initY;
                                    newLeft = Math.max(-overflowLimit, Math.min(newLeft, win.innerWidth - petSize + overflowLimit));
                                    newTop = Math.max(-overflowLimit, Math.min(newTop, win.innerHeight - petSize + overflowLimit));
                                    petBox.style.left = newLeft + 'px'; petBox.style.top = newTop + 'px';
                                    e.stopPropagation(); if(e.cancelable) e.preventDefault(); 
                                }
                            } else { updateLookAt(e.touches[0].clientX, e.touches[0].clientY); }
                        }, { passive: false });

                        doc.addEventListener('touchend', endInteraction); doc.addEventListener('touchcancel', endInteraction);
                        setTimeout(animate, 1500);
                    })();
                `;
                parentDoc.body.appendChild(script);
            };
            setTimeout(initLulu, 500); 
        }
    </script>
    """

    html_code = html_template.replace("__PETS_JSON_DATA__", pets_json_str)
    components.html(html_code, height=0, width=0)


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
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    main_inds = [c for c in df.columns if c.startswith('MAIN_')]
    sub_groups = {}
    for c in df.columns:
        gid = SUB_PATTERN.match(c)
        if gid:
            sub_groups.setdefault(gid.group(1), []).append(c)

    rows = 2 + len(sub_groups)
    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.5, 0.15] + [0.35 / max(1, len(sub_groups))] * len(sub_groups)
    )

    if df['trade_date'].dt.time.nunique() <= 1:
        x_labels = df['trade_date'].dt.strftime('%Y-%m-%d')
    else:
        x_labels = df['trade_date'].dt.strftime('%m-%d %H:%M')

    fig.add_trace(go.Candlestick(
        x=x_labels, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#FD1050', decreasing_line_color='#00FF00', name='K线'
    ), row=1, col=1)

    colors = ['#FFFF00', '#FF00FF', '#00FFFF', '#FFFFFF']
    for i, col in enumerate(main_inds):
        fig.add_trace(go.Scatter(x=x_labels, y=df[col], name=col, line=dict(color=colors[i % 4], width=1.2)), row=1,
                      col=1)

    if 'Signal' in df.columns:
        buys = df[df['Signal'] == 1]
        sells = df[df['Signal'] == -1]

        if df['trade_date'].dt.time.nunique() <= 1:
            buy_x = buys['trade_date'].dt.strftime('%Y-%m-%d')
            sell_x = sells['trade_date'].dt.strftime('%Y-%m-%d')
        else:
            buy_x = buys['trade_date'].dt.strftime('%m-%d %H:%M')
            sell_x = sells['trade_date'].dt.strftime('%m-%d %H:%M')

        fig.add_trace(go.Scatter(x=buy_x, y=buys['Low'] * 0.998, mode='markers',
                                 marker=dict(symbol='triangle-up', size=14, color='#00FFFF'), name='买'), row=1, col=1)
        fig.add_trace(go.Scatter(x=sell_x, y=sells['High'] * 1.002, mode='markers',
                                 marker=dict(symbol='triangle-down', size=14, color='#FF00FF'), name='卖'), row=1,
                      col=1)

    fig.add_trace(go.Bar(x=x_labels, y=df.get('Volume', np.zeros(len(df))),
                         marker_color=np.where(df['Close'] >= df['Open'], '#FD1050', '#00FF00')), row=2, col=1)

    row_idx = 3
    for gid in sorted(sub_groups.keys(), key=int):
        for i, col in enumerate(sub_groups[gid]):
            if 'HIST' in col.upper():
                fig.add_trace(go.Bar(x=x_labels, y=df[col], marker_color=np.where(df[col] >= 0, '#FD1050', '#00FF00')),
                              row=row_idx, col=1)
            else:
                fig.add_trace(go.Scatter(x=x_labels, y=df[col], line=dict(color=colors[i % 4])), row=row_idx, col=1)
        row_idx += 1

    fig.update_layout(height=500 + len(sub_groups) * 150, template="none", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=x_labels, nticks=8, showgrid=True,
                     gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    return fig


# ==========================================
# 🔥 核心引擎 1：极客量化 IDE (代码编译器)
# ==========================================
def render_ide_page():
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">💻 极客量化 IDE</h3></div>',
                unsafe_allow_html=True)

    # ---------------- 策略模板库 ----------------
    default_code = """def generate_signals(df):\n    df['MAIN_MA5'] = df['Close'].rolling(5).mean()\n    df['MAIN_MA20'] = df['Close'].rolling(20).mean()\n    df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)\n    return df"""

    boll_code = """def generate_signals(df):\n    # 1. 计算布林带三轨 (主图显示)\n    df['MAIN_BOLL_MID'] = df['Close'].rolling(window=20).mean()\n    std = df['Close'].rolling(window=20).std()\n    df['MAIN_BOLL_UP'] = df['MAIN_BOLL_MID'] + 2 * std\n    df['MAIN_BOLL_DN'] = df['MAIN_BOLL_MID'] - 2 * std\n    \n    # 2. 生成买卖信号\n    df['Signal'] = 0\n    df.loc[df['Close'] > df['MAIN_BOLL_UP'], 'Signal'] = 1\n    df.loc[df['Close'] < df['MAIN_BOLL_DN'], 'Signal'] = -1\n    return df"""

    kdj_code = """def generate_signals(df):\n    # 1. 手搓 KDJ 指标 (副图 1 显示)\n    n, m1, m2 = 9, 3, 3\n    low_list = df['Low'].rolling(window=n).min()\n    high_list = df['High'].rolling(window=n).max()\n    rsv = (df['Close'] - low_list) / (high_list - low_list) * 100\n    \n    df['SUB1_K'] = rsv.ewm(com=m1-1, adjust=False).mean()\n    df['SUB1_D'] = df['SUB1_K'].ewm(com=m2-1, adjust=False).mean()\n    df['SUB1_J'] = 3 * df['SUB1_K'] - 2 * df['SUB1_D']\n    \n    # 2. 生成买卖信号\n    df['Signal'] = 0\n    df.loc[df['SUB1_J'] < 20, 'Signal'] = 1\n    df.loc[df['SUB1_J'] > 80, 'Signal'] = -1\n    return df"""

    macd_code = """def generate_signals(df):\n    # 1. 计算 MACD (副图 1 显示，且包含 HIST 柱状图)\n    exp1 = df['Close'].ewm(span=12, adjust=False).mean()\n    exp2 = df['Close'].ewm(span=26, adjust=False).mean()\n    \n    df['SUB1_MACD_DIFF'] = exp1 - exp2\n    df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()\n    df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])\n    \n    # 2. 生成买卖信号\n    df['Signal'] = 0\n    df.loc[(df['SUB1_MACD_DIFF'] > df['SUB1_MACD_DEA']) & (df['SUB1_MACD_DIFF'].shift(1) <= df['SUB1_MACD_DEA'].shift(1)), 'Signal'] = 1\n    df.loc[(df['SUB1_MACD_DIFF'] < df['SUB1_MACD_DEA']) & (df['SUB1_MACD_DIFF'].shift(1) >= df['SUB1_MACD_DEA'].shift(1)), 'Signal'] = -1\n    return df"""

    templates = {
        "💡 空白双均线模板 (默认)": default_code,
        "📈 趋势突破流 (布林带 BOLL)": boll_code,
        "🌊 震荡反转流 (超买超卖 KDJ)": kdj_code,
        "🚀 动量加速流 (量价 MACD)": macd_code
    }

    # 动态抓取外部插件策略
    try:
        import strategy_templates
        import inspect
        for name, func in inspect.getmembers(strategy_templates, inspect.isfunction):
            if name.startswith("strategy_"):
                display_name = "🛡️ 严谨：" + name.replace("strategy_", "").upper()
                templates[display_name] = inspect.getsource(func)
    except ImportError:
        pass
    # --------------------------------------------

    c1, c2 = st.columns([2.2, 1.8])
    with c1:
        st.markdown("#### ⌨️ 策略代码区")

        t_col1, t_col2 = st.columns([3, 1])
        with t_col1:
            selected_tpl = st.selectbox("📚 新手村：加载经典开源模板", list(templates.keys()),
                                        label_visibility="collapsed")
        with t_col2:
            if st.button("📥 载入模板", use_container_width=True):
                st.session_state.generated_code = templates[selected_tpl]
                st.rerun()

        current_code = st.session_state.get('generated_code', '')
        if not current_code.strip():
            current_code = default_code

        user_code = st.text_area("Code", value=current_code, height=450, label_visibility="collapsed")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 同步保存至全局", type="primary", use_container_width=True):
                st.session_state.generated_code = user_code
                st.success("✅ 代码注入成功！")
        with col_btn2:
            run_debug = st.button("🐞 运行防爆测试", use_container_width=True)

    with c2:
        st.markdown("#### 🖥️ Console 日志")
        if run_debug:
            try:
                t0 = time.time()
                dummy_df = pd.DataFrame({
                    'trade_date': pd.date_range('20240101', periods=100),
                    'Open': np.random.uniform(2000, 2100, 100),
                    'High': np.random.uniform(2100, 2150, 100),
                    'Low': np.random.uniform(1950, 2000, 100),
                    'Close': np.random.uniform(2000, 2100, 100),
                    'Volume': np.random.randint(1000, 5000, 100)
                })
                res_df = safe_exec_fut_strategy(user_code, dummy_df)

                st.success(f"✅ 编译完美通过！耗时: {time.time() - t0:.4f} 秒")
                if 'Signal' in res_df.columns:
                    st.write("🎯 信号统计:")
                    st.json(res_df['Signal'].value_counts().to_dict())
                else:
                    st.warning("⚠️ 警告：未返回 `Signal` 列！")

                custom_cols = [c for c in res_df.columns if c.startswith(('MAIN_', 'SUB'))]
                if custom_cols:
                    st.write("📊 主副图指标提取雷达:")
                    st.write(custom_cols)
            except Exception as e:
                st.error("❌ 编译失败！")
                st.code(str(e), language="python")


def render_futures_backtest():
    if not HAS_AKSHARE:
        st.error("🚨 请在终端执行：`pip install akshare`")
        return

    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">🔗 期货全量审计</h3></div>',
                unsafe_allow_html=True)

    if "fut_bt_run" not in st.session_state:
        st.session_state.fut_bt_run = False

    c1, c2 = st.columns([1, 3])
    with c1:
        fut_code_input = st.text_input("代码", "")
        freq_map = {"日线": "D", "60分钟": "60", "30分钟": "30", "15分钟": "15", "5分钟": "5", "1分钟": "1"}
        freq_choice = st.selectbox("周期", list(freq_map.keys()), index=0)
        freq = freq_map[freq_choice]

        span_map = {"近1个月": 0.08, "近3个月": 0.25, "近半年": 0.5, "近1年": 1, "近3年": 3, "近5年": 5}
        start_year = int(datetime.now().year - span_map[st.selectbox("时间跨度", list(span_map.keys()), index=3)])
        start_date_str = f"{start_year}0101"

        margin_input = st.text_input("保证金率 (%)", value="", placeholder="留空默认自动计算")
        mult_input = st.text_input("合约乘数", value="", placeholder="留空自动匹配")

        if st.button("🚀 开始回测", type="primary", use_container_width=True):
            if fut_code_input.strip() == "":
                st.error("请输入代码！")
            else:
                st.session_state.fut_bt_run = True

    with c2:
        if st.session_state.fut_bt_run and fut_code_input.strip():
            with st.spinner("调用 AkShare..."):
                try:
                    real_code = fut_code_input.upper().strip().split('.')[0]
                    df = None
                    try:
                        if freq == 'D':
                            df = ak.futures_zh_daily_sina(symbol=real_code)
                        else:
                            df = ak.futures_zh_minute_sina(symbol=real_code, period=freq)
                    except Exception:
                        pass

                    if df is None or df.empty:
                        st.warning(f"⚠️ 容灾机制：未拉取到 `{real_code}` 真实数据。生成模拟高频数据。")
                        base_p = 3000 if 'RB' in real_code else 2000
                        closes_array = np.random.normal(0, base_p * 0.0015, 399).cumsum()
                        closes = base_p + np.insert(closes_array, 0, 0)

                        dates = pd.date_range(end=datetime.now(), periods=400,
                                              freq=freq.replace('m', 'T') if freq != 'D' else 'D')
                        df = pd.DataFrame({'datetime': dates, 'close': closes})
                        df['open'] = df['close'].shift(1).fillna(base_p)
                        df['high'] = df['close'] + 5
                        df['low'] = df['close'] - 5
                        df['volume'] = np.random.randint(1000, 5000, 400)

                    df.rename(columns={'datetime': 'trade_date', 'date': 'trade_date'}, inplace=True, errors='ignore')
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    df = df[df['trade_date'] >= pd.to_datetime(start_date_str)].reset_index(drop=True)

                    if df.empty:
                        st.error("❌ 所选时间范围内无数据。")
                        st.session_state.fut_bt_run = False
                    else:
                        df.rename(
                            columns=lambda x: x.capitalize() if x in ['open', 'high', 'low', 'close', 'volume'] else x,
                            inplace=True)

                        sym_match = re.match(r'^([A-Za-z]+)', real_code)
                        sym_letter = sym_match.group(1).upper() if sym_match else 'SA'

                        mult_map = {'SA': 20, 'RB': 10, 'I': 100, 'FG': 20, 'TA': 5, 'MA': 10, 'CF': 5, 'JM': 60,
                                    'J': 100, 'UR': 20}

                        f_margin = float(margin_input) / 100.0 if margin_input.strip() else 0.12
                        f_mult = float(mult_input) if mult_input.strip() else mult_map.get(sym_letter, 10.0)
                        st.success(f"✅ 挂载：**{real_code}**！乘数: **{f_mult}**, 保证金: **{f_margin * 100:.2f}%**")

                        df['MAIN_MA5'] = df['Close'].rolling(5).mean()
                        df['MAIN_MA20'] = df['Close'].rolling(20).mean()

                        if st.session_state.get('generated_code'):
                            try:
                                df = safe_exec_fut_strategy(st.session_state.generated_code, df)
                            except:
                                df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)
                        else:
                            df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)

                        df['Pos'] = df.get('Signal', pd.Series([0] * len(df))).replace(0, np.nan).ffill().fillna(0)

                        init_cash, lots = 1000000, 10
                        df['P_Diff'] = df['Close'].diff().fillna(0)
                        df['Long_PnL'] = np.where(df['Pos'].shift(1) == 1, df['P_Diff'] * f_mult * lots, 0)
                        df['Short_PnL'] = np.where(df['Pos'].shift(1) == -1, -df['P_Diff'] * f_mult * lots, 0)
                        df['Total_PnL'] = df['Long_PnL'] + df['Short_PnL']
                        df['Equity'] = init_cash + df['Total_PnL'].cumsum()
                        df['Margin'] = df['Close'] * f_mult * f_margin * lots * df['Pos'].abs().shift(1).fillna(0)

                        eq_end = df['Equity'].iloc[-1]
                        st.session_state.fut_bt_data = df
                        st.session_state.fut_bt_metrics = {
                            "total": (eq_end - init_cash) / init_cash,
                            "max_dd": (df['Equity'] / df['Equity'].cummax() - 1).min(),
                            "margin": df['Margin'].max(),
                            "cash": init_cash
                        }

                except Exception as e:
                    st.error(f"运算熔断: {e}")
                    st.session_state.fut_bt_run = False

        if getattr(st.session_state, 'fut_bt_data', None) is not None:
            m = st.session_state.fut_bt_metrics
            df = st.session_state.fut_bt_data

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="metric-box"><p>总收益 (双边)</p><h2>{m["total"] * 100:.2f}%</h2></div>',
                        unsafe_allow_html=True)
            c2.markdown(f'<div class="metric-box"><p>总权益</p><h2>¥ {m["cash"] * (1 + m["total"]):,.0f}</h2></div>',
                        unsafe_allow_html=True)
            c3.markdown(
                f'<div class="metric-box"><p>最大回撤</p><h2 class="danger-text">{m["max_dd"] * 100:.2f}%</h2></div>',
                unsafe_allow_html=True)
            c4.markdown(f'<div class="metric-box"><p>最高占用</p><h2>¥ {m["margin"]:,.0f}</h2></div>',
                        unsafe_allow_html=True)

            st.plotly_chart(render_fut_charts(df), use_container_width=True)


@st_fragment
def render_futures_sandbox():
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">🌪️ 期货高频沙盘推演</h3></div>',
                unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.text_input("标的", "SA2409")
    with c2:
        base_price = st.number_input("初始基准", 2000.0)
    with c3:
        speed = st.slider("频率(s)", 0.1, 2.0, 0.5)
    with c4:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        is_run = st.toggle("🚀 启动脉冲")

    col_l, col_r = st.columns([1, 2.5])
    dom_ph = col_l.empty()
    cht_ph = col_r.empty()

    if is_run:
        cp = base_price
        hist = []
        while is_run:
            import plotly.graph_objects as go

            cp += np.random.choice([-3, -2, -1, 0, 1, 2, 3])
            hist.append(cp)
            hist = hist[-100:]

            asks_html = "".join([
                                    f'<div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖{5 - i}</span><span>{cp + 5 - i:.0f}</span><span>{np.random.randint(10, 500)}</span></div>'
                                    for i in range(5)])
            bids_html = "".join([
                                    f'<div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买{i + 1}</span><span>{cp - i - 1:.0f}</span><span>{np.random.randint(10, 500)}</span></div>'
                                    for i in range(5)])

            color = "#FD1050" if cp >= (hist[-2] if len(hist) > 1 else cp) else "#00FF00"

            dom_ph.markdown(f"""
            <div class="glass-card" style="padding:15px;">
                <h4 style="color:#ff4b4b; margin-top:0;">卖盘</h4>
                {asks_html}
                <hr>
                <h3 style="text-align:center; color:{color}; margin:0;">现价: {cp:.0f}</h3>
                <hr>
                <h4 style="color:#00ffcc; margin-top:0;">买盘</h4>
                {bids_html}
            </div>
            """, unsafe_allow_html=True)

            fig = go.Figure(go.Scatter(y=hist, fill='tozeroy', line=dict(color='#00bfff', width=2),
                                       fillcolor='rgba(0,191,255,0.1)'))
            fig.update_layout(height=380, template="plotly_dark", margin=dict(l=0, r=0, t=10, b=0),
                              xaxis=dict(visible=False))
            cht_ph.plotly_chart(fig, use_container_width=True, key=f"s_{time.time()}")
            time.sleep(speed)
    else:
        dom_ph.info("请开启上方【启动脉冲】开关。")


def render_new_features_page():
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">🧩 插件中心已稳定</h3></div>',
                unsafe_allow_html=True)