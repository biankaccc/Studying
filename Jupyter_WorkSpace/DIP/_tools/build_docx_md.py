# -*- coding: utf-8 -*-
"""
由论文 Markdown 生成《中国图象图形学报》体例的 Word 版。

支持：中英文题名、署名与首页信息、摘要、标题层级、三线表、图片与图题、公式、参考文献。

公式有两种模式（环境变量 DOCX_MATH 控制）：
    omml —— **默认**。生成 Word 原生数学对象，可在 Word 中双击编辑（推荐）。
            关键：分式的分子/分母必须用 m:num / m:den 标签（**不能**用 m:e），
            否则 Word 会报"文件可能已经损坏"并拒绝打开。详见 omml.py 注释。
    img  —— 把公式渲染成 PNG 插入（mathimg.py）。文档一定能打开，但公式不可编辑，
            字号与正文也不易完全匹配，仅作兜底。

用法：
    python build_docx_md.py 0303
    set DOCX_MATH=img && python build_docx_md.py 0303
"""
import io
import os
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt

sys.path.insert(0, str(Path(__file__).parent))
import mathimg as _mathimg      # LaTeX -> PNG 渲染器（默认方案）
import omml as _omml            # LaTeX -> OMML 转换器（备选方案）

DIP = Path(r"D:\workspace\Jupyter_WorkSpace\DIP")
CN, CN_H, EN = "宋体", "黑体", "Times New Roman"
MATH_MODE = os.environ.get("DOCX_MATH", "omml").lower()
EQ_CACHE = DIP / "_tools" / "_eqcache"      # 公式图片缓存目录


# ----------------------------------------------------------------------
def add_inline_math(doc_paragraph, latex, size=10.5):
    """
    在段落中插入行内公式。按 MATH_MODE 选择图片或 OMML。
    图片模式把公式图片作为内联图片插入，与文字同段混排。
    """
    if MATH_MODE == "omml":
        _omml.append_inline_math(doc_paragraph, latex, size=size)
        return
    try:
        png = _mathimg.render_cache(latex, EQ_CACHE)
        run = doc_paragraph.add_run()
        run.add_picture(str(png), height=Pt(size * 1.55))
    except Exception:
        # 渲染失败时退回纯文本，绝不中断整篇生成
        set_run(doc_paragraph.add_run(f" {latex} "), size=size)


def add_equation(doc, latex, number=None, *, size=11.0):
    """
    插入居中显示公式，编号右对齐。

    排版用两个制表位实现（不能只靠段落居中，否则编号会紧贴公式）：
        [居中制表位 半版心] <公式> [右制表位 全版心] （编号）
    """
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(5)
    pf.space_after = Pt(5)
    pf.line_spacing = 1.0
    # 左对齐 + 制表位：公式靠居中制表位落到中间，编号靠右制表位贴右边
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sec = doc.sections[0]
    avail = Emu(sec.page_width - sec.left_margin - sec.right_margin).cm
    pf.tab_stops.add_tab_stop(Cm(avail / 2), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Cm(avail), WD_TAB_ALIGNMENT.RIGHT)
    p.add_run("\t")

    if MATH_MODE == "omml":
        # 【关键】显示公式必须用 <m:oMathPara> 包裹 <m:oMath>。
        # 直接把裸 <m:oMath> 挂在段落里，Word 会报"文件可能已经损坏"并拒绝打开
        # （行内公式则必须用裸 <m:oMath>，两者不可混用）。已实测验证。
        para = _omml._e("oMathPara")
        omath = _omml._e("oMath")
        for node in _omml.latex_to_omml(latex):
            omath.append(node)
        para.append(omath)
        p._p.append(para)
    else:
        try:
            png = _mathimg.render_cache(latex, EQ_CACHE)
            from PIL import Image
            with Image.open(png) as im:
                ratio = im.height / max(1, im.width)
            h_cm = min(3.0, 12.5 * ratio)
            run = p.add_run()
            run.add_picture(str(png), height=Cm(h_cm))
        except Exception:
            set_run(p.add_run(latex), size=size)

    if number:
        p.add_run("\t")           # 右制表位：编号贴右边
        set_run(p.add_run(f"（{number}）"), size=size)
    return p


def set_run(run, *, cn=CN, en=EN, size=10.5, bold=False, italic=False):
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
    return run


def para(doc, text="", *, cn=CN, size=10.5, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         space_before=0, space_after=2, line=1.15, first_line=0.0):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = line
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    if first_line:
        pf.first_line_indent = Pt(size * first_line)
    if text:
        set_run(p.add_run(text), cn=cn, size=size, bold=bold)
    return p


def rich(doc, text, *, size=10.5, first_line=2.0, space_after=2,
         align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    """
    按 **粗体**、$行内公式$ 分段写入。
    行内公式用 OMML 插入，在 Word 中显示为真正的数学式（含上下标）。
    """
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.line_spacing = 1.15
    pf.space_after = Pt(space_after)
    if first_line:
        pf.first_line_indent = Pt(size * first_line)

    # 先把 **粗体** 切出来，再在每个片段里切 $公式$
    for seg in re.split(r"(\*\*[^*]+\*\*)", text):
        if not seg:
            continue
        bold = seg.startswith("**") and seg.endswith("**")
        inner = seg[2:-2] if bold else seg
        for part in re.split(r"(\$[^$]+\$)", inner):
            if not part:
                continue
            if part.startswith("$") and part.endswith("$") and len(part) > 2:
                add_inline_math(p, part[1:-1], size=size)
            else:
                set_run(p.add_run(part), size=size, bold=bold)
    return p


def heading(doc, text, level):
    size = 12.0 if level == 1 else 10.5
    return para(doc, text, cn=CN_H, size=size, bold=True,
                align=WD_ALIGN_PARAGRAPH.LEFT,
                space_before=10 if level == 1 else 7, space_after=4)


def set_cell_border(cell, **kw):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        spec = kw.get(edge)
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


def cell_text(cell, text, *, bold=False, size=9, math=True):
    """写入表格单元格；单元格内的 $公式$ 也转为 OMML。"""
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(1.5)
    p.paragraph_format.space_after = Pt(1.5)
    if not math:
        set_run(p.add_run(text), size=size, bold=bold)
        return
    for part in re.split(r"(\$[^$]+\$)", text):
        if not part:
            continue
        if part.startswith("$") and part.endswith("$") and len(part) > 2:
            add_inline_math(p, part[1:-1], size=size)
        else:
            set_run(p.add_run(part), size=size, bold=bold)


def add_table(doc, header, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(header):
        cell_text(t.rows[0].cells[j], h, bold=True)
    for i, r in enumerate(rows, start=1):
        for j, v in enumerate(r):
            cell_text(t.rows[i].cells[j], v)
    last = len(rows)
    for i, row in enumerate(t.rows):
        for cell in row.cells:
            b = {}
            if i == 0:
                b["top"], b["bottom"] = 12, 6
            if i == last:
                b["bottom"] = 12
            set_cell_border(cell, **b)
    para(doc, "", space_after=4)
    return t


# ----------------------------------------------------------------------
def build(chapter, md_file=None, out_name=None):
    """
    由论文 Markdown 生成 Word。

    chapter  : 章节目录名，如 "0303"
    md_file  : 可选，明确指定源 Markdown 路径（默认自动在目录内查找）
    out_name : 可选，明确指定输出 docx 文件名（默认与源 md 同名）
    """
    folder = DIP / chapter
    if md_file is not None:
        md_path = Path(md_file)
        if not md_path.is_absolute():
            md_path = folder / md_path
    else:
        md_path = next(folder.glob("*课设论文*.md"), None)
        if md_path is None:
            md_path = next((p for p in folder.glob("*.md")
                            if "大纲" not in p.name and "要求" not in p.name), None)
    if md_path is None or not md_path.exists():
        raise SystemExit(f"{folder} 下找不到论文 Markdown")
    out = folder / (out_name if out_name else (md_path.stem + ".docx"))

    lines = io.open(md_path, encoding="utf-8").read().split("\n")
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = EN
    st.font.size = Pt(10.5)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), CN)

    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.top_margin = sec.bottom_margin = Cm(2.5)
    sec.left_margin = sec.right_margin = Cm(2.5)

    i = 0
    first_h1_done = False
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        # ---- 图片 ----
        m = re.match(r"!\[.*?\]\((.+?)\)", s)
        if m:
            img = folder / m.group(1)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            if img.exists():
                p.add_run().add_picture(str(img), width=Cm(15.0))
            else:
                set_run(p.add_run(f"［图件缺失：{img.name}］"), size=9)
            i += 1
            continue

        # ---- 表格 ----
        if s.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].strip()) - set("|-: ") == set():
            header = [c.strip() for c in s.strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            add_table(doc, header, rows)
            continue

        # ---- 显示公式：转为 OMML 真公式，编号右对齐 ----
        if s == "$$":
            j = i + 1
            buf = []
            while j < len(lines) and lines[j].strip() != "$$":
                buf.append(lines[j])
                j += 1
            latex = " ".join(x.strip() for x in buf).strip()
            num = ""
            mn = re.search(r"\\tag\{(\d+)\}", latex)
            if mn:
                num = mn.group(1)
            add_equation(doc, latex, number=num)
            i = j + 1
            continue

        # ---- 标题 ----
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            lvl, text = len(m.group(1)), m.group(2)
            if lvl == 1 and not first_h1_done:
                first_h1_done = True
                para(doc, text, cn=CN_H, size=16, bold=True,
                     align=WD_ALIGN_PARAGRAPH.CENTER, space_before=6, space_after=4)
                # 英文题名（下一非空行若为全英文，则作为英文题名）
                if i + 2 < len(lines) and lines[i + 2].strip().startswith("**") \
                        and not re.search(r"[\u4e00-\u9fff]", lines[i + 2]):
                    para(doc, lines[i + 2].strip().strip("*"), size=11, bold=True,
                         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8)
                    i += 2
            else:
                heading(doc, text, lvl)
            i += 1
            continue

        # ---- 空行 / 分隔线 / 代码块 ----
        if not s or set(s) <= set("-— "):
            i += 1
            continue
        if s.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            for b in buf:
                para(doc, b, size=9, cn="Consolas", space_after=0)
            para(doc, "", space_after=3)
            continue
        if s.startswith(">"):                      # 引用块转小字备注
            para(doc, s.lstrip("> ").strip(), size=9, space_after=2)
            i += 1
            continue
        if s.startswith("- ") or re.match(r"^\d+\.\s", s):
            rich(doc, s, first_line=0, space_after=1)
            i += 1
            continue

        # ---- 正文 ----
        rich(doc, s)
        i += 1

    doc.save(str(out))
    print(f"已生成 Word：{out.name}  ({out.stat().st_size/1024:.1f} KB)")
    return out


if __name__ == "__main__":
    # 用法：
    #   python build_docx_md.py 0303
    #   python build_docx_md.py 0303 <源md文件名> <输出docx文件名>
    _chap = sys.argv[1] if len(sys.argv) > 1 else "0303"
    _md = sys.argv[2] if len(sys.argv) > 2 else None
    _out = sys.argv[3] if len(sys.argv) > 3 else None
    build(_chap, _md, _out)
