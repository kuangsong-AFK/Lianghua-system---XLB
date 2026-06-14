import runpy
import sys
import traceback
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "DL_Quant_System"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

try:
    runpy.run_path(str(APP_DIR / "app.py"), run_name="__main__")
except Exception as exc:
    st.error("应用启动失败，下面是 Streamlit Cloud 捕获到的真实错误。")
    st.exception(exc)
    with st.expander("完整 traceback"):
        st.code(traceback.format_exc(), language="python")
