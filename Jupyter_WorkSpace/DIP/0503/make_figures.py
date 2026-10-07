# -*- coding: utf-8 -*-
"""生成 0503 论文图1：本文算法整体流程 → data/fig_0_pipeline.png"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

D = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0503")
DATA = D / "data"
DATA.mkdir(parents=True, exist_ok=True)

avail = {f.name for f in font_manager.fontManager.ttflist}
cn = next((n for n in ["Microsoft YaHei", "SimHei", "SimSun"] if n in avail), None)
plt.rcParams["font.sans-serif"] = ([cn] if cn else []) + ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(11.5, 7.5))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")
BOX = dict(boxstyle="round,pad=0.45", linewidth=1.3)
EDGE = "#33475b"
C_IN = "#eeeeee"        # 输入
C_DEG = "#f6e0d5"       # 退化 / 复原
C_NOISE = "#dbe9f6"     # 噪声
C_PRE = "#dff2e0"       # 前置降噪与评价


def box(x, y, w, h, text, color, fs=11.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, facecolor=color,
                                edgecolor=EDGE, **BOX))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.6)


def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=16, linewidth=1.5, color=EDGE))


# ---- 图例 ----
ax.text(1, 98.6, "图例：", fontsize=10, fontweight="bold", va="center")
for k, (c, t) in enumerate([(C_IN, "输入"), (C_DEG, "退化/复原"),
                            (C_NOISE, "噪声"), (C_PRE, "前置降噪与评价")]):
    x0 = 11 + k * 22
    ax.add_patch(FancyBboxPatch((x0, 97.3), 3.2, 2.6, facecolor=c,
                                edgecolor=EDGE, boxstyle="round,pad=0.15"))
    ax.text(x0 + 4.2, 98.5, t, fontsize=9.8, va="center")

# ---- 第 1 行：清晰原图 → 高斯 PSF ----
box(4, 85, 42, 9.5, "清晰原图 f（512×512）", C_IN)
arrow(46, 89.7, 54, 89.7)
box(54, 85, 42, 9.5, "高斯 PSF h（25×25, $\\sigma$=3.0）", C_IN)

# ---- ① 退化仿真 ----
arrow(50, 85, 50, 79)
box(20, 69, 60, 9.5, "① 退化仿真  g = f*h + n", C_DEG, bold=True)

# ---- 第 3 行：噪声类型 || 退化图像 ----
arrow(50, 69, 50, 63)
box(4, 53, 44, 9.5, "噪声：高斯白 / 椒盐 / 条带", C_NOISE)
box(52, 53, 44, 9.5, "退化图像 g", C_NOISE, bold=True)

# ---- ② 前置降噪 ----
arrow(50, 53, 50, 47)
box(20, 37, 60, 9.5, "② 前置降噪（低通 / 中值，可选）", C_PRE, bold=True)

# ---- ③ 维纳复原 ----
arrow(50, 37, 50, 31)
box(20, 21, 60, 9.5, "③ 维纳复原  conj(H)/(|H|$^2$+K) · G", C_DEG, bold=True)

# ---- ④ 逆变换 ----
arrow(50, 21, 50, 15)
box(20, 5, 60, 9.5, "④ 逆变换 → 复原图像", C_DEG, bold=True)

# ---- ⑤ 评价 ----
arrow(50, 5, 50, -1)
box(20, -11, 60, 9.5, "⑤ 评价：PSNR / SSIM（以 f 为基准）", C_PRE, bold=True)

ax.set_ylim(-13, 101)
plt.tight_layout()
out = DATA / "fig_0_pipeline.png"
plt.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"已生成 {out.name}  ({out.stat().st_size/1024:.1f} KB)")
