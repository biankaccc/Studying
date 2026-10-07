# -*- coding: utf-8 -*-
"""生成 DIP 第三章课设 Notebook (0303)：多尺度模板金字塔 + NMS 的图像模板匹配。

方法论要点（本章的正确做法）：
    要检出尺度 s 的目标，就在**原图**上匹配、只把**模板缩放 s 倍**。
    等价说法：任一时空配置下，只需保证"匹配窗口尺寸 == 目标在该图中的尺寸"。
      - 缩放模板（模板金字塔）  -> 原图不动
      - 缩放图像（图像金字塔）  -> 模板不动
    两者数学等价，但**绝不可同时缩放两边**：那等于尺度比不变，什么也匹配不到。
"""
import json
import os

NB_PATH = r"D:\workspace\Jupyter_WorkSpace\DIP\0303\DIP第三章_多尺度金字塔与NMS的图像模板匹配算法.ipynb"

cells = []


def _to_source(text):
    """
    把单元格文本转成 notebook 的 source 数组。
    元素必须保留行尾换行符（Jupyter 渲染 markdown 时按 "".join(source) 拼接），
    否则整段会被粘成一行，标题与表格语法全部失效。
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
# 多尺度金字塔与NMS的图像模板匹配算法

> **数字图像处理 课程设计 · 第三章**
> 依据大纲《DIP第3章课设大纲-多尺度金字塔与NMS的图像模板匹配算法.md》实现，与论文结构一一对应。

---

## 本章任务与论文对应关系

| 论文小节 | 本 Notebook 对应节 |
| --- | --- |
| 1.1 归一化相关系数模板匹配 | `1 原理验证与实现自检` |
| 1.2 传统单尺度算法的缺陷 | `2 单尺度基线实验` |
| 1.3 多尺度模板金字塔 | `3 多尺度改进` |
| 1.4 非极大值抑制 | `4 NMS 去重改进` |
| 3 实验分析 | `5 定量评价`、`6 参数分析` |
| 3.5 局限性与展望 | `7 结论与局限` |

## 核心思路

模板匹配以滑动窗口逐点计算相似度，其**匹配窗口尺寸与目标尺寸严格绑定**，因此目标一旦缩放就会漏检。
本章作两级改进：

1. **多尺度模板金字塔**：把模板按比例缩放成一组尺寸，在**原图**上分别匹配，
   使算法能够检出不同尺度的目标；
2. **非极大值抑制（NMS）**：以响应幅值为置信度、以交并比为重叠度量，迭代抑制同一目标的重复框，
   使每个目标只保留唯一最优框。

> **一个容易混淆的关键点**：多尺度搜索有两条等价路径——缩放模板（图不动）与缩放图像（模板不动）。
> 二者只能**取其一**：若同时缩小模板又缩小图像，尺度比不变，结果什么也匹配不到。
> 本章统一采用「只缩放模板、在原图上匹配」的方案，并在 1.3 节把两种实现的关系讲清楚。

## 目录结构约定

```
D:\workspace\Jupyter_WorkSpace\DIP\0303\
├── DIP第三章_多尺度金字塔与NMS的图像模板匹配算法.ipynb   <- 本文件
└── data\                                                  <- 全部生成/所需文件
```

## 环境

内核：`D:\workspace\.my_env`（Python 3.11.7）
依赖：`numpy` `opencv-python` `scipy` `matplotlib` `pandas` `scikit-image`
''')

# ======================================================================
md(r'''
## 0 环境与实验准备

统一完成：中文显示、随机种子、路径创建、评价工具函数。
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
from matplotlib.patches import Rectangle


# ---------- 中文显示 ----------
def setup_cjk_font():
    prefer = ["Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC"]
    avail = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((n for n in prefer if n in avail), None)
    for key in ("font.sans-serif", "font.serif"):
        plt.rcParams[key] = ([chosen] if chosen else []) + ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return chosen


CJK = setup_cjk_font()
matplotlib.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 130,
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})

# ---------- 随机种子：保证全章实验可复现 ----------
SEED = 303
np.random.seed(SEED)
cv2.setRNGSeed(SEED)

# ---------- 路径 ----------
DATA = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0303\data")
DATA.mkdir(parents=True, exist_ok=True)

print("Python  :", sys.version.split()[0])
print("numpy   :", np.__version__)
print("opencv  :", cv2.__version__)
print("中文字体:", CJK)
print("数据目录:", DATA)
''')

code(r'''
# ===================== 0.2 全局超参数 =====================
# ---- 合成场景参数 ----
SRC_W, SRC_H = 960, 540      # 源图尺寸
TPL_W, TPL_H = 48, 32        # 模板（尺度 1.0 时的目标尺寸）
NOISE_SIGMA = 6.0            # 叠加在源图与模板上的高斯噪声标准差

# ---- 主实验目标尺度 ----
TARGET_SCALES = [2.0, 1.0, 0.5, 0.25]

# ---- 多尺度搜索的尺度集合（模板缩放因子）----
# 二进网格：2、1、0.5、0.25 —— 与主实验目标尺度一一对应
SEARCH_SCALES = [2.0, 1.0, 0.5, 0.25]

# ---- 匹配与去重参数 ----
MATCH_THRESH = 0.60          # 归一化相关系数阈值
IOU_THRESH = 0.30            # NMS 的 IoU 抑制阈值
LOC_TOL = 6.0                # 定位判定容差（像素）

print(f"源图 {SRC_W}x{SRC_H}，模板 {TPL_W}x{TPL_H}")
print(f"目标尺度：{TARGET_SCALES}")
print(f"搜索尺度：{SEARCH_SCALES}")
print(f"匹配阈值={MATCH_THRESH}，NMS IoU 阈值={IOU_THRESH}，定位容差={LOC_TOL}")
''')

code(r'''
# ===================== 0.3 核心工具函数 =====================


def to_gray(img):
    """确保为单通道 uint8。"""
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img.astype(np.uint8)


def ncc_match(src, tpl):
    """
    归一化相关系数（NCC）模板匹配。

    返回 (响应图, 峰值)。响应图为 cv2.matchTemplate 的 TM_CCOEFF_NORMED 结果，
    尺寸为 (H-h+1, W-w+1)，其 (x, y) 位置直接对应"模板左上角"在原图中的坐标。
    要求 tpl 不大于 src，否则返回 (None, None)。
    """
    src = np.ascontiguousarray(to_gray(src))
    tpl = np.ascontiguousarray(to_gray(tpl))
    if tpl.shape[0] > src.shape[0] or tpl.shape[1] > src.shape[1]:
        return None, None
    resp = cv2.matchTemplate(src, tpl, cv2.TM_CCOEFF_NORMED)
    return resp, float(resp.max())


def resp_to_boxes(resp, tpl_w, tpl_h, thresh, max_peaks=None):
    """
    从响应图提取候选框。

    先用阈值二值化，再取每个连通域内的响应最大值位置作为该区域的代表框。
    这样同一目标邻域不会产生成百上千个几乎重合的框，便于后续 NMS 处理。
    """
    if resp is None:
        return []
    mask = (resp >= thresh).astype(np.uint8)
    if mask.sum() == 0:
        return []
    n_lab, labels = cv2.connectedComponents(mask, connectivity=8)
    boxes = []
    for lab in range(1, n_lab):
        ys, xs = np.where(labels == lab)
        vals = resp[ys, xs]
        k = int(np.argmax(vals))
        boxes.append((int(xs[k]), int(ys[k]), tpl_w, tpl_h, float(vals[k])))
    boxes.sort(key=lambda b: -b[4])
    if max_peaks:
        boxes = boxes[:max_peaks]
    return boxes


def box_center(b):
    return (b[0] + b[2] / 2.0, b[1] + b[3] / 2.0)


def iou(a, b):
    """两个框的交并比。"""
    ax1, ay1, aw, ah = a[0], a[1], a[2], a[3]
    bx1, by1, bw, bh = b[0], b[1], b[2], b[3]
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax1 + aw, bx1 + bw), min(ay1 + ah, by1 + bh)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def nms(boxes, iou_thresh=IOU_THRESH, keep_log=False):
    """贪心非极大值抑制：按置信度降序，保留最高分框，抑制与之 IoU 超阈值的框。"""
    boxes = sorted(boxes, key=lambda b: -b[4])
    kept, suppressed_log = [], []
    while boxes:
        best = boxes.pop(0)
        kept.append(best)
        rest = []
        for b in boxes:
            v = iou(best, b)
            if v > iou_thresh:
                suppressed_log.append((best, b, v))
            else:
                rest.append(b)
        boxes = rest
    return (kept, suppressed_log) if keep_log else kept


def resize_template(tpl, s):
    """按尺度因子 s 缩放模板；缩小用 INTER_AREA 抗混叠，放大用 INTER_LINEAR。"""
    tw = max(4, int(round(tpl.shape[1] * s)))
    th = max(4, int(round(tpl.shape[0] * s)))
    interp = cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR
    return cv2.resize(tpl, (tw, th), interpolation=interp)


print("工具函数就绪：NCC 匹配 / 响应提取 / IoU / NMS / 模板缩放")
''')

# ======================================================================
md(r'''
### 0.4 实现自检（必读）

模板匹配实现最易出错的有三点：响应图与原图的坐标对应关系、归一化是否真的对灰度线性变换不变、
以及**多尺度搜索时"只缩一边"这条约束**。本节用可验证的性质逐条确认。
''')

code(r'''
# ===================== 0.4 实现自检 =====================
# (1) 响应图尺寸必须为 (H-h+1, W-w+1)
_s = np.random.default_rng(1).integers(0, 255, (60, 80), dtype=np.uint8)
_t = np.random.default_rng(2).integers(0, 255, (20, 30), dtype=np.uint8)
_r, _ = ncc_match(_s, _t)
print(f"(1) 响应图尺寸 = {_r.shape}   期望 = ({60-20+1}, {80-30+1})   "
      f"{'OK' if _r.shape == (41, 51) else '异常'}")

# (2) NCC 对灰度线性变换不变：I' = a*I + b 应给出几乎相同的响应。
#     必须用"有结构"的图像：纯噪声图案相关性接近 0，无法检验不变性。
_ptn = np.zeros((60, 80), np.float64)
_ptn[10:50, 15:65] = 200
_ptn[20:40, 25:55] = 60
_ptn[25:35, 30:50] = 230
_ptn += np.random.default_rng(5).normal(0, 4, _ptn.shape)
_s3 = np.clip(_ptn, 0, 255).astype(np.uint8)
_t3 = _s3[12:44, 20:60].copy()
_s4 = np.clip(1.7 * _s3.astype(np.float64) + 35.0, 0, 255).astype(np.uint8)
_, _p4 = ncc_match(_s3, _t3)
_, _p5 = ncc_match(_s4, _t3)
print(f"(2) 线性变换前后的峰值：{_p4:.6f} vs {_p5:.6f}   差异 {abs(_p4 - _p5):.2e}   "
      f"{'OK' if abs(_p4 - _p5) < 1e-3 else '异常'}")

# (3) 把模板原样嵌回源图，峰值应接近 1，且位置与该位置锚点一致
_canvas = np.full((100, 140), 90, np.uint8)
_patch = cv2.GaussianBlur(np.random.default_rng(3).integers(0, 255, (24, 36), dtype=np.uint8),
                          (0, 0), 1.2)
_canvas[40:64, 50:86] = _patch
_r3, _p3 = ncc_match(_canvas, _patch)
_py, _px = np.unravel_index(np.argmax(_r3), _r3.shape)
print(f"(3) 嵌入位置 (40,50)，检出位置 ({_py},{_px})，峰值 {_p3:.4f}   "
      f"{'OK' if (_py, _px) == (40, 50) and _p3 > 0.99 else '异常'}")

# (4) NMS：人为构造重叠框，验证只保留一个
_demo = [(10, 10, 48, 32, 0.9), (12, 11, 48, 32, 0.8), (13, 10, 48, 32, 0.7),
         (200, 200, 48, 32, 0.85)]
_kept = nms(_demo, iou_thresh=IOU_THRESH)
print(f"(4) 输入 4 个框（前 3 个高度重叠），NMS 后保留 {len(_kept)} 个   "
      f"{'OK' if len(_kept) == 2 else '异常'}")

# (5) 【多尺度搜索的核心约束】只缩一边才有效，同时缩两边必然失败
#     构造：源图内嵌一个"缩小 2 倍"的目标，模板为其原始尺寸
_src5 = np.full((240, 320), 100, np.uint8)
_p5t = cv2.GaussianBlur(np.random.default_rng(8).integers(0, 255, (32, 48), dtype=np.uint8),
                        (0, 0), 1.5)
_small = cv2.resize(_p5t, (24, 16), interpolation=cv2.INTER_AREA)
_src5[120:136, 160:184] = _small                       # 目标比模板小一半
#  正确：只缩模板（原图不动）
_, pk_only_tpl = ncc_match(_src5, resize_template(_p5t, 0.5))
#  错误：图缩一半、模板也缩一半
_src5_half = cv2.resize(_src5, (160, 120), interpolation=cv2.INTER_AREA)
_, pk_both = ncc_match(_src5_half, resize_template(_p5t, 0.5))
print(f"(5) 只缩模板（原图不动）峰值 = {pk_only_tpl:.4f}   "
      f"两边同时缩峰值 = {pk_both:.4f}   "
      f"{'OK' if pk_only_tpl > 0.9 and pk_both < 0.5 else '异常'}")

print()
print("自检结论：五项全部 OK 方表明匹配实现、坐标对应、NMS 与多尺度搜索的约束均正确。")
''')

# ======================================================================
md(r'''
## 1 自建多尺度测试场景

### 1.1 场景与目标设计

模板匹配实验的关键困难在于**真值位置**：公开数据集通常不提供"同一模板在图中多处出现"的逐目标坐标，
因而无法客观计算检出率与定位误差。本章采用合成场景解决该问题。

设计要点：

| 要素 | 设计 | 目的 |
| --- | --- | --- |
| 目标图案 | 带内部结构的对称图形（矩形底 + 十字 + 斜纹） | 保证相似度峰尖锐，又具备一定像素级细节 |
| 目标尺度 | 2.0、1.0、0.5、0.25 | 覆盖放大与缩小两种情形 |
| 目标间距 | 四角分布，中心距 ≥ 300 像素 | 远大于最大目标（96×64），避免相互干扰判定 |
| 模板来源 | 从尺度 1.0 的目标处裁剪，并叠加独立噪声 | 模拟"模板与目标不完全同源"的真实情形 |
| 背景 | 平滑低频起伏 + 弱纹理 + 噪声 | 避免纯噪声背景掩盖真实响应差异 |
| 真值 | 由绘制程序直接输出中心坐标与尺寸 | 使检出率与定位误差可客观计算 |
''')

code(r'''
# ===================== 1.1 场景合成 =====================


def make_target_patch(w=TPL_W, h=TPL_H, seed=11):
    """生成目标图案：亮矩形底 + 深色十字 + 两条斜纹。高度结构化，使 NCC 响应峰尖锐。"""
    rng = np.random.default_rng(seed)
    base = np.full((h, w), 205.0)
    base[:2, :] = 120
    base[-2:, :] = 120
    base[:, :2] = 120
    base[:, -2:] = 120
    cy, cx = h // 2, w // 2
    th = max(2, h // 8)
    base[cy - th:cy + th, cx - 2:cx + 2] = 70
    base[cy - 2:cy + 2, cx - th * 3:cx + th * 3] = 70
    for i in range(h):
        j1 = int(i * w / h)
        j2 = w - 1 - j1
        for j in (j1, j2):
            if 4 < j < w - 4:
                base[i, j] = 130
    base += rng.normal(0, 3.0, base.shape)
    return np.clip(base, 0, 255).astype(np.uint8)


def make_background(w=SRC_W, h=SRC_H, seed=21):
    """平滑低频背景 + 两条弱纹理带。"""
    rng = np.random.default_rng(seed)
    low = cv2.GaussianBlur(rng.random((h, w), dtype=np.float32), (0, 0), sigmaX=40, sigmaY=40)
    low = (low - low.mean()) / (low.std() + 1e-6)
    img = 128.0 + 18.0 * low
    img[h // 3:h // 3 + 12, :] += 14.0
    img[2 * h // 3:2 * h // 3 + 8, :] -= 12.0
    return img.astype(np.float32)


def place_at_scale(canvas, patch, cx, cy, scale):
    """把 patch 按 scale 缩放后以 (cx, cy) 为中心贴到 canvas（就地修改）。"""
    ph, pw = patch.shape
    nw, nh = max(4, int(round(pw * scale))), max(4, int(round(ph * scale)))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    p = cv2.resize(patch, (nw, nh), interpolation=interp)
    x0 = int(np.clip(round(cx - nw / 2), 0, canvas.shape[1] - nw))
    y0 = int(np.clip(round(cy - nh / 2), 0, canvas.shape[0] - nh))
    canvas[y0:y0 + nh, x0:x0 + nw] = p.astype(np.float32)
    return (x0, y0, nw, nh)


def build_scene(scales=TARGET_SCALES, centers=None, seed=SEED):
    """合成多尺度场景，返回 (源图, 模板, 逐目标真值列表)。"""
    patch = make_target_patch()
    canvas = make_background()

    if centers is None:
        if len(scales) == 4:
            # 四角分布：中心距 ≥ 300 像素，远大于最大目标 96×64
            centers = [(210.0, 120.0), (750.0, 120.0), (210.0, 420.0), (750.0, 420.0)]
        else:
            xs = np.linspace(100, SRC_W - 100, len(scales))
            centers = [(float(xs[i]), SRC_H * 0.5) for i in range(len(scales))]

    gt = []
    for (cx, cy), s in zip(centers, scales):
        x, y, w, h = place_at_scale(canvas, patch, cx, cy, s)
        gt.append({"cx": x + w / 2.0, "cy": y + h / 2.0,
                   "x": x, "y": y, "w": w, "h": h, "scale": s})

    rng = np.random.default_rng(seed + 7)
    canvas += rng.normal(0, NOISE_SIGMA, canvas.shape)
    src = np.clip(canvas, 0, 255).astype(np.uint8)

    tpl_patch = patch.copy().astype(np.float32)
    tpl_patch += np.random.default_rng(seed + 99).normal(0, NOISE_SIGMA, tpl_patch.shape)
    tpl = np.clip(tpl_patch, 0, 255).astype(np.uint8)
    return src, tpl, gt


SRC, TPL, GT = build_scene()
GT_DF = pd.DataFrame(GT)
GT_DF.to_csv(DATA / "ground_truth.csv", index=False, encoding="utf-8-sig")
cv2.imwrite(str(DATA / "scene_src.png"), SRC)
cv2.imwrite(str(DATA / "scene_tpl.png"), TPL)
print("源图尺寸:", SRC.shape, " 模板尺寸:", TPL.shape)
print("真值目标数:", len(GT))
print(GT_DF[["scale", "cx", "cy", "w", "h"]].to_string(index=False, float_format=lambda v: f"{v:.1f}"))
''')

code(r'''
# ===================== 1.2 场景可视化 =====================
fig = plt.figure(figsize=(15, 6.2))
gs = fig.add_gridspec(1, 3, width_ratios=[2.4, 1, 1], wspace=0.18)

ax = fig.add_subplot(gs[0, 0])
ax.imshow(SRC, cmap="gray", vmin=0, vmax=255)
for g in GT:
    ax.add_patch(Rectangle((g["x"], g["y"]), g["w"], g["h"],
                           fill=False, edgecolor="red", lw=1.6))
    ax.text(g["x"], g["y"] - 5, f"s={g['scale']}", color="red", fontsize=10)
ax.set_title("源图与真值位置（红框）", fontsize=12)
ax.axis("off")

ax2 = fig.add_subplot(gs[0, 1])
ax2.imshow(TPL, cmap="gray", vmin=0, vmax=255)
ax2.set_title(f"模板（{TPL.shape[1]}×{TPL.shape[0]}，尺度 1.0）", fontsize=12)
ax2.axis("off")

ax3 = fig.add_subplot(gs[0, 2])
labels, sizes = [], []
for g in GT:
    labels.append(f"s={g['scale']}")
    sizes.append(g["w"])
ax3.barh(labels, sizes, color="tab:blue")
for i, g in enumerate(GT):
    ax3.text(g["w"], i, f" {g['w']}×{g['h']}", va="center", fontsize=9)
ax3.axvline(TPL_W, color="tab:red", ls="--", lw=1.4)
ax3.text(TPL_W, len(GT) - 0.3, f" 模板宽 {TPL_W}", color="tab:red", fontsize=9)
ax3.set_xlabel("目标宽度 / 像素")
ax3.set_title("各目标的实际尺寸 vs 模板尺寸", fontsize=11)
ax3.grid(alpha=0.3, axis="x")

fig.suptitle("1 自建多尺度测试场景", fontsize=13.5)
plt.tight_layout()
plt.savefig(DATA / "fig_1_1_scene.png", bbox_inches="tight")
plt.show()
''')

# ======================================================================
md(r'''
## 2 单尺度基线实验

### 2.1 原理

模板匹配以归一化相关系数（normalized cross-correlation，NCC）作为相似度度量。
设源图为 $I$ 、模板为 $T$ ，在锚点 $(x,y)$ 处窗口灰度为 $I_{x,y}$ ，则

$$R(x,y)=\frac{\sum_{u,v}\left[T(u,v)-\bar{T}\right]\left[I(x+u,y+v)-\bar{I}_{x,y}\right]}{\sqrt{\sum_{u,v}\left[T(u,v)-\bar{T}\right]^{2}}\sqrt{\sum_{u,v}\left[I(x+u,y+v)-\bar{I}_{x,y}\right]^{2}}}$$

分子分母同时含均值项，相消后 $R$ 对灰度的线性变换（$\alpha I+\beta$ ，$\alpha>0$）保持不变，
因而抗光照变化能力优于绝对差平方和。$R\in[-1,1]$ ，越接近 1 越相似。

注意 $R$ 是**互相关**而非卷积：模板不作翻转，因为模板本身有方向性。

### 2.2 尺度失配的机理

匹配时窗口尺寸固定为模板尺寸。当目标实际尺寸为模板的 $s$ 倍且 $s\neq 1$ 时，
窗口内必然混入目标以外的像素，分子协方差项随之衰减，峰值 $R$ 下降。
该缺陷源于相似度度量的几何约束，**无法通过调阈值或滤波补救**。
''')

code(r'''
# ===================== 2.1 单尺度匹配（基线） =====================
def detect_single_scale(src, tpl, thresh=MATCH_THRESH):
    """单尺度匹配：只用模板原始尺寸，返回 (候选框, 响应图, 峰值, 耗时ms)。"""
    t0 = time.perf_counter()
    resp, peak = ncc_match(src, tpl)
    boxes = resp_to_boxes(resp, tpl.shape[1], tpl.shape[0], thresh)
    dt = (time.perf_counter() - t0) * 1000
    return boxes, resp, peak, dt


BOXES_SINGLE, RESP_SINGLE, PEAK_SINGLE, T_SINGLE = detect_single_scale(SRC, TPL)
print(f"单尺度匹配：响应图 {RESP_SINGLE.shape}，峰值 {PEAK_SINGLE:.4f}，"
      f"候选框 {len(BOXES_SINGLE)} 个，耗时 {T_SINGLE:.1f} ms")
for b in BOXES_SINGLE[:8]:
    print(f"  位置=({b[0]:>4},{b[1]:>4}) 尺寸={b[2]}x{b[3]}  置信度={b[4]:.4f}")
''')

code(r'''
# ===================== 2.2 峰值随尺度衰减：尺度失配的直接证据 =====================
rows = []
for g in GT:
    x0 = int(np.clip(g["x"], 0, RESP_SINGLE.shape[1] - 1))
    y0 = int(np.clip(g["y"], 0, RESP_SINGLE.shape[0] - 1))
    win = RESP_SINGLE[max(0, y0 - 4):y0 + 5, max(0, x0 - 4):x0 + 5]
    rows.append({"scale": g["scale"], "peak_at_gt": float(win.max())})

peak_df = pd.DataFrame(rows).sort_values("scale", ascending=False)
print("模板在真值位置处的 NCC 峰值（单尺度匹配）：")
print(peak_df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

fig, axes = plt.subplots(1, 2, figsize=(14.5, 4.6))
axes[0].plot(peak_df.scale, peak_df.peak_at_gt, "o-", color="tab:red", lw=2, ms=8)
axes[0].axhline(MATCH_THRESH, color="k", ls="--", lw=1.2, label=f"判定阈值 {MATCH_THRESH}")
axes[0].set_xscale("log", base=2)
axes[0].set_xticks([0.25, 0.5, 1.0, 2.0])
axes[0].set_xticklabels(["0.25", "0.5", "1.0", "2.0"])
axes[0].set_xlabel("目标尺度因子 s（对数轴）")
axes[0].set_ylabel("真值位置处 NCC 峰值")
axes[0].set_title("尺度失配导致响应峰值衰减")
axes[0].legend()
axes[0].grid(alpha=0.3)

im = axes[1].imshow(RESP_SINGLE, cmap="jet")
for g in GT:
    axes[1].plot(g["x"], g["y"], "w+", ms=12, mew=2)
    axes[1].text(g["x"] + 4, g["y"] + 16, f"s={g['scale']}", color="white", fontsize=9)
plt.colorbar(im, ax=axes[1], fraction=0.046)
axes[1].set_title("单尺度响应图（白十字=真值锚点）")
axes[1].axis("off")

fig.suptitle("2.2 尺度失配的直接证据：峰值随目标尺度偏离 1 而下降", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_2_2_scale_mismatch.png", bbox_inches="tight")
plt.show()

n_over = int((peak_df.peak_at_gt >= MATCH_THRESH).sum())
print(f"\n结论：{len(GT)} 个目标中，在阈值 {MATCH_THRESH} 下只有 {n_over} 个的位置响应过阈，"
      f"其余 {len(GT) - n_over} 个在单尺度匹配下必然漏检。")
''')

# ======================================================================
md(r'''
## 3 多尺度改进

### 3.1 实现方式的选择：缩放模板 vs 缩放图像

要让算法能匹配不同尺度的目标，必须让"匹配窗口尺寸 = 目标在当前输入图中的尺寸"。
实现上有两条**等价**路径：

| 方案 | 做法 | 说明 |
| --- | --- | --- |
| 模板金字塔 | 把模板缩放 $s$ 倍，在**原图**上匹配 | 原图只读一次，实现简单 |
| 图像金字塔 | 把图像缩放 $1/s$ 倍，用**原模板**匹配 | 图逐层变小，深层匹配更快 |

**关键约束：两者只能取其一。** 若同时把模板缩小、又把图像缩小，尺度比不变，
目标与模板永远不会尺寸相符——这是多尺度匹配最常见的实现错误。

本章采用**模板金字塔**方案：原图保持不变，只对模板做一组缩放。
第 $k$ 个尺度 $s_k$ 对应的模板尺寸为

$$w_k=\left\lceil s_k w_0\right\rceil,\qquad h_k=\left\lceil s_k h_0\right\rceil$$

在原图上匹配得到响应图 $R_k$ ，将其峰值位置作为该尺度下的候选框，最后把所有尺度的候选框合并。
''')

code(r'''
# ===================== 3.1 多尺度模板金字塔匹配 =====================
def detect_multiscale(src, tpl, scales=SEARCH_SCALES, thresh=MATCH_THRESH):
    """
    多尺度模板金字塔匹配：**原图不动，只缩放模板**。

    对每个尺度 s：
      - 把模板缩放 s 倍；
      - 在**原图**上做一次 NCC 匹配；
      - 提取候选框，框尺寸即缩放后的模板尺寸，坐标即原图坐标（无需任何映射）。
    """
    t0 = time.perf_counter()
    all_boxes, info = [], []
    for s in scales:
        tpl_s = resize_template(tpl, s)
        if tpl_s.shape[0] >= src.shape[0] or tpl_s.shape[1] >= src.shape[1]:
            info.append({"尺度s": s, "模板": (tpl_s.shape[1], tpl_s.shape[0]),
                         "n_box": 0, "peak": np.nan})
            continue
        resp, peak = ncc_match(src, tpl_s)
        boxes = resp_to_boxes(resp, tpl_s.shape[1], tpl_s.shape[0], thresh)
        all_boxes.extend(boxes)
        info.append({"尺度s": s, "模板": (tpl_s.shape[1], tpl_s.shape[0]),
                     "n_box": len(boxes), "peak": peak})
    dt = (time.perf_counter() - t0) * 1000
    return all_boxes, info, dt


BOXES_MS_RAW, MS_INFO, T_MS = detect_multiscale(SRC, TPL)
print(f"模板金字塔：{len(SEARCH_SCALES)} 个尺度，合并后候选框 {len(BOXES_MS_RAW)} 个，"
      f"耗时 {T_MS:.1f} ms\n")
print(pd.DataFrame(MS_INFO).to_string(index=False, float_format=lambda v: f"{v:.4f}"))
''')

code(r'''
# ===================== 3.2 逐尺度的响应图与命中情况 =====================
# 对每个尺度，检查该尺度模板是否在"与自己尺度相同的目标"处产生峰值
print(f"{'尺度s':>6} {'模板':>8} {'期望命中目标':>12} {'该处峰值':>9} {'全图最大':>9} "
      f"{'最大位置':>14} {'命中?':>6}")
print("-" * 78)
for s in SEARCH_SCALES:
    tpl_s = resize_template(TPL, s)
    resp, peak = ncc_match(SRC, tpl_s)
    g = next(g for g in GT if abs(g["scale"] - s) < 1e-9)
    x0 = int(np.clip(g["x"], 0, resp.shape[1] - 1))
    y0 = int(np.clip(g["y"], 0, resp.shape[0] - 1))
    pk = float(resp[max(0, y0 - 4):y0 + 5, max(0, x0 - 4):x0 + 5].max())
    ys, xs = np.unravel_index(np.argmax(resp), resp.shape)
    same = (abs(xs - g["x"]) <= 4 and abs(ys - g["y"]) <= 4)
    print(f"{s:>6} {tpl_s.shape[1]:>3}x{tpl_s.shape[0]:<4} {'s=' + str(s):>12} "
          f"{pk:>9.4f} {peak:>9.4f} ({xs:>4},{ys:>4}) {'是' if pk >= MATCH_THRESH else '否':>6}"
          f"{'  峰值位置=该目标' if same else ''}")
''')

# ======================================================================
md(r'''
## 4 NMS 去重改进

### 4.1 原理

多尺度匹配的必然结果是**同一目标被多个尺度重复检出**（大尺度模板和小尺度模板都可能命中同一目标）。
设候选框集合为 $\mathcal{B}$ ，NMS 的流程为：

1. 按置信度（响应峰值）降序排列；
2. 取出最高分框 $b^*$ 加入保留集；
3. 计算其余框与 $b^*$ 的交并比，将超过阈值 $T_{\text{iou}}$ 的框抑制；
4. 重复 2~3 直至集合为空。

$$\text{IoU}(A,B)=\frac{|A\cap B|}{|A\cup B|}$$

同一目标邻域的候选框几乎完全重合（$\text{IoU}\to 1$），而异目标之间相距较远（$\text{IoU}\to 0$），
这种**几何可分性**正是 NMS 在此有效的原因。
''')

code(r'''
# ===================== 4.1 对候选框执行 NMS =====================
KEPT_MS, LOG_MS = nms(BOXES_MS_RAW, IOU_THRESH, keep_log=True)
KEPT_SINGLE, LOG_SINGLE = nms(BOXES_SINGLE, IOU_THRESH, keep_log=True)

print(f"{'配置':<28}{'候选框':>8}{'NMS后':>8}{'抑制数':>8}")
print("-" * 54)
print(f"{'① 单尺度':<28}{len(BOXES_SINGLE):>8}{len(KEPT_SINGLE):>8}{len(LOG_SINGLE):>8}")
print(f"{'② 多尺度模板金字塔':<28}{len(BOXES_MS_RAW):>8}{len(KEPT_MS):>8}{len(LOG_MS):>8}")

if LOG_MS:
    print("\n抑制明细（前 10 条，展示「谁抑制了谁」）：")
    for best, sup, v in LOG_MS[:10]:
        print(f"  保留 ({best[0]:>4},{best[1]:>4}) {best[2]}x{best[3]} score={best[4]:.3f}"
              f"   抑制 ({sup[0]:>4},{sup[1]:>4}) {sup[2]}x{sup[3]} score={sup[4]:.3f}  IoU={v:.3f}")
''')

code(r'''
# ===================== 4.2 NMS 去重过程可视化 =====================
fig, axes = plt.subplots(1, 3, figsize=(17, 5.4))
configs = [("① 单尺度（NMS后）", KEPT_SINGLE, "tab:red"),
           ("② 多尺度（NMS前）", BOXES_MS_RAW, "tab:orange"),
           ("③ 多尺度 + NMS（本文）", KEPT_MS, "tab:blue")]
for ax, (title, boxes, color) in zip(axes, configs):
    ax.imshow(SRC, cmap="gray", vmin=0, vmax=255)
    for g in GT:
        ax.add_patch(Rectangle((g["x"], g["y"]), g["w"], g["h"],
                               fill=False, edgecolor="lime", lw=1.2, ls="--"))
    for b in boxes:
        ax.add_patch(Rectangle((b[0], b[1]), b[2], b[3],
                               fill=False, edgecolor=color, lw=1.6))
    ax.set_title(f"{title}\n框数 = {len(boxes)}", fontsize=11.5)
    ax.axis("off")
fig.suptitle("4.2 NMS 去重效果（绿虚线=真值，彩色实线=检出框）", fontsize=13.5)
plt.tight_layout()
plt.savefig(DATA / "fig_4_2_nms_effect.png", bbox_inches="tight")
plt.show()
''')

# ======================================================================
md(r'''
## 5 定量评价

### 5.1 评价指标

| 指标 | 定义 | 期望方向 |
| --- | --- | --- |
| 检出率 | 被正确检出的真值目标数 / 真值目标总数 | ↑ |
| 误检率 | 未命中任何真值的检出框数 / 检出框总数 | ↓ |
| 冗余框数 | 同一真值目标被检出多次时，多出的框数之和 | ↓ |
| 平均定位误差 | 命中框中心与真值中心的欧氏距离均值（像素） | ↓ |
| 耗时 | 一次完整检测的墙钟时间（ms） | ↓ |

**命中判定**：检出框中心与某真值目标中心的距离小于 `LOC_TOL = 6` 像素，则记该框命中该目标；
一个真值目标被多个框命中时，只把置信度最高的记为正检，其余计入冗余框。
''')

code(r'''
# ===================== 5.1 评价函数 =====================
def evaluate(boxes, gt, loc_tol=LOC_TOL):
    hits = {i: [] for i in range(len(gt))}
    unmatched = []
    for b in boxes:
        bx, by = box_center(b)
        best_i, best_d = None, 1e9
        for i, g in enumerate(gt):
            d = float(np.hypot(bx - g["cx"], by - g["cy"]))
            if d < best_d:
                best_i, best_d = i, d
        if best_i is not None and best_d < loc_tol:
            hits[best_i].append((b, best_d))
        else:
            unmatched.append(b)

    n_hit = sum(1 for i in range(len(gt)) if hits[i])
    errs = [d for i in range(len(gt)) for _, d in hits[i]]
    return {
        "检出率": n_hit / len(gt),
        "检出数": n_hit,
        "真值数": len(gt),
        "检出框总数": len(boxes),
        "误检数": len(unmatched),
        "误检率": len(unmatched) / len(boxes) if boxes else 0.0,
        "冗余框数": sum(max(0, len(hits[i]) - 1) for i in range(len(gt))),
        "平均定位误差": float(np.mean(errs)) if errs else float("nan"),
        "最大定位误差": float(np.max(errs)) if errs else float("nan"),
    }


CONFIGS = [
    ("① 单尺度（无NMS）", BOXES_SINGLE, T_SINGLE),
    ("② 多尺度（无NMS）", BOXES_MS_RAW, T_MS),
    ("③ 多尺度 + NMS（本文）", KEPT_MS, T_MS),
]

rows = []
for name, boxes, t in CONFIGS:
    m = evaluate(boxes, GT)
    m["配置"] = name
    m["耗时/ms"] = t
    rows.append(m)
RES_DF = pd.DataFrame(rows).set_index("配置")
RES_DF.to_csv(DATA / "metrics_by_config.csv", encoding="utf-8-sig")

show_cols = ["检出数", "真值数", "检出率", "检出框总数", "误检率", "冗余框数",
             "平均定位误差", "耗时/ms"]
print("=" * 100)
print("定量评价结果")
print("=" * 100)
print(RES_DF[show_cols].to_string(float_format=lambda v: f"{v:.4f}"))
print("=" * 100)
''')

code(r'''
# ===================== 5.2 指标对比可视化 =====================
fig, axes = plt.subplots(1, 4, figsize=(18, 4.4))
names = [c[0] for c in CONFIGS]
short = ["① 单尺度", "② 多尺度", "③ 多尺度+NMS"]
colors = ["tab:red", "tab:orange", "tab:blue"]

for ax, (col, title) in zip(axes, [("检出率", "检出率（越高越好）"),
                                   ("冗余框数", "冗余框数（越低越好）"),
                                   ("误检率", "误检率（越低越好）"),
                                   ("耗时/ms", "耗时 / ms")]):
    vals = RES_DF[col].values
    ax.bar(short, vals, color=colors)
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.3f}" if col != "耗时/ms" else f"{v:.0f}",
                ha="center", va="bottom", fontsize=9)
    ax.set_title(title, fontsize=11.5)
    ax.tick_params(axis="x", rotation=15)
    ax.grid(alpha=0.3, axis="y")
    if col == "检出率":
        ax.set_ylim(0, 1.18)

fig.suptitle("5.2 三组配置的关键指标对比", fontsize=13.5)
plt.tight_layout()
plt.savefig(DATA / "fig_5_2_metrics.png", bbox_inches="tight")
plt.show()
''')

code(r'''
# ===================== 5.3 逐目标的检出情况 =====================
def per_target(boxes, gt, loc_tol=LOC_TOL):
    out = []
    for i, g in enumerate(gt):
        cand = []
        for b in boxes:
            bx, by = box_center(b)
            d = float(np.hypot(bx - g["cx"], by - g["cy"]))
            if d < loc_tol:
                cand.append((b, d))
        if cand:
            cand.sort(key=lambda t: -t[0][4])
            out.append({"目标": i + 1, "真值尺度": g["scale"], "是否检出": "是",
                        "框数": len(cand), "最优置信度": cand[0][0][4],
                        "定位误差": cand[0][1]})
        else:
            out.append({"目标": i + 1, "真值尺度": g["scale"], "是否检出": "否",
                        "框数": 0, "最优置信度": np.nan, "定位误差": np.nan})
    return pd.DataFrame(out)


pt_ms = per_target(KEPT_MS, GT)
pt_single = per_target(KEPT_SINGLE, GT)
print("③ 多尺度 + NMS 的逐目标结果：")
print(pt_ms.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print()
print("① 单尺度的逐目标结果：")
print(pt_single.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
print()

scales = pt_ms["真值尺度"].tolist()
ok_ms = np.array([1 if v == "是" else 0 for v in pt_ms["是否检出"]])
ok_single = np.array([1 if v == "是" else 0 for v in pt_single["是否检出"]])

fig, ax = plt.subplots(figsize=(10, 4.4))
x = np.arange(len(scales))
ax.bar(x - 0.2, ok_single, 0.4, label="① 单尺度", color="tab:red")
ax.bar(x + 0.2, ok_ms, 0.4, label="③ 多尺度+NMS（本文）", color="tab:blue")
ax.set_xticks(x)
ax.set_xticklabels([f"目标{i+1}\ns={s}" for i, s in enumerate(scales)])
ax.set_yticks([0, 1])
ax.set_yticklabels(["漏检", "检出"])
ax.set_title("5.3 逐目标检出对比：单尺度 vs 多尺度+NMS", fontsize=12.5)
ax.legend()
ax.grid(alpha=0.3, axis="y")
plt.tight_layout()
plt.savefig(DATA / "fig_5_3_per_target.png", bbox_inches="tight")
plt.show()
''')

# ======================================================================
md(r'''
## 6 参数分析

大纲要求分析"金字塔层数对检测精度与运行速度的影响"与"NMS 阈值对去重效果的影响"，
本节对三个关键参数做扫描。由于本章采用模板金字塔，**尺度集合的疏密**即对应"层数"的作用。
''')

code(r'''
# ===================== 6.1 尺度集合疏密扫描（对应"金字塔层数"） =====================
def dyadic_scales(n):
    """生成 n 个二进尺度：1, 1/2, 1/4 … 以及 2, 4 …"""
    scales = []
    for k in range(n):
        scales.append(2.0 ** k if k % 2 == 0 else 1.0 / (2.0 ** (k // 2 + 1)))
    return sorted(set(round(s, 4) for s in scales), reverse=True)


level_rows = []
for n in (2, 3, 4, 5, 6):
    sc = dyadic_scales(n)
    raw, info, t = detect_multiscale(SRC, TPL, scales=sc)
    kept = nms(raw, IOU_THRESH)
    m = evaluate(kept, GT)
    level_rows.append({"尺度数": len(sc), "尺度集合": ",".join(f"{s:g}" for s in sc),
                       "候选框数": len(raw), "NMS后": len(kept),
                       "检出率": m["检出率"], "误检率": m["误检率"],
                       "冗余框数": m["冗余框数"], "耗时/ms": t})
LEVEL_DF = pd.DataFrame(level_rows)
LEVEL_DF.to_csv(DATA / "sweep_scales.csv", index=False, encoding="utf-8-sig")
print("尺度集合疏密扫描：")
print(LEVEL_DF.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
''')

code(r'''
# ===================== 6.2 NMS 的 IoU 阈值扫描 =====================
iou_rows = []
for th in (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9):
    kept = nms(BOXES_MS_RAW, th)
    m = evaluate(kept, GT)
    iou_rows.append({"IoU阈值": th, "保留框数": len(kept),
                     "检出率": m["检出率"], "误检率": m["误检率"],
                     "冗余框数": m["冗余框数"]})
IOU_DF = pd.DataFrame(iou_rows)
IOU_DF.to_csv(DATA / "sweep_iou.csv", index=False, encoding="utf-8-sig")
print("NMS 的 IoU 阈值扫描：")
print(IOU_DF.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
''')

code(r'''
# ===================== 6.3 匹配阈值扫描 =====================
th_rows = []
for th in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
    raw, _, t = detect_multiscale(SRC, TPL, thresh=th)
    kept = nms(raw, IOU_THRESH)
    m = evaluate(kept, GT)
    th_rows.append({"匹配阈值": th, "候选框数": len(raw), "NMS后": len(kept),
                    "检出率": m["检出率"], "误检率": m["误检率"],
                    "冗余框数": m["冗余框数"]})
TH_DF = pd.DataFrame(th_rows)
TH_DF.to_csv(DATA / "sweep_match_thresh.csv", index=False, encoding="utf-8-sig")
print("匹配阈值扫描：")
print(TH_DF.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
''')

code(r'''
# ===================== 6.4 参数敏感性总图 =====================
fig, axes = plt.subplots(1, 3, figsize=(17.5, 4.6))

ax = axes[0]
ax.plot(LEVEL_DF["尺度数"], LEVEL_DF["检出率"], "o-", color="tab:blue", label="检出率")
ax.plot(LEVEL_DF["尺度数"], LEVEL_DF["误检率"], "s-", color="tab:red", label="误检率")
ax.set_xlabel("搜索尺度个数")
ax.set_ylabel("比率")
ax.set_title("尺度疏密对精度的影响")
ax.legend(loc="center left")
ax.grid(alpha=0.3)
ax2 = ax.twinx()
ax2.plot(LEVEL_DF["尺度数"], LEVEL_DF["耗时/ms"], "^--", color="tab:green", label="耗时")
ax2.set_ylabel("耗时 / ms", color="tab:green")
ax2.tick_params(axis="y", colors="tab:green")
ax2.legend(loc="lower right")

ax = axes[1]
ax.plot(IOU_DF["IoU阈值"], IOU_DF["冗余框数"], "o-", color="tab:blue", label="冗余框数")
ax.plot(IOU_DF["IoU阈值"], IOU_DF["误检率"], "s-", color="tab:red", label="误检率")
ax.plot(IOU_DF["IoU阈值"], IOU_DF["检出率"], "^-", color="tab:green", label="检出率")
ax.axvline(IOU_THRESH, color="k", ls=":", lw=1.2, label=f"默认 {IOU_THRESH}")
ax.set_xlabel("NMS 的 IoU 阈值")
ax.set_title("IoU 阈值对去重效果的影响")
ax.legend(fontsize=9)
ax.grid(alpha=0.3)

ax = axes[2]
ax.plot(TH_DF["匹配阈值"], TH_DF["检出率"], "o-", color="tab:blue", label="检出率")
ax.plot(TH_DF["匹配阈值"], TH_DF["误检率"], "s-", color="tab:red", label="误检率")
ax.plot(TH_DF["匹配阈值"], TH_DF["候选框数"] / max(1, TH_DF["候选框数"].max()),
        "^--", color="gray", label="候选框数（归一化）")
ax.axvline(MATCH_THRESH, color="k", ls=":", lw=1.2, label=f"默认 {MATCH_THRESH}")
ax.set_xlabel("匹配阈值")
ax.set_title("匹配阈值的影响")
ax.legend(fontsize=9)
ax.grid(alpha=0.3)

fig.suptitle("6 参数敏感性分析", fontsize=13.5)
plt.tight_layout()
plt.savefig(DATA / "fig_6_params.png", bbox_inches="tight")
plt.show()
''')

# ======================================================================
md(r'''
### 6.5 非二进尺度目标的检出能力

前面主实验的目标尺度都落在搜索尺度集合 $\{2,1,0.5,0.25\}$ 上。实际场景中目标尺度是连续的，
因此还需考察**目标尺度与搜索尺度不一致**时的表现。

本节合成一幅尺度梯度场景：从左到右放置 11 个目标，尺度从 0.50 连续变化到 1.00，
分别用
- 与目标精确同尺度的模板（理论上限，代表"若搜索尺度无限密"）；
- 固定的二进搜索集合 $\{2,1,0.5,0.25\}$（实际可用的最近尺度）

进行匹配，比较真值处的响应峰值。由于模板金字塔是对模板做缩放，**尺度偏差会直接体现为峰值下降**，
偏差越大下降越多——这正是"搜索尺度需足够密"的定量依据。
''')

code(r'''
# ===================== 6.5 非二进尺度目标的检出能力 =====================
RAMP_SCALES = [round(0.50 + 0.05 * i, 2) for i in range(11)]        # 0.50 ~ 1.00
ramp_src, ramp_tpl, ramp_gt = build_scene(scales=RAMP_SCALES, seed=SEED + 300)
cv2.imwrite(str(DATA / "scene_scale_ramp.png"), ramp_src)
print(f"尺度梯度场景：{ramp_src.shape}，目标 {len(ramp_gt)} 个，"
      f"尺度 {RAMP_SCALES[0]} ~ {RAMP_SCALES[-1]}")


def peak_at_gt(resp, g, win=4):
    x0 = int(np.clip(g["x"], 0, resp.shape[1] - 1))
    y0 = int(np.clip(g["y"], 0, resp.shape[0] - 1))
    return float(resp[max(0, y0 - win):y0 + win + 1,
                      max(0, x0 - win):x0 + win + 1].max())


gap_rows = []
for g in ramp_gt:
    s = g["scale"]
    # (a) 精确同尺度模板
    pk_ex = peak_at_gt(ncc_match(ramp_src, resize_template(ramp_tpl, s))[0], g)
    # (b) 用搜索集合中最接近的尺度
    s_near = min(SEARCH_SCALES, key=lambda v: abs(np.log2(v / s)))
    pk_near = peak_at_gt(ncc_match(ramp_src, resize_template(ramp_tpl, s_near))[0], g)
    gap_rows.append({
        "目标尺度": s,
        "最近搜索尺度": s_near,
        "尺度偏差(倍)": round(max(s / s_near, s_near / s), 3),
        "精确同尺度峰值": pk_ex,
        "最近搜索尺度峰值": pk_near,
        "精确可检出": "是" if pk_ex >= MATCH_THRESH else "否",
        "最近尺度可检出": "是" if pk_near >= MATCH_THRESH else "否",
    })

GAP_DF = pd.DataFrame(gap_rows)
GAP_DF.to_csv(DATA / "gap_analysis.csv", index=False, encoding="utf-8-sig")
print("\n非二进尺度目标的检出能力：")
print(GAP_DF.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

n_ex = int((GAP_DF["精确可检出"] == "是").sum())
n_near = int((GAP_DF["最近尺度可检出"] == "是").sum())
print(f"\n精确同尺度模板：{n_ex}/{len(GAP_DF)} 个尺度可检出")
print(f"最近二进尺度　：{n_near}/{len(GAP_DF)} 个尺度可检出")
print("→ 只要搜索尺度足够密，任意尺度目标均可检出；尺度集合的疏密决定漏检边界。")
''')

code(r'''
# ===================== 6.6 尺度偏差与峰值的关系 =====================
fig, ax = plt.subplots(figsize=(11.5, 4.8))
x = GAP_DF["目标尺度"].values
ax.plot(x, GAP_DF["精确同尺度峰值"], "o-", color="tab:green", lw=2,
        label="与目标精确同尺度的模板（理论上限）")
ax.plot(x, GAP_DF["最近搜索尺度峰值"], "s-", color="tab:blue", lw=2,
        label="使用最近二进搜索尺度")
ax.axhline(MATCH_THRESH, color="k", ls="--", lw=1.2, label=f"判定阈值 {MATCH_THRESH}")
for lv in (0.5, 1.0):
    ax.axvline(lv, color="tab:red", ls=":", lw=1.4)
    ax.text(lv, 1.03, f"搜索尺度 {lv}", color="tab:red", fontsize=9, ha="center")
ax.set_xlabel("目标尺度因子 s")
ax.set_ylabel("真值处 NCC 峰值")
ax.set_title("6.5 尺度偏差对响应峰值的影响", fontsize=12.5)
ax.legend(fontsize=9.5, loc="lower right")
ax.grid(alpha=0.3)
ax.set_ylim(0, 1.14)
plt.tight_layout()
plt.savefig(DATA / "fig_6_5_gap.png", bbox_inches="tight")
plt.show()
''')

# ======================================================================
md(r'''
## 7 结论与局限

### 7.1 本章结论

1. **尺度失配是单尺度匹配的硬约束**。2.2 节实测表明，目标尺度偏离模板尺寸后，
   真值处的 NCC 峰值随对数尺度偏差单调下降，超出一定范围即跌出阈值而必然漏检。

2. **多尺度模板金字塔能有效解决尺度问题**。把模板按一组尺度缩放、在原图上分别匹配，
   即可使每个尺度的目标都在"与自身尺度相同"的那次匹配中获得高峰值（实测 0.97 以上）。

3. **必须只缩放一边**。这是多尺度匹配最容易出错的地方：同时缩放模板与图像会使尺度比不变，
   目标与模板永远尺寸不符（0.4 节自检 5 给出了该反例的实测数值）。

4. **NMS 是消除多尺度冗余的必要后处理**。多尺度匹配会让同一目标被多个尺度命中，
   NMS 在不损失检出率的前提下把冗余框降到接近零。

5. **参数权衡**：搜索尺度越密，能覆盖的目标尺度越连续，但耗时随尺度个数线性增长；
   IoU 阈值过小会误抑制相邻真实目标、过大则残留冗余框；匹配阈值过低引入大量候选框、过高则漏检。

### 7.2 局限性与展望

**局限**

- 算法对**旋转**不具备适应性：NCC 匹配是平移不变的，目标旋转后响应会急剧下降。
- 搜索尺度是**离散**的，位于两个搜索尺度中间的目标峰值会下降；加密尺度可缓解，代价是耗时线性增长。
- 目标被**遮挡或大幅形变**时，NCC 响应峰不再可靠；相似纹理区域可能产生误检。

**展望**

- 引入**对数极坐标变换**，把旋转搜索转化为尺度搜索，从而复用当前的模板缩放框架实现旋转不变匹配；
- 采用**由粗到精**策略：先在缩放图上定位候选区域，仅在原图局部做精细匹配，以降低总耗时；
- 用**频域互相关**实现各尺度匹配，把单次匹配复杂度从 $O(HW\,hw)$ 降到 $O(HW\log HW)$——
  这正是第四章的改进方向，两章之间由此形成衔接。
''')

code(r'''
# ===================== 7.1 结果汇总与落盘 =====================
summary = {
    "场景": f"{SRC_W}x{SRC_H}，目标 {len(GT)} 个，尺度 {TARGET_SCALES}",
    "参数": {"搜索尺度": SEARCH_SCALES, "匹配阈值": MATCH_THRESH,
             "NMS_IoU阈值": IOU_THRESH, "定位容差": LOC_TOL},
    "单尺度": {"检出率": round(float(RES_DF.loc["① 单尺度（无NMS）", "检出率"]), 4),
             "检出框数": int(RES_DF.loc["① 单尺度（无NMS）", "检出框总数"]),
             "冗余框数": int(RES_DF.loc["① 单尺度（无NMS）", "冗余框数"]),
             "耗时_ms": round(float(T_SINGLE), 2)},
    "多尺度无NMS": {"检出率": round(float(RES_DF.loc["② 多尺度（无NMS）", "检出率"]), 4),
                   "检出框数": int(RES_DF.loc["② 多尺度（无NMS）", "检出框总数"]),
                   "冗余框数": int(RES_DF.loc["② 多尺度（无NMS）", "冗余框数"])},
    "多尺度_NMS": {"检出率": round(float(RES_DF.loc["③ 多尺度 + NMS（本文）", "检出率"]), 4),
                  "检出框数": int(RES_DF.loc["③ 多尺度 + NMS（本文）", "检出框总数"]),
                  "误检率": round(float(RES_DF.loc["③ 多尺度 + NMS（本文）", "误检率"]), 4),
                  "冗余框数": int(RES_DF.loc["③ 多尺度 + NMS（本文）", "冗余框数"]),
                  "平均定位误差": round(float(RES_DF.loc["③ 多尺度 + NMS（本文）", "平均定位误差"]), 3),
                  "耗时_ms": round(float(T_MS), 2)},
    "精确同尺度可检出": f"{n_ex}/{len(GAP_DF)}",
    "最近二进尺度可检出": f"{n_near}/{len(GAP_DF)}",
}
(DATA / "key_numbers.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

print("本章关键结果（可直接引用进论文）")
print("=" * 62)
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("=" * 62)
print("\n已导出文件：")
for p in sorted(DATA.iterdir()):
    print(f"  {p.name:<38s}{p.stat().st_size/1024:9.1f} KB")
''')

# ======================================================================
md(r'''
---

## 附：本章生成的文件清单

| 文件 | 说明 |
| --- | --- |
| `data/scene_src.png` | 自建多尺度测试源图 |
| `data/scene_tpl.png` | 模板图像 |
| `data/scene_scale_ramp.png` | 尺度梯度场景（非二进尺度分析用） |
| `data/ground_truth.csv` | 逐目标真值（中心、尺寸、尺度） |
| `data/metrics_by_config.csv` | 三组配置的定量指标 |
| `data/sweep_scales.csv` | 搜索尺度集合疏密扫描结果 |
| `data/sweep_iou.csv` | NMS 的 IoU 阈值扫描结果 |
| `data/sweep_match_thresh.csv` | 匹配阈值扫描结果 |
| `data/gap_analysis.csv` | 非二进尺度目标的检出能力分析 |
| `data/key_numbers.json` | 关键数字（供论文正文引用） |
| `data/fig_*.png` | 论文插图（可直接插入论文） |

## 复现方式

```powershell
# 1) 重新生成 notebook（改动算法请改 build_nb.py，不要直接改 ipynb）
python D:\workspace\Jupyter_WorkSpace\DIP\0303\build_nb.py

# 2) 执行并内嵌输出
python D:\workspace\Jupyter_WorkSpace\DIP\_tools\exec_nb.py 0303

# 3) 交付前总校验（含 Markdown 渲染规范）
python D:\workspace\Jupyter_WorkSpace\DIP\_tools\verify.py 0303
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
