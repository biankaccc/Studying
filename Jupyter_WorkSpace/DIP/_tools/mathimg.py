# -*- coding: utf-8 -*-
"""
LaTeX 公式 -> PNG 图片渲染器（用于 Word 版论文）。

为什么用图片而不是 OMML：本机 Word（Office16）会拒绝打开含特定 OMML 嵌套
（如"分式内含上下标"）的文档，报"文件可能已经损坏"。图片方案可保证：
  1. Word 一定能打开；
  2. 分式、根号、上下标、求和等显示效果与 LaTeX 一致；
  3. 转 PDF、打印、送审均无问题。

代价：公式不可在 Word 中编辑（OMML 可编辑）。若日后 OMML 方案验证通过，
可换回 omml.py。

渲染用 matplotlib 的 mathtext（自带，无需 LaTeX 发行版）。
"""
import hashlib
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# \mathrm{...} 里可能含中文（如分段函数的"像素为前景"），必须配置 CJK 字体，
# 否则 matplotlib 会用 dummy symbol 替换，公式里出现空白方块。
_CJK = None
for _name in ("Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC"):
    if _name in {f.name for f in font_manager.fontManager.ttflist}:
        _CJK = _name
        break
if _CJK:
    plt.rcParams["font.sans-serif"] = [_CJK] + list(plt.rcParams["font.sans-serif"])
    plt.rcParams["font.serif"] = [_CJK] + list(plt.rcParams["font.serif"])
    plt.rcParams["mathtext.fontset"] = "custom"
    plt.rcParams["mathtext.rm"] = _CJK
    plt.rcParams["mathtext.it"] = f"{_CJK}:italic"
    plt.rcParams["mathtext.bf"] = f"{_CJK}:bold"
plt.rcParams["axes.unicode_minus"] = False

# ---------------------------------------------------------------- 语法适配
# matplotlib mathtext 不支持的写法 -> 等价替代
GREEK = ("alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu "
         "xi pi rho sigma tau upsilon phi chi psi omega "
         "Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega").split()

FUNCS = ("sin cos tan cot sec csc arcsin arccos arctan sinh cosh tanh "
         "exp log ln lim max min arg det dim gcd deg").split()


def _adapt(tex):
    """把论文 LaTeX 适配为 matplotlib mathtext 可解析的形式。"""
    s = tex

    # 去掉排版指令
    s = re.sub(r"\\tag\{[^}]*\}", "", s)
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = s.replace("\\nonumber", "").replace("\\notag", "")
    s = re.sub(r"\\(left|right|displaystyle|limits|nolimits)", "", s)
    s = re.sub(r"\\(big|Big|bigg|Bigg)\b", "", s)
    s = re.sub(r"\\[;,!]|\\quad|\\qquad|\\,", r"\\;", s)

    # 空白与换行（注意：不能在此处替换 \\\\，否则 cases 的行分隔符会丢失，
    # 必须等 latex_to_png 处理完 cases 环境后再替换）
    s = re.sub(r"[ \t]+", " ", s).strip()
    s = s.replace("\n", " ")
    # 去掉最外层的 $$ 或 $
    s = s.strip("$").strip()

    # \text{...} / \mathrm{...} / \operatorname{...} -> \mathrm{...}
    s = re.sub(r"\\(?:text|textrm|operatorname|mathrm)\{([^{}]*)\}",
               lambda m: r"\mathrm{" + m.group(1) + "}", s)

    return s


def _render_plain(body, out_path, fontsize, dpi):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${body}$", fontsize=fontsize)
    fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight",
                pad_inches=0.035, facecolor="white")
    plt.close(fig)


def _render_cases(left, rows, out_path, *, fontsize=13, dpi=220):
    """
    手工绘制分段函数：左边表达式 + 大花括号 + 右侧各行条件。

    matplotlib mathtext 不支持多行 array/cases 环境，故自行拼合：
    把花括号字符竖向拉伸，与逐行渲染的结果并排绘制。
    """
    from matplotlib import font_manager as fm
    from PIL import Image

    tmp = Path(out_path).parent
    tmp.mkdir(parents=True, exist_ok=True)

    # 逐行渲染
    row_imgs = []
    for k, r in enumerate(rows):
        rp = tmp / f"_row_{k}.png"
        _render_plain(r, rp, fontsize, dpi)
        row_imgs.append(rp)

    # 左侧表达式
    lp = tmp / "_left.png"
    if left.strip():
        _render_plain(left, lp, fontsize, dpi)

    def load(p):
        return Image.open(p).convert("RGBA")

    imgs = [load(p) for p in row_imgs]
    gap = int(dpi * 0.05)
    total_h = sum(im.height for im in imgs) + gap * (len(imgs) - 1)
    total_w = max(im.width for im in imgs)

    body = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 0))
    y = 0
    for im in imgs:
        body.paste(im, (0, y), im)
        y += im.height + gap

    # 花括号：用字体渲染后竖向拉伸到 body 高度
    brace_h = total_h
    brace_font = fm.FontProperties(family="DejaVu Serif", size=fontsize * 0.8)
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, "{", fontproperties=brace_font, fontsize=fontsize * 3.2)
    bp = tmp / "_brace.png"
    fig.savefig(str(bp), dpi=dpi, bbox_inches="tight", pad_inches=0.01,
                facecolor="white")
    plt.close(fig)
    brace = load(bp)
    new_w = max(1, int(brace.width * brace_h / brace.height * 0.55))
    brace = brace.resize((new_w, brace_h), Image.LANCZOS)

    left_img = load(lp) if lp.exists() else None

    pad = int(dpi * 0.06)
    W = (left_img.width + pad if left_img else 0) + brace.width + pad + body.width
    H = max(total_h, left_img.height if left_img else 0)
    canvas = Image.new("RGBA", (W, H), (255, 255, 255, 255))

    x = 0
    if left_img:
        canvas.paste(left_img, (x, (H - left_img.height) // 2), left_img)
        x += left_img.width + pad
    canvas.paste(brace, (x, (H - brace.height) // 2), brace)
    x += brace.width + pad
    canvas.paste(body, (x, (H - body.height) // 2), body)

    canvas.convert("RGB").save(str(out_path))
    return canvas.size


def latex_to_png(tex, out_path, *, fontsize=13, dpi=220):
    """把 LaTeX 公式渲染为 PNG，返回 (宽px, 高px) 或抛异常。"""
    body = _adapt(tex)

    # 分段函数单独处理（mathtext 不支持多行）
    m = re.search(r"\\begin\{cases\}(.*?)\\end\{cases\}", body, re.S)
    if m:
        left = body[:m.start()].strip()
        if left.endswith("="):
            left = left[:-1].strip()
        inner = m.group(1)
        rows = []
        for r in re.split(r"\\\\", inner):
            if not r.strip():
                continue
            cells = [c.strip() for c in r.split("&")]
            rows.append(r"\quad ".join(cells))
        # 左侧表达式与等号一起渲染，保留 "="
        left_full = body[:m.start()].strip()
        w, h = _render_cases(left_full, rows, out_path, fontsize=fontsize, dpi=dpi)
        return w, h

    _render_plain(body, out_path, fontsize, dpi)
    from PIL import Image
    with Image.open(out_path) as im:
        return im.size


def render_cache(tex, cache_dir, *, fontsize=13, dpi=220):
    """
    渲染公式并缓存（按内容哈希命名），返回图片路径。
    同一公式只渲染一次。
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(f"{tex}|{fontsize}|{dpi}".encode("utf-8")).hexdigest()[:16]
    p = cache_dir / f"eq_{key}.png"
    if not p.exists():
        latex_to_png(tex, p, fontsize=fontsize, dpi=dpi)
    return p


if __name__ == "__main__":
    import sys
    TESTS = [
        r"R(x,y)=\frac{\sum_{u,v}\big[T(u,v)-\bar{T}\big]\big[I(x+u,y+v)-\bar{I}_{x,y}\big]}"
        r"{\sqrt{\sum_{u,v}\big[T(u,v)-\bar{T}\big]^{2}}}",
        r"H(u,v)=\exp\left(-\frac{D^{2}(u,v)}{2D_0^{2}}\right)",
        r"\text{IoU}(A,B)=\frac{|A\cap B|}{|A\cup B|}",
        r"\sigma_k^{2} \leftarrow \sigma_k^{2} + \rho\,\big[(I_t-\mu_k)^{2} - \sigma_k^{2}\big]",
        r"M(x,y)=\begin{cases} 1, & \text{像素为前景}\\ 0, & \text{像素为背景} \end{cases}",
        r"O\Big(\sum_{l=0}^{L-1} \frac{HW}{4^{l}} \cdot M_{l} N_{l}\Big) \approx O\Big(HWMN \cdot \frac{4}{3}\Big)",
        r"(x,y)_{\text{orig}} = 2^{l}\,(x,y)_{l}",
        r"\mathcal{F}\{f(x,y) * h(x,y)\} = F(u,v)\cdot H(u,v)",
    ]
    out = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\_tools\_eqtest")
    out.mkdir(parents=True, exist_ok=True)
    bad = 0
    for k, t in enumerate(TESTS):
        try:
            w, h = latex_to_png(t, out / f"eq{k}.png")
            print(f"OK  {w:>4}x{h:<4} {t[:56]}")
        except Exception as e:
            bad += 1
            print(f"!!  {type(e).__name__}: {str(e)[:80]}")
            print(f"    源: {t[:80]}")
    print(f"\n自检: {'全部通过' if bad == 0 else str(bad) + ' 个失败'}")
    sys.exit(0 if bad == 0 else 1)
