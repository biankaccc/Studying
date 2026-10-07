# DIP 课设工具目录

本目录存放**所有章节共用**的脚本。章节专属的构建脚本放在各章节目录内（如 `0202\build_nb.py`）。

## 目录约定

```
D:\workspace\Jupyter_WorkSpace\DIP\
├── _tools\                     ← 本目录：跨章节通用工具
│   ├── verify.py               总校验（交付前必跑）
│   ├── check_md.py             校验 notebook 的 Markdown 书写规范
│   ├── check_outlines.py       校验各章论文框架是否满足学报格式
│   ├── exec_nb.py              执行 notebook 并内嵌输出
│   ├── build_docx_md.py        由论文 Markdown 生成 Word（公式转 OMML）
│   ├── mathimg.py             LaTeX → PNG 公式渲染器（默认方案）
│   ├── omml.py                 LaTeX → OMML 公式转换器（备选，本机 Word 拒开）
│   ├── build_docx.py           0202 专用 Word 生成器（手写排版）
│   ├── sort_refs.py            参考文献按首作者字母序重排
│   ├── sync_refs.py            让 Word 生成器的文献顺序与 Markdown 对齐
│   └── _backup_outlines\       各章原始大纲的备份（改写前的存档）
├── 0202\
│   ├── build_nb.py             ★ 本章 notebook 的源码（改代码改这里，不改 ipynb）
│   ├── make_figures.py         ★ 本章插图生成
│   ├── <章标题>.ipynb           交付物 ①
│   ├── <论文标题>.md            交付物 ②
│   ├── <论文标题>.docx          交付物 ③
│   ├── data\                   交付物 ④（图/视频/CSV/JSON）
│   └── _scratch\               临时脚本与执行日志，可随时清空
└── 0303\ 0402\ 0503\ 0602\     其他章节，结构同上
```

## 标准工作流

### 1. 修改 notebook 内容

**不要直接改 `.ipynb`**——它是由 `0202\build_nb.py` 生成的。改 `build_nb.py`，然后：

```powershell
python D:\workspace\Jupyter_WorkSpace\DIP\0202\build_nb.py
```

### 2. 执行 notebook 并把输出内嵌

```powershell
python D:\workspace\Jupyter_WorkSpace\DIP\_tools\exec_nb.py 0202
```

留空参数则自动选最近修改过的 notebook。执行日志写入 `<章节>\_scratch\run_report.txt`。

> 为什么不用 `nbconvert --execute`：本机 `.my_env` 下 nbclient/nbconvert 会出现 IOPub 捕获异常
> （执行耗时 2.9 s、零输出，实际未执行）。`exec_nb.py` 用手写异步内核循环绕开该问题。

### 3. 生成论文 Word

```powershell
python D:\workspace\Jupyter_WorkSpace\DIP\_tools\build_docx_md.py 0303
```

该工具由论文 Markdown 直接生成 Word，并**把 `$...$` 与 `$$...$$` 公式转换为 OMML 原生数学对象**
（分式、根号、上下标、大型运算符等可正常渲染，且能在 Word 中双击编辑）。

> 公式相关注意：
> - python-docx 不支持公式，必须转 OMML，转换器见 `omml.py`；
> - 公式文字不在 `paragraph.text` 中，提取 Word 文本做核对时须遍历 OMML 的 `m:t` 节点；
> - 生成前请**关闭 Word**，否则 `~$xxx.docx` 锁文件会导致无法覆盖写入。

0202 章另有一份手写排版的生成器 `build_docx.py`（内容与图表为逐段书写，非 Markdown 驱动）。

若改动过参考文献顺序，先运行 `sort_refs.py` 再运行 `sync_refs.py`，保证 md 与 docx 顺序一致。

### 4. 交付前校验（必跑）

```powershell
python D:\workspace\Jupyter_WorkSpace\DIP\_tools\verify.py 0202
```

覆盖 7 大类共 36 项：

| 类别 | 检查内容 |
| --- | --- |
| 1 源码完整性 | 代码单元是否被粘成单行、是否全部已执行、图是否内嵌、有无残留错误 |
| 2 文件齐备性 | ipynb / md / docx / data 是否齐全，有无散落日志 |
| 3 图件与字形 | PNG 尺寸是否合理、有无中文字形缺失告警 |
| 4 参考文献 | 数量 ≥15、近 10 年 ≥60%、DOI 覆盖、字母序 |
| 5 论文合规 | 题名 ≤20 字且无禁用词、摘要四项、图表双语、分类号 |
| 6 交付物一致性 | 文献数、三线表数、内嵌图数、**公式 OMML 结构与残留**、表格数值 |
| 7 Markdown 规范 | notebook 中 markdown 块结构、source 换行格式 |

退出码非 0 表示存在「不通过」项。

## 依赖

`.my_env` 环境需具备：`numpy` `scipy` `matplotlib` `opencv-python` `scikit-image`
`pandas` `jupyter_client` `python-docx`。

## 论文框架（大纲）

每章的论文框架存放在 `DIP\xxxx\DIP第N章课设大纲-<论文题目>.md`，已按学报要求编排。
文件名格式统一为 `DIP第N章课设大纲-<论文题目>.md`（题名取自该文件的一级标题）。
校验可直接运行：

```powershell
python D:\workspace\Jupyter_WorkSpace\DIP\_tools\check_outlines.py
```

检查项：题名 ≤20 字且无禁用词、中英文摘要四项齐全、关键词 5~8 个、含中图法分类号、
引言编号为 0、图表中英文对照、参考文献数量与 DOI 覆盖。

各章原始大纲的改写前存档位于 `_backup_outlines\`。

## 约定

- 交付物目录只放**能一键重建产物**的脚本，临时脚本一律进 `_scratch\`，任务完成后删除。
- 论文、notebook、`data\` 三处的数字必须完全一致（`verify.py` 第 6 类会交叉核对）。
- 所有随机过程固定种子，保证重跑结果一致。
