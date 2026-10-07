# -*- coding: utf-8 -*-
"""LaTeX 数学公式 -> OMML（Office Math Markup Language）转换器。

python-docx 不支持插入数学公式，Word 的原生公式格式是 OMML。
本模块把论文中使用的 LaTeX 子集转换为 OMML XML 节点，供 python-docx 直接 append 进段落，
从而在 Word 中显示为**真正的公式**（分式、根号、上下标、求和、希腊字母、重音等均可正常渲染，
且可在 Word 中双击编辑）。

支持的 LaTeX 子集：
    \\frac{a}{b}          -> 分式
    \\sqrt{a}             -> 根号
    \\sum_{}^{} \\prod_{}^{} \\int_{}^{}  -> 大型运算符
    a^{b} a_{b} a_{b}^{c} -> 上下标
    \\bar{a} \\hat{a} \\tilde{a} \\vec{a} -> 重音
    \\text{...} \\mathrm{...} \\mathcal{...} \\big \\Big \\left \\right
    \\alpha \\beta \\Gamma \\odot \\cdot \\times \\approx \\le \\ge \\pm \\infty
    \\qquad \\quad \\, \\; \\!  -> 间距
"""
import re

from lxml import etree
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"


def _e(tag):
    """创建 OMML 元素（带 m: 命名空间）。"""
    return OxmlElement("m:" + tag)


def _mr(text, *, italic=True, style=None):
    """创建一个数学 run（m:r）。italic=False 时用正体（m:nor）。"""
    r = _e("r")
    if not italic:
        rpr = _e("rPr")
        rpr.append(_e("nor"))
        r.append(rpr)
    t = _e("t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


def _sub_sup(children, tag):
    """构造 m:sub / m:sup / m:e 容器（nary 的上下限必须用专用标签）。"""
    e = _e(tag)
    for c in children:
        e.append(c)
    return e


def _grp(children, tag="e"):
    """把若干子节点包进指定的参数容器（默认 m:e）。"""
    e = _e(tag)
    for c in children:
        e.append(c)
    return e


# ---------------------------------------------------------------- 符号表
GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ",
    "sigma": "σ", "tau": "τ", "upsilon": "υ", "phi": "φ", "chi": "χ",
    "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ",
    "Pi": "Π", "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ",
    "Omega": "Ω",
}

OPS = {
    "cdot": "·", "times": "×", "div": "÷", "pm": "±", "mp": "∓",
    "approx": "≈", "neq": "≠", "ne": "≠", "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥",
    "ll": "≪", "gg": "≫", "in": "∈", "notin": "∉", "subset": "⊂",
    "cup": "∪", "cap": "∩", "odot": "⊙", "otimes": "⊗", "oplus": "⊕",
    "ast": "∗", "star": "⋆", "circ": "∘", "bullet": "∙",
    "leftarrow": "←", "rightarrow": "→", "to": "→", "leftrightarrow": "↔",
    "Rightarrow": "⇒", "Leftarrow": "⇐", "mapsto": "↦",
    "infty": "∞", "partial": "∂", "nabla": "∇", "propto": "∝",
    "equiv": "≡", "sim": "∼", "simeq": "≃", "cong": "≅",
    "downarrow": "↓", "uparrow": "↑", "angle": "∠", "perp": "⊥",
    "quad": "\u2003", "qquad": "\u2003\u2003", ",": "\u2009", ";": "\u2005",
    "!": "", " ": "\u2009",
}

LARGE_OPS = {
    "sum": "∑", "prod": "∏", "int": "∫", "iint": "∬", "oint": "∮",
    "bigcup": "⋃", "bigcap": "⋂", "lim": "lim", "max": "max", "min": "min",
}

ACCENTS = {
    "bar": "̄", "hat": "̂", "tilde": "̃", "vec": "⃗",
    "dot": "̇", "ddot": "̈", "overline": "̄",
}

# 正体内容（函数名、文字）
UPRIGHT_FUNCS = {"sin", "cos", "tan", "exp", "log", "ln", "max", "min",
                 "arg", "det", "dim", "lim", "gcd", "mod"}


# ---------------------------------------------------------------- 解析器
class _P:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def eof(self):
        return self.i >= len(self.s)

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    # --- 读取一个"组"：{...} 或单个 token ---
    def group(self):
        self.skip_space()
        if self.peek() == "{":
            self.i += 1
            nodes = self.parse_until("}")
            if self.peek() == "}":
                self.i += 1
            return nodes
        if self.peek() == "\\":
            return self.command()
        if not self.eof():
            ch = self.s[self.i]
            self.i += 1
            return [_mr(ch)]
        return []

    def skip_space(self):
        while self.i < len(self.s) and self.s[self.i] == " ":
            self.i += 1

    def parse_until(self, stop):
        out = []
        while not self.eof():
            if stop and self.peek() == stop:
                break
            out.extend(self.atom())
        return out

    # --- 读一个原子，并处理其后的上下标 ---
    def atom(self):
        self.skip_space()
        if self.eof():
            return []
        c = self.peek()

        if c == "\\":
            base = self.command()
        elif c == "{":
            self.i += 1
            base = self.parse_until("}")
            if self.peek() == "}":
                self.i += 1
        elif c in "}":
            self.i += 1
            return []
        elif c == "&":
            self.i += 1
            return [_mr(" ")]
        else:
            self.i += 1
            base = [_mr(c)]

        return self.apply_scripts(base)

    def apply_scripts(self, base):
        """处理紧跟其后的 _ 与 ^。"""
        sub = sup = None
        for _ in range(2):
            self.skip_space()
            p = self.peek()
            if p == "_":
                self.i += 1
                sub = self.group()
            elif p == "^":
                self.i += 1
                sup = self.group()
            else:
                break
        # 注意：上下标结构**必须**带属性元素（即使为空），否则 Word 报文件损坏。
        if sub is not None and sup is not None:
            n = _e("sSubSup")
            n.append(_e("sSubSupPr"))
            n.append(_grp(base))
            n.append(_grp(sub, "sub"))       # 下标必须用 m:sub
            n.append(_grp(sup, "sup"))       # 上标必须用 m:sup
            return [n]
        if sub is not None:
            n = _e("sSub")
            n.append(_e("sSubPr"))
            n.append(_grp(base))
            n.append(_grp(sub, "sub"))
            return [n]
        if sup is not None:
            n = _e("sSup")
            n.append(_e("sSupPr"))
            n.append(_grp(base))
            n.append(_grp(sup, "sup"))
            return [n]
        return base

    # --- 反斜杠命令 ---
    def command(self):
        assert self.peek() == "\\"
        self.i += 1
        # 单字符命令（转义符）
        if not self.eof() and not self.s[self.i].isalpha():
            ch = self.s[self.i]
            self.i += 1
            if ch == "\\":
                return [_mr("\n")]
            return [_mr(ch)]

        m = re.match(r"[A-Za-z]+", self.s[self.i:])
        name = m.group(0) if m else ""
        self.i += len(name)

        # 无参数的符号
        if name in GREEK:
            return [_mr(GREEK[name])]
        if name in OPS:
            return [_mr(OPS[name])]
        if name in UPRIGHT_FUNCS:
            r = _mr(name, italic=False)
            r.append(_mr("\u2061"))          # 函数应用符，避免与变量粘连
            return [r]
        if name in ("big", "Big", "bigg", "Bigg", "left", "right", "displaystyle",
                    "limits", "nolimits"):
            self.skip_space()
            if name in ("left", "right") and not self.eof() and self.peek() in "()[]|.":
                ch = self.s[self.i]
                self.i += 1
                if ch == ".":
                    return []
                return [_mr(ch)]
            return []
        if name == "text" or name == "mathrm" or name == "operatorname":
            inner = self.raw_group()
            return [_mr(inner, italic=False)]
        if name == "mathcal":
            inner = self.raw_group()
            return [_mr(inner, italic=True)]
        if name in ("mathbf", "boldsymbol"):
            return self.group()

        # 带参数的命令
        if name == "frac" or name == "dfrac" or name == "tfrac":
            num = self.group()
            den = self.group()
            n = _e("f")
            n.append(_e("fPr"))
            # 【关键】分式的分子/分母必须用 m:num / m:den，**不能**用通用的 m:e。
            # 用 m:e 会让 Word 报"文件可能已经损坏"并拒绝打开文档（已实测验证）。
            n.append(_grp(num, "num"))
            n.append(_grp(den, "den"))
            return [n]
        if name == "sqrt":
            body = self.group()
            n = _e("rad")
            n.append(_e("radPr"))
            n.append(_e("deg"))          # 次数可空，但标签须存在
            n.append(_grp(body))
            return [n]
        if name in LARGE_OPS:
            sym = LARGE_OPS[name]
            n = _e("nary")
            pr = _e("naryPr")
            chr_el = _e("chr")
            chr_el.set(qn("m:val"), sym)
            pr.append(chr_el)
            lim = _e("limLoc")
            lim.set(qn("m:val"), "undOvr")
            pr.append(lim)
            n.append(pr)
            sub = sup = None
            self.skip_space()
            if self.peek() == "_":
                self.i += 1
                sub = self.group()
                self.skip_space()
            if self.peek() == "^":
                self.i += 1
                sup = self.group()
            # OMML 规范：m:nary 的子元素顺序必须是 m:sub、m:sup、m:e
            # 上下限必须用专用标签 m:sub / m:sup，不能用 m:e（否则 Word 拒开文档）
            n.append(_sub_sup(sub or [], "sub"))
            n.append(_sub_sup(sup or [], "sup"))
            n.append(_grp([]))
            return [n]
        if name in ACCENTS:
            body = self.group()
            n = _e("acc")
            pr = _e("accPr")
            chr_el = _e("chr")
            chr_el.set(qn("m:val"), ACCENTS[name])
            pr.append(chr_el)
            n.append(pr)
            n.append(_grp(body))
            return [n]
        if name == "begin" or name == "end":
            self.raw_group()
            if name == "begin":
                return [_mr(" { ")]
            return [_mr(" } ")]
        if name in ("overline",):
            body = self.group()
            n = _e("bar")
            n.append(_e("barPr"))
            n.append(_grp(body))
            return [n]

        # 未知命令：退回为字面文本（不丢内容）
        return [_mr("\\" + name)]

    def raw_group(self):
        """读取 {...} 的原始文本（用于 \\text 等）。"""
        self.skip_space()
        if self.peek() != "{":
            if not self.eof():
                ch = self.s[self.i]
                self.i += 1
                return ch
            return ""
        self.i += 1
        depth, out = 1, []
        while self.i < len(self.s) and depth:
            ch = self.s[self.i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    self.i += 1
                    break
            out.append(ch)
            self.i += 1
        return "".join(out)


def _delim(children, beg="", end="", *, beg_chr="(", end_chr=")"):
    """构造带左右定界符的结构 m:d。"""
    d = _e("d")
    pr = _e("dPr")
    b = _e("begChr")
    b.set(qn("m:val"), beg_chr)
    en = _e("endChr")
    en.set(qn("m:val"), end_chr)
    pr.append(b)
    pr.append(en)
    d.append(pr)
    d.append(_grp(children))
    return d


def _matrix(rows):
    """rows: [[nodes,...], ...] -> OMML 矩阵 m:m。

    OMML 规范：m:m 含若干 m:mr；每个 m:mr 含若干 **并列的 m:e**（每列一个 m:e）。
    """
    m = _e("m")
    pr = _e("mPr")
    base = _e("baseJc")
    base.set(qn("m:val"), "center")
    pr.append(base)
    m.append(pr)
    for row in rows:
        mr = _e("mr")
        for cell in row:
            mr.append(_grp(cell))        # 每个单元格 = 一个 m:e
        m.append(mr)
    return m


def _parse_cases(inner):
    """把 cases/array 环境内容解析为「左侧花括号 + 矩阵」。"""
    rows_raw = re.split(r"\\\\", inner)
    rows = []
    for r in rows_raw:
        if not r.strip():
            continue
        cells = r.split("&")
        rows.append([_P(c).parse_until(None) for c in cells])
    if not rows:
        return []
    ncol = max(len(r) for r in rows)
    for r in rows:                       # 补齐列数，保证矩阵规整
        while len(r) < ncol:
            r.append([])
    return [_delim([_matrix(rows)], beg_chr="{", end_chr="")]


def latex_to_omml(latex):
    """把一段 LaTeX 数学式转换成 OMML 节点列表。"""
    # 去掉 \tag{n}、\label、\nonumber 等排版指令
    latex = re.sub(r"\\tag\{[^}]*\}", "", latex)
    latex = re.sub(r"\\label\{[^}]*\}", "", latex)
    latex = latex.replace("\\nonumber", "").replace("\\notag", "")

    # 先处理 cases / array 环境（内部含 & 与 \\，需专门解析）
    env_re = re.compile(r"\\begin\{(cases|array|aligned|matrix|pmatrix|bmatrix)\}"
                        r"(\{[^}]*\})?(.*?)\\end\{\1\}", re.S)
    out = []
    pos = 0
    for m0 in env_re.finditer(latex):
        out.extend(_P(latex[pos:m0.start()]).parse_until(None))
        env, _cols, inner = m0.group(1), m0.group(2), m0.group(3)
        beg, end = (("{", "") if env == "cases"
                    else ("(", ")") if env == "pmatrix"
                    else ("[", "]") if env == "bmatrix"
                    else ("", ""))
        body = _parse_cases(inner)
        if env == "cases":
            out.extend(body)
        else:
            rows = []
            for r in re.split(r"\\\\", inner):
                if r.strip():
                    rows.append([_P(c).parse_until(None) for c in r.split("&")])
            if rows:
                ncol = max(len(r) for r in rows)
                for r in rows:
                    while len(r) < ncol:
                        r.append([])
                mat = _matrix(rows)
                out.extend([_delim([mat], beg_chr=beg, end_chr=end)] if beg
                           else [mat])
        pos = m0.end()
    out.extend(_P(latex[pos:]).parse_until(None))
    return out


def _drop_redundant_ns(el):
    """
    【已停用，保留仅为记录教训】曾用于删除元素上冗余的 xmlns:m 声明。

    该实现调用 lxml 的 etree.cleanup_namespaces()，副作用是把根元素
    <w:document> 上由 mc:Ignorable 引用的扩展命名空间声明（o、r、v、wp、w10…）
    一并删除，导致 Word 报"文件可能已经损坏"而拒绝打开文档。
    **请勿再启用**，也不要自行调用 cleanup_namespaces。
    """
    return el          # 停用：见上方说明
    return el


# 注意：绝对不要在插入 OMML 后调用 lxml 的 etree.cleanup_namespaces()。
# 它会把根元素 <w:document> 上"当前未被引用"的命名空间声明（o、r、v、wp、w10 等
# 由 mc:Ignorable 引用的扩展命名空间）一并删除，导致 **Word 报"文件可能已经损坏"
# 而拒绝打开文档**（实测：根元素声明由 17 个锐减到 3 个即触发）。
# 子元素上重复声明 xmlns:m 虽冗余，但完全合法，务必保留原样。


# ---------------------------------------------------------------- 写入 Word
def add_omml_paragraph(doc, latex, number=None, *, tab_cm=(7.5, 15.0)):
    """
    在文档中插入一个居中公式段落，编号右对齐（用制表符实现）。
    """
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(4)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf.tab_stops.add_tab_stop(_cm(tab_cm[0]), WD_ALIGN_PARAGRAPH.CENTER)
    pf.tab_stops.add_tab_stop(_cm(tab_cm[1]), WD_ALIGN_PARAGRAPH.RIGHT)

    run = p.add_run("\t")
    _set_size(run, 10.5)

    omath = _e("oMath")
    for node in latex_to_omml(latex):
        omath.append(node)
    p._p.append(omath)

    if number:
        r2 = p.add_run("\t" + f"（{number}）")
        _set_size(r2, 10.5)
    return p


def _cm(v):
    from docx.shared import Cm
    return Cm(v)


def _set_size(run, size):
    from docx.shared import Pt
    run.font.size = Pt(size)


def append_inline_math(paragraph, latex, size=10.5, cn="宋体", en="Times New Roman"):
    """把行内公式作为 OMML 追加到已有段落。"""
    omath = _e("oMath")
    for node in latex_to_omml(latex):
        omath.append(node)
    paragraph._p.append(omath)
    return omath


def validate_omml(nodes):
    """
    校验生成的 OMML 片段是否符合 Schema 的关键约束，返回问题列表。

    重点检查在实现中真实踩过的坑：
      - 属性元素（*Pr）必须排在最前；
      - 各结构必须使用**正确的子元素标签**（如 nary 的上下限是 m:sub/m:sup，不是 m:e）；
      - 必填子元素不得缺失。
    """
    REQUIRED = {
        # 结构 -> (子元素顺序, 必须出现（可重复）的标签)
        "f": (["fPr", "num", "den"], ["num", "den"]),
        "rad": (["radPr", "deg", "e"], ["e"]),      # deg 可省略
        "sSub": (["sSubPr", "e", "sub"], ["e", "sub"]),
        "sSup": (["sSupPr", "e", "sup"], ["e", "sup"]),
        "sSubSup": (["sSubSupPr", "e", "sub", "sup"], ["e", "sub", "sup"]),
        "nary": (["naryPr", "sub", "sup", "e"], ["e"]),   # sub/sup 各至多一个
        "acc": (["accPr", "e"], ["e"]),
        "d": (["dPr", "e"], ["e"]),
        "m": (["mPr", "mr"], ["mr"]),
        "mr": (["e"], ["e"]),                             # 一或多个 e（每列一个）
        "func": (["funcPr", "fName", "e"], ["fName", "e"]),
        "limLow": (["limLowPr", "e", "lim"], ["e", "lim"]),
        "limUpp": (["limUppPr", "e", "lim"], ["e", "lim"]),
    }
    problems = []
    for node in nodes:
        for el in node.iter():
            if not isinstance(el.tag, str):
                continue
            tag = etree.QName(el).localname
            if tag not in REQUIRED:
                continue
            order, must = REQUIRED[tag]
            kids = [etree.QName(k).localname for k in el]

            # 1) 属性元素必须在首位，且最多一个
            pr_idx = [i for i, k in enumerate(kids) if k.endswith("Pr")]
            if pr_idx and pr_idx != [0]:
                problems.append(f"m:{tag}: 属性元素不在首位 -> {kids}")
            if len(pr_idx) > 1:
                problems.append(f"m:{tag}: 属性元素重复 -> {kids}")

            # 2) 所有子元素标签都必须是本结构允许的
            illegal = [k for k in kids if k not in order and not k.endswith("Pr")]
            if illegal:
                problems.append(f"m:{tag}: 出现非法子元素 {illegal}（允许 {order}）")

            # 3) 必填项不得缺失（考虑可重复）
            for req in must:
                if req not in kids:
                    problems.append(f"m:{tag}: 缺少必填 m:{req}（实际 {kids}）")

            # 4) 子元素出现顺序必须与规范一致（忽略重复项与"可省略且未出现"的项）
            seq = [k for k in kids if k in order]
            seen = []
            for k in seq:
                if not seen or seen[-1] != k:
                    seen.append(k)
            # 把期望序列中"可选且实际未出现"的项剔除后再比较
            expect = [k for k in order if k in seen or k in must]
            if seen != expect[:len(seen)]:
                problems.append(f"m:{tag}: 子元素顺序为 {seen}，期望 {order}")

            # 5) nary 的上下限：sub/sup 各至多一个
            if tag == "nary":
                if kids.count("sub") > 1 or kids.count("sup") > 1:
                    problems.append(f"m:nary: sub/sup 重复 -> {kids}")
    return problems


if __name__ == "__main__":
    # 自检：转换代表性公式并做结构校验
    tests = [
        r"R(x,y)=\frac{\sum_{u,v}\big[T(u,v)-\bar{T}\big]}"
        r"{\sqrt{\sum_{u,v}\big[T(u,v)-\bar{T}\big]^{2}}}",
        r"H(u,v)=\exp\left(-\frac{D^{2}(u,v)}{2D_0^{2}}\right)",
        r"\omega_k \leftarrow (1-\alpha)\omega_k + \alpha",
        r"\text{IoU}(A,B)=\frac{|A \cap B|}{|A \cup B|}",
        r"\sigma_k^2 \leftarrow \sigma_k^2 + \rho\,\big[(I_t-\mu_k)^2 - \sigma_k^2\big]",
        r"M(x,y)=\begin{cases} 1, & \text{像素为前景}\\ 0, & \text{像素为背景} \end{cases}",
        r"O\Big(\sum_{l=0}^{L-1} \frac{HW}{4^{l}} \cdot M_{l} N_{l}\Big) \approx O\Big(HWMN \cdot \frac{4}{3}\Big)",
        r"\mathcal{F}\{f(x,y) * h(x,y)\} = F(u,v)\cdot H(u,v)",
    ]
    allbad = 0
    for t in tests:
        nodes = latex_to_omml(t)
        bad = validate_omml(nodes)
        allbad += len(bad)
        flag = "OK  " if not bad else "!!  "
        print(f"{flag}结构问题 {len(bad)} | {t[:52]}")
        for b in bad[:3]:
            print(f"        {b}")
    print("\n自检:", "全部通过" if allbad == 0 else f"发现 {allbad} 个结构问题")


