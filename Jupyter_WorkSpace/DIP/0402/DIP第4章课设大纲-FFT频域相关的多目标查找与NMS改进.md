# FFT频域相关的多目标查找与NMS改进

**Multi-Target Detection by FFT Frequency-Domain Correlation with Non-Maximum Suppression**

⬜⬜⬜　　⬜⬜⬜（单位名称，城市 邮编）

**中图法分类号：** TP391.41　　**文献标识码：** A

**作者简介：** ⬜⬜，出生年⬜，硕士研究生，主要研究方向为数字图像处理与图像匹配。
E-mail：2857241539@qq.com。　**通信作者：** ⬜⬜⬜，职称⬜⬜，E-mail：⬜⬜⬜。

**说明：** 本论文为课程设计成果，无基金项目资助。

---

## 摘要

**目的**：在一幅图像中查找多个相同目标是工业检测与图像检索中的常见需求。空域模板匹配以滑动窗口逐点计算相似度，运算量为 $O(HWMN)$ ，模板稍大即难以满足实时性；频域匹配可借助快速傅里叶变换降低单次代价，但其结果是相似度响应图，峰值在目标周围连成一片，直接按阈值筛选会让同一目标被反复检出。

**方法**：以基于快速傅里叶变换（FFT）的频域相关作为查找多个目标的主体方法，以非极大值抑制（NMS）作为主要改进。频域部分依据卷积定理把空域相关转化为频域共轭相乘：源图与模板补零至 $(H+M-1)\times(W+N-1)$ ，各自去均值后作二维傅里叶变换，取模板频谱的复共轭与源图频谱逐点相乘，逆变换取实部、裁剪到有效区并归一化到 $[0,1]$ ，一次变换即得到全图所有目标的候选位置。改进部分针对响应峰连成平台的问题，以响应值为置信度、以交并比为重叠度量迭代抑制，使每个目标只保留唯一最优框。

**结果**：在自建的 512 像素×384 像素、含 6 个相同目标的灰度测试图上实验。补零后尺寸 415×543，FFT 匹配单次耗时 31.5 ms。频域相关与直接逐位置乘加的结果最大相对误差为 $3.89\times10^{-16}$ ，达到 float64 精度；6 个真值位置响应值为 0.986～1.000。匹配阈值 0.6 下，仅用 FFT 匹配得到 87 个候选框（平均每目标 14.5 个）；叠加 NMS 后降为 6 个，恰等于真值目标数，检出率 100%、平均定位误差 0 像素，抑制本身仅耗时 0.28 ms。参数分析表明匹配阈值在 0.5～0.95 范围内结果均为 6 个正确框，交并比阈值在 0.05～0.7 范围内结果一致，增至 0.9 时残留 51 个框。

**结论**：基于 FFT 的频域相关一次给出全图所有目标位置，复杂度 $O(HW\log(HW))$ 与模板面积无关；叠加 NMS 以 0.28 ms 的极小代价把重复候选框由 87 个收敛为 6 个，实现"一个目标一个框"的多目标查找，且该步骤与匹配算法解耦，可移植到其他相关型匹配方法之后。方法局限在于假定目标只发生平移，对旋转与尺度变化不具备适应性，目标高度密集时交并比判别会失效。

**关键词**：模板匹配；快速傅里叶变换；频域相关；非极大值抑制；多目标查找；峰值抑制

**Abstract**

**Objective**: Detecting multiple identical targets within a single image is a common requirement in industrial inspection and image retrieval. Spatial-domain template matching evaluates similarity point by point with a sliding window at a cost of O(HWMN), which becomes prohibitive as soon as the template grows; frequency-domain matching can reduce the cost of a single match by means of the fast Fourier transform, but its result is only a similarity response map whose peaks form a connected plateau around each target, so direct thresholding detects the same target repeatedly.

**Method**: Frequency-domain correlation based on the fast Fourier transform (FFT) serves as the main method for locating multiple targets, and non-maximum suppression (NMS) is introduced as the principal improvement. By the convolution theorem the source image and the template are zero-padded to (H+M-1) x (W+N-1), their means are removed, both are transformed by the two-dimensional Fourier transform, the complex conjugate of the template spectrum is multiplied point-wise with the source spectrum, and an inverse transform followed by taking the real part, cropping to the valid region and normalizing to [0,1] yields the candidate positions of all targets in one pass. The improvement iteratively suppresses sub-optimal peaks using response magnitude as confidence and intersection over union as the overlap measure, so that exactly one optimal box is retained per target.

**Result**: Experiments were carried out on a self-built 512 x 384 grey-scale test image containing six identical targets. The zero-padded size is 415 x 543 and a single FFT match takes 31.5 ms. The maximum relative error between the frequency-domain correlation and direct point-wise multiply-accumulate is 3.89e-16, the float64 precision level, and the response values at the six ground-truth positions range from 0.986 to 1.000. At a matching threshold of 0.6, FFT matching alone yields 87 candidate boxes (14.5 per target); after non-maximum suppression the number drops to 6, exactly the number of ground-truth targets, with a detection rate of 100% and a mean localization error of 0 pixels, while the suppression itself costs only 0.28 ms. Parameter analysis shows that matching thresholds between 0.5 and 0.95 all give 6 correct boxes, and that intersection-over-union thresholds between 0.05 and 0.7 give identical results whereas 0.9 leaves 51 boxes.

**Conclusion**: Frequency-domain correlation based on the FFT provides the positions of all targets in one pass with a complexity of O(HW log(HW)) independent of the template area; superimposing non-maximum suppression collapses 87 duplicate candidates into 6 at a negligible extra cost of 0.28 ms, realizing one-box-per-target multi-target detection, and being decoupled from the matching algorithm the step can be transplanted behind other correlation-based methods. The method assumes pure translation, so it is not invariant to rotation or scaling, and its intersection-over-union criterion fails for densely packed targets.

**Key words**: template matching; fast Fourier transform; frequency-domain correlation; non-maximum suppression; multi-target detection; peak suppression

---

## 0 引言

- 背景：多目标查找的需求；空域匹配 $O(HWMN)$ 的效率瓶颈。
- 频域途径：卷积定理 + FFT，复杂度 $O(HW\log HW)$ 且与模板面积无关，一次变换覆盖全图。
- 新问题：响应图只是中间结果，峰值平台导致重复检出，无法直接给出目标数。
- 本文做法：FFT 频域相关为**主体方法**，NMS 为**主要改进**；给出正确性判据（与直接乘加一致）、实现要点（补零、裁剪、归一化）与定量实验。

## 1 方法原理

### 1.1 空域模板匹配

归一化相关系数定义（式1）；对灰度线性变换不变（Lewis, 1995）；逐位置重算导致复杂度高。

### 1.2 基于 FFT 的频域匹配

- 卷积定理：互相关对应频域共轭相乘（式2）；响应由一次逆变换得到（式3）。
- 实现要点：**补零**（避免循环相关产生边界假峰）、**去均值**（避免直流主导）、**裁剪有效区 + 归一化**（输出无界，不归一化则阈值失效）。

### 1.3 频域匹配的固有不足

响应峰在目标周围连成平台；式(3)只做全局去均值、未做窗口内归一化，峰比式(1)更平缓，故仅靠阈值无法保证"一目标一框"。

### 1.4 主要改进：非极大值抑制

以置信度排序、以交并比（式4）为重叠度量迭代抑制；本场景候选框尺寸统一，交并比由中心位移唯一决定，几何可分性好。

## 2 实验与分析

### 2.1 实验设置

自建 512×384 灰度图，6 个目标（3×2 网格），模板 32×32，背景为低频起伏加噪声；真值由程序输出；固定随机种子。评价指标：检出率、平均定位误差。

**表1　测试数据与参数设置**

| 项目 | 设置 |
|---|---|
| 图像尺寸 / 像素 | 512 × 384 |
| 模板尺寸 / 像素 | 32 × 32 |
| 目标个数 | 6（3×2 网格） |
| 补零后尺寸 / 像素 | 415 × 543 |
| 响应图有效区 / 像素 | 353 × 481 |
| 匹配阈值 $T$ | 0.60 |
| NMS 交并比阈值 | 0.30 |

### 2.2 FFT 匹配的正确性与多目标查找

- 图1 算法流程；图2 场景与真值；图3 响应图与剖面。
- 正确性：与直接逐位置乘加最大相对误差 $3.89\times10^{-16}$ ；6 个真值处响应值 0.986～1.000。
- 单次匹配耗时 31.5 ms。

### 2.3 直接阈值筛选的重复检出问题

阈值 0.6 下候选框 87 个，真值仅 6 个，平均每目标 14.5 个（图4）。

### 2.4 叠加 NMS 后的改进效果

**表2　改进前后的对比**

| 配置 | 框数 | 检出率 / % | 平均定位误差 / 像素 | 耗时 / ms |
|---|---|---|---|---|
| 仅 FFT 匹配 | 87 | 100.0 | 0.00 | 31.52 |
| FFT 匹配 + NMS（本文） | 6 | 100.0 | 0.00 | 31.79 |

NMS 自身耗时 0.28 ms，相对匹配可忽略。

### 2.5 参数影响

**表3　匹配阈值的影响**

| 匹配阈值 | 候选框数 | NMS 后框数 | 检出率 / % |
|---|---|---|---|
| 0.50 | 170 | 6 | 100.0 |
| 0.60 | 87 | 6 | 100.0 |
| 0.70 | 36 | 6 | 100.0 |
| 0.80 | 18 | 6 | 100.0 |
| 0.90 | 6 | 6 | 100.0 |
| 0.95 | 6 | 6 | 100.0 |

**表4　NMS 交并比阈值的影响**

| 交并比阈值 | 保留框数 | 检出率 / % |
|---|---|---|
| 0.05～0.70 | 6 | 100.0 |
| 0.90 | 51 | 100.0 |

### 2.6 局限性与展望

平移不变假设的边界；边界效应；密集目标时交并比判别失效。展望：多尺度金字塔与极坐标变换、分数重置型抑制、相位相关。

## 3 结论

FFT 频域相关一次给出全图所有目标位置（复杂度与模板面积无关，实测正确性达浮点精度）；NMS 以 0.28 ms 的代价把候选框由 87 个收敛为 6 个，检出率 100%、定位误差 0 像素。方法模块化、可移植；局限为仅适应平移。

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

**图1　本文算法整体流程**
**Fig.1　Overall flowchart of the proposed algorithm**

**图2　测试场景、模板与真值位置**
**Fig.2　Test scene, template and ground-truth positions**

**图3　FFT 响应图与响应剖面**
**Fig.3　FFT response map and response profile**

**图4　直接阈值筛选产生的重复候选框**
**Fig.4　Duplicate candidate boxes produced by direct thresholding**

**图5　改进前后的检测结果对比**
**Fig.5　Detection results before and after the improvement**

**图6　两个关键参数的影响**
**Fig.6　Influence of the two key parameters**
