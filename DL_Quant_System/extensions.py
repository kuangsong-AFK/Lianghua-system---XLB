# ==========================================
# 文件名：extensions.py (扩展功能先锋营)
# 功能：极客 IDE、AkShare 期货、高频沙盘
# ==========================================
import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import time
import traceback
import math
import re
import pandas as pd
import numpy as np
from datetime import datetime

try:
    from streamlit import fragment as st_fragment
except ImportError:
    try:
        from streamlit import experimental_fragment as st_fragment
    except ImportError:
        st_fragment = lambda f: f

try:
    import akshare as ak

    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

SUB_PATTERN = re.compile(r'^SUB(\d+)_')


def summon_global_3d_lulu():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lulu.glb")
    if not os.path.exists(p):
        return
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    components.html(f"""
    <script>
        if (!window.parent.__LULU_ON__) {{
            window.parent.__LULU_ON__ = true;
            const l = (s) => new Promise(r => {{ const x = window.parent.document.createElement('script'); x.src = s; x.onload = r; window.parent.document.head.appendChild(x); }});
            setTimeout(async () => {{
                await l("https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js");
                await l("https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js");
                const doc = window.parent.document;
                const box = doc.createElement('div');
                box.style.cssText = "position:fixed; bottom:20px; right:20px; width:280px; height:280px; z-index:99999; cursor:grab; pointer-events:none;";
                doc.body.appendChild(box);
                const scene = new window.parent.THREE.Scene();
                const cam = new window.parent.THREE.PerspectiveCamera(45, 1, 0.1, 100); cam.position.set(0, 0.8, 5.5);
                const ren = new window.parent.THREE.WebGLRenderer({{ alpha: true, antialias: true }});
                ren.setSize(280, 280); box.appendChild(ren.domElement);
                scene.add(new window.parent.THREE.AmbientLight(0xffffff, 0.9));
                const dl = new window.parent.THREE.DirectionalLight(0xffffff, 1.2); dl.position.set(5,10,5); scene.add(dl);
                let mx;
                new window.parent.THREE.GLTFLoader().load("data:application/octet-stream;base64,{b64}", (g) => {{
                    g.scene.position.y = -1.2; scene.add(g.scene);
                    if(g.animations.length) {{ mx = new window.parent.THREE.AnimationMixer(g.scene); mx.clipAction(g.animations[0]).play(); }}
                    const ck = new window.parent.THREE.Clock();
                    const ani = () => {{ window.parent.requestAnimationFrame(ani); if(mx) mx.update(ck.getDelta()); ren.render(scene, cam); }};
                    ani();
                }});
            }}, 500);
        }}
    </script>
    """, height=0, width=0)


def safe_exec_fut_strategy(code, df):
    l_vars = {}
    exec(code.replace("pandas.np", "np"), {"pd": pd, "np": np, "math": math}, l_vars)
    fn = next((v for k, v in l_vars.items() if callable(v)), None)
    if fn:
        res = fn(df)
        if 'Signal' in res.columns:
            res['Signal'] = np.sign(res['Signal'].fillna(0).round(1)).astype(int)
        return res
    return df


def render_fut_charts(df):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    m_cols = [c for c in df.columns if c.startswith('MAIN_')]
    s_dict = {}
    for c in df.columns:
        if m := SUB_PATTERN.match(c):
            s_dict.setdefault(m.group(1), []).append(c)

    fig = make_subplots(
        rows=2 + len(s_dict), cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.5, 0.15] + [0.35 / max(1, len(s_dict))] * len(s_dict)
    )

    xl = df['trade_date'].dt.strftime('%Y-%m-%d' if df['trade_date'].dt.time.nunique() <= 1 else '%m-%d %H:%M')

    fig.add_trace(go.Candlestick(x=xl, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K线'),
                  row=1, col=1)

    colors = ['#FFFF00', '#FF00FF', '#00FFFF', '#FFFFFF']
    for i, c in enumerate(m_cols):
        fig.add_trace(go.Scatter(x=xl, y=df[c], name=c, line=dict(color=colors[i % 4], width=1.2)), row=1, col=1)

    if 'Signal' in df.columns:
        for sig, nm, clr, sym, off in [(1, '买', '#00FFFF', 'triangle-up', 0.95),
                                       (-1, '卖', '#FF00FF', 'triangle-down', 1.05)]:
            mask = df['Signal'] == sig
            fig.add_trace(
                go.Scatter(
                    x=xl[mask],
                    y=df.loc[mask, 'Low' if sig == 1 else 'High'] * off,
                    mode='markers',
                    marker=dict(symbol=sym, size=14, color=clr),
                    name=nm
                ),
                row=1, col=1
            )

    fig.add_trace(go.Bar(x=xl, y=df.get('Volume', np.zeros(len(df))),
                         marker_color=np.where(df['Close'] >= df['Open'], '#FD1050', '#00FF00')), row=2, col=1)

    for idx, k in enumerate(sorted(s_dict.keys(), key=int)):
        for i, c in enumerate(s_dict[k]):
            if 'HIST' in c.upper():
                t = go.Bar(x=xl, y=df[c], marker_color=np.where(df[c] >= 0, '#FD1050', '#00FF00'))
            else:
                t = go.Scatter(x=xl, y=df[c], line=dict(color=colors[i % 4]))
            fig.add_trace(t, row=3 + idx, col=1)

    fig.update_layout(height=500 + len(s_dict) * 150, template="none", paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', showlegend=False, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(type='category', categoryorder='array', categoryarray=xl, nticks=8, showgrid=True,
                     gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
    return fig


def render_ide_page():
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">💻 极客量化 IDE</h3></div>',
                unsafe_allow_html=True)
    def_code = "def generate_signals(df):\n    df['MAIN_MA5'] = df['Close'].rolling(5).mean()\n    df['Signal'] = np.where(df['Close'] > df['MAIN_MA5'], 1, -1)\n    return df"
    code = st.session_state.get('generated_code', '') or def_code

    c1, c2 = st.columns([2.2, 1.8])
    with c1:
        st.markdown("#### ⌨️ 策略编辑区")
        user_code = st.text_area("Code", value=code, height=450, label_visibility="collapsed")
        b1, b2 = st.columns(2)
        if b1.button("💾 同步保存至中枢", type="primary", use_container_width=True):
            st.session_state.generated_code = user_code
            st.success("已注入引擎！")
        run_debug = b2.button("🐞 运行防爆测试", use_container_width=True)

    with c2:
        st.markdown("#### 🖥️ Console")
        if run_debug:
            try:
                t0 = time.time()
                d_df = pd.DataFrame({
                    'trade_date': pd.date_range('2024', periods=100),
                    'Open': np.random.uniform(2000, 2100, 100),
                    'Close': np.random.uniform(2000, 2100, 100)
                })
                res = safe_exec_fut_strategy(user_code, d_df)
                st.success(f"✅ 编译通过！耗时: {time.time() - t0:.4f}s")
                if 'Signal' in res.columns:
                    st.json(res['Signal'].value_counts().to_dict())
            except Exception as e:
                st.error("❌ 编译失败")
                st.code(str(e))


def render_futures_backtest():
    if not HAS_AKSHARE:
        return st.error("需执行: pip install akshare")

    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">🔗 期货全量审计</h3></div>',
                unsafe_allow_html=True)

    if "fut_bt_run" not in st.session_state:
        st.session_state.fut_bt_run = False

    c1, c2 = st.columns([1, 3])
    with c1:
        code = st.text_input("代码", "")
        freq_map = {"日线": "D", "30分钟": "30", "5分钟": "5"}
        freq = freq_map[st.selectbox("周期", list(freq_map.keys()), index=1)]

        if st.button("🚀 开始回测", type="primary", use_container_width=True):
            st.session_state.fut_bt_run = True

    with c2:
        if st.session_state.fut_bt_run and code:
            with st.spinner("调用 AkShare..."):
                real_code = code.upper().split('.')[0]
                df = None
                try:
                    if freq == 'D':
                        df = ak.futures_zh_daily_sina(real_code)
                    else:
                        df = ak.futures_zh_minute_sina(real_code, freq)
                except Exception:
                    pass

                if df is None or df.empty:
                    st.warning(f"⚠️ 触发容灾，生成 {freq} 模拟数据")
                    bp = 3000 if 'RB' in real_code else 2000

                    closes_array = np.random.normal(0, bp * 0.0015, 399).cumsum()
                    closes = bp + np.insert(closes_array, 0, 0)

                    df = pd.DataFrame({
                        'datetime': pd.date_range(end=datetime.now(), periods=400, freq='T'),
                        'close': closes
                    })
                    df['open'] = df['close'].shift(1).fillna(bp)
                    df['high'] = df['close'] + 5
                    df['low'] = df['close'] - 5
                    df['volume'] = np.random.randint(1000, 5000, 400)

                df.rename(columns={'datetime': 'trade_date', 'date': 'trade_date'}, inplace=True, errors='ignore')
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df.rename(columns=lambda x: x.capitalize() if x in ['open', 'high', 'low', 'close', 'volume'] else x,
                          inplace=True)

                df['MAIN_MA5'] = df['Close'].rolling(5).mean()
                df['MAIN_MA20'] = df['Close'].rolling(20).mean()

                if st.session_state.get('generated_code'):
                    try:
                        df = safe_exec_fut_strategy(st.session_state.generated_code, df)
                    except Exception:
                        df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)
                else:
                    df['Signal'] = np.where(df['MAIN_MA5'] > df['MAIN_MA20'], 1, -1)

                df['Pos'] = df.get('Signal', pd.Series([0] * len(df))).replace(0, np.nan).ffill().fillna(0)

                df['Long_PnL'] = np.where(df['Pos'].shift(1) == 1, df['Close'].diff().fillna(0) * 10 * 10, 0)
                df['Short_PnL'] = np.where(df['Pos'].shift(1) == -1, -df['Close'].diff().fillna(0) * 10 * 10, 0)
                df['Equity'] = 1000000 + (df['Long_PnL'] + df['Short_PnL']).cumsum()

                cx = st.columns(4)
                ret = (df['Equity'].iloc[-1] - 1000000) / 1000000
                cx[0].metric("总收益", f"{ret * 100:.2f}%")
                cx[1].metric("终值", f"{df['Equity'].iloc[-1]:.0f}")

                st.plotly_chart(render_fut_charts(df), use_container_width=True)


@st_fragment
def render_futures_sandbox():
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">🌪️ 期货高频沙盘推演</h3></div>',
                unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    bp = c1.number_input("基准价", 2000)
    spd = c2.slider("刷新(s)", 0.1, 1.0, 0.5)
    is_run = c3.toggle("🚀 启动引擎")

    ph_l, ph_r = st.columns([1, 2.5])
    dom, cht = ph_l.empty(), ph_r.empty()

    if is_run:
        cp = bp
        hist = []
        while is_run:
            import plotly.graph_objects as go

            cp += np.random.choice([-2, -1, 0, 1, 2])
            hist.append(cp)
            hist = hist[-100:]

            asks_html = "".join([
                                    f'<div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>卖{5 - i}</span><span>{cp + 5 - i}</span><span>{np.random.randint(10, 500)}</span></div>'
                                    for i in range(5)])
            bids_html = "".join([
                                    f'<div style="display:flex; justify-content:space-between; color:#cbd5e1;"><span>买{i + 1}</span><span>{cp - i - 1}</span><span>{np.random.randint(10, 500)}</span></div>'
                                    for i in range(5)])

            dom.markdown(f"""
            <div class="glass-card" style="padding:15px;">
                <h4 style="color:#ff4b4b;">卖盘</h4>
                {asks_html}
                <hr>
                <h3 style="text-align:center; color:{'#FD1050' if np.random.rand() > 0.5 else '#00FF00'};">现价: {cp}</h3>
                <hr>
                <h4 style="color:#00ffcc;">买盘</h4>
                {bids_html}
            </div>
            """, unsafe_allow_html=True)

            fig = go.Figure(go.Scatter(y=hist, fill='tozeroy', line=dict(color='#00bfff')))
            fig.update_layout(height=380, template="plotly_dark", margin=dict(l=0, r=0, t=10, b=0))
            cht.plotly_chart(fig, use_container_width=True, key=f"s_{time.time()}")

            time.sleep(spd)


def render_new_features_page():
    st.markdown('<div class="glass-card"><h3 style="margin-bottom:0;">🧩 插件中心已稳定</h3></div>',
                unsafe_allow_html=True)