# -*- coding: utf-8 -*-
"""生成图1：本文算法整体流程图（中英双语标注）。"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import font_manager

# 中文字体
avail = {f.name for f in font_manager.fontManager.ttflist}
cn = next((n for n in ["Microsoft YaHei", "SimHei", "SimSun"] if n in avail), None)
plt.rcParams["font.sans-serif"] = ([cn] if cn else []) + ["DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

OUT = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0202\data") / "fig_2_0_flowchart.png"

fig, ax = plt.subplots(figsize=(11.5, 6.2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 62)
ax.axis("off")

BOX = dict(boxstyle="round,pad=0.45", linewidth=1.3)
C_MAIN = "#dbe9f6"      # 本文新增模块
C_GMM = "#f6e0d5"       # 传统 GMM
C_IO = "#eeeeee"        # 输入输出


def box(x, y, w, h, text, color, fs=10.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, facecolor=color, edgecolor="#33475b",
                                **BOX))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.5)


def arrow(x1, y1, x2, y2, label=None, style="-|>", color="#33475b", ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=16, linewidth=1.4,
                                 color=color, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.2, label, ha="center", va="bottom",
                fontsize=8.8, color="#33475b")


# ---- 第一行：输入 -> GMM -> 原始掩码 ----
box(2, 44, 16, 10, "输入视频帧 $I_t$\nInput frame", C_IO)
box(23, 44, 20, 10, "GMM 逐像素背景建模\nGMM background modeling", C_GMM)
box(48, 44, 17, 10, "原始前景掩码 $M_t$\nRaw mask", C_GMM)

arrow(18, 49, 23, 49)
arrow(43, 49, 48, 49)

# 从原始掩码下折到频域链
arrow(56.5, 44, 56.5, 38.5, "步骤①")

# ---- 第二行：频域处理链（本文新增） ----
box(3, 27, 18, 11, "二维傅里叶变换\n$F=\\mathcal{F}\\{M_t\\}$\n2-D Fourier transform", C_MAIN)
box(24.5, 27, 18, 11, "高斯低通传递函数\n$H(u,v)=e^{-D^2/2D_0^2}$\nGaussian low-pass", C_MAIN)
box(46, 27, 18, 11, "频域逐点相乘\n$F_f=F\\odot H$\n(卷积定理)\nPoint-wise product", C_MAIN)
box(67.5, 27, 18, 11, "逆傅里叶变换\n$M_{mag}=|\\mathcal{F}^{-1}\\{F_f\\}|$\nInverse transform", C_MAIN)

arrow(21, 32.5, 24.5, 32.5)
arrow(42.5, 32.5, 46, 32.5)
arrow(64, 32.5, 67.5, 32.5)
# 传递函数自上而下汇入相乘
arrow(33.5, 27, 33.5, 24.5, style="-")
arrow(33.5, 24.5, 52, 24.5, style="-")
arrow(52, 24.5, 52, 27)

# ---- 第三行：阈值 -> 净化掩码 -> 下一帧 ----
box(67.5, 12, 18, 10, "阈值二值化 $\\tau=0.5$\n第⑩式 / Thresholding", C_MAIN)
arrow(76.5, 27, 76.5, 22)
box(67.5, 1, 18, 9, "净化掩码 $M'_t$\nPurified mask", C_IO)
arrow(76.5, 12, 76.5, 10)

# 反馈：下一帧回到输入
arrow(67.5, 5.5, 10, 5.5, "步骤⑤：更新 GMM 参数并读取下一帧 / update model, next frame",
      style="-|>", color="#7a7a7a", ls="--")
arrow(10, 5.5, 10, 44)

# 图例
ax.text(3, 58.5, "图例：", fontsize=9.5, fontweight="bold")
ax.add_patch(FancyBboxPatch((8.5, 57.0), 6, 3.0, facecolor=C_GMM, edgecolor="#33475b", **BOX))
ax.text(15.2, 58.5, "传统 GMM 环节", fontsize=9, va="center")
ax.add_patch(FancyBboxPatch((28, 57.0), 6, 3.0, facecolor=C_MAIN, edgecolor="#33475b", **BOX))
ax.text(34.7, 58.5, "本文新增频域环节", fontsize=9, va="center")
ax.add_patch(FancyBboxPatch((52, 57.0), 6, 3.0, facecolor=C_IO, edgecolor="#33475b", **BOX))
ax.text(58.7, 58.5, "输入输出", fontsize=9, va="center")

plt.tight_layout()
plt.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
print("已生成:", OUT)
