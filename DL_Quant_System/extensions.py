# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：统一管理和路由所有的新增模块
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def summon_global_3d_lulu():
    """越狱版：将 3D 模型注入到主网页全局悬浮"""

    # 1. 绝对路径雷达锁定模型
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path):
        st.warning(f"⚠️ 警报：在 `{file_path}` 未找到模型。请确保模型名为 `lulu.glb`。")
        return

    # 2. 转化为 Base64 流作为越狱携带的“干粮”
    with st.spinner("正在施展空间跃迁魔法..."):
        with open(file_path, "rb") as f:
            glb_b64 = base64.b64encode(f.read()).decode("utf-8")

    # 3. 注入越狱 JS 脚本 (核心：操作 window.parent.document)
    html_code = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    <script>
        // 延迟 500 毫秒执行，确保外层主网页已经完全加载完毕
        setTimeout(() => {{
            try {{
                // 🚀 越狱核心：获取外层主网页的统治权
                const doc = window.parent.document;

                // 防重复召唤：如果主网页上已经有噜噜了，就直接退出
                if (doc.getElementById('lulu-global-pet')) return;

                // 1. 在主网页最顶层创建一个完全透明的悬浮舱
                const petBox = doc.createElement('div');
                petBox.id = 'lulu-global-pet';
                petBox.style.cssText = `
                    position: fixed;
                    bottom: 30px;
                    right: 30px;
                    width: 250px;
                    height: 250px;
                    z-index: 9999999; /* 保证在所有元素最上层 */
                    cursor: grab;
                    user-select: none;
                    pointer-events: auto;
                    filter: drop-shadow(0px 15px 20px rgba(0,0,0,0.4)); /* 悬浮立体阴影 */
                    transition: transform 0.2s ease;
                `;

                // 添加一个对话气泡
                const bubble = doc.createElement('div');
                bubble.style.cssText = `
                    position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
                    opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #ff8c00;
                    color: #fff; padding: 8px 15px; border-radius: 12px; font-size: 14px;
                    white-space: nowrap; transition: opacity 0.3s; pointer-events: none;
                `;
                bubble.innerText = "主公，我越狱出来啦！🦦";
                petBox.appendChild(bubble);

                // 正式将悬浮舱挂载到主网页身体上！
                doc.body.appendChild(petBox);

                // 2. 在悬浮舱内初始化 3D 引擎 (背景必须设为全透明 alpha: true)
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                camera.position.set(0, 1.2, 5.5); // 调整远近大小

                const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
                renderer.setSize(250, 250);
                renderer.outputEncoding = THREE.sRGBEncoding; // 材质保真
                petBox.appendChild(renderer.domElement);

                // 3. 光影设置
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
                scene.add(ambientLight);
                const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
                dirLight.position.set(5, 10, 5);
                scene.add(dirLight);

                // 4. 加载主公的 GLB 模型
                let mixer;
                const loader = new THREE.GLTFLoader();
                const glbDataUrl = "data:application/octet-stream;base64,{glb_b64}";

                loader.load(glbDataUrl, function (gltf) {{
                    const model = gltf.scene;
                    model.position.set(0, -1, 0); // 让模型在框内居中下沉一点
                    scene.add(model);

                    // 如果有待机动画，自动播放
                    if (gltf.animations && gltf.animations.length > 0) {{
                        mixer = new THREE.AnimationMixer(model);
                        const action = mixer.clipAction(gltf.animations[0]);
                        action.play();
                    }}

                    // 👀 眼神跟随黑科技：监听全网页的鼠标移动
                    doc.addEventListener('mousemove', (e) => {{
                        const mouseX = (e.clientX / window.parent.innerWidth) * 2 - 1;
                        const mouseY = -(e.clientY / window.parent.innerHeight) * 2 + 1;
                        model.rotation.y = mouseX * 0.6; // 左右转头
                        model.rotation.x = -mouseY * 0.3; // 上下抬头
                    }});
                }});

                // 5. 渲染循环
                const clock = new THREE.Clock();
                function animate() {{
                    requestAnimationFrame(animate);
                    if (mixer) mixer.update(clock.getDelta());
                    renderer.render(scene, camera);
                }}
                animate();

                // 6. 全局拖拽交互引擎 (支持在整个网页上拖动)
                let isDragging = false, startX, startY, initLeft, initTop, isClick = true;

                petBox.onmousedown = (e) => {{
                    isDragging = true; isClick = true;
                    startX = e.clientX; startY = e.clientY;
                    const rect = petBox.getBoundingClientRect();
                    initLeft = rect.left; initTop = rect.top;

                    // 解除 bottom/right 锁定，改用 left/top 绝对定位进行拖拽
                    petBox.style.bottom = 'auto'; 
                    petBox.style.right = 'auto';
                    petBox.style.left = initLeft + 'px';
                    petBox.style.top = initTop + 'px';
                    petBox.style.cursor = 'grabbing';
                    petBox.style.transform = 'scale(1.05)'; // 抓起时放大一点，增强手感
                }};

                // 注意：拖拽事件绑定在全网页 (doc) 上，这样鼠标滑得再快也不会脱手
                doc.addEventListener('mousemove', (e) => {{
                    if (!isDragging) return;
                    if (Math.abs(e.clientX - startX) > 5) isClick = false; // 移动超过 5px 算作拖拽，非点击
                    petBox.style.left = (initLeft + e.clientX - startX) + 'px';
                    petBox.style.top = (initTop + e.clientY - startY) + 'px';
                }});

                doc.addEventListener('mouseup', () => {{
                    if (!isDragging) return;
                    isDragging = false;
                    petBox.style.cursor = 'grab';
                    petBox.style.transform = 'scale(1)'; // 放下时恢复原大小

                    // 如果是单纯点击，弹出气泡
                    if (isClick) {{
                        const ts = ["主公，我能在全网页乱跑啦！🚀", "量化大赚！带我吃橘子！🍊", "正在调集算力...🧠"];
                        bubble.innerText = ts[Math.floor(Math.random() * ts.length)];
                        bubble.style.opacity = '1';
                        setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                    }}
                }});

            }} catch(e) {{
                console.log("越狱失败:", e);
            }}
        }}, 500); // 延迟 500ms 启动，绝不抢占系统资源
    </script>
    """

    # 这里将 height 设为 0，因为 3D 模型已经越狱到主网页上了，这个沙盒可以直接隐身
    components.html(html_code, height=0, width=0)


def render_new_features_page():
    """插件中心的主入口"""
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧩 扩展插件中心</h3><p class="sub-text">模块化架构已打通，新兵器随时可在此列装。</p></div>',
        unsafe_allow_html=True)

    st.success("✨ 全局悬浮越狱协议已启动！噜噜已跳出组件框！请看右下角！")

    # 唤醒越狱版 3D 引擎！
    summon_global_3d_lulu()