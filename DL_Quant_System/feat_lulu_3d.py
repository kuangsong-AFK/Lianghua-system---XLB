# ==========================================
# 文件名：feat_lulu_3d.py (3D 水豚培育舱)
# 功能：利用 Three.js 在独立沙盒中渲染 3D 模型
# ==========================================
import streamlit as st
import streamlit.components.v1 as components


def render_3d_lulu():
    st.markdown("### 🦦 3D 虚拟噜噜 (培育舱)")
    st.info("💡 提示：主公，您可以使用**鼠标左键旋转**，**滚轮缩放**，**右键平移**来全方位观察噜噜！")

    # 注入 Three.js 引擎与手搓的 3D 水豚代码
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; overflow: hidden; background-color: #0f172a; border-radius: 12px; }
            #canvas-container { width: 100%; height: 500px; display: flex; justify-content: center; align-items: center; }
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div id="canvas-container"></div>
        <script>
            // 1. 基础场景设置
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color('#0f172a'); // 深色背景

            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(5, 5, 8);

            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.shadowMap.enabled = true;
            container.appendChild(renderer.domElement);

            // 2. 光照系统
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
            dirLight.position.set(10, 10, 10);
            dirLight.castShadow = true;
            scene.add(dirLight);

            // 3. 手搓 3D 噜噜 (Capybara)
            const luluGroup = new THREE.Group();

            // 材质定义
            const furMaterial = new THREE.MeshLambertMaterial({ color: 0x8B5A2B }); // 棕色毛发
            const darkMaterial = new THREE.MeshLambertMaterial({ color: 0x221100 }); // 深色五官
            const orangeMaterial = new THREE.MeshLambertMaterial({ color: 0xff8c00 }); // 橘子

            // 身体 (圆润的方块)
            const bodyGeo = new THREE.BoxGeometry(2, 1.5, 3);
            const body = new THREE.Mesh(bodyGeo, furMaterial);
            body.position.y = 1;
            body.castShadow = true;
            luluGroup.add(body);

            // 头部
            const headGeo = new THREE.BoxGeometry(1.2, 1.2, 1.5);
            const head = new THREE.Mesh(headGeo, furMaterial);
            head.position.set(0, 1.5, 1.8);
            head.castShadow = true;
            luluGroup.add(head);

            // 眼睛
            const eyeGeo = new THREE.SphereGeometry(0.1, 16, 16);
            const leftEye = new THREE.Mesh(eyeGeo, darkMaterial);
            leftEye.position.set(0.6, 1.7, 2.2);
            luluGroup.add(leftEye);
            const rightEye = new THREE.Mesh(eyeGeo, darkMaterial);
            rightEye.position.set(-0.6, 1.7, 2.2);
            luluGroup.add(rightEye);

            // 鼻子
            const snoutGeo = new THREE.BoxGeometry(0.6, 0.4, 0.2);
            const snout = new THREE.Mesh(snoutGeo, darkMaterial);
            snout.position.set(0, 1.3, 2.5);
            luluGroup.add(snout);

            // 耳朵
            const earGeo = new THREE.BoxGeometry(0.2, 0.3, 0.2);
            const leftEar = new THREE.Mesh(earGeo, darkMaterial);
            leftEar.position.set(0.6, 2.1, 1.5);
            luluGroup.add(leftEar);
            const rightEar = new THREE.Mesh(earGeo, darkMaterial);
            rightEar.position.set(-0.6, 2.1, 1.5);
            luluGroup.add(rightEar);

            // 四条腿
            const legGeo = new THREE.BoxGeometry(0.4, 0.8, 0.4);
            const positions = [
                [0.6, 0.4, 1.0], [-0.6, 0.4, 1.0], 
                [0.6, 0.4, -1.0], [-0.6, 0.4, -1.0]
            ];
            positions.forEach(pos => {
                const leg = new THREE.Mesh(legGeo, furMaterial);
                leg.position.set(pos[0], pos[1], pos[2]);
                leg.castShadow = true;
                luluGroup.add(leg);
            });

            // 头顶的橘子
            const orangeGeo = new THREE.SphereGeometry(0.25, 16, 16);
            const orange = new THREE.Mesh(orangeGeo, orangeMaterial);
            orange.position.set(0, 2.35, 1.6);
            luluGroup.add(orange);

            scene.add(luluGroup);

            // 添加一个简单的地面
            const groundGeo = new THREE.PlaneGeometry(20, 20);
            const groundMat = new THREE.MeshLambertMaterial({ color: 0x1e293b, side: THREE.DoubleSide });
            const ground = new THREE.Mesh(groundGeo, groundMat);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);

            // 4. 控制器与动画循环
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.target.set(0, 1, 0);

            // 让噜噜缓慢呼吸浮动
            let time = 0;
            function animate() {
                requestAnimationFrame(animate);
                time += 0.05;
                // 呼吸效果：身体和头部微微上下浮动
                luluGroup.position.y = Math.sin(time) * 0.05;

                controls.update();
                renderer.render(scene, camera);
            }
            animate();

            // 自适应窗口大小
            window.addEventListener('resize', () => {
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            });
        </script>
    </body>
    </html>
    """, height=520)

    st.markdown("""
    ---
    **🛠️ 资产替换指南：**
    未来主公若在 Sketchfab 等网站下载了精美的 `.gltf` 水豚模型文件，只需将模型放在同级目录，我们即可在这段代码中引入 `GLTFLoader`，用真实精美的 3D 资产替换掉这个由方块拼成的“积木噜噜”！
    """)