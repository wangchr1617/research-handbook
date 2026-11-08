
# Research Handbook

本仓库旨在记录学习与科研过程中常用的入门资源，并为团队提供一个共享、合作与提升科研水平的平台，方便成员查阅与贡献。

## 🤝 Preface

入学两年来，我深感自学的挑战与不易。真诚感谢刘晗煜师兄的启发，让我萌生了创建这个仓库的想法。希望它能成为后来的师弟师妹们学习路上的一份助力。

也真心期待大家积极参与，共同完善内容、补充资源，并提出宝贵的改进建议。无论是分享学习笔记、科研心得，还是记录遇到的困难和思考，每一份贡献都是团队宝贵的财富。

愿这个仓库不仅是知识的汇聚之地，更成为我们交流想法、携手进步的共同平台。

## 从哪里开始

完整阅读顺序见[入门阅读目录](getting-started/阅读目录.md)与[专题阅读目录](notes/阅读目录.md)。

第一次访问，建议从[入门路线](getting-started/README.md)开始；想先动手，可以运行 [RMSE 小案例](examples/rmse/README.md)。希望分享学习与计算经验，可阅读[贡献指南](CONTRIBUTING.md)。

开发科研 Agent 应用，可阅读[后端工程专题](notes/后端工程/README.md)，并运行包含登录、文件上传、历史会话与后台任务的 [Agent Demo](examples/backend/agent-demo/README.md)。

构建文献检索与科研知识库，可阅读[知识工程专题](notes/知识工程/README.md)，学习 MinerU 文档解析、RAG、知识图谱与 Neo4j，并对照 Archeos、Alkemie 的源码实例。

查找结构、性质、谱学、反应和 AI 训练数据，可阅读[材料数据库专题](notes/材料数据库专题/README.md)，了解数据内容、官网入口与 API 调用方法。

研究未知晶体结构，可先读[晶体结构预测专题](notes/晶体结构预测专题/README.md)了解任务、生成模型、数据与评价，再读[晶体结构搜索专题](notes/晶体结构搜索专题/README.md)学习全局优化算法、软件工作流与结果验证。

材料计算可从[材料应用专题](notes/材料应用/README.md)按材料体系、功能性质或应用目标选择教程与[实际案例](examples/materials/README.md)。

认识毕业后的产业与学术方向，可阅读[企业专题](notes/企业专题/README.md)和[高校与研究院专题](notes/高校与研究院专题/README.md)，按领域对照产品、研究方法、工具平台与岗位能力。

搭建自己的计算环境，可阅读[算力硬件与集群搭建专题](notes/算力硬件与集群搭建专题/README.md)，从需求分析、CPU/GPU 与存储选型走到网络、Slurm 部署和基本运维。

## 最近新增的十篇笔记

展示 `notes/` 与 `getting-started/` 最近新增的十篇正文笔记，新增笔记时同步更新。按新增日期及加入先后倒序排列，无法区分先后时按路径排序；历史日期依据 Git 新增记录，更新或重命名已有笔记不计入新增。维护规则见 [AGENTS.md](AGENTS.md#阅读目录与最近新增笔记)。

| 新增日期 | 笔记 | 主题 |
| --- | --- | --- |
| 2026-11-08 | [Packmol 盐溶液与电荷平衡](notes/Packmol/Packmol盐溶液与电荷平衡.md) | Packmol |
| 2026-11-08 | [Quantum ESPRESSO 能带与态密度](notes/Quantum%20ESPRESSO/QE能带与态密度.md) | Quantum ESPRESSO |
| 2026-11-08 | [环境依赖 SK 的应变能带验证](notes/机器学习紧束缚模型/环境依赖SK/环境依赖SK的应变能带验证.md) | 环境依赖 SK |
| 2026-11-08 | [含 SOC 哈密顿量的能带验收](notes/机器学习哈密顿量/自旋与扩展/含SOC哈密顿量的能带验收.md) | 自旋与扩展 |
| 2026-11-08 | [铁电极化分支与薄膜响应](notes/材料应用/铁电与介电/铁电极化分支与薄膜响应.md) | 铁电与介电 |
| 2026-11-08 | [合金弹性与空位迁移的模型验证](notes/材料应用/金属与合金/合金弹性与空位迁移的模型验证.md) | 金属与合金 |
| 2026-11-08 | [磁各向异性能与易磁化轴](notes/材料应用/磁性与自旋/磁各向异性能与易磁化轴.md) | 磁性与自旋 |
| 2026-11-08 | [热电输运张量与 ZT 的对照](notes/材料应用/热电/热电输运张量与ZT的对照.md) | 热电 |
| 2026-11-08 | [聚合物链构象与熔体平衡](notes/材料应用/有机与高分子/聚合物链构象与熔体平衡.md) | 有机与高分子 |
| 2026-11-08 | [氧化物空位与离子迁移](notes/材料应用/无机非金属/氧化物空位与离子迁移.md) | 无机非金属 |

## 目录导航

| 目录 | 用途 |
| --- | --- |
| [getting-started](getting-started/README.md) | 入门路线、环境准备与新生指南 |
| [notes](notes/README.md) | 专题原理、学习笔记与研究方法 |
| [inputs](inputs/README.md) | 按软件或任务组织的计算输入模板 |
| [scripts](scripts/README.md) | 可复用脚本与计算辅助工具 |
| [examples](examples/README.md) | 科研案例、Notebook 与配套数据 |
| [templates](templates/README.md) | 学习与计算记录模板 |

机器学习原子模型可按任务进入：[势函数](notes/机器学习势函数/README.md)用于原子能量与动力学，[哈密顿量](notes/机器学习哈密顿量/README.md)用于电子矩阵与能谱，[紧束缚模型](notes/机器学习紧束缚模型/README.md)用于有效轨道空间与参数学习。

项目协作约定见 [AGENTS.md](AGENTS.md)，供成员与不同 AI 助手参考。

## 🛠️ Usage

1. 如何下载？

```bash
git clone https://github.com/wangchr1617/research-handbook.git
```

2. 如何贡献？

欢迎通过 Issue 提出问题，或通过 Pull Request 补充资料。具体步骤见[贡献指南](CONTRIBUTING.md)。

## 📄 License

此仓库采用 MIT 许可证授权。详情请参见 [LICENSE](LICENSE)。

## 💬 Contact

Markdown 和 Git 相关问题请首先参阅 [Markdown 入门](getting-started/git/Markdown入门.md) 和 [Git 入门](getting-started/git/Git入门.md)。

如果有任何问题或建议，请随时提交 Issue 或联系仓库所有者。
