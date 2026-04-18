import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader
import time
import os
from datetime import datetime


# ==========================================
# 路线二：锻造神兵 DA-LSTM (双重注意力网络)
# ==========================================
class DA_LSTM(nn.Module):
    def __init__(self, input_size=6, hidden_size=64, num_layers=2, dropout=0.2):
        super(DA_LSTM, self).__init__()
        self.hidden_size = hidden_size

        # 特征注意力层 (Feature Attention)
        self.feature_attn = nn.Sequential(
            nn.Linear(input_size, input_size),
            nn.Tanh(),
            nn.Linear(input_size, input_size)
        )

        # 加厚装甲：双层 LSTM + Dropout 防止高频数据过拟合
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)

        # 时间注意力层 (Temporal Attention)
        self.temporal_attn = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )

        self.fc_out = nn.Linear(hidden_size, 1)

    def forward(self, x):
        f_weights = F.softmax(self.feature_attn(x), dim=-1)
        x_attended = x * f_weights
        lstm_out, _ = self.lstm(x_attended)
        t_weights = F.softmax(self.temporal_attn(lstm_out), dim=1)
        context_vector = torch.sum(t_weights * lstm_out, dim=1)
        return self.fc_out(context_vector)


# ==========================================
# 路线一：独家“利润导向”不对称损失函数
# ==========================================
class AsymmetricProfitLoss(nn.Module):
    def __init__(self, penalty_multiplier=10.0):
        super(AsymmetricProfitLoss, self).__init__()
        self.penalty_multiplier = penalty_multiplier
        self.mse = nn.MSELoss()

    def forward(self, pred_return, true_return):
        # 1. 基础回归误差 (保底拟合)
        base_loss = self.mse(pred_return, true_return)

        # 2. 方向判断：相乘小于0代表方向反了
        # 使用 relu 截断：只有当 (-pred_return * true_return) > 0 时才激活惩罚
        wrong_direction = torch.relu(-pred_return * true_return)

        # 3. 惩罚放大器：错得越离谱，方向越反，惩罚越重
        # 加上 torch.abs() 确保惩罚力度与偏差绝对值挂钩
        penalty = torch.mean(wrong_direction * torch.abs(true_return - pred_return)) * self.penalty_multiplier

        # 最终军法：底线误差 + 致命方向惩罚
        return base_loss + penalty


# ==========================================
# 统帅中军：训练与炼丹主程序
# ==========================================
def train_model():
    print("===" * 15)
    print("🔥 小吕布量化 Pro - 终极三位一体算法启动 🔥")
    print("===" * 15)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🚀 当前挂载算力核心: {device.type.upper()}")

    data_path = 'high_freq_arsenal_SA.pt'
    if not os.path.exists(data_path):
        print("❌ 粮草库为空！请先运行 data_forge.py！")
        return

    checkpoint = torch.load(data_path, map_location='cpu', weights_only=False)
    X_tensor = checkpoint['X']
    y_tensor = checkpoint['y']

    train_size = int(len(X_tensor) * 0.8)
    X_train, y_train = X_tensor[:train_size], y_tensor[:train_size]
    X_test, y_test = X_tensor[train_size:], y_tensor[train_size:]

    batch_size = 64
    train_loader = DataLoader(TensorDataset(X_train, y_train), batch_size=batch_size, shuffle=True)

    print(f"📦 战区划分完毕: 训练集 {len(X_train)} 个，测试集 {len(X_test)} 个。")

    # 部署神兵与新军法 (AsymmetricProfitLoss)
    model = DA_LSTM(input_size=6, hidden_size=64, num_layers=2).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # 启用不对称利润损失函数，设置 15 倍惩罚！
    criterion = AsymmetricProfitLoss(penalty_multiplier=15.0)

    epochs = 40  # 因为损失函数更严苛，稍微增加几轮试炼

    print("\n⚔️ 全军出击！开始【利润导向】深度反向传播...")
    start_time = time.time()

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0

        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)

            optimizer.zero_grad()
            predictions = model(batch_X)

            # 【核心微操】：计算涨跌幅 (Return) 而非绝对价格
            # batch_X[:, -1, 0] 取的是滑窗中最后一天/一分钟的收盘价
            current_price = batch_X[:, -1, 0].unsqueeze(1)
            pred_return = predictions - current_price
            true_return = batch_y - current_price

            # 使用新军法审判
            loss = criterion(pred_return, true_return)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * batch_X.size(0)

        train_loss /= len(train_loader.dataset)

        if (epoch + 1) % 5 == 0 or epoch == 0:
            model.eval()
            with torch.no_grad():
                test_preds = model(X_test.to(device))
                test_current_price = X_test[:, -1, 0].unsqueeze(1).to(device)
                t_pred_return = test_preds - test_current_price
                t_true_return = y_test.to(device) - test_current_price
                test_loss = criterion(t_pred_return, t_true_return).item()
            print(f"🔄 Epoch [{epoch + 1}/{epochs}] | 训练军法误差: {train_loss:.6f} | 测试军法误差: {test_loss:.6f}")

    print(f"\n🎉 炼丹完成！总耗时: {time.time() - start_time:.2f} 秒")

    # 模型入库与新老交替程序
    print("\n📦 正在执行模型入库与新老交替程序...")
    model_dir = 'models'
    archive_dir = os.path.join(model_dir, 'archive')
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(archive_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    latest_path = os.path.join(model_dir, 'da_lstm_sa_latest.pth')
    backup_path = os.path.join(archive_dir, f'da_lstm_sa_{timestamp}_asymmetric.pth')

    torch.save(model.state_dict(), backup_path)
    torch.save(model.state_dict(), latest_path)

    print(f"🗄️ 带有【不对称利润特性】的历史战绩已归档: {os.path.abspath(backup_path)}")
    print(f"👑 最新实战杀戮模型已覆盖完毕: {os.path.abspath(latest_path)}")


if __name__ == "__main__":
    train_model()