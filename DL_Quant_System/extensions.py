# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：统一管理和路由所有的新增模块
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def summon_global_3d_lulu():
    """终极寄生版：4K超清画质 + 完美响应式全端适配"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path): return

    with st.spinner("正在加载超清 3D 引擎与移动端适配模块..."):
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

                        // 🔥 核心重构：响应式尺寸计算器 🔥
                        const getPetSize = () => win.innerWidth <= 768 ? 160 : 300;
                        const getPetBottom = () => win.innerWidth <= 768 ? 15 : 30;
                        const getPetRight = () => win.innerWidth <= 768 ? 10 : 20;
                        const getFontSize = () => win.innerWidth <= 768 ? '12px' : '14px';

                        let currentSize = getPetSize();

                        // 1. 创建物理悬浮舱 (使用动态尺寸)
                        const petBox = doc.createElement('div');
                        petBox.id = 'lulu-global-pet';
                        petBox.style.cssText = \`position: fixed; bottom: \${getPetBottom()}px; right: \${getPetRight()}px; width: \${currentSize}px; height: \${currentSize}px; z-index: 9999999; cursor: grab; user-select: none; pointer-events: auto; transition: transform 0.2s; touch-action: none;\`; 
                        doc.body.appendChild(petBox);

                        const bubble = doc.createElement('div');
                        bubble.style.cssText = \`position: absolute; top: \${win.innerWidth <= 768 ? '-5px' : '10px'}; left: 50%; transform: translateX(-50%); opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #ff8c00; color: #fff; padding: 6px 12px; border-radius: 12px; font-size: \${getFontSize()}; white-space: nowrap; transition: opacity 0.3s; pointer-events: none;\`;
                        petBox.appendChild(bubble);

                        // 2. 超清渲染环境
                        const scene = new THREE.Scene();
                        // 手机端因为画布小，需要把镜头再拉远一点点才能看全
                        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                        camera.position.set(0, 0.8, win.innerWidth <= 768 ? 5.5 : 5.0); 

                        const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
                        renderer.setSize(currentSize, currentSize);
                        renderer.setPixelRatio(win.devicePixelRatio ? win.devicePixelRatio : 1);
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
                                if (state === 'IDLE') {{
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

                        // 🔥 核心重构：监听窗口尺寸变化 (手机横竖屏、电脑拉伸窗口) 🔥
                        win.addEventListener('resize', () => {{
                            const newSize = getPetSize();
                            if (newSize !== currentSize) {{
                                currentSize = newSize;
                                petBox.style.width = currentSize + 'px';
                                petBox.style.height = currentSize + 'px';
                                renderer.setSize(currentSize, currentSize);
                                camera.position.set(0, 0.8, win.innerWidth <= 768 ? 5.5 : 5.0);
                                bubble.style.fontSize = getFontSize();
                                bubble.style.top = win.innerWidth <= 768 ? '-5px' : '10px';
                            }}
                        }});

                        // 3. 渲染循环
                        const clock = new THREE.Clock();
                        function animate() {{
                            win.requestAnimationFrame(animate);
                            const delta = clock.getDelta();
                            const time = clock.getElapsedTime();
                            if (mixer) mixer.update(delta);

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

                        // 4. 全端融合交互引擎
                        let isDragging = false, initX, initY, startL, startT, isClick = true;

                        const getX = (e) => e.touches ? e.touches[0].clientX : e.clientX;
                        const getY = (e) => e.touches ? e.touches[0].clientY : e.clientY;

                        const startDrag = (e) => {{
                            isDragging = true; isClick = true; state = 'STRUGGLING';
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

                            // 边缘防溢出处理，不让噜噜被拖到屏幕外面
                            let newLeft = startL + curX - initX;
                            let newTop = startT + curY - initY;
                            // 限制范围
                            newLeft = Math.max(0, Math.min(newLeft, win.innerWidth - currentSize));
                            newTop = Math.max(0, Math.min(newTop, win.innerHeight - currentSize));

                            petBox.style.left = newLeft + 'px';
                            petBox.style.top = newTop + 'px';

                            if(e.touches) e.preventDefault(); 
                        }};

                        const endDrag = () => {{
                            if (!isDragging) return;
                            isDragging = false; 
                            petBox.style.cursor = 'grab';
                            petBox.style.transform = 'scale(1)';
                            if (state !== 'DANCING') state = 'IDLE';

                            if (isClick) {{
                                const ts = ["主公，手机上我也很乖巧！📱", "量化大赚！吃橘子！🍊", "屏幕好高清呀~🦦", "今天赚了多少呀？💸"];
                                bubble.innerText = ts[Math.floor(Math.random() * ts.length)];
                                bubble.style.opacity = '1';
                                setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                            }}
                        }};

                        const doDance = () => {{
                            state = 'DANCING';
                            danceTimer = 3.0; 
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
        "💡 交互说明：\n1. **电脑端**：单击说话，拖拽挣扎，双击跳舞。\n2. **手机端自适应**：自动缩小防遮挡，触摸滑动防止越界，快速点两下跳舞。")