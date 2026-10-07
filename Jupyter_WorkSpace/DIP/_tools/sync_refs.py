# -*- coding: utf-8 -*-
"""
把 build_docx.py 中的参考文献顺序与论文 Markdown 对齐。
做法：先解析出 builder 中原有的 30 条文献，再按 Markdown 的字母序重排。
"""
import ast
import io
import re
from pathlib import Path

MD = next(Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0202").glob("*课设论文*.md"))
BUILDER = Path(r"D:\workspace\Jupyter_WorkSpace\DIP\_tools\build_docx.py")


def key(text):
    """首作者姓氏（连字符视作空格，使 St-Charles 排在 Stauffer 之后）。"""
    one = " ".join(text.split())
    surname = re.split(r"[,\s]", one)[0].replace("-", " ")
    return re.sub(r"[^A-Za-z ]", "", surname).lower()


# ---- 1. 读取 Markdown 的顺序 ----
s = io.open(MD, encoding="utf-8").read()
body = s.split("## 参考文献")[1].split("## 图题")[0]
md_items = [b.strip() for b in body.strip().split("\n\n") if b.strip()]
md_items = [i for i in md_items if set(i.strip()) - set("-— \n")]
md_order = [key(i) for i in md_items]
print(f"Markdown 文献 {len(md_items)} 条")

# ---- 2. 解析 builder 里的 refs 列表 ----
src = io.open(BUILDER, encoding="utf-8").read()
m = re.search(r"\nrefs = \[\n(.*?)\n\]\n", src, re.S)
if not m:
    raise SystemExit("未找到 refs 列表")
block = m.group(1)
lines = [l for l in block.split("\n") if l.strip()]
parts, cur = [], ""
for l in lines:
    cur += l.strip()
    if not cur.endswith(","):
        continue
    parts.append(cur)
    cur = ""
old_items = ast.literal_eval("[" + "".join(parts) + "]")
print(f"builder 文献 {len(old_items)} 条")

by_key = {}
for o in old_items:
    by_key.setdefault(key(o), []).append(o)

missing = [k for k in md_order if k not in by_key]
if missing:
    print("!! builder 中缺少以下文献:", missing)

new_items = []
for k in md_order:
    if by_key.get(k):
        new_items.append(by_key[k].pop(0))
for k, rest in by_key.items():          # builder 中多出来的
    new_items.extend(rest)
print(f"重排后 {len(new_items)} 条，顺序是否与 Markdown 一致: "
      f"{[key(i) for i in new_items] == md_order}")


def fmt(t, indent="    "):
    """折行成 Python 相邻字符串字面量，避免超长行。"""
    words, lines_, cur = t.split(" "), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 100:
            lines_.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines_.append(cur)
    out = []
    for l in lines_:
        out.append(indent + '"' + l.replace('"', '\\"') + ' "')
    out[-1] = out[-1][:-1] + '",'
    return "\n".join(out)


src = src[:m.start(1)] + "\n" + "\n".join(fmt(t) for t in new_items) + "\n" + src[m.end(1):]
io.open(BUILDER, "w", encoding="utf-8").write(src)
print("build_docx.py 的参考文献顺序已同步")
