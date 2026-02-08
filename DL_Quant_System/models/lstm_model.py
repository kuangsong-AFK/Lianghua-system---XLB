import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler


class LSTMPredictor:
    def __init__(self, sequence_length=10):
        # 使用过去 10 天的数据预测未来
        self.sequence_length = sequence_length
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def prepare_data(self, df):
        # 选择特征列 (基于你之前在 utils 中定义的特征)
        features = ['close', 'MA5', 'MA20', 'ROC5', 'VOLATILITY5']
        data = df[features].values
        target = df['target'].values

        # 归一化
        scaled_data = self.scaler.fit_transform(data)

        X, y = [], []
        for i in range(len(scaled_data) - self.sequence_length):
            X.append(scaled_data[i: i + self.sequence_length])
            y.append(target[i + self.sequence_length])

        return np.array(X), np.array(y)

    def build_model(self, input_shape):
        model = Sequential([
            # 第一层 LSTM
            LSTM(units=50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            # 第二层 LSTM
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            # 输出层：预测具体的涨跌幅百分比
            Dense(units=1)
        ])
        model.compile(optimizer='adam', loss='mse')
        self.model = model
        return model


if __name__ == "__main__":
    from utils.feature_engineering import construct_features
    import os

    # 加载之前下载的数据
    df = pd.read_csv("data/000001.SZ.csv")
    df_features = construct_features(df)

    predictor = LSTMPredictor()
    X, y = predictor.prepare_data(df_features)

    print(f"✅ 数据准备就绪：特征形状 {X.shape}, 标签形状 {y.shape}")

    # 构建并查看模型结构
    model = predictor.build_model((X.shape[1], X.shape[2]))
    model.summary()