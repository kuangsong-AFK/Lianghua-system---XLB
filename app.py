import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "DL_Quant_System"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

runpy.run_path(str(APP_DIR / "app.py"), run_name="__main__")
