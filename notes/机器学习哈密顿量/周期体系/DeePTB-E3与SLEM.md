# DeePTB-E3 与 SLEM

**适用环境：通用（原理）；实现接口按 DeePTB 对应版本准备。**

DeePTB 不只有 Slater–Koster 参数路线。DeePTB-E3 使用等变表示学习轨道算符矩阵，SLEM 是其中重要的严格局域架构。它与 [DeePTB-SK](../../机器学习紧束缚模型/环境依赖SK/DeePTB-SK.md)适合放在两个相邻专题中对照阅读。

## 一、历史与开发团队

Zhanghao Zhouyin、Zixi Gan、MingKang Liu、Shishir Kumar Pandey、Linfeng Zhang 和 Qiangqiang Gu 在 2024 年发布 SLEM 预印本，于 ICLR 2025 发表。实现进入 DeepModeling 的 DeePTB 项目，与 Gu 等人的紧束缚模型路线相衔接。[^paper][^docs]

## 二、严格局域等变表示

SLEM 在固定局域邻域内构造节点与原子对特征，通过多体耦合提高表达能力，同时控制感受野不随层数向远端不断扩张。它还使用 SO(2) 卷积相关设计降低高角阶运算成本，面向包含较高轨道角动量的基组。[^paper]

这里的“消息”应结合具体更新规则理解：模型可以有局域聚合和层间更新，而不等同于通常跨邻居多跳传播的节点消息网络。局域性有助于大体系分块与并行，但不自动解决长程电荷响应。

## 三、不同算符怎样输出

哈密顿量和密度矩阵可采用等变张量表示；固定原子基的重叠积分具有严格两中心性质，官方方法说明用 SK 参数化获得更高效的表示。[^docs]

因此不能笼统地说“E3 路线把所有矩阵都用同一个等变输出头学习”。也不能因为能学习密度矩阵，就跳过其电子数、厄米性及适用占据条件检查。

## 四、与 SK 路线比较

| 路线 | 主要输出与监督 | 适合首先检查 |
| --- | --- | --- |
| DeePTB-SK | 环境相关 TB 参数，典型为能谱监督 | 轨道空间、能窗、SK 约定 |
| DeePTB-E3 / SLEM | 参考基下的算符矩阵 | 轨道规范、矩阵标签、等变与局域性 |

二者共享软件生态，但标签、配置与评估不能直接互换。E3 也不是“SK 只要多开一个参数”就能得到的模型。

## 五、结果检查

先用官方小体系教程核对解析与装配，然后检查 $H,S$、旋转等变、能带及目标算符性质。大规模应用分别报告模型推理、装配与谱求解成本，避免把矩阵预测速度当成整个电子结构流程的速度。

## 实践：Si 的 SLEM 完整输入与文件布局

配套[Si E3 输入](../../../inputs/machine-learning/deeptb-si-e3.json)采用官方 CPU 例子。关键配置如下：

```json
{
  "common_options": {"basis": {"Si": "1s1p"}, "device": "cpu", "overlap": true},
  "model_options": {
    "embedding": {"method": "slem", "r_max": {"Si": 7.4},
                  "irreps_hidden": "32x0e+32x1o+16x2e", "n_layers": 3,
                  "avg_num_neighbors": 86, "tp_radial_emb": true},
    "prediction": {"method": "e3tb", "neurons": [64, 64]}
  }
}
```

此处只是完整输入的模型部分，训练还需要 `train_options` 与 `data_options`。`1s1p` 表示一组 s 与一组 p 空间轨道，共四轨道，不是 Si 的完整物理电子壳层写法。64 个 Si 的全矩阵若显式稠密存储为 `256×256`，训练则常按局域块稀疏组织。

数据选项设定 `root=./data`、`prefix=Si64`、`get_Hamiltonian=true` 和 `get_overlap=true`，要求相应的结构、轨道矩阵和重叠数据，而非仅有能带标签。

```bash
dptb train input_short_cpu.json -o ./training
dptb run band.json -i ./training/checkpoint/实际检查点.pth -o ./band_output -stu ./data/Si64.vasp
```

检查点文件名以实际训练输出为准，不把上面的说明性名称复制后当成已有文件。完整命令与数据格式见[官方 E3 教程](https://deeptb.readthedocs.io/en/latest/quick_start/hands_on/tutorial4_E3_si.html)。

## 为什么输出头与损失要配套

该例 `prediction.method=e3tb` 配合 `loss_options.train.method=hamil_abs`；SK 能谱学习使用 `eigvals`，二者标签含义不同。更换输出头却沿用另一条路线的数据标志，可能在读取阶段报错，也可能训练到与目标不一致的量。

中间表示维数为 $32+32\times3+16\times5=208$，三层表示更新仍遵循严格局域设计，不应按 `3×7.4 Å` 简单解释为多跳半径。结合边/节点更新源码再判断物理依赖范围。

## 参考资料

[^paper]: Z. Zhouyin et al. Learning local equivariant representations for quantum operators. *ICLR* (2025). [预印本及版本](https://arxiv.org/abs/2407.06053)。
[^docs]: DeePTB. [E3 官方教程与算符表示说明](https://deeptb.readthedocs.io/en/latest/quick_start/hands_on/tutorial4_E3_si.html)、[官方实现](https://github.com/deepmodeling/DeePTB)。

返回[分类导航](README.md)或[专题首页](../README.md)。
