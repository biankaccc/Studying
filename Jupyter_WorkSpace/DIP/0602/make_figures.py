# -*- coding: utf-8 -*-
"""生成第六章论文图1：本文算法整体流程图 data/fig_0_pipeline.png"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

for _n in ["Microsoft YaHei", "SimHei", "SimSun"]:
    if _n in {f.name for f in font_manager.fontManager.ttflist}:
        plt.rcParams["font.sans-serif"] = [_n, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False

DATA = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0602\data")
DATA.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(13.2, 4.9))
ax.set_xlim(0, 100)
ax.set_ylim(0, 46)
ax.axis("off")

STEPS = [
    ("输入\n带噪图像对 A、B", "#dce9f7"),
    ("频域低通预处理\n$H(u,v)$ 抑制高频", "#ffd9a0"),
    ("SIFT 特征提取\n关键点 + 128 维描述子", "#dce9f7"),
    ("比值粗匹配\n最近邻 / 次近邻", "#dce9f7"),
    ("RANSAC 剔除外点\n+ 最小二乘重估计", "#dce9f7"),
    ("输出\n$H$ 与映射误差", "#d6f0d6"),
]

bw, bh, gap = 14.0, 10.0, 3.4
n = len(STEPS)
total = n * bw + (n - 1) * gap
x0 = (100 - total) / 2
yc = 30.0

centers = []
for i, (text, color) in enumerate(STEPS):
    x = x0 + i * (bw + gap)
    box = FancyBboxPatch((x, yc - bh / 2), bw, bh,
                         boxstyle="round,pad=0.35,rounding_size=1.2",
                         linewidth=1.4, edgecolor="#3a3a3a", facecolor=color)
    ax.add_patch(box)
    ax.text(x + bw / 2, yc, text, ha="center", va="center", fontsize=9.4)
    centers.append(x + bw / 2)
    if i:
        ax.add_patch(FancyArrowPatch((centers[i - 1] + bw / 2 + 0.4, yc),
                                     (x - 0.4, yc), arrowstyle="-|>",
                                     mutation_scale=13, linewidth=1.3,
                                     color="#3a3a3a"))

# 基础算法的旁路：跳过预处理
bx0 = centers[0]
bx1 = centers[2]
ax.add_patch(FancyArrowPatch((bx0, yc - bh / 2 - 0.6), (bx0, 12.5),
                             arrowstyle="-", linewidth=1.2, color="#b03030",
                             linestyle=(0, (4, 3))))
ax.add_patch(FancyArrowPatch((bx0, 12.5), (bx1, 12.5), arrowstyle="-",
                             linewidth=1.2, color="#b03030",
                             linestyle=(0, (4, 3))))
ax.add_patch(FancyArrowPatch((bx1, 12.5), (bx1, yc - bh / 2 - 0.6),
                             arrowstyle="-|>", mutation_scale=13, linewidth=1.2,
                             color="#b03030", linestyle=(0, (4, 3))))
ax.text((bx0 + bx1) / 2, 14.4, "① 基础算法：跳过预处理，直接送入 SIFT",
        ha="center", va="bottom", fontsize=9.2, color="#b03030")

ax.text(50, 41.5, "② 本文方法：在特征提取之前串联频域降噪预处理",
        ha="center", va="center", fontsize=11.5, weight="bold")
ax.text(50, 6.2, "两幅图像使用完全相同的滤波参数（$D_0$、阶数 $n$）",
        ha="center", va="center", fontsize=9.6, color="#444444",
        bbox=dict(boxstyle="round,pad=0.45", facecolor="#f3f3f3",
                  edgecolor="#bbbbbb"))

plt.tight_layout()
out = DATA / "fig_0_pipeline.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"已生成 {out}  ({out.stat().st_size/1024:.1f} KB)")
