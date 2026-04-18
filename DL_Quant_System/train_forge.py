import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
import time
import os


# ==========================================
# 1. 锻造神兵：DA-LSTM (双重注意力长短期记忆网络)
# ==========================================
class DA_LSTM(nn.Module):
    def __init__(self, input_size=6, hidden_size=64, num_layers=1):
        super(DA_LSTM, self).__init__()
        self.hidden_size = hidden_size

        # 特征注意力层 (Feature Attention) - 告诉模型"看哪个因子"
        self.feature_attn = nn.Sequential(
            nn.Linear(input_size, input_size),
            nn.Tanh(),
            nn.Linear(input_size, input_size)
        )

        # 核心记忆中枢 (LSTM)
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)

        # 时间注意力层 (Temporal Attention) - 告诉模型"看哪根K线"
        self.temporal_attn = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )

        # 输出层：预测 T+1 的绝对价格 (归一化后)
        self.fc_out = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # 1. 激活特征注意力
        f_weights = F.softmax(self.feature_attn(x), dim=-1)
        x_attended = x * f_weights

        # 2. LSTM 串行推演
        lstm_out, _ = self.lstm(x_attended)

        # 3. 激活时间注意力
        t_weights = F.softmax(self.temporal_attn(lstm_out), dim=1)
        context_vector = torch.sum(t_weights * lstm_out, dim=1)

        # 4. 致命一击：输出最终预测
        return self.fc_out(context_vector)


# ==========================================
# 2. 统帅中军：训练与炼丹主程序
# ==========================================
def train_model():
    print("===" * 15)
    print("🔥 小吕布量化 Pro - RTX 5070 炼丹炉启动 🔥")
    print("===" * 15)

    # 1. 雷达侦测显卡
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🚀 当前挂载算力核心: {device.type.upper()} (准备迎接算力狂飙！)")

    # 2. 提取粮草
    data_path = 'high_freq_arsenal_SA.pt'
    if not os.path.exists(data_path):
        print("❌ 粮草库为空！请先运行 data_forge.py！")
        return

    checkpoint = torch.load(data_path, map_location='cpu', weights_only=False)
    X_tensor = checkpoint['X']
    y_tensor = checkpoint['y']

    # 划分前线战区 (80% 训练集, 20% 测试集)
    train_size = int(len(X_tensor) * 0.8)
    X_train, y_train = X_tensor[:train_size], y_tensor[:train_size]
    X_test, y_test = X_tensor[train_size:], y_tensor[train_size:]

    # 装填弹夹 (DataLoader)
    batch_size = 64
    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True)

    print(f"📦 战区划分完毕: 训练集 {len(X_train)} 个样本，测试集 {len(X_test)} 个样本。")

    # 3. 部署神兵与军规
    model = DA_LSTM(input_size=6, hidden_size=64).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()  # 首战使用均方误差保底

    epochs = 30  # 试炼轮数

    print("\n⚔️ 全军出击！开始深度反向传播训练...")
    start_time = time.time()

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0

        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)

            # 前向推演
            optimizer.zero_grad()
            predictions = model(batch_X)

            # 计算误差并反向传播
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * batch_X.size(0)

        train_loss /= len(train_loader.dataset)

        # 每 5 轮汇报一次战况
        if (epoch + 1) % 5 == 0 or epoch == 0:
            # 在测试集上进行火力侦察
            model.eval()
            with torch.no_grad():
                test_preds = model(X_test.to(device))
                test_loss = criterion(test_preds, y_test.to(device)).item()
            print(f"🔄 Epoch [{epoch + 1}/{epochs}] | 训练误差(Loss): {train_loss:.6f} | 阵地测试误差: {test_loss:.6f}")

    end_time = time.time()
    print(f"\n🎉 炼丹完成！总耗时: {end_time - start_time:.2f} 秒 (RTX 5070 简直是性能怪兽！)")

    # 4. 凝结仙丹 (导出权重文件)
    os.makedirs('models', exist_ok=True)
    save_path = 'models/da_lstm_sa_weights_v1.pth'
    torch.save(model.state_dict(), save_path)
    print(f"💊 极简仙丹(权重文件)已提取！保存在: {os.path.abspath(save_path)}")
    print("💡 第二战役圆满收官！这颗仙丹随时可以空投到 Streamlit 云端指挥台！")


if __name__ == "__main__":
    train_model()