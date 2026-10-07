# -*- coding: utf-8 -*-
"""生成 0402 论文图1：本文算法整体流程 → data/fig_0_pipeline.png"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager

D = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0402")
DATA = D / "data"

# ---------- 1) 画流程图 ----------
avail = {f.name for f in font_manager.fontManager.ttflist}
cn = next((n for n in ["Microsoft YaHei", "SimHei", "SimSun"] if n in avail), None)
plt.rcParams["font.sans-serif"] = ([cn] if cn else []) + ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(11, 7.2))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
BOX = dict(boxstyle="round,pad=0.45", linewidth=1.3)
C_IN, C_FFT, C_SEL, C_NMS = "#eeeeee", "#dbe9f6", "#f6e0d5", "#dff2e0"


def box(x, y, w, h, text, color, fs=10.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, facecolor=color,
                                edgecolor="#33475b", **BOX))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.6)


def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=16, linewidth=1.4, color="#33475b"))


box(6, 86, 38, 10, "源图 I（512×384）", C_IN)
box(56, 86, 38, 10, "模板 T（32×32）", C_IN)
arrow(44, 91, 56, 91)

box(18, 70, 64, 10, "① 补零去均值：补到 415×543，各自减均值", C_FFT, bold=True)
arrow(25, 86, 25, 80); arrow(75, 86, 75, 80); arrow(50, 80, 50, 80)

box(18, 54, 64, 10, "② FFT 匹配：F·conj(G) 后逆变换 → 响应图", C_FFT, bold=True)
arrow(50, 70, 50, 64)

box(18, 38, 64, 10, "③ 裁剪有效区(353×481) + 归一化到 [0,1]", C_FFT, bold=True)
arrow(50, 54, 50, 48)

box(18, 22, 64, 10, "④ 阈值筛选：过阈值位置作为候选 → 87 个框", C_SEL, bold=True)
arrow(50, 38, 50, 32)

box(18, 6, 64, 10, "⑤ NMS 去重：IoU 迭代抑制 → 6 个唯一框", C_NMS, bold=True)
arrow(50, 22, 50, 16)

ax.text(3, 96.5, "图例：", fontsize=9.5, fontweight="bold")
for k, (c, t) in enumerate([(C_IN, "输入"), (C_FFT, "FFT 匹配"), (C_SEL, "阈值筛选"),
                            (C_NMS, "NMS 改进")]):
    x0 = 11 + k * 20
    ax.add_patch(FancyBboxPatch((x0, 95.3), 3, 2.4, facecolor=c,
                                edgecolor="#33475b", boxstyle="round,pad=0.15"))
    ax.text(x0 + 3.8, 96.4, t, fontsize=9, va="center")

plt.tight_layout()
flow = DATA / "fig_0_pipeline.png"
plt.savefig(flow, dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print("已生成流程图:", flow.name)
