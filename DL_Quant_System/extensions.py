# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：统一管理和路由所有的新增模块
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def summon_global_3d_lulu():
    """终极寄生版：解决空气墙边缘阻挡 + 终极物理防抖防误触"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path): return

    with st.spinner("正在加载终极物理触控引擎..."):
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
                        // 🔥 核心破解1：允许空气墙溢出屏幕外 80px，让实体完美贴边 🔥
                        const overflowLimit = 80; 

                        // 1. 创建物理悬浮舱
                        const petBox = doc.createElement('div');
                        petBox.id = 'lulu-global-pet';
                        petBox.style.cssText = "position: fixed; bottom: 20px; right: 20px; width: " + petSize + "px; height: " + petSize + "px; z-index: 9999999; cursor: grab; user-select: none; pointer-events: auto; transition: transform 0.2s; touch-action: none;"; 
                        doc.body.appendChild(petBox);

                        const bubble = doc.createElement('div');
                        bubble.style.cssText = "position: absolute; top: 0px; left: 50%; transform: translateX(-50%); opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #ff8c00; color: #fff; padding: 8px 15px; border-radius: 12px; font-size: 14px; white-space: nowrap; transition: opacity 0.3s; pointer-events: none;";
                        petBox.appendChild(bubble);

                        // 2. 超清渲染环境
                        const scene = new THREE.Scene();
                        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                        camera.position.set(0, 0.8, 5.5); 

                        const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
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

                        const loader = new THREE.GLTFLoader();
                        loader.load("data:application/octet-stream;base64," + win.__LULU_B64__, (gltf) => {{
                            model = gltf.scene;
                            model.position.set(0, -1.2, 0); 
                            scene.add(model);

                            if (gltf.animations.length > 0) {{
                                mixer = new THREE.AnimationMixer(model);
                                mixer.clipAction(gltf.animations[0]).play();
                            }}

                            const updateLookAt = (clientX, clientY) => {{
                                lastActivityTime = Date.now();
                                if (state === 'IDLE' && idleActionState === 'NONE') {{
                                    const mouseX = (clientX / win.innerWidth) * 2 - 1;
                                    const mouseY = -(clientY / win.innerHeight) * 2 + 1;
                                    targetRotY = mouseX * 0.8;
                                    targetRotX = -mouseY * 0.4;
                                }}
                            }};
                            doc.addEventListener('mousemove', (e) => updateLookAt(e.clientX, e.clientY));
                            doc.addEventListener('touchmove', (e) => {{
                                if(e.touches.length > 0) updateLookAt(e.touches[0].clientX, e.touches[0].clientY);
                            }}, {{passive: true}});
                        }});

                        // 3. 渲染循环 & 挂机检测引擎
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
                                    idleActionState = act;
                                    idleActionTimer = 2.5; 
                                    lastActivityTime = now; 

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
                                    model.rotation.y += 0.2;
                                    model.rotation.x = 0; model.rotation.z = 0; model.position.x = 0;

                                    danceTimer -= delta;
                                    if (danceTimer <= 0) {{ state = 'IDLE'; model.position.y = -1.2; }}
                                }} else if (idleActionState === 'HOP') {{
                                    model.position.y = -1.2 + Math.abs(Math.sin(time * 15)) * 0.3;
                                    model.rotation.x = 0; model.rotation.y = 0;
                                    idleActionTimer -= delta;
                                    if (idleActionTimer <= 0) {{ idleActionState = 'NONE'; model.position.y = -1.2; }}
                                }} else if (idleActionState === 'LOOK_AROUND') {{
                                    model.rotation.y = Math.sin(time * 3) * 0.6; 
                                    model.rotation.x = 0;
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
                        animate();

                        // 4. 电竞级触控引擎
                        let isDragging = false, initX, initY, startL, startT, isPossibleClick = false;
                        let clickTimeout = null;
                        let lastTapTime = 0;

                        const getX = (e) => e.touches ? e.touches[0].clientX : e.clientX;
                        const getY = (e) => e.touches ? e.touches[0].clientY : e.clientY;

                        const doSpeak = (customTexts) => {{
                            const ts = customTexts || ["主公，我在这呢！🥰", "量化大赚！吃橘子！🍊", "点击我也不会晕的~🦦", "今天赚了多少呀？💸"];
                            bubble.innerText = ts[Math.floor(Math.random() * ts.length)];
                            bubble.style.opacity = '1';
                            setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                        }};

                        const doDance = () => {{
                            state = 'DANCING';
                            danceTimer = 3.0; 
                            lastActivityTime = Date.now();
                            bubble.innerText = "好耶！开心转圈圈！💃🕺";
                            bubble.style.opacity = '1';
                            setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                        }};

                        const startInteraction = (e) => {{
                            initX = getX(e); initY = getY(e);
                            const r = petBox.getBoundingClientRect();
                            startL = r.left; startT = r.top;

                            isDragging = false; 
                            isPossibleClick = true; 

                            petBox.style.bottom = 'auto'; petBox.style.right = 'auto';
                            petBox.style.left = startL + 'px'; petBox.style.top = startT + 'px';
                        }};

                        const moveInteraction = (e) => {{
                            const curX = getX(e); const curY = getY(e);
                            const moveDist = Math.sqrt(Math.pow(curX - initX, 2) + Math.pow(curY - initY, 2));

                            // 🔥 核心破解2：将死区调大到 20 像素！彻底解决肉垫压迫产生的形变误触 🔥
                            if (moveDist > 20) {{ 
                                if (!isDragging) {{
                                    isDragging = true;
                                    isPossibleClick = false;
                                    state = 'STRUGGLING';
                                    idleActionState = 'NONE';
                                    petBox.style.cursor = 'grabbing';
                                    petBox.style.transform = 'scale(1.05)';
                                    petBox.style.transition = 'none'; 
                                }}

                                let newLeft = startL + curX - initX;
                                let newTop = startT + curY - initY;

                                // 🔥 空气墙穿透计算：允许坐标出现负数或超出屏幕宽度，让透明边框滚出去，实体贴边 🔥
                                newLeft = Math.max(-overflowLimit, Math.min(newLeft, win.innerWidth - petSize + overflowLimit));
                                newTop = Math.max(-overflowLimit, Math.min(newTop, win.innerHeight - petSize + overflowLimit));

                                petBox.style.left = newLeft + 'px';
                                petBox.style.top = newTop + 'px';

                                if(e.cancelable) e.preventDefault(); 
                            }}
                        }};

                        const endInteraction = (e) => {{
                            petBox.style.transition = 'transform 0.2s'; 
                            petBox.style.cursor = 'grab';
                            petBox.style.transform = 'scale(1)';
                            lastActivityTime = Date.now();

                            if (isDragging) {{
                                isDragging = false;
                                if (state !== 'DANCING') state = 'IDLE';
                                return; 
                            }}

                            if (isPossibleClick) {{
                                const currentTime = new Date().getTime();
                                const tapLength = currentTime - lastTapTime;
                                clearTimeout(clickTimeout); 

                                if (tapLength < 350 && tapLength > 0) {{
                                    doDance();
                                }} else {{
                                    clickTimeout = setTimeout(() => {{
                                        doSpeak();
                                    }}, 300);
                                }}
                                lastTapTime = currentTime;
                            }}
                        }};

                        petBox.addEventListener('mousedown', startInteraction);
                        doc.addEventListener('mousemove', moveInteraction);
                        doc.addEventListener('mouseup', endInteraction);

                        petBox.addEventListener('touchstart', startInteraction, {{passive: true}});
                        doc.addEventListener('touchmove', moveInteraction, {{passive: false}});
                        doc.addEventListener('touchend', endInteraction);

                    }})();
                `;
                parentDoc.body.appendChild(script);
            }};
            initLulu();
        }}
    </script>
    """
    components.html(html_code, height=0, width=0)


def render_new_features_page():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧩 扩展插件中心</h3></div>',
        unsafe_allow_html=True)
    st.info("💡 移动端交互已升级：增加 20px 物理防抖死区、允许空气墙穿透屏幕边缘贴靠！")