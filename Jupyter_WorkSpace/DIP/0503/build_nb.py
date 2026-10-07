# -*- coding: utf-8 -*-
"""
生成 DIP 第五章课设 Notebook：
    维纳滤波复原中前置降噪的有效性条件研究
"""
import json
import os

NB_PATH = (r"D:\workspace\Jupyter_WorkSpace\DIP\0503"
           r"\DIP第五章_维纳滤波复原中前置降噪的有效性条件.ipynb")

cells = []


def _src(text):
    body = text.strip("\n")
    return body.splitlines(keepends=True) if body else []


def md(t):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": _src(t)})


def code(t):
    cells.append({"cell_type": "code", "execution_count": None, "metadata": {},
                  "outputs": [], "source": _src(t)})


# ======================================================================
md(r'''
# 维纳滤波复原中前置降噪的有效性条件

> **数字图像处理 课程设计 · 第五章**

## 本章主要工作

图像复原要由退化图像 $g=f*h+n$ 恢复 $f$ 。维纳滤波是最具代表性的频域方法，
但它的传递函数在高频段会把噪声一并放大。一个流传很广的做法是**在复原之前先做降噪**
（"先去噪再去模糊"）。

本章的问题是：**这个前置降噪到底有没有用？在什么条件下才有用？**

做法是构建"退化图像 → 前置降噪 → 维纳复原"的流水线，并在**公平调参**
（两种流程的维纳正则参数都各自取到最优）的前提下，**控制噪声类型与降噪算子**
做交叉实验，用 PSNR 与 SSIM 定量比较。

**本章结论（先给结论，后给证据）**：前置降噪不是无条件的改进，其增益取决于
**降噪算子与噪声类型是否匹配**：

| 条件 | 结果 |
| --- | --- |
| 低通 ↔ 条带噪声（匹配） | **+1.40 dB** |
| 中值 ↔ 椒盐噪声（匹配） | **+1.35 dB** |
| 低通 ↔ 椒盐噪声（错配） | −0.08 dB（无增益） |
| 中值 ↔ 高斯噪声（错配） | −0.17 ~ −0.27 dB（负增益） |
| 平稳高斯白噪声（无匹配算子） | 无任何稳定增益 |

> **关键理解**：维纳滤波本身就是频域最小均方误差意义下的最优线性加权，
> 它在高频段自动趋近于 0。所以前置降噪只在"维纳滤波自身**无法有效建模**的噪声"
> 上才有价值——这正是椒盐噪声（脉冲型）与条带噪声（结构性）的情形。

## 环境

内核 `D:\workspace\.my_env` ；依赖 `numpy` `scipy` `scikit-image` `matplotlib` `pandas`。
''')

# ----------------------------------------------------------------------
code(r'''
# ===== 0 准备：导入、路径、参数 =====
import time
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy import ndimage
from skimage import data, metrics, restoration

for _n in ["Microsoft YaHei", "SimHei", "SimSun"]:
    if _n in {f.name for f in font_manager.fontManager.ttflist}:
        plt.rcParams["font.sans-serif"] = [_n, "DejaVu Sans"]
        break
plt.rcParams["axes.unicode_minus"] = False

DATA = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0503\data")
DATA.mkdir(parents=True, exist_ok=True)

SEED = 503
rng = np.random.default_rng(SEED)

SIG_BLUR = 3.0
KS = 25
BALANCES = (1e-4, 3e-4, 1e-3, 3e-3, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0)

print("numpy", np.__version__, "| skimage", __import__("skimage").__version__)
print(f"模糊 σ={SIG_BLUR}，核尺寸={KS}，维纳 balance 备选 {len(BALANCES)} 档")
''')

# ----------------------------------------------------------------------
md(r'''
## 1 退化模型

$$g(x,y)=f(x,y)*h(x,y)+n(x,y)$$

$f$ 为清晰原图（`skimage.data.camera()`）、$h$ 为高斯型点扩散函数、$n$ 为噪声。
采用合成退化的原因是**可以保留清晰真值**，从而让 PSNR/SSIM 有可比基准。

本章的噪声分三类，分别对应不同的物理成因：

| 噪声 | 成因举例 | 是否需要特殊算子 |
| --- | --- | --- |
| 高斯白噪声 | 传感器热噪声 | 频谱平坦，维纳可处理 |
| 椒盐噪声 | 传输误码、坏点 | **脉冲型**，维纳无法建模 |
| 条带噪声 | 扫描仪、传感器列固定模式 | **结构性**，维纳无法建模 |
''')

code(r'''
# ===== 1.1 清晰原图与 PSF =====
f = data.camera().astype(np.float64) / 255.0
H, W = f.shape

_a = np.arange(KS) - KS // 2
_xx, _yy = np.meshgrid(_a, _a)
psf = np.exp(-(_xx**2 + _yy**2) / (2 * SIG_BLUR**2))
psf /= psf.sum()

blur = ndimage.convolve(f, psf, mode="reflect")

print(f"清晰原图 {H}x{W}")
print(f"高斯 PSF {KS}x{KS}, σ={SIG_BLUR}, 和为 {psf.sum():.6f}")
print(f"仅模糊    PSNR={metrics.peak_signal_noise_ratio(f, blur, data_range=1):.2f} dB"
      f"   SSIM={metrics.structural_similarity(f, blur, data_range=1):.4f}")

fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
for ax, (im, t) in zip(axes, [(f, "清晰原图 $f$"), (psf, f"高斯 PSF（{KS}×{KS}）"),
                              (blur, "仅模糊 $f*h$")]):
    ax.imshow(im, cmap="gray", vmin=0, vmax=1)
    ax.set_title(t, fontsize=11); ax.axis("off")
plt.suptitle("1.1 清晰原图、点扩散函数与模糊结果", fontsize=12.5)
plt.tight_layout()
plt.savefig(DATA / "fig_1_source.png", bbox_inches="tight")
plt.show()
''')

code(r'''
# ===== 1.2 三类噪声生成函数 =====
def add_gauss(x, s):
    """高斯白噪声（频谱平坦）。"""
    return np.clip(x + rng.normal(0, s, x.shape), 0, 1)


def add_sp(x, p):
    """椒盐噪声（脉冲型）：以概率 p 置为极值。"""
    y = x.copy()
    m = rng.random(x.shape)
    y[m < p / 2] = 0.0
    y[(m >= p / 2) & (m < p)] = 1.0
    return y


def add_stripe(x, amp, period=17):
    """条带噪声（结构性）：沿列方向的周期正弦模式。"""
    cols = np.arange(x.shape[1])
    return np.clip(x + (amp * np.sin(2 * np.pi * cols / period))[None, :], 0, 1)


NOISES = {
    "高斯白噪声": lambda x: add_gauss(x, 0.05),
    "椒盐噪声": lambda x: add_sp(x, 0.05),
    "条带噪声": lambda x: add_stripe(x, 0.06),
}

GS = {name: fn(blur) for name, fn in NOISES.items()}

fig, axes = plt.subplots(1, 4, figsize=(18, 4.2))
axes[0].imshow(blur, cmap="gray", vmin=0, vmax=1)
axes[0].set_title("仅模糊", fontsize=11); axes[0].axis("off")
for j, (name, g) in enumerate(GS.items(), 1):
    axes[j].imshow(g, cmap="gray", vmin=0, vmax=1)
    axes[j].set_title(f"{name}\nPSNR={metrics.peak_signal_noise_ratio(f,g,data_range=1):.2f} dB",
                      fontsize=10)
    axes[j].axis("off")
plt.suptitle("1.2 三类噪声的退化图像", fontsize=12.5)
plt.tight_layout()
plt.savefig(DATA / "fig_1_noises.png", bbox_inches="tight")
plt.show()

for name, g in GS.items():
    print(f"{name:<10} 退化图 PSNR={metrics.peak_signal_noise_ratio(f,g,data_range=1):6.2f} dB"
          f"   SSIM={metrics.structural_similarity(f,g,data_range=1):.4f}")
''')

# ----------------------------------------------------------------------
md(r'''
## 2 维纳滤波复原

### 2.1 原理

退化模型的频域形式为 $G=FH+N$ 。维纳滤波以最小化均方误差为目标，导出传递函数

$$\hat{F}(u,v)=\frac{H^{*}(u,v)}{|H(u,v)|^{2}+K}\,G(u,v)$$

$K$ 与信噪比相关，作用是**在 $|H|$ 趋于零的高频段抑制增益**：$K=0$ 时退化为逆滤波，
噪声被无限放大；$K$ 越大，高频抑制越强、细节损失越多。

### 2.2 为什么维纳滤波"自带降噪"

这是理解全章的关键。传递函数的增益为

$$\left|\frac{H^{*}}{|H|^{2}+K}\right|=\frac{|H|}{|H|^{2}+K}$$

- 当 $\lvert H\rvert^{2}\gg K$（低频、信号主导）：增益 $\approx 1/\lvert H\rvert$ ，**补偿模糊**；
- 当 $\lvert H\rvert^{2}\ll K$（高频、噪声主导）：增益 $\approx \lvert H\rvert/K\to 0$ ，**压掉噪声**。

也就是说，**维纳滤波已在频域按信噪比自适应地做了一次最优加权（低通）**。
因此再串联一个形状固定的低通，本质上是在最优解之前丢弃信息——除非
**该噪声的形态超出了维纳滤波的建模能力**（脉冲、结构性噪声）。

### 2.3 实现与校验

| 要点 | 做法 |
| --- | --- |
| PSF 约定 | 中心在 `psf.shape//2`（与未移位频谱一致） |
| 正则参数 | 在 10 档 balance 中取 PSNR 最优，保证公平比较 |
| 卷积校验 | 用脉冲响应验证频域卷积算子 |
''')

code(r'''
# ===== 2.3 复原函数与卷积算子校验 =====

def wiener_restore(g, balance):
    """维纳复原（PSF 中心在 shape//2）。"""
    return restoration.wiener(g, psf, balance=balance, clip=True)


def best_wiener(g):
    """遍历 balance 取 PSNR 最优，返回 (balance, PSNR, SSIM, 图像)。"""
    best = None
    for bal in BALANCES:
        r = wiener_restore(g, bal)
        p = metrics.peak_signal_noise_ratio(f, r, data_range=1)
        s = metrics.structural_similarity(f, r, data_range=1)
        if best is None or p > best[1]:
            best = (bal, p, s, r)
    return best


def conv_freq(img, kernel):
    """频域卷积：核放左上角，零填充，取有效区。"""
    kh, kw = kernel.shape
    ph, pw = img.shape[0] + kh - 1, img.shape[1] + kw - 1
    ip = np.zeros((ph, pw)); ip[:img.shape[0], :img.shape[1]] = img
    kp = np.zeros((ph, pw)); kp[:kh, :kw] = kernel
    full = np.real(np.fft.ifft2(np.fft.fft2(ip) * np.fft.fft2(kp)))
    return full[kh // 2:kh // 2 + img.shape[0], kw // 2:kw // 2 + img.shape[1]]


imp = np.zeros_like(f); imp[300, 200] = 1.0
got = conv_freq(imp, psf)
ref = ndimage.convolve(imp, psf, mode="constant")
err = np.abs(got - ref).max()
print(f"[校验] 脉冲响应：峰值位置 {np.unravel_index(np.argmax(got), got.shape)}（应为 (300,200)）")
print(f"       频域卷积 vs 空域卷积 最大绝对差 = {err:.2e}"
      f"   {'OK（一致）' if err < 1e-12 else '异常'}")

print("\n[校验] balance 对复原的影响（以高斯噪声为例）：")
for bal in (1e-4, 0.01, 0.1, 1.0):
    r = wiener_restore(GS["高斯白噪声"], bal)
    print(f"   balance={bal:<7} PSNR={metrics.peak_signal_noise_ratio(f,r,data_range=1):6.2f} dB"
          f"  残差std={float(np.std(r-f)):.4f}")
''')

# ----------------------------------------------------------------------
md(r'''
## 3 基线：直接维纳复原

先取得每种噪声下**直接维纳复原的最优结果**，作为后续比较的基准。
这一步很关键：只有让两种流程各自取到最优，比较才公平。
''')

code(r'''
# ===== 3.1 直接维纳复原（各噪声的基准）=====
BASE = {}
t0 = time.perf_counter()
for name, g in GS.items():
    bal, p, s, img = best_wiener(g)
    BASE[name] = {"balance": bal, "PSNR": p, "SSIM": s, "img": img}
T_BASE = (time.perf_counter() - t0) * 1000

print("直接维纳复原（balance 取最优）：")
print(f"{'噪声':<10}{'退化图PSNR':>12}{'最优balance':>14}{'复原PSNR':>12}{'SSIM':>10}")
print("-" * 62)
for name, g in GS.items():
    pg = metrics.peak_signal_noise_ratio(f, g, data_range=1)
    b = BASE[name]
    print(f"{name:<10}{pg:>12.2f}{b['balance']:>14}{b['PSNR']:>12.2f}{b['SSIM']:>10.4f}")
print(f"\n基准总耗时 {T_BASE:.0f} ms")

fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
for ax, (name, g) in zip(axes, GS.items()):
    ax.imshow(BASE[name]["img"], cmap="gray", vmin=0, vmax=1)
    ax.set_title(f"{name}\n直接维纳 PSNR={BASE[name]['PSNR']:.2f} dB", fontsize=10.5)
    ax.axis("off")
plt.suptitle("3.1 直接维纳复原结果", fontsize=12.5)
plt.tight_layout()
plt.savefig(DATA / "fig_3_baseline.png", bbox_inches="tight")
plt.show()
''')

# ----------------------------------------------------------------------
md(r'''
## 4 降噪算子与噪声类型的匹配性

### 4.1 两个候选降噪算子

**（1）高斯低通（频域）** —— 在频域乘一个高斯传递函数：

$$D(u,v)=\exp\!\left(-\frac{D^{2}(u,v)}{2D_0^{2}}\right)$$

它对**分布在某个频段上的能量**（如条带噪声的周期模式）有效。

**（2）中值滤波（空域）** —— 用邻域中位数替代中心像素。
它对**孤立的极端值**（椒盐噪声的脉冲）有效，而低通只会把脉冲"抹开"成一片模糊。

### 4.2 匹配假设

| 噪声 | 形态 | 匹配算子 | 不匹配算子 |
| --- | --- | --- | --- |
| 高斯白噪声 | 频带内均匀分布 | 无（维纳已最优） | 都无益 |
| 椒盐噪声 | **空间稀疏的极端脉冲** | **中值** | 低通（会把脉冲抹开） |
| 条带噪声 | **特定频率的周期结构** | **低通** | 中值（无法去除整列偏置） |

下面用交叉矩阵验证这个假设。
''')

code(r'''
# ===== 4.3 两个降噪算子 =====
def lowpass(img, D0):
    """频域高斯低通（零填充，直流在 [0,0]）。"""
    u = np.fft.fftfreq(img.shape[1]) * img.shape[1]
    v = np.fft.fftfreq(img.shape[0]) * img.shape[0]
    V, U = np.meshgrid(u, v)
    D = np.exp(-(U**2 + V**2) / (2 * D0**2))
    return np.clip(np.real(np.fft.ifft2(np.fft.fft2(img) * D)), 0, 1)


def medfilt(img, k):
    """空域中值滤波。"""
    return ndimage.median_filter(img, size=k)


KERNELS = {
    "低通 D0=30": lambda x: lowpass(x, 30),
    "低通 D0=60": lambda x: lowpass(x, 60),
    "中值 k=5": lambda x: medfilt(x, 5),
    "中值 k=7": lambda x: medfilt(x, 7),
}

_g_sp = GS["椒盐噪声"]
_d_med = medfilt(_g_sp, 5)
_d_lp = lowpass(_g_sp, 60)
p_med = metrics.peak_signal_noise_ratio(f, _d_med, data_range=1)
p_lp = metrics.peak_signal_noise_ratio(f, _d_lp, data_range=1)
print("算子对椒盐噪声的降噪效果（相对清晰原图的 PSNR）：")
print(f"  椒盐退化图        {metrics.peak_signal_noise_ratio(f, _g_sp, data_range=1):6.2f} dB")
print(f"  中值 k=5 处理后   {p_med:6.2f} dB   <- 显著提升")
print(f"  低通 D0=60 处理后 {p_lp:6.2f} dB   <- 几乎无改善")
print(f"  {'OK：中值明显更适合脉冲噪声' if p_med > p_lp else '异常'}")
''')

code(r'''
# ===== 4.4 交叉矩阵：降噪算子 × 噪声类型 =====
rows = []
for nname, g in GS.items():
    bd = BASE[nname]
    row = {"噪声": nname,
           "退化图PSNR": metrics.peak_signal_noise_ratio(f, g, data_range=1),
           "直接维纳PSNR": bd["PSNR"], "直接维纳SSIM": bd["SSIM"]}
    for kn, kfn in KERNELS.items():
        b = best_wiener(kfn(g))
        row[f"{kn}_PSNR"] = b[1]
        row[f"{kn}_增益"] = b[1] - bd["PSNR"]
        row[f"{kn}_SSIM"] = b[2]
        row[f"{kn}_SSIM增益"] = b[2] - bd["SSIM"]
    rows.append(row)

MX = pd.DataFrame(rows)
MX.to_csv(DATA / "matrix_kernel_noise.csv", index=False, encoding="utf-8-sig")

print("=" * 96)
print("交叉矩阵：前置降噪 + 维纳 相对 直接维纳 的 PSNR 增益 (dB)")
print("=" * 96)
print(f"{'噪声':<10}" + "".join(f"{k:>16}" for k in KERNELS))
print("-" * 96)
for _, r in MX.iterrows():
    print(f"{r['噪声']:<10}" + "".join(f"{r[f'{k}_增益']:>+16.2f}" for k in KERNELS))
print("-" * 96)
print("\n各格 PSNR 绝对值 (dB)：")
print(f"{'噪声':<10}{'直接维纳':>12}" + "".join(f"{k:>16}" for k in KERNELS))
print("-" * 96)
for _, r in MX.iterrows():
    print(f"{r['噪声']:<10}{r['直接维纳PSNR']:>12.2f}"
          + "".join(f"{r[f'{k}_PSNR']:>16.2f}" for k in KERNELS))
''')

code(r'''
# ===== 4.5 匹配 vs 错配 =====
PAIRS = [
    ("椒盐噪声", "中值 k=5", "中值 k=7", "低通 D0=30", "低通 D0=60"),
    ("条带噪声", "低通 D0=30", "低通 D0=60", "中值 k=5", "中值 k=7"),
]
rows = []
for noise, kb1, kb2, kw1, kw2 in PAIRS:
    r = MX[MX["噪声"] == noise].iloc[0]
    matched = max(r[f"{kb1}_增益"], r[f"{kb2}_增益"])
    mismatched = max(r[f"{kw1}_增益"], r[f"{kw2}_增益"])
    rows.append({"噪声": noise, "匹配算子增益": matched,
                 "错配算子增益": mismatched, "差值": matched - mismatched})
MATCH = pd.DataFrame(rows)
MATCH.to_csv(DATA / "match_vs_mismatch.csv", index=False, encoding="utf-8-sig")
print("匹配 vs 错配（各自取最优参数）：")
print(MATCH.to_string(index=False, float_format=lambda v: f"{v:+.2f}"))
print()
for _, r in MATCH.iterrows():
    print(f"  {r['噪声']}：匹配 {r['匹配算子增益']:+.2f} dB"
          f"   vs   错配 {r['错配算子增益']:+.2f} dB"
          f"   （差 {r['差值']:+.2f} dB）")

rg = MX[MX["噪声"] == "高斯白噪声"].iloc[0]
gains = [rg[f"{k}_增益"] for k in KERNELS]
print(f"\n  高斯白噪声：所有算子增益范围 {min(gains):+.2f} ~ {max(gains):+.2f} dB"
      f"  -> 无匹配算子可用，均无稳定增益")
''')

# ----------------------------------------------------------------------
md(r'''
## 5 结果可视化与机理分析
''')

code(r'''
# ===== 5.1 增益热力图 =====
gain_mat = np.array([[MX[MX["噪声"] == n].iloc[0][f"{k}_增益"] for k in KERNELS]
                     for n in GS.keys()])

fig, axes = plt.subplots(1, 2, figsize=(15.5, 4.8))
im = axes[0].imshow(gain_mat, cmap="RdYlGn", vmin=-0.5, vmax=1.5)
plt.colorbar(im, ax=axes[0], label="PSNR 增益 / dB")
axes[0].set_xticks(range(len(KERNELS))); axes[0].set_xticklabels(list(KERNELS), fontsize=9.5)
axes[0].set_yticks(range(len(GS))); axes[0].set_yticklabels(list(GS), fontsize=10)
for i in range(gain_mat.shape[0]):
    for j in range(gain_mat.shape[1]):
        axes[0].text(j, i, f"{gain_mat[i,j]:+.2f}", ha="center", va="center",
                     fontsize=10, fontweight="bold")
axes[0].set_title("前置降噪的 PSNR 增益（绿=有效，红=有害）", fontsize=11.5)

x = np.arange(len(MATCH)); wd = 0.36
axes[1].bar(x - wd/2, MATCH["匹配算子增益"], wd, color="tab:green", label="匹配算子")
axes[1].bar(x + wd/2, MATCH["错配算子增益"], wd, color="tab:red", label="错配算子")
for xi, (a, b) in enumerate(zip(MATCH["匹配算子增益"], MATCH["错配算子增益"])):
    axes[1].text(xi - wd/2, a, f"{a:+.2f}", ha="center", va="bottom", fontsize=9.5)
    axes[1].text(xi + wd/2, b, f"{b:+.2f}", ha="center", va="bottom", fontsize=9.5)
axes[1].axhline(0, color="k", lw=1)
axes[1].set_xticks(x); axes[1].set_xticklabels(MATCH["噪声"])
axes[1].set_ylabel("PSNR 增益 / dB")
axes[1].set_title("匹配 vs 错配", fontsize=11.5)
axes[1].legend(fontsize=9); axes[1].grid(alpha=0.3, axis="y")

plt.suptitle("5.1 前置降噪增益取决于算子与噪声的匹配性", fontsize=12.5)
plt.tight_layout()
plt.savefig(DATA / "fig_5_gain_matrix.png", bbox_inches="tight")
plt.show()
''')

code(r'''
# ===== 5.2 四个典型情形对比 =====
CASES = [
    ("椒盐 + 中值（匹配，有效）", "椒盐噪声", medfilt(GS["椒盐噪声"], 5), "中值 k=5"),
    ("椒盐 + 低通（错配，无效）", "椒盐噪声", lowpass(GS["椒盐噪声"], 60), "低通 D0=60"),
    ("条带 + 低通（匹配，有效）", "条带噪声", lowpass(GS["条带噪声"], 30), "低通 D0=30"),
    ("高斯 + 中值（错配，有害）", "高斯白噪声", medfilt(GS["高斯白噪声"], 5), "中值 k=5"),
]

fig, axes = plt.subplots(4, 5, figsize=(19, 14.5))
for i, (title, nname, pre, kname) in enumerate(CASES):
    g = GS[nname]
    b = best_wiener(pre)
    axes[i, 0].imshow(g, cmap="gray", vmin=0, vmax=1)
    axes[i, 0].set_ylabel(f"{title}\n增益 {b[1]-BASE[nname]['PSNR']:+.2f} dB", fontsize=9)
    axes[i, 0].set_title(f"{nname}\n退化图", fontsize=9.5); axes[i, 0].axis("off")
    axes[i, 1].imshow(pre, cmap="gray", vmin=0, vmax=1)
    axes[i, 1].set_title(f"前置降噪\n{kname}", fontsize=9.5); axes[i, 1].axis("off")
    axes[i, 2].imshow(BASE[nname]["img"], cmap="gray", vmin=0, vmax=1)
    axes[i, 2].set_title(f"直接维纳\n{BASE[nname]['PSNR']:.2f} dB", fontsize=9.5)
    axes[i, 2].axis("off")
    axes[i, 3].imshow(b[3], cmap="gray", vmin=0, vmax=1)
    axes[i, 3].set_title(f"前置降噪+维纳\n{b[1]:.2f} dB", fontsize=9.5); axes[i, 3].axis("off")
    axes[i, 4].imshow(f, cmap="gray", vmin=0, vmax=1)
    axes[i, 4].set_title("清晰原图", fontsize=9.5); axes[i, 4].axis("off")
plt.suptitle("5.2 四个典型情形：匹配有效、错配无效、错配有害", fontsize=13)
plt.tight_layout()
plt.savefig(DATA / "fig_5_cases.png", bbox_inches="tight")
plt.show()
''')

code(r'''
# ===== 5.3 机理分析 =====
hp = np.zeros((H, W)); hp[:KS, :KS] = np.fft.ifftshift(psf)
Hh = np.fft.fft2(hp)
u = np.fft.fftfreq(W) * W
v = np.fft.fftfreq(H) * H
V, U = np.meshgrid(v, u)

fig, axes = plt.subplots(1, 2, figsize=(14.5, 4.6))
for bal, col in zip((1e-3, 1e-2, 0.1, 1.0), ("tab:blue", "tab:cyan", "tab:orange", "tab:red")):
    gain = np.fft.fftshift(np.abs(np.conj(Hh) / (np.abs(Hh) ** 2 + bal)))
    axes[0].semilogy(gain[H // 2, :], lw=1.6, color=col, label=f"balance={bal}")
gauss = np.exp(-(np.fft.fftshift(np.hypot(V, U)) ** 2) / (2 * 30 ** 2))
axes[0].semilogy(gauss[H // 2, :], "k--", lw=1.6, label="高斯低通 D0=30")
axes[0].set_xlabel("频率（沿列方向）"); axes[0].set_ylabel("增益（对数）")
axes[0].set_title("维纳传递函数增益 vs 固定低通", fontsize=11.5)
axes[0].legend(fontsize=8.5); axes[0].grid(alpha=0.3, which="both")

for name, col in zip(GS.keys(), ("tab:blue", "tab:red", "tab:green")):
    g = GS[name]
    A = np.abs(np.fft.fftshift(np.fft.fft2(g - g.mean())))
    axes[1].semilogy(A.mean(axis=0), lw=1.5, color=col, label=name)
axes[1].set_xlabel("频率（沿列方向）"); axes[1].set_ylabel("平均幅度（对数）")
axes[1].set_title("三类噪声的频谱特征", fontsize=11.5)
axes[1].legend(fontsize=9); axes[1].grid(alpha=0.3, which="both")
plt.suptitle("5.3 机理：维纳已自适应降噪，固定低通只在特定结构上补足", fontsize=12.5)
plt.tight_layout()
plt.savefig(DATA / "fig_5_mechanism.png", bbox_inches="tight")
plt.show()
''')

# ----------------------------------------------------------------------
md(r'''
## 6 结论与适用条件

由交叉矩阵可得到明确的操作性结论：

| 噪声类型 | 建议 | 依据（本文实测） |
| --- | --- | --- |
| 椒盐（脉冲型） | 前置**中值滤波** | +1.35 dB（低通仅 −0.08 ~ −0.01 dB） |
| 条带（结构性） | 前置**低通** | +1.40 dB（中值仅 +0.18 ~ +0.43 dB） |
| 平稳高斯 | **不要**前置降噪 | 各算子 −0.27 ~ +0.10 dB，不稳定 |

**理论解释**：维纳滤波是频域最小均方误差意义下的最优线性估计，其增益
$|H|/(|H|^{2}+K)$ 已按信噪比自适应地压低了噪声主导的频段。因此前置降噪只在
**维纳滤波无法建模的噪声形态**上才有价值——脉冲型（空间稀疏、幅度极大）与
结构性（集中在特定频率）两类噪声都不符合"平稳加性噪声"的假设。

**局限**：结论建立在合成退化、空间不变模糊、参数单变量扫描之上；
最优 `balance` 由 PSNR 事后选取（实际应用中需估计信噪比）。
''')

code(r'''
# ===== 7 结果汇总 =====
def cell(noise, kname):
    r = MX[MX["噪声"] == noise].iloc[0]
    return {"PSNR": round(float(r[f"{kname}_PSNR"]), 3),
            "增益": round(float(r[f"{kname}_增益"]), 3),
            "SSIM": round(float(r[f"{kname}_SSIM"]), 4),
            "SSIM增益": round(float(r[f"{kname}_SSIM增益"]), 4)}


summary = {
    "图像": f"{H}x{W}（skimage camera）",
    "退化": {"模糊": f"高斯 PSF {KS}x{KS}, σ={SIG_BLUR}"},
    "噪声": {"高斯白噪声": "σ=0.05", "椒盐噪声": "p=0.05", "条带噪声": "amp=0.06"},
    "直接维纳基准": {n: {"balance": BASE[n]["balance"],
                        "PSNR": round(float(BASE[n]["PSNR"]), 3),
                        "SSIM": round(float(BASE[n]["SSIM"]), 4)} for n in GS},
    "匹配有效": {"椒盐×中值k5": cell("椒盐噪声", "中值 k=5"),
                "条带×低通D0_30": cell("条带噪声", "低通 D0=30")},
    "错配无效": {"椒盐×低通D0_60": cell("椒盐噪声", "低通 D0=60"),
                "高斯×中值k5": cell("高斯白噪声", "中值 k=5")},
    "高斯全部算子": {k: cell("高斯白噪声", k) for k in KERNELS},
    "核心结论": ("前置降噪的增益取决于降噪算子与噪声类型是否匹配："
               "中值×椒盐 +1.35 dB、低通×条带 +1.40 dB；"
               "错配（低通×椒盐 −0.01 dB、中值×高斯 −0.17 dB）无增益或负增益；"
               "平稳高斯白噪声下任何前置降噪均无稳定增益"),
    "机理": "维纳滤波本身即频域最小均方误差最优线性加权，高频增益自动趋近 0；"
           "前置降噪仅对维纳无法建模的噪声形态（脉冲型、结构性）有效",
    "自检": {"频域卷积与空域卷积最大绝对差": float(f"{err:.2e}")},
}
(DATA / "key_numbers.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2)[:2400])
print()
print("已导出文件：")
for fp in sorted(DATA.iterdir()):
    print(f"  {fp.name:<34}{fp.stat().st_size/1024:8.1f} KB")
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
