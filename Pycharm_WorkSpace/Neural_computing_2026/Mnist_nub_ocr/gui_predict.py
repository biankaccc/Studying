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
model.load_state_dict(torch.load("mnist_cnn_best.pth", map_location=device, weights_only=True))
model.eval()

transform = transforms.Compose([
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
        # ========== 核心预处理：提取数字包围盒，居中，适配MNIST格式 ==========
        img_np = np.array(self.image)
        # 找到所有白色像素（手写笔画）
        coords = np.where(img_np > 20)
        if len(coords[0]) == 0:
            self.label_result.config(text="画布为空！")
            return
        ymin, ymax = coords[0].min(), coords[0].max()
        xmin, xmax = coords[1].min(), coords[1].max()
        # 裁剪出数字区域
        digit_crop = img_np[ymin:ymax, xmin:xmax]
        crop_img = Image.fromarray(digit_crop)
        # 保持比例缩放到20×20（MNIST标准，留边）
        crop_img.thumbnail((20, 20), Image.Resampling.LANCZOS)
        # 创建28×28黑色背景，把数字居中粘贴
        mnist_img = Image.new("L", (28, 28), 0)
        paste_x = (28 - crop_img.width) // 2
        paste_y = (28 - crop_img.height) // 2
        mnist_img.paste(crop_img, (paste_x, paste_y))

        # 转tensor + 归一化
        tensor_img = transform(mnist_img).unsqueeze(0).to(device)
        with torch.no_grad():
            out = model(tensor_img)
            prob = torch.softmax(out, dim=1)  # 计算各类概率
            pred = torch.argmax(prob, dim=1).item()
            pred_conf = prob[0, pred].item()  # 获取预测类别的置信度

        self.label_result.config(text=f"识别结果：{pred}，置信度：{pred_conf:.4f}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("手写数字识别")
    app = DrawApp(root)
    root.mainloop()
