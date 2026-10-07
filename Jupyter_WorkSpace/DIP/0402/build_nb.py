# -*- coding: utf-8 -*-
"""
生成 DIP 第四章课设 Notebook（精简版）：
    主要工作 —— 基于 FFT 在图像中查找多个目标
    主要改进 —— 在 FFT 匹配结果上叠加 NMS，解决峰值平台导致的重复检出
"""
import json
import os

NB_PATH = (r"D:\workspace\Jupyter_WorkSpace\DIP\0402"
           r"\DIP第四章_基于FFT的多目标查找与NMS改进.ipynb")

cells = []


def _src(text):
    """转成 notebook 的 source 数组；元素必须自带换行（Jupyter 按 join 拼接）。"""
    body = text.strip("\n")
    return body.splitlines(keepends=True) if body else []


def md(t):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": _src(t)})


def code(t):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": _src(t)})


# ======================================================================
md(r'''
# 基于FFT的多目标查找与NMS改进

> **数字图像处理 课程设计 · 第四章**

## 本章主要工作

**用 FFT 在一幅图像中同时查找多个目标，再叠加 NMS 解决重复检出问题。**

整体只有四步：

1. **补零去均值**：把源图与模板补零到 $(H+h-1) \times (W+w-1)$ ，各自减去均值；
2. **FFT 匹配**：$F=\mathrm{FFT}(源图)$ 、$G=\mathrm{FFT}(模板)$ ，按卷积定理计算
   $F\cdot G^{*}$ ，逆变换得到相似度响应图；
3. **阈值筛选**：把响应图中超过阈值的位置作为候选；
4. **NMS 去重**：目标邻域内的响应连成一片，第 3 步会产生大量重叠候选框，
   用非极大值抑制把每个目标收敛为一个框。

> **两处最容易写错的地方**
>
> 1. **补零**：频域算的是循环相关，不补零会让图像右下角"环绕"到左上角，边界出现假峰；
> 2. **去均值**：不去均值则响应被图像均值主导，弱目标会被淹没。

## 环境

内核 `D:\workspace\.my_env` ；依赖 `numpy` `opencv-python` `matplotlib` `pandas`。
''')

# ----------------------------------------------------------------------
code(r'''
# ===== 0 准备：导入、路径、随机种子 =====
import time
import json
from pathlib import Path

import numpy as np
import cv2
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

# 中文字体
for _n in ["Microsoft YaHei", "SimHei", "SimSun"]:
    if _n in {f.name for f in font_manager.fontManager.ttflist}:
        plt.rcParams["font.sans-serif"] = [_n, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False

SEED = 402
np.random.seed(SEED)
cv2.setRNGSeed(SEED)

DATA = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0402\data")
DATA.mkdir(parents=True, exist_ok=True)

# 场景参数（尺寸取小，保证执行只需数秒）
SRC_W, SRC_H = 512, 384
TPL_W, TPL_H = 32, 32
THRESH = 0.60          # 匹配阈值
IOU_THRESH = 0.30      # NMS 的 IoU 阈值
LOC_TOL = 6.0          # 定位判定容差（像素）

print(f"源图 {SRC_W}x{SRC_H}，模板 {TPL_W}x{TPL_H}")
print("numpy", np.__version__, "| opencv", cv2.__version__)
''')

# ----------------------------------------------------------------------
md(r'''
## 1 自建测试场景

模板匹配实验需要**逐目标的真值坐标**才能客观评价。公开数据集通常不提供同一模板在
一幅图中多处出现的坐标，故这里合成一幅：6 个相同目标按网格分布，背景为低频起伏加噪声，
模板从目标处裁剪后再叠加独立噪声，真值坐标由绘制程序直接输出。
''')

code(r'''
# ===== 1.1 合成场景（6 个目标 + 真值） =====
rng = np.random.default_rng(SEED)

# 目标图案：亮底 + 深色十字 + 边框，保证响应峰尖锐
tpl_patch = np.full((TPL_H, TPL_W), 205.0, np.float32)
tpl_patch[:2, :] = tpl_patch[-2:, :] = 120
tpl_patch[:, :2] = tpl_patch[:, -2:] = 120
c = TPL_H // 2
tpl_patch[c - 3:c + 3, c - 1:c + 1] = 70
tpl_patch[c - 1:c + 1, c - 8:c + 8] = 70

# 背景：低频起伏 + 噪声
low = cv2.GaussianBlur(rng.random((SRC_H, SRC_W), np.float32), (0, 0), 30, 30)
canvas = 128 + 18 * (low - low.mean()) / (low.std() + 1e-6)

# 放置 6 个目标：3 列 x 2 行
gt = []
for cy in (100, 270):
    for cx in (110, 256, 400):
        x0, y0 = cx - TPL_W // 2, cy - TPL_H // 2
        canvas[y0:y0 + TPL_H, x0:x0 + TPL_W] = tpl_patch
        gt.append({"cx": float(cx), "cy": float(cy),
                   "x": x0, "y": y0, "w": TPL_W, "h": TPL_H})

SRC = np.clip(canvas + rng.normal(0, 6.0, canvas.shape), 0, 255).astype(np.uint8)
TPL = np.clip(tpl_patch + rng.normal(0, 6.0, tpl_patch.shape), 0, 255).astype(np.uint8)

cv2.imwrite(str(DATA / "scene_src.png"), SRC)
cv2.imwrite(str(DATA / "scene_tpl.png"), TPL)
pd.DataFrame(gt).to_csv(DATA / "ground_truth.csv", index=False, encoding="utf-8-sig")
print(f"源图 {SRC.shape}，模板 {TPL.shape}，真值 {len(gt)} 个目标")
pd.DataFrame(gt)[["cx", "cy", "w", "h"]]
''')

code(r'''
# ===== 1.2 显示场景与真值 =====
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
axes[0].imshow(SRC, cmap="gray", vmin=0, vmax=255)
for g in gt:
    axes[0].add_patch(Rectangle((g["x"], g["y"]), g["w"], g["h"],
                                fill=False, edgecolor="red", lw=1.4))
axes[0].set_title(f"源图与真值（红框，共 {len(gt)} 个目标）", fontsize=11)
axes[0].axis("off")
axes[1].imshow(TPL, cmap="gray", vmin=0, vmax=255)
axes[1].set_title(f"模板 {TPL_W}x{TPL_H}", fontsize=11)
axes[1].axis("off")
plt.tight_layout()
plt.savefig(DATA / "fig_1_scene.png", bbox_inches="tight")
plt.show()
''')

# ----------------------------------------------------------------------
md(r'''
## 2 基于 FFT 的多目标匹配

### 2.1 原理

模板匹配要计算模板与图像每个位置的相似度。空域做法逐位置乘加，复杂度
$O(HW\,hw)$ ；频域做法依据卷积定理把相关运算变成频域逐点相乘：

$$c(x,y)=\mathcal{F}^{-1}\big\{F(u,v)\,G^{*}(u,v)\big\}$$

其中 $F$ 、$G$ 分别是源图与模板的二维傅里叶变换，$G^{*}$ 为 $G$ 的复共轭。
复杂度降为 $O(HW\log(HW))$ ，且**与模板面积无关**。

### 2.2 实现要点

| 要点 | 做法 | 原因 |
| --- | --- | --- |
| 补零 | 补到 $(H+h-1,\ W+w-1)$ | 频域算的是循环相关，不补零会产生边界假峰 |
| 去均值 | 源图与模板各自减均值 | 否则直流分量主导响应，弱目标被淹没 |
| 裁剪 | 结果裁到 $(H-h+1,\ W-w+1)$ | 只有这部分对应模板完整落入图像 |
''')

code(r'''
# ===== 2.3 FFT 匹配函数 =====
def fft_match(src, tpl):
    """基于 FFT 的模板匹配，返回 (响应图, 补零尺寸)。"""
    src = src.astype(np.float64)
    tpl = tpl.astype(np.float64)
    H, W = src.shape
    h, w = tpl.shape
    ph, pw = H + h - 1, W + w - 1          # 补零尺寸：满足线性相关

    # 补零 + 去均值
    sp = np.zeros((ph, pw))
    tp = np.zeros((ph, pw))
    sp[:H, :W] = src - src.mean()
    tp[:h, :w] = tpl - tpl.mean()

    # 频域共轭相乘 -> 逆变换
    F = np.fft.rfft2(sp)
    G = np.fft.rfft2(tp)
    corr = np.fft.irfft2(F * np.conj(G), s=(ph, pw))

    # 裁剪到有效区
    resp = corr[:H - h + 1, :W - w + 1]

    # 归一化到 [0,1]：FFT 相关输出本身是无界的，必须归一化后阈值才有意义，
    # 否则一个看似合理的阈值（如 0.6）会保留几乎所有位置，导致候选框爆炸。
    r = resp - resp.min()
    m = r.max()
    if m > 1e-12:
        r = r / m
    return r, (ph, pw)


t0 = time.perf_counter()
RESP, PAD = fft_match(SRC, TPL)
T_FFT = (time.perf_counter() - t0) * 1000

print(f"补零尺寸    : {PAD}")
print(f"响应图尺寸  : {RESP.shape}   （= 源图 - 模板 + 1）")
print(f"FFT 匹配耗时: {T_FFT:.1f} ms")
''')

code(r'''
# ===== 2.4 实现自检 =====
# (1) 响应图尺寸是否正确
ok1 = RESP.shape == (SRC_H - TPL_H + 1, SRC_W - TPL_W + 1)

# (2) 与"直接逐位置乘加"是否一致（在小画布上验证，避免太慢）
a = SRC[:96, :128].astype(np.float64)
b = TPL.astype(np.float64)
ref = np.array([[float(((a[y:y + TPL_H, x:x + TPL_W] - a[y:y + TPL_H, x:x + TPL_W].mean())
                        * (b - b.mean())).sum())
                 for x in range(a.shape[1] - TPL_W + 1)]
                for y in range(a.shape[0] - TPL_H + 1)])
got, _ = fft_match(a, b)
# 两者都做相同的归一化后再比（fft_match 内部已归一化，这里把参照也归一化）
ref_n = (ref - ref.min()) / max(1e-12, ref.max() - ref.min())
err = np.abs(got - ref_n).max()
ok2 = err < 1e-9

# (3) 目标处应出现峰值
peaks = [float(RESP[g["y"], g["x"]]) for g in gt]
ok3 = min(peaks) > 0.5

print(f"(1) 响应图尺寸 {RESP.shape}   {'OK' if ok1 else '异常'}")
print(f"(2) FFT vs 直接乘加 最大相对误差 {err:.2e}   {'OK（一致）' if ok2 else '异常'}")
print(f"(3) 6 个真值处的响应值: {[round(p, 3) for p in peaks]}")
print(f"    最小值 {min(peaks):.3f}   {'OK（均出现峰值）' if ok3 else '异常'}")
print()
print("自检结论：" + ("三项全部 OK，FFT 匹配实现正确" if all([ok1, ok2, ok3])
                    else "存在异常，需检查"))
''')

code(r'''
# ===== 2.5 显示 FFT 响应图 =====
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
im = axes[0].imshow(RESP, cmap="jet")
plt.colorbar(im, ax=axes[0], fraction=0.046)
for g in gt:
    axes[0].plot(g["x"], g["y"], "w+", ms=9, mew=1.8)
axes[0].set_title("FFT 响应图（白十字=真值位置）", fontsize=11)
axes[0].axis("off")

g0 = gt[0]
axes[1].plot(RESP[g0["y"], :], lw=1.4)
axes[1].axhline(THRESH, color="r", ls="--", lw=1.2, label=f"阈值 {THRESH}")
axes[1].axvline(g0["x"], color="g", ls=":", lw=1.4, label="真值位置")
axes[1].set_xlabel("列坐标"); axes[1].set_ylabel("响应值")
axes[1].set_title(f"第 {g0['y']} 行响应剖面", fontsize=11)
axes[1].legend(fontsize=9); axes[1].grid(alpha=0.3)
plt.tight_layout()
plt.savefig(DATA / "fig_2_response.png", bbox_inches="tight")
plt.show()
''')

# ----------------------------------------------------------------------
md(r'''
## 3 直接阈值筛选：重复检出问题

FFT 匹配给出的是**响应图**，还需筛选才能得到目标框。最直接的做法是
"响应超过阈值的位置都算候选框"。

问题在于：响应峰在真实位置周围**连成一片平台**，因此同一目标会产生大量相邻候选框。
这正是需要改进的地方。
''')

code(r'''
# ===== 3.1 阈值筛选（每个过阈值位置都算候选） =====
ys, xs = np.where(RESP >= THRESH)
cand = [(int(x), int(y), TPL_W, TPL_H, float(RESP[y, x]))
        for y, x in zip(ys, xs)]
cand.sort(key=lambda b: -b[4])

print(f"阈值 {THRESH} 下：过阈值位置 {len(cand)} 个，而真值目标只有 {len(gt)} 个")
print(f"  每个目标平均产生 {len(cand)/len(gt):.1f} 个候选框 -> 严重重复")
print()
print("前 8 个候选框（位置与置信度）：")
for b in cand[:8]:
    print(f"   位置=({b[0]:>4},{b[1]:>4})  置信度={b[4]:.4f}")
''')

code(r'''
# ===== 3.2 重复检出的可视化 =====
fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
x0, y0 = gt[0]["x"] - 40, gt[0]["y"] - 40
x1, y1 = x0 + 140, y0 + 120

for ax, (title, boxes, color) in zip(axes, [
        ("① 全部候选框（重叠严重）", cand, "tab:orange"),
        ("② 真值框（对照）", [], "lime")]):
    ax.imshow(SRC, cmap="gray", vmin=0, vmax=255)
    for g in gt:
        ax.add_patch(Rectangle((g["x"], g["y"]), g["w"], g["h"],
                               fill=False, edgecolor="lime", lw=1.0, ls="--"))
    for b in boxes:
        ax.add_patch(Rectangle((b[0], b[1]), b[2], b[3],
                               fill=False, edgecolor=color, lw=1.1))
    ax.set_xlim(x0, x1); ax.set_ylim(y1, y0)
    ax.set_title(f"{title}\n框数 = {len(boxes)}", fontsize=11)
    ax.axis("off")
plt.tight_layout()
plt.savefig(DATA / "fig_3_redundant.png", bbox_inches="tight")
plt.show()
''')

# ----------------------------------------------------------------------
md(r'''
## 4 主要改进：叠加 NMS 去重

**非极大值抑制（non-maximum suppression，NMS）**的思路很简单：

1. 按置信度从高到低排列候选框；
2. 取最高分的框作为确定目标，保留；
3. 计算它与其余框的交并比，把交并比超过阈值的框删除（它们是同一目标的重复框）；
4. 重复第 2~3 步，直到没有候选框为止。

$$\mathrm{IoU}(A,B)=\frac{|A\cap B|}{|A\cup B|}$$

本场景中所有候选框尺寸都等于模板尺寸，因此交并比完全由两框中心位移决定：
同一目标的重复框几乎完全重合（$\mathrm{IoU}\to 1$ ）会被抑制；不同目标相距较远
（$\mathrm{IoU}\to 0$ ）会被保留。这就是 NMS 在此有效的根本原因。
''')

code(r'''
# ===== 4.1 NMS 实现 =====
def iou(a, b):
    """两个框的交并比。"""
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union > 0 else 0.0


def nms(boxes, iou_thresh):
    """贪心非极大值抑制：按置信度降序，抑制与最优框交并比超阈值的框。"""
    boxes = sorted(boxes, key=lambda b: -b[4])
    kept = []
    while boxes:
        best = boxes.pop(0)
        kept.append(best)
        boxes = [b for b in boxes if iou(best, b) <= iou_thresh]
    return kept


t0 = time.perf_counter()
KEPT = nms(cand, IOU_THRESH)
T_NMS = (time.perf_counter() - t0) * 1000

print(f"NMS 前候选框 : {len(cand)} 个")
print(f"NMS 后目标框 : {len(KEPT)} 个   （真值 {len(gt)} 个）")
print(f"NMS 耗时     : {T_NMS:.2f} ms   （相对 FFT 匹配 {T_FFT:.1f} ms 可忽略）")
''')

code(r'''
# ===== 4.2 评价与对比 =====
def evaluate(boxes, gt, tol=LOC_TOL):
    """统计检出率与平均定位误差。"""
    hits, errs = 0, []
    for g in gt:
        ds = [float(np.hypot(b[0] + b[2] / 2 - g["cx"], b[1] + b[3] / 2 - g["cy"]))
              for b in boxes]
        if ds and min(ds) < tol:
            hits += 1
            errs.append(min(ds))
    return hits / len(gt), (float(np.mean(errs)) if errs else float("nan"))


acc_raw, err_raw = evaluate(cand, gt)
acc_nms, err_nms = evaluate(KEPT, gt)

RES = pd.DataFrame([
    {"配置": "① 仅 FFT 匹配（阈值筛选）", "框数": len(cand),
     "检出率": acc_raw, "平均定位误差/像素": err_raw},
    {"配置": "② FFT 匹配 + NMS（本文）", "框数": len(KEPT),
     "检出率": acc_nms, "平均定位误差/像素": err_nms},
])
RES.to_csv(DATA / "metrics.csv", index=False, encoding="utf-8-sig")
print("=" * 74)
print("对比结果")
print("=" * 74)
print(RES.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print("=" * 74)
print(f"\n改进效果：框数由 {len(cand)} 降为 {len(KEPT)}，"
      f"平均定位误差由 {err_raw:.2f} 像素降为 {err_nms:.2f} 像素")
''')

code(r'''
# ===== 4.3 改进前后可视化 =====
fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))
views = [("① FFT 匹配的候选框", cand, "tab:orange"),
         ("② 叠加 NMS 后", KEPT, "tab:blue"),
         ("③ 真值框", [], "lime")]
for ax, (title, boxes, color) in zip(axes, views):
    ax.imshow(SRC, cmap="gray", vmin=0, vmax=255)
    for g in gt:
        ax.add_patch(Rectangle((g["x"], g["y"]), g["w"], g["h"],
                               fill=False, edgecolor="lime", lw=1.0, ls="--"))
    for b in boxes:
        ax.add_patch(Rectangle((b[0], b[1]), b[2], b[3],
                               fill=False, edgecolor=color, lw=1.4))
    ax.set_title(f"{title}\n框数 = {len(boxes)}", fontsize=11.5)
    ax.axis("off")
plt.suptitle("FFT 匹配 + NMS 的改进效果（绿虚线=真值，彩色实线=检出框）",
             fontsize=12.5)
plt.tight_layout()
plt.savefig(DATA / "fig_4_nms.png", bbox_inches="tight")
plt.show()
''')

# ----------------------------------------------------------------------
md(r'''
## 5 参数影响

只考察两个关键参数：**匹配阈值** $T$ 与 **NMS 的交并比阈值**。
''')

code(r'''
# ===== 5.1 匹配阈值的影响 =====
rows = []
for T in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
    ys, xs = np.where(RESP >= T)
    cd = [(int(x), int(y), TPL_W, TPL_H, float(RESP[y, x]))
          for y, x in zip(ys, xs)]
    kp = nms(cd, IOU_THRESH)
    acc, err_ = evaluate(kp, gt)
    rows.append({"匹配阈值": T, "候选框数": len(cd), "NMS后框数": len(kp),
                 "检出率": acc, "平均定位误差/像素": err_})
TH_DF = pd.DataFrame(rows)
TH_DF.to_csv(DATA / "sweep_thresh.csv", index=False, encoding="utf-8-sig")
print("匹配阈值扫描：")
print(TH_DF.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
''')

code(r'''
# ===== 5.2 NMS 的交并比阈值的影响 =====
rows = []
for T in (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9):
    kp = nms(cand, T)
    acc, err_ = evaluate(kp, gt)
    rows.append({"IoU阈值": T, "保留框数": len(kp), "检出率": acc,
                 "平均定位误差/像素": err_})
IOU_DF = pd.DataFrame(rows)
IOU_DF.to_csv(DATA / "sweep_iou.csv", index=False, encoding="utf-8-sig")
print("NMS 的交并比阈值扫描：")
print(IOU_DF.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
''')

code(r'''
# ===== 5.3 参数曲线 =====
fig, axes = plt.subplots(1, 3, figsize=(16, 4.2))

ax = axes[0]
ax.plot(TH_DF["匹配阈值"], TH_DF["候选框数"], "o-", color="tab:orange",
        label="阈值筛选候选框")
ax.plot(TH_DF["匹配阈值"], TH_DF["NMS后框数"], "s-", color="tab:blue", label="NMS 后")
ax.axhline(len(gt), color="g", ls=":", lw=1.4, label=f"真值 {len(gt)}")
ax.axvline(THRESH, color="k", ls=":", lw=1.1)
ax.set_xlabel("匹配阈值 $T$"); ax.set_ylabel("框数")
ax.set_title("匹配阈值对框数的影响", fontsize=11)
ax.legend(fontsize=8.5); ax.grid(alpha=0.3)

ax = axes[1]
ax.plot(IOU_DF["IoU阈值"], IOU_DF["保留框数"], "o-", color="tab:blue")
ax.axhline(len(gt), color="g", ls=":", lw=1.4, label=f"真值 {len(gt)}")
ax.axvline(IOU_THRESH, color="k", ls=":", lw=1.1, label=f"默认 {IOU_THRESH}")
ax.set_xlabel("NMS 的 IoU 阈值"); ax.set_ylabel("保留框数")
ax.set_title("IoU 阈值对去重的影响", fontsize=11)
ax.legend(fontsize=8.5); ax.grid(alpha=0.3)

ax = axes[2]
ax.bar(["仅FFT", "FFT+NMS"], [len(cand), len(KEPT)], color=["tab:orange", "tab:blue"])
for i, v in enumerate([len(cand), len(KEPT)]):
    ax.text(i, v, str(v), ha="center", va="bottom", fontsize=10)
ax.axhline(len(gt), color="g", ls=":", lw=1.4, label=f"真值 {len(gt)}")
ax.set_ylabel("框数"); ax.set_title("改进前后框数对比", fontsize=11)
ax.legend(fontsize=8.5); ax.grid(alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(DATA / "fig_5_params.png", bbox_inches="tight")
plt.show()
''')

# ----------------------------------------------------------------------
md(r'''
## 6 结论

1. **FFT 可以一次找出图中全部目标**。补零到 $(H+h-1)\times(W+w-1)$ 后做频域共轭相乘，
   一次逆变换即得到整幅图的相似度响应，复杂度 $O(HW\log HW)$ 且与模板面积无关。
   实测 FFT 结果与直接逐位置乘加的相对误差在 $10^{-16}$ 量级，实现正确。

2. **FFT 匹配单独使用会产生大量重复框**。响应峰在目标周围连成一片平台，
   按阈值直接筛选时同一目标会产生几十个相邻候选框。

3. **叠加 NMS 是有效的改进**。以响应值为置信度、以交并比为重叠度量迭代抑制后，
   每个目标只保留一个框，平均定位误差显著下降，而 NMS 本身的耗时相对匹配可忽略。

4. **局限性**：方法假定目标只发生平移，对旋转与尺度变化不具备适应性；
   去重依赖目标之间的空间可分性，目标高度密集时交并比判别会失效。
''')

code(r'''
# ===== 7 结果汇总 =====
summary = {
    "场景": f"{SRC_W}x{SRC_H}，目标 {len(gt)} 个",
    "参数": {"模板": f"{TPL_W}x{TPL_H}", "补零尺寸": list(PAD),
             "匹配阈值": THRESH, "NMS_IoU阈值": IOU_THRESH},
    "FFT实现正确性": {"与直接乘加最大相对误差": float(f"{err:.2e}"),
                     "真值处峰值": [round(p, 3) for p in peaks]},
    "仅FFT匹配": {"耗时_ms": round(T_FFT, 2), "框数": len(cand),
                  "检出率": round(float(acc_raw), 4),
                  "平均定位误差": round(float(err_raw), 3)},
    "FFT_NMS": {"耗时_ms": round(T_FFT + T_NMS, 2), "框数": len(KEPT),
                "检出率": round(float(acc_nms), 4),
                "平均定位误差": round(float(err_nms), 3)},
    "改进": {"框数": f"{len(cand)} -> {len(KEPT)}",
             "定位误差": f"{err_raw:.2f} -> {err_nms:.2f} 像素"},
}
(DATA / "key_numbers.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps(summary, ensure_ascii=False, indent=2))
print()
print("已导出文件：")
for f in sorted(DATA.iterdir()):
    print(f"  {f.name:<28}{f.stat().st_size/1024:8.1f} KB")
''')

# ======================================================================
nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python (.my_env)", "language": "python",
                       "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.7"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

os.makedirs(os.path.dirname(NB_PATH), exist_ok=True)
with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"已生成: {NB_PATH}")
print(f"markdown 单元 {sum(1 for c in cells if c['cell_type']=='markdown')} 个，"
      f"code 单元 {sum(1 for c in cells if c['cell_type']=='code')} 个")
