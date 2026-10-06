# model_no_dropout.py
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
from tqdm import tqdm

DATA_FILE = "bike_data.pt"
BATCH_SIZE = 1024
N_EPOCHS = 500
LR = 0.01

class BaselineModel(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 250),
            nn.ReLU(),
            nn.Linear(250, 150),
            nn.ReLU(),
            nn.Linear(150, 50),
            nn.ReLU(),
            nn.Linear(50, 25),
            nn.ReLU(),
            nn.Linear(25, 1)
        )
    def forward(self, x):
        return self.net(x)

def train():
    # 本地可信文件，weights_only=False
    ckpt = torch.load(DATA_FILE, weights_only=False)
    X_train, y_train = ckpt["X_train"], ckpt["y_train"]
    X_val, y_val = ckpt["X_val"], ckpt["y_val"]
    input_dim = ckpt["input_dim"]

    train_dataset = TensorDataset(X_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

    model = BaselineModel(input_dim)
    loss_fn = nn.MSELoss()
    optimizer = optim.SGD(model.parameters(), lr=LR)

    train_hist = []
    val_hist = []

    # 外层epoch进度条
    pbar = tqdm(range(N_EPOCHS), desc="No Dropout Training")
    for epoch in pbar:
        model.train()
        total_train_loss = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            pred = model(batch_x)
            loss = loss_fn(pred, batch_y)
            loss.backward()
            optimizer.step()
            total_train_loss += loss.item() * batch_x.shape[0]
        avg_train_loss = total_train_loss / len(train_loader.dataset)

        model.eval()
        with torch.no_grad():
            val_pred = model(X_val)
            val_loss = loss_fn(val_pred, y_val).item()
        train_hist.append(avg_train_loss)
        val_hist.append(val_loss)

        # 实时更新进度条信息
        pbar.set_postfix({"train_loss": f"{avg_train_loss:.4f}", "val_loss": f"{val_loss:.4f}"})

    # 保存训练历史
    torch.save({"train_loss": train_hist, "val_loss": val_hist}, "history_no_dropout.pt")
    print("\n==== No Dropout Model Finished ====")
    print(f"Min Val Loss: {min(val_hist):.6f}, at epoch {np.argmin(val_hist)}")
    return train_hist, val_hist

if __name__ == "__main__":
    train()
