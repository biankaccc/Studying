# -*- coding: utf-8 -*-
"""校验 0303/0402/0503/0602 四份改写后的大纲是否满足学报撰稿要求。"""
import io
import re
from pathlib import Path

DIP = Path(r"D:\workspace\Jupyter_WorkSpace\DIP")
TARGETS = [
    ("0202", "DIP第2章课设大纲-*.md"),
    ("0303", "DIP第3章课设大纲-*.md"),
    ("0402", "DIP第4章课设大纲-*.md"),
    ("0503", "DIP第5章课设大纲-*.md"),
    ("0602", "DIP第6章课设大纲-*.md"),
]
BANNED = ("基于", "一种", "利用", "方法")


def check(chap, pattern):
    files = list((DIP / chap).glob(pattern))
    print(f"\n{'='*72}\n【{chap}】")
    if not files:
        print("  !! 未找到改写后的文件")
        return 0, 0
    f = files[0]
    s = io.open(f, encoding="utf-8").read()
    print(f"  文件：{f.name}  ({f.stat().st_size/1024:.1f} KB)")
    fails, warns = 0, 0

    # 题名
    m = re.search(r"^# (.+)$", s, re.M)
    title = m.group(1).strip() if m else ""
    n_cjk = len(re.findall(r"[\u4e00-\u9fff]", title))
    ok = n_cjk <= 20
    fails += 0 if ok else 1
    print(f"  [{'OK ' if ok else 'FAIL'}] 题名 {n_cjk} 字：{title}")
    hit = [w for w in BANNED if w in title]
    if hit:
        fails += 1
    print(f"  [{'OK ' if not hit else 'FAIL'}] 题名无禁用词" + (f" 命中 {hit}" if hit else ""))

    # 摘要四项
    for lab in ("目的", "方法", "结果", "结论"):
        if f"**{lab}**" not in s:
            print(f"  [FAIL] 中文摘要缺『{lab}』")
            fails += 1
    else_ok = all(f"**{l}**" in s for l in ("目的", "方法", "结果", "结论"))
    if else_ok:
        print("  [OK ] 中文摘要四項齐全")
    for lab in ("Objective", "Method", "Result", "Conclusion"):
        if f"**{lab}**" not in s:
            print(f"  [FAIL] 英文摘要缺『{lab}』")
            fails += 1
    if all(f"**{l}**" in s for l in ("Objective", "Method", "Result", "Conclusion")):
        print("  [OK ] 英文摘要四项齐全")

    # 关键词 / 分类号
    kw = re.search(r"\*\*关键词\*\*：(.+)", s)
    n_kw = len([k for k in kw.group(1).split("；") if k.strip()]) if kw else 0
    ok = 5 <= n_kw <= 8
    fails += 0 if ok else 1
    print(f"  [{'OK ' if ok else 'FAIL'}] 关键词 {n_kw} 个（要求 5~8）")
    print(f"  [{'OK ' if '中图法分类号' in s else 'FAIL'}] 含中图法分类号")
    if "中图法分类号" not in s:
        fails += 1

    # 章节编号
    has_intro0 = "## 0 引言" in s
    print(f"  [{'OK ' if has_intro0 else 'FAIL'}] 引言编号为 0")
    if not has_intro0:
        fails += 1

    # 图表
    figs = len(re.findall(r"\*\*图\d　", s))
    tabs = len(re.findall(r"\*\*表\d　", s))
    print(f"  [{'OK ' if figs else 'WARN'}] 图题 {figs} 个；表题 {tabs} 个")

    # 参考文献
    if "## 参考文献" in s:
        body = s.split("## 参考文献")[1].split("## 图题")[0]
        items = [b.strip() for b in body.strip().split("\n\n") if b.strip()]
        items = [i for i in items if set(i.strip()) - set("-— \n")]
        no_doi = [i[:45] for i in items if "DOI:" not in i and "[M]" not in i]
        print(f"  [{'OK ' if len(items)>=15 else 'WARN'}] 文献 {len(items)} 篇"
              + ("" if len(items) >= 15 else "（不足 15 篇，需后续扩充）"))
        if len(items) < 15:
            warns += 1
        if no_doi:
            print(f"  [WARN] {len(no_doi)} 条无 DOI：{no_doi[0]}...")
            warns += 1

    # 占位符数量
    n_ph = s.count("⬜")
    print(f"  [INFO] 待填占位符 {n_ph} 处")
    return fails, warns


total_f, total_w = 0, 0
for chap, pat in TARGETS:
    f, w = check(chap, pat)
    total_f += f
    total_w += w

print(f"\n{'='*72}")
print(f"合计：不通过 {total_f} 项，警告 {total_w} 项")
