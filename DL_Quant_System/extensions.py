# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：极客 IDE、AkShare 期货、高频沙盘、多模型 3D 桌宠
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
    """终极寄生版 V3：支持多模型无缝切换、彻底拦截原生右键菜单"""
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

    with st.spinner("正在为雷达加装多维宇宙识别系统..."):
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

    # 将字典转为 JSON 字符串
    pets_json_str = json.dumps(pet_b64_data)

    # 采用极其安全的变量挂载方式，杜绝字符串过大导致的解析崩溃
    html_template = """
    <script>
        const parentWin = window.parent;
        const parentDoc = parentWin.document;

        // V3 版本：确保强制刷新后执行最新代码
        if (!parentWin.__LULU_V3_INITIALIZED__) {
            parentWin.__LULU_V3_INITIALIZED__ = true;

            // 安全挂载庞大的模型数据到顶级对象，避免模板字符串解析超载
            parentWin.__PETS_JSON_DATA__ = __PETS_JSON_DATA__;

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
                        const petData = window.__PETS_JSON_DATA__;

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
                        ctxMenu.id = 'lulu-ctx-menu';
                        ctxMenu.style.cssText = "position: fixed; display: none; background: rgba(15, 23, 35, 0.95); border: 1px solid rgba(0, 255, 204, 0.5); border-radius: 12px; padding: 6px; z-index: 10000000; color: #fff; font-size: 14px; min-width: 140px; box-shadow: 0 8px 24px rgba(0,0,0,0.8); backdrop-filter: blur(10px);";
                        doc.body.appendChild(ctxMenu);

                        const menuTitle = doc.createElement('div');
                        menuTitle.innerHTML = "<b>✨ 召唤新伙伴</b>";
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
                                if(petData[petName] && petData[petName] !== "") {
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

                        // 🔥 终极拦截：阻止 Canvas 被原生浏览器识别为图片并弹出“另存为” 🔥
                        renderer.domElement.addEventListener('contextmenu', function(e) { e.preventDefault(); }, false);
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
        } else {
            // 如果已经初始化过了，只热更新模型字典，防止重新注入脚本导致冲突
            parentWin.__PETS_JSON_DATA__ = __PETS_JSON_DATA__;
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
        if gid: sub_groups.setdefault(gid.group(1), []).append(c)

    rows = 2 + len(sub_groups)
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.5, 0.15] + [0.35 / max(1, len(sub_groups))] * len(sub_groups))

    if df['trade_date'].dt.time.nunique() <= 1:
        x_labels = df['trade_date'].dt.strftime('%Y-%m-%d')
    else:
        x_labels = df['trade_date'].dt.strftime('%m-%d %H:%M')

    fig.add_trace(go.Candlestick(x=x_labels, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 increasing_line_color='#FD1050', decreasing_line_color='#00FF00', name='K线'), row=1,
                  col=1)
    colors = ['#FFFF00', '#FF00FF', '#00FFFF', '#FFFFFF']
    for i, col in enumerate(main_inds): fig.add_trace(
        go.Scatter(x=x_labels, y=df[col], name=col, line=dict(width=1.2, color=colors[i % 4])), row=1, col=1)

    if 'Signal' in df.columns:
        buys, sells = df[df['Signal'] == 1], df[df['Signal'] == -1]

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
                         marker_color=np.where(df['Close'] >= df['Open'], '#FD1050', '#00FF00'), name='成交量'), row=2,
                  col=1)

    row_idx = 3
    for gid in sorted(sub_groups.keys(), key=int):
        for i, col in enumerate(sub_groups[gid]):
            if 'HIST' in col.upper():
                fig.add_trace(
                    go.Bar(x=x_labels, y=df[col], marker_color=np.where(df[col] >= 0, '#FD1050', '#00FF00'), name=col),
                    row=row_idx, col=1)
            else:
                line_color = colors[i % 4]
                fig.add_trace(go.Scatter(x=x_labels, y=df[col], line=dict(width=1.5, color=line_color), name=col),
                              row=row_idx, col=1)
        row_idx += 1

    fig.update_layout(
        height=500 + len(sub_groups) * 150, template="none", paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)', xaxis_rangeslider_visible=False, dragmode='pan',
        hovermode='x', showlegend=False, margin=dict(l=10, r=10, t=10, b=10)
    )

    fig.update_xaxes(type='category', categoryorder='array', categoryarray=x_labels, nticks=8, showgrid=True,
                     gridwidth=1, gridcolor='rgba(128,128,128,0.2)', tickangle=0)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    return fig


# ==========================================
# 🔥 核心引擎 1：极客量化 IDE (代码编译器)
# ==========================================
def render_ide_page():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">💻 极客量化 IDE (代码沙盒编译器)</h3><p class="sub-text">您可以直接修改 AI 生成的策略，或者在此手动硬编码！支持一键沙盒运行测试，防止实盘崩溃。</p></div>',
        unsafe_allow_html=True)

    # ================= 新手村基础模板库 =================
    default_code = """def generate_signals(df):
    # 【小吕布策略模板】在此处编写您的 Pandas 核心逻辑
    df['MAIN_MA5'] = df['Close'].rolling(window=5).mean()
    df['MAIN_MA20'] = df['Close'].rolling(window=20).mean()

    # 必须生成 Signal 列: 1买入, -1卖出, 0持有
    df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)

    return df"""

    boll_code = """def generate_signals(df):
    # 1. 计算布林带三轨 (主图显示)
    df['MAIN_BOLL_MID'] = df['Close'].rolling(window=20).mean()
    std = df['Close'].rolling(window=20).std()
    df['MAIN_BOLL_UP'] = df['MAIN_BOLL_MID'] + 2 * std
    df['MAIN_BOLL_DN'] = df['MAIN_BOLL_MID'] - 2 * std

    # 2. 生成买卖信号
    df['Signal'] = 0
    df.loc[df['Close'] > df['MAIN_BOLL_UP'], 'Signal'] = 1
    df.loc[df['Close'] < df['MAIN_BOLL_DN'], 'Signal'] = -1

    return df"""

    kdj_code = """def generate_signals(df):
    # 1. 手搓 KDJ 指标 (副图 1 显示)
    n, m1, m2 = 9, 3, 3
    low_list = df['Low'].rolling(window=n).min()
    high_list = df['High'].rolling(window=n).max()
    rsv = (df['Close'] - low_list) / (high_list - low_list) * 100

    df['SUB1_K'] = rsv.ewm(com=m1-1, adjust=False).mean()
    df['SUB1_D'] = df['SUB1_K'].ewm(com=m2-1, adjust=False).mean()
    df['SUB1_J'] = 3 * df['SUB1_K'] - 2 * df['SUB1_D']

    # 2. 生成买卖信号
    df['Signal'] = 0
    df.loc[df['SUB1_J'] < 20, 'Signal'] = 1
    df.loc[df['SUB1_J'] > 80, 'Signal'] = -1

    return df"""

    macd_code = """def generate_signals(df):
    # 1. 计算 MACD (副图 1 显示，且包含 HIST 柱状图)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()

    df['SUB1_MACD_DIFF'] = exp1 - exp2
    df['SUB1_MACD_DEA'] = df['SUB1_MACD_DIFF'].ewm(span=9, adjust=False).mean()
    df['SUB1_MACD_HIST'] = 2 * (df['SUB1_MACD_DIFF'] - df['SUB1_MACD_DEA'])

    # 2. 生成买卖信号
    df['Signal'] = 0
    df.loc[(df['SUB1_MACD_DIFF'] > df['SUB1_MACD_DEA']) & (df['SUB1_MACD_DIFF'].shift(1) <= df['SUB1_MACD_DEA'].shift(1)), 'Signal'] = 1
    df.loc[(df['SUB1_MACD_DIFF'] < df['SUB1_MACD_DEA']) & (df['SUB1_MACD_DIFF'].shift(1) >= df['SUB1_MACD_DEA'].shift(1)), 'Signal'] = -1

    return df"""

    templates = {
        "💡 经典双均线模板 (默认)": default_code,
        "📈 趋势突破流 (布林带 BOLL)": boll_code,
        "🌊 震荡反转流 (超买超卖 KDJ)": kdj_code,
        "🚀 动量加速流 (量价 MACD)": macd_code
    }

    # 🔥 预留接口：尝试从外部策略军火库动态加载高级策略 🔥
    try:
        import strategy_templates
        import inspect
        for name, func in inspect.getmembers(strategy_templates, inspect.isfunction):
            if name.startswith("strategy_"):
                display_name = "🛡️ 严谨：" + name.replace("strategy_", "").upper()
                templates[display_name] = inspect.getsource(func)
    except ImportError:
        pass
    # =======================================================

    c1, c2 = st.columns([2.2, 1.8])

    with c1:
        st.markdown("#### ⌨️ 策略代码编辑区")

        # --- 策略模板加载器 UI ---
        t_col1, t_col2 = st.columns([3, 1])
        with t_col1:
            selected_tpl = st.selectbox("📚 预设经典策略模板", list(templates.keys()), label_visibility="collapsed")
        with t_col2:
            if st.button("📥 载入模板", use_container_width=True):
                st.session_state.generated_code = templates[selected_tpl]
                st.rerun()
        # ------------------------

        current_code = st.session_state.get('generated_code', '')
        if not current_code.strip():
            current_code = default_code

        user_code = st.text_area("Code Editor", value=current_code, height=450, label_visibility="collapsed")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 同步保存至全局引擎", use_container_width=True, type="primary"):
                st.session_state.generated_code = user_code
                st.success("✅ 代码已成功注入全局中枢！现在您可以切换到【全量回测】页面进行图表渲染了。")
        with col_btn2:
            run_debug = st.button("🐞 运行防爆沙盒测试", use_container_width=True)

    with c2:
        st.markdown("#### 🖥️ 编译器控制台 (Console)")
        console_ph = st.empty()

        if run_debug:
            with console_ph.container():
                st.info("正在挂载虚拟沙盒测试环境...")
                try:
                    dates = pd.date_range('20240101', periods=100)
                    dummy_df = pd.DataFrame({
                        'trade_date': dates,
                        'Open': np.random.uniform(2000, 2100, 100),
                        'High': np.random.uniform(2100, 2150, 100),
                        'Low': np.random.uniform(1950, 2000, 100),
                        'Close': np.random.uniform(2000, 2100, 100),
                        'Volume': np.random.randint(1000, 5000, 100)
                    })

                    st.text("🚀 正在强行编译执行您的代码...")
                    start_time = time.time()
                    res_df = safe_exec_fut_strategy(user_code, dummy_df)
                    exec_time = time.time() - start_time

                    st.success(f"✅ 编译完美通过！内核耗时: {exec_time:.4f} 秒")

                    if 'Signal' in res_df.columns:
                        try:
                            sig_counts = res_df['Signal'].value_counts().to_dict()
                        except:
                            sig_counts = "获取分布失败，但列已生成。"
                        st.write("🎯 **买卖信号探测统计**:")
                        st.json(sig_counts)
                    else:
                        st.warning("⚠️ 警告：您的代码忘了返回 `Signal` 列！(规定 1=买入, -1=卖出, 0=观望)")

                    custom_cols = [c for c in res_df.columns if c.startswith(('MAIN_', 'SUB'))]
                    if custom_cols:
                        st.write("📊 **主副图指标提取雷达**:")
                        st.write(custom_cols)

                    st.write("🔍 **沙盒返回的数据矩阵 (前 3 行)**:")
                    st.dataframe(res_df.head(3))

                except Exception as e:
                    st.error("❌ 沙盒编译失败！您的代码存在语法或逻辑错误：")
                    st.code(str(e), language="python")
                    with st.expander("展开查看底层 Traceback 堆栈", expanded=False):
                        st.code(traceback.format_exc(), language="text")
        else:
            console_ph.info(
                "等待您下达编译指令...\n\n点击左侧【运行防爆沙盒测试】按钮，系统将凭空生成虚拟行情数据并安全执行您的代码，绝不会导致实盘引擎崩溃。")


# ==========================================
# 🔥 核心引擎 2：期货全量审计 (AkShare 开源神兵版)
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

        fut_code_input = st.text_input("🎯 期货合约代码", value="", placeholder="直接输入，如: SA2409")

        freq_mapping = {"日线 (Daily)": "D", "60分钟 (60min)": "60", "30分钟 (30min)": "30", "15分钟 (15min)": "15",
                        "5分钟 (5min)": "5", "1分钟 (1min)": "1"}
        freq_choice = st.selectbox("⏱️ 数据周期", list(freq_mapping.keys()), index=0)
        selected_freq = freq_mapping[freq_choice]

        span_mapping = {"近1个月": 0.08, "近3个月": 0.25, "近半年": 0.5, "近1年": 1, "近3年": 3, "近5年": 5}
        span_choice = st.selectbox("⏳ 回测时间跨度", list(span_mapping.keys()), index=3)
        start_year = int(datetime.now().year - span_mapping[span_choice])
        start_date_str = f"{start_year}0101"

        margin_input_str = st.text_input("⚖️ 保证金比例 (%)", value="", placeholder="留空默认自动计算")
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
                    real_code = fut_code_input.upper().strip().split('.')[0]
                    df = None

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
                        pass

                    if df is None or df.empty:
                        st.warning(
                            f"⚠️ **触发容灾机制**：AkShare 接口未返回 `{real_code}` 的真实数据。\n\n系统已自动启动【底层沙盒模拟引擎】，为您瞬间生成逼真的 **{freq_choice}** 高频推演数据！")
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
                        df = df[df['trade_date'] >= pd.to_datetime(start_date_str)].reset_index(drop=True)

                    if df.empty:
                        st.error("❌ 您选择的时间范围内没有数据。请尝试拉长【回测时间跨度】。")
                        st.session_state.fut_bt_run = False
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
                            for col in df_ai.columns:
                                if col == 'Signal' or col.startswith(('MAIN_', 'SUB')): df[col] = df_ai[col]
                        else:
                            df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)

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
                    st.error(f"系统运算发生熔断: {e}")
                    st.session_state.fut_bt_run = False

        if st.session_state.fut_bt_data is not None:
            m = st.session_state.fut_bt_metrics
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
            st.markdown("""
            <div class="metric-box" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <p>等待主公下达指令</p>
                <h2 style="color: #cbd5e1;">点击 [开始穿透回测] 进行推演</h2>
                <p class="sub-text" style="margin-top: 10px;">AkShare 引擎已接管，自动突破高频数据封锁！</p>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# 🔥 核心引擎 3：期货高频沙盘 (加装 Fragment 防闪烁黑科技)
# ==========================================
@st_fragment
def render_futures_sandbox():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🌪️ 期货高频沙盘模拟推演</h3><p class="sub-text">Tick 级盘口模拟、毫秒级信号响应测试与动态滑点侦测。</p></div>',
        unsafe_allow_html=True)
    st.warning("⚠️ 高频警告：期货自带杠杆且波动剧烈，请确保您的‘止损熔断’脚本已装载且经过极寒测试。")

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
    dom_placeholder = c_left.empty()
    chart_placeholder = c_right.empty()

    if is_running:
        current_price = base_price
        tick_history = []

        while is_running:
            # 引入更昂贵的绘图库在这里以懒加载方式启动，加速首屏
            import plotly.graph_objects as go

            price_change = np.random.choice([-3, -2, -1, 0, 1, 2, 3])
            current_price += price_change
            tick_history.append(current_price)
            if len(tick_history) > 100: tick_history.pop(0)

            asks = [(current_price + i, np.random.randint(10, 500)) for i in range(5, 0, -1)]
            bids = [(current_price - i, np.random.randint(10, 500)) for i in range(1, 6)]

            with dom_placeholder.container():
                st.markdown('<div class="glass-card" style="padding: 15px;">', unsafe_allow_html=True)
                st.markdown('<h4 style="margin-top:0; color:#ff4b4b;">卖盘 (Ask)</h4>', unsafe_allow_html=True)
                for i, (p, v) in enumerate(asks):
                    st.markdown(
                        f'<div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖{5 - i}</span><span>{p:.0f}</span><span>{v}</span></div>',
                        unsafe_allow_html=True)

                st.markdown('<hr style="margin: 10px 0; border-color: rgba(255,255,255,0.1);">', unsafe_allow_html=True)
                color = "#FD1050" if price_change >= 0 else "#00FF00"
                st.markdown(
                    f'<h3 style="margin:0; text-align:center; color:{color}; text-shadow: 0 0 10px {color}80;">现价: {current_price:.0f}</h3>',
                    unsafe_allow_html=True)
                st.markdown('<hr style="margin: 10px 0; border-color: rgba(255,255,255,0.1);">', unsafe_allow_html=True)

                st.markdown('<h4 style="margin-top:0; color:#00ffcc;">买盘 (Bid)</h4>', unsafe_allow_html=True)
                for i, (p, v) in enumerate(bids):
                    st.markdown(
                        f'<div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买{i + 1}</span><span>{p:.0f}</span><span>{v}</span></div>',
                        unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with chart_placeholder.container():
                fig = go.Figure(data=go.Scatter(
                    y=tick_history, mode='lines', line=dict(color='#00bfff', width=2),
                    fill='tozeroy', fillcolor='rgba(0, 191, 255, 0.1)'
                ))
                fig.update_layout(
                    height=380, template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(showgrid=False, visible=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig, use_container_width=True, key=f"tick_chart_{time.time()}")

            time.sleep(speed)
    else:
        dom_placeholder.info("请打开上方的【启动高频脉冲引擎】开关，唤醒沙盘。")
        chart_placeholder.markdown("""
        <div class="metric-box" style="height: 380px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
            <p>高频推演</p><h2 style="color: #00ffcc;">等待引擎唤醒...</h2>
        </div>
        """, unsafe_allow_html=True)