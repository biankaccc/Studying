# 维纳滤波复原中前置降噪的有效性条件

**On the Validity Conditions of Pre-Denoising in Wiener Filtering Restoration**

⬜⬜⬜　　⬜⬜⬜（单位名称，城市 邮编）

**中图法分类号：** TP391.41　　**文献标识码：** A

**作者简介：** ⬜⬜，出生年⬜，硕士研究生，主要研究方向为数字图像处理与图像复原。
E-mail：2857241539@qq.com。　**通信作者：** ⬜⬜⬜，职称⬜⬜，E-mail：⬜⬜⬜。

**说明：** 本论文为课程设计成果，无基金项目资助。

---

## 摘要

**目的**：图像复原旨在由退化图像 $g=f*h+n$ 恢复原始图像 $f$ ，维纳滤波是其中最具代表性的频域方法。工程与教学中流传"先在复原之前串联一步降噪"的做法，但其是否普遍有效、有效性与噪声类型的关系如何，缺乏在公平调参条件下的定量考察。本文对此进行系统研究。

**方法**：构建"退化图像 → 前置降噪 → 维纳复原"的流水线，设计**噪声类型 × 降噪算子**的双因素交叉实验：噪声因素取平稳高斯白噪声、脉冲型椒盐噪声、结构性条带噪声；算子因素取频域高斯低通与空域中值滤波，各两档参数，共 12 个实验格。为消除调参偏差，两种流程的维纳正则参数 $K$ 均在 10 档候选中各自取 PSNR 最优。指标为峰值信噪比（PSNR）与结构相似度（SSIM），并从维纳传递函数的频域增益形式分析其"自带降噪"的机理。

**结果**：实验得到清晰的双因素交互规律。**匹配时前置降噪有效**：中值滤波对椒盐噪声提升 1.35 dB（SSIM +0.1494），低通对条带噪声提升 1.40 dB（SSIM +0.1056）。**错配时无效或有害**：低通对椒盐噪声 −0.01 dB，中值对高斯噪声 −0.17～−0.27 dB。**对平稳高斯白噪声，四种算子全部无稳定增益**（−0.27～+0.10 dB）。匹配与错配的 PSNR 差值分别为 1.36 dB 与 0.96 dB。机理分析表明维纳传递函数的增益为 $|H|/(|H|^{2}+K)$ ，在低频段趋于 $1/|H|$ 以补偿模糊、在高频段趋于 0 以压制噪声，即**维纳滤波已完成一次按信噪比自适应的最优频域加权**；只有形态超出其"平稳加性噪声"假设的噪声（脉冲型、结构性）才需要额外的前置降噪。

**结论**：维纳滤波复原中的前置降噪不是无条件的改进，其增益取决于降噪算子与噪声类型的匹配性。对脉冲型噪声应选中值滤波，对结构性条带噪声应选低通滤波，对平稳高斯噪声则不应引入前置降噪。该结论为"先去噪再去模糊"给出了明确的操作边界：前置降噪补足的是维纳滤波的**建模能力**，而非其噪声放大缺陷——后者已由正则参数 $K$ 处理。局限在于结论建立在合成退化与空间不变模糊之上，最优正则参数由 PSNR 事后选取。

**关键词**：图像复原；维纳滤波；前置降噪；噪声类型；中值滤波；峰值信噪比

**Abstract**

**Objective**: Image restoration aims to recover the original image f from a degraded observation g = f*h + n, and Wiener filtering is one of the most representative frequency-domain methods. A practice widely circulated in engineering and teaching is to cascade a denoising stage before restoration, namely to denoise and then deblur. Whether this is generally effective, and how its effectiveness depends on the noise type, has not been quantitatively examined under fair parameter tuning. This work addresses that question.

**Method**: A pipeline of degraded image, pre-denoising and Wiener restoration is constructed, and a two-factor crossed experiment is designed: the noise factor takes stationary additive white Gaussian noise, impulsive salt-and-pepper noise and structural stripe noise, while the operator factor takes frequency-domain Gaussian low-pass filtering and spatial median filtering, each with two settings, giving twelve cells. To eliminate tuning bias the Wiener regularization parameter K of both pipelines is independently optimized over ten candidates by PSNR. Peak signal-to-noise ratio and structural similarity are used as metrics, and the intrinsic denoising behaviour of the Wiener filter is analysed from the frequency-domain form of its gain.

**Result**: The experiment reveals a clear two-factor interaction. Pre-denoising is effective under matching: median filtering raises the PSNR of salt-and-pepper noise by 1.35 dB with a structural similarity gain of 0.1494, and low-pass filtering raises that of stripe noise by 1.40 dB with a gain of 0.1056. Under mismatch it is ineffective or harmful: low-pass filtering on salt-and-pepper noise gives -0.01 dB and median filtering on Gaussian noise gives -0.17 to -0.27 dB. For stationary white Gaussian noise all four operators show no stable gain, ranging from -0.27 to +0.10 dB. The PSNR difference between matching and mismatching operators is 1.36 dB and 0.96 dB. The mechanism analysis shows that the Wiener gain equals |H|/(|H|^2 + K), tending to 1/|H| at low frequencies to compensate the blur and to zero at high frequencies to suppress noise; the Wiener filter thus already performs an optimal signal-to-noise-ratio-adaptive frequency-domain weighting. Only noise whose morphology falls outside its stationary additive noise assumption, namely impulsive and structural noise, requires additional pre-denoising.

**Conclusion**: Pre-denoising in Wiener filtering restoration is not an unconditional improvement; its benefit depends on the match between the denoising operator and the noise type. Median filtering should be chosen for impulsive noise, low-pass filtering for structural stripe noise, and no pre-denoising for stationary Gaussian noise. This gives an explicit operational boundary to the empirical practice of denoising before deblurring: pre-denoising compensates for the limited modelling capability of the Wiener filter rather than for its noise amplification, the latter already being handled by the regularization parameter K. The conclusions are limited to synthetic degradations with spatially invariant blur, and the optimal regularization parameter was selected post hoc by PSNR.

**Key words**: image restoration; Wiener filtering; pre-denoising; noise type; median filtering; peak signal-to-noise ratio

---

## 0 引言

- 背景：退化模型 $g=f*h+n$ ；图像复原的频域方法以维纳滤波为代表。
- 维纳滤波的已知弱点：高频段噪声放大、强边缘振铃；反卷积放大噪声是逆问题的固有性质。
- 流传的做法：复原前先降噪（"先去噪再去模糊"）；在若干文献中被采用。
- 相反的证据：去噪-去模糊领域近期普遍转向**联合处理**，理由是顺序流水线逐级放大误差、早期丢失的信息不可恢复。
- 待澄清的理论问题：维纳滤波的增益在噪声主导频段已趋近零，**它自己就完成了一次自适应低通**；那么前置降噪在什么情况下才有价值？
- 本文做法：构建流水线，设计**噪声类型 × 降噪算子**交叉实验，在两种流程各自最优调参下比较。
- 贡献：给出前置降噪有效性的**匹配性判据**；从增益形式解释机理（补足建模能力而非噪声放大缺陷）。

## 1 方法原理

### 1.1 退化模型与频域复原

$g=f*h+n$ 的频域形式（式1）；直接逆滤波在 $H\to 0$ 频段剧烈放大噪声。

### 1.2 维纳滤波及其"自带降噪"特性

- 传递函数（式2）；幅度增益（式3）。
- 两个极限：$|H|^{2}\gg K$ 增益 $\approx 1/|H|$ 补偿模糊；$|H|^{2}\ll K$ 增益 $\to 0$ 压制噪声。
- **结论：维纳滤波本身即一次按信噪比自适应的最优频域加权。**

### 1.3 前置降噪及其匹配性假设

- 高斯低通（式4）：对**特定频段的能量**有效。
- 中值滤波：对**空间稀疏的极端值**有效。

| 噪声 | 形态 | 匹配算子 | 理由 |
| --- | --- | --- | --- |
| 高斯白噪声 | 频带内均匀 | 无 | 符合维纳假设，维纳已最优 |
| 椒盐噪声 | 空间稀疏极端脉冲 | 中值 | 低通会把脉冲抹开 |
| 条带噪声 | 特定频率周期结构 | 低通 | 中值无法去除整列偏置 |

## 2 实验与分析

### 2.1 实验设置

**表1　实验设置**

| 项目 | 设置 |
|---|---|
| 图像 | 512×512（skimage camera） |
| 模糊核 | 高斯，σ=3.0，25×25 |
| 高斯白噪声 | σ = 0.05 |
| 椒盐噪声 | p = 0.05 |
| 条带噪声 | 幅值 0.06，周期 17 |
| 降噪算子 | 低通 D0=30/60；中值 k=5/7 |
| 维纳正则参数 | 10 档按 PSNR 取优 |

实现校验：脉冲响应检验频域卷积算子，与空域卷积最大绝对差 $3.47\times10^{-18}$。

### 2.2 基线：直接维纳复原

**表2　三种噪声下直接维纳复原的最优结果**

| 噪声 | 退化图 PSNR | 最优 K | 复原 PSNR | SSIM |
|---|---|---|---|---|
| 高斯白噪声 | 22.02 | 1.0 | 24.18 | 0.6244 |
| 椒盐噪声 | 16.97 | 3.0 | 23.15 | 0.5380 |
| 条带噪声 | 22.52 | 3.0 | 20.92 | 0.3129 |

### 2.3 交叉实验结果

**表3　前置降噪相对直接维纳复原的 PSNR 增益（dB）**

| 噪声 | 低通 D0=30 | 低通 D0=60 | 中值 k=5 | 中值 k=7 |
|---|---|---|---|---|
| 高斯白噪声 | −0.14 | +0.10 | −0.17 | −0.27 |
| 椒盐噪声 | −0.08 | −0.01 | **+1.35** | +1.16 |
| 条带噪声 | **+1.40** | +0.42 | +0.18 | +0.43 |

**表4　各格 PSNR 绝对值（dB）**

| 噪声 | 直接维纳 | 低通30 | 低通60 | 中值k5 | 中值k7 |
|---|---|---|---|---|---|
| 高斯白噪声 | 24.18 | 24.03 | 24.28 | 24.00 | 23.90 |
| 椒盐噪声 | 23.15 | 23.08 | 23.14 | 24.51 | 24.31 |
| 条带噪声 | 20.92 | 22.31 | 21.34 | 21.10 | 21.35 |

三条规律：① 匹配时有正增益（+1.35、+1.40 dB）；② 错配时无效或有害（−0.01、−0.17～−0.27 dB）；③ **对平稳高斯噪声四种算子全部无稳定增益**。

**表5　匹配与错配的对比**

| 噪声 | 匹配算子增益 | 错配算子增益 | 差值 |
|---|---|---|---|
| 椒盐噪声 | +1.35（中值） | −0.01（低通） | **+1.36** |
| 条带噪声 | +1.40（低通） | +0.43（中值） | **+0.96** |

### 2.4 机理分析

- **维纳已按信噪比自适应加权**：增益曲线无论 $K$ 取何值都在噪声主导的高频段自动衰减，比固定形状的低通更优 → 解释高斯噪声下无增益。
- **前置降噪补足的是建模能力**：匹配有效的两种情形，其噪声形态都**超出**式(1) 的"平稳加性噪声"假设（空间稀疏的脉冲、频域集中的周期结构），而维纳以单一 $K$ 作平滑加权，无法表达这类结构。
- **故"前置降噪抑制噪声放大"的说法不准确**：噪声放大由 $K$ 负责且已解决；前置降噪的真正作用是剔除不符合假设的成分，使维纳的假设更成立。

### 2.5 局限性与展望

局限：合成退化与空间不变模糊；最优 $K$ 事后选取；未覆盖混合噪声。
展望：噪声类型自动判别；非平稳噪声（泊松-高斯、列相关读出噪声）下的收益；序贯与联合处理的定量边界。

## 3 结论

① 前置降噪不是无条件改进，增益取决于**算子与噪声类型的匹配性**（匹配 +1.35/+1.40 dB；错配 −0.01/−0.17～−0.27 dB；差值 1.36/0.96 dB）。
② 对平稳高斯噪声任何前置降噪均无稳定增益，因为维纳增益本身在高频趋于零。
③ 前置降噪补足的是**建模能力**，而非噪声放大缺陷。
操作性建议：脉冲型噪声用中值，结构性条带噪声用低通，平稳高斯噪声不用前置降噪。

## 参考文献

Boulanger J, Kervrann C, Bouthemy P, Elbau P, Statnik J B, Sibarita J B, Salamero J. 2016. Joint denoising and deconvolution in fluorescence microscopy//IEEE International Conference on Image Processing. Phoenix, USA: IEEE: 1724-1728. DOI: 10.1109/ICIP.2016.7532653.

Brunelli R. 2009. Template Matching Techniques in Computer Vision: Theory and Practice[M]. Chichester: Wiley: 1-40. DOI: 10.1002/9780470744055.

Chen L, Zhang J W, Lin S, Fang F, Ren J S. 2022. D2HNet: joint denoising and deblurring with hierarchical network for robust night image restoration//Computer Vision – ECCV 2022. Cham: Springer: 91-110. DOI: 10.1007/978-3-031-19800-7_6.

Gonzalez R C, Woods R E. 2018. Digital Image Processing[M]. 4th ed. New York: Pearson: 178-252.

Haralick R M, Shapiro L G. 1992. Computer and Robot Vision, Volume II[M]. Reading: Addison-Wesley: 289-330.

Huang S Q, Liu Q. 2022. Addressing scale imbalance for small object detection with dense detector[J]. Neurocomputing, 473: 68-78. DOI: 10.1016/j.neucom.2021.11.107.

Jiang X Y, Xia Y F, Zhang X P, Ma J Y. 2022. Robust image matching via local graph structure consensus[J]. Pattern Recognition, 126: 108588. DOI: 10.1016/j.patcog.2022.108588.

Kalsotra R, Arora S. 2021. Background subtraction for moving object detection: explorations of recent developments and challenges[J]. The Visual Computer, 38(12): 4151-4178. DOI: 10.1007/s00371-021-02286-0.

Lewis J P. 1995. Fast normalized cross-correlation//Vision Interface. Quebec, Canada: Canadian Image Processing and Pattern Recognition Society: 120-123.

Liu C, Szeliski R, Kang S B, Zitnick C L, Freeman W T. 2009. Automatic estimation and removal of noise from a single image[J]. IEEE Transactions on Pattern Analysis and Machine Intelligence, 30(2): 299-314. DOI: 10.1109/TPAMI.2007.1176.

Mei L C, Zhao Y F, Wang H Y, Wang C Y, Zhang J, Zhao X X. 2022. Matching by pixel distribution comparison: multisource image template matching[J]. IET Signal Processing, 17(2): e12176. DOI: 10.1049/sil2.12176.

Nan Y, Ji H. 2020. Handling noise in image deblurring via joint learning//Computer Vision – ECCV 2020. Cham: Springer: 517-533. DOI: 10.1007/978-3-030-58517-4_31.

Paulin G, Ivasic-Kos M. 2023. Review and analysis of synthetic dataset generation methods and techniques for application in computer vision[J]. Artificial Intelligence Review, 56(9): 9221-9265. DOI: 10.1007/s10462-022-10358-3.

Szeliski R. 2022. Computer Vision: Algorithms and Applications[M]. 2nd ed. Cham: Springer: 51-108. DOI: 10.1007/978-3-030-34372-9.

Viola P, Jones M. 2001. Rapid object detection using a boosted cascade of simple features//Proceedings of the 2001 IEEE Computer Society Conference on Computer Vision and Pattern Recognition. Kauai, USA: IEEE: 511-518. DOI: 10.1109/CVPR.2001.990517.

Wang X Y, Yang H Y, Fu Z K. 2012. Edge detection algorithm based on wavelet transform and Wiener filter//2012 International Conference on Image Analysis and Signal Processing. Hangzhou, China: IEEE: 1-4. DOI: 10.1109/IASP.2012.6425051.

Zhang Y J. 2021. Frequency domain filtering//Handbook of Image Engineering. Singapore: Springer: 539-559. DOI: 10.1007/978-981-15-5873-3_13.

## 图题（中英文对照）

**图1　本文算法整体流程**
**Fig.1　Overall flowchart of the proposed algorithm**

**图2　清晰原图、点扩散函数与三类噪声的退化图像**
**Fig.2　Original image, point spread function and the degraded images with three noise types**

**图3　直接维纳复原的基线结果**
**Fig.3　Baseline results of direct Wiener restoration**

**图4　前置降噪增益的交叉矩阵与匹配性对比**
**Fig.4　Cross matrix of pre-denoising gain and the matching comparison**

**图5　四个典型情形的直观对比**
**Fig.5　Visual comparison of four representative cases**

**图6　维纳传递函数增益与三类噪声的频谱特征**
**Fig.6　Gain of the Wiener transfer function and the spectral characteristics of the three noise types**
