# DeePTB-SK

**适用环境：通用（原理）；具体运行环境按 DeePTB 官方教程准备。**

DeePTB-SK 保留 Slater–Koster 紧束缚结构，用神经网络学习局域环境对在位与跃迁参数的影响。它的典型监督来自参考能谱，因此无需把参考 DFT 的整套原子轨道矩阵直接作为目标。

## 一、历史与开发团队

Qiangqiang Gu、Zhanghao Zhouyin、Shishir Kumar Pandey、Peng Zhang、Linfeng Zhang 与 Weinan E 在 2023 年公开预印本，2024 年发表于 *Nature Communications*。原论文合作单位包括北京大学、AI for Science Institute、天津大学、DP Technology 等。实现位于 DeepModeling 项目的 DeePTB。[^paper][^code]

## 二、从传统 SK 到环境相关参数

传统两中心 SK 的径向积分通常只依赖键长与元素对。DeePTB 为其加入局域环境修正，示意为

$$
V_{ll'\zeta}^{ij}=\mathcal F_{ll'\zeta}
(r_{ij},\mathcal N_i,\mathcal N_j),
$$

其中 $\zeta$ 标识 $\sigma,\pi,\delta$ 等键通道。网络把邻域编码成不变量，用来调整参数；方向关系仍通过 SK 表装配。具体模型可组合基础径向形式与环境修正，上式仅概括依赖关系，并非指定软件中的加法或乘法修正形式。[^paper]

学得参数后组装 $H(\mathbf k)$，求本征值，再与参考能带比较损失。SK 公式的入门推导见[从双原子到能带](../基础与比较/从双原子到紧束缚能带.md)。

## 三、能谱监督带来的优势与歧义

优势是可用常见 DFT 能带标签，构造较紧凑的有效轨道空间，并描述热扰动或应变后的电子性质。参考数据并不必须与有效 TB 使用完全相同的基。

同时，能谱无法唯一确定矩阵及波函数。SK 形式、局域性与平滑性提供约束，但不能据带误差小就认为所有光学、拓扑或输运算符都准确。轨道数与能窗也限制可以恢复的信息。

## 四、DeePTB 的两条路线

| 路线 | 学习重点 | 标签与检查 |
| --- | --- | --- |
| SK | 低维参数与环境修正 | 能带、轨道空间、能窗与方向约定 |
| [E3 / SLEM](../../机器学习哈密顿量/周期体系/DeePTB-E3与SLEM.md) | 等变算符矩阵 | 矩阵规范、轨道块与算符约束 |

DeePTB 是共享软件名，不能把两条路线的配置、训练损失和适用边界混成一套。与 Deep Potential 联用时，原子轨迹和电子性质由相应模型分别承担；TB 模型不会自动成为势能模型。

## 五、结果检查与实践入口

先用硅等官方小体系学习轨道、键和能窗设置；重建参考能带后训练，再在独立应变、位移和一般 $k$ 点上测试。高温或缺陷应用还需要对应构型覆盖，不能只拟合平衡晶体的高对称路径。

官方文档包含 SK 与 E3 的独立教程，命令和配置随版本核对：[DeePTB 文档](https://deeptb.readthedocs.io/en/latest/)。

## 实践：Si 的基础 SK 与环境修正分两步

配套[基础 SK 输入](../../../inputs/machine-learning/deeptb-si-sk.json)取自官方 `input_2.json`，[环境相关输入](../../../inputs/machine-learning/deeptb-si-environment.json)取自 `input_3.json`。二者共享 `Si: ["3s","3p","d*"]` 的轨道空间，但学习的自由度不同。

```json
{
  "embedding": {"method": "se2", "rs": 2.5, "rc": 5.0,
                "radial_net": {"neurons": [10, 20, 30]}},
  "prediction": {"method": "sktb", "neurons": [16, 16, 16]}
}
```

上面是环境模型 `model_options` 的部分。它在基础 `nnsk` 参数化上加入结构环境编码和预测头；完整输入中还保留基线与冻结策略。不能把不含 `embedding` 的基础 `nnsk` 训练直接称作已经学习了环境修正。

`3s+3p+d*` 对应一组 s、一组 p 和一组 d 有效轨道，共九个空间轨道；`d*` 是有效极化/扩展通道约定，不是宣称占据了某个 d 壳层。数据中 `get_eigenvalues=true`、`get_Hamiltonian=false` 明确采用能谱监督。

## 输入路径、checkpoint 与后处理

在匹配的官方 silicon tutorial 目录中放置数据与输入，然后运行：

```bash
dptb train input_2.json -o ./sk_train
dptb train input_3.json -o ./env_train
```

第二步需要按[官方教程](https://deeptb.readthedocs.io/en/latest/)设置相应基线初始化，不能只把两个目录顺序运行就假定模型参数会自动传递。CPU 试运行要修改 `common_options.device`；官方配置本身写的是 CUDA。

[能带后处理输入](../../../inputs/machine-learning/deeptb-si-band.json)规定 $k$ 路径、标签、电子数与显示能窗。示例的 `E_fermi=-4.722` 来自该示例参考口径，不能照抄到另一份 Si 计算，更不能用于任意材料。

从数学上看，网络参数影响跃迁，跃迁影响 $H(k)$，本征值进入损失；可先运行[SSH 能谱拟合](../../../examples/machine-learning/atomistic-models/fit_ssh.py)，观察整条链如何实际优化。

## 参考资料

[^paper]: Q. Gu et al. Deep learning tight-binding approach for large-scale electronic simulations at finite temperatures with ab initio accuracy. *Nature Communications* **15**, 6772 (2024). [正式论文](https://doi.org/10.1038/s41467-024-51006-4)、[预印本](https://arxiv.org/abs/2307.04638)。
[^code]: DeepModeling. [DeePTB 官方仓库](https://github.com/deepmodeling/DeePTB)。

返回[分类导航](README.md)或[专题首页](../README.md)。
