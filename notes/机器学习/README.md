# 机器学习

按学习顺序阅读：[阅读目录](阅读目录.md)。

**适用环境：通用（原理）；Python、PyTorch 和科研应用按各篇环境说明准备。**

先了解数据划分、模型训练和验证，再按任务选择模型。深度学习实践使用 PyTorch。

## 先跑通数据与训练流程

先看 [数据划分与模型评估](基础与评估/数据划分与模型评估.md)，再运行 [scikit-learn 回归基线](基础与评估/scikit-learn回归基线.md)。理解简单模型后，使用 [PyTorch 自定义数据集](PyTorch基础/PyTorch自定义数据集.md)接入自己的表格，再进入下面的网络训练路线。

这些小例子不需要下载大型数据集，先用 CPU 验证形状、单位和评估流程。Python 基础见 [脚本与数组](../Python/README.md)。

## 学习路线与分类

| 目录 | 内容与建议顺序 |
| --- | --- |
| [基础与评估](基础与评估/README.md) | 先建立数据划分、基线训练与独立评估流程。 |
| [传统模型](传统模型/README.md) | 比较分类、支持向量机、树模型和降维方法。 |
| [PyTorch 基础](PyTorch基础/README.md) | 学习张量、自动微分、数据集、训练保存与设备配置。 |
| [神经网络与科研应用](神经网络与科研应用/README.md) | 按图像、序列、表示学习和科研任务选择网络。 |

## 原子与电子模型专题

通用训练基础之后，可按研究对象阅读[机器学习势函数](../机器学习势函数/README.md)、[机器学习哈密顿量](../机器学习哈密顿量/README.md)和[机器学习紧束缚模型](../机器学习紧束缚模型/README.md)。三个专题分别讨论能量与力、电子矩阵、轨道空间与参数化，并相互链接。

配套实践见 [CGCNN](../../examples/machine-learning/cgcnn/CGCNN入门.ipynb)和 [PaiNN](../../examples/machine-learning/painn/PaiNN模型.ipynb)，具体依赖与数据按对应案例准备。

## 资料来源与版本

通用原理与传统模型章节收录自《机器学习实战》（Hands-On Machine Learning with Scikit-Learn and TensorFlow）的中文资料，原书作者为 Aurélien Géron。各章附有译者注、公式、图片和代码说明。

原资料的版权信息为：Copyright 2017 Aurélien Géron，O’Reilly，ISBN 978-1-491-96229-9。通用章节中的部分 Python 示例沿用原资料接口，运行时需核对 scikit-learn 等依赖版本；首次实践优先使用上面的回归基线和 PyTorch 路线。

PyTorch 笔记根据各篇所列官方文档编写，配套代码使用人工小数据解释流程。用于真实材料数据时仍需独立评估；多卡训练还需在实际分配的硬件中核对。通用章节配图放在 `assets/hands-on-ml/`。
