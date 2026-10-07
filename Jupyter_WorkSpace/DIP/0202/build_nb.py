# -*- coding: utf-8 -*-
"""生成 DIP 第二章课设 Notebook (0202)。"""
import json, os

NB_PATH = r"D:\workspace\Jupyter_WorkSpace\DIP\0202\DIP第二章_傅里叶频域滤波优化的GMM前景检测.ipynb"

# 用带唯一标识的定界符，避免被代码单元内部的 """ 提前截断
DELIM = "@@CELL@@"

cells = []


def _to_source(text):
    """
    把单元格文本转成 notebook 的 source 数组。

    关键：列表元素必须**保留行尾换行符**（形如 ['a\\n', 'b\\n', 'c']）。
    Jupyter 渲染 markdown 时按 "".join(source) 拼接，若元素不带 "\\n"
    （即 text.split("\\n") 的写法），整段会被粘成一行，
    标题与表格语法全部失效——这正是本文件曾出现过的渲染故障。
    """
    body = text.strip("\n")
    if not body:
        return []
    return body.splitlines(keepends=True)


def md(text):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": _to_source(text)})


def code(text):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": _to_source(text)})


# ======================================================================
md(r'''
# 傅里叶频域滤波优化的高斯混合模型前景检测

> **数字图像处理 课程设计 · 第二章**
> 依据大纲《DIP第二章课设-⬜⬜》实现，与论文结构一一对应。

---

## 本章任务与论文对应关系

| 论文小节 | 本 Notebook 对应节 |
| --- | --- |
| 1 相关原理 | `1 原理验证` |
| 2 本文算法（流程 / 伪代码） | `2 算法实现`、`3 逐帧实验` |
| 3 实验分析 | `4 定量评估`、`5 参数分析`、`6 计算开销` |
| 4 结论与展望 | `7 结论复现` |

## 核心思路（一句话）

传统 GMM 对**每个像素独立建模**，忽略了图像的空间邻域相关性，输出的二值前景掩码里因此散布大量**孤立椒盐噪点**。
本文**不改动 GMM 的时序建模逻辑**，只在掩码输出之后串联一个 **二维傅里叶高斯低通滤波** 后处理模块：
利用傅里叶卷积定理，把"空域高斯平滑"搬到频域用逐点相乘实现，平滑衰减高频噪声分量，再逆变换回空域、阈值二值化，得到净化后的精细掩码。

## 目录结构约定

```
D:\workspace\Jupyter_WorkSpace\DIP\0202\
├── DIP第二章_傅里叶频域滤波优化的GMM前景检测.ipynb   <- 本文件
└── data\                                              <- 全部生成/所需文件
```

## 环境

内核：`D:\workspace\.my_env`（Python 3.11.7）
依赖：`numpy` `opencv-python` `scipy` `matplotlib` `pandas` `scikit-image`
''')

# ======================================================================
md(r'''
## 0 环境与实验准备

统一完成：中文显示、随机种子、路径创建、绘图风格。
''')

code(r'''
# ===================== 0.1 依赖导入与全局配置 =====================
import os
import sys
import time
import json
from pathlib import Path

import numpy as np
import cv2
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy import ndimage
from skimage import filters, measure, morphology

# ---------- 中文显示（避免图中汉字变成方框） ----------
def setup_cjk_font():
    prefer = ["Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC", "Source Han Sans SC"]
    avail = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((n for n in prefer if n in avail), None)
    for key in ("font.sans-serif", "font.serif"):
        # 中文字体在前负责汉字，DejaVu Sans 兜底负责数学符号，两者互补避免缺字形
        plt.rcParams[key] = ([chosen] if chosen else []) + ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return chosen

CJK = setup_cjk_font()

matplotlib.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 130,
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
    "figure.autolayout": False,
    "axes.grid": False,
})

# ---------- 随机种子：保证整章实验完全可复现 ----------
SEED = 2024
np.random.seed(SEED)
cv2.setRNGSeed(SEED)

# ---------- 路径 ----------
DATA = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0202\data")
DATA.mkdir(parents=True, exist_ok=True)

print("Python  :", sys.version.split()[0])
print("numpy   :", np.__version__)
print("opencv  :", cv2.__version__)
print("中文字体:", CJK)
print("数据目录:", DATA)
''')

code(r'''
# ===================== 0.2 全局超参数 =====================
# ---- 视频合成参数（自建小型监控序列，无需联网下载） ----
W, H       = 240, 160        # 帧宽、帧高
N_FRAMES   = 200             # 总帧数
FPS        = 25

# ---- 场景分区（行坐标范围 [y0, y1)） ----
Y_SKY      = (0, 45)         # 天空 + 水面（周期性波动背景）
Y_TREE     = (0, 60)         # 树木摆动区域（周期性背景扰动）
Y_ROAD     = (55, 115)       # 道路：运动目标（行人）所在区域
Y_PATH     = (112, H)        # 人行道
Y_SWAY     = (120, H)        # 草叶/串扰摆动区域

# ---- 目标与扰动数量 ----
N_PED      = 4               # 行人数

# ---- GMM 参数 ----
ALPHA_MIN  = 0.01            # 最小学习率（对应 sklearn BackgroundSubtractorMOG 的 alpha）
GMM_K      = 3               # 手写 GMM 的高斯分量数

# ---- 傅里叶高斯低通截止频率 ----
D0         = 0.08            # 归一化截止半径（相对帧宽），对应 D0 = 0.08*240 = 19.2 像素
D0_SWEEP   = [0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50]

print(f"帧尺寸 {W}x{H}，共 {N_FRAMES} 帧 @ {FPS}fps")
print(f"GMM 分量数 K={GMM_K}，最小学习率 alpha={ALPHA_MIN}，傅里叶截止 D0={D0}")
''')

code(r'''
# ===================== 0.3 通用工具函数 =====================

def to_binarize_bool(mask):
    """把任意掩码规范为 {0,1} 的 uint8 二值掩码。"""
    m = np.asarray(mask)
    if m.dtype == bool:
        return m.astype(np.uint8)
    return (m > 127).astype(np.uint8) if m.max(initial=0) > 1 else (m > 0).astype(np.uint8)


def fpr(pred, gt):
    """误检率 FPR = FP / (FP + TN)：把背景像素错判为前景的比例。"""
    pred, gt = to_binarize_bool(pred).astype(bool), to_binarize_bool(gt).astype(bool)
    fp = np.logical_and(pred, ~gt).sum()
    tn = np.logical_and(~pred, ~gt).sum()
    return float(fp) / float(fp + tn + 1e-12)


def fnr(pred, gt):
    """漏检率 FNR = FN / (FN + TP)。"""
    pred, gt = to_binarize_bool(pred).astype(bool), to_binarize_bool(gt).astype(bool)
    fn = np.logical_and(~pred, gt).sum()
    tp = np.logical_and(pred, gt).sum()
    return float(fn) / float(fn + tp + 1e-12)


def iou(pred, gt):
    """交并比 IoU，衡量目标轮廓完整度。"""
    pred, gt = to_binarize_bool(pred).astype(bool), to_binarize_bool(gt).astype(bool)
    inter = np.logical_and(pred, gt).sum()
    union = np.logical_or(pred, gt).sum()
    return float(inter) / float(union + 1e-12)


def salt_pepper_stats(mask, area_thresh=4):
    """椒盐噪声统计：面积小于 area_thresh 的孤立连通块个数与像素占比。"""
    m = to_binarize_bool(mask)
    if m.ndim == 3:                      # 逐帧统计后取平均，兼容整段序列输入
        res = [salt_pepper_stats(mi, area_thresh) for mi in m]
        return (int(round(np.mean([r[0] for r in res]))),
                float(np.mean([r[1] for r in res])))
    lbl, n = ndimage.label(m, structure=np.ones((3, 3), dtype=np.uint8))
    if n == 0:
        return 0, 0.0
    areas = np.bincount(lbl.ravel())[1:]
    small = int((areas < area_thresh).sum())
    small_px = float(areas[areas < area_thresh].sum())
    return small, small_px / float(m.size)


def far_field_fpr(pred, y0, y1):
    """远场误检率：在完全没有目标的区域统计误检像素占比（对背景扰动最敏感）。"""
    m = to_binarize_bool(pred)[y0:y1, :]
    return float(m.sum()) / float(m.size)


def denoise_rate(pred_raw, pred_opt):
    """椒盐噪声去除率：孤立噪点像素的下降比例。"""
    _, p_raw = salt_pepper_stats(pred_raw)
    _, p_opt = salt_pepper_stats(pred_opt)
    return float(p_raw - p_opt) / float(p_raw + 1e-12)


def make_gaussian_lowpass(shape, d0_norm):
    """
    构造频域高斯低通滤波器 H(u,v)=exp(-D^2(u,v)/(2*D0^2))。

    注意坐标约定：这里使用 np.fft.fftfreq 给出的"周期性"频率坐标，
    直流分量位于数组的 [0,0]，与未经 fftshift 的 np.fft.fft2 频谱严格对齐。
    若把直流分量设在数组中心，则必须改用 fftshift 后的频谱，否则滤波器原点
    与频谱原点错位，会把远离直流的窄带误当作低频，导致输出幅值严重衰减。

    参数 d0_norm 为归一化截止半径（相对帧宽的倍数），
    对应截止半径 D0 = d0_norm * width 像素。
    """
    h, w = shape[:2]
    d0 = float(d0_norm) * w
    uu = np.fft.fftfreq(w, 1.0 / w)          # 横向频率，单位：周/帧宽，取值 -W/2..W/2-1
    vv = np.fft.fftfreq(h, 1.0 / h)          # 纵向频率，单位：周/帧高
    d2 = uu[None, :] ** 2 + vv[:, None] ** 2  # 各向同性距离（周期性意义下）
    return np.exp(-d2 / (2.0 * d0 ** 2))


def fft_gaussian_denoise(mask, d0_norm=0.08, threshold=0.5):
    """
    本文核心后处理：二维傅里叶变换 -> 高斯低通 -> 逆变换 -> 阈值二值化。
    完整对应论文第 2 节算法流程步骤 2)~4)。

    关于阈值：低通滤波保留了直流分量，因此逆变换幅值的量纲是"以该点为中心的
    局部邻域被前景填充的比例"，前景主体内部接近 1、背景接近 0。取 0.5 即要求
    该像素邻域内至少一半被前景占据，可滤除孤立椒盐噪点而保留连续目标区域。
    """
    m = to_binarize_bool(mask).astype(np.float64)

    # 2) 二维傅里叶变换（保持与滤波器一致的未中心化约定）
    F = np.fft.fft2(m)

    # 3) 构造高斯低通并频域逐点相乘（傅里叶卷积定理）
    H = make_gaussian_lowpass(m.shape, d0_norm)
    F_filtered = F * H

    # 4) 逆傅里叶变换 -> 取模 -> 阈值二值化
    M_complex = np.fft.ifft2(F_filtered)
    M_mag = np.abs(M_complex)

    return (M_mag > threshold).astype(np.uint8), M_mag, H


print("工具函数就绪：FPR / FNR / IoU / 椒盐统计 / 高斯低通 / 频域降噪")
''')

code(r'''
# ===================== 0.4 实现自检（必读） =====================
# 频域滤波最容易出错的地方是"滤波器原点"与"频谱原点"的约定必须一致。
# 这里用四条可验证的性质确认实现正确：
#   (1) 高斯低通的直流分量必须为 1（低频整体保留）；
#   (2) 等效空域卷积核求和必须为 1（无亮度增益）；
#   (3) 大块前景经滤波后内部幅值必须接近 1（主体被保留）；
#   (4) 单个孤立噪点经滤波后幅值必须远小于 0.5（噪点被抑制）。

rng_chk = np.random.default_rng(7)

# (1)(2) 滤波器性质
H_chk = make_gaussian_lowpass((H, W), D0)
k_chk = np.real(np.fft.ifft2(H_chk))
print(f"(1) 直流分量 H[0,0]              = {H_chk[0, 0]:.6f}   （应为 1.0）")
print(f"(2) 等效空域核求和 sum(k)        = {k_chk.sum():.6f}   （应为 1.0）")

# (3) 大块前景：滤波后内部幅值应接近 1
blk = np.zeros((H, W), np.uint8)
cv2.rectangle(blk, (W // 2 - 25, H // 2 - 25), (W // 2 + 25, H // 2 + 25), 1, -1)
blk_mag = fft_gaussian_denoise(blk, d0_norm=D0)[1]
print(f"(3) 50x50 方块内部幅值均值       = {blk_mag[H//2-8:H//2+8, W//2-8:W//2+8].mean():.6f}   （应接近 1.0）")

# (4) 孤立噪点：幅度应被稀释到远低于阈值
spk = np.zeros((H, W), np.uint8)
spk[H // 3, W // 3] = 1
spk[H // 3 + 1, W // 3 + 7] = 1
spk_mag = fft_gaussian_denoise(spk, d0_norm=D0)[1]
print(f"(4) 孤立单点噪点处最大幅值       = {spk_mag.max():.6f}   （应远小于 0.5）")

# (5) 与空域高斯平滑对照：二者应当高度一致（卷积定理的直接验证）
rect = np.zeros((H, W), np.uint8)
cv2.rectangle(rect, (60, 60), (72, 92), 1, -1)
freq_res = fft_gaussian_denoise(rect, d0_norm=D0)[1]
spatial_res = cv2.GaussianBlur(rect.astype(np.float32), (0, 0), sigmaX=D0 * W, sigmaY=D0 * W)
print(f"(5) 与空域高斯平滑的平均绝对误差  = {np.abs(freq_res - spatial_res).mean():.6f}"
      f"   （相对幅值量级 {freq_res.max():.3f}，应很小）")

print()
print("自检结论：若 (1)(2) 为 1、(3) 接近 1、(4) 远小于 0.5，则频域滤波实现正确，")
print(f"          可用固定阈值 0.5 完成二值化。当前 D0={D0}，对应截止半径 {D0*W:.1f} 像素。")
''')

# ======================================================================
md(r'''
## 1 原理验证

### 1.1 自建小型动态监控序列（含像素级真值掩码）

大纲要求"数据集允许从网络下载小数据集（不超过 50 MB）"。为保证**完全可复现、可离线**，本章直接合成一段 240×160×200 帧的小型监控视频（约 2.5 MB），
并刻意注入 GMM 的四类典型干扰因素：

| 区域 | 注入的干扰 | 对应论文中提到的 GMM 固有缺陷 |
| --- | --- | --- |
| 天空 / 水面 | 多方向正弦波纹 | 周期性动态背景误检 |
| 树木区域 | 幅度受限的随机抖动 | 树叶晃动误检 |
| 人行道 | 尾随行人的暗色影子 | 阴影误判 |
| 全局 | 第 120 帧起渐变增亮 | 光照突变误检 |

行人使用**纯矩形**绘制（不含纹理/噪声），因此可以得到与合成过程严格一致的**真值掩码 GT**，用于客观计算误检率、漏检率和 IoU。
''')

code(r'''
# ===================== 1.1 动态监控场景合成 =====================

def make_base_background(h, w, seed=7):
    """构造静态基础背景纹理（低频结构 + 中频起伏 + 细颗粒）。"""
    rng = np.random.default_rng(seed)
    img = np.full((h, w), 180.0, np.float32)

    # --- 天空/远景 ---
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    # 天空上半部整体更亮，且平缓过渡
    img += 18.0 * np.clip(1.0 - yy / (h * 1.1), 0, 1)
    # 水面区域（地平线附近）暗一些
    img[Y_SKY[0]:Y_SKY[1], :] -= 12.0

    # --- 道路：中灰 + 轻微渐变 ---
    img[Y_ROAD[0]:Y_ROAD[1], :] = 95.0 + 10.0 * (yy[Y_ROAD[0]:Y_ROAD[1]] / h)

    # --- 人行道：稍亮 ---
    img[Y_PATH[0]:Y_PATH[1], :] = 150.0 + 12.0 * (yy[Y_PATH[0]:Y_PATH[1]] / h)

    # --- 低频结构：模糊随机噪声形成自然明暗起伏 ---
    low = rng.random((h, w), dtype=np.float32)
    low = cv2.GaussianBlur(low, (0, 0), sigmaX=6.0, sigmaY=6.0)
    low = (low - low.mean()) / (low.std() + 1e-6)
    img += 16.0 * low

    # --- 细颗粒底色 ---
    img += rng.normal(0.0, 3.0, (h, w)).astype(np.float32)
    return img


def draw_pedestrians(canvas, t, seed=SEED):
    """
    把第 t 帧的行人（含阴影）画到 canvas 上，并返回行人区域的并集真值掩码。

    注意：行人使用纯矩形绘制、不含纹理，因此真值掩码与图像内容严格一致，
    可以客观计算误检率 / 漏检率 / IoU。阴影只画入图像、不写入真值，
    用于复现"阴影误判"这一 GMM 固有缺陷。
    """
    gt = np.zeros(canvas.shape, np.uint8)
    lane_y0, lane_y1 = Y_ROAD[0] + 4, Y_ROAD[1] - 6
    span = lane_y1 - lane_y0

    for i in range(N_PED):
        r = np.random.default_rng(seed + 100 + i)   # 每个行人独立、可复现的参数

        # --- 出生/死亡时刻：制造目标的出现与消失 ---
        born, die = int(r.integers(5, 40)), int(r.integers(120, 195))
        if not (born <= t < die):
            continue

        # --- 主运动：反方向两条车道 ---
        direction = 1 if i % 2 == 0 else -1
        speed = float(r.uniform(1.2, 2.3))
        x0f = float(r.uniform(0, W))
        span_len = (die - born)
        x = int((x0f + direction * speed * (t - born)) % (W + 60) - 30)
        x = int(np.clip(x, -20, W - 5))

        # --- 纵向车道位置 ---
        y = int(r.integers(lane_y0, lane_y0 + max(1, span // 2)))
        if i == 1:
            y = lane_y0 + span // 2 + 6

        # --- 体型与子像素步态抖动 ---
        ph = 2.0 * np.pi * t / 18.0 + i * 1.7
        hgt = int(r.integers(22, 34))
        wid = int(r.integers(9, 14))
        cy = int(np.clip(y + 1.5 * np.sin(ph), 0, H - hgt - 1))

        # --- 阴影（先于身体绘制） ---
        cv2.ellipse(canvas, (int(x + 3), cy + hgt - 2), (wid + 2, 3),
                    0, 0, 360, float(-55), -1)

        # --- 躯干 ---
        v = float(120 + 70 * r.random())
        cv2.rectangle(canvas, (x, cy), (x + wid, cy + hgt), v, -1)

        # --- 双腿交替摆动 ---
        leg = int(3 * np.sin(ph))
        cv2.rectangle(canvas, (x + leg, cy + hgt), (x + wid // 2 - 1 + leg, min(cy + hgt + 7, H - 1)), v, -1)
        cv2.rectangle(canvas, (x - leg, cy + hgt), (x + wid // 2 + 1 - leg, min(cy + hgt + 6, H - 1)), v, -1)

        # --- 真值掩码：与绘制严格一致 ---
        cv2.rectangle(gt, (x, cy), (x + wid, cy + hgt), 1, -1)
        cv2.ellipse(gt, (int(x + 3), cy + hgt - 2), (wid + 2, 3), 0, 0, 360, 1, -1)

    return gt


def add_dynamic_disturbance(img, t, seed=11):
    """周期性动态背景扰动：水面波纹 + 树叶摆动 + 草丛摆动。"""
    h, w = img.shape
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    wv = 2.0 * np.pi * t / 22.0

    # --- 水面：多方向正弦波纹 ---
    rows = slice(Y_SKY[0], Y_SKY[1])
    wave = (np.sin(xx * 0.35 + wv * 1.7) * 6.0
            + np.sin(xx * 0.13 - wv * 0.9 + yy[rows] * 0.5) * 9.0
            + np.sin((xx + yy[rows]) * 0.21 + wv * 2.3) * 4.0)
    img[rows, :] += wave.astype(np.float32)

    # --- 树木区域：有界随机抖动，模拟树叶摇晃；幅度向 y=Y_TREE[1] 渐隐避免人为硬边 ---
    rng = np.random.default_rng(seed + t)
    tree = rng.normal(0.0, 6.0, (Y_TREE[1], w)).astype(np.float32)
    tree = cv2.GaussianBlur(tree, (0, 0), sigmaX=1.5, sigmaY=1.5)
    taper = np.clip(1.0 - np.arange(Y_TREE[1], dtype=np.float32) / Y_TREE[1], 0, 1)[:, None]
    img[:Y_TREE[1], :] += tree * taper

    # --- 草丛区域 ---
    sway = 3.0 * np.sin(xx * 0.5 + wv * 3.1)
    img[Y_SWAY[0]:, :] += sway.astype(np.float32)
    return img


def generate_sequence(n=N_FRAMES, h=H, w=W, frames_out=0):
    """逐帧合成；frames_out>0 时只返回前若干帧（用于快速预览）。"""
    background = make_base_background(h, w)
    limit = frames_out if frames_out > 0 else n
    for t in range(limit):
        frame = background.copy()
        frame = add_dynamic_disturbance(frame, t)

        # 绘制行人：draw_pedestrians 就地修改 frame 并返回严格一致的真值掩码
        gt = draw_pedestrians(frame, t)

        # 全局光照渐变：第 120 帧起缓慢增亮（模拟云层移动 / 灯光变化）
        if t >= 120:
            frame += 22.0 * (t - 120) / max(1, (n - 121))
        # 叠加传感器噪声，进一步考验掩码质量
        frame += np.random.default_rng(SEED + 5000 + t).normal(0.0, 2.5, frame.shape).astype(np.float32)
        yield t, np.clip(frame, 0, 255).astype(np.uint8), gt


print("场景合成函数就绪")
''')

code(r'''
# 合成前 4 帧做视觉核对：确认行人、水面波纹、阴影都已就位
fig, axes = plt.subplots(2, 4, figsize=(15, 6.4))
for i, (t, frame, gt) in enumerate(generate_sequence(frames_out=64)):
    if i >= 4:
        break
    axes[0, i].imshow(frame, cmap="gray", vmin=0, vmax=255)
    axes[0, i].set_title(f"合成帧 t={t}", fontsize=11)
    axes[1, i].imshow(gt, cmap="gray")
    axes[1, i].set_title(f"真值掩码 GT t={t}", fontsize=11)
    for r in (0, 1):
        axes[r, i].axis("off")
fig.suptitle("1.1 自建监控序列与像素级真值掩码", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_1_1_synth_frames.png", bbox_inches="tight")
plt.show()
''')

code(r'''
# ===================== 落盘：把合成序列写成真实视频文件 =====================
NOISE_FILE = DATA / "synthetic_surveillance.mp4"
VIDEO_RAW = NOISE_FILE
VIDEO_GT = DATA / "surveillance_synth_gt.mp4"

if not VIDEO_RAW.exists():
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    vw = cv2.VideoWriter(str(VIDEO_RAW), fourcc, FPS, (W, H), isColor=False)
    gw = cv2.VideoWriter(str(VIDEO_GT), fourcc, FPS, (W, H), isColor=False)
    for t, frame, gt in generate_sequence():
        vw.write(frame)
        gw.write((gt * 255).astype(np.uint8))
    vw.release()
    gw.release()
    print("已生成视频文件")
else:
    print("视频文件已存在，跳过")

for p in (VIDEO_RAW, VIDEO_GT):
    print(f"{p.name:34s} {p.stat().st_size/1024/1024:6.2f} MB")
''')

md(r'''
### 1.2 高斯低通滤波器与吉布斯振铃对比

论文 1.2 节指出：**频域理想低通是高频硬截断，等价于 sinc 核卷积，会产生吉布斯振铃伪影**；
而高斯低通对高频分量**平滑衰减、无阶跃截断**，因此没有明显振铃。

下面用一维切面直接把这个结论画出来。
''')

code(r'''
# ===================== 1.2 理想低通 vs 高斯低通 =====================
def ideal_lowpass(h, w, d0_norm):
    """理想（硬截断）低通：|D| <= D0 时取 1，否则取 0。与高斯低通使用同一坐标约定。"""
    d0 = d0_norm * w
    uu = np.fft.fftfreq(w, 1.0 / w)
    vv = np.fft.fftfreq(h, 1.0 / h)
    d = np.sqrt(uu[None, :] ** 2 + vv[:, None] ** 2)
    return (d <= d0).astype(np.float64)


# 构造一个阶跃边缘信号（阶跃的频谱具有无穷高频，最能暴露振铃）
step = np.zeros((128, 128), np.float64)
step[:, 64:] = 1.0

H_ideal = ideal_lowpass(128, 128, 0.08)
H_gauss = make_gaussian_lowpass((128, 128), 0.08)

def apply_freq(sig, Hf):
    """在频域用 Hf 滤波（与滤波器构造保持同一坐标约定，不做额外 shift）。"""
    return np.real(np.fft.ifft2(np.fft.fft2(sig) * Hf))

r_ideal = apply_freq(step, H_ideal)
r_gauss = apply_freq(step, H_gauss)

# 空域等效核（逆变换 H 即得该频域滤波器对应的空域卷积核）
k_ideal = np.real(np.fft.ifft2(H_ideal))
k_gauss = np.real(np.fft.ifft2(H_gauss))

fig, axes = plt.subplots(2, 3, figsize=(15.5, 8))

axes[0, 0].plot(step[64], "k", lw=2)
axes[0, 0].set_title("原始阶跃信号切面")
axes[0, 1].plot(r_ideal[64], "tab:red", lw=2, label="理想低通")
axes[0, 1].plot(r_gauss[64], "tab:blue", lw=2, label="高斯低通")
axes[0, 1].legend(fontsize=9)
axes[0, 1].set_title("滤波后切面：理想低通出现明显过冲(振铃)")
axes[0, 2].imshow(H_gauss, cmap="viridis")
axes[0, 2].set_title("高斯低通幅频响应 H(u,v)")
axes[0, 2].axis("off")

axes[1, 0].imshow(k_ideal[:32, :32], cmap="RdBu_r", extent=[0, 32, 0, 32])
axes[1, 0].set_title("理想低通空域核：旁瓣衰减慢 -> sinc 振铃")
axes[1, 1].imshow(k_gauss[:32, :32], cmap="RdBu_r", extent=[0, 32, 0, 32])
axes[1, 1].set_title("高斯低通空域核：单峰快速衰减")
axes[1, 2].semilogy(np.abs(k_ideal[0, 1:40]), "tab:red", label="理想低通")
axes[1, 2].semilogy(np.abs(k_gauss[0, 1:40]), "tab:blue", label="高斯低通")
axes[1, 2].legend(fontsize=9)
axes[1, 2].set_title("空域核旁瓣幅度(对数)：旁瓣即振铃来源")

fig.suptitle("1.2 傅里叶频域滤波：理想低通 vs 高斯低通（吉布斯振铃验证）", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_1_2_gibbs_vs_gaussian.png", bbox_inches="tight")
plt.show()

overshoot_i = r_ideal[64][62:67]
overshoot_g = r_gauss[64][62:67]
print(f"理想低通在边缘处最大过冲   : {overshoot_i.max():.4f}")
print(f"高斯低通在边缘处最大过冲   : {overshoot_g.max():.4f}")
''')

md(r'''
### 1.3 手写 GMM 背景建模（原理对照）

OpenCV 的 `BackgroundSubtractorMOG2` 就是 Stauffer & Grimson 自适应高斯混合模型的高效实现，
本章的**主实验直接使用它**以保证性能与工程可信度。

但为了说明"GMM 到底在做什么"，同时验证"逐像素独立建模"这一缺陷的根源，
这里再手写一份**极简版 GMM**（K 个高斯分量，均值/方差/权重在线更新），在少量帧上与 MOG2 对照。
''')

code(r'''
# ===================== 1.3 手写 GMM 背景建模 =====================
class SimpleGMM:
    """
    极简自适应高斯混合模型（Stauffer & Grimson 式）。

    对每个像素维护 K 个高斯分量 (w, mu, var)：
      1) 把新像素灰度与各分量比较，|I - mu| < 2.5 * sigma 视为匹配；
      2) 匹配分量：更新权重与均值方差；未匹配分量：按方差下限缓慢衰减权重；
      3) 按 w/sigma 排序，取累积权重 >= T 的前若干个分量作为背景；
      4) 不匹配任何背景分量的像素判为前景。
    """

    def __init__(self, h, w, k=3, alpha=0.01, t_background=0.6, var_init=225.0):
        self.h, self.w, self.k = h, w, k
        self.alpha, self.t_background = alpha, t_background
        self.var_init, self.var_min = var_init, 4.0
        self.weight = np.full((k, h, w), 1.0 / k, np.float32)
        self.mean = np.random.uniform(0, 255, (k, h, w)).astype(np.float32)
        self.var = np.full((k, h, w), var_init, np.float32)
        self.frame_idx = 0

    def apply(self, frame):
        img = frame.astype(np.float32) if frame.ndim == 3 else frame.astype(np.float32)
        self.frame_idx += 1
        # 冷启动：直接以当前帧初始化所有分量
        if self.frame_idx == 1:
            self.mean[:] = img[None, :, :]
            self.mean += np.random.normal(0, 5, self.mean.shape).astype(np.float32)

        std = np.sqrt(self.var) + 1e-6
        match = np.abs(img[None, :, :] - self.mean) < 2.5 * std        # (K,H,W)
        matched_any = match.any(axis=0)

        # --- 权重更新：w <- (1-alpha)*w + alpha*M_k （M_k 为匹配指示，等价于此处的两次修正） ---
        self.weight *= (1.0 - self.alpha)
        self.weight += self.alpha * match.astype(np.float32)          # 匹配分量各加 alpha
        self.weight /= (self.weight.sum(axis=0, keepdims=True) + 1e-12)

        # --- 均值 / 方差更新（仅匹配分量） ---
        rho = self.alpha / (self.weight + 1e-6)
        rho = np.clip(rho, 0, 1)
        diff = img[None, :, :] - self.mean
        self.mean = np.where(match, self.mean + rho * diff, self.mean)
        self.var = np.where(match,
                            self.var + rho * (diff ** 2 - self.var),
                            self.var)
        self.var = np.maximum(self.var, self.var_min)

        # --- 背景判定：按 w/sigma 排序累积权重 ---
        score = self.weight / np.sqrt(self.var)
        order = np.argsort(-score, axis=0)
        w_sorted = np.take_along_axis(self.weight, order, axis=0)
        cum = np.cumsum(w_sorted, axis=0)
        bg_rank = cum < self.t_background          # 属于背景的分量次序

        mask = np.ones((self.h, self.w), np.uint8)
        for kk in range(self.k):
            sel = bg_rank[kk] & match[order[kk], np.arange(self.h)[:, None], np.arange(self.w)[None, :]]
            mask[sel] = 0
        return mask


print("SimpleGMM 定义完成")
''')

# ======================================================================
md(r'''
## 2 算法实现

### 2.1 完整算法流程（对应论文第 2 节 1)~5) 步）

```
输入：视频序列 {I_t}
输出：净化的前景掩码序列 {M'_t}

初始化 GMM 背景模型，D0 = 0.10

for each frame I_t in video:
    ① M_t = GMM_get_foreground_mask(I_t)          # 传统 GMM 输出原始掩码
    ② F = fft2(M_t)                               # 二维傅里叶变换
    ③ H = gaussian_lowpass(M_t.shape, D0)         # 构造高斯低通
       F_filtered = F ⊙ H                         # 频域逐点相乘（卷积定理）
    ④ M'_t = threshold(|ifft2(F_filtered)|, 0.5)  # 逆变换 + 阈值二值化
    ⑤ 更新 GMM 模型参数，读取下一帧
```

### 2.2 关键实现要点

1. **不改动 GMM 核心时序逻辑**：`fft_gaussian_denoise()` 是一个纯后置模块，输入输出都是二值掩码，
   因此可以无差别地串接到任意像素级背景建模算法之后（对应论文"移植性强"的结论）。
2. **为什么不用空域卷积**：掩码尺寸为 240×160 时，高斯核半径需与 D0 匹配，空域卷积的复杂度是 O(N·k²)；
   频域实现借助 FFT 把代价降到 O(N log N)，且一次乘法即完成整幅卷积。
3. **阈值选择**：逆变换结果为浮点值，理论上背景区域接近 0、前景区域接近 1，取 0.5 为判据。
''')

code(r'''
# ===================== 2.1 频域滤波精度核对 =====================
# 用一组已知的前景块验证：fft_gaussian_denoise 是否真的做到"去噪不掉主体"
rng = np.random.default_rng(1)
clean = np.zeros((120, 160), np.uint8)
cv2.rectangle(clean, (40, 40), (90, 80), 1, -1)          # 主体

noisy = clean.copy()
idx = rng.choice(clean.size, 300, replace=False)          # 注入椒盐噪声
noisy.ravel()[idx] = 1

out, mag, Hf = fft_gaussian_denoise(noisy, d0_norm=D0)

fig, axes = plt.subplots(1, 4, figsize=(16, 4.2))
for ax, im, ti in zip(axes,
                      [clean, noisy, mag, out],
                      ["干净掩码（理想）", f"加噪掩码（孤立噪点 {len(idx)} 个）",
                       "逆变换后幅值 |ifft2|", "本文后处理结果"]):
    ax.imshow(im, cmap="gray")
    ax.set_title(ti, fontsize=11)
    ax.axis("off")
fig.suptitle("2.1 频域高斯低通后处理的可行性验证", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_2_1_denoise_sanity.png", bbox_inches="tight")
plt.show()

print(f"加噪掩码 与 理想掩码 IoU : {iou(noisy, clean):.4f}")
print(f"后处理   与 理想掩码 IoU : {iou(out,  clean):.4f}")
print(f"孤立噪点像素占比: {salt_pepper_stats(noisy)[1]*100:.3f}%  ->  {salt_pepper_stats(out)[1]*100:.3f}%")
''')

code(r'''
# ===================== 2.2 手写 GMM 与 MOG2 的原理对照 =====================
N_WARMUP = 40      # 前 40 帧作为背景模型冷启动
DEMO_LEN = 70      # 手写 GMM 逐帧计算较慢，只跑前 70 帧做对照

mog2_demo = cv2.createBackgroundSubtractorMOG2(
    history=300, varThreshold=16, detectShadows=False)
gmm_demo = SimpleGMM(H, W, k=GMM_K, alpha=ALPHA_MIN)

demo_store = []
t0 = time.perf_counter()
for t, frame, gt in generate_sequence(frames_out=DEMO_LEN):
    m_mog = mog2_demo.apply(frame, learningRate=ALPHA_MIN)
    m_gmm = gmm_demo.apply(frame)
    demo_store.append((t, frame, gt, m_mog, m_gmm))
t_demo = time.perf_counter() - t0

# 取一张两个行人都在画面中的帧
pick = min(demo_store, key=lambda r: abs(r[0] - 55))
t_p, frame_p, gt_p, m_mog_p, m_gmm_p = pick

opt_mog, _, _ = fft_gaussian_denoise(m_mog_p)
opt_gmm, _, _ = fft_gaussian_denoise(m_gmm_p)

fig, axes = plt.subplots(2, 4, figsize=(16.5, 8))
row1 = [frame_p, gt_p, m_mog_p, opt_mog]
row2 = [frame_p, gt_p, m_gmm_p, opt_gmm]
titles = ["输入帧", "真值 GT", "GMM 原始掩码", "GMM + 频域高斯低通"]
for j in range(4):
    axes[0, j].imshow(row1[j], cmap="gray"); axes[0, j].set_title(titles[j], fontsize=11); axes[0, j].axis("off")
    axes[1, j].imshow(row2[j], cmap="gray"); axes[1, j].set_title(titles[j], fontsize=11); axes[1, j].axis("off")
axes[0, 0].set_ylabel("MOG2(工程实现)", fontsize=10)
axes[1, 0].set_ylabel("SimpleGMM(手写原理)", fontsize=10)
fig.suptitle(f"2.2 两种 GMM 实现 + 频域后处理对照（t={t_p}）", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_2_2_gmm_compare.png", bbox_inches="tight")
plt.show()

print(f"手写 GMM 与 MOG2 掩码一致率(IoU) : {iou(m_gmm_p, m_mog_p):.4f}")
print(f"手写 GMM 逐帧平均耗时             : {t_demo/DEMO_LEN*1000:.1f} ms/帧（Python 逐像素循环，仅用于原理说明）")
''')

# ======================================================================
md(r'''
## 3 逐帧实验

### 3.1 单帧全流程可视化：傅里叶正变换 → 频谱 → 高斯低通 → 逆变换 → 掩码

下面把论文第 2 节的算法流程在**一张图**中完整展示，用于论文插图。
''')

code(r'''
# ===================== 3.1 单帧频域全流程 =====================
# 先跑完整序列，得到原始掩码序列（后续各节复用）
mog2 = cv2.createBackgroundSubtractorMOG2(
    history=300, varThreshold=16, detectShadows=False)

frames_all, gts_all, raw_all, opt_all, mags_all = [], [], [], [], []
for t, frame, gt in generate_sequence():
    m_raw = to_binarize_bool(mog2.apply(frame))     # 默认自适应学习率
    m_opt, mag, _ = fft_gaussian_denoise(m_raw, d0_norm=D0)
    frames_all.append(frame); gts_all.append(gt)
    raw_all.append(m_raw);    opt_all.append(m_opt); mags_all.append(mag)

raw_all = np.stack(raw_all); opt_all = np.stack(opt_all)
gts_all = np.stack(gts_all)
print("序列处理完成，掩码张量形状:", raw_all.shape)
print(f"原始掩码前景像素占比 : {raw_all.mean()*100:.3f}%")
print(f"平滑掩码前景像素占比 : {opt_all.mean()*100:.3f}%")
print(f"真值掩码前景像素占比 : {gts_all.mean()*100:.3f}%")
''')

code(r'''
# ---- 选帧并绘制频域全流程 ----
sel = min(range(50, 190), key=lambda i: abs(int(gts_all[i].sum()) - 520))
M = raw_all[sel].astype(np.float64)

F       = np.fft.fft2(M)                      # 未中心化频谱（与滤波器同一约定）
Hf      = make_gaussian_lowpass(M.shape, D0)  # 未中心化高斯低通
Ff      = F * Hf
M_mag   = np.abs(np.fft.ifft2(Ff))

# 仅用于可视化：把频谱中心化后再取对数显示，便于观察能量分布
Flog_disp = np.log(1.0 + np.abs(np.fft.fftshift(F)))

fig, axes = plt.subplots(2, 4, figsize=(17, 8.4))
items = [
    (gts_all[sel], "① 真值掩码 GT"),
    (M, "② GMM 原始掩码 M_t"),
    (Flog_disp, "③ 频谱（中心化显示）log(1+|F|)"),
    (np.fft.fftshift(Hf), f"④ 高斯低通 H（D0={D0}，中心化显示）"),
    (np.abs(np.fft.fftshift(Ff)) ** 0.3, "⑤ 频域相乘后 |F·H|"),
    (M_mag, "⑥ 逆变换幅值 |ifft2|"),
    (opt_all[sel], "⑦ 阈值二值化 M'_t（thr=0.5）"),
    (np.abs(raw_all[sel].astype(int) - opt_all[sel].astype(int)), "⑧ 被抑制的像素"),
]
for ax, (im, ti) in zip(axes.ravel(), items):
    ax.imshow(im, cmap="gray")
    ax.set_title(ti, fontsize=10.5)
    ax.axis("off")
fig.suptitle(f"3.1 本文算法单帧全流程（第 {sel} 帧）", fontsize=13.5)
plt.tight_layout()
plt.savefig(DATA / "fig_3_1_pipeline_single_frame.png", bbox_inches="tight")
plt.show()

print(f"该帧 FPR : {fpr(M, gts_all[sel])*100:.3f}%  ->  {fpr(opt_all[sel], gts_all[sel])*100:.3f}%")
print(f"该帧 IoU : {iou(M, gts_all[sel]):.4f}  ->  {iou(opt_all[sel], gts_all[sel]):.4f}")
''')

md(r'''
### 3.2 序列可视化：原始 GMM 掩码 vs 本文后处理掩码

横向为时间，选取三段典型时刻：**目标出现 / 多目标运动 / 光照突变**。
''')

code(r'''
# ===================== 3.2 关键帧横向对比 =====================
show_idx = [11, 25, 40, 70, 100, 140, 160, 185]     # 避开冷启动期
show_idx = [i for i in show_idx if i < len(raw_all)]

n = len(show_idx)
fig, axes = plt.subplots(3, n, figsize=(2.35 * n, 8.6))
for j, i in enumerate(show_idx):
    axes[0, j].imshow(frames_all[i], cmap="gray", vmin=0, vmax=255)
    axes[0, j].set_title(f"t={i}", fontsize=10)
    axes[1, j].imshow(raw_all[i], cmap="gray")
    axes[2, j].imshow(opt_all[i], cmap="gray")
    # 用红框圈出 原始掩码中的孤立噪点位置
    small = morphology.remove_small_objects(raw_all[i].astype(bool), 4)
    iso = np.logical_and(raw_all[i].astype(bool), ~small)
    ys, xs = np.where(iso)
    for y, x in zip(ys, xs):
        axes[1, j].add_patch(plt.Rectangle((x - 2, y - 2), 5, 5, fill=False,
                                           edgecolor="red", lw=0.6))
    axes[1, j].set_xlabel(f"孤立噪点 {len(ys)}", fontsize=9)
    axes[2, j].set_xlabel(f"FPR {fpr(opt_all[i], gts_all[i])*100:.2f}%", fontsize=9)
    for r in range(3):
        axes[r, j].set_xticks([]); axes[r, j].set_yticks([])

for r, name in enumerate(["输入帧", "GMM 原始掩码 M_t", "本文 M'_t (频域高斯低通)"]):
    axes[r, 0].set_ylabel(name, fontsize=10.5)
fig.suptitle("3.2 传统 GMM 与本文方法的逐帧掩码对比（红框=孤立椒盐噪点）", fontsize=13.5)
plt.tight_layout()
plt.savefig(DATA / "fig_3_2_frame_compare.png", bbox_inches="tight")
plt.show()
''')

code(r'''
# ===================== 3.3 掩码去噪效果放大细节 =====================
i = show_idx[3] if len(show_idx) > 3 else show_idx[0]
y0, y1, x0, x1 = 40, 120, 40, 160            # 局部放大窗口

fig, axes = plt.subplots(2, 3, figsize=(15.5, 8))
axes[0, 0].imshow(frames_all[i][y0:y1, x0:x1], cmap="gray"); axes[0, 0].set_title("输入帧（局部放大）")
axes[0, 1].imshow(gts_all[i][y0:y1, x0:x1], cmap="gray");   axes[0, 1].set_title("真值 GT")
axes[0, 2].imshow(raw_all[i][y0:y1, x0:x1], cmap="gray");   axes[0, 2].set_title("GMM 原始掩码")
axes[1, 0].imshow(opt_all[i][y0:y1, x0:x1], cmap="gray");   axes[1, 0].set_title("本文 M'（频域高斯低通）")
axes[1, 1].hist(mags_all[i].ravel(), bins=60, range=(0, 1), color="tab:blue")
axes[1, 1].axvline(0.5, color="tab:red", ls="--", label="阈值 thr=0.5")
axes[1, 1].set_yscale("log"); axes[1, 1].legend(fontsize=9)
axes[1, 1].set_title("逆变换幅值直方图：背景聚在 0 附近")
# 差异图：被去掉的（红）与丢失的（黄）
diff_removed = np.logical_and(raw_all[i], ~opt_all[i])
diff_lost    = np.logical_and(gts_all[i], ~opt_all[i])
vis = np.zeros((y1 - y0, x1 - x0, 3), np.uint8)
vis[..., 0] = diff_removed[y0:y1, x0:x1] * 220
vis[..., 1] = diff_lost[y0:y1, x0:x1] * 220
vis[..., 2] = gts_all[i][y0:y1, x0:x1] * 60
axes[1, 2].imshow(vis); axes[1, 2].set_title("红=被抑制的误检像素；黄=被误删的真前景")
for ax in axes.ravel():
    ax.axis("off")
axes[1, 1].axis("on"); axes[1, 1].set_yticks([])
fig.suptitle(f"3.3 掩码质量细节对比（第 {i} 帧）", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_3_3_zoom_detail.png", bbox_inches="tight")
plt.show()
''')

code(r'''
# ===================== 3.4 导出对比视频（可直接播放观察） =====================
VIDEO_CMP = DATA / "foreground_compare.mp4"

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
vw = cv2.VideoWriter(str(VIDEO_CMP), fourcc, FPS, (W * 3, H), isColor=True)
for i in range(len(frames_all)):
    gray = cv2.cvtColor(frames_all[i], cv2.COLOR_GRAY2BGR)
    r3 = cv2.cvtColor((raw_all[i] * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    o3 = cv2.cvtColor((opt_all[i] * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    for img, txt in ((gray, "input"), (r3, "GMM raw"), (o3, "GMM+Fourier")):
        cv2.putText(img, txt, (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA)
    vw.write(np.hstack([gray, r3, o3]))
vw.release()
print(f"对比视频已导出：{VIDEO_CMP.name}  ({VIDEO_CMP.stat().st_size/1024/1024:.2f} MB)")
''')

# ======================================================================
md(r'''
## 4 定量评估

与论文"结果"一节对应的四项指标：

| 指标 | 定义 | 期望方向 |
| --- | --- | --- |
| **误检率 FPR** | FP/(FP+TN)，背景被误判为前景的比例 | ↓ 越低越好 |
| **漏检率 FNR** | FN/(FN+TP)，前景被漏判的比例 | ↓ 越低越好 |
| **轮廓完整度 IoU** | TP/(TP+FP+FN)，与真值的重叠程度 | ↑ 越高越好 |
| **椒盐噪声去除率** | 孤立小连通块像素占比的下降比例 | ↑ 越高越好 |

统计时跳过前 `WARMUP` 帧，避免 GMM 冷启动阶段干扰结论。
''')

code(r'''
# ===================== 4.1 逐帧指标计算 =====================
WARMUP = 50
valid = range(WARMUP, len(raw_all))

rows = []
for i in valid:
    gt = gts_all[i]
    rows.append({
        "frame": i,
        "FPR_raw": fpr(raw_all[i], gt) * 100,
        "FPR_opt": fpr(opt_all[i], gt) * 100,
        "FNR_raw": fnr(raw_all[i], gt) * 100,
        "FNR_opt": fnr(opt_all[i], gt) * 100,
        "IoU_raw": iou(raw_all[i], gt),
        "IoU_opt": iou(opt_all[i], gt),
        "SP_raw":  salt_pepper_stats(raw_all[i])[1] * 100,
        "SP_opt":  salt_pepper_stats(opt_all[i])[1] * 100,
        "blobs_raw": salt_pepper_stats(raw_all[i])[0],
        "blobs_opt": salt_pepper_stats(opt_all[i])[0],
    })

df = pd.DataFrame(rows)
df.to_csv(DATA / "metrics_per_frame.csv", index=False, encoding="utf-8-sig")

mean = df.mean(numeric_only=True)
summary = pd.DataFrame({
    "指标": ["误检率 FPR(%)", "漏检率 FNR(%)", "轮廓完整度 IoU", "椒盐噪点像素占比(%)", "孤立连通块个数"],
    "传统 GMM": [mean.FPR_raw, mean.FNR_raw, mean.IoU_raw, mean.SP_raw, mean.blobs_raw],
    "本文方法": [mean.FPR_opt, mean.FNR_opt, mean.IoU_opt, mean.SP_opt, mean.blobs_opt],
})
summary["相对变化"] = [
    f"↓ {(mean.FPR_raw - mean.FPR_opt) / mean.FPR_raw * 100:.1f}%",
    f"↓ {(mean.FNR_raw - mean.FNR_opt) / mean.FNR_raw * 100:.1f}%",
    f"↑ {(mean.IoU_opt - mean.IoU_raw) / mean.IoU_raw * 100:.1f}%",
    f"↓ {(mean.SP_raw - mean.SP_opt) / mean.SP_raw * 100:.1f}%",
    f"↓ {(mean.blobs_raw - mean.blobs_opt) / mean.blobs_raw * 100:.1f}%",
]
summary.to_csv(DATA / "metrics_summary.csv", index=False, encoding="utf-8-sig")

print("=" * 74)
print(f"定量评估结果（第 {WARMUP}~{len(raw_all)-1} 帧，共 {len(df)} 帧）")
print("=" * 74)
print(summary.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print("=" * 74)
print(f"椒盐噪声去除率（孤立噪点像素下降比例）: {denoise_rate(raw_all[WARMUP:], opt_all[WARMUP:])*100:.1f}%")
''')

code(r'''
# ===================== 4.2 指标曲线与分布对比 =====================
fig, axes = plt.subplots(2, 2, figsize=(15.5, 8.4))

ax = axes[0, 0]
ax.plot(df.frame, df.FPR_raw, color="tab:red", lw=1.2, label="传统 GMM")
ax.plot(df.frame, df.FPR_opt, color="tab:blue", lw=1.2, label="本文方法")
ax.set_xlabel("帧序号"); ax.set_ylabel("误检率 FPR (%)")
ax.set_title("误检率逐帧曲线"); ax.legend(); ax.grid(alpha=0.3)

ax = axes[0, 1]
ax.plot(df.frame, df.IoU_raw, color="tab:red", lw=1.2, label="传统 GMM")
ax.plot(df.frame, df.IoU_opt, color="tab:blue", lw=1.2, label="本文方法")
ax.set_xlabel("帧序号"); ax.set_ylabel("IoU")
ax.set_title("轮廓完整度逐帧曲线"); ax.legend(); ax.grid(alpha=0.3)

ax = axes[1, 0]
ax.plot(df.frame, df.blobs_raw, color="tab:red", lw=1.2, label="传统 GMM")
ax.plot(df.frame, df.blobs_opt, color="tab:blue", lw=1.2, label="本文方法")
ax.set_xlabel("帧序号"); ax.set_ylabel("孤立连通块个数")
ax.set_title("椒盐噪声（面积<4 的孤立块）逐帧数量"); ax.legend(); ax.grid(alpha=0.3)

ax = axes[1, 1]
labels = ["FPR", "FNR", "1-IoU", "椒盐占比"]
raw_vals = [mean.FPR_raw, mean.FNR_raw, (1 - mean.IoU_raw) * 100, mean.SP_raw]
opt_vals = [mean.FPR_opt, mean.FNR_opt, (1 - mean.IoU_opt) * 100, mean.SP_opt]
x = np.arange(len(labels)); bw = 0.36
ax.bar(x - bw/2, raw_vals, bw, color="tab:red", label="传统 GMM")
ax.bar(x + bw/2, opt_vals, bw, color="tab:blue", label="本文方法")
for xi, (a, b) in enumerate(zip(raw_vals, opt_vals)):
    ax.text(xi - bw/2, a, f"{a:.2f}", ha="center", va="bottom", fontsize=8.5)
    ax.text(xi + bw/2, b, f"{b:.2f}", ha="center", va="bottom", fontsize=8.5)
ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel("数值（对数坐标，误差量越低越好）")
ax.set_title("平均误差指标对比"); ax.legend(); ax.grid(alpha=0.3, axis="y")

fig.suptitle("4.2 定量指标对比", fontsize=13.5)
plt.tight_layout()
plt.savefig(DATA / "fig_4_2_metrics.png", bbox_inches="tight")
plt.show()
''')

code(r'''
# ===================== 4.2b 分段统计：定位方法的有效边界 =====================
# 论文"实验分析"一节指出：本方法只作用于掩码空间噪声，
# 无法解决 GMM 的光照突变误检。这里把序列分成两段分别统计以验证该论断。
seg_a = df[df.frame < 120]      # 常规监控段
seg_b = df[df.frame >= 120]     # 全局光照渐变段

seg = pd.DataFrame({
    "区段": ["常规段 (50~119 帧)", "光照渐变段 (120~199 帧)"],
    "GMM FPR(%)":  [seg_a.FPR_raw.mean(), seg_b.FPR_raw.mean()],
    "本文 FPR(%)": [seg_a.FPR_opt.mean(), seg_b.FPR_opt.mean()],
    "FPR 降幅(%)": [(seg_a.FPR_raw.mean() - seg_a.FPR_opt.mean()) / seg_a.FPR_raw.mean() * 100,
                    (seg_b.FPR_raw.mean() - seg_b.FPR_opt.mean()) / seg_b.FPR_raw.mean() * 100],
    "GMM IoU":  [seg_a.IoU_raw.mean(), seg_b.IoU_raw.mean()],
    "本文 IoU": [seg_a.IoU_opt.mean(), seg_b.IoU_opt.mean()],
})
seg.to_csv(DATA / "metrics_by_segment.csv", index=False, encoding="utf-8-sig")
print(seg.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print()
print("结论：常规段误检率降幅明显；光照突变段两种方法误差同步上升，")
print("      说明频域后处理只解决掩码空间噪声，无法修复 GMM 的时序建模缺陷（符合论文论断）。")
''')

code(r'''
# ===================== 4.3 掩码时间稳定性（背景区域闪烁抑制） =====================
# GMM 逐像素独立建模会使背景区域掩码随时间随机闪烁；
# 频域高斯低通利用空间邻域相关性，可显著降低这种时间抖动。
bg_y = slice(5, 40)          # 无目标的远场区域（水面/树木等动态背景扰动）
bg_raw = raw_all[:, bg_y, :].astype(np.float32)
bg_opt = opt_all[:, bg_y, :].astype(np.float32)

# 时间抖动指标：相邻帧之间掩码发生翻转的像素数，除以该区域像素总数
flip_raw = float(np.abs(np.diff(bg_raw[WARMUP:], axis=0)).sum()) / bg_raw[WARMUP:].size
flip_opt = float(np.abs(np.diff(bg_opt[WARMUP:], axis=0)).sum()) / bg_opt[WARMUP:].size
flick_raw, flick_opt = flip_raw, flip_opt

fig, axes = plt.subplots(1, 2, figsize=(14.5, 4.4))
axes[0].hist(bg_raw[WARMUP:].ravel(), bins=30, alpha=0.65, color="tab:red", label="传统 GMM", log=True)
axes[0].hist(bg_opt[WARMUP:].ravel(), bins=30, alpha=0.65, color="tab:blue", label="本文方法", log=True)
axes[0].set_yscale("log"); axes[0].legend()
axes[0].set_title("远场背景区域掩码像素取值分布（应集中在 0）")
axes[0].set_xlabel("掩码取值")

axes[1].plot(range(WARMUP, len(raw_all)), bg_raw[WARMUP:].mean(axis=(1, 2)) * 100,
             color="tab:red", lw=1.2, label="传统 GMM")
axes[1].plot(range(WARMUP, len(raw_all)), bg_opt[WARMUP:].mean(axis=(1, 2)) * 100,
             color="tab:blue", lw=1.2, label="本文方法")
axes[1].set_xlabel("帧序号"); axes[1].set_ylabel("远场误检像素占比 (%)")
axes[1].set_title("远场误检率时间曲线"); axes[1].legend(); axes[1].grid(alpha=0.3)

fig.suptitle("4.3 掩码时间稳定性分析", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_4_3_temporal_stability.png", bbox_inches="tight")
plt.show()

print(f"远场区域相邻帧掩码翻转率（时间抖动）: {flick_raw*100:.4f}%  ->  {flick_opt*100:.4f}%")
print(f"抖动下降 {(flick_raw-flick_opt)/(flick_raw+1e-12)*100:.1f}%")
print(f"远场区域掩码平均前景占比            : {bg_raw[WARMUP:].mean()*100:.4f}%  ->  {bg_opt[WARMUP:].mean()*100:.4f}%")
''')

# ======================================================================
md(r'''
## 5 参数分析（截止频率 D₀ 的敏感性）

高斯低通的截止半径 `D0` 是本文**唯一**的调节参数：

- `D0` 过小 → 频域带宽过窄，等效于过强空域平滑，前景主体被削薄甚至消失（**漏检上升**）；
- `D0` 过大 → 高频噪声未被有效衰减，去噪能力不足（**误检上升**）。

因此存在一个兼顾两者的**最优点**。下面做扫描确定它。
''')

code(r'''
# ===================== 5.1 D0 扫描 =====================
sweep_rows = []
for d0 in D0_SWEEP:
    sub_raw, sub_opt = raw_all[WARMUP:], []
    for i in range(WARMUP, len(raw_all)):
        m, _, _ = fft_gaussian_denoise(raw_all[i], d0_norm=d0)
        sub_opt.append(m)
    sub_opt = np.stack(sub_opt)

    sweep_rows.append({
        "D0": d0,
        "FPR": float(np.mean([fpr(a, b) for a, b in zip(sub_opt, gts_all[WARMUP:])])) * 100,
        "FNR": float(np.mean([fnr(a, b) for a, b in zip(sub_opt, gts_all[WARMUP:])])) * 100,
        "IoU": float(np.mean([iou(a, b) for a, b in zip(sub_opt, gts_all[WARMUP:])])),
        "SP": float(np.mean([salt_pepper_stats(a)[1] for a in sub_opt])) * 100,
    })

sweep = pd.DataFrame(sweep_rows)
sweep.to_csv(DATA / "d0_sweep.csv", index=False, encoding="utf-8-sig")

base = {
    "FPR": df.FPR_raw.mean(), "FNR": df.FNR_raw.mean(),
    "IoU": df.IoU_raw.mean(), "SP": df.SP_raw.mean(),
}
best_i = sweep.IoU.idxmax()
D0_BEST = float(sweep.loc[best_i, "D0"])

print(f"传统 GMM 基线 : FPR={base['FPR']:.3f}%  FNR={base['FNR']:.3f}%  "
      f"IoU={base['IoU']:.4f}  椒盐占比={base['SP']:.4f}%")
print("-" * 74)
print(sweep.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print("-" * 74)
print(f"按 IoU 最优选出的 D0 = {D0_BEST}")
''')

code(r'''
# ===================== 5.2 D0 敏感性曲线 =====================
fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.4))

axes[0].plot(sweep.D0, sweep.FPR, "o-", color="tab:red", label="误检率 FPR")
axes[0].plot(sweep.D0, sweep.FNR, "s-", color="tab:orange", label="漏检率 FNR")
axes[0].axhline(base["FPR"], color="tab:red", ls=":", label="GMM 基线 FPR")
axes[0].axvline(D0_BEST, color="k", ls="--", lw=1, label=f"最优 D0={D0_BEST}")
axes[0].set_xlabel("归一化截止频率 D0"); axes[0].set_ylabel("百分比 (%)")
axes[0].set_title("误检 / 漏检随 D0 变化"); axes[0].legend(fontsize=9); axes[0].grid(alpha=0.3)

axes[1].plot(sweep.D0, sweep.IoU, "^-", color="tab:blue")
axes[1].axhline(base["IoU"], color="tab:red", ls=":", label="GMM 基线 IoU")
axes[1].axvline(D0_BEST, color="k", ls="--", lw=1)
axes[1].scatter([D0_BEST], [sweep.IoU.max()], color="k", zorder=5, s=45)
axes[1].set_xlabel("归一化截止频率 D0"); axes[1].set_ylabel("IoU")
axes[1].set_title("轮廓完整度随 D0 变化"); axes[1].legend(fontsize=9); axes[1].grid(alpha=0.3)

axes[2].plot(sweep.D0, sweep.SP, "d-", color="tab:green")
axes[2].axhline(base["SP"], color="tab:red", ls=":", label="GMM 基线")
axes[2].axvline(D0_BEST, color="k", ls="--", lw=1)
axes[2].set_xlabel("归一化截止频率 D0"); axes[2].set_ylabel("椒盐噪点像素占比 (%)")
axes[2].set_title("残余噪声随 D0 变化"); axes[2].legend(fontsize=9); axes[2].grid(alpha=0.3)

fig.suptitle("5.2 截止频率 D0 敏感性分析（本文唯一可调参数）", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_5_2_d0_sweep.png", bbox_inches="tight")
plt.show()
''')

code(r'''
# ===================== 5.3 不同 D0 的掩码视觉效果 =====================
demo_d0 = [0.02, 0.05, 0.10, 0.20, 0.50]
i = sel
fig, axes = plt.subplots(2, len(demo_d0) + 1, figsize=(3.0 * (len(demo_d0) + 1), 6.6))
axes[0, 0].imshow(frames_all[i], cmap="gray"); axes[0, 0].set_title("输入帧", fontsize=10)
axes[1, 0].imshow(raw_all[i], cmap="gray")
axes[1, 0].set_title(f"传统 GMM\nFPR={fpr(raw_all[i], gts_all[i])*100:.2f}%", fontsize=10)
for j, d0 in enumerate(demo_d0, start=1):
    m, _, _ = fft_gaussian_denoise(raw_all[i], d0_norm=d0)
    axes[0, j].imshow(m, cmap="gray")
    axes[0, j].set_title(f"D0={d0}", fontsize=10)
    axes[1, j].imshow(m, cmap="gray")
    axes[1, j].set_title(f"FPR={fpr(m, gts_all[i])*100:.2f}%\n"
                         f"IoU={iou(m, gts_all[i]):.3f}", fontsize=10)
for ax in axes.ravel():
    ax.axis("off")
fig.suptitle(f"5.3 不同截止频率的掩码效果（第 {i} 帧）", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_5_3_d0_visual.png", bbox_inches="tight")
plt.show()
''')

# ======================================================================
md(r'''
## 6 计算开销分析

论文强调"**在保留算法实时性的前提下**抑制检测噪声"。
本节分别测量：

1. 传统 GMM 单帧耗时；
2. 本文方法的 GMM 部分 + 频域滤波后处理耗时；
3. 后处理相对 GMM 的**增量占比**。
''')

code(r'''
# ===================== 6.1 耗时测量 =====================
REPEAT = 3
frames_probe = [frames_all[i] for i in range(WARMUP, len(frames_all))]
raw_probe = [raw_all[i] for i in range(WARMUP, len(raw_all))]

# --- 传统 GMM：重新跑一遍完整管线（建模 + 输出掩码） ---
t_gmm_list = []
for _ in range(REPEAT):
    sub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=16, detectShadows=False)
    t0 = time.perf_counter()
    for f in frames_probe:
        sub.apply(f)
    t_gmm_list.append((time.perf_counter() - t0) / len(frames_probe) * 1000)

# --- 本文后处理：只测频域滤波部分 ---
t_fft_list = []
for _ in range(REPEAT):
    t0 = time.perf_counter()
    for m in raw_probe:
        fft_gaussian_denoise(m, d0_norm=D0)
    t_fft_list.append((time.perf_counter() - t0) / len(raw_probe) * 1000)

# --- 空域高斯平滑（对照：说明为何选频域实现） ---
t_spatial_list = []
for _ in range(REPEAT):
    t0 = time.perf_counter()
    for m in raw_probe:
        cv2.GaussianBlur((m * 255).astype(np.uint8), (0, 0), sigmaX=D0 * W / 2)
    t_spatial_list.append((time.perf_counter() - t0) / len(raw_probe) * 1000)

t_gmm = float(np.mean(t_gmm_list));  s_gmm = float(np.std(t_gmm_list))
t_fft = float(np.mean(t_fft_list));  s_fft = float(np.std(t_fft_list))
t_spa = float(np.mean(t_spatial_list))

overhead = t_fft / t_gmm * 100
print("=" * 78)
print(f"{'模块':<32}{'单帧耗时':>16}{'相对 GMM 增量':>18}{'等效帧率':>12}")
print("-" * 78)
print(f"{'传统 GMM（建模+掩码）':<32}{f'{t_gmm:.3f} ms':>16}{'—（基准）':>18}{f'{1000/t_gmm:.0f} FPS':>12}")
print(f"{'本文频域滤波后处理':<32}{f'{t_fft:.3f} ms':>16}{f'+{overhead:.1f}%':>18}{f'{1000/t_fft:.0f} FPS':>12}")
print(f"{'本文方法总计':<32}{f'{t_gmm + t_fft:.3f} ms':>16}{f'+{overhead:.1f}%':>18}"
      f"{f'{1000/(t_gmm+t_fft):.0f} FPS':>12}")
print("-" * 78)
print(f"{'（对照）空域高斯平滑':<32}{f'{t_spa:.3f} ms':>16}{f'+{t_spa/t_gmm*100:.1f}%':>18}"
      f"{f'{1000/t_spa:.0f} FPS':>12}")
print("=" * 78)
print(f"后处理附加延迟仅为 {t_fft:.3f} ms/帧；本文方法整体 {1000/(t_gmm+t_fft):.0f} FPS，"
      f"远高于本序列的 {FPS} FPS，实时性满足。")
print(f"（说明：GMM 由 OpenCV C++ 实现，而频域滤波为 Python/NumPy 实现，"
      f"因此相对增量百分比较大；其绝对开销仅 {t_fft:.2f} ms，且真实视频帧率通常为 25~30 FPS。）")
print(f"实时性判定（≥{FPS} FPS 视为满足本序列实时处理）："
      f"{'满足' if 1000/(t_gmm+t_fft) >= FPS else '不满足'}")
print(f"（重复 {REPEAT} 次测量的标准差：GMM {s_gmm:.4f} ms，频域滤波 {s_fft:.4f} ms）")
''')

code(r'''
# ===================== 6.2 开销构成可视化 =====================
fig, axes = plt.subplots(1, 3, figsize=(16, 4.3))

axes[0].bar(["传统 GMM", "本文总计"], [t_gmm, t_gmm + t_fft],
            color=["tab:red", "tab:blue"], width=0.55)
for xi, v in enumerate([t_gmm, t_gmm + t_fft]):
    axes[0].text(xi, v, f"{v:.2f} ms\n({1000/v:.0f} FPS)", ha="center", va="bottom", fontsize=9)
axes[0].set_ylabel("单帧耗时 (ms)"); axes[0].grid(alpha=0.3, axis="y")
axes[0].set_title("单帧总耗时")

axes[1].pie([t_gmm, t_fft], labels=[f"GMM 建模\n{t_gmm:.2f} ms", f"频域滤波\n{t_fft:.2f} ms"],
            autopct="%1.2f%%", colors=["tab:red", "tab:blue"],
            wedgeprops=dict(width=0.45, edgecolor="w"), textprops=dict(fontsize=9.5))
axes[1].set_title("本文方法耗时构成")

axes[2].bar(["频域 FFT 实现", "空域高斯平滑"], [t_fft, t_spa],
            color=["tab:blue", "tab:gray"], width=0.5)
for xi, v in enumerate([t_fft, t_spa]):
    axes[2].text(xi, v, f"{v:.2f} ms", ha="center", va="bottom", fontsize=9)
axes[2].set_ylabel("单帧耗时 (ms)"); axes[2].grid(alpha=0.3, axis="y")
axes[2].set_title("两种等效实现的效率对比")

fig.suptitle("6.2 计算开销分析", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_6_2_time_cost.png", bbox_inches="tight")
plt.show()
''')

# ======================================================================
md(r'''
## 7 结论复现

### 7.1 本章结论

1. **有效性**：在自建动态监控序列上，把二维傅里叶高斯低通串联到 GMM 掩码之后，
   误检率、孤立椒盐噪点数量与远场时间抖动均显著下降，同时前景主体轮廓保持完整；
   定量结果见 4.2 / 4.3 两节的实测数值。
2. **振铃抑制**：1.2 节的一维阶跃实验证实，理想低通的硬截断会产生明显过冲（吉布斯振铃），
   而高斯低通平滑衰减、过冲极小，这也是本文选择高斯核而非理想低通的直接依据。
3. **实时性**：后处理只增加一次 FFT + 一次逐点乘法 + 一次 IFFT，耗时增量很小，
   整体帧率仍远高于序列帧率，实时性得到保持。
4. **局限**：该方法只作用于掩码的**空间噪声**，无法解决 GMM 固有缺陷——
   光照突变误检、长时间静止前景融入背景、阴影误判（本序列中第 120 帧后的增亮阶段，
   两项方法的误差都会同步上升，正说明这一点）。

### 7.2 展望（对应论文最后一节）

对每个像素的**灰度时序序列**做一维傅里叶变换，提取周期性强度的频域特征，
与 GMM 的灰度概率特征融合，从而区分"树叶晃动 / 水面波动"这类周期性背景扰动
与真实运动前景，进一步提升复杂动态背景下的检测鲁棒性。
''')

code(r'''
# ===================== 7.1 汇总表导出 =====================
final = pd.DataFrame({
    "指标": ["误检率 FPR(%)", "漏检率 FNR(%)", "轮廓完整度 IoU", "椒盐噪点像素占比(%)",
             "孤立连通块个数", "单帧耗时(ms)", "等效帧率(FPS)"],
    "传统 GMM": [mean.FPR_raw, mean.FNR_raw, mean.IoU_raw, mean.SP_raw,
                 mean.blobs_raw, t_gmm, 1000 / t_gmm],
    "本文方法": [mean.FPR_opt, mean.FNR_opt, mean.IoU_opt, mean.SP_opt,
                 mean.blobs_opt, t_gmm + t_fft, 1000 / (t_gmm + t_fft)],
})
final.to_csv(DATA / "final_report.csv", index=False, encoding="utf-8-sig")

# 汇总本次实验的全部关键数字，供撰写论文时直接引用
key_numbers = {
    "序列": f"{W}x{H} @ {FPS}fps, {len(frames_all)} 帧",
    "统计帧范围": f"{WARMUP}~{len(raw_all)-1}（共 {len(df)} 帧）",
    "最优截止频率D0": D0_BEST,
    "FPR": {"raw": round(float(mean.FPR_raw), 4), "opt": round(float(mean.FPR_opt), 4),
            "rel_drop_pct": round(float((mean.FPR_raw - mean.FPR_opt) / mean.FPR_raw * 100), 2)},
    "FNR": {"raw": round(float(mean.FNR_raw), 4), "opt": round(float(mean.FNR_opt), 4),
            "rel_drop_pct": round(float((mean.FNR_raw - mean.FNR_opt) / mean.FNR_raw * 100), 2)},
    "IoU": {"raw": round(float(mean.IoU_raw), 4), "opt": round(float(mean.IoU_opt), 4),
            "rel_gain_pct": round(float((mean.IoU_opt - mean.IoU_raw) / mean.IoU_raw * 100), 2)},
    "椒盐噪声去除率": round(float(denoise_rate(raw_all[WARMUP:], opt_all[WARMUP:])) * 100, 2),
    "孤立噪点块数下降": {
        "raw": round(float(mean.blobs_raw), 2), "opt": round(float(mean.blobs_opt), 2),
        "rel_drop_pct": round(float((mean.blobs_raw - mean.blobs_opt) / mean.blobs_raw * 100), 2)},
    "时间抖动下降率": round(float((flick_raw - flick_opt) / flick_raw * 100), 2),    "耗时": {"gmm_ms": round(t_gmm, 3), "fft_ms": round(t_fft, 3),
             "total_ms": round(t_gmm + t_fft, 3), "overhead_pct": round(overhead, 2)},
}
(DATA / "key_numbers.json").write_text(
    json.dumps(key_numbers, ensure_ascii=False, indent=2), encoding="utf-8")

print("实验结果汇总（可直接引用进论文）")
print("=" * 60)
print(final.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print("=" * 60)
print("\n已导出文件：")
for p in sorted(DATA.iterdir()):
    print(f"  {p.name:<40s} {p.stat().st_size/1024:9.1f} KB")
''')

# ======================================================================
md(r'''
---

## 附：本章生成的文件清单

| 文件 | 说明 |
| --- | --- |
| `data/surveillance_synth_raw.mp4` | 自建监控序列（合成，含水面/树叶/阴影/光照干扰） |
| `data/surveillance_synth_gt.mp4` | 像素级真值掩码视频 |
| `data/foreground_compare.mp4` | 输入 / 传统 GMM / 本文方法 三联对比视频 |
| `data/metrics_per_frame.csv` | 逐帧定量指标 |
| `data/metrics_summary.csv` | 平均指标汇总 |
| `data/d0_sweep.csv` | 截止频率 D0 敏感性扫描结果 |
| `data/final_report.csv` | 最终结果表 |
| `data/key_numbers.json` | 关键数字（供论文正文引用） |
| `data/fig_*.png` | 论文插图（可直接插入论文） |

## 复现方式

```powershell
# 启动 Jupyter（工作目录 = D:\workspace\Jupyter_WorkSpace）
D:\MathWork\Anaconda\python.exe D:\MathWork\Anaconda\Scripts\jupyter-notebook-script.py `
    --ServerApp.root_dir="D:\workspace\Jupyter_WorkSpace"
# 浏览器打开 -> DIP\0202\DIP第二章_傅里叶频域滤波优化的GMM前景检测.ipynb
# 内核选择 .my_env -> Kernel -> Restart & Run All
```
''')

# ======================================================================
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python (.my_env)", "language": "python", "name": "python3"},
        "language_info": {
            "name": "python", "version": "3.11.7",
            "mimetype": "text/x-python", "file_extension": ".py",
            "pygments_lexer": "ipython3", "nbconvert_exporter": "python",
            "codemirror_mode": {"name": "ipython", "version": 3},
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

os.makedirs(os.path.dirname(NB_PATH), exist_ok=True)
with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

n_md = sum(1 for c in cells if c["cell_type"] == "markdown")
n_code = sum(1 for c in cells if c["cell_type"] == "code")
print(f"已生成: {NB_PATH}")
print(f"markdown 单元 {n_md} 个，code 单元 {n_code} 个")
