import numpy as np
import matplotlib.pyplot as plt

# 解决中文乱码
# Windows 中文字体
plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False


# 读取保存的训练日志
data = np.load("train_log.npz")
train_loss = data["train_loss"]
train_acc = data["train_acc"]
val_loss = data["val_loss"]
val_acc = data["val_acc"]

# 打印统计信息
print("======= 训练结果统计 =======")
print(f"训练轮数：{len(train_loss)}")
print(f"最终训练集损失：{train_loss[-1]:.4f}")
print(f"最终训练集精度：{train_acc[-1]:.4f}")
print(f"最终验证集损失：{val_loss[-1]:.4f}")
print(f"最终验证集精度：{val_acc[-1]:.4f}")
print(f"最高验证精度：{np.max(val_acc):.4f}")

# 绘图
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12,5))
epochs = np.arange(1, len(train_loss)+1)

ax1.plot(epochs, train_loss, marker='o', label="训练损失")
ax1.plot(epochs, val_loss, marker='s', label="验证损失")
ax1.set_xlabel("Epoch")
ax1.set_ylabel("Loss")
ax1.set_title("损失曲线")
ax1.legend()
ax1.grid(True)

ax2.plot(epochs, train_acc, marker='o', label="训练精度")
ax2.plot(epochs, val_acc, marker='s', label="验证精度")
ax2.set_xlabel("Epoch")
ax2.set_ylabel("Accuracy")
ax2.set_title("精度曲线")
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()
