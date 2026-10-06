# gui_predict.py
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw
import torch
import torch.nn as nn
import torchvision.transforms as TF
from torchvision.transforms import ToTensor

# ===================== 1. 模型定义【一字不差复制训练脚本的MNISTCNN】 =====================
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

# ===================== 2. 加载模型 =====================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = MNISTCNN().to(device)
# ⚠️ 文件名必须和训练保存一致：mnist_cnn_best.pth
checkpoint = torch.load("mnist_cnn_best.pth", map_location=device, weights_only=True)
model.load_state_dict(checkpoint)
model.eval()

# MNIST标准归一化（和训练代码必须一模一样）
transform = TF.Compose([
    ToTensor(),
    TF.Normalize((0.1307,), (0.3081,))
])

# ===================== 3. GUI画板设置 =====================
class DigitGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("手写数字识别")
        self.canvas_size = 400
        self.brush_size = 18
        self.last_x = None
        self.last_y = None

        # 画布
        self.canvas = tk.Canvas(root, bg="black", width=self.canvas_size, height=self.canvas_size)
        self.canvas.pack(pady=10)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.reset_pos)

        # PIL内存画布，用来保存图像
        self.image = Image.new("L", (self.canvas_size, self.canvas_size), 0)
        self.draw_pil = ImageDraw.Draw(self.image)

        # 按钮区域
        frame_btn = ttk.Frame(root)
        frame_btn.pack()
        self.btn_predict = ttk.Button(frame_btn, text="识别数字", command=self.predict_digit)
        self.btn_clear = ttk.Button(frame_btn, text="清空画布", command=self.clear_canvas)
        self.btn_predict.grid(row=0, column=0, padx=5)
        self.btn_clear.grid(row=0, column=1, padx=5)

        # 结果显示
        self.result_text = tk.StringVar(value="识别结果：")
        label_result = ttk.Label(root, textvariable=self.result_text, font=("SimHei",20))
        label_result.pack(pady=8)

    def draw(self, event):
        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill="white", width=self.brush_size, capstyle=tk.ROUND)
            self.draw_pil.line([self.last_x, self.last_y, event.x, event.y], fill=255, width=self.brush_size)
        self.last_x, self.last_y = event.x, event.y

    def reset_pos(self, event):
        self.last_x = None
        self.last_y = None

    def clear_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new("L", (self.canvas_size, self.canvas_size), 0)
        self.draw_pil = ImageDraw.Draw(self.image)
        self.result_text.set("识别结果：")

    # ===================== 核心优化：图像预处理（裁剪+居中） =====================
    def preprocess_image(self, img):
        # img: PIL灰度图，黑底白字
        # 找到白色数字包围盒
        bbox = img.getbbox()
        if bbox is None:
            return None
        # 裁剪出数字区域
        digit_region = img.crop(bbox)
        w, h = digit_region.size
        # 给数字四周预留一点边距（MNIST数字四周有少量留白）
        padding = max(w, h) // 5
        new_w = w + padding*2
        new_h = h + padding*2
        square_img = Image.new("L", (new_w, new_h), 0)
        square_img.paste(digit_region, (padding, padding))
        # 缩放到28×28
        square_img = square_img.resize((28,28), Image.Resampling.LANCZOS)
        return square_img

    def predict_digit(self):
        img = self.image.copy()
        img = self.preprocess_image(img)
        if img is None:
            self.result_text.set("识别结果：画布为空！")
            return

        tensor_img = transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            logits = model(tensor_img)
            pred = torch.argmax(logits, dim=1).item()
            prob = torch.softmax(logits, dim=1)[0, pred].item()
        self.result_text.set(f"识别结果：{pred}，置信度：{prob:.3f}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DigitGUI(root)
    root.mainloop()
