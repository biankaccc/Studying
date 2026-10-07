# -*- coding: utf-8 -*-
"""
DIP 课设交付物总校验（只读，不修改任何交付物）。

用法：
    python verify.py                  # 自动定位最近的章节目录
    python verify.py 0202             # 指定章节

检查项：
    1 源码完整性（notebook 代码单元是否含换行，未被粘成单行）
    2 文件齐备性（ipynb / md / docx / data）
    3 图件与三线表（尺寸是否合理、数量、中文缺字形告警）
    4 参考文献（数量、近 10 年占比、DOI 覆盖、字母序）
    5 论文合规（题名禁用词、摘要分项、图表双语、关键数字一致性）
"""
import io
import json
import os
import re
import struct
import sys
from pathlib import Path

DIP_ROOT = Path(r"D:\workspace\Jupyter_WorkSpace\DIP")

PASS, FAIL, WARN = "通过", "不通过", "注意"
results = []


def record(name, ok, detail=""):
    results.append((PASS if ok else FAIL, name, detail))
    print(f"  [{PASS if ok else FAIL}] {name}" + (f" —— {detail}" if detail else ""))
    return ok


def warn(name, detail):
    results.append((WARN, name, detail))
    print(f"  [{WARN}] {name} —— {detail}")


# ----------------------------------------------------------------------
def find_chapter(arg=None):
    if arg:
        d = DIP_ROOT / arg
        if d.is_dir():
            return d
        raise SystemExit(f"找不到章节目录：{d}")
    cands = [d for d in DIP_ROOT.iterdir()
             if d.is_dir() and re.fullmatch(r"\d{4}", d.name)]
    cands.sort(key=lambda d: (len(list(d.glob("*.ipynb"))), d.name), reverse=True)
    if not cands:
        raise SystemExit("DIP 目录下没有形如 0202 的章节目录")
    return cands[0]


def pick(folder, patterns, exclude=()):
    """在目录下按若干通配模式取一个文件。"""
    for pat in patterns:
        for p in sorted(folder.glob(pat)):
            if not any(e in p.name for e in exclude):
                return p
    return None


# ----------------------------------------------------------------------
def check_source_integrity(nb_path):
    print("\n1 源码完整性")
    if nb_path is None:
        return record("notebook 存在", False, "目录下未找到 .ipynb")
    nb = json.loads(io.open(nb_path, encoding="utf-8").read())
    codes = [c for c in nb["cells"] if c["cell_type"] == "code"]

    def text(c):
        s = c["source"]
        return "\n".join(s) if isinstance(s, list) else s

    stuck = [(i, len(text(c))) for i, c in enumerate(codes)
             if len(text(c)) > 400 and text(c).count("\n") < 5]
    record("代码单元未被粘成单行", not stuck,
           f"{len(codes)} 个代码单元，异常 {len(stuck)} 个" if stuck else f"{len(codes)} 个代码单元全部正常")
    untitled = [i for i, c in enumerate(codes) if c.get("execution_count") is None]
    record("全部代码单元已执行（输出内嵌）", not untitled,
           f"未执行单元：{untitled}" if untitled else "")
    n_png = sum(1 for c in codes for o in c.get("outputs", [])
                if "image/png" in (o.get("data") or {}))
    record("图已内嵌到 notebook", n_png >= 4, f"内嵌图 {n_png} 张")
    errs = [(i, o.get("ename")) for i, c in enumerate(codes)
            for o in c.get("outputs", []) if o.get("output_type") == "error"]
    record("无残留错误输出", not errs, str(errs) if errs else "")
    return nb


def check_files(folder, nb_path, md_path, docx_path):
    print("\n2 文件齐备性")
    record("Notebook (.ipynb)", nb_path is not None,
           nb_path.name if nb_path else "缺失")
    record("论文 Markdown (.md)", md_path is not None)
    record("论文 Word (.docx)", docx_path is not None)
    data = folder / "data"
    record("data 子目录", data.is_dir())
    if data.is_dir():
        figs = list(data.glob("fig_*.png"))
        record("data 内有插图", len(figs) >= 4, f"{len(figs)} 张")
        record("data 内有结果数据表", bool(list(data.glob("*.csv"))),
               f"{len(list(data.glob('*.csv')))} 个 CSV")
    stray = [p.name for p in folder.iterdir()
             if p.is_file() and p.suffix in (".txt", ".log", ".bak")]
    if stray:
        warn("章节目录存在日志/备份文件", str(stray))


def check_figures(folder, nb):
    print("\n3 图件与字形")
    data = folder / "data"
    bad = []
    for p in sorted(data.glob("fig_*.png")):
        with open(p, "rb") as f:
            head = f.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            bad.append(p.name)
            continue
        w, h = struct.unpack(">II", head[16:24])
        if not (200 < w < 20000 and 150 < h < 20000 and w / h < 8):
            bad.append(f"{p.name} {w}x{h}")
    record("图件尺寸正常", not bad, str(bad) if bad else "")
    glyph = 0
    if nb is not None:
        for c in nb["cells"]:
            for o in c.get("outputs", []):
                if o.get("output_type") == "stream":
                    glyph += o.get("text", "").count("missing from current font")
    record("无中文字形缺失告警", glyph == 0, f"{glyph} 条" if glyph else "")


def check_refs(md_path):
    print("\n4 参考文献")
    if md_path is None:
        return record("论文 Markdown 可读", False)
    s = io.open(md_path, encoding="utf-8").read()
    if "## 参考文献" not in s:
        return record("含参考文献节", False)
    body = s.split("## 参考文献")[1]
    for stop in ("## 图题", "## 附录"):
        body = body.split(stop)[0]
    items = [b.strip() for b in body.strip().split("\n\n") if b.strip()]
    items = [i for i in items if set(i.strip()) - set("-— \n")]     # 排除纯分隔线
    record("文献数量 ≥15", len(items) >= 15, f"实际 {len(items)} 篇")
    n_items = len(items)

    years = []
    no_doi = []
    for it in items:
        one = " ".join(it.split())
        m = re.search(r"\b(19\d\d|20\d\d)\b", one)
        if m:
            years.append(int(m.group(1)))
        if "DOI:" not in one and "[M]" not in one:
            no_doi.append(one[:50])
    if years:
        recent = [y for y in years if y >= 2015]
        ratio = len(recent) / len(years)
        record("近 10 年文献 ≥60%", ratio >= 0.6,
               f"{len(recent)}/{len(years)} = {ratio*100:.0f}%")

    def key(it):
        """按首作者姓氏排序；连字符视作空格，使 St-Charles 排在 Stauffer 之后。"""
        head = re.split(r"[,\s]", " ".join(it.split()))[0]
        head = head.replace("-", " ")
        return re.sub(r"[^A-Za-z ]", "", head).lower()

    keys = [key(i) for i in items]
    disorder = [(keys[i - 1], keys[i]) for i in range(1, len(keys))
                if keys[i] < keys[i - 1]]
    record("文献按首作者字母序排列", not disorder, str(disorder[:3]) if disorder else "")
    if no_doi:
        warn("以下条目无 DOI（书籍可豁免）", "; ".join(no_doi))
    return n_items


def check_paper(md_path, nb):
    print("\n5 论文合规")
    if md_path is None:
        return
    s = io.open(md_path, encoding="utf-8").read()
    first = next((l for l in s.split("\n") if l.startswith("# ")), "")
    title = first.lstrip("# ").strip()
    record("中文题名 ≤20 字", len(re.findall(r"[\u4e00-\u9fff]", title)) <= 20,
           f"实际 {len(re.findall(r'[一-龥]', title))} 字：{title}")
    banned = [w for w in ("基于", "一种", "利用") if w in title]
    record("题名无禁用词", not banned, str(banned) if banned else "")
    for label in ("目的", "方法", "结果", "结论"):
        if f"**{label}**" not in s and f"**{label}**:" not in s:
            record(f"中文摘要含『{label}』", False)
            break
    else:
        record("中文摘要四项齐全（目的/方法/结果/结论）", True)

    # 摘要四要素必须【各自单独成段】（规范 6.1）。检查方式：找到摘要区间，
    # 看以 **目的**/**方法**/**结果**/**结论** 开头的行是否为独立行。
    m_abs = re.search(r"##\s*摘要\s*\n(.*?)(?=\n\*\*Abstract\*\*|\n##\s)",
                      s, re.S)
    if m_abs:
        abs_lines = [l for l in m_abs.group(1).split("\n") if l.strip()]
        starts = {}
        for l in abs_lines:
            for lab in ("目的", "方法", "结果", "结论"):
                if l.lstrip().startswith(f"**{lab}**"):
                    starts[lab] = l
        record("摘要四要素各自单独成段", len(starts) == 4,
               f"独立成段的要素 {len(starts)}/4"
               + (f"，缺 {[k for k in ('目的','方法','结果','结论') if k not in starts]}"
                  if len(starts) < 4 else ""))
    for label in ("Objective", "Method", "Result", "Conclusion"):
        if f"**{label}**" not in s:
            record(f"英文摘要含『{label}』", False)
            break
    else:
        record("英文摘要四项齐全", True)
    fig_caps = len(re.findall(r"\*\*图\d　", s))
    tbl_caps = len(re.findall(r"\*\*表\d　", s))
    record("含图题（中英文对照）", fig_caps >= 1, f"{fig_caps} 个图题")
    record("含表题（中英文对照）", tbl_caps >= 1, f"{tbl_caps} 个表题")
    # 图题与表题必须中英文成对出现
    fig_en = len(re.findall(r"\*\*Fig\.\d", s))
    tbl_en = len(re.findall(r"\*\*Table \d", s))
    record("图题中英文成对", fig_en >= fig_caps,
           f"中文 {fig_caps} / 英文 {fig_en}")
    record("表题中英文成对", tbl_en >= tbl_caps,
           f"中文 {tbl_caps} / 英文 {tbl_en}")
    record("含中图法分类号", "中图法分类号" in s)
    if "⬜" in s:
        warn("论文中存在待补占位符 ⬜", f"{s.count('⬜')} 处（作者单位/出生年等）")


def count_refs_blob(text):
    """统计一段文本中的参考文献条数，兼容三种常见写法：
       ① 以 [N] 编号（如 [1] Author ...）
       ② 纯段落列表（以空行分隔）
       ③ 以数字 + 点编号（如 1. Author ...）
    注意：调用方必须传入**参考文献节之后**的文本，不能传全文。
    """
    n1 = len(re.findall(r"^\s*\[\d+\]\s", text, re.M))
    if n1 >= 3:
        return n1
    n2 = len(re.findall(r"^\s*\d+[.)]\s+\S", text, re.M))
    if n2 >= 3:
        return n2
    # 纯段落：以"姓氏 首字母缩写. 年份."开头的段落
    n3 = len(re.findall(r"^\s*[A-Z][A-Za-z\-']+(?:\s+[A-Z]\.)?[,\s].*?\b(19|20)\d\d\b",
                        text, re.M))
    if n3 >= 3:
        return n3
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    blocks = [b for b in blocks if set(b) - set("-— \n")]
    return len(blocks)


def check_consistency(md_path, docx_path, refs_count):
    """交叉一致性：Word 与 Markdown 的文献数、图数、表数与关键指标必须一致。"""
    print("\n6 交付物一致性")
    if md_path is None or docx_path is None:
        return record("md 与 docx 均存在", False)
    try:
        from docx import Document
    except ImportError:
        return warn("未安装 python-docx", "跳过 docx 一致性检查")

    doc = Document(str(docx_path))
    # 提取文本时必须同时包含 OMML 公式内的文本：
    # 公式现在渲染为 Word 原生数学对象，其文字不在 paragraph.text 中。
    M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
    M_T = "{%s}t" % M_NS

    def para_text(p):
        s = p.text or ""
        for t in p._p.iter(M_T):
            s += (t.text or "")
        return s

    dtxt = "\n".join(para_text(p) for p in doc.paragraphs)
    for tb in doc.tables:
        for row in tb.rows:
            for c in row.cells:
                dtxt += "\n" + " ".join(para_text(p) for p in c.paragraphs)

    # --- 参考文献条数一致：取 docx 中**最后一次**出现"参考文献"之后的文本 ---
    parts = dtxt.split("参考文献")
    tail = parts[-1] if len(parts) > 1 else ""
    n_docx_refs = count_refs_blob(tail)
    record("md 与 docx 文献数一致", abs(n_docx_refs - refs_count) <= 1,
           f"md {refs_count} 条 / docx {n_docx_refs} 条")

    # --- 图表数量一致（用与生成器相同的判定方式统计 md 表格）---
    md = io.open(md_path, encoding="utf-8").read()
    md_figs = len(re.findall(r"!\[.*?\]\(.+?\)", md))
    md_lines = md.split("\n")
    n_md_tbls, k = 0, 0
    while k < len(md_lines):
        cur = md_lines[k].strip()
        nxt = md_lines[k + 1].strip() if k + 1 < len(md_lines) else ""
        if cur.startswith("|") and nxt.startswith("|") and set(nxt) - set("|-: ") == set():
            n_md_tbls += 1
            k += 2
            while k < len(md_lines) and md_lines[k].strip().startswith("|"):
                k += 1
        else:
            k += 1
    n_img = len([r for r in doc.part.rels.values() if "image" in r.reltype])
    record("docx 内嵌图数与 md 一致", n_img >= md_figs,
           f"md {md_figs} 张 / docx {n_img} 张")
    record("docx 三线表数与 md 一致", len(doc.tables) == n_md_tbls,
           f"md {n_md_tbls} 个 / docx {len(doc.tables)} 个")

    # --- 关键指标：从 md 的表格中自动抽取数字，再检查 docx 中是否同样出现 ---
    #     两个坑：
    #       ① img 模式下公式是图片，公式里的数字不在 Word 文本层，须剔除公式内容；
    #       ② $$...$$ 公式块中可能含以 | 开头的行（如绝对值 |I_t-μ_k|），
    #          会被误判成表格行——必须整块跳过。
    nums = set()
    in_math_block = False
    for line in md.split("\n"):
        st = line.strip()
        if st.startswith("$$"):
            # 单行 $$...$$ 或块起止
            if st.count("$$") == 1:
                in_math_block = not in_math_block
            continue
        if in_math_block:
            continue
        if not st.startswith("|"):
            continue
        for cell in st.strip("|").split("|"):
            text_only = re.sub(r"\$[^$]*\$", " ", cell)      # 去掉行内公式
            for tok in re.findall(r"\d+\.\d+|\b\d{2,}\b", text_only):
                nums.add(tok)
    nums = {n for n in nums if not re.fullmatch(r"(19|20)\d\d", n)}    # 去掉年份
    miss_d = sorted(n for n in nums if n not in dtxt)
    record("md 表格数值均在 docx 中出现", not miss_d,
           f"缺失 {len(miss_d)} 个：{miss_d[:6]}" if miss_d else f"共核对 {len(nums)} 个数值")

    # --- 中文字数规模 ---
    n_cjk = len(re.findall(r"[\u4e00-\u9fff]", md))
    record("论文正文规模合理", n_cjk >= 3000, f"中文字数 {n_cjk}")

    # --- 公式：按 DOCX_MATH 模式分别校验 ---
    #     omml 模式（默认）：公式为 Word 原生数学对象，可在 Word 中编辑；
    #     img 模式：公式渲染为 PNG 插入（兜底方案，公式不可编辑）。
    import zipfile
    MATH_MODE = os.environ.get("DOCX_MATH", "omml").lower()
    M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8")
        n_media = len([n for n in z.namelist()
                       if n.startswith("word/media/") and n.lower().endswith(".png")])
    # 显示公式的计数必须与生成器一致：只有"整行仅为 $$"才算块定界。
    # 之前用正则 \$\$(.+?)\$\$ 跨行配对，遇到句中的 $$K$$ 会误配，导致数量虚高。
    md_lines = md.split("\n")
    n_disp = 0
    k2 = 0
    while k2 < len(md_lines):
        if md_lines[k2].strip() == "$$":
            j2 = k2 + 1
            while j2 < len(md_lines) and md_lines[j2].strip() != "$$":
                j2 += 1
            if j2 < len(md_lines):
                n_disp += 1
            k2 = j2 + 1
        else:
            k2 += 1
    # 行内公式：剔除公式块内容后再数，避免块内被重复计入
    md_wo_blocks = re.sub(r"(?m)^\$\$.*?^\$\$", " ", md, flags=re.S)
    n_inline_md = len(re.findall(r"(?<!\$)\$([^$]+)\$(?!\$)", md_wo_blocks))
    n_formulas = n_disp + n_inline_md
    record("Markdown 含公式", n_formulas > 0,
           f"公式 {n_formulas} 个（显示 {n_disp}，行内 {n_inline_md}）")

    if MATH_MODE == "omml":
        n_math = xml.count("<m:oMath>")
        record("Word 公式为真 OMML（可编辑）", n_math > 0, f"公式对象 {n_math} 个")
        if n_math > 0:
            record("OMML 命名空间已在根元素声明",
                   M_NS in re.search(r"<w:document\b[^>]*>", xml).group(0))
        # 【致命约束 1】分式的分子/分母必须是 m:num / m:den，写成 m:e 会让
        # Word 报"文件可能已经损坏"并拒绝打开（实测验证）。
        n_f = xml.count("<m:f>")
        if n_f:
            n_num, n_den = xml.count("<m:num>"), xml.count("<m:den>")
            record("分式用 m:num/m:den（非 m:e）",
                   n_num == n_f and n_den == n_f,
                   f"分式 {n_f}，分子 {n_num}，分母 {n_den}")
        # 【致命约束 2】显示公式必须用 m:oMathPara 包裹；裸 m:oMath 会导致
        # Word 拒绝打开。行内公式则必须用裸 m:oMath（不用包裹）。
        n_para = xml.count("<m:oMathPara>")
        record("显示公式用 m:oMathPara 包裹", n_para >= n_disp,
               f"oMathPara {n_para} 个，显示公式 {n_disp} 个")
    else:
        n_inline = xml.count("<w:drawing>")
        record("公式已渲染为图片插入", n_inline >= n_formulas,
               f"内联图对象 {n_inline} 个，公式 {n_formulas} 个")
        record("公式图片已写入包内", n_media > 0, f"word/media 下 PNG {n_media} 个")

    # --- 【关键】让 Word 真的打开一次：这是"文档是否可用"的最终判据 ---
    #     踩过的坑：lxml 能解析、python-docx 能读、Schema 校验也通过，
    #     但 Word 仍可能因结构问题报"文件可能已经损坏"而拒绝打开。
    try:
        import pythoncom
        import win32com.client as _win32
        pythoncom.CoInitialize()
        _word = _win32.Dispatch("Word.Application")
        _word.Visible = False
        _word.DisplayAlerts = 0
        try:
            _word.Documents.Open(str(docx_path), ReadOnly=True,
                                 AddToRecentFiles=False, Visible=False)
            record("Word 实际打开成功", True, "已由 Word 打开验证通过")
        finally:
            try:
                _word.Quit()
            except Exception:
                pass
            pythoncom.CoUninitialize()
    except ImportError:
        warn("未安装 pywin32", "跳过 Word 实际打开验证")
    except Exception as e:
        msg = str(e)
        if "损坏" in msg or "corrupt" in msg.lower():
            record("Word 实际打开成功", False, f"Word 拒绝打开：{msg[:70]}")
        else:
            warn("Word 打开验证未完成", msg[:70])


def check_markdown(nb_path):
    """检查 notebook 中 markdown 单元的块结构，防止表格等语法不渲染。"""
    print("\n7 Markdown 书写规范")
    if nb_path is None or not nb_path.exists():
        return
    import subprocess
    checker = Path(__file__).with_name("check_md.py")
    if not checker.exists():
        return warn("未找到 check_md.py", "跳过 markdown 检查")
    r = subprocess.run([sys.executable, str(checker)], capture_output=True)
    out = r.stdout.decode("utf-8", "replace")
    m = re.search(r"合计 (\d+) 处", out)
    n = int(m.group(1)) if m else -1
    det = ""
    if n > 0:
        det = "; ".join(l.strip() for l in out.split("\n") if l.strip().startswith("["))[:160]
    record("markdown 块结构合规（表格可正常渲染）", n == 0,
           f"{n} 处问题 {det}" if n > 0 else "0 处问题")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    folder = find_chapter(arg)
    print(f"章节目录：{folder}\n")

    nb_path = pick(folder, ["*.ipynb"], exclude=("checkpoint",))
    # 论文正文：优先 "*课设论文*.md"，并排除大纲与要求文档
    md_path = pick(folder, ["*课设论文*.md", "*论文*.md", "*.md"],
                   exclude=("课设大纲", "大纲", "要求"))
    docx_path = pick(folder, ["*.docx"], exclude=("~$",))

    nb = check_source_integrity(nb_path)
    check_files(folder, nb_path, md_path, docx_path)
    check_figures(folder, nb)
    n_refs = check_refs(md_path)
    check_paper(md_path, nb)
    check_consistency(md_path, docx_path, n_refs)
    check_markdown(nb_path)

    n_fail = sum(1 for r in results if r[0] == FAIL)
    n_warn = sum(1 for r in results if r[0] == WARN)
    print(f"\n{'='*66}\n合计 {len(results)} 项检查："
          f"通过 {len(results)-n_fail-n_warn}，不通过 {n_fail}，注意 {n_warn}\n{'='*66}")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
