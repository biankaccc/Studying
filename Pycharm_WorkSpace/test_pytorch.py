import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# ===================== 核心：自动用你的 RTX4070 GPU =====================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("✅ 使用设备:", device)

# ===================== 生成虚拟数据（不用下载！秒加载）=====================
# 生成假的图片和标签（模拟MNIST）
x = torch.randn(10000, 1, 28, 28)  # 1万张图片
y = torch.randint(0, 10, (10000,))  # 1万个标签
dataset = TensorDataset(x, y)
train_loader = DataLoader(dataset, batch_size=64, shuffle=True)


# ===================== 定义CNN模型 =====================
class CNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x


model = CNN().to(device)

# ===================== 损失函数 & 优化器 =====================
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)

# ===================== 开始训练（GPU加速）=====================
print("🚀 训练开始...")
for epoch in range(5):
    model.train()
    total_loss = 0
    for data, label in train_loader:
        data, label = data.to(device), label.to(device)

        optimizer.zero_grad()
        outputs = model(data)
        loss = criterion(outputs, label)
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
    print(f"Epoch {epoch + 1}  Loss: {total_loss / len(train_loader):.4f}")

print("🎉 训练完成！GPU 正常工作！")