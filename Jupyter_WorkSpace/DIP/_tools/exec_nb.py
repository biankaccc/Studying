# -*- coding: utf-8 -*-
"""
执行指定章节目录下的 notebook，并把输出内嵌写回原文件。

用法：
    python exec_nb.py 0202                 # 执行 DIP\0202 下的 notebook
    python exec_nb.py <notebook 完整路径>   # 直接指定文件

不依赖 nbclient / nbconvert（二者在本机 .my_env 下存在 IOPub 捕获异常），
直接用手写异步内核循环，输出捕获与写回过程完全可控。
写回前会先校验源码未被压平（source 行数组必须以 "\n" 连接还原）。
"""
import asyncio
import io
import json
import re
import sys
import time
from pathlib import Path

from jupyter_client.manager import AsyncKernelManager

DIP_ROOT = Path(r"D:\workspace\Jupyter_WorkSpace\DIP")


def resolve_notebook(arg=None):
    """定位目标 notebook：支持章节号、完整路径或留空（自动选最近修改的）。"""
    if arg:
        p = Path(arg)
        if p.is_file() and p.suffix == ".ipynb":
            return p
        folder = p if p.is_dir() else DIP_ROOT / str(arg)
        if not folder.is_dir():
            raise SystemExit(f"找不到章节目录：{folder}")
        nbs = sorted(folder.glob("*.ipynb"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not nbs:
            raise SystemExit(f"{folder} 下没有 .ipynb")
        return nbs[0]
    nbs = sorted(DIP_ROOT.glob("*/*.ipynb"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not nbs:
        raise SystemExit("DIP 目录下没有找到任何 notebook")
    return nbs[0]


NB = resolve_notebook(sys.argv[1] if len(sys.argv) > 1 else None)
LOG = NB.parent / "_scratch" / "run_report.txt"


def read_nb():
    return json.loads(io.open(NB, encoding="utf-8").read())


def cell_text(source):
    """
    把 notebook 的 source 还原成完整文本，自动兼容两种常见存法：

      A. 元素自带行尾换行（Jupyter 规范）：['a\\n', 'b\\n', 'c']  -> "".join
      B. 元素为裸行、不含换行：            ['a', 'b', 'c']        -> "\\n".join

    误判会直接破坏渲染：
      - 对 A 用 "\\n".join  -> 每个换行翻倍，表格/代码块被空行撑破，markdown 不再渲染；
      - 对 B 用 "".join     -> 所有行粘成一行，标题与表格语法全部失效。
    """
    if not isinstance(source, list):
        return source
    if len(source) > 1 and all(e.endswith("\n") for e in source[:-1]):
        return "".join(source)          # A 型
    return "\n".join(source)            # B 型（及单元素）


def check_source(nb):
    """正常 = 每个 code 单元还原后确实包含换行（不是被粘成一行的注释）。"""
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    bad = []
    for i, c in enumerate(code):
        txt = cell_text(c["source"])
        if len(txt) > 200 and txt.count("\n") < 2:
            bad.append((i, len(txt), txt.count("\n")))
    return (len(bad) == 0), f"code 单元 {len(code)} 个，内容异常单元 {len(bad)} 个"


async def execute(log_lines):
    nb = read_nb()
    ok, msg = check_source(nb)
    print("源码校验:", msg)
    if not ok:
        print("!! 源码已损坏，拒绝执行。请先重新运行 build_0202_nb.py")
        return False

    cell_paths = []          # (cell_index_in_nb, code_text, code_line_count)
    for idx, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        text = cell_text(c["source"])
        cell_paths.append((idx, text, len(text.splitlines())))

    km = AsyncKernelManager(kernel_name="python3")
    await km.start_kernel(cwd=str(NB.parent))
    kc = km.client()
    kc.start_channels()
    await kc.wait_for_ready(timeout=90)

    log_lines.append("内核: %s" % km.kernel_name)
    log_lines.append("工作目录: %s" % NB.parent)
    log_lines.append("=" * 78)

    exec_counter = 0
    failures = 0
    for idx, text, nlines in cell_paths:
        exec_counter += 1
        t0 = time.perf_counter()
        msg_id = kc.execute(text)
        outputs, err = [], None
        while True:
            m = await kc.get_iopub_msg(timeout=1800)
            if m.get("parent_header", {}).get("msg_id") != msg_id:
                continue
            t = m["msg_type"]
            content = m["content"]
            if t == "stream":
                outputs.append({"output_type": "stream", "name": content["name"],
                                "text": content["text"]})
            elif t == "execute_result":
                outputs.append({"output_type": "execute_result",
                                "execution_count": content.get("execution_count"),
                                "data": content.get("data", {}),
                                "metadata": content.get("metadata", {})})
            elif t == "display_data":
                outputs.append({"output_type": "display_data",
                                "data": content.get("data", {}),
                                "metadata": content.get("metadata", {})})
            elif t == "error":
                err = f"{content.get('ename')}: {content.get('evalue')}"
                outputs.append({"output_type": "error", "ename": content.get("ename"),
                                "evalue": content.get("evalue"),
                                "traceback": content.get("traceback", [])})
            elif t == "status" and content.get("execution_state") == "idle":
                break
        dt = time.perf_counter() - t0

        nb["cells"][idx]["execution_count"] = exec_counter
        nb["cells"][idx]["outputs"] = outputs

        head = text.split("\n")[0][:58] if text else ""
        n_img = sum(1 for o in outputs if o.get("output_type") in ("display_data", "execute_result")
                    and "image/png" in (o.get("data") or {}))
        flag = "ERR" if err else "ok "
        log_lines.append(f"[{flag}] 单元{idx:>2} {dt:7.2f}s 行数{nlines:>4} 输出{len(outputs):>3} 图{n_img:>2} | {head}")
        # 实时把进度打到标准输出，便于外部观察长任务（否则只能等全部跑完）
        try:
            print(f"[{flag}] 单元{idx:>2} {dt:7.2f}s  图{n_img:>2} | {head}",
                  flush=True)
        except Exception:
            pass
        printable = []
        for o in outputs:
            if o["output_type"] == "stream":
                printable.append(o["text"])
            elif o["output_type"] == "error":
                printable.append(f"{o['ename']}: {o['evalue']}")
                printable.append("\n".join(l[-300:] for l in o.get("traceback", [])[-10:]))
        body = "".join(printable)
        body = "\n".join(l for l in body.split("\n")
                         if "UserWarning" not in l and "plt." not in l
                         and "func(*args" not in l and "print_figure" not in l
                         and "self._get_loop" not in l)
        for l in body.split("\n"):
            if l.strip():
                log_lines.append("        " + l)
        if err:
            failures += 1
            log_lines.append("        !! " + err)
            break

    kc.stop_channels()
    await km.shutdown_kernel(now=True)

    if failures == 0:
        # 写回时把全部单元的 source 规范化为"每行以 \n 结尾"的数组。
        # 必须同时处理 markdown 单元：Jupyter 渲染 markdown 时按 "".join(source)
        # 拼接，元素若不含行尾换行，整段会被粘成一行，标题与表格语法全部失效。
        for c in nb["cells"]:
            if c["cell_type"] in ("markdown", "code"):
                c["source"] = cell_text(c["source"]).splitlines(keepends=True)
        io.open(NB, "w", encoding="utf-8").write(
            json.dumps(nb, ensure_ascii=False, indent=1))
        log_lines.append("")
        log_lines.append(">>> 全部执行成功，输出已内嵌写回 notebook")
        return True
    log_lines.append("")
    log_lines.append(">>> 存在失败单元，未写回")
    return False


log_lines = []
ok = asyncio.run(execute(log_lines))
report = "\n".join(log_lines)
LOG.parent.mkdir(parents=True, exist_ok=True)      # 章节目录下可能尚无 _scratch
io.open(LOG, "w", encoding="utf-8").write(report)
print(report)
sys.exit(0 if ok else 1)
