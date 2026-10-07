# SIFT与FFT频域预处理的图像几何变换参数估计

**SIFT Feature Matching with FFT Pre-Processing for Estimating Image Geometric Transformation Parameters**

⬜⬜⬜

⬜⬜⬜（单位名称，城市 邮编）

**中图法分类号：** TP391.41　　**文献标识码：** A

**作者简介：** ⬜⬜，出生年⬜，硕士研究生，主要研究方向为数字图像处理与图像配准。
E-mail：2857241539@qq.com。
**通信作者：** ⬜⬜⬜，职称⬜⬜，E-mail：⬜⬜⬜。

**说明：** 本论文为课程设计成果，无基金项目资助。

---

## 摘要

**目的**：由两幅图像估计其间的几何变换（单应矩阵）参数是图像配准、全景拼接与视觉定位的基础环节。尺度不变特征变换（scale-invariant feature transform，SIFT）结合随机采样一致性（random sample consensus，RANSAC）是该任务的经典方案，但 SIFT 的极值检测基于高斯差分尺度空间，该算子对高频具有放大作用：噪声会在平滑度不足的区域产生虚假关键点，并破坏真实关键点描述子的可区分性，使可利用的正确匹配减少、匹配内点率下降，进而使单应矩阵估计精度变差。为提升噪声条件下的估计精度，提出在特征提取之前串联频域降噪预处理的方法。

**方法**：构建"频域降噪预处理 → SIFT 特征提取 → 特征粗匹配 → RANSAC 剔除外点 → 最小二乘求解单应矩阵"的流水线。预处理模块对输入图像作二维傅里叶变换，依据噪声主要分布于高频、而有意义的特征能量集中于中低频的先验，构造巴特沃斯低通传递函数抑制高频噪声分量，经逆变换后送入 SIFT。为避免理想低通硬截断引入振铃而制造新的虚假边缘，选用通带平坦、过渡带平滑的巴特沃斯形式，并全程采用未移位的频谱索引约定以保证直流分量全通。为定量评价改进效果，以关键点数量、匹配点对数、内点数量、内点率、单应矩阵对真值的映射误差与总耗时作为指标；由于测试图像对由程序合成、变换真值精确已知，各匹配是否真正对应可客观判定，评价不依赖人工标注。实验在 24 个随机种子上重复并报告均值。

**结果**：在自建的 512 像素×384 像素、含 90 个随机图元的灰度图像对上实验，噪声标准差取 32 灰度级，截止频率取 0.18 周期/像素。与基础算法相比，本文方法的匹配点对数由 171.6 对增至 306.6 对（增加 78.7%），内点数量由 143.0 个增至 262.8 个（增加 83.8%），内点率由 83.32% 升至 85.74%；单应矩阵对真值的平均映射误差由 0.334 像素降至 0.258 像素，**降低 22.6%**，最大映射误差由 1.089 像素降至 0.889 像素，两种配置的估计成功率均为 100%。参数分析表明：平均映射误差随截止频率呈单峰变化，从 0.03 时的 0.698 像素降至 0.18 时的最低值 0.258 像素，再回升至 0.50 时的 0.325 像素；噪声越强收益越明显，噪声标准差 48 时误差降低 35.7%，而噪声标准差 16 时仅降低 5.9%；在无噪声图像上预处理反而使误差由 0.038 像素升至 0.044 像素（相对上升 14.8%，绝对量仅 0.006 像素）。预处理本身耗时 29.2 ms，总耗时由 65.0 ms 增至 109.4 ms。

**结论**：频域低通预处理能有效恢复被噪声破坏的特征响应与描述子可区分性，显著增加可利用的正确匹配数量，从而在噪声条件下明显提升单应矩阵的估计精度；该模块与特征检测、匹配与鲁棒估计环节完全解耦，可置于任意特征检测流程之前。其局限在于：预处理以损失高频细节为代价，收益随噪声水平下降而迅速衰减，在低噪声条件下因平滑引起的定位偏差反而使精度轻微下降；方法假定噪声在整幅图像上统计均匀，对空间非均匀噪声与周期性干扰不适用。此外，预处理与 SIFT 尺度空间内置的高斯平滑存在功能重叠，故其适用范围应界定为噪声较强而图像主体结构清晰的配准任务。

**关键词**：图像配准；SIFT特征；随机采样一致性；单应矩阵；频域降噪；重投影误差

**Abstract**

**Objective**: Estimating the geometric transformation, i.e. the homography, between two images is a fundamental step in image registration, panoramic stitching and visual localization. The combination of the scale-invariant feature transform (SIFT) and random sample consensus (RANSAC) is the classical solution to this task, but the extrema detection of SIFT is based on a difference-of-Gaussians scale space, an operator that amplifies high frequencies. Noise therefore generates spurious keypoints in regions of insufficient smoothness and degrades the discriminability of the descriptors of genuine keypoints, so that fewer correct matches survive and the inlier ratio drops, which in turn degrades the accuracy of the estimated homography. To improve estimation accuracy under noise, a frequency-domain denoising pre-processing stage is introduced before feature extraction.

**Method**: A pipeline is constructed that consists of frequency-domain pre-denoising, SIFT feature extraction, coarse feature matching, RANSAC outlier rejection and least-squares homography estimation. The pre-processing stage applies a two-dimensional Fourier transform to the input images and, exploiting the prior that noise occupies high frequencies whereas informative features concentrate at middle and low frequencies, constructs a Butterworth low-pass transfer function that suppresses high-frequency noise while retaining principal contours and structural texture; the result is then transformed back and passed to SIFT. A Butterworth form is chosen rather than an ideal low-pass because the hard truncation of the latter introduces ringing that manufactures new spurious edges. Throughout, an unshifted spectral indexing convention is used so that the DC component is fully passed. To quantify the improvement, the number of keypoints, the number of putative matches, the number of inliers, the inlier ratio, the mapping error of the homography against the ground truth and the total runtime are adopted as metrics; because the test image pairs are synthesized and the transformation ground truth is exactly known, whether each match is a true correspondence can be judged objectively without manual annotation. Experiments are repeated over 24 random seeds and the means are reported.

**Result**: Experiments were conducted on a self-built 512 x 384 grey-scale image pair containing 90 random primitives, with a noise standard deviation of 32 grey levels and a cutoff frequency of 0.18 cycles/pixel. Compared with the baseline, the proposed method increases the number of putative matches from 171.6 to 306.6 (an increase of 78.7%) and the number of inliers from 143.0 to 262.8 (an increase of 83.8%), while the inlier ratio rises from 83.32% to 85.74%. The mean mapping error of the homography against the ground truth drops from 0.334 to 0.258 pixels, a reduction of 22.6%, and the maximum mapping error drops from 1.089 to 0.889 pixels, with an estimation success rate of 100% for both configurations. Parameter analysis shows that the mean mapping error varies unimodally with the cutoff frequency, falling from 0.698 pixels at 0.03 to a minimum of 0.258 pixels at 0.18 and rising again to 0.325 pixels at 0.50; the benefit grows with noise, reaching a 35.7% error reduction at a noise standard deviation of 48 but only 5.9% at 16. On a noise-free image the pre-processing is instead harmful, raising the error from 0.038 to 0.044 pixels, a relative increase of 14.8% but an absolute change of only 0.006 pixels. The pre-processing itself costs 29.2 ms and the total runtime increases from 65.0 to 109.4 ms.

**Conclusion**: Frequency-domain low-pass pre-processing effectively restores the feature responses and descriptor discriminability destroyed by noise and substantially increases the number of usable correct matches, thereby markedly improving homography estimation accuracy under noise. Being decoupled from feature detection, matching and robust estimation, the module can be placed in front of any feature detection pipeline. Its limitations are that it trades away high-frequency detail, that its benefit decays rapidly as noise decreases so that under low noise the localization bias caused by smoothing slightly degrades accuracy, and that it assumes statistically uniform noise over the whole image and is therefore unsuitable for spatially varying or periodic interference. Moreover, the pre-processing overlaps functionally with the Gaussian smoothing already present in the SIFT scale space, so its scope should be defined as registration tasks with strong noise and clearly structured image content.

**Key words**: image registration; SIFT feature; random sample consensus; homography; frequency-domain denoising; reprojection error

---

## 0 引言

由两幅图像估计其间的几何变换参数，是图像配准、全景拼接、增强现实与视觉定位的共同前置环节（Szeliski, 2022）。其核心是根据图像间的对应关系求解单应矩阵 $H$ ，进而完成坐标映射。为此，Lowe 提出尺度不变特征变换（SIFT），通过在尺度空间检测极值点并构造梯度方向直方图描述子，使特征点对尺度缩放、旋转与一定程度的视角变化保持不变，成为该领域影响最深远的方法（Lowe, 2004）。后续研究在此基础上发展出 SURF、ORB 等加速方案（Bay 等, 2008；Rublee 等, 2011），近年则出现了以深度学习为基础的特征检测与匹配方法（DeTone 等, 2018；Sarlin 等, 2020；Sun 等, 2021）。

然而特征匹配不可避免地存在错误对应，若使用最小二乘直接求解，少量外点即可显著拉偏解。为此，Fischler 和 Bolles 提出随机采样一致性（RANSAC），通过对最小样本集反复随机采样、以模型一致性计数筛选内点，从而在存在大量外点时仍能稳健估计模型参数（Fischler 和 Bolles, 1981）；此后又出现了多种改进的鲁棒估计框架（Raguram 等, 2013；Barath 和 Matas, 2018；Barath 等, 2020）。SIFT 与 RANSAC 的组合已成为几何变换估计的标准框架，并被广泛用于图像配准与三维重建（Zhang 和 Xie, 2021）。

该框架的薄弱环节在于特征检测阶段对噪声的敏感性。SIFT 的极值检测基于高斯差分（difference of Gaussians，DoG）尺度空间，而 DoG 本质上是一个带通算子：噪声在图像中表现为高频随机起伏，经过 DoG 后在原本平滑的区域也可能产生超过阈值的响应，形成虚假关键点。同时，噪声还会污染真实关键点的邻域梯度直方图，使其描述子的可区分性下降。这两方面的危害是双重的：一方面虚假点之间会产生大量误匹配、真实点又难以稳定匹配，使匹配内点率下降；另一方面，RANSAC 的迭代中抽到含虚假点样本的概率随之上升，需要更多迭代才能收敛，甚至收敛到错误的单应矩阵（Zhang 和 Xie, 2021；Ma 等, 2021）。

针对该问题，已有研究从描述子改进、匹配策略优化与鲁棒估计增强等方面提出改进（Mikolajczyk 和 Schmid, 2005；Jiang 等, 2022；Bellavia 和 Mishkin, 2022）。本文从**预处理**角度切入：既然噪声的能量主要集中在频域高频段，而具有结构意义的特征（角点、边缘、斑点）对应中低频成分，那么在特征提取之前对高频作适度衰减，即可在源头减少虚假响应、恢复真实结构的特征响应。该方法不改动 SIFT 与 RANSAC 的任何内部逻辑，仅增加一个前处理模块，结构简单、可解释性强。

本文的贡献在于三点。第一，构建了"频域降噪预处理 + SIFT + RANSAC"的完整流水线，并通过 24 个随机种子的重复实验，定量说明预处理在匹配数量、内点率与单应矩阵映射误差上的作用。第二，实验采用自建图像对（对同一场景施加已知单应变换与可控噪声），因此具备精确的真值对应关系，使映射误差具备客观基准，随机种子固定、结果可复现。第三，明确方法的边界：预处理必然损失高频细节，其收益随噪声水平下降而衰减，在低噪声条件下甚至转为轻微损失，本文以实测数据给出这一权衡的定量刻画。

## 1 相关原理

### 1.1 SIFT 特征提取

SIFT 的流程分为四步：尺度空间极值检测、关键点精确定位、方向分配与描述子生成（Lowe, 2004）。

**（1）尺度空间与 DoG。** 高斯尺度空间定义为原始图像与不同尺度高斯核的卷积，如式（1）：

$$
L(x,y,\sigma)=G(x,y,\sigma) * I(x,y) \tag{1}
$$

高斯差分由相邻尺度相减得到，如式（2）：

$$
D(x,y,\sigma)=\big[G(x,y,k\sigma)-G(x,y,\sigma)\big] * I(x,y)=L(x,y,k\sigma)-L(x,y,\sigma) \tag{2}
$$

在 $D$ 的尺度空间中对每个采样点与同层及相邻层的邻域共 26 个点比较，检测极值点作为候选关键点。DoG 这一带通运算对高频噪声具有放大作用，是 SIFT 对噪声敏感的根源。

**（2）关键点定位与描述子。** 通过拟合三维二次函数剔除低对比度点与边缘响应点；随后依据关键点邻域梯度方向的主方向实现旋转不变性；最后在 $16 \times 16$ 邻域内统计 8 个方向的梯度直方图，形成 128 维描述子。由于该直方图由邻域梯度累加而成，噪声会同时扰动真实关键点的梯度方向分布，使其描述子与正确对应点之间的距离增大，从而在后续比值判据中被淘汰。

### 1.2 特征匹配

对两幅图像的关键点描述子作最近邻搜索，常用欧氏距离或其比值作为判据。为提高可靠性，Lowe 建议使用最近邻与次近邻距离之比作为筛选条件：若最近邻距离远小于次近邻距离，说明该匹配的区分度较高（Lowe, 2004）。该判据本质上要求正确对应在描述子空间中显著优于错误的候选，因此当噪声削弱了描述子的可区分性时，通过判据的正确匹配数量会明显减少。

### 1.3 RANSAC 与单应矩阵估计

设两幅图像的对应点对为 $\{(p_i, q_i)\}$ ，单应矩阵 $H$ 满足式（3），其中点采用齐次坐标表示：

$$
\begin{bmatrix} q_x \\ q_y \\ 1 \end{bmatrix}
\sim H \begin{bmatrix} p_x \\ p_y \\ 1 \end{bmatrix}, \qquad
H = \begin{bmatrix} h_{11} & h_{12} & h_{13} \\ h_{21} & h_{22} & h_{23} \\ h_{31} & h_{32} & 1 \end{bmatrix} \tag{3}
$$

$H$ 含 8 个自由度，故每次需采 4 对对应点求解。RANSAC 的流程为：随机抽取 4 对点求解 $H$ ；计算所有点对在该 $H$ 下的重投影误差，误差小于阈值的记为内点；统计内点数量；重复以上过程若干次，取内点数量最多的模型，并用其全部内点作最小二乘重估计以提升精度（Fischler 和 Bolles, 1981）。

评价指标为重投影误差，其定义如式（4）：

$$
E = \frac{1}{N}\sum_{i=1}^{N}\big\| q_i - \pi(H p_i) \big\|_2 \tag{4}
$$

式中，$\pi(\cdot)$ 表示由齐次坐标归一化为二维坐标，$N$ 为内点数量。重投影误差越小，说明 $H$ 估计越准确。本文进一步利用合成数据的真值优势，在图像上均匀取一组网格点，比较估计矩阵 $H$ 与真值矩阵 $H_{gt}$ 把它们映射到的位置，以该平均距离作为**映射误差**，它不依赖于哪些匹配被选为内点，因而能更公平地反映参数估计本身的精度。

### 1.4 基础算法的缺陷

RANSAC 的成功依赖一个前提：随机样本中包含足够多的真实对应。设内点率为 $w$ ，每次采样取 $m=4$ 对点，则一次采样全为内点的概率为 $w^{m}$ ；若要保证以概率 $p$ 至少取得一组正确样本，所需迭代次数如式（5）：

$$
k = \frac{\log(1-p)}{\log(1-w^{m})} \tag{5}
$$

由式（5）可见，$k$ 对 $w$ 极其敏感：当 $w$ 由 0.5 降至 0.2 时，在 $p=0.99$ 下所需迭代次数由约 72 次激增至约 2 850 次。噪声引起的虚假关键点与误匹配正是通过降低 $w$ 来恶化 RANSAC 的收敛性，这为"减少虚假特征、恢复真实匹配"的改进方向提供了理论依据。

此外，虚假关键点还会带来定位偏差：由于它们不对应真实结构，其坐标存在较大随机误差，会污染最小二乘重估计环节，直接抬高重投影误差。

### 1.5 频域降噪预处理

由 1.1 节可知，SIFT 的噪声敏感性源于 DoG 对高频的放大。若能在特征提取之前对高频进行适度衰减，即可从源头减少虚假响应、并恢复被噪声淹没的真实结构响应。

设输入图像为 $f(x,y)$ ，其频谱为 $F(u,v)$ 。构造中心化距离 $D(u,v)$ 下的低通传递函数，如式（6）：

$$
H(u,v)=\frac{1}{1+\big[D(u,v)/D_0\big]^{2n}} \tag{6}
$$

式中，$D_0$ 为截止频率，$n$ 为阶数。式（6）为巴特沃斯低通，其特点是通带平坦、过渡带平滑，避免理想低通硬截断引入的振铃——后者会在图像中制造新的虚假边缘，反而增加虚假关键点。滤波后的图像由式（7）给出：

$$
f'(x,y)=\mathcal{F}^{-1}\big\{F(u,v)\,H(u,v)\big\} \tag{7}
$$

**权衡关系。** 截止频率 $D_0$ 是唯一可调参数，其取值决定方法的效果：

- $D_0$ 过大 → 噪声衰减不足，虚假关键点依然存在，改进收益有限；
- $D_0$ 过小 → 图像细节被平滑，真实结构（如小尺寸纹理、锐利角点）被削弱，导致可用关键点总数下降，可能出现"误匹配减少但内点数量同时减少"的现象，甚至使估计精度因约束不足而下降。

这一权衡是方法的固有限制，将在 3.4 节通过参数扫描定量刻画。

## 2 本文算法

### 2.1 整体流程

本文方法的完整流水线如图1所示：

1）**构造图像对。** 取一幅清晰图像，对其施加已知的单应变换生成第二幅图像，再对两幅图像施加强度可控的加性噪声，从而获得具有精确真值对应关系的测试图像对；

2）**频域降噪预处理。** 对两幅输入图像分别作二维傅里叶变换，按式（6）构造低通传递函数抑制高频噪声，经逆变换得到预处理图像；

3）**SIFT 特征提取。** 在预处理图像上检测关键点并生成 128 维描述子；

4）**特征粗匹配。** 以描述子距离作最近邻搜索，并以最近邻与次近邻距离之比作筛选；

5）**RANSAC 剔除外点并求解单应矩阵。** 迭代采样、统计内点，取内点最多的模型并用全部内点作最小二乘重估计，输出 $H$ 与映射误差。

**图1　本文算法整体流程**
**Fig.1　Overall flowchart of the proposed algorithm**

![图1](data/fig_0_pipeline.png)

### 2.2 关键实现要点

**（1）真值对应的建立。** 自建图像对的关键优势在于：单应矩阵的真值已知，因此可直接比较估计值与真值，并据此计算内点的判别基准。这使评价不依赖人工标注，完全客观。本文把与真值一致的匹配（在真值变换下重投影偏差小于 2 像素）单独统计，作为"可利用的正确匹配数"。

**（2）两幅图像使用相同参数。** 预处理必须对图像 A 与图像 B 采用**完全一致**的截止频率与滤波器形式。若两幅图像的预处理强度不一致，其梯度分布与特征响应将产生系统性差异，人为引入误匹配。3.4 节的对照实验验证了这一约束：把图 B 的截止频率改为 0.35 而图 A 保持 0.18 后，匹配点对由 306.6 降至 228.4，映射误差由 0.258 像素升至 0.311 像素。

**（3）频谱索引约定。** 滤波器原点必须与频谱索引约定一致。本文全程使用未移位的 `fft2` / `ifft2` ，此时直流分量位于索引 `[0,0]` ，距离必须用未移位的频率坐标按环绕方式构造，从而保证 $H(0,0)=1$ 、图像亮度不被整体压低；若改用 `fftshift` 把频谱中心移到画面中央，则距离构造也必须同步中心化，二者混用会使滤波器中心错位。

**（4）与 SIFT 内置平滑的关系。** SIFT 自身在构建尺度空间时已包含高斯平滑。因此预处理的作用是"降低输入噪声基底"，而非替代尺度空间平滑。当噪声水平较低时，SIFT 内置的平滑已足以抑制噪声，预处理的增量收益将趋于零甚至转为损失；这一预期已在 3.4 节通过多噪声水平的实验验证。

**（5）滤波器形式选择。** 应避免使用理想低通。其空域等效核为 sinc 型，会在边缘附近产生振铃，人为制造虚假边缘与虚假关键点，与改进目标背道而驰。

**（6）固定随机性。** 噪声生成与 RANSAC 采样均含随机过程，须固定随机种子，并在多个独立种子上重复以降低单次结果的偶然性。

### 2.3 复杂度分析

设图像尺寸为 $H \times W$ 。预处理包含一次正变换与一次逆变换，复杂度为 $O(HW\log(HW))$ ，相对 SIFT 自身在多个尺度上的卷积开销可忽略。SIFT 的特征检测复杂度约为 $O(HW)$ （每个尺度层面），而 RANSAC 的复杂度为 $O(k \cdot N)$ ，其中 $k$ 为迭代次数、$N$ 为匹配点对数。

值得注意的是，频域预处理的收益具有"双重性"：一方面它直接消耗少量计算（实测 29.2 ms），另一方面它通过增加正确匹配、提高内点率而降低了 RANSAC 所需的迭代次数 $k$ ，从而在整体上部分抵消自身开销。不过在本实验的固定迭代设置下，总耗时仍由 65.0 ms 增至 109.4 ms，即预处理的开销并未被完全抵消。

## 3 实验分析

### 3.1 实验设置

实验采用自建图像对：源图为 512 像素×384 像素的灰度合成图，由低频起伏背景叠加 90 个随机矩形、椭圆与线段构成，以提供丰富的角点与斑点结构。对源图施加已知单应矩阵 $H_{gt}$ 生成第二幅图像，再对两幅图像分别叠加标准差可控的独立高斯噪声。真值矩阵为

$$
H_{gt} = \begin{bmatrix} 1.08 & 0.06 & 34.0 \\ -0.05 & 1.05 & 20.0 \\ 1.2\times10^{-4} & 8\times10^{-5} & 1.0 \end{bmatrix} \tag{8}
$$

即包含约 8% 的尺度变化、约 3° 的旋转、约 32 像素的平移以及轻微的透视畸变。随机种子固定为 602 起始的连续 24 个，全部结果均在该 24 个种子上取均值，因而可完全复现。

采用自建数据的原因在于：真实图像对不存在单应矩阵真值，重投影误差与内点判别只能依赖人工标注或间接推断；自建数据使真值精确已知，评价完全客观，且噪声强度可控，便于考察方法在不同噪声水平下的表现。合成数据在计算机视觉方法评价中的适用性已有系统讨论（Paulin 和 Ivasic-Kos, 2023）。

对照设置两组：① 基础算法（带噪图像直接作 SIFT + RANSAC，无频域预处理）；② 本文方法（频域降噪预处理 + SIFT + RANSAC）。为使两组比较不受 RANSAC 随机性的额外干扰，两组均采用固定的 500 次迭代；SIFT 采用 OpenCV 默认参数且不限制特征点数量，比值判据阈值取 0.75。评价指标包括关键点数量、匹配点对数、与真值一致的匹配数、内点数量、内点率、单应矩阵映射误差（均值与最大值）与总耗时，并输出匹配连线可视化图。

**表1　实验数据与参数设置**
**Table 1　Experimental data and parameter settings**

| 项目 | 设置 |
|---|---|
| 源图像尺寸 / 像素 | 512 × 384（灰度，90 个随机图元） |
| 单应变换类型与幅度 | 尺度约 1.08、旋转约 3°、平移 (34, 20)、轻微透视 |
| 噪声类型与标准差 | 加性高斯白噪声，主对照 32 灰度级 |
| 低通截止频率 $D_0$ 与阶数 $n$ | 0.18 周期/像素，$n=2$ |
| 最近邻距离比阈值 | 0.75 |
| RANSAC 重投影阈值与迭代上限 | 3.0 像素，500 次（固定） |
| 真对应判定容差 | 2.0 像素 |
| 随机种子 | 602–625，共 24 个 |

### 3.2 定性结果

图2给出源图、带噪图与经单应变换后的第二幅图像。图3对比了带噪图像与频域预处理后的图像及其对数频谱：预处理后图像的高频随机起伏被明显抑制，频谱外围的能量显著下降。

频域滤波实现的自检结果为：传递函数在直流处的取值 $H(0,0)=1.000000$ ，未移位实现与"中心化距离"实现在数值上完全一致（最大差 0.00）；截止频率处的响应为 0.5000，与理论值一致；传递函数随频率距离单调不增。降噪后图像的高频能量（拉普拉斯响应均方）由 21 551.1 降至 148.7，与无噪真值图像的均方根误差由 31.64 降至 13.44，表明滤波方向正确且直流分量未被压制。此外，单应变换真值经交叉验证：程序内齐次坐标公式与 OpenCV 透视变换的最大偏差为 $1.14\times10^{-13}$ ，可视为数值精度一致。

匹配环节的自检显示，通过比值判据的 163 对匹配中，与真值一致的有 117 对、不一致 46 对；正确匹配的平均距离比为 0.469，明显小于错误匹配的 0.637，说明比值判据确实起到了区分作用。RANSAC 的自检在 200 对真对应外加 80 对随机外点（外点率 28.6%）的条件下进行，恢复出的矩阵对真对应的平均映射误差为 0.0000 像素，真对应被判为内点的比例为 100%。

图4给出两种方案的匹配连线对比，取自第 602 号种子的代表性图像对（该对图像上基础算法匹配 163 对，本文方法匹配 281 对；表2报告的则是 24 个种子的均值）。可以看出，基础算法的匹配连线数量明显偏少，其中还夹杂若干交叉的错误连线；本文方法的有效连线显著增多，连线整体更为一致。

**图2　测试场景与带噪图像对**
**Fig.2　Test scene and the noisy image pair**

![图2](data/fig_1_scene.png)

**图3　带噪图像与频域预处理图像的对比**
**Fig.3　Comparison between the noisy image and the frequency-domain pre-processed image**

![图3](data/fig_2_denoise.png)

**图4　两种方案的匹配连线可视化对比**
**Fig.4　Visualization comparison of match lines between the two configurations**

![图4](data/fig_3_matches.png)

### 3.3 定量结果

两组对照在噪声标准差 32、截止频率 0.18 条件下的定量指标如表2。

**表2　两组对照实验的定量指标**
**Table 2　Quantitative metrics of the two comparative configurations**

| 指标 | 基础算法（无预处理） | 本文方法（频域预处理） |
|---|---|---|
| 关键点数量（图A / 图B） | 1299 / 1317 | 2163 / 2089 |
| 匹配点对数 | 171.6 | 306.6 |
| 与真值一致的匹配数 | 126.0 | 234.3 |
| 内点数量 | 143.0 | 262.8 |
| 内点率 / % | 83.32 | 85.74 |
| 映射误差均值 / 像素 | 0.334 | 0.258 |
| 映射误差最大值 / 像素 | 1.089 | 0.889 |
| 预处理耗时 / ms | 0.0 | 29.2 |
| 总耗时 / ms | 65.0 | 109.4 |
| 单应矩阵估计成功率 | 100% | 100% |

由表2可见三点。第一，**预处理后匹配数量与内点数量大幅上升而内点率同步提高**，二者并不矛盾：在噪声标准差 32 的条件下，噪声既制造虚假响应，也破坏了真实关键点的描述子，使基础算法的正确匹配大量流失；预处理抑制了高频噪声，使真实结构的特征响应与描述子得以恢复，因而可获得约 1.79 倍的匹配点对、约 1.84 倍的内点数量，同时内点率由 83.32% 升至 85.74%。这与 1.5 节的权衡分析相呼应——在本组参数下关键点并未因平滑而不足，权衡的负面一侧尚未显现。

第二，**映射误差的下降是方法有效性的核心证据**。平均映射误差由 0.334 像素降至 0.258 像素，降低 22.6%；最大映射误差由 1.089 像素降至 0.889 像素。误差下降的主要来源是参与最小二乘重估计的内点数量增加，使解更稳定。两种配置的估计成功率均为 100%，说明在本实验条件下基础算法并未完全失败，预处理的作用体现为精度而非成功率的改善。

第三，**总耗时上升**。预处理本身耗时 29.2 ms，总耗时由 65.0 ms 增至 109.4 ms。其原因是预处理后关键点数量由约 1300 增至约 2100，SIFT 的检测与描述子匹配开销随之增加。因此本文方法以计算代价换取精度，适用于对精度要求高于实时性的配准任务。

### 3.4 参数分析

**（1）低通截止频率 $D_0$ 。** 表3给出 $D_0$ 由 0.03 增至 0.50 的结果。当 $D_0=0.03$ 时通带过窄，可用关键点仅 59.3 个、匹配点对 41.0 对，约束不足使映射误差升至 0.698 像素（最大误差达 2.477 像素）；$D_0$ 增大到 0.18 时关键点达 2163.3 个、匹配点对 306.6 对，映射误差降至最低的 0.258 像素；继续增大到 0.25～0.50 则噪声抑制不足，关键点数量虽继续增长（最高达 4628.2 个）但多为噪声驱动，映射误差回升至 0.280～0.325 像素。可见映射误差随截止频率呈**单峰形**变化，本实验条件下最优值为 0.18 周期/像素，本文取该值。值得注意的是，内点率随 $D_0$ 减小而升高（0.03 时达 91.26%），但此时匹配数量过少，说明**内点率高并不等价于估计精度高**，评价必须同时考察匹配数量。

**表3　截止频率 $D_0$ 的影响**
**Table 3　Influence of the cutoff frequency**

| $D_0$ / (周期/像素) | 关键点数 | 匹配点对数 | 内点率 / % | 映射误差 / 像素 | 最大映射误差 / 像素 | 总耗时 / ms |
|---|---|---|---|---|---|---|
| 0.03 | 59.3 | 41.0 | 91.26 | 0.698 | 2.477 | 98.6 |
| 0.05 | 155.3 | 101.5 | 90.34 | 0.398 | 1.302 | 100.3 |
| 0.08 | 382.3 | 208.4 | 85.77 | 0.341 | 1.178 | 103.3 |
| 0.12 | 835.4 | 294.2 | 87.13 | 0.293 | 0.978 | 107.8 |
| **0.18** | **2163.3** | **306.6** | **85.74** | **0.258** | **0.889** | **118.5** |
| 0.25 | 4628.2 | 260.1 | 83.86 | 0.280 | 0.937 | 153.1 |
| 0.35 | 2937.7 | 206.1 | 82.63 | 0.307 | 0.943 | 131.6 |
| 0.50 | 1745.0 | 180.1 | 83.00 | 0.325 | 1.037 | 118.4 |

**（2）噪声水平的影响。** 表4给出噪声标准差由 0 增至 48 的结果。**本文方法的收益随噪声增强而增大**：噪声标准差为 48 时映射误差由 0.630 像素降至 0.405 像素，降低 35.7%；为 32 时降低 22.6%；为 16 时降低 5.9%；为 8 时降低 15.2%。而在**无噪声**图像上，预处理反而使误差由 0.038 像素升至 0.044 像素，相对上升 14.8%（绝对量仅 0.006 像素）。这一结果直接验证了 2.2 节关于"预处理与 SIFT 内置平滑关系"的预期：无噪声时 SIFT 内置平滑已足够，预处理的平滑反而引入轻微的定位偏差；噪声越强，预处理降低噪声基底的增量价值越明显。这也界定了方法的适用范围——**应仅在高噪声条件下启用**。

**表4　噪声水平对两种方案的影响**
**Table 4　Influence of the noise level on the two configurations**

| 噪声标准差 | 基础算法匹配数 | 本文方法匹配数 | 基础算法内点率 / % | 本文方法内点率 / % | 基础算法映射误差 / 像素 | 本文方法映射误差 / 像素 | 误差降低 / % |
|---|---|---|---|---|---|---|---|
| 0 | 463.0 | 505.0 | 95.46 | 98.22 | 0.038 | 0.044 | −14.8 |
| 8 | 411.5 | 494.7 | 90.08 | 93.98 | 0.123 | 0.105 | 15.2 |
| 16 | 316.3 | 468.0 | 86.63 | 90.83 | 0.170 | 0.160 | 5.9 |
| 32 | 171.6 | 306.6 | 83.32 | 85.74 | 0.334 | 0.258 | 22.6 |
| 48 | 97.3 | 169.3 | 81.11 | 82.04 | 0.630 | 0.405 | 35.7 |

**（3）RANSAC 重投影阈值。** 表5给出该阈值的影响。阈值决定内点判别标准：取 1.0 像素时过于严格，内点率仅 47.30%，正确匹配被大量排除，映射误差升至 0.510 像素；取 3.0 像素时内点率 85.74%、误差最低为 0.258 像素；取 5.0 与 8.0 像素时内点率虽升至 90.82% 与 92.52%，但部分误匹配被纳入内点，误差回升至 0.290 与 0.318 像素。故该阈值不宜过小或过大，本文取 3.0 像素。

**表5　RANSAC 重投影阈值的影响**
**Table 5　Influence of the RANSAC reprojection threshold**

| 重投影阈值 / 像素 | 内点率 / % | 映射误差 / 像素 |
|---|---|---|
| 1.0 | 47.30 | 0.510 |
| 2.0 | 76.56 | 0.306 |
| 3.0 | 85.74 | 0.258 |
| 5.0 | 90.82 | 0.290 |
| 8.0 | 92.52 | 0.318 |

图5给出截止频率、可用特征数与噪声水平三项参数对估计精度的影响曲线。

**图5　截止频率与噪声水平对估计精度的影响**
**Fig.5　Influence of the cutoff frequency and the noise level on estimation accuracy**

![图5](data/fig_4_params.png)

### 3.5 局限性与展望

本文方法存在三点局限。第一，频域预处理以损失高频细节为代价，当被配准图像含有丰富高频纹理（如草地、砂石、细密文字）时，预处理会削弱这些区域的特征响应；本实验中 $D_0$ 过小（0.03～0.05）时关键点数量急剧下降、映射误差显著上升，正是这一代价的直接体现。第二，SIFT 的尺度空间本身已包含高斯平滑，因而预处理与内置平滑存在功能重叠，其增量收益随噪声水平下降而迅速衰减——实测在无噪声条件下精度反而下降 14.8%，说明方法在低噪声场景得不偿失，必须结合噪声水平估计来决定是否启用。第三，方法假定噪声在整幅图像上统计均匀，且采用全局统一的截止频率，若噪声具有空间变化的特性或为周期性干扰（如条带噪声），统一滤波将顾此失彼，甚至可能在周期噪声所在频点之外误伤结构信息。

后续可从三个方向改进：一是依据局部噪声估计或频谱分析自适应确定截止频率，使滤波强度随图像区域与噪声水平变化，从而在低噪声区域关闭滤波、避免无谓的精度损失；二是将预处理与特征检测纳入统一框架，例如在尺度空间中显式引入噪声模型的加权，而非在输入端作简单低通；三是采用鲁棒范数或加权最小二乘替代 RANSAC 的最小二乘重估计，进一步降低残余外点对 $H$ 估计的影响。

## 4 结论

针对 SIFT 与 RANSAC 在噪声条件下特征响应被破坏、可利用正确匹配减少，进而使单应矩阵估计精度下降的问题，本文提出在特征提取之前串联频域降噪预处理的改进方法。方法依据噪声能量集中于高频、结构特征能量集中于中低频的先验，构造平滑过渡的巴特沃斯低通传递函数抑制高频噪声，在保留主体结构的同时降低虚假响应。

在 512 像素×384 像素的自建图像对上（噪声标准差 32、截止频率 0.18 周期/像素、24 个随机种子取均值），本文方法把匹配点对数由 171.6 对提升至 306.6 对，内点数量由 143.0 个提升至 262.8 个，内点率由 83.32% 提升至 85.74%；单应矩阵对真值的平均映射误差由 0.334 像素降至 0.258 像素，降低 22.6%，最大映射误差由 1.089 像素降至 0.889 像素。参数分析给出三条规律：其一，映射误差随截止频率呈单峰变化，最优值为 0.18 周期/像素，过小则关键点不足、过大则噪声抑制不足；其二，收益随噪声增强而增大，噪声标准差 48 时误差降低 35.7%，无噪声时反而上升 14.8%，说明方法应界定为高噪声条件下的增强手段；其三，两幅图像必须采用同一组滤波参数，参数不一致会使匹配点对由 306.6 降至 228.4、映射误差由 0.258 像素升至 0.311 像素。

本文方法的普适性与适用范围可概括为：方法以图像为输入、以预处理图像为输出，其降噪模块与特征提取、匹配与鲁棒估计环节完全解耦，因而可置于 SIFT、SURF、ORB 等任意特征检测流程之前，具备良好的模块化移植性；由于仅依赖频谱先验而不依赖训练数据，方法适用于噪声水平较高、图像结构较为清晰、对被配准区域高频纹理要求不苛刻的场景，如监控图像的配准与常规图像拼接；在低噪声条件、强高频纹理或空间非均匀噪声的场景下，需与自适应滤波或噪声建模方法配合使用。

## 参考文献

Barath D, Matas J. 2018. Graph-Cut RANSAC//2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition. Salt Lake City, USA: IEEE: 6733-6741. DOI: 10.1109/CVPR.2018.00704.

Barath D, Noskova J, Ivashechkin M, Matas J. 2020. MAGSAC++, a fast, reliable and accurate robust estimator//2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition. Seattle, USA: IEEE: 1301-1309. DOI: 10.1109/CVPR42600.2020.00138.

Bay H, Ess A, Tuytelaars T, Van Gool L. 2008. Speeded-Up Robust Features (SURF)[J]. Computer Vision and Image Understanding, 110(3): 346-359. DOI: 10.1016/j.cviu.2007.09.014.

Bellavia F, Mishkin D. 2022. HarrisZ+: Harris corner selection for next-gen image matching pipelines[J]. Pattern Recognition Letters, 158: 141-147. DOI: 10.1016/j.patrec.2022.04.022.

Brown M, Lowe D G. 2007. Automatic panoramic image stitching using invariant features[J]. International Journal of Computer Vision, 74(1): 59-73. DOI: 10.1007/s11263-006-0002-3.

DeTone D, Malisiewicz T, Rabinovich A. 2018. SuperPoint: self-supervised interest point detection and description//2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops. Salt Lake City, USA: IEEE. DOI: 10.1109/CVPRW.2018.00060.

Fischler M A, Bolles R C. 1981. Random sample consensus: a paradigm for model fitting with applications to image analysis and automated cartography[J]. Communications of the ACM, 24(6): 381-395. DOI: 10.1145/358669.358692.

Jiang X Y, Xia Y F, Zhang X P, Ma J Y. 2022. Robust image matching via local graph structure consensus[J]. Pattern Recognition, 126: 108588. DOI: 10.1016/j.patcog.2022.108588.

Lowe D G. 2004. Distinctive image features from scale-invariant keypoints[J]. International Journal of Computer Vision, 60(2): 91-110. DOI: 10.1023/B:VISI.0000029664.99615.94.

Ma J Y, Jiang X Y, Fan A X, Jiang J J, Yan J Q. 2021. Image matching from handcrafted to deep features: a survey[J]. International Journal of Computer Vision, 129(1): 23-79. DOI: 10.1007/s11263-020-01359-2.

Mikolajczyk K, Schmid C. 2005. A performance evaluation of local descriptors[J]. IEEE Transactions on Pattern Analysis and Machine Intelligence, 27(10): 1615-1630. DOI: 10.1109/TPAMI.2005.188.

Paulin G, Ivasic-Kos M. 2023. Review and analysis of synthetic dataset generation methods and techniques for application in computer vision[J]. Artificial Intelligence Review, 56(9): 9221-9265. DOI: 10.1007/s10462-022-10358-3.

Raguram R, Chum O, Pollefeys M, Matas J, Frahm J M. 2013. USAC: a universal framework for random sample consensus[J]. IEEE Transactions on Pattern Analysis and Machine Intelligence, 35(8): 2022-2038. DOI: 10.1109/TPAMI.2012.257.

Rublee E, Rabaud V, Konolige K, Bradski G. 2011. ORB: an efficient alternative to SIFT or SURF//2011 International Conference on Computer Vision. Barcelona, Spain: IEEE: 2564-2571. DOI: 10.1109/ICCV.2011.6126544.

Sarlin P E, DeTone D, Malisiewicz T, Rabinovich A. 2020. SuperGlue: learning feature matching with graph neural networks//2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition. Seattle, USA: IEEE: 4937-4946. DOI: 10.1109/CVPR42600.2020.00499.

Sun J M, Shen Z H, Wang Y A, Bao H J, Zhou X W. 2021. LoFTR: detector-free local feature matching with transformers//2021 IEEE/CVF Conference on Computer Vision and Pattern Recognition. Nashville, USA: IEEE: 8918-8927. DOI: 10.1109/CVPR46437.2021.00881.

Szeliski R. 2022. Computer Vision: Algorithms and Applications[M]. 2nd ed. Cham: Springer. DOI: 10.1007/978-3-030-34372-9.

Wijaya M C. 2022. Template matching using improved rotations Fourier transform method[J]. International Journal of Electronics and Telecommunications, 68(4): 881-888. DOI: 10.24425/ijet.2022.143898.

Zhang Y J. 2021. Frequency domain filtering//Handbook of Image Engineering. Singapore: Springer: 539-559. DOI: 10.1007/978-981-15-5873-3_13.

Zhang Y J, Xie Y Q. 2021. Adaptive clustering feature matching algorithm based on SIFT and RANSAC//2021 2nd International Conference on Electronics, Communications and Information Technology. Sanya, China: IEEE: 174-179. DOI: 10.1109/CECIT53797.2021.00038.

Zitová B, Flusser J. 2003. Image registration methods: a survey[J]. Image and Vision Computing, 21(11): 977-1000. DOI: 10.1016/S0262-8856(03)00137-9.

## 图题（中英文对照）

**图1　本文算法整体流程**
**Fig.1　Overall flowchart of the proposed algorithm**

**图2　测试场景与带噪图像对**
**Fig.2　Test scene and the noisy image pair**

**图3　带噪图像与频域预处理图像的对比**
**Fig.3　Comparison between the noisy image and the frequency-domain pre-processed image**

**图4　两种方案的匹配连线可视化对比**
**Fig.4　Visualization comparison of match lines between the two configurations**

**图5　截止频率与噪声水平对估计精度的影响**
**Fig.5　Influence of the cutoff frequency and the noise level on estimation accuracy**

---

## 附录：本章结果文件

| 文件 | 说明 |
| --- | --- |
| `data/fig_0_pipeline.png` | 本文算法整体流程图 |
| `data/fig_1_scene.png` | 源图、带噪图与变换后图像 |
| `data/fig_2_denoise.png` | 带噪与频域预处理图像及其对数频谱 |
| `data/fig_3_matches.png` | 两种方案的匹配连线对比 |
| `data/fig_4_params.png` | 截止频率与噪声水平的影响曲线 |
| `data/img_A_noisy.png` | 带噪源图 A |
| `data/img_B_noisy.png` | 带噪变换图 B |
| `data/img_A_clean.png` | 无噪源图 A |
| `data/table2_compare.csv` | 两组对照的定量指标 |
| `data/sweep_d0.csv` | 截止频率扫描结果 |
| `data/sweep_noise.csv` | 噪声水平扫描结果 |
| `data/sweep_thresh.csv` | RANSAC 重投影阈值扫描结果 |
| `data/key_numbers.json` | 关键数字汇总 |

对应 Notebook：`DIP第六章_SIFT与FFT频域预处理的图像几何变换参数估计.ipynb`
