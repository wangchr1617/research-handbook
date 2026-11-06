# DeepH

**适用环境：通用（原理）；数据来自相容的局域轨道电子结构计算。**

DeepH 学习晶体结构到局域基下 DFT 哈密顿量矩阵块的映射，目标是绕过新结构上重复进行的自洽场迭代。它保留电子结构信息，与只学习势能面的 Deep Potential 不同。

## 一、历史与开发团队

He Li、Zun Wang、Nianlong Zou、Meng Ye、Runzhang Xu、Xiaoxun Gong、Wenhui Duan 和 Yong Xu 于 2022 年正式发表 DeepH，预印本于 2021 年公开。工作主要由清华大学徐勇、段文晖相关团队及合作单位完成。[^paper]

## 二、局域矩阵块与局域坐标

对原子轨道基而言，矩阵可按原子对拆成 $H_{i\alpha,j\beta}(\mathbf R)$。局域轨道使远距离耦合较小，从而可用截断图组织稀疏块。网络读取结构邻域，预测每条相关边对应的矩阵块。

难点是 $p,d$ 等轨道随旋转混合。原始 DeepH 利用由局域几何定义的坐标系，在局域表示中学习矩阵，再通过基变换恢复全局表示。这把输出的旋转协变问题转化为规范一致的局域学习与变换。[^paper]

## 三、推理流程与边界

结构 → 周期邻居图 → 局域坐标 → 预测局域块 → 变回全局轨道基 → 装配 $H(\mathbf k),S(\mathbf k)$ → 电子性质。

其中 $S$ 需由相容的基和流程提供或处理，不能默认 $S=I$。矩阵预测代替的是相应参考方法下的自洽结果代理；改变电荷态、磁态或全局电子边界条件时，几何局域环境未必足以确定原来的标签。

局域坐标方案还要关注近共线邻居、参考轴切换和近对称构型。后续 [DeepH-E3](DeepH-E3.md)将等变性更直接地放入网络，以减少对局域坐标处理的依赖。

## 四、特点与适用问题

DeepH 的代表性应用包括大超胞、扭转范德华结构等：小胞中学到的局域结构–矩阵关系，可在局部环境相似的大体系中组合。它没有自动解决所有长程电荷重排，也没有免除后续大规模谱计算的成本。

与 [DeePTB-SK](../../机器学习紧束缚模型/环境依赖SK/DeePTB-SK.md)相比，DeepH 更直接学习参考基中的矩阵块；后者用参数化低维 TB 形式和能谱目标构造有效模型。

## 五、结果检查

先用解析得到的参考矩阵重建能带，再学习少量结构；检查周期位移、轨道顺序、局域到全局变换和厄米性。仅有矩阵 MAE 不够，还需比较目标能窗、带隙及派生性质。代码与数据处理入口见 [DeepH-pack](https://github.com/mzjb/DeepH-pack)。

## 实践：Graphene 的原始 INI 输入

配套[graphene 输入](../../../inputs/machine-learning/deeph-graphene.ini)来自原始 DeepH-pack 的 `ini/graphene.ini`，不是后来新包的 TOML 接口。其关键部分是：

```ini
[basic]
interface = npz
dataset_name = graphene
graph_dir = /home/user/DeepH/graph_data/
save_dir = /home/user/DeepH/result/
raw_dir = /path/to/downloaded/dataset
[graph]
create_from_DFT = False
radius = 6.0
```

这里 `/home/user` 和 `/path/to` 是需要改写的数据/结果位置；`interface=npz` 意味着它读取已经整理的矩阵数据，不能直接把含 OUTCAR 的目录放进去。完整文件的 `orbital` 枚举 C–C 轨道对的输出索引。

例如 C 的 `s2p2d1` 基含两个 s 径向函数、两组 p 和一组 d，共 $2+2\times3+5=13$ 个轨道；C–C 块就是 `13×13`。在位块也包括不同轨道间耦合，不是只存十三个对角数。

## 从文件到电子谱的实际步骤

在该历史实现中，先按对应教程生成可读数据，再运行：

```bash
deeph-train --config graphene.ini
```

CLI 入口由[原始 `setup.py`](https://github.com/mzjb/DeepH-pack/blob/main/setup.py)注册。原始配置使用随机比例切分，正式研究应另保留独立构型验证。不要把上游示例中的用户路径当成集群实际目录。

局域坐标预测后，要对块做相容基变换，按原子对和晶格位移装配。设一维周期的相邻胞跃迁为 $T$，则 $H(k)=H_0+e^{ikd}T+e^{-ikd}T^\dagger$，后两项配对确保厄米性。二维 graphene 只是把平移和相位扩展到二维晶格；漏掉负平移的共轭块会产生非厄米谱。

实空间装配的可运行例子见[SSH 矩阵与能带脚本](../../../examples/machine-learning/atomistic-models/fit_ssh.py)，其规则与真实大块相同，但模型维数和标签来源不同。

## 参考资料

[^paper]: H. Li et al. Deep-learning density functional theory Hamiltonian for efficient ab initio electronic-structure calculation. *Nature Computational Science* **2**, 367–377 (2022). [正式论文](https://doi.org/10.1038/s43588-022-00265-6)、[预印本](https://arxiv.org/abs/2104.03786)。

返回[分类导航](README.md)或[专题首页](../README.md)。
