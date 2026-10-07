# -*- coding: utf-8 -*-
"""生成 0303 的算法流程图（图1）：多尺度模板金字塔 + NMS。"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager

avail = {f.name for f in font_manager.fontManager.ttflist}
cn = next((n for n in ["Microsoft YaHei", "SimHei", "SimSun"] if n in avail), None)
plt.rcParams["font.sans-serif"] = ([cn] if cn else []) + ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0303\data") / "fig_3_1_pipeline.png"

fig, ax = plt.subplots(figsize=(13.5, 7.2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 72)
ax.axis("off")

BOX = dict(boxstyle="round,pad=0.42", linewidth=1.25)
C_IO = "#eeeeee"       # 输入输出
C_BASE = "#f6e0d5"     # 基础算法
C_MS = "#dbe9f6"       # 多尺度改进
C_NMS = "#dff2e0"      # 去重改进


def box(x, y, w, h, text, color, fs=10, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, facecolor=color,
                                edgecolor="#33475b", **BOX))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.5)


def arrow(x1, y1, x2, y2, color="#33475b", ls="-", label=None, fs=8.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=15, linewidth=1.35,
                                 color=color, linestyle=ls))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.1, label, ha="center",
                va="bottom", fontsize=fs, color=color)


# ---- 输入 ----
box(3, 57, 20, 10, "源图 $I$（固定不动）\nSource image", C_IO)
box(28, 57, 20, 10, "模板 $T$（$48\\times32$）\nTemplate", C_IO)
ax.text(50.5, 62, "＋", fontsize=20, ha="center", va="center")

# ---- 多尺度模板金字塔 ----
box(55, 57, 40, 10, "① 多尺度模板金字塔：按尺度集合 $s_k$ 缩放模板\n"
                    "Multi-scale template pyramid: resize template by $s_k$",
    C_MS, fs=10, bold=True)

# 尺度通道
scales = [(2.0, "96×64"), (1.0, "48×32"), (0.5, "24×16"), (0.25, "12×8")]
xs = [4, 27, 50, 73]
for (s, size), x in zip(scales, xs):
    box(x, 41, 21, 9, f"$s$={s:g} → {size}\n尺度通道", C_MS, fs=9.5)
    arrow(x + 10.5, 57, x + 10.5, 50)
ax.text(50, 52.6, "模板缩放（分尺度并行）", ha="center", fontsize=9,
        color="#33475b", style="italic")

# ---- NCC 匹配 ----
for x in xs:
    box(x, 26.5, 21, 9, "② NCC 匹配（在原图上）\nNCC matching", C_BASE, fs=9.5)
    arrow(x + 10.5, 41, x + 10.5, 35.5)
ax.text(50, 37.6, "每个尺度都在同一张原图上匹配 —— 只缩模板、不缩原图",
        ha="center", fontsize=9, color="#a33", style="italic")

# ---- 阈值筛选 ----
for x in xs:
    box(x, 15.5, 21, 7.5, "③ 阈值筛选\n候选框", C_BASE, fs=9.5)
    arrow(x + 10.5, 26.5, x + 10.5, 23)

# ---- 合并 ----
box(4, 5.5, 42, 7.5, "④ 合并各尺度候选框\nMerge candidates", C_MS, fs=10)
for x in xs:
    arrow(x + 10.5, 15.5, 25, 13)
arrow(25, 13, 25, 13)

# ---- NMS ----
box(52, 5.5, 44, 7.5, "⑤ 非极大值抑制 NMS → 每目标唯一框\n"
                      "NMS → one box per target", C_NMS, fs=10, bold=True)
arrow(46, 9.25, 52, 9.25)

# 图例
ax.text(3, 69.5, "图例：", fontsize=9.5, fontweight="bold")
for i, (c, t) in enumerate([(C_IO, "输入输出"), (C_BASE, "基础算法"),
                            (C_MS, "多尺度改进"), (C_NMS, "去重改进")]):
    x0 = 10 + i * 20
    ax.add_patch(FancyBboxPatch((x0, 68.2), 3, 2.4, facecolor=c,
                                edgecolor="#33475b", boxstyle="round,pad=0.15"))
    ax.text(x0 + 3.8, 69.4, t, fontsize=9, va="center")

plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print("已生成:", OUT)
