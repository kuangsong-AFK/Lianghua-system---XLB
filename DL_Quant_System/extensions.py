# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def summon_3d_lulu():
    """读取本地 GLB 模型并注入到前端"""
    file_path = "lulu.glb"

    # 1. 检查模型文件是否存在
    if not os.path.exists(file_path):
        st.warning("⚠️ 报告主公：未找到 `lulu.glb` 模型文件，请检查是否已放入同级目录。")
        return

    # 2. 将 GLB 文件转化为 Base64 流，突破云端读取限制
    with open(file_path, "rb") as f:
        glb_b64 = base64.b64encode(f.read()).decode("utf-8")

    # 3. 注入 Three.js 3D 渲染引擎与悬浮逻辑
    components.html(f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script>
        let isUpdating = false;
        const run3DEngine = () => {{
            if(isUpdating) return;
            isUpdating = true;

            requestAnimationFrame(() => {{
                const doc = window.parent.document;

                // 如果已经召唤过，就不再重复召唤
                if (doc.getElementById('lulu-3d-container')) {{
                    isUpdating = false;
                    return;
                }}

                // 1. 创建物理悬浮舱 (支持拖拽)
                const luluBox = doc.createElement('div');
                luluBox.id = 'lulu-3d-container';
                luluBox.style.cssText = `
                    position: fixed; bottom: 80px; right: 40px; z-index: 999999; 
                    width: 200px; height: 200px; cursor: grab; user-select: none;
                    filter: drop-shadow(0px 10px 15px rgba(0,0,0,0.5));
                `;

                // 对话气泡
                const bubble = doc.createElement('div');
                bubble.id = 'lulu-3d-bubble';
                bubble.style.cssText = `
                    position: absolute; top: -30px; left: 50%; transform: translateX(-50%);
                    opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #ff8c00; 
                    color: #fff; padding: 6px 10px; border-radius: 10px; font-size: 13px; 
                    white-space: nowrap; transition: opacity 0.3s ease; pointer-events: none;
                `;
                bubble.innerText = "主公，我变 3D 啦！🦦";
                luluBox.appendChild(bubble);
                doc.body.appendChild(luluBox);

                // 2. 初始化 Three.js 渲染环境 (背景透明)
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                // 摄像机位置，如果您觉得模型太大/太小，可以修改这里的值 (X, Y, Z)
                camera.position.set(0, 1.5, 5); 

                const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
                renderer.setSize(200, 200);
                luluBox.appendChild(renderer.domElement);

                // 添加神仙光影
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
                scene.add(ambientLight);
                const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
                dirLight.position.set(5, 10, 5);
                scene.add(dirLight);

                // 3. 解析并加载主公的 GLB 模型
                let mixer; // 动画混合器
                const loader = new THREE.GLTFLoader();
                const glbDataUrl = "data:application/octet-stream;base64,{glb_b64}";

                loader.load(glbDataUrl, function (gltf) {{
                    const model = gltf.scene;

                    // 模型初始姿态微调 (Y轴下沉一点居中)
                    model.position.y = -1; 

                    scene.add(model);

                    // 如果腾讯混元生成了内置动画(绑骨后的待机动画)，则直接播放！
                    if (gltf.animations && gltf.animations.length > 0) {{
                        mixer = new THREE.AnimationMixer(model);
                        const action = mixer.clipAction(gltf.animations[0]);
                        action.play();
                    }}

                    // 鼠标跟随旋转互动
                    doc.addEventListener('mousemove', (e) => {{
                        // 让模型微微转头看向鼠标
                        const mouseX = (e.clientX / window.innerWidth) * 2 - 1;
                        const mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
                        model.rotation.y = mouseX * 0.5;
                        model.rotation.x = -mouseY * 0.2;
                    }});
                }});

                // 4. 渲染循环
                const clock = new THREE.Clock();
                function animate() {{
                    requestAnimationFrame(animate);
                    if (mixer) mixer.update(clock.getDelta());
                    renderer.render(scene, camera);
                }}
                animate();

                // 5. 拖拽与点击交互引擎
                let isDragging = false, startX, startY, initLeft, initTop, isClick = true;
                luluBox.onmousedown = (e) => {{
                    isDragging = true; isClick = true;
                    startX = e.clientX; startY = e.clientY;
                    const rect = luluBox.getBoundingClientRect();
                    initLeft = rect.left; initTop = rect.top;
                    luluBox.style.bottom = 'auto'; luluBox.style.right = 'auto';
                    luluBox.style.left = initLeft + 'px'; luluBox.style.top = initTop + 'px';
                    luluBox.style.cursor = 'grabbing';
                }};

                doc.onmousemove = (e) => {{
                    if (!isDragging) return;
                    if (Math.abs(e.clientX - startX) > 5) isClick = false;
                    luluBox.style.left = (initLeft + e.clientX - startX) + 'px';
                    luluBox.style.top = (initTop + e.clientY - startY) + 'px';
                }};

                doc.onmouseup = () => {{
                    if (!isDragging) return;
                    isDragging = false;
                    luluBox.style.cursor = 'grab';

                    // 点击触发气泡
                    if (isClick) {{
                        const ts = ["主公，我变 3D 啦！✨", "量化大赚，吃橘子！🍊", "调用 Kimi 中...🧠"];
                        bubble.innerText = ts[Math.floor(Math.random() * ts.length)];
                        bubble.style.opacity = '1';
                        setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                    }}
                }};
            }});
            isUpdating = false;
        }};
        runGlobalEngine();
    </script>
    """, height=0, width=0)


def render_new_features_page():
    """该页面的主渲染函数"""
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧩 扩展插件中心</h3><p class="sub-text">模块化架构已打通，新兵器随时可在此列装。</p></div>',
        unsafe_allow_html=True)

    st.info("✅ 报告主公：已在底层发起 3D 引擎召唤阵！请看右下角！")

    # 唤醒咱们刚刚写的 3D 引擎！
    summon_3d_lulu()