import pandas as pd
import numpy as np


def construct_features(df):
    """
    输入原始行情数据，输出带特征的数据集
    """
    # 确保按日期升序排列（Tushare 返回通常是降序）
    df = df.sort_values('trade_date').reset_index(drop=True)

    # 1. 基础价格特征
    # 计算 5 日和 20 日移动平均线
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()

    # 2. 动量特征 (Momentum)
    # 5日涨跌幅
    df['ROC5'] = df['close'].pct_change(periods=5)

    # 3. 波动率特征
    # 5日收益率的标准差
    df['VOLATILITY5'] = df['close'].pct_change().rolling(window=5).std()

    # 4. 预测目标 (Label): 这里的目标是预测下一天的收盘价涨跌幅
    # 我们将明天的 pct_chg 向上平移，作为今天的 target
    df['target'] = df['pct_chg'].shift(-1)

    # 5. 清洗数据：删除因为滚动计算产生的空值 (NaN)
    df = df.dropna()

    return df


if __name__ == "__main__":
    # 测试代码
    import os

    file_path = "data/000001.SZ.csv"
    if os.path.exists(file_path):
        raw_data = pd.read_csv(file_path)
        feature_data = construct_features(raw_data)
        print("✅ 特征构建完成！当前特征列：")
        print(feature_data[['trade_date', 'close', 'MA5', 'MA20', 'target']].head())