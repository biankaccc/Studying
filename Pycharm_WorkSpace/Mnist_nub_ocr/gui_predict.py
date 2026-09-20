import torch
import torch.nn as nn
from torchvision import transforms
import tkinter as tk
from PIL import Image, ImageDraw
import numpy as np

# ===================== 网络定义，必须和训练文件保持一致 =====================
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

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = MNISTCNN().to(device)
# weights_only=True 消除警告
model.load_state_dict(torch.load("mnist_cnn_best.pth", map_location=device, weights_only=True))
model.eval()

transform = transforms.Compose([
    transforms.Resize((28, 28)),
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])

# ===================== GUI画布 =====================
class DrawApp:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=280, height=280, bg="black")
        self.canvas.pack()
        self.btn_predict = tk.Button(root, text="识别数字", command=self.predict)
        self.btn_predict.pack(side=tk.LEFT, padx=10, pady=5)
        self.btn_clear = tk.Button(root, text="清空画布", command=self.clear)
        self.btn_clear.pack(side=tk.LEFT, padx=10, pady=5)
        self.label_result = tk.Label(root, text="结果：", font=("Arial",20))
        self.label_result.pack(pady=10)

        self.image = Image.new("L", (280, 280), 0)
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.bind("<B1-Motion>", self.paint)

    def paint(self, event):
        r = 12
        x1, y1 = event.x - r, event.y - r
        x2, y2 = event.x + r, event.y + r
        self.canvas.create_oval(x1,y1,x2,y2, fill="white", outline="white")
        self.draw.ellipse([x1,y1,x2,y2], fill=255)

    def clear(self):
        self.canvas.delete("all")
        self.image = Image.new("L", (280, 280), 0)
        self.draw = ImageDraw.Draw(self.image)
        self.label_result.config(text="结果：")

    def predict(self):
        img = self.image.resize((28,28))
        tensor_img = transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            out = model(tensor_img)
            pred = torch.argmax(out, dim=1).item()
        self.label_result.config(text=f"识别结果：{pred}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("手写数字识别")
    app = DrawApp(root)
    root.mainloop()
