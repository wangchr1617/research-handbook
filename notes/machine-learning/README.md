# 机器学习

先了解数据划分、模型训练和验证，再按任务选择模型。深度学习实践使用 PyTorch。

## 先跑通数据与训练流程

先看 [数据划分与模型评估](数据划分与模型评估.md)，再运行 [scikit-learn 回归基线](scikit-learn回归基线.md)。理解简单模型后，使用 [PyTorch 自定义数据集](PyTorch自定义数据集.md)接入自己的表格，再进入下面的网络训练路线。

这些小例子不需要下载大型数据集，先用 CPU 验证形状、单位和评估流程。Python 基础见 [脚本与数组](../python/README.md)。

## 通用原理与传统模型

| 笔记 | 适用环境 |
| --- | --- |
| [机器学习概览](机器学习概览.md) | 通用（原理）/ Python（示例） |
| [完整机器学习项目实践](完整机器学习项目实践.md) | 通用（原理）/ Python（示例） |
| [分类](分类.md) | 通用（原理）/ Python（示例） |
| [模型训练](模型训练.md) | 通用（原理）/ Python（示例） |
| [支持向量机](支持向量机.md) | 通用（原理）/ Python（示例） |
| [决策树](决策树.md) | 通用（原理）/ Python（示例） |
| [集成学习与随机森林](集成学习与随机森林.md) | 通用（原理）/ Python（示例） |
| [降维](降维.md) | 通用（原理）/ Python（示例） |
| [支持向量机对偶问题](支持向量机对偶问题.md) | 通用（原理）/ Python（示例） |

## PyTorch 学习路线

先读安装、自动微分和训练循环，再选择网络模型。除安装与设备配置外，下面的小例子都可以在 CPU 跑通，不要求先获得 GPU。

| 笔记 | 内容 |
| --- | --- |
| [PyTorch 安装与入门](PyTorch安装与入门.md) | 官网、独立环境、CPU / CUDA / MPS、张量 |
| [PyTorch 自动微分](PyTorch自动微分.md) | 梯度、反向传播、能量对坐标求导 |
| [PyTorch 模型训练与保存](PyTorch模型训练与保存.md) | DataLoader、MLP、训练验证、检查点 |
| [PyTorch 卷积神经网络](PyTorch卷积神经网络.md) | 二维卷积与图像张量维度 |
| [PyTorch 循环神经网络](PyTorch循环神经网络.md) | GRU 与时间序列 |
| [PyTorch 自编码器](PyTorch自编码器.md) | 潜在表示与重建 |
| [PyTorch 强化学习入门](PyTorch强化学习入门.md) | DQN 目标与一次参数更新 |
| [PyTorch 设备与并行训练](PyTorch设备与并行训练.md) | 设备迁移、混合精度与 DDP 准备 |

## 科研应用

| 笔记 | 适用环境 |
| --- | --- |
| [MatterGen 入门](MatterGen入门.md) | Windows + WSL（镜像准备）、Linux 集群（运行） |

配套实践见 [CGCNN](../../examples/machine-learning/cgcnn/CGCNN入门.ipynb)和 [PaiNN](../../examples/machine-learning/painn/PaiNN模型.ipynb)，具体依赖与数据按对应案例准备。

## 资料来源与版本

通用原理与传统模型章节收录自《机器学习实战》（Hands-On Machine Learning with Scikit-Learn and TensorFlow）的中文资料，原书作者为 Aurélien Géron。各章附有译者注、公式、图片和代码说明。

原资料的版权信息为：Copyright 2017 Aurélien Géron，O’Reilly，ISBN 978-1-491-96229-9。通用章节中的部分 Python 示例沿用原资料接口，运行时需核对 scikit-learn 等依赖版本；首次实践优先使用上面的回归基线和 PyTorch 路线。

PyTorch 笔记根据各篇所列官方文档编写，配套代码使用人工小数据解释流程。它们用于解释流程，真实材料数据仍需独立评估；多卡训练还需在实际分配的硬件中核对。通用章节配图放在 `assets/hands-on-ml/`。
