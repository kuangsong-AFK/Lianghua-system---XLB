# ==========================================
# 文件名：feat_lulu_3d.py (3D 水豚培育舱 - 真身版)
# 功能：利用 GLTFLoader 加载腾讯混元生成的真实 3D 模型
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def render_3d_lulu():
    st.markdown("### 🦦 3D 虚拟噜噜 (培育舱)")
    st.info("💡 提示：主公，您可以使用**鼠标左键旋转**，**滚轮缩放**，**右键平移**来全方位观察真实的噜噜！")

    file_path = "lulu.glb"

    # 1. 检查模型文件是否存在
    if not os.path.exists(file_path):
        st.error(
            f"⚠️ 未找到 `{file_path}` 模型文件！请确保您已将腾讯混元生成的模型下载并重命名为 `lulu.glb`，放在当前文件夹中。")
        return

    # 2. 将 GLB 文件转化为 Base64 流，突破云端 iframe 读取限制
    with st.spinner('正在为您召唤 3D 噜噜真身...'):
        with open(file_path, "rb") as f:
            glb_b64 = base64.b64encode(f.read()).decode("utf-8")

    # 3. 注入 Three.js 引擎与 GLTFLoader
    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; overflow: hidden; background-color: #0f172a; border-radius: 12px; }}
            #canvas-container {{ width: 100%; height: 500px; display: flex; justify-content: center; align-items: center; }}
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
            scene.background = new THREE.Color('#0f172a'); // 深色背景

            // 相机设置
            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 2, 6); // 调整相机距离

            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.shadowMap.enabled = true;
            // 色彩空间映射，让腾讯混元生成的 PBR 材质颜色更鲜艳真实
            renderer.outputEncoding = THREE.sRGBEncoding; 
            container.appendChild(renderer.domElement);

            // 光照系统 (打亮模型)
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
            scene.add(ambientLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
            dirLight.position.set(5, 10, 5);
            dirLight.castShadow = true;
            scene.add(dirLight);

            // 补个背光，展现立体感
            const backLight = new THREE.DirectionalLight(0xffffff, 0.5);
            backLight.position.set(-5, 5, -5);
            scene.add(backLight);

            // 添加一个网格地面，增强空间感
            const grid = new THREE.GridHelper(10, 10, 0x888888, 0x444444);
            scene.add(grid);

            // 核心：加载真实 GLB 模型
            let mixer; 
            const loader = new THREE.GLTFLoader();
            const glbDataUrl = "data:application/octet-stream;base64,{glb_b64}";

            loader.load(glbDataUrl, function (gltf) {{
                const model = gltf.scene;

                // 将模型居中放在网格上
                model.position.set(0, 0, 0); 

                // 让模型拥有阴影
                model.traverse(function(node) {{
                    if (node.isMesh) {{
                        node.castShadow = true;
                        node.receiveShadow = true;
                    }}
                }});

                scene.add(model);

                // 播放腾讯混元生成的骨骼动画
                if (gltf.animations && gltf.animations.length > 0) {{
                    mixer = new THREE.AnimationMixer(model);
                    const action = mixer.clipAction(gltf.animations[0]);
                    action.play();
                }}
            }});

            // 控制器
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.target.set(0, 1, 0); // 视角看向模型中心

            // 动画循环
            const clock = new THREE.Clock();
            function animate() {{
                requestAnimationFrame(animate);
                if (mixer) mixer.update(clock.getDelta());
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();

            // 窗口缩放自适应
            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }});
        </script>
    </body>
    </html>
    """, height=520)