# FFT频域相关的多目标查找与NMS改进

**Multi-Target Detection by FFT Frequency-Domain Correlation with Non-Maximum Suppression**

⬜⬜⬜

⬜⬜⬜（单位名称，城市 邮编）

**中图法分类号：** TP391.41　　**文献标识码：** A

**作者简介：** ⬜⬜，出生年⬜，硕士研究生，主要研究方向为数字图像处理与图像匹配。
E-mail：2857241539@qq.com。
**通信作者：** ⬜⬜⬜，职称⬜⬜，E-mail：⬜⬜⬜。

**说明：** 本论文为课程设计成果，无基金项目资助。

---

## 摘要

**目的**：在一幅图像中查找多个相同目标，是工业检测与图像检索中的常见需求。空域模板匹配以滑动窗口逐点计算相似度，当模板尺寸为 $M\times N$ 、图像尺寸为 $H\times W$ 时运算量为 $O(HWMN)$ ，模板稍大即难以满足实时性；把匹配搬到频域可借助快速傅里叶变换显著降低单次匹配代价，但匹配结果只是一张相似度响应图，其峰值在目标周围连成一片，直接按阈值筛选会让同一目标被反复检出，无法直接给出目标个数与位置。

**方法**：以基于快速傅里叶变换（fast Fourier transform，FFT）的频域相关作为查找多个目标的主体方法，以非极大值抑制（non-maximum suppression，NMS）作为其上的主要改进。频域部分依据卷积定理把空域相关运算转化为频域共轭相乘：将源图与模板补零至 $(H+M-1)\times(W+N-1)$ 以满足线性相关条件，各自减去均值后作二维傅里叶变换，取模板频谱的复共轭与源图频谱逐点相乘，逆变换取实部并裁剪到有效区 $(H-M+1)\times(W-N+1)$ ，得到归一化到 $[0,1]$ 的相似度响应图，一次变换即可给出全图所有目标的候选位置。改进部分针对响应峰连成平台的问题，以响应值为置信度、以交并比为重叠度量，迭代抑制同一目标邻域内的次优峰值，使每个目标只保留唯一最优框。

**结果**：在自建的 512 像素×384 像素、含 6 个相同目标的灰度测试图上实验。补零后尺寸为 $415\times543$ ，FFT 匹配单次耗时 31.5 ms。频域相关结果与直接逐位置乘加的结果最大相对误差为 $3.89\times10^{-16}$ ，达到 float64 精度，实现正确性得到验证；6 个真值位置的响应值为 0.986～1.000，全部出现明显峰值。在匹配阈值 0.6 下，仅用 FFT 匹配会得到 87 个候选框（平均每个目标 14.5 个，严重重复）；叠加非极大值抑制后候选框降为 6 个，恰好等于真值目标数，检出率 100%，平均定位误差 0 像素，而抑制本身的耗时仅 0.28 ms，相对匹配耗时可忽略。参数分析表明：匹配阈值在 0.5～0.95 范围内，经抑制后结果均为 6 个正确框；交并比阈值在 0.05～0.7 范围内结果一致，增至 0.9 时残留 51 个框，说明该阈值不宜取得过大。

**结论**：基于 FFT 的频域相关可以一次给出全图所有目标的位置，复杂度 $O(HW\log(HW))$ 与模板面积无关；在其结果上叠加非极大值抑制，能在几乎不增加耗时（0.28 ms）的前提下把重复候选框由 87 个收敛为 6 个，实现"一个目标一个框"的多目标查找。该抑制步骤与匹配算法解耦，可直接移植到其他相关型匹配方法之后。方法的局限在于假定目标只发生平移，对旋转与尺度变化不具备适应性，且当目标高度密集时交并比判别会失效。

**关键词**：模板匹配；快速傅里叶变换；频域相关；非极大值抑制；多目标查找；峰值抑制

**Abstract**

**Objective**: Detecting multiple identical targets within a single image is a common requirement in industrial inspection and image retrieval. Spatial-domain template matching evaluates similarity point by point with a sliding window, and its computational cost is O(HWMN) for a template of size M x N and an image of size H x W, which becomes prohibitive as soon as the template grows; moving the matching operation into the frequency domain can greatly reduce the cost of a single match by means of the fast Fourier transform. However, the matching result is only a similarity response map whose peaks form a connected plateau around each target, so extracting candidates directly by thresholding detects the same target repeatedly and cannot give the number and positions of the targets.

**Method**: Frequency-domain correlation based on the fast Fourier transform (FFT) serves as the main method for locating multiple targets, and non-maximum suppression (NMS) is introduced as the principal improvement on top of it. In the frequency-domain part, the convolution theorem reformulates spatial correlation as conjugated multiplication in the frequency domain: the source image and the template are zero-padded to (H+M-1) x (W+N-1) to satisfy the linear-correlation condition, their means are removed, both are transformed by the two-dimensional Fourier transform, the complex conjugate of the template spectrum is multiplied point-wise with the source spectrum, and an inverse transform followed by taking the real part and cropping to the valid region of (H-M+1) x (W-N+1) yields a similarity response map normalized to [0,1]. A single transform therefore provides the candidate positions of all targets in the image. The improvement addresses the connected peak plateau: response magnitude serves as confidence and intersection over union as the overlap measure, so that sub-optimal peaks within the neighbourhood of a target are iteratively suppressed and exactly one optimal box is retained per target.

**Result**: Experiments were carried out on a self-built 512 x 384 grey-scale test image containing six identical targets. The zero-padded size is 415 x 543 and a single FFT match takes 31.5 ms. The maximum relative error between the frequency-domain correlation and direct point-wise multiply-accumulate is 3.89e-16, i.e. the float64 precision level, which verifies the correctness of the implementation; the response values at the six ground-truth positions range from 0.986 to 1.000, so all of them produce distinct peaks. At a matching threshold of 0.6, FFT matching alone yields 87 candidate boxes (14.5 per target on average, a severe duplication); after non-maximum suppression the number of candidates drops to 6, exactly equal to the number of ground-truth targets, with a detection rate of 100% and a mean localization error of 0 pixels, while the suppression itself costs only 0.28 ms, negligible compared with the matching cost. Parameter analysis shows that the result after suppression remains 6 correct boxes for matching thresholds between 0.5 and 0.95, and that intersection-over-union thresholds between 0.05 and 0.7 give identical results whereas a value of 0.9 leaves 51 boxes, indicating that this threshold should not be set too large.

**Conclusion**: Frequency-domain correlation based on the FFT provides the positions of all targets in one pass, with a complexity of O(HW log(HW)) that is independent of the template area. Superimposing non-maximum suppression on its result collapses 87 duplicate candidates into 6 at an almost negligible extra cost of 0.28 ms, which realizes one-box-per-target multi-target detection. Being decoupled from the matching algorithm, the suppression step can be transplanted directly behind other correlation-based matching methods. The method is limited in that it assumes pure translation, so it is not invariant to rotation or scaling, and its intersection-over-union criterion fails when targets are densely packed.

**Key words**: template matching; fast Fourier transform; frequency-domain correlation; non-maximum suppression; multi-target detection; peak suppression

---

## 0 引言

在一幅图像中查找多个相同目标，是工业零件计数、印刷品缺陷检测与文档图像检索中的常见需求。模板匹配通过度量模板与图像局部区域的相似性来定位目标，无需训练样本、原理简单，是这类任务的基础手段（Brunelli, 2009）。

空域模板匹配以滑动窗口逐点计算相似度。当模板尺寸为 $M\times N$ 、图像尺寸为 $H\times W$ 时，单次全图匹配的运算量为 $O(HWMN)$ ，与模板面积成正比（Haralick 和 Shapiro, 1992）。模板稍大，该量级即成为瓶颈。

频域方法为解决该瓶颈提供了成熟途径。依据卷积定理，空域的相关运算等价于频域中的逐点乘积，而快速傅里叶变换把单次变换的复杂度降至 $O(HW\log(HW))$ ，与模板面积无关（Gonzalez 和 Woods, 2018）。因此把匹配迁移到频域，可以**一次变换就得到全图所有位置的相似度**，从而实现多目标的同时查找（Szeliski, 2022）。

然而，频域匹配给出的只是**相似度响应图**，还不是目标框。响应峰在真实位置周围连成一片平台，若直接把每个超过阈值的位置都算作候选，同一目标会产生几十个相互重叠的框，无法给出正确目标数（Neubeck 和 Van Gool, 2006）。非极大值抑制正是消除这类重复框的标准手段，其在大规模目标检测中的成功应用已充分证明其有效性（Viola 和 Jones, 2001）。

本文以基于 FFT 的频域相关作为查找多个目标的**主体方法**，以非极大值抑制作为其上的**主要改进**，形成"补零去均值 → FFT 匹配 → 阈值筛选 → NMS 去重"的完整流程。工作内容包含三点：一是给出频域匹配的正确性判据，即与直接逐位置乘加的结果应达到浮点精度一致；二是厘清实现中"补零"与"有效区裁剪"的必要性，并指出**响应图必须归一化后阈值才有意义**；三是通过实验定量说明仅用 FFT 匹配的重复检出问题，以及叠加 NMS 后的改善幅度。

**图1　本文算法整体流程**
**Fig.1　Overall flowchart of the proposed algorithm**

![图1](data/fig_0_pipeline.png)

## 1 方法原理

### 1.1 空域模板匹配

空域模板匹配以归一化相关系数为相似度度量，在位置 $(x,y)$ 处定义为式（1）：

$$
R(x,y)=\frac{\sum_{u,v}\big[T(u,v)-\bar{T}\big]\big[I(x+u,y+v)-\bar{I}_{x,y}\big]}
{\sqrt{\sum_{u,v}\big[T(u,v)-\bar{T}\big]^{2}}\;\sqrt{\sum_{u,v}\big[I(x+u,y+v)-\bar{I}_{x,y}\big]^{2}}} \tag{1}
$$

式中 $I$ 为源图像，$T$ 为模板，$\bar{T}$ 与 $\bar{I}_{x,y}$ 分别为模板均值与当前窗口均值。式（1）对灰度线性变换不变，抗光照变化能力较强（Lewis, 1995），但每个候选位置都要重新计算窗口内的和、平方和与乘积和，代价高。

### 1.2 基于 FFT 的频域匹配

设源图与模板去均值后的二维傅里叶变换分别为 $F(u,v)$ 与 $G(u,v)$ 。由卷积定理，互相关对应频域中共轭相乘，见式（2）：

$$
\mathcal{F}\big\{f \star g\big\} = F(u,v)\,G^{*}(u,v) \tag{2}
$$

式中 $\star$ 表示互相关，$G^{*}$ 为 $G$ 的复共轭。于是整幅图的相似度响应可由一次逆变换得到，见式（3）：

$$
c(x,y)=\mathcal{F}^{-1}\big\{F(u,v)\,G^{*}(u,v)\big\} \tag{3}
$$

与空域逐位置计算相比，式（3）的复杂度为 $O(HW\log(HW))$ ，**与模板面积无关**，且一次变换即覆盖全图所有位置，因此天然适合"在图像中查找多个目标"。

实现时有三个要点：

**（1）补零。** 式（2）成立的前提是**循环相关**。要得到与空域线性相关相同的结果，必须把两幅图补零至 $(H+M-1)\times(W+N-1)$ ；否则图像的右下角会"环绕"到左上角，在响应图边界产生虚假峰值。

**（2）去均值。** 图像的直流分量在频域位于原点，幅值远大于其余分量。若不先扣除均值，响应将被图像均值主导，弱目标被完全淹没。

**（3）裁剪与归一化。** 逆变换的结果只有前 $(H-M+1)$ 行与前 $(W-N+1)$ 列对应"模板完整落入图像"，应裁剪到该有效区。此外，式（3）的输出是**无界的**（其量纲与图像灰度、像素数有关），必须先归一化到 $[0,1]$ 再设阈值——否则一个看似合理的阈值（如 0.6）几乎不起过滤作用，会保留大量位置并导致后续处理量爆炸。这是实现中最容易忽略的一点。

### 1.3 频域匹配的固有不足

式（3）的响应图在真实位置周围是一个**连续的峰值平台**：模板与目标严格对齐时响应最大，轻微错位时下降缓慢。若把每个超过阈值的位置都视为候选框，同一目标会产生大量相邻的重叠框，既无法给出正确目标数，也使定位结果混乱。

问题的根源在于：式（3）只做了**全局**去均值，未做窗口内归一化，因此响应峰比式（1）的归一化相关更平缓，过阈值区域更宽。这说明**仅靠阈值无法保证"一个目标一个框"**，必须引入基于几何关系的后处理。

### 1.4 主要改进：非极大值抑制

非极大值抑制以置信度为排序依据、以交并比（intersection over union，IoU）为重叠度量，流程为：将候选框按置信度降序排列；取出最高分框作为确定目标并保留；计算它与其余框的 IoU，将超过阈值 $T_{\text{iou}}$ 的框抑制；重复上述过程直至候选集为空。IoU 定义如式（4）：

$$
\text{IoU}(A,B)=\frac{|A\cap B|}{|A\cup B|} \tag{4}
$$

本场景中所有候选框尺寸都等于模板尺寸，因此 IoU 完全由两框的中心位移决定：同一目标的重复框几乎完全重合，IoU 接近 1，会被抑制；不同目标相距较远，IoU 接近 0，会被保留。这一几何可分性正是 NMS 在此有效的根本原因。

## 2 实验与分析

### 2.1 实验设置

实验采用自建测试图：512 像素×384 像素灰度图，模板 32 像素×32 像素，图中放置 6 个相同目标，按 3 列×2 行网格分布，中心分别位于 $(110,100)$ 、$(256,100)$ 、$(400,100)$ 、$(110,270)$ 、$(256,270)$ 、$(400,270)$ 像素处。目标图案为亮底加深色十字与边框，背景为低频起伏叠加标准差 6.0 的高斯噪声，模板另叠加同强度独立噪声。真值坐标由绘制程序直接输出。采用自建数据的理由是公开数据集通常不提供同一模板在一幅图中多处出现的逐目标坐标，难以客观统计检出率与定位误差；自建数据可精确控制目标个数与位置，且随机种子固定（`SEED=402`），结果完全可复现。

参数设置为：匹配阈值 0.6，NMS 的交并比阈值 0.3，定位判定容差 6 像素。评价指标为检出率（正确检出目标数与真值目标数之比）与平均定位误差（检出框中心与真值中心的欧氏距离）。

**表1　测试数据与参数设置**
**Table 1　Test data and parameter settings**

| 项目 | 设置 |
|---|---|
| 图像尺寸 / 像素 | 512 × 384 |
| 模板尺寸 / 像素 | 32 × 32 |
| 目标个数 | 6（3×2 网格） |
| 补零后尺寸 / 像素 | 415 × 543 |
| 响应图有效区 / 像素 | 353 × 481 |
| 匹配阈值 $T$ | 0.60 |
| NMS 交并比阈值 $T_{\text{iou}}$ | 0.30 |

### 2.2 FFT 匹配的正确性与多目标查找

图2给出源图、模板与真值位置。图3给出 FFT 响应图，其中 6 个真值位置均出现明显峰值。

FFT 匹配单次耗时 31.5 ms。为验证实现正确，在相同画布上把 FFT 结果与"直接逐位置乘加"的结果对比，两者最大相对误差为 $3.89\times10^{-16}$ ，达到 float64 精度，表明频域实现正确。6 个真值位置的响应值依次为 0.998、0.996、1.000、0.999、0.996、0.986，最小值 0.986，全部远高于阈值。

**图2　测试场景、模板与真值位置**
**Fig.1　Test scene, template and ground-truth positions**

![图2](data/fig_2_scene.png)

**图3　FFT 响应图与响应剖面**
**Fig.2　FFT response map and response profile**

![图3](data/fig_3_response.png)

### 2.3 直接阈值筛选的重复检出问题

FFT 匹配给出的是响应图，还需筛选才能得到目标框。最直接的做法是"响应超过阈值的位置都算候选框"。

在匹配阈值 0.6 下，这样得到的候选框共 **87 个**，而真值目标只有 6 个，平均每个目标产生 14.5 个候选框。从候选框位置可以看到，除 6 个置信度接近 1 的正确位置外，其余都是与它们相邻的重叠框。这说明**仅用 FFT 匹配无法直接完成多目标查找**。

**图4　直接阈值筛选产生的重复候选框**
**Fig.3　Duplicate candidate boxes produced by direct thresholding**

![图4](data/fig_4_redundant.png)

### 2.4 叠加 NMS 后的改进效果

在候选框上执行非极大值抑制（交并比阈值 0.3），结果如表2。

**表2　改进前后的对比（匹配阈值 0.6）**
**Table 2　Comparison before and after the improvement**

| 配置 | 框数 | 检出率 / % | 平均定位误差 / 像素 | 耗时 / ms |
|---|---|---|---|---|
| 仅 FFT 匹配（阈值筛选） | 87 | 100.0 | 0.00 | 31.52 |
| FFT 匹配 + NMS（本文） | **6** | 100.0 | 0.00 | 31.79 |

由表2可见：候选框由 87 个收敛为 6 个，**恰好等于真值目标数**，检出率保持 100%，平均定位误差为 0 像素；NMS 本身仅耗时 0.28 ms，相对 31.5 ms 的匹配耗时可忽略。因此该改进以极小代价解决了 FFT 匹配的重复检出问题。

**图5　改进前后的检测结果对比**
**Fig.4　Detection results before and after the improvement**

![图5](data/fig_5_nms.png)

### 2.5 参数影响

**（1）匹配阈值 $T$ 。** 表3给出阈值由 0.5 增至 0.95 的结果。阈值越低，过阈值位置越多（0.5 时 170 个，0.95 时 6 个），但**经 NMS 后始终为 6 个正确框**，检出率与定位误差均不受影响。这说明 NMS 使方法对阈值具有较强鲁棒性；不过阈值过低会显著增加候选框数量与抑制负担，故不宜取过小值。

**表3　匹配阈值的影响**
**Table 3　Influence of the matching threshold**

| 匹配阈值 | 候选框数 | NMS 后框数 | 检出率 / % | 平均定位误差 / 像素 |
|---|---|---|---|---|
| 0.50 | 170 | 6 | 100.0 | 0.00 |
| 0.60 | 87 | 6 | 100.0 | 0.00 |
| 0.70 | 36 | 6 | 100.0 | 0.00 |
| 0.80 | 18 | 6 | 100.0 | 0.00 |
| 0.90 | 6 | 6 | 100.0 | 0.00 |
| 0.95 | 6 | 6 | 100.0 | 0.00 |

**（2）NMS 的交并比阈值 $T_{\text{iou}}$ 。** 表4给出该阈值的影响。在 0.05～0.7 范围内，保留框数均为 6、检出率 100%、定位误差 0，说明方法对取值不敏感；当增至 0.9 时，由于抑制过弱，残留 51 个框。因此该阈值应在 0.05～0.7 范围内选取，本文取 0.3。

**表4　NMS 交并比阈值的影响**
**Table 4　Influence of the intersection-over-union threshold**

| 交并比阈值 | 保留框数 | 检出率 / % | 平均定位误差 / 像素 |
|---|---|---|---|
| 0.05 | 6 | 100.0 | 0.00 |
| 0.10 | 6 | 100.0 | 0.00 |
| 0.20 | 6 | 100.0 | 0.00 |
| 0.30 | 6 | 100.0 | 0.00 |
| 0.50 | 6 | 100.0 | 0.00 |
| 0.70 | 6 | 100.0 | 0.00 |
| 0.90 | 51 | 100.0 | 0.00 |

**图6　两个关键参数的影响**
**Fig.5　Influence of the two key parameters**

![图6](data/fig_6_params.png)

### 2.6 局限性与展望

本文方法存在三点局限。第一，式（3）的频域相关本质是平移不变运算，目标一旦发生旋转或尺度变化，响应峰值将显著下降，这是方法最根本的边界。第二，尽管采用了补零策略，有限尺寸图像仍存在边界效应，靠近边缘的目标响应会被截断。第三，去重依赖目标间的空间可分性，当目标高度密集甚至相互重叠时，交并比判别会失效。

后续可从三个方向改进：一是引入多尺度金字塔与旋转不变的极坐标变换，把旋转与尺度搜索纳入同一框架；二是采用分数重置型抑制策略，通过衰减重叠框置信度而非直接删除，以改善密集目标场景；三是利用相位相关方法提升抗噪能力并缓解边界效应。

## 3 结论

本文以基于快速傅里叶变换的频域相关作为在图像中查找多个目标的主体方法，并叠加非极大值抑制作为主要改进。

频域部分依据卷积定理把空域相关转化为频域共轭相乘：把源图与模板补零至 $(H+M-1)\times(W+N-1)$ 、各自去均值后作二维傅里叶变换，取模板频谱的复共轭与源图频谱逐点相乘，逆变换取实部、裁剪到有效区并归一化，即得到全图的相似度响应图。该方法一次变换覆盖所有位置，复杂度 $O(HW\log(HW))$ 与模板面积无关。实测其与直接逐位置乘加的结果最大相对误差为 $3.89\times10^{-16}$ ，达到 float64 精度，6 个真值位置的响应值为 0.986～1.000，全部正确出峰。

改进部分针对响应峰连成平台导致的重复检出：在匹配阈值 0.6 下，仅用 FFT 匹配会得到 87 个候选框（平均每目标 14.5 个），叠加非极大值抑制后收敛为 6 个，恰好等于真值目标数，检出率 100%、平均定位误差 0 像素，而抑制本身仅耗时 0.28 ms。参数分析表明匹配阈值在 0.5～0.95、交并比阈值在 0.05～0.7 范围内结果均稳定正确。

本文方法的适用范围可概括为：以"源图 + 模板"为输入、以目标框集合为输出，其中频域匹配模块可替换为任意满足平移不变假设的相关型匹配算法，去重模块与匹配算法完全解耦，故具备良好的模块化移植性；由于不依赖训练数据且复杂度可控，适用于目标数量不定、对实时性有一定要求的工业检测与文档检索场景；在存在旋转、显著尺度变化或目标高度重叠的场景下，需与多尺度金字塔、旋转不变变换或学习型检测器配合使用。

## 参考文献

Bellavia F, Mishkin D. 2022. HarrisZ+: Harris corner selection for next-gen image matching pipelines[J]. Pattern Recognition Letters, 158: 141-147. DOI: 10.1016/j.patrec.2022.04.022.

Brunelli R. 2009. Template Matching Techniques in Computer Vision: Theory and Practice[M]. Chichester: Wiley: 1-40. DOI: 10.1002/9780470744055.

Gonzalez R C, Woods R E. 2018. Digital Image Processing[M]. 4th ed. New York: Pearson: 178-252.

Haralick R M, Shapiro L G. 1992. Computer and Robot Vision, Volume II[M]. Reading: Addison-Wesley: 289-330.

Huang S Q, Liu Q. 2022. Addressing scale imbalance for small object detection with dense detector[J]. Neurocomputing, 473: 68-78. DOI: 10.1016/j.neucom.2021.11.107.

Jiang X Y, Xia Y F, Zhang X P, Ma J Y. 2022. Robust image matching via local graph structure consensus[J]. Pattern Recognition, 126: 108588. DOI: 10.1016/j.patcog.2022.108588.

Kalsotra R, Arora S. 2021. Background subtraction for moving object detection: explorations of recent developments and challenges[J]. The Visual Computer, 38(12): 4151-4178. DOI: 10.1007/s00371-021-02286-0.

Lewis J P. 1995. Fast normalized cross-correlation//Vision Interface. Quebec, Canada: Canadian Image Processing and Pattern Recognition Society: 120-123.

Li L, Li B X, Zhou H J. 2022. Lightweight multi-scale network for small object detection[J]. PeerJ Computer Science, 8: e1145. DOI: 10.7717/peerj-cs.1145.

Mei L C, Zhao Y F, Wang H Y, Wang C Y, Zhang J, Zhao X X. 2022. Matching by pixel distribution comparison: multisource image template matching[J]. IET Signal Processing, 17(2): e12176. DOI: 10.1049/sil2.12176.

Neubeck A, Van Gool L. 2006. Efficient non-maximum suppression//18th International Conference on Pattern Recognition. Hong Kong, China: IEEE: 850-855. DOI: 10.1109/ICPR.2006.479.

Paulin G, Ivasic-Kos M. 2023. Review and analysis of synthetic dataset generation methods and techniques for application in computer vision[J]. Artificial Intelligence Review, 56(9): 9221-9265. DOI: 10.1007/s10462-022-10358-3.

Szeliski R. 2022. Computer Vision: Algorithms and Applications[M]. 2nd ed. Cham: Springer: 51-108. DOI: 10.1007/978-3-030-34372-9.

Viola P, Jones M. 2001. Rapid object detection using a boosted cascade of simple features//Proceedings of the 2001 IEEE Computer Society Conference on Computer Vision and Pattern Recognition. Kauai, USA: IEEE: 511-518. DOI: 10.1109/CVPR.2001.990517.

Wang D C, Chen X N, Yi H, Zhao F. 2019. Improvement of non-maximum suppression in RGB-D object detection[J]. IEEE Access, 7: 144134-144143. DOI: 10.1109/ACCESS.2019.2945834.

Wijaya M C. 2022. Template matching using improved rotations Fourier transform method[J]. International Journal of Electronics and Telecommunications, 68(4): 881-888. DOI: 10.24425/ijet.2022.143898.

Yuan C B, Xu P, Chen G. 2023. High-accuracy low-latency non-maximum suppression processor for traffic object detection[J]. IEICE Electronics Express, 20(23): 20230445. DOI: 10.1587/elex.20.20230445.

## 图题（中英文对照）

**图2　测试场景、模板与真值位置**
**Fig.1　Test scene, template and ground-truth positions**

**图3　FFT 响应图与响应剖面**
**Fig.2　FFT response map and response profile**

**图4　直接阈值筛选产生的重复候选框**
**Fig.3　Duplicate candidate boxes produced by direct thresholding**

**图5　改进前后的检测结果对比**
**Fig.4　Detection results before and after the improvement**

**图6　两个关键参数的影响**
**Fig.5　Influence of the two key parameters**

---

## 附录：本章结果文件

| 文件 | 说明 |
| --- | --- |
| `data/scene_src.png` | 自建测试源图（6 个目标） |
| `data/scene_tpl.png` | 模板图像 |
| `data/ground_truth.csv` | 逐目标真值坐标 |
| `data/metrics.csv` | 改进前后的对比指标 |
| `data/sweep_thresh.csv` | 匹配阈值扫描结果 |
| `data/sweep_iou.csv` | NMS 交并比阈值扫描结果 |
| `data/key_numbers.json` | 关键数字汇总 |
| `data/fig_*.png` | 论文插图 |

对应 Notebook：`DIP第四章_基于FFT的多目标查找与NMS改进.ipynb`
