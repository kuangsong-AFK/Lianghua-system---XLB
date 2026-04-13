# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def summon_global_3d_lulu():
    """终极寄生版：固定大尺寸 + 待机挂机(AFK)互动系统"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path): return

    with st.spinner("正在加载 3D 引擎与 AFK 待机系统..."):
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

                        // 🔥 新增：AFK 待机系统变量 🔥
                        let lastActivityTime = Date.now();
                        let idleActionState = 'NONE'; // 待机子动作
                        let idleActionTimer = 0;

                        // 固定傲人尺寸，不再缩小！
                        const petSize = 280; 

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
                        renderer.setPixelRatio(win.devicePixelRatio ? Math.min(win.devicePixelRatio, 2) : 1); // 限制最大像素比防卡顿
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
                                // 重置挂机时间
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

                            // 🔥 挂机(AFK)检测逻辑 🔥
                            if (state === 'IDLE' && idleActionState === 'NONE') {{
                                if (now - lastActivityTime > 30000) {{ // 30秒无操作
                                    const actions = ['HOP', 'LOOK_AROUND', 'SPEAK'];
                                    const act = actions[Math.floor(Math.random() * actions.length)];
                                    idleActionState = act;
                                    idleActionTimer = 2.5; // 动作持续 2.5 秒
                                    lastActivityTime = now; // 动作完重置计时

                                    if (act === 'SPEAK') {{
                                        const texts = ["主公，您睡着了吗？🦦", "盯盘好累喔，发呆中...", "呼噜噜...💤"];
                                        bubble.innerText = texts[Math.floor(Math.random() * texts.length)];
                                        bubble.style.opacity = '1';
                                        setTimeout(() => {{ bubble.style.opacity = '0'; }}, 4000);
                                        idleActionState = 'NONE'; 
                                    }}
                                }}
                            }}

                            if (model) {{
                                // 处理交互状态
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
                                }} 
                                // 处理待机自发动作
                                else if (idleActionState === 'HOP') {{
                                    model.position.y = -1.2 + Math.abs(Math.sin(time * 15)) * 0.3;
                                    model.rotation.x = 0; model.rotation.y = 0;
                                    idleActionTimer -= delta;
                                    if (idleActionTimer <= 0) {{ idleActionState = 'NONE'; model.position.y = -1.2; }}
                                }} else if (idleActionState === 'LOOK_AROUND') {{
                                    model.rotation.y = Math.sin(time * 3) * 0.6; // 左右张望
                                    model.rotation.x = 0;
                                    idleActionTimer -= delta;
                                    if (idleActionTimer <= 0) {{ idleActionState = 'NONE'; model.rotation.y = targetRotY; }}
                                }} 
                                // 正常静默闲置
                                else {{
                                    model.position.y = -1.2 + Math.sin(time * 2) * 0.02;
                                    model.position.x = 0; model.rotation.z = 0;
                                    model.rotation.y += (targetRotY - model.rotation.y) * 0.1;
                                    model.rotation.x += (targetRotX - model.rotation.x) * 0.1;
                                }}
                            }}
                            renderer.render(scene, camera);
                        }}
                        animate();

                        // 4. 全端融合交互引擎
                        let isDragging = false, initX, initY, startL, startT, isClick = true;

                        const getX = (e) => e.touches ? e.touches[0].clientX : e.clientX;
                        const getY = (e) => e.touches ? e.touches[0].clientY : e.clientY;

                        const startDrag = (e) => {{
                            isDragging = true; isClick = true; state = 'STRUGGLING';
                            idleActionState = 'NONE'; // 打断待机动作
                            lastActivityTime = Date.now();
                            initX = getX(e); initY = getY(e);
                            const r = petBox.getBoundingClientRect();
                            startL = r.left; startT = r.top;
                            petBox.style.bottom = 'auto'; petBox.style.right = 'auto';
                            petBox.style.left = startL + 'px'; petBox.style.top = startT + 'px';
                            petBox.style.cursor = 'grabbing';
                            petBox.style.transform = 'scale(1.05)';
                        }};

                        const doDrag = (e) => {{
                            if (!isDragging) return;
                            const curX = getX(e); const curY = getY(e);
                            if (Math.abs(curX - initX) > 5 || Math.abs(curY - initY) > 5) isClick = false;

                            let newLeft = startL + curX - initX;
                            let newTop = startT + curY - initY;
                            newLeft = Math.max(0, Math.min(newLeft, win.innerWidth - petSize));
                            newTop = Math.max(0, Math.min(newTop, win.innerHeight - petSize));

                            petBox.style.left = newLeft + 'px';
                            petBox.style.top = newTop + 'px';

                            if(e.touches) e.preventDefault(); 
                        }};

                        const endDrag = () => {{
                            if (!isDragging) return;
                            isDragging = false; 
                            petBox.style.cursor = 'grab';
                            petBox.style.transform = 'scale(1)';
                            lastActivityTime = Date.now();
                            if (state !== 'DANCING') state = 'IDLE';

                            if (isClick) {{
                                const ts = ["主公，手机上我也很乖巧！📱", "量化大赚！吃橘子！🍊", "点击我也不会晕的~🦦"];
                                bubble.innerText = ts[Math.floor(Math.random() * ts.length)];
                                bubble.style.opacity = '1';
                                setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                            }}
                        }};

                        const doDance = () => {{
                            state = 'DANCING';
                            danceTimer = 3.0; 
                            lastActivityTime = Date.now();
                            bubble.innerText = "好耶！开心转圈圈！💃🕺";
                            bubble.style.opacity = '1';
                            setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                        }};

                        petBox.addEventListener('mousedown', startDrag);
                        doc.addEventListener('mousemove', doDrag);
                        doc.addEventListener('mouseup', endDrag);
                        petBox.addEventListener('dblclick', doDance);

                        petBox.addEventListener('touchstart', startDrag, {{passive: false}});
                        doc.addEventListener('touchmove', doDrag, {{passive: false}});
                        doc.addEventListener('touchend', endDrag);

                        let lastTap = 0;
                        petBox.addEventListener('touchend', (e) => {{
                            const currentTime = new Date().getTime();
                            const tapLength = currentTime - lastTap;
                            if (tapLength < 500 && tapLength > 0) {{
                                doDance();
                                e.preventDefault();
                            }}
                            lastTap = currentTime;
                        }});

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
    st.info(
        "💡 交互说明：\n1. **挂机陪伴**：放置 30 秒不理它，它会自己蹦跶、四处张望或找您搭话！\n2. **尺寸还原**：手机端不再缩小尺寸，全端统一 280x280 大图霸气呈现！")