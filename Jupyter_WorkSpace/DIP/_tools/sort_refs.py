# -*- coding: utf-8 -*-
"""把论文 Markdown 的参考文献按首作者字母序重排，并输出排序后的顺序供 Word 生成器同步。"""
import io
import re
from pathlib import Path

MD = next(Path(r"D:\workspace\Jupyter_WorkSpace\DIP\0202").glob("*课设论文*.md"))
s = io.open(MD, encoding="utf-8").read()

head, rest = s.split("## 参考文献", 1)
if "## 图题" in rest:
    refs_block, tail = rest.split("## 图题", 1)
    tail = "## 图题" + tail
else:
    refs_block, tail = rest, ""

items = [b.strip() for b in refs_block.strip().split("\n\n") if b.strip()]
items = [i for i in items if set(i.strip()) - set("-— \n")]          # 剔除纯分隔线


def sort_key(entry):
    """按首作者姓氏排序；连字符视作空格，使 St-Charles 排在 Stauffer 之后。"""
    one = " ".join(entry.split())
    surname = re.split(r"[,\s]", one)[0]
    surname = surname.replace("-", " ")
    return re.sub(r"[^A-Za-z ]", "", surname).lower()


items.sort(key=sort_key)

new_block = "\n\n## 参考文献\n\n" + "\n\n".join(items) + "\n\n"
io.open(MD, "w", encoding="utf-8").write(head + new_block.lstrip("\n") + tail)

print(f"重排完成，共 {len(items)} 条：")
for i, it in enumerate(items, 1):
    print(f"  {i:>2} {' '.join(it.split())[:72]}")
