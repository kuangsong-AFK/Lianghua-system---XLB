import tushare as ts
import os
import pandas as pd
import time

# 从 config.py 导入 TOKEN（推荐做法）
try:
    from config import TOKEN
except ImportError:
    TOKEN = os.getenv("TUSHARE_TOKEN", "")

if TOKEN:
    ts.set_token(TOKEN)
pro = ts.pro_api() if TOKEN else None


def download_daily_data(ts_code, start_date, end_date):
    """
    获取指定股票的日线行情数据（基础版）
    """
    if pro is None:
        print("缺少 TUSHARE_TOKEN，无法下载数据。")
        return None

    # 确保 data 目录存在
    if not os.path.exists("data"):
        os.makedirs("data")

    path = f"data/{ts_code}.csv"

    # 1. 检查本地是否存在
    if os.path.exists(path):
        print(f"📊 从本地加载数据: {ts_code}")
        df = pd.read_csv(path)
        return df

    # 2. 从网络获取（使用更基础的 daily 接口避免 pro_bar 报错）
    print(f"🌐 正在从 Tushare 下载 {ts_code} ...")
    try:
        # daily 接口返回的数据包括：股票代码、交易日期、开盘价、最高价、最低价、收盘价、昨收价、涨跌额、涨跌幅、成交量、成交额
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

        if df is not None and not df.empty:
            # 存为 CSV 备份
            df.to_csv(path, index=False)
            print(f"✅ {ts_code} 下载成功并保存至本地。")
            return df
        else:
            print(f"❌ 未获取到数据，请检查股票代码 {ts_code} 是否正确或积分是否足够。")
            return None

    except Exception as e:
        print(f"🛑 获取数据时发生错误: {e}")
        return None


# 测试运行
if __name__ == "__main__":
    # 尝试获取平安银行数据测试一下
    test_df = download_daily_data('000001.SZ', '20240101', '20260201')
    if test_df is not None:
        print(test_df.head())
