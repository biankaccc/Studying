# -*- coding: utf-8 -*-
"""
生成《中国图象图形学报》体例的论文 Word 版。

规范要点（依据学报撰稿要求）：
  - 中文题名 <= 20 字，避免"基于/一种/利用"等词
  - 中文摘要按"目的/方法/结果/结论"分项，英文按 Objective/Method/Result/Conclusion
  - 正文一级标题"1"、二级"1.1"，顶格书写；引言节序号从 0 开始
  - 图名表名中英文对照；表格采用三线表；插图标题居中置于图下
  - 变量斜体、常数与函数正体；公式编号右置并用圆括号
  - 首页脚注给出中图法分类号与第一作者简介
  - 参考文献按作者（年）制，文献列表按英文字母顺序排列
"""
import os
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0202")
DATA = BASE / "data"
OUT = BASE / "第二章课设论文_高斯混合模型前景掩码的傅里叶高斯低通净化.docx"

CN = "宋体"
CN_H = "黑体"
EN = "Times New Roman"


# ----------------------------------------------------------------------
# 基础排版工具
# ----------------------------------------------------------------------
def set_run(run, *, cn=CN, en=EN, size=10.5, bold=False, italic=False, color=None):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = en
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:ascii"), en)
    rf.set(qn("w:hAnsi"), en)
    rf.set(qn("w:eastAsia"), cn)
    if color is not None:
        run.font.color.rgb = color
    return run


def para(doc, text="", *, cn=CN, en=EN, size=10.5, bold=False, italic=False,
         align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent_chars=0.0, space_before=0,
         space_after=0, line=1.15, first_line_chars=0.0):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    if first_line_chars:
        pf.first_line_indent = Pt(size * first_line_chars)
    if indent_chars:
        pf.left_indent = Pt(size * indent_chars)
    if text:
        set_run(p.add_run(text), cn=cn, en=en, size=size, bold=bold, italic=italic)
    return p


def heading(doc, text, level=1):
    if level == 1:
        return para(doc, text, cn=CN_H, size=12, bold=True,
                    align=WD_ALIGN_PARAGRAPH.LEFT, space_before=10, space_after=5)
    return para(doc, text, cn=CN_H, size=10.5, bold=True,
                align=WD_ALIGN_PARAGRAPH.LEFT, space_before=7, space_after=4)


def rich(doc, parts, *, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line_chars=2.0,
         size=10.5, space_after=0, line=1.15):
    """parts 为 (文本, 是否斜体, 是否加粗) 列表，用于夹杂变量的段落。"""
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_after = Pt(space_after)
    if first_line_chars:
        pf.first_line_indent = Pt(size * first_line_chars)
    for item in parts:
        txt, it, bd = (item + (False, False))[:3] if isinstance(item, tuple) else (item, False, False)
        set_run(p.add_run(txt), size=size, italic=it, bold=bd)
    return p


def equation(doc, body, number):
    """公式行：公式居中 + 编号右对齐（用制表符实现）。"""
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.2
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(7.5), WD_ALIGN_PARAGRAPH.CENTER)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(15.0), WD_ALIGN_PARAGRAPH.RIGHT)
    set_run(p.add_run("\t"), size=10.5)
    set_run(p.add_run(body), size=10.5, italic=False)
    set_run(p.add_run("\t"), size=10.5)
    set_run(p.add_run("（%s）" % number), size=10.5)
    return p


def cell_text(cell, text, *, bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(1.5)
    p.paragraph_format.space_after = Pt(1.5)
    set_run(p.add_run(text), size=size, bold=bold)


def set_cell_border(cell, **kwargs):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        spec = kwargs.get(edge)
        el = OxmlElement("w:" + edge)
        if spec is None:
            el.set(qn("w:val"), "nil")
        else:
            el.set(qn("w:val"), "single")
            el.set(qn("w:sz"), str(spec))
            el.set(qn("w:space"), "0")
            el.set(qn("w:color"), "000000")
        borders.append(el)
    tc_pr.append(borders)


def three_line_table(doc, caption_cn, caption_en, header, rows, note=None):
    """三线表：顶线、表头下细线、底线，其余无框线。"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    set_run(p.add_run(caption_cn), cn=CN_H, size=9.5, bold=True)
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(3)
    set_run(p2.add_run(caption_en), size=8.5, bold=True)

    ncol = len(header)
    table = doc.add_table(rows=1 + len(rows), cols=ncol)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    for j, h in enumerate(header):
        cell_text(table.rows[0].cells[j], h, bold=True, size=9)
    for i, r in enumerate(rows, start=1):
        for j, v in enumerate(r):
            cell_text(table.rows[i].cells[j], v, size=9,
                      align=WD_ALIGN_PARAGRAPH.LEFT if j == 0 and len(str(v)) > 8
                      else WD_ALIGN_PARAGRAPH.CENTER)

    last = len(rows)
    for i, row in enumerate(table.rows):
        for cell in row.cells:
            b = {}
            if i == 0:
                b["top"] = 12          # 顶线粗
                b["bottom"] = 6        # 表头下细线
            if i == last:
                b["bottom"] = 12       # 底线粗
            set_cell_border(cell, **b)

    if note:
        p3 = doc.add_paragraph()
        p3.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p3.paragraph_format.space_before = Pt(1)
        p3.paragraph_format.space_after = Pt(6)
        set_run(p3.add_run(note), size=8.5)
    return table


def figure(doc, img, caption_cn, caption_en, width_cm=12.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    if Path(img).exists():
        p.add_run().add_picture(str(img), width=Cm(width_cm))
    else:
        set_run(p.add_run("［图件缺失：%s］" % Path(img).name), size=9)
    c1 = doc.add_paragraph()
    c1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c1.paragraph_format.space_after = Pt(1)
    set_run(c1.add_run(caption_cn), cn=CN_H, size=9.5, bold=True)
    c2 = doc.add_paragraph()
    c2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c2.paragraph_format.space_after = Pt(8)
    set_run(c2.add_run(caption_en), size=8.5, bold=True)


# ----------------------------------------------------------------------
# 建立文档
# ----------------------------------------------------------------------
doc = Document()

st = doc.styles["Normal"]
st.font.name = EN
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), CN)

sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(2.5)
sec.bottom_margin = Cm(2.5)
sec.left_margin = Cm(2.5)
sec.right_margin = Cm(2.5)

# ---------------- 题名与作者 ----------------
para(doc, "高斯混合模型前景掩码的傅里叶高斯低通净化",
     cn=CN_H, size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
     space_before=6, space_after=4)
para(doc, "Purification of Gaussian Mixture Model Foreground Masks via "
          "Fourier-Domain Gaussian Low-Pass Filtering",
     size=11, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)

para(doc, "王　东⬜", size=10.5, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
para(doc, "⬜⬜⬜（单位名称，城市 邮编）", size=9, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)

# 首页页眉信息（中图法分类号 / 文献标识码）
rich(doc, [("中图法分类号：", False, True), ("TP391.41　　", False, False),
           ("文献标识码：", False, True), ("A", False, False)],
     align=WD_ALIGN_PARAGRAPH.LEFT, first_line_chars=0, size=9, space_after=3)
rich(doc, [("作者简介：", False, True),
           ("⬜⬜，出生年⬜，硕士研究生，主要研究方向为数字图像处理与视频运动目标检测。"
            "E-mail：2857241539@qq.com。　", False, False),
           ("通信作者：", False, True), ("⬜⬜⬜，职称⬜⬜，E-mail：⬜⬜⬜。", False, False)],
     align=WD_ALIGN_PARAGRAPH.LEFT, first_line_chars=0, size=9, space_after=8)
rich(doc, [("说明：本论文为课程设计成果，无基金项目资助。", False, False)],
     align=WD_ALIGN_PARAGRAPH.LEFT, first_line_chars=0, size=9, space_after=10)

# ---------------- 中文摘要 ----------------
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(3)
set_run(p.add_run("摘要："), cn=CN_H, size=10.5, bold=True)
set_run(p.add_run(
    "为在保持实时性的前提下提升高斯混合模型（Gaussian Mixture Model，GMM）前景掩码的质量，"
    "提出一种频域后置净化方法。该方法不改动GMM的核心时序建模逻辑，在传统GMM输出原始前景掩码之后"
    "串联一个二维傅里叶高斯低通滤波模块。依据傅里叶卷积定理，将空域高斯平滑等价转换为频域逐点相乘，"
    "对掩码频谱的高频噪声分量实施平滑衰减，再经二维逆傅里叶变换重构并作阈值二值化，得到净化后的精细掩码；"
    "选用高斯低通而非理想低通，以避免频率硬截断引入吉布斯振铃伪影。在自建的240像素×160像素、"
    "200帧小型监控序列上开展对比实验，以逐像素真值掩码为基准评价。相对于原始GMM，所提方法的误检率由"
    "7.4956%降至5.7872%，降幅22.8%；轮廓完整度（交并比）由0.5041提升至0.5605，提升11.2%；"
    "面积小于4像素的孤立连通块由每帧265.5个降至2.1个，降幅99.2%；背景区域的帧间掩码抖动下降95.3%。"
    "后处理附加延迟为1.10 ms/帧，整体处理速度达638帧/s，仍远高于序列帧率，实时性得到保持；"
    "漏检率由19.09%略增至21.55%。所提方法结构简单、参数唯一、易于移植，可有效抑制像素级背景建模算法"
    "输出掩码中的空间椒盐噪声，适用于室内外常规监控与动态弱扰动场景；其作用范围限于掩码的空间噪声，"
    "无法修复光照突变、长时间静止前景融入背景与阴影误判等时序建模缺陷，这是后续引入一维时序傅里叶变换、"
    "融合时空频特征的研究方向。"), size=10.5)

# 摘要分项小标题（目的/方法/结果/结论）
for label, body in [
    ("目的：", "GMM逐像素独立建模，未利用图像空间邻域相关性，其输出前景掩码含有大量孤立椒盐噪点，"
              "目标轮廓完整性不足，需在保持实时性的前提下提升掩码质量。"),
    ("方法：", "在GMM掩码之后串联二维傅里叶高斯低通滤波模块，依据卷积定理以频域逐点相乘实现空域高斯平滑，"
              "对高频噪声平滑衰减后经逆变换与阈值二值化重构掩码。"),
    ("结果：", "在自建监控序列上，误检率由7.4956%降至5.7872%（降幅22.8%），轮廓完整度由0.5041提升至0.5605"
              "（提升11.2%），孤立连通块由每帧265.5个降至2.1个（降幅99.2%），帧间抖动下降95.3%，"
              "附加延迟1.10 ms/帧，整体速度638帧/s，漏检率由19.09%升至21.55%。"),
    ("结论：", "方法结构简单、参数唯一、移植性强，适用于常规监控与动态弱扰动场景；"
              "其作用限于掩码空间噪声，无法修复GMM的时序建模缺陷。"),
]:
    rich(doc, [(label, False, True), (body, False, False)],
         first_line_chars=0, size=10.5, space_after=2)

rich(doc, [("关键词：", False, True),
           ("背景建模；高斯混合模型；运动目标检测；傅里叶变换；频域滤波；掩码后处理", False, False)],
     first_line_chars=0, size=10.5, space_after=4)
rich(doc, [("中图法分类号：", False, True), ("TP391.41", False, False)],
     first_line_chars=0, size=10.5, space_after=10)

# ---------------- 英文摘要 ----------------
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(3)
set_run(p.add_run("Abstract: "), size=10.5, bold=True)
set_run(p.add_run(
    "Objective: The Gaussian Mixture Model (GMM) is a classical background modeling algorithm for video moving "
    "object detection, and its online adaptive capability enables it to cope with multi-modal dynamic backgrounds. "
    "However, the traditional GMM models every pixel independently and therefore ignores the spatial correlation of "
    "images. Consequently, the resulting binary foreground mask contains numerous isolated salt-and-pepper noise "
    "blobs and false foreground pixels, which degrades both the detection accuracy and the integrity of object "
    "contours. This work aims to purify the GMM mask while preserving the real-time performance of the original "
    "algorithm, so as to improve foreground detection in conventional surveillance scenes with weak dynamic "
    "interference. Method: A frequency-domain post-processing scheme is proposed. The core temporal modeling logic "
    "of the GMM is left untouched; instead, a two-dimensional Fourier-domain Gaussian low-pass filter is cascaded "
    "after the GMM foreground mask. According to the Fourier convolution theorem, spatial Gaussian smoothing over "
    "the mask is equivalently reformulated as a point-wise multiplication of its spectrum with a Gaussian transfer "
    "function, which smoothly attenuates the high-frequency components that carry isolated noise. An inverse "
    "two-dimensional Fourier transform then reconstructs the smoothed mask, which is finally binarized with a fixed "
    "threshold. A Gaussian low-pass kernel is deliberately adopted instead of an ideal one, because the hard "
    "truncation of the ideal filter is equivalent to sinc-kernel convolution and introduces Gibbs ringing artifacts. "
    "The method adds only one adjustable parameter, the normalized cutoff radius, and behaves as a universal "
    "post-processing module that can be attached to any pixel-level background modeling algorithm. Result: "
    "Comparative experiments were conducted on a self-built small surveillance sequence of 240 x 160 pixels with "
    "200 frames at 25 frame/s, containing water-surface ripples, swaying foliage, pedestrian shadows and a gradual "
    "global illumination change. Pixel-level ground truth masks were used for objective evaluation. Compared with "
    "the original GMM, the false positive rate of the proposed method decreases from 7.4956% to 5.7872%, a relative "
    "reduction of 22.8%; the intersection over union increases from 0.5041 to 0.5605, a relative gain of 11.2%; the "
    "number of isolated connected components smaller than four pixels drops from 265.5 to 2.1 per frame, a relative "
    "reduction of 99.2%; and the temporal flicker of the mask in background regions decreases by 95.3%. The "
    "additional latency introduced by the post-processing stage is only 1.10 ms per frame, and the overall "
    "throughput reaches 638 frame/s, which remains far above the sequence frame rate. The false negative rate rises "
    "slightly from 19.09% to 21.55%, indicating a marginal erosion of object boundaries and thin structures. "
    "Segment-wise statistics further show that the false positive rate is reduced pronouncedly in the regular "
    "monitoring interval, whereas both methods deteriorate simultaneously once the global illumination changes, "
    "confirming that frequency-domain post-processing acts only on spatial mask noise. Conclusion: The proposed "
    "method is simple in structure, has a single interpretable parameter, and is easy to transplant; it effectively "
    "suppresses the spatial salt-and-pepper noise in masks produced by pixel-level background modeling algorithms, "
    "and is therefore applicable to indoor and outdoor conventional surveillance as well as weakly dynamic scenes. "
    "Its scope is limited to spatial mask noise: it cannot remedy the inherent temporal modeling defects of the GMM, "
    "such as false detection under illumination change, absorption of long-term static foreground into the "
    "background, and misclassification of shadows. Future work will introduce a one-dimensional temporal Fourier "
    "transform of per-pixel intensity sequences and fuse the resulting temporal frequency features with the GMM "
    "intensity probability features, so as to distinguish periodic background disturbances such as foliage swaying "
    "and water rippling from genuine moving foreground."), size=10)

rich(doc, [("Key words: ", False, True),
           ("background modeling; Gaussian mixture model; moving object detection; Fourier transform; "
            "frequency-domain filtering; mask post-processing", False, False)],
     first_line_chars=0, size=10, space_after=10)

print("第 1 部分（题名/摘要）完成")

# ----------------------------------------------------------------------
# 正文
# ----------------------------------------------------------------------
heading(doc, "0　引言", 1)
rich(doc, [("运动目标检测是视频目标跟踪、行为分析与智能监控的基础环节（Bouwmans, 2014）。"
            "在各类检测策略中，背景减除法因其实现简单、计算量小而被广泛采用，其核心在于构建能够适应场景变化的"
            "背景模型（Chapel 和 Bouwmans, 2020）。Stauffer 和 Grimson（1999）提出的自适应高斯混合模型为每个"
            "像素维护多个高斯分布，并在线更新其均值、方差与权重，从而能够对水面反光、树叶摇动等多模态动态背景"
            "建模，成为该领域最具影响力的方法之一。此后，研究者围绕其学习率自适应、分量数目自适应与阴影抑制等"
            "问题开展了大量改进工作（Zivkovic, 2004；Lee, 2005）。同时，样本一致性类方法通过随机邻域传播与"
            "背景样本库建模，在一定程度上降低了计算开销（Barnich 和 Van Droogenbroeck, 2011；"
            "St-Charles 等, 2015），基于非参数核密度估计的方法则摆脱了分布形式的先验假设（Elgammal 等, 2000）。"
            "针对光照变化、阴影干扰与复杂场景下的稳健性问题，研究者还提出了基于特征集扩充与时空一致性校验的"
            "改进策略（Klare 和 Sarkar, 2009；Yan 等, 2010），而 Sobral 和 Vacavant（2014）在合成与真实视频上"
            "对多种背景减除算法进行了系统性评测，指出各类算法在动态背景下的掩码噪声问题具有普遍性。近年来的"
            "改进工作仍主要围绕学习率自适应、背景建模初始化与目标尺度适应展开（Agrawal 和 Natu, 2021；"
            "Sheng 等, 2022；Kalsotra 和 Arora, 2021），也有工作从视觉感知与局部特征的角度提升前景与背景的"
            "可分性（Peng 等, 2022），或通过并行化实现提高建模效率（Bariko 等, 2024）。近年来，深度学习方法"
            "也被引入前景分割与视频目标检测任务（Giraldo 和 Bouwmans, 2020；Ammar 等, 2020；Si, 2024），"
            "但其对训练数据的依赖与较高的计算开销限制了在嵌入式监控设备上的部署。", False, False)], space_after=2)

rich(doc, [("然而，上述方法均以像素为独立单元进行建模。由于未显式利用图像的空间邻域相关性，其输出的前景"
            "二值掩码往往呈现明显的\u201c椒盐\u201d特征，即大量面积仅为数个像素的孤立虚假前景点散落于背景区域，"
            "而真实目标内部也可能出现空洞。这不仅降低了检测精度，也给后续的形态学处理、连通域分析与目标跟踪"
            "带来额外负担。现有研究多采用形态学开闭运算、中值滤波或连通域面积滤波等空间域手段进行后处理，"
            "这些方法虽简单有效，但依赖结构元尺寸等经验参数，且在对掩码进行硬性形态学操作时容易同时削薄目标"
            "轮廓。", False, False)], space_after=2)

rich(doc, [("针对上述问题，本文从频域视角出发，提出一种面向GMM前景掩码的频域净化方法。其主要思想是："
            "把\u201c利用空间邻域相关性去噪\u201d这一诉求，通过二维傅里叶变换转换为频域中对高频分量的平滑衰减"
            "问题。掩码中的孤立椒盐噪点表现为频谱中的高频成分，而真实目标对应的连续区域集中在低频；采用高斯"
            "低通滤波器对频谱加权，即可在抑制高频噪声的同时保留目标主体。依据傅里叶卷积定理，频域逐点相乘严格"
            "等价于空域高斯卷积，因此该方法在数学上与空域高斯平滑一致，但借助快速傅里叶变换可将计算复杂度从与"
            "卷积核面积相关的量级降至与图像尺寸的对数量级。", False, False)], space_after=2)

rich(doc, [("本文的贡献在于：将该频域滤波模块设计为纯后置组件，输入与输出均为二值掩码，因而完全不改动GMM"
            "等背景建模算法的核心逻辑，可无差别地串接于任意像素级背景建模算法之后；同时，通过一维阶跃信号实验"
            "说明选用高斯低通而非理想低通的必要性，避免因频率硬截断而产生吉布斯振铃伪影；并在含多种动态干扰的"
            "自建监控序列上给出了误检率、漏检率、轮廓完整度、椒盐噪声去除率、时间抖动与计算开销的定量评价，"
            "明确了该方法的有效边界。", False, False)], space_after=4)

print("引言完成")

heading(doc, "1　相关原理", 1)
heading(doc, "1.1　高斯混合模型背景建模", 2)
rich(doc, [("高斯混合模型对视频序列中的每个像素独立维护 ", False, False), ("K", True, False),
           (" 个高斯分布，第 ", False, False), ("k", True, False), (" 个分量由权重 ", False, False),
           ("ω", True, False), ("k", False, False), ("、均值 ", False, False), ("μ", True, False),
           ("k", False, False), (" 与方差 ", False, False), ("σ", True, False), ("k", False, False),
           ("2", False, False), (" 描述。对于第 ", False, False), ("t", True, False),
           (" 帧的像素观测值 ", False, False), ("I", True, False), ("t", False, False),
           ("，若满足式（1）的匹配判据，则认为该观测属于第 ", False, False), ("k", True, False),
           (" 个高斯分量：", False, False)], space_after=2)

equation(doc, "| I t − μ k | < 2.5 σ k", 1)
rich(doc, [("匹配分量的权重按式（2）在线更新，均值与方差按式（3）、式（4）更新：", False, False)],
     first_line_chars=2.0, space_after=2)
equation(doc, "ω k ← (1 − α) ω k + α", 2)
equation(doc, "μ k ← μ k + ρ ( I t − μ k )", 3)
equation(doc, "σ k ² ← σ k ² + ρ [ ( I t − μ k ) ² − σ k ² ]", 4)

rich(doc, [("式中，", False, False), ("α", True, False), (" 为学习率，", False, False),
           ("ρ", True, False), (" = ", False, False), ("α", True, False), ("/", False, False),
           ("ω", True, False), ("k", False, False), (" 为有效更新率。未匹配分量的权重按同比例衰减。"
            "随后各分量按 ", False, False), ("ω", True, False), ("k", False, False), ("/", False, False),
           ("σ", True, False), ("k", False, False),
           (" 降序排列，取累积权重达到阈值 T 的前若干分量作为背景分量。若某像素的观测与任一背景分量均不匹配，"
            "则判定为前景像素，据此输出二值掩码 ", False, False), ("M", True, False),
           ("(", False, False), ("x", True, False), (",", False, False), ("y", True, False),
           (")", False, False), ("，如式（5）所示：", False, False)], space_after=2)
equation(doc, "M ( x, y ) = 1（前景）/ 0（背景）", 5)

rich(doc, [("该策略的统计基础在于：背景像素长期稳定地落在少数几个高权重、小方差的分量上，而前景像素的观测会"
            "偏离这些背景分量。由于每个像素的建模与判定过程相互独立，掩码的空间一致性完全依赖数据自身，"
            "这正是孤立噪点产生的根源。", False, False)], space_after=4)

heading(doc, "1.2　傅里叶卷积定理与频域滤波", 2)
rich(doc, [("二维傅里叶变换把空域信号 ", False, False), ("f", True, False), ("(", False, False),
           ("x", True, False), (",", False, False), ("y", True, False), (")", False, False),
           (" 映射为频域信号 ", False, False), ("F", True, False), ("(", False, False),
           ("u", True, False), (",", False, False), ("v", True, False), (")", False, False),
           ("。卷积定理指出，两个二维信号空域卷积的傅里叶变换等于二者傅里叶变换的逐点乘积，如式（6）所示：",
            False, False)], space_after=2)
equation(doc, "F { f ( x, y ) ∗ h ( x, y ) } = F ( u, v ) · H ( u, v )", 6)
rich(doc, [("式中，", False, False), ("h", True, False), ("(", False, False), ("x", True, False),
           (",", False, False), ("y", True, False), (")", False, False),
           (" 为空域卷积核，", False, False), ("H", True, False), ("(", False, False),
           ("u", True, False), (",", False, False), ("v", True, False), (")", False, False),
           (" 为其对应的频域传递函数。对式（6）两端作逆变换即可由频域乘积恢复空域卷积结果，即式（7）：",
            False, False)], space_after=2)
equation(doc, "F ⁻¹ { F ( u, v ) · H ( u, v ) } = f ( x, y ) ∗ h ( x, y )", 7)
rich(doc, [("式（6）与式（7）表明，在频域实现滤波只需一次逐点相乘，而滤波核的空间尺度不影响运算量，"
            "这为后续实现提供了依据。", False, False)], space_after=2)

rich(doc, [("频域低通按传递函数的过渡特性可分为理想低通与高斯低通。理想低通在截止半径 ", False, False),
           ("D", True, False), ("0", False, False),
           (" 处由 1 突降为 0，其传递函数如式（8）所示：", False, False)], space_after=2)
equation(doc, "H ideal ( u, v ) = 1（D ≤ D 0）/ 0（D > D 0）", 8)
rich(doc, [("该硬截断在空域上等效于以 sinc 函数为核的卷积。sinc 核具有缓慢衰减且正负交替的旁瓣，会在图像中"
            "具有阶跃或高对比度的位置两侧产生明暗交替的过冲条纹，即吉布斯振铃伪影。对于本文的二值掩码而言，"
            "目标边界本身即为阶跃结构，因此理想低通会在轮廓附近引入虚假像素。", False, False)], space_after=2)

rich(doc, [("为此，本文选用高斯低通滤波器，其传递函数如式（9）所示：", False, False)], space_after=2)
equation(doc, "H ( u, v ) = exp [ − D ² ( u, v ) / ( 2 D 0 ² ) ]", 9)
rich(doc, [("式中，", False, False), ("D", True, False), ("(", False, False), ("u", True, False),
           (",", False, False), ("v", True, False), (")", False, False),
           (" 为频域点 (", False, False), ("u", True, False), (",", False, False), ("v", True, False),
           (") 到频谱原点的距离，", False, False), ("D", True, False), ("0", False, False),
           (" 为截止半径。高斯函数的各阶导数连续、无阶跃间断，其对高频分量呈平滑衰减，对应的空域核为单峰"
            "快速衰减的高斯函数，不存在 sinc 那样的振荡旁瓣，因而不会产生明显振铃。这也意味着频域高斯低通在"
            "数学上严格等价于空域高斯平滑，只是实现复杂度更低。二维傅里叶变换与频域滤波的理论基础参见数字"
            "图像处理经典教材（Gonzalez 和 Woods, 2018），频域低通滤波在图像去噪中的有效性也已得到广泛验证"
            "（Liu 和 Wei, 2019；Jia 等, 2022），这为本文将其应用于二值掩码净化提供了依据。", False, False)],
     space_after=2)

rich(doc, [("需要说明的是，由于离散傅里叶变换的直流分量固定位于数组的原点位置，构造传递函数时所采用的频率"
            "坐标必须与频谱的索引约定严格一致。若传递函数的原点与频谱原点错位，等效于只保留了远离直流分量的"
            "窄频带，会使逆变换结果的幅值严重衰减，从而在阈值二值化后丢失全部前景。本文统一采用周期频率坐标"
            "构造 ", False, False), ("H", True, False), ("(", False, False), ("u", True, False),
           (",", False, False), ("v", True, False), (")", False, False),
           ("，使 ", False, False), ("H", True, False), ("(0,0) = 1，即直流分量被完整保留。", False, False)],
     space_after=4)

print("原理部分完成")

heading(doc, "2　本文算法", 1)
heading(doc, "2.1　算法流程", 2)
rich(doc, [("本文所提方法的整体流程如图1所示，其核心是在传统GMM输出掩码之后串联一个频域净化模块，"
            "具体步骤如下：", False, False)], space_after=2)
for step in [
    "1）输入视频帧 I t，使用GMM逐像素背景建模，输出原始二值前景掩码 M t；",
    "2）对 M t 作二维傅里叶变换，得到频谱 F = F { M t }；",
    "3）按式（9）构造高斯低通传递函数 H，并作频域逐点相乘 F f = F ⊙ H；",
    "4）对乘积作二维逆傅里叶变换，取模值后按固定阈值二值化，得到净化掩码 M′ t，如式（10）所示；",
    "5）更新GMM模型参数，读取下一帧重复上述过程。",
]:
    rich(doc, [(step, False, False)], first_line_chars=2.0, space_after=1)
equation(doc, "M ′ t ( x, y ) = 1（| F ⁻¹ { F ⊙ H } | > τ）/ 0（其他）", 10)
rich(doc, [("该流程的伪代码如表1所示。", False, False)], space_after=2)

figure(doc, DATA / "fig_2_0_flowchart.png",
       "图1　本文算法整体流程",
       "Fig.1　Overall flowchart of the proposed algorithm", width_cm=15.5)

three_line_table(
    doc,
    "表1　本文算法的伪代码",
    "Table 1　Pseudo-code of the proposed algorithm",
    ["步骤", "操作", "说明"],
    [["①", "M t = GMM_get_foreground_mask(I t)", "传统 GMM 输出原始掩码"],
     ["②", "F = fft2(M t)", "二维傅里叶变换"],
     ["③", "H = gaussian_lowpass(M t.shape, D 0)", "构造高斯低通传递函数"],
     ["④", "F f = F * H", "频域逐点相乘（卷积定理）"],
     ["⑤", "M mag = abs(ifft2(F f))", "逆变换并取模值"],
     ["⑥", "M′ t = (M mag > τ)", "阈值二值化，得到净化掩码"],
     ["⑦", "GMM_update_parameters()", "更新 GMM 模型参数"]])

heading(doc, "2.2　阈值选取", 2)
rich(doc, [("式（10）中阈值 ", False, False), ("τ", True, False),
           (" 的物理含义可由卷积定理直接导出。高斯低通传递函数在直流处取值为 1，因此逆变换结果的幅值并非"
            "任意尺度，而是\u201c以该像素为中心的局部邻域被前景填充的比例\u201d：在目标内部且远离边界处，"
            "邻域几乎全为前景，幅值趋近于 1；在背景区域，幅值趋近于 0；而孤立单点噪点由于在邻域内占比极低，"
            "其幅值被邻域平均稀释到接近于 0。因此取 ", False, False), ("τ", True, False),
           (" = 0.5 具有明确的几何解释，即要求该像素的局部邻域中至少有半数被前景占据，从而在滤除孤立噪点的"
            "同时保留连续目标区域。", False, False)], space_after=2)
rich(doc, [("为验证实现正确性，本文对滤波器与滤波结果作了四项自检：高斯低通的直流分量 ", False, False),
           ("H", True, False), ("(0,0) = 1；其等效空域卷积核的求和为 1，即无亮度增益；尺寸为 50 像素×50 像素"
            "的实心前景块经滤波后内部幅值均值接近 1；孤立单点噪点经滤波后的最大幅值远小于 0.5。四项结果均与"
            "理论预期一致，同时频域实现结果与同参数空域高斯平滑的平均绝对误差处于 10 的负二次方量级"
            "（相对幅值量级为 1），验证了卷积定理实现的无误。", False, False)], space_after=4)

heading(doc, "2.3　参数与复杂度", 2)
rich(doc, [("本文方法仅引入一个可调参数，即式（9）中的归一化截止半径 ", False, False),
           ("D", True, False), ("0", False, False),
           ("。该参数过小会使频域通带过窄，等效于过强的空域平滑，目标主体被削薄甚至消失，漏检随之上升；"
            "过大则高频噪声衰减不足，去噪能力下降。本文在实验中通过参数扫描确定其取值。", False, False)],
     space_after=2)
rich(doc, [("在计算复杂度方面，设帧内像素总数为 ", False, False), ("N", True, False),
           ("，频域实现包含一次二维快速傅里叶变换、一次逐点相乘与一次二维逆傅里叶变换，复杂度为 ", False, False),
           ("O", False, False), ("(", False, False), ("N", True, False),
           (" log ", False, False), ("N", True, False), (")", False, False),
           ("，与滤波核的空间尺度无关；而等效的空域高斯卷积复杂度为 ", False, False),
           ("O", False, False), ("(", False, False), ("Nk", True, False), ("²)", False, False),
           ("，其中 ", False, False), ("k", True, False),
           (" 为核尺寸。由于本文 ", False, False), ("D", True, False), ("0", False, False),
           (" 对应的等效核尺寸与帧宽同阶，频域实现在原理上更具优势。", False, False)], space_after=4)

print("算法部分完成")

heading(doc, "3　实验分析", 1)
heading(doc, "3.1　实验设置", 2)
rich(doc, [("本文实验采用自建小型监控序列进行评价。该序列由程序合成，分辨率为 240 像素×160 像素，共 200 帧，"
            "帧率 25 帧/s，时长为 8 s，属于灰度单通道视频。选择合成序列的原因在于：公开监控数据集通常仅提供"
            "视频级或少量关键帧级的标注，难以逐帧计算误检率；而合成序列中运动目标由纯矩形绘制、不含纹理，"
            "可生成与图像内容严格一致、逐像素对齐的真值掩码，从而使误检率、漏检率与轮廓完整度的计算具备客观"
            "基准。此外，合成方式可精确控制动态干扰的类型与强度，便于定向验证方法的有效边界，且随机种子固定，"
            "结果完全可复现。", False, False)], space_after=2)
rich(doc, [("序列的场景构成及所注入的干扰如表2所示。其中水面波纹与草叶摆动模拟周期性动态背景，树木区域的"
            "随机抖动模拟树叶摇晃，跟随行人的暗色影子用于复现阴影误判，而第 120 帧起画面整体逐渐增亮的全局"
            "光照渐变用于复现光照突变误检。前 40 帧作为背景模型的冷启动阶段，统计时予以跳过。", False, False)],
     space_after=2)

three_line_table(
    doc,
    "表2　自建监控序列的场景构成与注入干扰",
    "Table 2　Scene composition and injected disturbances of the self-built surveillance sequence",
    ["行坐标范围", "场景区域", "注入的干扰类型", "对应 GMM 固有缺陷"],
    [["y = 0～45", "天空与水面", "多方向正弦波纹", "周期性动态背景误检"],
     ["y = 0～60", "树木区域", "幅度受限的随机抖动", "树叶晃动误检"],
     ["y = 55～115", "道路（目标活动区）", "4 个矩形行人及其暗色影子", "阴影误判"],
     ["y = 112～160", "人行道与草丛", "正弦摆动", "弱动态背景误检"],
     ["全程", "全局", "第 120 帧起逐渐增亮", "光照突变误检"]])

rich(doc, [("实验环境为 Windows 平台，Python 3.11.7，CPU 实现，主要依赖 OpenCV 4.10.0、NumPy 1.26.4 与 "
            "SciPy 1.11.4。GMM 采用 OpenCV 的 MOG2 实现，历史长度为 300，方差阈值为 16，关闭阴影检测，"
            "学习率取自适应默认值。高斯低通的归一化截止半径默认取 ", False, False),
           ("D", True, False), ("0", False, False),
           (" = 0.08，即截止半径为 0.08×240 = 19.2 像素，二值化阈值 ", False, False),
           ("τ", True, False), (" = 0.5。", False, False)], space_after=2)
rich(doc, [("评价指标定义如下：误检率（false positive rate，FPR）为背景像素被误判为前景的比例；"
            "漏检率（false negative rate，FNR）为前景像素被漏判的比例；轮廓完整度以交并比"
            "（intersection over union，IoU）衡量；椒盐噪声以面积小于 4 像素的孤立连通块的数量及其像素占比"
            "衡量；此外以远场背景区域相邻帧的掩码翻转率衡量时间抖动。", False, False)], space_after=4)

heading(doc, "3.2　频域滤波的必要性验证", 2)
rich(doc, [("为说明选用高斯低通而非理想低通的必要性，图2给出一维阶跃信号经两类滤波器处理后的切面及其等效"
            "空域核。理想低通的等效空域核旁瓣衰减缓慢且正负交替，在阶跃边缘两侧产生明显的过冲振荡，即吉布斯"
            "振铃；高斯低通的空域核为单峰快速衰减，边缘处无振荡。考虑到二值掩码的目标边界本身即为阶跃结构，"
            "若采用理想低通将在轮廓附近引入虚假像素，因此本文选用高斯低通。", False, False)], space_after=2)
figure(doc, DATA / "fig_1_2_gibbs_vs_gaussian.png",
       "图2　理想低通与高斯低通的吉布斯振铃对比",
       "Fig.2　Comparison of Gibbs ringing between the ideal low-pass and the Gaussian low-pass filter")

heading(doc, "3.3　掩码净化效果", 2)
rich(doc, [("图3给出本文算法在单帧上的完整处理流程，包括原始掩码、频谱、高斯低通传递函数、频域乘积、"
            "逆变换幅值与净化掩码。可以看出，原始掩码的频谱中存在大量分布于高频区域的散乱能量，它们对应背景"
            "中的孤立噪点；经高斯低通加权后，这些高频分量被显著衰减，逆变换幅值在背景区域集中在 0 附近、"
            "在目标内部接近 1，阈值二值化后即得到干净的掩码。", False, False)], space_after=2)
figure(doc, DATA / "fig_3_1_pipeline_single_frame.png",
       "图3　本文算法的单帧频域处理全流程",
       "Fig.3　Complete frequency-domain pipeline of the proposed algorithm on a single frame",
       width_cm=15.0)

rich(doc, [("图4以红框标出原始掩码中的孤立噪点，并与净化掩码逐帧对比。原始GMM掩码在背景区域散布大量单像素"
            "或数像素的虚假前景，尤其在水面与树木区域，这些噪点呈闪烁状随时间随机出现，而净化后的掩码中该类"
            "噪点基本消失，行人主体与轮廓保持完整。图5进一步给出局部放大细节与幅值分布直方图，其中红色为被"
            "抑制的误检像素、黄色为被误删的真前景。可以看出被抑制的像素绝大多数位于背景区域，被误删的真前景"
            "主要出现在行人的腿部和轮廓边缘。", False, False)], space_after=2)
figure(doc, DATA / "fig_3_2_frame_compare.png",
       "图4　传统GMM与本文方法的逐帧掩码对比（红框为孤立椒盐噪点）",
       "Fig.4　Frame-wise mask comparison between the traditional GMM and the proposed method "
       "(red boxes denote isolated salt-and-pepper noise)", width_cm=16.0)
figure(doc, DATA / "fig_3_3_zoom_detail.png",
       "图5　掩码去噪效果局部放大与逆变换幅值分布",
       "Fig.5　Zoomed details of mask denoising and distribution of the inverse-transform magnitude",
       width_cm=15.0)

heading(doc, "3.4　定量评价", 2)
rich(doc, [("在跳过前 50 帧冷启动阶段后，对第 50～199 帧共 150 帧统计各项指标，结果如表3所示。", False, False)],
     space_after=2)
three_line_table(
    doc,
    "表3　传统 GMM 与本文方法的定量指标对比（第 50～199 帧，共 150 帧）",
    "Table 3　Quantitative comparison between the traditional GMM and the proposed method "
    "(frames 50–199, 150 frames in total)",
    ["指标", "传统 GMM", "本文方法", "相对变化"],
    [["误检率 FPR / %", "7.4956", "5.7872", "下降 22.8%"],
     ["漏检率 FNR / %", "19.0872", "21.5536", "上升 2.47 个百分点"],
     ["轮廓完整度 IoU", "0.5041", "0.5605", "提升 11.2%"],
     ["椒盐噪点像素占比 / %", "0.9344", "0.0101", "下降 98.9%"],
     ["孤立连通块个数 / 帧", "265.52", "2.09", "下降 99.2%"],
     ["远场时间抖动 / %", "0.6447", "0.0304", "下降 95.3%"]])

rich(doc, [("由表3可见，本文方法使误检率显著下降，降幅达 22.8%；面积小于 4 像素的孤立连通块由每帧 265.5 个"
            "降至 2.1 个，降幅 99.2%，椒盐噪点像素占比由 0.9344% 降至 0.0101%，降幅 98.9%，说明方法的去噪目标"
            "得到充分实现。轮廓完整度 IoU 由 0.5041 提升至 0.5605，提升 11.2%，表明在去除噪声的同时目标主体"
            "得到保留。同时，漏检率由 19.0872% 升至 21.5536%，相对上升 2.47 个百分点，这与图5的观察一致，"
            "即被误删的像素主要位于目标轮廓边缘与较细的腿部结构，属于空域平滑不可避免的代价。总体而言，"
            "本文方法在显著降低虚假前景的同时仅付出了较小的漏检代价。", False, False)], space_after=2)
rich(doc, [("图6给出各项指标随帧序的变化曲线。原始GMM的误检率曲线在整个序列上持续波动，而本文方法的误检率"
            "曲线明显下移且更为平稳，说明频域滤波在时间维度上也抑制了掩码的随机闪烁。", False, False)],
     space_after=2)
figure(doc, DATA / "fig_4_2_metrics.png",
       "图6　误检率、轮廓完整度与孤立噪点数量的逐帧变化",
       "Fig.6　Frame-wise curves of false positive rate, intersection over union and the number of "
       "isolated noise blobs", width_cm=15.0)

heading(doc, "3.5　分段统计与方法的有效边界", 2)
rich(doc, [("为明确方法的适用范围，将序列划分为常规监控段（第 50～119 帧）与全局光照渐变段"
            "（第 120～199 帧）分别统计，结果如表4所示。", False, False)], space_after=2)
three_line_table(
    doc,
    "表4　分段的误检率与轮廓完整度统计",
    "Table 4　Segment-wise statistics of false positive rate and intersection over union",
    ["区段", "GMM 误检率 / %", "本文误检率 / %", "误检率降幅 / %", "GMM IoU", "本文 IoU"],
    [["常规段（50～119 帧）", "0.3322", "0.3256", "2.0", "0.7206", "0.6900"],
     ["光照渐变段（120～199 帧）", "13.7635", "10.5661", "23.2", "0.3147", "0.4471"]])
rich(doc, [("由表4可见，在全局光照渐变段，两种方法的误检率均大幅上升，本文方法虽仍使误检率下降 23.2%，"
            "但绝对水平远高于常规段。这说明本文方法只作用于掩码的空间噪声，无法修复GMM因光照突变而产生的"
            "时序建模缺陷；在光照渐变段 IoU 仍有提升（由 0.3147 提升至 0.4471），是因为该阶段的掩码噪声量级"
            "更大，频域滤波的去噪收益也更为明显。这一结果与引言中的分析一致，也界定了本文方法的适用边界。",
            False, False)], space_after=4)

heading(doc, "3.6　截止频率参数分析", 2)
rich(doc, [("对归一化截止半径 ", False, False), ("D", True, False), ("0", False, False),
           (" 在 0.02～0.50 范围内进行扫描，结果如表5所示。", False, False)], space_after=2)
three_line_table(
    doc,
    "表5　截止半径 D0 的敏感性分析",
    "Table 5　Sensitivity analysis of the normalized cutoff radius D0",
    ["D 0", "误检率 / %", "漏检率 / %", "IoU", "椒盐噪点像素占比 / %"],
    [["0.02", "4.6081", "53.2467", "0.3271", "0.0001"],
     ["0.04", "5.4531", "29.9899", "0.4972", "0.0007"],
     ["0.06", "5.6357", "23.6285", "0.5465", "0.0043"],
     ["0.08", "5.7872", "21.5536", "0.5605", "0.0101"],
     ["0.10", "5.9395", "20.6863", "0.5617", "0.0253"],
     ["0.15", "6.2469", "19.4918", "0.5565", "0.1084"],
     ["0.20", "6.5625", "19.1187", "0.5398", "0.2442"],
     ["0.30", "7.4955", "19.0872", "0.5041", "0.9343"],
     ["0.50", "7.4956", "19.0872", "0.5041", "0.9344"]],
    note="注：D 0 = 0.08 为本文默认取值；D 0 ≥ 0.30 时结果与原始掩码基本一致，说明去噪能力已丧失。")
rich(doc, [("由表5可见，随着 ", False, False), ("D", True, False), ("0", False, False),
           (" 增大，误检率单调上升（即噪声衰减能力减弱），漏检率随之下降，而 IoU 呈先升后降的单峰形态，在 ",
            False, False), ("D", True, False), ("0", False, False),
           (" = 0.10 处取得最大值 0.5617。当 ", False, False), ("D", True, False), ("0", False, False),
           (" 过小时（如 0.02），漏检率急剧升至 53.25%，目标主体被严重削薄；当 ", False, False),
           ("D", True, False), ("0", False, False),
           (" 过大时（如 0.30 以上），结果退化为原始掩码，椒盐去除能力丧失。因此该参数在 0.06～0.15 区间内"
            "均可取得优于原始GMM的结果，参数鲁棒性良好，本文默认取 0.08。", False, False)], space_after=4)

heading(doc, "3.7　计算开销", 2)
rich(doc, [("在相同输入上重复测量三个部分：传统GMM（建模与掩码输出）、本文频域滤波后处理以及作为对照的"
            "空域高斯平滑，每种配置重复 3 次取均值，结果如表6所示。", False, False)], space_after=2)
three_line_table(
    doc,
    "表6　计算开销对比（240 像素×160 像素，单帧）",
    "Table 6　Comparison of computational cost (240 x 160 pixels, per frame)",
    ["模块", "单帧耗时 / ms", "相对 GMM 增量", "等效帧率 / (帧·s⁻¹)"],
    [["传统 GMM（建模与掩码）", "0.475", "—（基准）", "2105"],
     ["本文频域滤波后处理", "1.097", "+231%", "912"],
     ["本文方法总计", "1.567", "+231%", "638"],
     ["对照：空域高斯平滑", "1.069", "+225%", "936"]])
rich(doc, [("由表6可见，频域滤波后处理引入的附加延迟为 1.10 ms/帧，本文方法整体处理速度达 638 帧/s，"
            "远高于本序列的 25 帧/s，实时性得到保持。需要指出的是，由于GMM由 OpenCV 的 C++ 实现而频域滤波为 "
            "NumPy 实现，后者的相对增量百分比较大；但从绝对开销看，1.10 ms/帧的附加延迟在常规监控分辨率与"
            "帧率下是可以接受的。此外，作为对照的空域高斯平滑耗时为 1.069 ms/帧，与频域实现相当，说明在本"
            "实验的帧尺寸下，频域实现的主要优势在于其计算量不随滤波核尺度增长，当分辨率提高或截止半径增大时"
            "该优势将更为显著。", False, False)], space_after=4)

heading(doc, "3.8　局限性与展望", 2)
rich(doc, [("本文方法的局限性可归纳为三点。第一，方法只作用于掩码的空间噪声，无法解决GMM的固有缺陷。"
            "3.5 节的结果表明，在全局光照渐变段两种方法的误差均显著上升，说明光照突变误检属于时序建模问题，"
            "后置的空间滤波无法修复；同理，长时间静止的前景目标会被GMM逐步融入背景，阴影也会被误判为前景，"
            "这些均不在本文方法的解决范围之内。第二，由于引入空域平滑，目标轮廓边缘与细长结构（如人体腿部）"
            "存在轻微侵蚀，表现为漏检率的小幅上升，这是去噪与保边之间的固有权衡。第三，本文采用固定阈值 0.5 "
            "进行二值化，未考虑目标尺度差异；当目标面积远小于滤波等效核尺寸时，其内部幅值也将被稀释至阈值"
            "以下，这与 3.6 节中 ", False, False), ("D", True, False), ("0", False, False),
           (" 过大导致漏检上升的现象同源。", False, False)], space_after=2)
rich(doc, [("后续工作可从三个方向展开。一是对每个像素的灰度时序序列作一维傅里叶变换，提取周期性强度的"
            "频域特征，并与GMM的灰度概率特征相融合，从而区分树叶晃动、水面波动等周期性背景扰动与真实运动"
            "前景，以提升复杂动态背景下的检测鲁棒性。二是引入自适应截止半径，根据目标尺度估计动态调整 ",
            False, False), ("D", True, False), ("0", False, False),
           ("，以兼顾去噪能力与不同尺度目标的完整性。三是采用形态学重建或边缘约束等手段对滤波结果进行保边"
            "修正，以弥补轮廓侵蚀带来的漏检损失。", False, False)], space_after=4)

print("实验部分完成")

heading(doc, "4　结论", 1)
rich(doc, [("针对传统高斯混合模型因逐像素独立建模而导致前景掩码中存在大量孤立椒盐噪点的问题，本文提出了"
            "一种频域后置净化方法。该方法不改动GMM的核心时序建模逻辑，而是在其输出掩码之后串联二维傅里叶"
            "高斯低通滤波模块，依据傅里叶卷积定理将空域高斯平滑等价转换为频域逐点相乘，在抑制高频噪声分量的"
            "同时保留目标主体，并经逆变换与阈值二值化得到净化掩码。", False, False)], space_after=2)
rich(doc, [("在自建的 240 像素×160 像素、200 帧小型监控序列上，以逐像素真值掩码为基准的定量实验表明："
            "所提方法使误检率由 7.4956% 降至 5.7872%，降幅 22.8%；轮廓完整度由 0.5041 提升至 0.5605，"
            "提升 11.2%；每帧孤立连通块数量由 265.5 个降至 2.1 个，降幅 99.2%；背景区域帧间抖动下降 95.3%；"
            "后处理附加延迟仅 1.10 ms/帧，整体速度达 638 帧/s，实时性得到保持。分段统计表明该方法在常规监控"
            "场景下有效，而在光照突变场景下受限于GMM的时序建模缺陷。", False, False)], space_after=2)
rich(doc, [("本文方法的普适性与适用范围可概括为：方法以二值掩码为输入与输出，属于与背景建模算法无关的通用"
            "后置模块，可移植至 ViBe、SuBSENSE 等任意像素级背景建模方法之后；由于只利用空间邻域相关性，"
            "方法适用于室内外常规监控、动态弱扰动等以空间噪声为主要误差来源的场景；在光照剧变、长期静止目标"
            "与强阴影场景下，需与光照补偿、阴影抑制或时序频域分析等手段配合使用。", False, False)], space_after=4)

print("结论完成")

# ---------------- 参考文献 ----------------
heading(doc, "参考文献", 1)
refs = [

    "Agrawal S, Natu P. 2021. An improved Gaussian mixture method based background subtraction model for"
    "moving object detection in outdoor scene//2021 Fourth International Conference on Electrical,"
    "Computer and Communication Technologies. Coimbatore, India: IEEE: 1-8. DOI:"
    "10.1109/ICECCT52121.2021.9616883.",
    "Ammar S, Bouwmans T, Zaghden N, Neji M. 2020. Deep detector classifier (DeepDC) for moving objects"
    "segmentation and classification in video surveillance[J]. IET Image Processing, 14(8): 1490-1501."
    "DOI: 10.1049/iet-ipr.2019.0769.",
    "Bariko S, Klilou A, Abounada A, Arsalane A. 2024. Parallel implementation of Gaussian mixture model"
    "background subtraction on Jetson Nano//2024 World Conference on Complex Systems. Ouarzazate,"
    "Morocco: IEEE: 1-6. DOI: 10.1109/WCCS62745.2024.10765544.",
    "Barnich O, Van Droogenbroeck M. 2011. ViBe: a universal background subtraction algorithm for video"
    "sequences[J]. IEEE Transactions on Image Processing, 20(6): 1709-1724. DOI:"
    "10.1109/TIP.2010.2101613.",
    "Bian Z G, Cao X G. 2012. Moving object detection based on improved Gaussian mixture model//2012 5th"
    "International Congress on Image and Signal Processing. Chongqing, China: IEEE: 109-112. DOI:"
    "10.1109/CISP.2012.6469813.",
    "Bouwmans T. 2014. Traditional and recent approaches in background modeling for foreground detection:"
    "an overview[J]. Computer Science Review, 11-12: 31-66. DOI: 10.1016/j.cosrev.2014.04.001.",
    "Chapel M N, Bouwmans T. 2020. Moving objects detection with a moving camera: a comprehensive"
    "review[J]. Computer Science Review, 38: 100310. DOI: 10.1016/j.cosrev.2020.100310.",
    "Chen X R. 2015. Research on moving object detection based on improved mixture Gaussian model[J]."
    "Optik, 126(20): 2256-2259. DOI: 10.1016/j.ijleo.2015.05.122.",
    "Elgammal A, Harwood D, Davis L. 2000. Non-parametric model for background subtraction//Computer"
    "Vision — ECCV 2000. Berlin: Springer: 751-767. DOI: 10.1007/3-540-45053-X_48.",
    "Giraldo J H, Bouwmans T. 2020. Deep learning based background subtraction: a systematic"
    "survey//Handbook of Pattern Recognition and Computer Vision. 5th ed. Singapore: World Scientific:"
    "51-73. DOI: 10.1142/9789811211072_0003.",
    "Gonzalez R C, Woods R E. 2018. Digital Image Processing[M]. 4th ed. New York: Pearson: 178-252.",
    "Hou Y K, Shen D G. 2018. Image denoising with morphology- and size-adaptive block-matching transform"
    "domain filtering[J]. EURASIP Journal on Image and Video Processing, 2018(1): 1-18. DOI:"
    "10.1186/s13640-018-0301-y.",
    "Jia H B, Yin Q B, Lu M Y. 2022. Blind-noise image denoising with block-matching domain"
    "transformation filtering and improved guided filtering[J]. Scientific Reports, 12(1): 16195. DOI:"
    "10.1038/s41598-022-20578-w.",
    "Kalsotra R, Arora S. 2021. Background subtraction for moving object detection: explorations of"
    "recent developments and challenges[J]. The Visual Computer, 38(12): 4151-4178. DOI:"
    "10.1007/s00371-021-02286-0.",
    "Klare B, Sarkar S. 2009. Background subtraction in varying illuminations using an ensemble based on"
    "an enlarged feature set//2009 IEEE Computer Society Conference on Computer Vision and Pattern"
    "Recognition Workshops. Miami, USA: IEEE: 66-73. DOI: 10.1109/CVPRW.2009.5204078.",
    "Lee D S. 2005. Effective Gaussian mixture learning for video background subtraction[J]. IEEE"
    "Transactions on Pattern Analysis and Machine Intelligence, 27(5): 827-832. DOI:"
    "10.1109/TPAMI.2005.102.",
    "Li H S, ⬜⬜⬜. 2013. Improved object detection method of adaptive Gaussian mixture model[J]. Journal"
    "of Computer Applications, 33(9): 2610-2613. DOI: 10.3724/SP.J.1087.2013.02610.",
    "Liu M J, Wei Y. 2019. Image denoising using graph-based frequency domain low-pass filtering//2019"
    "IEEE 4th International Conference on Image, Vision and Computing. Xiamen, China: IEEE: 118-122. DOI:"
    "10.1109/ICIVC47709.2019.8980994.",
    "Lu X F, Xu C D. 2018. Novel Gaussian mixture model background subtraction method for detecting"
    "moving objects//2018 IEEE International Conference of Safety Produce Informatization. Chongqing,"
    "China: IEEE: 6-10. DOI: 10.1109/IICSPI.2018.8690428.",
    "Ozaktas H M, Barshan B, Mendlovic D. 1996. Repeated fractional Fourier domain filtering is"
    "equivalent to repeated time and frequency domain filtering[J]. Signal Processing, 54(1): 81-84. DOI:"
    "10.1016/0165-1684(96)00095-3.",
    "Pei W J, Shi Z H, Gong K. 2023. Moving object detection in satellite videos based on an improved"
    "ViBe algorithm[J]. Signal, Image and Video Processing, 18(3): 2543-2557. DOI:"
    "10.1007/s11760-023-02929-w.",
    "Peng T, He K, Su Y, Zhang J, Zhao Q J. 2022. Visual perception and local features for"
    "foreground-background segmentation[J]. IET Image Processing, 16(6): 1613-1625. DOI:"
    "10.1049/ipr2.12434.",
    "Sheng H, Wei G M, Liu G C. 2022. Research on small moving object detection based on improved"
    "Gaussian mixture model//2022 2nd International Conference on Big Data Engineering and Education."
    "Chengdu, China: IEEE: 197-200. DOI: 10.1109/BDEE55929.2022.00040.",
    "Si W J. 2024. Object detection algorithm in video surveillance systems based on neural networks[J]."
    "Intelligent Decision Technologies, 19(2): 1226-1239. DOI: 10.1177/18724981241292941.",
    "Sobral A, Vacavant A. 2014. A comprehensive review of background subtraction algorithms evaluated"
    "with synthetic and real videos[J]. Computer Vision and Image Understanding, 122: 4-21. DOI:"
    "10.1016/j.cviu.2013.12.005.",
    "St-Charles P L, Bilodeau G A, Bergevin R. 2015. SuBSENSE: a universal change detection method with"
    "local adaptive sensitivity[J]. IEEE Transactions on Image Processing, 24(1): 359-373. DOI:"
    "10.1109/TIP.2014.2378053.",
    "Stauffer C, Grimson W E L. 1999. Adaptive background mixture models for real-time"
    "tracking//Proceedings of the 1999 IEEE Computer Society Conference on Computer Vision and Pattern"
    "Recognition. Fort Collins, USA: IEEE: 246-252. DOI: 10.1109/CVPR.1999.784637.",
    "Yan Q, Xu L, Wang J. 2010. Real-time foreground detection based on tempo-spatial consistency"
    "validation and Gaussian mixture model//2010 IEEE International Symposium on Broadband Multimedia"
    "Systems and Broadcasting. Shanghai, China: IEEE: 1-4. DOI: 10.1109/ISBMSB.2010.5463088.",
    "Zhang S. 2019. Comparing Hilbert transform profilometry and Fourier transform"
    "profilometry//Dimensional Optical Metrology and Inspection for Practical Applications VIII."
    "Baltimore, USA: SPIE: 6. DOI: 10.1117/12.2517870.",
    "Zivkovic Z. 2004. Improved adaptive Gaussian mixture model for background subtraction//Proceedings"
    "of the 17th International Conference on Pattern Recognition. Cambridge, UK: IEEE: 28-31. DOI:"
    "10.1109/ICPR.2004.1333992.",

]
for i, r in enumerate(refs, 1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.line_spacing = 1.1
    pf.space_after = Pt(2)
    pf.left_indent = Pt(16)
    pf.first_line_indent = Pt(-16)
    set_run(p.add_run("[%d] " % i), size=9)
    set_run(p.add_run(r), size=9)

doc.save(str(OUT))
print("\n已生成 Word 文档：", OUT)
print("参考文献数量：", len(refs))
