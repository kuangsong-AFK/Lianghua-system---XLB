# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：统一管理和路由所有的新增模块
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import tushare as ts
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def summon_global_3d_lulu():
    """终极寄生版：军用级雷达白名单，彻底无视上方骨骼包围盒与隐形空气墙"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "lulu.glb")

    if not os.path.exists(file_path): return

    with st.spinner("正在为雷达加装白名单识别系统..."):
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
                        let lastActivityTime = Date.now();
                        let idleActionState = 'NONE'; 
                        let idleActionTimer = 0;

                        const petSize = 280; 
                        const overflowLimit = 80; 

                        const petBox = doc.createElement('div');
                        petBox.id = 'lulu-global-pet';
                        petBox.style.cssText = "position: fixed; bottom: 20px; right: 20px; width: " + petSize + "px; height: " + petSize + "px; z-index: 9999999; cursor: grab; user-select: none; pointer-events: none; transition: transform 0.2s; touch-action: none;"; 
                        doc.body.appendChild(petBox);

                        const bubble = doc.createElement('div');
                        bubble.style.cssText = "position: absolute; top: 0px; left: 50%; transform: translateX(-50%); opacity: 0; background: rgba(20, 28, 45, 0.95); border: 1px solid #ff8c00; color: #fff; padding: 8px 15px; border-radius: 12px; font-size: 14px; white-space: nowrap; transition: opacity 0.3s; pointer-events: none;";
                        petBox.appendChild(bubble);

                        const scene = new THREE.Scene();
                        const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
                        camera.position.set(0, 0.8, 5.5); 

                        const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: win.innerWidth > 768 }});
                        renderer.setSize(petSize, petSize);
                        renderer.setPixelRatio(win.devicePixelRatio ? Math.min(win.devicePixelRatio, 2) : 1);
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

                        let clickableMeshes = [];

                        const loader = new THREE.GLTFLoader();
                        loader.load("data:application/octet-stream;base64," + win.__LULU_B64__, (gltf) => {{
                            model = gltf.scene;
                            model.position.set(0, -1.2, 0); 

                            model.traverse((child) => {{
                                if (child.isMesh) {{
                                    let isTrash = false;
                                    if (child.material) {{
                                        if (child.material.transparent && child.material.opacity < 0.1) isTrash = true;
                                        if (child.material.opacity === 0) isTrash = true;
                                    }}

                                    if (isTrash) {{
                                        child.visible = false; 
                                    }} else {{
                                        clickableMeshes.push(child); 
                                    }}
                                }}
                            }});

                            scene.add(model);

                            if (gltf.animations.length > 0) {{
                                mixer = new THREE.AnimationMixer(model);
                                mixer.clipAction(gltf.animations[0]).play();
                            }}
                        }});

                        const raycaster = new THREE.Raycaster();
                        const mouseNDC = new THREE.Vector2();

                        const checkHit = (clientX, clientY) => {{
                            if (clickableMeshes.length === 0) return false;

                            const rect = renderer.domElement.getBoundingClientRect();
                            if (clientX < rect.left || clientX > rect.right || clientY < rect.top || clientY > rect.bottom) {{
                                return false;
                            }}

                            mouseNDC.x = ((clientX - rect.left) / petSize) * 2 - 1;
                            mouseNDC.y = -((clientY - rect.top) / petSize) * 2 + 1;

                            raycaster.setFromCamera(mouseNDC, camera);
                            const intersects = raycaster.intersectObjects(clickableMeshes, false);

                            return intersects.length > 0; 
                        }};

                        const updateLookAt = (clientX, clientY) => {{
                            lastActivityTime = Date.now();
                            if (state === 'IDLE' && idleActionState === 'NONE') {{
                                const mouseX = (clientX / win.innerWidth) * 2 - 1;
                                const mouseY = -(clientY / win.innerHeight) * 2 + 1;
                                targetRotY = mouseX * 0.8;
                                targetRotX = -mouseY * 0.4;
                            }}
                        }};

                        const clock = new THREE.Clock();
                        function animate() {{
                            win.requestAnimationFrame(animate);
                            const delta = clock.getDelta();
                            const time = clock.getElapsedTime();
                            if (mixer) mixer.update(delta);

                            const now = Date.now();

                            if (state === 'IDLE' && idleActionState === 'NONE') {{
                                if (now - lastActivityTime > 30000) {{ 
                                    const actions = ['HOP', 'LOOK_AROUND', 'SPEAK'];
                                    const act = actions[Math.floor(Math.random() * actions.length)];
                                    idleActionState = act;
                                    idleActionTimer = 2.5; 
                                    lastActivityTime = now; 

                                    if (act === 'SPEAK') {{
                                        doSpeak(["主公，您睡着了吗？🦦", "盯盘好累喔，发呆中...", "呼噜噜...💤"]);
                                        idleActionState = 'NONE'; 
                                    }}
                                }}
                            }}

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
                                }} else if (idleActionState === 'HOP') {{
                                    model.position.y = -1.2 + Math.abs(Math.sin(time * 15)) * 0.3;
                                    model.rotation.x = 0; model.rotation.y = 0;
                                    idleActionTimer -= delta;
                                    if (idleActionTimer <= 0) {{ idleActionState = 'NONE'; model.position.y = -1.2; }}
                                }} else if (idleActionState === 'LOOK_AROUND') {{
                                    model.rotation.y = Math.sin(time * 3) * 0.6; 
                                    model.rotation.x = 0;
                                    idleActionTimer -= delta;
                                    if (idleActionTimer <= 0) {{ idleActionState = 'NONE'; model.rotation.y = targetRotY; }}
                                }} else {{
                                    model.position.y = -1.2 + Math.sin(time * 2) * 0.02;
                                    model.position.x = 0; model.rotation.z = 0;
                                    model.rotation.y += (targetRotY - model.rotation.y) * 0.1;
                                    model.rotation.x += (targetRotX - model.rotation.x) * 0.1;
                                }}
                            }}
                            renderer.render(scene, camera);
                        }}

                        let isDragging = false, initX, initY, startL, startT, isPossibleClick = false;
                        let isHolding = false;
                        let clickTimeout = null;
                        let lastTapTime = 0;

                        const getX = (e) => e.touches ? e.touches[0].clientX : e.clientX;
                        const getY = (e) => e.touches ? e.touches[0].clientY : e.clientY;

                        const doSpeak = (customTexts) => {{
                            const ts = customTexts || ["主公，我在这呢！🥰", "量化大赚！吃橘子！🍊", "点击我也不会晕的~🦦", "今天赚了多少呀？💸"];
                            bubble.innerText = ts[Math.floor(Math.random() * ts.length)];
                            bubble.style.opacity = '1';
                            setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                        }};

                        const doDance = () => {{
                            state = 'DANCING';
                            danceTimer = 3.0; 
                            lastActivityTime = Date.now();
                            bubble.innerText = "好耶！开心转圈圈！💃🕺";
                            bubble.style.opacity = '1';
                            setTimeout(() => {{ bubble.style.opacity = '0'; }}, 3000);
                        }};

                        const startInteraction = (e) => {{
                            isHolding = true; 
                            initX = getX(e); initY = getY(e);
                            const r = petBox.getBoundingClientRect();
                            startL = r.left; startT = r.top;

                            isDragging = false; 
                            isPossibleClick = true; 

                            petBox.style.bottom = 'auto'; petBox.style.right = 'auto';
                            petBox.style.left = startL + 'px'; petBox.style.top = startT + 'px';
                        }};

                        win.addEventListener('mousemove', (e) => {{
                            if (isHolding) {{
                                const curX = getX(e); const curY = getY(e);
                                const moveDist = Math.sqrt(Math.pow(curX - initX, 2) + Math.pow(curY - initY, 2));

                                if (moveDist > 20) {{ 
                                    if (!isDragging) {{
                                        isDragging = true; isPossibleClick = false; state = 'STRUGGLING'; idleActionState = 'NONE';
                                        petBox.style.cursor = 'grabbing'; petBox.style.transform = 'scale(1.05)'; petBox.style.transition = 'none'; 
                                    }}
                                    let newLeft = startL + curX - initX; let newTop = startT + curY - initY;
                                    newLeft = Math.max(-overflowLimit, Math.min(newLeft, win.innerWidth - petSize + overflowLimit));
                                    newTop = Math.max(-overflowLimit, Math.min(newTop, win.innerHeight - petSize + overflowLimit));
                                    petBox.style.left = newLeft + 'px'; petBox.style.top = newTop + 'px';
                                    if(e.cancelable) e.preventDefault(); 
                                }}
                                return;
                            }}

                            updateLookAt(e.clientX, e.clientY);

                            if (checkHit(e.clientX, e.clientY)) {{
                                if (petBox.style.pointerEvents !== 'auto') {{
                                    petBox.style.pointerEvents = 'auto';
                                    petBox.style.cursor = 'grab';
                                }}
                            }} else {{
                                if (petBox.style.pointerEvents !== 'none') {{
                                    petBox.style.pointerEvents = 'none';
                                }}
                            }}
                        }}, true);

                        const endInteraction = (e) => {{
                            if (!isHolding) return;
                            isHolding = false; 
                            petBox.style.transition = 'transform 0.2s'; 
                            petBox.style.cursor = 'grab';
                            petBox.style.transform = 'scale(1)';
                            lastActivityTime = Date.now();

                            if (isDragging) {{
                                isDragging = false;
                                if (state !== 'DANCING') state = 'IDLE';
                                return; 
                            }}

                            if (isPossibleClick) {{
                                const currentTime = new Date().getTime();
                                const tapLength = currentTime - lastTapTime;
                                clearTimeout(clickTimeout); 

                                if (tapLength < 350 && tapLength > 0) {{
                                    doDance();
                                }} else {{
                                    clickTimeout = setTimeout(() => {{ doSpeak(); }}, 300);
                                }}
                                lastTapTime = currentTime;
                            }}
                        }};

                        petBox.addEventListener('mousedown', startInteraction);
                        doc.addEventListener('mouseup', endInteraction);
                        doc.addEventListener('mouseleave', endInteraction);

                        doc.addEventListener('touchstart', (e) => {{
                            if (checkHit(e.touches[0].clientX, e.touches[0].clientY)) {{
                                petBox.style.pointerEvents = 'auto';
                                startInteraction(e);
                                e.stopPropagation();
                            }} else {{
                                petBox.style.pointerEvents = 'none';
                            }}
                        }}, {{ capture: true, passive: false }});

                        doc.addEventListener('touchmove', (e) => {{
                            if (isHolding) {{
                                const curX = getX(e); const curY = getY(e);
                                const moveDist = Math.sqrt(Math.pow(curX - initX, 2) + Math.pow(curY - initY, 2));
                                if (moveDist > 20) {{ 
                                    if (!isDragging) {{
                                        isDragging = true; isPossibleClick = false; state = 'STRUGGLING'; idleActionState = 'NONE';
                                        petBox.style.cursor = 'grabbing'; petBox.style.transform = 'scale(1.05)'; petBox.style.transition = 'none'; 
                                    }}
                                    let newLeft = startL + curX - initX; let newTop = startT + curY - initY;
                                    newLeft = Math.max(-overflowLimit, Math.min(newLeft, win.innerWidth - petSize + overflowLimit));
                                    newTop = Math.max(-overflowLimit, Math.min(newTop, win.innerHeight - petSize + overflowLimit));
                                    petBox.style.left = newLeft + 'px'; petBox.style.top = newTop + 'px';

                                    e.stopPropagation();
                                    if(e.cancelable) e.preventDefault(); 
                                }}
                            }} else {{
                                updateLookAt(e.touches[0].clientX, e.touches[0].clientY);
                            }}
                        }}, {{ passive: false }});

                        doc.addEventListener('touchend', endInteraction);
                        doc.addEventListener('touchcancel', endInteraction);

                        setTimeout(animate, 1500);
                    }})();
                `;
                parentDoc.body.appendChild(script);
            }};

            setTimeout(initLulu, 500); 
        }}
    </script>
    """
    components.html(html_code, height=0, width=0)


def render_new_features_page():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🧩 扩展插件中心</h3></div>',
        unsafe_allow_html=True)
    st.info("💡 核心交互与 3D 桌宠已全部稳定运行！")


# ==========================================
# 🔥 核心引擎：期货全量审计 (接通 Tushare)
# ==========================================
def render_futures_backtest():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🔗 期货全量审计与归因分析</h3><p class="sub-text">支持中金所、上期所、大商所、郑商所全品种合约穿透式回测，引入真实杠杆与保证金校验体系。</p></div>',
        unsafe_allow_html=True)

    c1, c2 = st.columns([1, 3])
    with c1:
        fut_code = st.text_input("🎯 期货合约代码", value="SA2409.CZC", help="纯碱主力合约示例")
        margin_rate = st.slider("⚖️ 保证金比例 (%)", 5, 20, 12) / 100
        multiplier = st.number_input("🔢 合约乘数 (吨/手)", value=20, help="纯碱一手为20吨")

        # 假设固定初始资金和每次开仓手数，方便模拟
        init_cash = st.number_input("💰 初始资金", value=1000000, step=100000)
        trade_lots = st.number_input("📦 每次开仓手数", value=10, step=1)

        start_btn = st.button("🚀 开始穿透回测", type="primary", use_container_width=True)

    with c2:
        if start_btn:
            with st.spinner(f"正在通过 Tushare 调取 {fut_code} 历史连续数据..."):
                try:
                    # 1. 调取 Tushare 期货日线数据
                    pro = ts.pro_api()
                    df = pro.fut_daily(ts_code=fut_code, start_date='20230101')

                    if df.empty:
                        st.error(
                            f"❌ 未获取到 {fut_code} 的数据。请检查代码是否正确 (如: SA2409.CZC, I2409.DCE)。注：部分数据需 Tushare 相应积分权限。")
                    else:
                        st.success("✅ 数据拉取成功！杠杆乘数已注入，开始进行动态推演...")

                        # 2. 数据清洗与排序
                        df = df.sort_values('trade_date').reset_index(drop=True)
                        df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

                        # 3. 模拟一个非常基础的双均线策略产生交易信号
                        df['MA10'] = df['close'].rolling(10).mean()
                        df['MA20'] = df['close'].rolling(20).mean()
                        # 产生信号：金叉做多(1)，死叉做空(-1)
                        df['Signal'] = np.where(df['MA10'] > df['MA20'], 1, -1)
                        # 信号延迟一天作为实际持仓 (Pos)
                        df['Pos'] = df['Signal'].shift(1).fillna(0)

                        # 4. 期货真实杠杆盈亏计算核心逻辑
                        # 绝对点数变化
                        df['Point_PnL'] = df['close'] - df['close'].shift(1)

                        # 单手实际盈亏金额 = 点数变化 * 乘数 * 仓位方向
                        df['Cash_PnL_Per_Lot'] = df['Point_PnL'] * multiplier * df['Pos']

                        # 总盈亏 = 单手盈亏 * 手数
                        df['Total_PnL'] = df['Cash_PnL_Per_Lot'] * trade_lots

                        # 动态资金权益 (Equity)
                        df['Equity'] = init_cash + df['Total_PnL'].cumsum()

                        # 占用保证金计算 = 结算价 * 乘数 * 保证金率 * 手数
                        df['Margin_Used'] = df['close'] * multiplier * margin_rate * trade_lots

                        # 5. 渲染专业级图表 (带资金与保证金占用情况)
                        fig = make_subplots(
                            rows=3, cols=1, shared_xaxes=True,
                            vertical_spacing=0.05,
                            row_heights=[0.5, 0.25, 0.25],
                            subplot_titles=("K线与均线", "动态资金权益曲线 (带杠杆)", "保证金占用监控")
                        )

                        # Row 1: K线图
                        fig.add_trace(go.Candlestick(
                            x=df['trade_date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                            name='K线'
                        ), row=1, col=1)
                        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['MA10'], line=dict(color='yellow', width=1),
                                                 name='MA10'), row=1, col=1)
                        fig.add_trace(
                            go.Scatter(x=df['trade_date'], y=df['MA20'], line=dict(color='cyan', width=1), name='MA20'),
                            row=1, col=1)

                        # Row 2: 资金曲线
                        fig.add_trace(go.Scatter(
                            x=df['trade_date'], y=df['Equity'], name='动态权益',
                            line=dict(color='#00ffcc', width=2), fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.1)'
                        ), row=2, col=1)

                        # Row 3: 保证金占用
                        fig.add_trace(go.Scatter(
                            x=df['trade_date'], y=df['Margin_Used'], name='占用保证金',
                            line=dict(color='#ff4b4b', width=1), fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.2)'
                        ), row=3, col=1)

                        fig.update_layout(
                            height=700, template="plotly_dark",
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=40, b=10)
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # 计算几个简单的绩效指标
                        final_equity = df['Equity'].iloc[-1]
                        total_return = (final_equity - init_cash) / init_cash * 100
                        max_margin = df['Margin_Used'].max()

                        c_res1, c_res2, c_res3 = st.columns(3)
                        c_res1.metric("期末总权益", f"¥ {final_equity:,.2f}", f"{total_return:.2f}%")
                        c_res2.metric("最高保证金占用", f"¥ {max_margin:,.2f}")
                        c_res3.metric("资金使用率 (峰值)", f"{(max_margin / init_cash) * 100:.2f}%",
                                      delta_color="inverse")

                except Exception as e:
                    st.error(f"系统运算发生熔断: {e}")
        else:
            st.markdown("""
            <div class="metric-box" style="height: 250px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
                <p>等待主公下达指令</p>
                <h2 style="color: #cbd5e1;">点击左侧 [开始穿透回测] 按钮</h2>
                <p class="sub-text" style="margin-top: 10px;">系统将自动调取 Tushare 数据并结合杠杆进行推演计算</p>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# 🔥 新增功能：期货高频沙盘
# ==========================================
def render_futures_sandbox():
    st.markdown(
        '<div class="glass-card"><h3 style="color:var(--text-color); margin-bottom:0;">🌪️ 期货高频沙盘模拟推演</h3><p class="sub-text">Tick 级盘口模拟、毫秒级信号响应测试与动态滑点侦测。</p></div>',
        unsafe_allow_html=True)
    st.warning("⚠️ 高频警告：期货自带杠杆且波动剧烈，请确保您的‘止损熔断’脚本已装载且经过极寒测试。")

    c_left, c_right = st.columns([1, 2.5])
    with c_left:
        # 模拟高频 L2 DOM 盘口
        st.markdown("""
        <div class="glass-card" style="padding: 15px;">
            <h4 style="margin-top:0; color:#ff4b4b;">卖盘 (Ask)</h4>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖五</span><span>2512</span><span>124</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖四</span><span>2511</span><span>32</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖三</span><span>2510</span><span>15</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖二</span><span>2509</span><span>8</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖一</span><span>2508</span><span>45</span></div>
            <hr style="margin: 10px 0; border-color: rgba(255,255,255,0.1);">
            <h3 style="margin:0; text-align:center; color:#00ffcc; text-shadow: 0 0 10px rgba(0,255,204,0.5);">现价: 2507</h3>
            <hr style="margin: 10px 0; border-color: rgba(255,255,255,0.1);">
            <h4 style="margin-top:0; color:#00ffcc;">买盘 (Bid)</h4>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买一</span><span>2506</span><span>89</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买二</span><span>2505</span><span>12</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买三</span><span>2504</span><span>56</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买四</span><span>2503</span><span>105</span></div>
            <div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买五</span><span>2502</span><span>210</span></div>
        </div>
        """, unsafe_allow_html=True)

    with c_right:
        st.markdown("""
        <div class="metric-box" style="height: 380px; display: flex; flex-direction: column; justify-content: center; align-items: center;">
            <p>高频推演</p>
            <h2 style="color: #00ffcc;">Tick 走势图及 DOM 深度图渲染区</h2>
            <p class="sub-text" style="margin-top: 10px;">(待后续接入 websocket 实时流数据)</p>
        </div>
        """, unsafe_allow_html=True)