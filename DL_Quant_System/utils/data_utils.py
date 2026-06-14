import os

import pandas as pd
import tushare as ts

try:
    from data_loader import fetch_stock_data
    from secure_config import get_secret
except ImportError:
    from DL_Quant_System.data_loader import fetch_stock_data
    from DL_Quant_System.secure_config import get_secret


TOKEN = get_secret("TUSHARE_TOKEN") or os.getenv("TUSHARE_TOKEN", "")
if TOKEN:
    try:
        ts.set_token(TOKEN)
    except Exception:
        pass


def download_daily_data(ts_code, start_date, end_date):
    """Load daily stock data from Tushare first, then local CSV samples."""
    df, source = fetch_stock_data(
        ts_code,
        adj=None,
        start_date=start_date,
        tushare_token=TOKEN,
        tushare_module=ts,
    )
    if df is None or df.empty:
        print(f"no market data found for {ts_code}")
        return None

    if end_date and "trade_date" in df.columns:
        end = pd.to_datetime(str(end_date).replace("-", ""), errors="coerce")
        df = df[pd.to_datetime(df["trade_date"], errors="coerce") <= end]

    print(f"loaded {ts_code} from {source}")
    return df.reset_index(drop=True)


if __name__ == "__main__":
    test_df = download_daily_data("000001.SZ", "20240101", "20260201")
    if test_df is not None:
        print(test_df.head())
