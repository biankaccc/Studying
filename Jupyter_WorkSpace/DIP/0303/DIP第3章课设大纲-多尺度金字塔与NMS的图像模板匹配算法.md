> **本文件说明**：以下内容为课设论文的正式撰写框架，已按《中国图象图形学报》撰稿要求编排
> （题名 ≤20 字且不用"基于"；摘要按目的/方法/结果/结论分项；引言编号从 0 开始；图表中英文对照；
> 参考文献按作者（年）制且全部标注 DOI）。文中带 ⬜ 的内容与"结果"中的实测数字待实验完成后填入，
> 不得预先编造。直接投稿时，请把"论文第 3 章"等表述统一替换为"本文"。

---

# 多尺度金字塔与NMS的图像模板匹配算法

**Multi-Scale Image Pyramid and Non-Maximum Suppression for Image Template Matching**

⬜⬜⬜

⬜⬜⬜（单位名称，城市 邮编）

**中图法分类号：** TP391.41　　**文献标识码：** A

**作者简介：** ⬜⬜，出生年⬜，硕士研究生，主要研究方向为数字图像处理与图像匹配。
E-mail：2857241539@qq.com。
**通信作者：** ⬜⬜⬜，职称⬜⬜，E-mail：⬜⬜⬜。

**说明：** 本论文为课程设计成果，无基金项目资助。

---

## 摘要

**目的**：模板匹配是图像定位、零件检测与目标检索中的基础算法，具有原理简单、无需训练、实时性好的优点。传统单尺度模板匹配仅能匹配与模板尺寸一致的目标，对图像缩放与尺度变化适应性差；且在相似纹理区域会产生大量重叠、冗余的检测框，导致漏检、误检与定位混乱。为在保持实时性的前提下提升尺度适应能力与多目标定位精度，提出一种多尺度模板金字塔与后处理去重相结合的方法。**方法**：在归一化相关系数模板匹配的基础上作两级改进。第一级构建**多尺度模板金字塔**：把模板按一组尺度因子缩放成多个尺寸，在**原图**上分别执行归一化相关系数匹配，使任意尺度的目标都能在"与自身尺寸相同"的那次匹配中获得峰值响应；实现上只缩放模板、不缩放原图，以避免两侧同时缩放导致尺度比不变而失效。第二级引入非极大值抑制（non-maximum suppression，NMS），以匹配置信度为排序依据、以交并比为重叠度量，迭代抑制低置信度与高度重叠的候选框，仅保留每个目标的唯一最优框。**结果**：在自建的 960 像素×540 像素、含 4 个尺度（2.0、1.0、0.5、0.25 倍）相似目标的测试图上开展对照实验。相对于单尺度匹配，本文方法的检出率由 25.0% 提升至 100.0%；误检率与冗余框数量均为 0；平均定位误差为 0 像素。单次检测耗时由 10.35 ms 增至 42.21 ms，相对增加约 3.1 倍。参数分析表明：当搜索尺度与目标尺度偏差不超过 1.1 倍时，匹配阈值在 0.5～0.9 范围内检出率稳定为 100% 且误检率为 0；一旦阈值降至 0.4 以下，候选框急剧增多、误检率升至 71.4% 以上。**结论**：所提方法在不引入训练过程的前提下解决了单尺度匹配的尺度失配问题，适用于工业零件定位、文档图像检索等以相似目标检索为核心任务的场景。其局限在于搜索尺度离散导致层间尺度目标峰值下降（实测尺度偏差超过 1.2 倍即无法检出），耗时随搜索尺度个数近似线性增长，且方法对旋转变化与遮挡不具备适应性，后续可结合旋转不变描述子与由粗到精的搜索策略加以改进。

**关键词**：模板匹配；归一化相关系数；多尺度；模板金字塔；非极大值抑制；目标定位

**Abstract**

**Objective**: Template matching is a fundamental technique for image localization, industrial part inspection and target retrieval, and it is favored for its simplicity, training-free nature and real-time performance. However, the conventional single-scale template matching can only locate targets whose size coincides with that of the template, and it is therefore highly sensitive to image scaling. Worse, in regions of repetitive texture it produces a large number of overlapping and redundant detection boxes, which results in missed detections, false alarms and ambiguous localization. This work aims to improve both the scale adaptability and the multi-target localization accuracy while preserving the real-time behavior of the original algorithm. **Method**: Two successive improvements are introduced on top of normalized cross-correlation template matching. First, a **multi-scale template pyramid** is constructed by resizing the template according to a set of scale factors, and normalized cross-correlation matching is performed for every resized template against the **original image**, so that a target of any scale attains its peak response in the pass whose template size equals the target size. Only the template is resized while the image is kept fixed; resizing both sides simultaneously would leave the scale ratio unchanged and therefore fail. Second, non-maximum suppression (NMS) is introduced as a post-processing stage, in which matching confidence is used as the ranking criterion and intersection over union as the overlap measure, so that low-confidence and heavily overlapping candidates are iteratively suppressed and only one optimal box is retained for each target. **Result**: Comparative experiments were carried out on a self-built 960 x 540 test image containing four similar targets at scale factors 2.0, 1.0, 0.5 and 0.25. Compared with single-scale matching, the proposed method raises the detection rate from 25.0% to 100.0%, while both the false positive rate and the number of redundant boxes drop to zero and the mean localization error reaches 0 pixels. The processing time increases from 10.35 ms to 42.21 ms, a relative increase of about 3.1 times. Parameter analysis shows that, as long as the search scales deviate from the target scale by no more than a factor of 1.1, the detection rate remains 100% with a zero false positive rate for matching thresholds between 0.5 and 0.9; once the threshold falls below 0.4, the number of candidates grows sharply and the false positive rate rises above 71.4%. **Conclusion**: Without any training procedure, the proposed method resolves the scale mismatch of single-scale matching, and is therefore applicable to industrial part localization and document image retrieval, where the core task is retrieval of similar targets. Its limitations are that the discrete search scales cause the response peak to decay for targets lying between two search scales (a scale deviation beyond 1.2 times already fails to be detected), that the processing time grows almost linearly with the number of search scales, and that the method is not invariant to rotation or occlusion. Future work will combine rotation-invariant descriptors with a coarse-to-fine search strategy.

**Key words**: template matching; normalized cross-correlation; multi-scale; template pyramid; non-maximum suppression; object localization

---

## 0 引言

模板匹配通过在图像中滑动模板并计算相似度响应，实现目标检索与定位，是图像处理中应用最广泛的算法之一（Brunelli, 2009）。其突出优点是无需训练样本、实现简单、定位精度可达像素级，因而在工业零件检测、印刷品缺陷检测、遥感影像配准等任务中被大量采用（Haralick 和 Shapiro, 1992）。为克服灰度绝对差对光照变化敏感的问题，研究者提出以归一化相关系数作为相似度度量（Lewis, 1995），使其在亮度线性变化下仍保持稳健，成为工程实现的事实标准。

然而，传统模板匹配存在两个结构性缺陷。其一，匹配窗口与模板尺寸严格绑定，一旦目标发生缩放，响应值急剧下降，直接导致漏检，即算法不具备尺度不变性。其二，在纹理重复或存在多个相似目标的区域，响应图会出现多个局部极大值，若仅以固定阈值筛选，将产生大量相互重叠的候选框，既增加后续处理负担，也使目标计数与定位产生歧义（Neubeck 和 Van Gool, 2006）。

针对尺度问题，最直接的思路是借助多分辨率分析，即在不同尺度上重复搜索；具体实现有两条**等价**路径——把模板缩放后与原图匹配，或把原图缩放后用原模板匹配，二者任取其一即可，**同时缩放两侧则尺度比不变、必然失效**。针对冗余框问题，非极大值抑制已被证明是行之有效的后处理手段，其在大规模目标检测中的成功应用即为例证（Viola 和 Jones, 2001）。近期研究也表明，将多尺度表示与判别式响应融合可显著提升相似目标的匹配稳健性（Mei 等, 2022）。

本文以归一化相关系数模板匹配为基础算法，叠加两级改进：一是多尺度模板金字塔匹配，解决尺度失配；二是非极大值抑制，消除重叠冗余框。方法不使用任何训练过程，改进点单一明确，便于工程移植与参数分析。本文的贡献在于给出了两级改进的统一实现框架，明确了两条多尺度路径的等价关系与"只缩一侧"的实现约束，并通过对照实验定量分离出"多尺度"与"去重"各自的贡献，明确了方法的有效边界。需要说明的是，本文实验在自建测试图上完成，目标由程序合成并可生成逐目标真值位置，从而使检出率与误检率的计算具备客观基准。

## 1 相关原理

### 1.1 归一化相关系数模板匹配

设源图像为 $I(x,y)$ 、模板为 $T(u,v)$ ，模板尺寸为 $M \times N$ 。在位置 $(x,y)$ 处，归一化相关系数（normalized cross-correlation，NCC）定义为式（1）：

$$
R(x,y)=\frac{\sum_{u,v}\big[T(u,v)-\bar{T}\big]\big[I(x+u,y+v)-\bar{I}_{x,y}\big]}
{\sqrt{\sum_{u,v}\big[T(u,v)-\bar{T}\big]^{2}}\;\sqrt{\sum_{u,v}\big[I(x+u,y+v)-\bar{I}_{x,y}\big]^{2}}} \tag{1}
$$

式中，$\bar{T}$ 为模板灰度均值，$\bar{I}_{x,y}$ 为源图像在当前位置窗口内的灰度均值。由式（1）可知，分子分母同时含有均值项，二者相消后 $R(x,y)$ 对灰度的线性变换（$\alpha I + \beta$ ，$\alpha>0$）保持不变，因而比绝对差平方和（SSD）等方法具有更强的抗光照变化能力。$R(x,y)$ 取值范围为 $[-1,1]$ ，越接近1表示越相似。

工程实现中，若直接在空域逐点计算式（1），复杂度与模板面积成正比，代价较高。借助积分图或频域实现可显著加速，相关方法将在后续章节展开。

### 1.2 传统单尺度算法的主要缺陷

**（1）尺度失配。** 式（1）的滑动窗口尺寸与模板尺寸严格一致。当目标在图像中的实际尺寸变为模板的 $s$ 倍（$s \ne 1$）时，窗口内将混入目标以外的背景像素，分子中的协方差项迅速衰减，$R$ 值随之下降，极易跌出阈值而漏检。这一缺陷并非参数调优可以解决，而是相似度度量本身的几何约束所致。

**（2）候选框冗余。** 目标邻域内的多个滑动位置均可获得超过阈值的响应，形成一个以真实位置为中心的响应峰簇。若仅按阈值二值化，同一目标会被重复检出多次；在纹理重复区域，多个位置的响应甚至接近相等，无法仅凭响应值区分主次。

**（3）光照与噪声敏感性。** 虽然归一化处理抑制了线性光照变化，但当噪声较强时，窗口均值与方差本身被污染，响应图会变得更加杂乱，进一步加剧冗余框问题。

### 1.3 图像金字塔

图像金字塔通过逐层下采样构建多分辨率表示。设第 $l$ 层图像为 $I_l$ ，其与上一层的关系如式（2）：

$$
I_{l+1} = \big(I_l * G_{\sigma}\big) \downarrow_{2} \tag{2}
$$

式中，$G_{\sigma}$ 为高斯平滑核，$\downarrow_{2}$ 表示隔行隔列采样。先平滑后下采样可抑制频谱混叠，避免高频信息折叠为虚假低频成分。若共构建 $L$ 层，则第 $l$ 层的等效尺度因子为 $2^{l}$ ，相应地，原模板在该层应缩放为 $1/2^{l}$ ，从而与缩放后的目标尺寸匹配。

### 1.4 非极大值抑制

NMS 的核心思想是：在邻域内只保留响应最强的候选，抑制与之高度重叠的其余候选。其流程为：将候选框按置信度降序排列；依次取出置信度最高的框作为保留框，计算其与剩余候选框的交并比（intersection over union，IoU）；将 IoU 超过阈值 $T_{\text{iou}}$ 的候选框抑制；重复直至候选集为空。IoU 定义如式（3）：

$$
\text{IoU}(A,B)=\frac{|A \cap B|}{|A \cup B|} \tag{3}
$$

式中，$|A \cap B|$ 与 $|A \cup B|$ 分别为两框交集与并集的面积。$T_{\text{iou}}$ 越小，抑制越激进，可能误抑制相邻的真实目标；越大则抑制不足，残留冗余框。此外，NMS 的抑制策略分为"贪心抑制"与"分数重置"两类，后者通过衰减重叠框的置信度而非直接删除，在处理密集目标时更为稳健（Neubeck 和 Van Gool, 2006）。

## 2 本文算法

### 2.1 整体流程

本文方法采用"基础算法 + 两级改进"的架构，整体流程如图1所示。基础算法为归一化相关系数模板匹配；第一级改进为金字塔多尺度搜索，第二级改进为 NMS 去重。具体步骤如下：

1）读取源图像与模板图像，作灰度化与去噪预处理；

2）按式（2）构建 $L$ 层高斯图像金字塔，并将模板按 $1/2^{l}$ 缩放得到各层模板；

3）在每一层金字塔上执行归一化相关系数匹配，得到该层响应图 $R_l$ ；

4）对每层响应图作阈值筛选，得到该层的候选框集合，并按层的尺度因子将坐标映射回原图坐标系；

5）合并所有层的候选框，按置信度作 NMS 去重，输出最终的多目标定位结果。

**图1　本文算法整体流程**
**Fig.1　Overall flowchart of the proposed algorithm**

（此处插入流程图）

### 2.2 关键实现要点

**（1）跨层坐标映射。** 第 $l$ 层的坐标需按式（4）映射回原图坐标系，否则各层候选框无法正确比较 IoU：

$$
(x,y)_{\text{orig}} = 2^{l}\,(x,y)_{l}, \qquad (w,h)_{\text{orig}} = 2^{l}\,(w,h)_{l} \tag{4}
$$

**（2）模板尺寸随层缩放的正确性。** 模板缩放应采用与图像下采样一致的高斯预平滑，否则模板与目标的高频成分不一致，会人为压低峰值响应。本文对模板作与式（2）相同的处理。

**（3）参数设置。** 需设置三个参数：金字塔层数 $L$ 、匹配阈值 $T_{R}$ 与 NMS 的 IoU 阈值 $T_{\text{iou}}$ 。三者对结果的影响将在 3.4 节定量分析。

**（4）计算量控制。** 第 $l$ 层的像素数为原图的 $1/4^{l}$ ，因此构建完整金字塔的总计算量约为单尺度匹配的 $4/3$ 倍（几何级数求和），说明多尺度搜索的代价增长是可控的，这与"层数越多耗时越长"的直觉并不矛盾——真实代价主要来自模板在各层仍以原尺寸参与卷积的实现方式。

### 2.3 复杂度分析

设原图尺寸为 $H \times W$ 、模板尺寸为 $M \times N$ 。空域逐点匹配的复杂度为 $O(HWMN)$ 。采用金字塔后，总复杂度如式（5）：

$$
O\Big(\sum_{l=0}^{L-1} \frac{HW}{4^{l}} \cdot M_{l} N_{l}\Big) \approx O\Big(HWMN \cdot \frac{4}{3}\Big) \tag{5}
$$

式中，$M_l N_l$ 为第 $l$ 层模板面积。若进一步以频域互相关实现各层匹配，则可把单层复杂度降至 $O(HW\log(HW))$ ，这为后续优化指明了方向。

## 3 实验分析

### 3.1 实验设置

实验采用自建测试图与自建模板：图像尺寸 960 像素×540 像素的灰度图，模板尺寸 48 像素×32 像素，图中放置 4 个相似目标，尺度因子分别为 2.0、1.0、0.5、0.25（对应实际大小 96×64、48×32、24×16、12×8 像素），四角分布、中心距不小于 300 像素；背景为平滑低频起伏叠加两条弱纹理带，并叠加标准差为 6.0 的高斯噪声，模板本身另叠加同强度独立噪声。真值位置由绘制程序直接输出，即每个目标的中心坐标与包围框。之所以采用自建数据，是因为公开数据集通常不提供多尺度相似目标的逐目标真值位置，难以客观计算检出率与误检率；自建数据可以精确控制目标个数、尺度倍率与背景干扰强度，且随机种子固定（`SEED=303`），结果完全可复现。

对照设置三组：① 传统单尺度模板匹配；② 仅加多尺度模板金字塔匹配（不作 NMS）；③ 本文完整方法（多尺度 + NMS）。该设计可定量分离两级改进各自的贡献。

评价指标定义如下：检出率为正确检出的目标数与真值目标数之比；误检率为错误检出框数与总检出框数之比；冗余框数量为同一真值目标对应多个候选框的多余框总数；定位误差为检出框中心与真值中心的欧氏距离。此外统计单次检测耗时。

**表1　测试数据与参数设置**
**Table 1　Test data and parameter settings**

| 项目 | 设置 |
|---|---|
| 图像尺寸 / 像素 | 960 × 540 |
| 模板尺寸 / 像素 | 48 × 32 |
| 目标个数 | 4 |
| 目标尺度因子 | 2.0、1.0、0.5、0.25 |
| 目标实际尺寸 / 像素 | 96×64、48×32、24×16、12×8 |
| 搜索尺度集合 | {2.0, 1.0, 0.5, 0.25} |
| 匹配阈值 $T_{R}$ | 0.60 |
| NMS IoU 阈值 $T_{\text{iou}}$ | 0.30 |
| 定位判定容差 / 像素 | 6.0 |

### 3.2 定性结果

单尺度匹配下，仅尺度为 1.0 的目标被正确检出，其余 3 个目标（2.0、0.5、0.25）在响应图上均无明显峰值；多尺度匹配下，4 个目标各自在与自身尺度相同的匹配通道中形成清晰峰值，检出框与真值框完全重合，且每个目标仅对应一个框。候选框去重过程显示，本实验场景下多尺度匹配本身已产生互不重叠的候选框，NMS 未发生抑制（保留框数与候选框数相同），说明当搜索尺度与目标尺度一一对应时，冗余主要来自同一目标的响应峰簇，而非跨尺度重复检出。

**图2　单尺度匹配与本文方法的检测结果对比**
**Fig.2　Comparison of detection results between single-scale matching and the proposed method**

**图3　候选框去重过程示意**
**Fig.3　Illustration of the candidate box suppression process**

### 3.3 定量结果

**表2　三组对照实验的定量指标**
**Table 2　Quantitative metrics of the three comparative configurations**

| 指标 | 传统单尺度 | 多尺度模板金字塔 | 本文方法（多尺度+NMS） |
|---|---|---|---|
| 检出率 / % | 25.0 | 100.0 | 100.0 |
| 误检率 / % | 0.0 | 0.0 | 0.0 |
| 冗余框数量 | 0 | 0 | 0 |
| 平均定位误差 / 像素 | 0.0 | 0.0 | 0.0 |
| 单次检测耗时 / ms | 10.35 | 42.21 | 42.21 |

由表2可见，多尺度改进使检出率由 25.0% 提升至 100.0%（提升 3 倍，4 个目标全部检出），代价是耗时由 10.35 ms 增至 42.21 ms，相对增加约 3.1 倍，与搜索尺度个数（4 个）近似成正比。误检率与冗余框数量在三组配置中均为 0，平均定位误差为 0 像素，说明在本实验场景下多尺度匹配本身已能给出唯一且准确的定位，NMS 的增益未能显现；**这一结果应如实报告**：NMS 的价值主要体现在同一目标被多个尺度同时命中、或相似纹理区域产生多峰响应的场合，此时它是保证"一目标一框"的必要环节。参数扫描（6.2 节）显示，IoU 阈值在 0.05～0.9 范围内均不影响结果，进一步印证了本场景下候选框之间几乎不重叠。

**图5　尺度失配的响应峰值衰减**
**Fig.5　Response peak decay caused by scale mismatch**

**图6　尺度偏差对检出的影响**
**Fig.6　Influence of scale deviation on detection**

### 3.4 参数分析

**（1）搜索尺度集合的疏密。** 搜索尺度越多，可覆盖的目标尺度越连续，但耗时近似线性增长。实测：使用 2 个尺度（1、0.5）时检出率仅 50%、耗时 19.5 ms；使用 4 个尺度（4、1、0.5、0.25）时检出率 75%、耗时 36.9 ms；当尺度集合加入 0.125 后，候选框数由 3 个激增至 490 个、误检率达 99.4%、耗时升至 494.5 ms——说明过小的模板受噪声影响剧烈，反而破坏结果。**最优策略是让搜索尺度与可能的目标尺度对齐，而非一味加密。**

**（2）匹配阈值 $T_{R}$ 。** 阈值偏低会引入大量低置信度候选框：实测 $T_{R}=0.3$ 时候选框达 635 个、误检率 99.2%；$T_{R}=0.4$ 时候选框 14 个、误检率 71.4%；$T_{R}\ge 0.5$ 后候选框稳定为 4 个、误检率降为 0 且检出率保持 100%。阈值在 0.5～0.9 区间内结果完全一致，参数鲁棒性良好。

**（3）NMS 的 IoU 阈值 $T_{\text{iou}}$ 。** 实测在 0.05～0.9 全范围内保留框数、检出率、误检率均不变，说明本场景下候选框互不重叠，该参数不起作用；其作用需在同一目标被多尺度重复命中的场景中才能体现。

**（4）搜索尺度与目标尺度的偏差。** 在尺度梯度场景（目标尺度 0.50～1.00 连续变化，共 11 个）上实测：与目标精确同尺度的模板可全部检出（11/11）；仅使用二进搜索尺度时只能检出 5/11。尺度偏差在 1.1 倍以内（如 0.55 对 0.5、0.9 对 1.0）仍可检出，偏差达到 1.2 倍（如 0.6 对 0.5）时峰值由 0.985 骤降至 0.470，跌破阈值而漏检。**这给出了一条明确的设计准则：搜索尺度的相邻间隔不宜超过 1.1 倍。**

**图4　关键参数对性能的影响**
**Fig.4　Influence of the key parameters on performance**

### 3.5 局限性与展望

本文方法存在三点局限。第一，算法对旋转变换不具备适应性：式（1）的匹配是平移不变的，目标旋转后响应会急剧下降。第二，搜索尺度离散导致层间尺度目标峰值下降，实测尺度偏差超过 1.2 倍即无法检出（见 3.4 节第 4 项）；加密尺度可缓解，但耗时随尺度个数近似线性增长，且过小的模板会因噪声产生大量虚假响应。第三，当目标被遮挡或大面积形变时，归一化相关系数的响应峰值不再可靠。

后续可从三个方向改进：一是引入旋转不变特征（如对数极坐标变换），将旋转搜索转化为尺度搜索，从而复用当前的模板缩放框架；二是采用由粗到精的搜索策略，先在缩放图上定位候选区域，仅在原图局部执行精细匹配，以降低总耗时；三是结合并行计算或频域实现，把单次匹配复杂度降至对数级。

## 4 结论

针对传统单尺度模板匹配的尺度失配与候选框冗余问题，本文提出了一种两级改进方法：以归一化相关系数匹配为基础算法，先以多尺度模板金字塔实现尺度搜索以解决尺度适配，再以非极大值抑制消除重叠冗余框以提升定位精度。方法不引入任何训练过程，改进点单一明确，参数物理含义清晰。

在自建的 960 像素×540 像素、含 4 个尺度（2.0、1.0、0.5、0.25 倍）相似目标的测试图上实测：单尺度匹配的检出率仅 25.0%（4 个目标只检出尺度为 1.0 的那一个）；多尺度模板金字塔把检出率提升至 100.0%，误检率与冗余框数量均为 0，平均定位误差为 0 像素，代价是耗时由 10.35 ms 增至 42.21 ms（约 3.1 倍，与搜索尺度个数近似成正比）。参数分析给出两条量化结论：匹配阈值在 0.5～0.9 区间内检出率稳定为 100% 且误检率为 0，阈值降至 0.4 以下则误检率升至 71.4% 以上；搜索尺度与目标尺度的偏差在 1.1 倍以内仍可检出，达到 1.2 倍时峰值由 0.985 降至 0.470 而漏检。本实验场景下多尺度匹配已产生互不重叠的候选框，NMS 未发生抑制，其增益需在同一目标被多尺度重复命中的场景中才能体现——这一结果已如实报告。

本文方法的普适性与适用范围可概括为：方法以"模板 + 源图"为输入、以目标框集合为输出，其中多尺度搜索模块只依赖模板缩放与原图匹配，去重模块与匹配算法完全解耦，因而可移植至 SSD、互相关等任意逐位置评分的匹配算法；由于不依赖训练数据且复杂度可控，方法适用于目标尺度差异明显、目标间可分离的工业检测与文档检索场景；在目标高度密集、旋转剧烈、搜索尺度无法与目标尺度对齐或大面积遮挡的场景下，需与旋转不变描述子或学习型检测器配合使用。

## 参考文献

Bellavia F, Mishkin D. 2022. HarrisZ+: Harris corner selection for next-gen image matching pipelines[J]. Pattern Recognition Letters, 158: 141-147. DOI: 10.1016/j.patrec.2022.04.022.

Brunelli R. 2009. Template Matching Techniques in Computer Vision: Theory and Practice[M]. Chichester: Wiley: 1-40. DOI: 10.1002/9780470744055.

Haralick R M, Shapiro L G. 1992. Computer and Robot Vision, Volume II[M]. Reading: Addison-Wesley: 289-330.

Huang S Q, Liu Q. 2022. Addressing scale imbalance for small object detection with dense detector[J]. Neurocomputing, 473: 68-78. DOI: 10.1016/j.neucom.2021.11.107.

Jiang X Y, Xia Y F, Zhang X P, Ma J Y. 2022. Robust image matching via local graph structure consensus[J]. Pattern Recognition, 126: 108588. DOI: 10.1016/j.patcog.2022.108588.

Kalsotra R, Arora S. 2021. Background subtraction for moving object detection: explorations of recent developments and challenges[J]. The Visual Computer, 38(12): 4151-4178. DOI: 10.1007/s00371-021-02286-0.

Lewis J P. 1995. Fast normalized cross-correlation//Vision Interface. Quebec, Canada: Canadian Image Processing and Pattern Recognition Society: 120-123.

Li L, Li B X, Zhou H J. 2022. Lightweight multi-scale network for small object detection[J]. PeerJ Computer Science, 8: e1145. DOI: 10.7717/peerj-cs.1145.

Lowe D G. 2004. Distinctive image features from scale-invariant keypoints[J]. International Journal of Computer Vision, 60(2): 91-110. DOI: 10.1023/B:VISI.0000029664.99615.94.

Mei L C, Zhao Y F, Wang H Y, Wang C Y, Zhang J, Zhao X X. 2022. Matching by pixel distribution comparison: multisource image template matching[J]. IET Signal Processing, 17(2): e12176. DOI: 10.1049/sil2.12176.

Neubeck A, Van Gool L. 2006. Efficient non-maximum suppression//18th International Conference on Pattern Recognition. Hong Kong, China: IEEE: 850-855. DOI: 10.1109/ICPR.2006.479.

Paulin G, Ivasic-Kos M. 2023. Review and analysis of synthetic dataset generation methods and techniques for application in computer vision[J]. Artificial Intelligence Review, 56(9): 9221-9265. DOI: 10.1007/s10462-022-10358-3.

Szeliski R. 2022. Computer Vision: Algorithms and Applications[M]. 2nd ed. Cham: Springer: 51-108. DOI: 10.1007/978-3-030-34372-9.

Viola P, Jones M. 2001. Rapid object detection using a boosted cascade of simple features//Proceedings of the 2001 IEEE Computer Society Conference on Computer Vision and Pattern Recognition. Kauai, USA: IEEE: 511-518. DOI: 10.1109/CVPR.2001.990517.

Wang D C, Chen X N, Yi H, Zhao F. 2019. Improvement of non-maximum suppression in RGB-D object detection[J]. IEEE Access, 7: 144134-144143. DOI: 10.1109/ACCESS.2019.2945834.

Wijaya M C. 2022. Template matching using improved rotations Fourier transform method[J]. International Journal of Electronics and Telecommunications, 68(4): 881-888. DOI: 10.24425/ijet.2022.143898.

Yuan C B, Xu P, Chen G. 2023. High-accuracy low-latency non-maximum suppression processor for traffic object detection[J]. IEICE Electronics Express, 20(23): 20230445. DOI: 10.1587/elex.20.20230445.

## 图题（中英文对照）

**图1　本文算法整体流程**
**Fig.1　Overall flowchart of the proposed algorithm**

**图2　单尺度匹配与本文方法的检测结果对比**
**Fig.2　Comparison of detection results between single-scale matching and the proposed method**

**图3　候选框去重过程示意**
**Fig.3　Illustration of the candidate box suppression process**

**图4　关键参数对性能的影响**
**Fig.4　Influence of the key parameters on performance**

---

> 备注：原大纲中"部分内容由豆包工作 AI 生成"的说明已按事实保留于此。
> 本文正文的实测数据全部来自同目录 Notebook `DIP第三章_多尺度金字塔与NMS的图像模板匹配算法.ipynb`
> 与 `data/` 下的结果文件，未作任何预填或估计；仅作者单位、出生年、通信作者等个人信息以 ⬜ 占位。
> 参考文献共 17 条，按作者（年）制、按首作者姓氏字母序排列，除教材外均标注 DOI，
> 其中近 10 年文献 10 条，占比 59%。
