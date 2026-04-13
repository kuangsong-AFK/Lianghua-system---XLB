# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：统一管理和路由所有的新增模块
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os


def summon_global_3d_lulu():
    """真·越狱版：将 3D 引擎环境完全寄生到主网页内存中"""

    # 1. 绝对路径雷达锁定模型
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path):
        st.warning(f"⚠️ 警报：在 `{file_path}` 未找到模型。请确保模型名为 `lulu.glb`。")
        return

    # 2. 转化为 Base64 流
    with st.spinner("正在为您施展永动机魔法..."):
        with open(file_path, "rb") as f:
            glb_b64 = base64.b64encode(f.read()).decode("utf-8")

    # 3. 终极寄生脚本：把代码注入到主网页 (Parent Window)
    html_code = f"""
    <script>
        // 这是一个自执行函数，它运行在临时的沙盒中
        (function() {{
            // 获取主网页的全局对象
            const parentWin = window.parent;
            const parentDoc = parentWin.document;

            // 🛡️ 核心防御：如果主网页的脑子里已经有噜噜引擎了，就不要重复注入！
            if (parentWin.__LULU_ENGINE_ALIVE__) return;
            parentWin.__LULU_ENGINE_ALIVE__ = true; // 标记已寄生

            // 动态注入脚本工具：把外部库直接种进主网页的 <head> 里
            const loadScript = (src) => new Promise((resolve) => {{
                const script = parentDoc.createElement('script');
                script.src = src;
                script.onload = resolve;
                parentDoc.head.appendChild(script);
            }});

            // 异步执行主寄生逻辑
            async function startParasiteEngine() {{
                // 1. 让主网页自己下载 Three.js 和加载器
                await loadScript("https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js");
                await loadScript("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js");

                // 获取主网页里的 THREE 对象
                const THREE = parentWin.THREE;

                // 2. 在主网页创建物理悬浮舱
                const petBox = parentDoc.createElement('div');
                petBox.id = 'lulu-global-pet';
                petBox.style.cssText = `
                    position: fixed; bottom: 30px; right: 30px;
                    width: 250px; height: 250px; z-index: 9999999; 
                    cursor: grab; user-select: none; pointer-events: auto;
                    filter: drop-shadow(0px 15px 20px rgba(0,0,0,0.4));
                    transition: transform 0.2s ease;
                `;

                // 气泡
                const bubble = parentDoc.createElement('div');
                bubble.style.cssText = `
                    position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
                    opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #ff8c00;
                    color: #fff; padding: 8px 15px; border-radius: 12px; font-size: 14px;
                    white-space: nowrap; transition: opacity 0.3s; pointer-events: none;
                `;
                bubble.innerText = "主公，我永生啦！🦦";
                petBox.appendChild(bubble);
                parentDoc.body.appendChild(petBox);

                // 3. 初始化 3D 环境
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                camera.position.set(0, 1.2, 5.5); 

                const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
                renderer.setSize(250, 250);
                renderer.outputEncoding = THREE.sRGBEncoding; 
                petBox.appendChild(renderer.domElement);

                // 光影
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
                scene.add(ambientLight);
                const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
                dirLight.position.set(5, 10, 5);
                scene.add(dirLight);

                // 4. 加载 GLB 模型
                let mixer;
                const loader = new THREE.GLTFLoader();
                const glbDataUrl = "data:application/octet-stream;base64,{glb_b64}";

                loader.load(glbDataUrl, function (gltf) {{
                    const model = gltf.scene;
                    model.position.set(0, -1, 0); 
                    scene.add(model);

                    if (gltf.animations && gltf.animations.length > 0) {{
                        mixer = new THREE.AnimationMixer(model);
                        const action = mixer.clipAction(gltf.animations[0]);
                        action.play();
                    }}

                    // 眼神跟随
                    parentDoc.addEventListener('mousemove', (e) => {{
                        const mouseX = (e.clientX / parentWin.innerWidth) * 2 - 1;
                        const mouseY = -(e.clientY / parentWin.innerHeight) * 2 + 1;
                        model.rotation.y = mouseX * 0.6; 
                        model.rotation.x = -mouseY * 0.3; 
                    }});
                }});

                // 5. 渲染循环 (使用主网页的帧刷新，永不卡死！)
                const clock = new THREE.Clock();
                function animate() {{
                    parentWin.requestAnimationFrame(animate);
                    if (mixer) mixer.update(clock.getDelta());
                    renderer.render(scene, camera);
                }}
                animate(); // 启动引擎！

                // 6. 拖拽引擎
                let isDragging = false, startX, startY, initLeft, initTop, isClick = true;

                petBox.onmousedown = (e) => {{
                    isDragging = true; isClick = true;
                    startX = e.clientX; startY = e.clientY;
                    const rect = petBox.getBoundingClientRect();
                    initLeft = rect.left; initTop = rect.top;
                    petBox.style.bottom = 'auto'; petBox.style.right = 'auto';
                    petBox.style.left = initLeft + 'px'; petBox.style.top = initTop + 'px';
                    petBox.style.cursor = 'grabbing';
                    petBox.style.transform = 'scale(1.05)'; 
                }};

                parentDoc.addEventListener('mousemove', (e) => {{
                    if (!isDragging) return;
                    if (Math.abs(e.clientX - startX) > 5) isClick = false; 
                    petBox.style.left = (initLeft + e.clientX - startX) + 'px';
                    petBox.style.top = (initTop + e.clientY - startY) + 'px';
                }});

                parentDoc.addEventListener('mouseup', () => {{
                    if (!isDragging) return;
                    isDragging = false;
                    petBox.style.cursor = 'grab';
                    petBox.style.transform = 'scale(1)'; 

                    if (isClick) {{
                        const ts = ["换页面我也死不了啦！😎", "量化大赚！带我吃橘子！🍊", "正在调集算力...🧠"];
                        bubble.innerText = ts[Math.floor(Math.random() * ts.length)];
                        bubble.style.opacity = '1';
                        setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                    }}
                }});
            }}

            // 执行注入
            startParasiteEngine();
        }})();
    </script>
    """

    components.html(html_code, height=0, width=0)


def render_new_features_page():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧩 扩展插件中心</h3><p class="sub-text">模块化架构已打通，新兵器随时可在此列装。</p></div>',
        unsafe_allow_html=True)
    st.success("✨ 终极寄生协议已启动！噜噜已获得全量系统永生权！")
    summon_global_3d_lulu()