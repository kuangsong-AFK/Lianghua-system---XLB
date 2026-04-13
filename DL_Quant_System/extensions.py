# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def render_new_features_page():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧩 扩展插件中心</h3><p class="sub-text">模块化架构已打通，新兵器随时可在此列装。</p></div>',
        unsafe_allow_html=True)

    st.info("✅ 报告主公：已启动云端安全协议！3D 全息展示舱已就绪！(鼠标左键旋转，滚轮缩放)")

    # 1. 绝对路径雷达锁定 lulu.glb
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path):
        st.warning(f"⚠️ 警报：在精准路径 `{file_path}` 依旧未找到模型。请确保您的模型名字全是小写 `lulu.glb`。")
        return

    # 2. 模型碎纸机：转化为 Base64 流突破云端限制
    with st.spinner("正在将 3D 资产注入全息舱..."):
        with open(file_path, "rb") as f:
            glb_b64 = base64.b64encode(f.read()).decode("utf-8")

    # 3. 就地建造 3D 全息舱 (不再越狱，绝对安全！)
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: transparent; }}
            /* 豪华展示舱的 CSS 样式 */
            #canvas-container {{ 
                width: 100%; 
                height: 500px; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                border-radius: 16px; 
                overflow: hidden; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
                background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
                border: 1px solid rgba(0, 255, 204, 0.2);
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
    </head>
    <body>
        <div id="canvas-container"></div>

        <script>
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();

            // 相机设置 (控制镜头远近，您可以把 6 改成 8 或 4 来看看效果)
            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 1.5, 6);

            // 渲染器设置
            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.outputEncoding = THREE.sRGBEncoding; // 让材质色彩更真实
            container.appendChild(renderer.domElement);

            // 光影魔术手
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
            scene.add(ambientLight);

            const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
            dirLight.position.set(5, 10, 5);
            scene.add(dirLight);

            const backLight = new THREE.DirectionalLight(0xffffff, 0.5);
            backLight.position.set(-5, 5, -5);
            scene.add(backLight);

            // 底座特效 (发光的圆环)
            const ringGeo = new THREE.RingGeometry(1.5, 1.6, 64);
            const ringMat = new THREE.MeshBasicMaterial({{ color: 0x00ffcc, side: THREE.DoubleSide, transparent: true, opacity: 0.5 }});
            const ring = new THREE.Mesh(ringGeo, ringMat);
            ring.rotation.x = Math.PI / 2;
            ring.position.y = -1;
            scene.add(ring);

            // 加载主公的真实模型
            let mixer;
            const loader = new THREE.GLTFLoader();
            const glbDataUrl = "data:application/octet-stream;base64,{glb_b64}";

            loader.load(glbDataUrl, function (gltf) {{
                const model = gltf.scene;

                // 将模型往下沉一点，踩在发光圆环上
                model.position.set(0, -1, 0); 
                scene.add(model);

                // 如果腾讯混元绑定了骨骼动画，直接播放！
                if (gltf.animations && gltf.animations.length > 0) {{
                    mixer = new THREE.AnimationMixer(model);
                    const action = mixer.clipAction(gltf.animations[0]);
                    action.play();
                }}
            }});

            // 全方位控制器
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.target.set(0, 0.5, 0); // 聚焦点设置在模型胸口高度

            // 动画循环
            const clock = new THREE.Clock();
            function animate() {{
                requestAnimationFrame(animate);
                if (mixer) mixer.update(clock.getDelta());

                // 让地上的发光圆环缓缓旋转
                ring.rotation.z += 0.01;

                controls.update();
                renderer.render(scene, camera);
            }}
            animate();

            // 窗口自适应
            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }});
        </script>
    </body>
    </html>
    """

    # 给足高度，直接在页面中央渲染！绝对不会被云端屏蔽！
    components.html(html_code, height=520)