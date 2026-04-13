# ==========================================
# 文件名：extensions.py (动作进化版)
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def summon_global_3d_lulu():
    """终极寄生版：赋予噜噜挣扎与跳舞的灵魂"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path): return

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

                        let state = 'IDLE'; // IDLE, STRUGGLING, DANCING
                        let danceTimer = 0;

                        const petBox = doc.createElement('div');
                        petBox.id = 'lulu-global-pet';
                        petBox.style.cssText = "position: fixed; bottom: 30px; right: 30px; width: 220px; height: 220px; z-index: 9999999; cursor: grab; user-select: none; pointer-events: auto; transition: transform 0.2s;";
                        doc.body.appendChild(petBox);

                        const scene = new THREE.Scene();
                        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                        camera.position.set(0, 1.2, 5);
                        const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
                        renderer.setSize(220, 220);
                        renderer.outputEncoding = THREE.sRGBEncoding;
                        petBox.appendChild(renderer.domElement);

                        const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
                        scene.add(ambientLight);
                        const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
                        dirLight.position.set(5, 10, 5);
                        scene.add(dirLight);

                        let model, mixer;
                        const loader = new THREE.GLTFLoader();
                        loader.load("data:application/octet-stream;base64," + win.__LULU_B64__, (gltf) => {{
                            model = gltf.scene;
                            model.position.y = -1.2;
                            scene.add(model);
                            if (gltf.animations.length > 0) {{
                                mixer = new THREE.AnimationMixer(model);
                                mixer.clipAction(gltf.animations[0]).play();
                            }}
                        }});

                        // 渲染主循环
                        const clock = new THREE.Clock();
                        function animate() {{
                            win.requestAnimationFrame(animate);
                            const delta = clock.getDelta();
                            const time = clock.getElapsedTime();
                            if (mixer) mixer.update(delta);

                            if (model) {{
                                if (state === 'STRUGGLING') {{
                                    // 挣扎：高频抖动
                                    model.position.x = Math.sin(time * 50) * 0.05;
                                    model.rotation.z = Math.cos(time * 50) * 0.1;
                                }} else if (state === 'DANCING') {{
                                    // 跳舞：大跳 + 旋转
                                    model.position.y = -1.2 + Math.abs(Math.sin(time * 10)) * 0.5;
                                    model.rotation.y += 0.2;
                                    danceTimer -= delta;
                                    if (danceTimer <= 0) {{ 
                                        state = 'IDLE'; model.position.y = -1.2; model.position.x = 0; 
                                    }}
                                }} else {{
                                    // 闲置：微弱呼吸
                                    model.position.y = -1.2 + Math.sin(time * 2) * 0.02;
                                }}
                            }}
                            renderer.render(scene, camera);
                        }}
                        animate();

                        // 交互事件
                        let isDragging = false, initX, initY, startL, startT, isClick = true;

                        petBox.onmousedown = (e) => {{
                            isDragging = true; isClick = true; state = 'STRUGGLING';
                            initX = e.clientX; initY = e.clientY;
                            const r = petBox.getBoundingClientRect();
                            startL = r.left; startT = r.top;
                            petBox.style.bottom = 'auto'; petBox.style.right = 'auto';
                            petBox.style.left = startL + 'px'; petBox.style.top = startT + 'px';
                            petBox.style.cursor = 'grabbing';
                        }};

                        doc.addEventListener('mousemove', (e) => {{
                            if (!isDragging) return;
                            if (Math.abs(e.clientX - initX) > 5) isClick = false;
                            petBox.style.left = (startL + e.clientX - initX) + 'px';
                            petBox.style.top = (startT + e.clientY - initY) + 'px';
                        }});

                        doc.addEventListener('mouseup', () => {{
                            if (!isDragging) return;
                            isDragging = false; petBox.style.cursor = 'grab';
                            if (state !== 'DANCING') state = 'IDLE';
                        }});

                        petBox.ondblclick = () => {{
                            state = 'DANCING';
                            danceTimer = 3.0; // 跳舞3秒
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
    st.info("💡 交互说明：拖拽噜噜会【挣扎】，双击它会【跳舞】！")
    summon_global_3d_lulu()