import akshare as ak
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import torch
import os


def fetch_high_freq_data(symbol="SA0", period="5"):
    """
    📡 侦察营：利用 AkShare 白嫖高频分钟线数据
    symbol: SA0 代表纯碱连续主力合约
    period: 5 代表 5 分钟 K 线
    """
    print(f"📡 正在无视收费墙，强行拉取 {symbol} 的 {period} 分钟级高频数据...")
    try:
        # 拉取新浪期货分钟线数据
        df = ak.futures_zh_minute_sina(symbol=symbol, period=period)
        # 统一列名以适配咱们的装甲
        df = df.rename(columns={'datetime': 'trade_time'})
        # 确保数据类型为浮点数
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        print(f"✅ 成功拉取 {len(df)} 根高频 K 线！")
        return df
    except Exception as e:
        print(f"❌ 数据拉取失败，请检查网络或合约代码: {e}")
        return None


def forge_micro_features(df):
    """
    ⚔️ 锻造营：将粗糙的 OHLCV 锻造为高维微观特征
    """
    print("⚔️ 正在锻造量化微观结构张量...")

    # 基础特征：对数收益率 (比普通涨跌幅更适合神经网络)
    df['Log_Ret'] = np.log(df['close'] / df['close'].shift(1))

    # 特征1：高频波动率 (Realized Volatility) - 捕捉市场情绪的剧烈程度
    df['Volatility'] = df['Log_Ret'].rolling(window=12).std()

    # 特征2：微观买卖力量失衡 (近似 OBI)
    # 逻辑：收盘价越靠近最高价，买盘越强(+)；靠近最低价，卖盘越强(-)
    df['Micro_Imbalance'] = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'] + 1e-8)

    # 特征3：量价动能 (成交量激增且伴随上涨为正，下跌为负)
    df['Volume_Momentum'] = df['volume'].pct_change() * np.sign(df['Log_Ret'])

    # 剔除因为计算均线和位移产生的 NaN 空值
    df = df.dropna().reset_index(drop=True)
    return df


def build_tensor_arsenal(df, seq_len=60):
    """
    📦 打包营：将二维表格切片为 PyTorch 最爱的三维张量
    seq_len: 滑动窗口长度（60根5分钟K线 = 1个交易日左右）
    """
    print(f"📦 正在按滑窗 {seq_len} 打包三维张量...")

    # 提取我们锻造的核心特种弹药
    feature_cols = ['close', 'volume', 'Log_Ret', 'Volatility', 'Micro_Imbalance', 'Volume_Momentum']
    data_matrix = df[feature_cols].values

    # 归一化：将所有数值无情压缩到 0~1 之间，防止神经网络梯度爆炸
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data_matrix)

    X, y = [], []
    # 滑窗切割：用过去 seq_len 个 Tick，预测第 seq_len+1 个 Tick 的收盘价
    for i in range(seq_len, len(data_scaled) - 1):
        X.append(data_scaled[i - seq_len: i, :])  # 历史特征矩阵
        y.append(data_scaled[i + 1, 0])  # T+1 的目标价 (索引0对应close)

    X_tensor = torch.tensor(np.array(X), dtype=torch.float32)
    y_tensor = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(1)  # 增加一个维度变为 [batch, 1]

    print(f"✅ 粮草打包完毕！\n特征矩阵 X 维度: {X_tensor.shape} (批次, 滑窗, 特征数)\n目标矩阵 y 维度: {y_tensor.shape}")
    return X_tensor, y_tensor, scaler


if __name__ == "__main__":
    print("===" * 15)
    print("🚀 小吕布量化 Pro - 本地高频数据兵工厂启动 🚀")
    print("===" * 15)

    # 1. 统帅发令：拉取纯碱 (SA0) 5 分钟数据
    raw_df = fetch_high_freq_data(symbol="SA0", period="5")

    if raw_df is not None:
        # 2. 锻造微观特征
        featured_df = forge_micro_features(raw_df)

        # 3. 切片打包 (滑窗设为 60)
        X, y, scaler = build_tensor_arsenal(featured_df, seq_len=60)

        # 4. 将打包好的粮草存入本地军械库
        save_path = 'high_freq_arsenal_SA.pt'
        torch.save({'X': X, 'y': y, 'scaler': scaler}, save_path)
        print(f"💾 战备物资已硬核写入本地硬盘：{os.path.abspath(save_path)}")
        print("💡 第一战役大获全胜！随时可送入 RTX 5070 进行炼丹！")