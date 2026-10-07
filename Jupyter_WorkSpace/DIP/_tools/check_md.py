# -*- coding: utf-8 -*-
"""
精确扫描 notebook 中 markdown 单元的真实渲染隐患（低误报版）。

只报以下确实会破坏渲染的写法：
  A 表格前一行为非空         -> 表格被当作普通文字，不渲染为表格
  B 表格后紧跟非空行且不是表格 -> 表格块被截断（Jupyter 下易整体失效）
  C 标题与其它块同行          -> 标题不渲染
  D 块内容与块标记挤在同一行   -> 列表项与后续内容合并、表格行粘连等
  E 分隔线 --- 后面紧跟标题    -> 被解析为下划线，破坏渲染
  F 表格分隔行缺失/列数不一致
  G 全角竖线 ｜ 或隐形字符
"""
import io
import json
import re
from pathlib import Path

DIP = Path(r"D:\workspace\Jupyter_WorkSpace\DIP")
NB_FILES = sorted(DIP.glob("*/[!_]*.ipynb"))
INVISIBLE = {"\u200b", "\u200c", "\u200d", "\ufeff", "\u00a0"}


def is_table(l):
    return l.strip().startswith("|")


def is_table_sep(l):
    s = l.strip()
    return s.startswith("|") and set(s) - set("|-: ") == set() and "-" in s


def is_heading(l):
    return bool(re.match(r"^\s{0,3}#{1,6}\s", l))


def is_hr(l):
    return bool(re.fullmatch(r"\s{0,3}(-{3,}|\*{3,}|_{3,})\s*", l))


def scan(path):
    nb = json.loads(io.open(path, encoding="utf-8").read())
    issues = []
    for ci, c in enumerate(nb["cells"]):
        if c["cell_type"] != "markdown":
            continue
        src = c["source"]

        # S. source 数组格式：元素必须保留行尾换行符
        #    Jupyter 渲染 markdown 时按 "".join(source) 拼接，元素若不带 "\n"，
        #    整段会被粘成一行，标题与表格语法全部失效。
        if isinstance(src, list) and len(src) > 1:
            without_lf = [e for e in src[:-1] if not e.endswith("\n")]
            if without_lf:
                issues.append(("S source元素缺行尾换行", ci, 0,
                               f"{len(without_lf)}/{len(src)-1} 个元素不以 \\n 结尾，"
                               f"渲染会粘成一行（例：{without_lf[0][:26]!r}）"))

        # S2. 换行翻倍：非空行之间出现 2 个以上连续空行元素
        #     （由 "元素自带换行 + 又用 '\n'.join 拼接" 造成，
        #      会把代码块与表格用空行撑破，Jupyter 下表格直接不渲染）
        if isinstance(src, list):
            run = 0
            for j, e in enumerate(src):
                is_blank = (not e.strip()) and (e.endswith("\n") or e == "")
                if is_blank:
                    run += 1
                else:
                    if run >= 2:
                        issues.append(("S2 换行翻倍（连续空行过多）", ci, j + 1 - run,
                                       f"连续 {run} 个空行元素，表格/代码块可能失效"))
                    run = 0

        lines = src if isinstance(src, list) else src.split("\n")
        n = len(lines)
        for j, ln in enumerate(lines):
            prev = lines[j - 1] if j > 0 else ""
            nxt = lines[j + 1] if j + 1 < n else ""
            s, sp, sn = ln.strip(), prev.strip(), nxt.strip()

            # A 表格前一行非空（且不是表格本身）
            if is_table(ln) and not is_table(prev) and j > 0 and sp:
                issues.append(("A 表格前缺空行", ci, j + 1, s[:54]))
            # B 表格后紧跟非空非表格行（表格中间被打断）
            if is_table(ln) and j + 1 < n and sn and not is_table(nxt):
                issues.append(("B 表格后缺空行", ci, j + 1, s[:54]))
            # C 标题与其它块同行
            if is_heading(ln) and ("|" in s or s.rstrip().endswith(">")):
                issues.append(("C 标题与他块同行", ci, j + 1, s[:54]))
            # E 分隔线后紧跟标题（会被当作下划线）
            if is_hr(ln) and j + 1 < n and is_heading(nxt):
                issues.append(("E 分隔线紧跟标题", ci, j + 1, s[:54]))
            # G 全角竖线 / 隐形字符
            if "\uff5c" in ln:
                issues.append(("G 全角竖线", ci, j + 1, s[:54]))
            if any(ch in INVISIBLE for ch in ln):
                issues.append(("G 隐形字符", ci, j + 1, s[:54]))

        # D 列表项与后续内容挤在一行（同行既有列表标记又有多余块标记）
        for j, ln in enumerate(lines):
            s = ln.strip()
            if re.match(r"^([-*+]|\d+[.)])\s", s) and s.count("|") >= 2 and "|" in s:
                if not s.startswith("|"):
                    issues.append(("D 列表内含表格竖线", ci, j + 1, s[:54]))

        # F 表格结构
        groups, cur = [], []
        for ln in lines:
            if is_table(ln):
                cur.append(ln)
            else:
                if cur:
                    groups.append(cur)
                cur = []
        if cur:
            groups.append(cur)
        for g in groups:
            ncols = [len(re.findall(r"(?<!\\)\|", r)) - 1 for r in g]
            sep_ok = len(g) >= 2 and is_table_sep(g[1])
            if not sep_ok:
                issues.append(("F 表格缺分隔行", ci, 0, g[0][:54]))
            elif len(set(ncols)) != 1:
                issues.append(("F 表格列数不一致", ci, 0,
                               f"{set(ncols)}  {g[0][:44]}"))
    return issues


total = 0
for nb in NB_FILES:
    iss = scan(nb)
    print(f"\n{'='*74}\n{nb.relative_to(DIP)}   —— {len(iss)} 处\n{'='*74}")
    for it in iss:
        print(f"  [{it[0]}] 单元#{it[1]} 行{it[2]}  「{it[3]}」")
    total += len(iss)
print(f"\n{'='*74}\n合计 {total} 处")
