# -*- coding: utf-8 -*-
"""
把 0202 / 0303 论文摘要的四要素改为各自单独成段（规范 6.1 要求）。

原摘要把 目的/方法/结果/结论 挤在同一段，需按 `**方法**` 等标记切分为独立段落。
"""
import io
import re
from pathlib import Path

DIP = Path(r"D:\workspace\Jupyter_WorkSpace\DIP")
TARGETS = {
    "0202": "第二章课设论文_高斯混合模型前景掩码的傅里叶高斯低通净化.md",
    "0303": "第三章课设论文_多尺度金字塔与NMS的图像模板匹配算法.md",
}
LABELS = ("目的", "方法", "结果", "结论")

for chap, name in TARGETS.items():
    p = DIP / chap / name
    s = io.open(p, encoding="utf-8").read()

    m = re.search(r"(##\s*摘要\s*\n)(.*?)(\n\*\*Abstract\*\*)", s, re.S)
    if not m:
        print(f"{chap}: 未找到摘要区间，跳过")
        continue
    head, body, tail = m.group(1), m.group(2), m.group(3)
    body_one = " ".join(x.strip() for x in body.split("\n") if x.strip())

    # 按 **标签** 切分为 4 段
    positions = []
    for lab in LABELS:
        mm = re.search(r"\*\*" + lab + r"\*\*", body_one)
        if mm:
            positions.append((mm.start(), lab))
    positions.sort()
    if len(positions) != 4:
        print(f"{chap}: 只找到 {len(positions)} 个要素标记，跳过")
        continue

    segs = []
    for k, (pos, lab) in enumerate(positions):
        end = positions[k + 1][0] if k + 1 < len(positions) else len(body_one)
        segs.append(body_one[pos:end].strip())

    new_body = "\n\n" + "\n\n".join(segs) + "\n"
    s2 = s[:m.start()] + head + new_body + tail + s[m.end():]
    io.open(p, "w", encoding="utf-8").write(s2)

    # 校验
    m2 = re.search(r"##\s*摘要\s*\n(.*?)(?=\n\*\*Abstract\*\*)", s2, re.S)
    got = [l.strip()[:6] for l in m2.group(1).split("\n")
           if re.match(r"^\*\*(目的|方法|结果|结论)\*\*", l.strip())]
    n_cjk = len(re.findall(r"[\u4e00-\u9fff]", s2))
    print(f"{chap}: 摘要独立成段 {len(got)}/4  -> {got}")
    print(f"       论文大小 {p.stat().st_size/1024:.1f} KB，汉字 {n_cjk}")
