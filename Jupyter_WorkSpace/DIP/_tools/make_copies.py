# -*- coding: utf-8 -*-
"""
生成"副本"：把当前原件同步为带"副本"后缀的文件（docx 与 md 各一份）。

名称规则：<原文件名>副本.<ext>
"""
import io
import re
import shutil
from pathlib import Path

DIP = Path(r"D:\workspace\Jupyter_WorkSpace\DIP")
CHAPTERS = ("0202", "0303", "0402")

for chap in CHAPTERS:
    folder = DIP / chap
    print("=" * 70)
    print(chap)
    print("=" * 70)
    made = []
    for p in sorted(folder.iterdir()):
        if p.is_dir() or p.name.startswith("~$"):
            continue
        if not re.search(r"课设论文.*\.(docx|md)$", p.name):
            continue
        if "副本" in p.name:
            continue
        dst = p.with_name(p.stem + "副本" + p.suffix)
        shutil.copy2(p, dst)
        made.append(dst)
        print(f"  {dst.name:<60} {dst.stat().st_size/1024:8.1f} KB")
    if not made:
        print("  （未找到论文文件）")
