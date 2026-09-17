import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import numpy as np

# ===================== 设备 =====================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# ===================== 数据预处理 =====================
train_transform = transforms.Compose([
    transforms.RandomRotation(10),
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

val_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

train_dataset = datasets.MNIST(root="./data", train=True, download=True, transform=train_transform)
test_dataset = datasets.MNIST(root="./data", train=False, download=True, transform=val_transform)

train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=0)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False, num_workers=0)

# ===================== 网络定义 =====================
class MNISTCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool = nn.MaxPool2d(2, 2)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(64 * 12 * 12, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = torch.relu(self.bn1(self.conv1(x)))
        x = torch.relu(self.bn2(self.conv2(x)))
        x = self.pool(x)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        x = self.dropout2(x)
        return self.fc2(x)

model = MNISTCNN().to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9, weight_decay=1e-4)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, "min", patience=2, factor=0.5)

# ===================== 训练/验证函数（已改名val_one_epoch，避开pytest） =====================
def train_one_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss = 0.0
    correct = 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
    avg_loss = total_loss / len(loader)
    acc = correct / len(loader.dataset)
    return avg_loss, acc

def val_one_epoch(model, loader, criterion):
    model.eval()
    total_loss = 0.0
    correct = 0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            total_loss += loss.item()
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
    avg_loss = total_loss / len(loader)
    acc = correct / len(loader.dataset)
    return avg_loss, acc

# ===================== 训练主循环（MAX_EPOCH=3） =====================
max_epoch = 3
patience = 3
best_val_acc = 0.0
early_stop_cnt = 0

# 保存日志列表
train_loss_list = []
train_acc_list = []
val_loss_list = []
val_acc_list = []

for epoch in range(max_epoch):
    print(f"\n==== Epoch {epoch+1}/{max_epoch} ====")
    train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer)
    val_loss, val_acc = val_one_epoch(model, test_loader, criterion)
    scheduler.step(val_loss)

    train_loss_list.append(train_loss)
    train_acc_list.append(train_acc)
    val_loss_list.append(val_loss)
    val_acc_list.append(val_acc)

    print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
    print(f"Val   Loss: {val_loss:.4f} | Val   Acc: {val_acc:.4f}")

    if val_acc > best_val_acc:
        best_val_acc = val_acc
        early_stop_cnt = 0
        torch.save(model.state_dict(), "mnist_cnn_best.pth")
        print("Save best model.")
    else:
        early_stop_cnt +=1
        print(f"Early stop count: {early_stop_cnt}/{patience}")
        if early_stop_cnt >= patience:
            print("=== Early Stop Triggered ===")
            break

# ===================== 保存训练日志 =====================
np.savez("train_log.npz",
         train_loss=np.array(train_loss_list),
         train_acc=np.array(train_acc_list),
         val_loss=np.array(val_loss_list),
         val_acc=np.array(val_acc_list))
print("\n训练日志已保存至 train_log.npz")
print("模型权重保存至 mnist_cnn_best.pth")
