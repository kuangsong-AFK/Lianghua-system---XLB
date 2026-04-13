# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：统一管理和路由所有的新增模块
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def summon_global_3d_lulu():
    """终极寄生版：解决视距、眼神跟随、单击与双击"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path): return

    with st.spinner("正在加载 3D 引擎与交互模块..."):
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

                        let state = 'IDLE'; // 状态机：IDLE, STRUGGLING, DANCING
                        let danceTimer = 0;

                        // 1. 扩大悬浮舱尺寸，防止半截身子！
                        const petBox = doc.createElement('div');
                        petBox.id = 'lulu-global-pet';
                        petBox.style.cssText = "position: fixed; bottom: 30px; right: 30px; width: 300px; height: 300px; z-index: 9999999; cursor: grab; user-select: none; pointer-events: auto; transition: transform 0.2s;";
                        doc.body.appendChild(petBox);

                        // 优化气泡位置
                        const bubble = doc.createElement('div');
                        bubble.style.cssText = "position: absolute; top: 10px; left: 50%; transform: translateX(-50%); opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #ff8c00; color: #fff; padding: 8px 15px; border-radius: 12px; font-size: 14px; white-space: nowrap; transition: opacity 0.3s; pointer-events: none;";
                        petBox.appendChild(bubble);

                        // 2. 初始化环境：拉远相机并降低高度
                        const scene = new THREE.Scene();
                        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                        camera.position.set(0, 0.5, 6.5); // (X左右, Y高低, Z远近) 这样能看清全身

                        const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
                        renderer.setSize(300, 300); // 必须和悬浮舱一样大
                        renderer.outputEncoding = THREE.sRGBEncoding;
                        petBox.appendChild(renderer.domElement);

                        const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
                        scene.add(ambientLight);
                        const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
                        dirLight.position.set(5, 10, 5);
                        scene.add(dirLight);

                        let model, mixer;
                        let targetRotY = 0; // 眼神跟随目标角度
                        let targetRotX = 0;

                        const loader = new THREE.GLTFLoader();
                        loader.load("data:application/octet-stream;base64," + win.__LULU_B64__, (gltf) => {{
                            model = gltf.scene;
                            model.position.set(0, -1.2, 0); // 居中摆放
                            scene.add(model);

                            if (gltf.animations.length > 0) {{
                                mixer = new THREE.AnimationMixer(model);
                                mixer.clipAction(gltf.animations[0]).play();
                            }}

                            // 获取全网页鼠标移动，计算眼神目标角度
                            doc.addEventListener('mousemove', (e) => {{
                                if (state === 'IDLE') {{
                                    const mouseX = (e.clientX / win.innerWidth) * 2 - 1;
                                    const mouseY = -(e.clientY / win.innerHeight) * 2 + 1;
                                    targetRotY = mouseX * 0.8;
                                    targetRotX = -mouseY * 0.4;
                                }}
                            }});
                        }});

                        // 3. 渲染主循环 (引擎心脏)
                        const clock = new THREE.Clock();
                        function animate() {{
                            win.requestAnimationFrame(animate);
                            const delta = clock.getDelta();
                            const time = clock.getElapsedTime();
                            if (mixer) mixer.update(delta);

                            if (model) {{
                                if (state === 'STRUGGLING') {{
                                    // 挣扎：重置身体朝向并高频抖动
                                    model.rotation.y = 0;
                                    model.rotation.x = 0;
                                    model.position.x = Math.sin(time * 50) * 0.05;
                                    model.rotation.z = Math.cos(time * 50) * 0.1;
                                    model.position.y = -1.2;
                                }} else if (state === 'DANCING') {{
                                    // 跳舞：跳跃 + 旋转
                                    model.position.y = -1.2 + Math.abs(Math.sin(time * 10)) * 0.5;
                                    model.rotation.y += 0.2;
                                    model.rotation.x = 0;
                                    model.rotation.z = 0;
                                    model.position.x = 0;

                                    danceTimer -= delta;
                                    if (danceTimer <= 0) {{ 
                                        state = 'IDLE'; 
                                        model.position.y = -1.2; 
                                    }}
                                }} else {{
                                    // 闲置：微弱呼吸 + 眼神平滑跟随鼠标！
                                    model.position.y = -1.2 + Math.sin(time * 2) * 0.02;
                                    model.position.x = 0;
                                    model.rotation.z = 0;
                                    // 让模型平滑转向目标角度 (插值动画，显得很灵动)
                                    model.rotation.y += (targetRotY - model.rotation.y) * 0.1;
                                    model.rotation.x += (targetRotX - model.rotation.x) * 0.1;
                                }}
                            }}
                            renderer.render(scene, camera);
                        }}
                        animate();

                        // 4. 全局交互事件判定
                        let isDragging = false, initX, initY, startL, startT, isClick = true;

                        petBox.onmousedown = (e) => {{
                            isDragging = true; isClick = true; state = 'STRUGGLING';
                            initX = e.clientX; initY = e.clientY;
                            const r = petBox.getBoundingClientRect();
                            startL = r.left; startT = r.top;
                            petBox.style.bottom = 'auto'; petBox.style.right = 'auto';
                            petBox.style.left = startL + 'px'; petBox.style.top = startT + 'px';
                            petBox.style.cursor = 'grabbing';
                            petBox.style.transform = 'scale(1.05)';
                        }};

                        doc.addEventListener('mousemove', (e) => {{
                            if (!isDragging) return;
                            if (Math.abs(e.clientX - initX) > 5) isClick = false; // 动了就不是点击
                            petBox.style.left = (startL + e.clientX - initX) + 'px';
                            petBox.style.top = (startT + e.clientY - initY) + 'px';
                        }});

                        doc.addEventListener('mouseup', () => {{
                            if (!isDragging) return;
                            isDragging = false; 
                            petBox.style.cursor = 'grab';
                            petBox.style.transform = 'scale(1)';
                            if (state !== 'DANCING') state = 'IDLE';

                            // 单击判定：触发说话
                            if (isClick) {{
                                const ts = ["主公，我在这呢！🥰", "量化大赚！吃橘子！🍊", "点击我也不会晕的~🦦", "今天赚了多少呀？💸"];
                                bubble.innerText = ts[Math.floor(Math.random() * ts.length)];
                                bubble.style.opacity = '1';
                                setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                            }}
                        }});

                        // 双击判定：触发跳舞
                        petBox.ondblclick = () => {{
                            state = 'DANCING';
                            danceTimer = 3.0; // 跳舞3秒
                            bubble.innerText = "好耶！开心转圈圈！💃🕺";
                            bubble.style.opacity = '1';
                            setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                        }};
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
    st.info("💡 交互说明：单击说话，拖拽挣扎，双击跳舞！")