<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/research_handbook_logo.webp">
    <img src="docs/assets/research_handbook_logo_light.webp" alt="Research Handbook 标志" width="680">
  </picture>
</p>

# Research Handbook

ALKEMIE 课题组共建的科研学习手册。从配置环境、提交第一份计算，到查阅材料模拟方法、复现案例和开发科研工具。

[开始学习](#从哪里开始) · [最新笔记](#最近新增的十篇笔记) · [目录导航](#目录导航) · [参与贡献](#参与贡献) · [致谢](#致谢)

## 从哪里开始

- **刚入组**　从[入门阅读目录](getting-started/阅读目录.md)开始，按自己的系统准备环境，练习使用 Linux 集群和 Git。
- **想先动手**　运行 [RMSE 小案例](examples/rmse/README.md)，或打开[公式实验台](https://wangchr1617.github.io/research-handbook/)，拖动参数观察带隙、声子色散、态密度和扩散拟合的变化。静态示意图见[公式配图索引](examples/formula-figures/README.md)。
- **已有研究方向**　用[专题阅读目录](notes/阅读目录.md)选取学习顺序，或在下方按研究任务找资料。

## 最近新增的十篇笔记

[列表维护规则](AGENTS.md#阅读目录与最近新增笔记)

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

### 按研究任务找资料

| 想做什么 | 阅读入口 |
| --- | --- |
| 按材料体系或性质做计算 | [材料应用专题](notes/材料应用/README.md)和[配套案例](examples/materials/README.md) |
| 预测未知晶体结构 | 先读[晶体结构预测](notes/晶体结构预测专题/README.md)了解生成模型、数据与评价，再读[晶体结构搜索](notes/晶体结构搜索专题/README.md)学习全局优化、软件工作流与结果验证 |
| 选机器学习原子模型 | 用[势函数](notes/机器学习势函数/README.md)研究原子能量与动力学，用[哈密顿量](notes/机器学习哈密顿量/README.md)研究电子矩阵与能谱，用[紧束缚模型](notes/机器学习紧束缚模型/README.md)学习有效轨道空间与参数 |
| 查找材料数据 | 在[材料数据库专题](notes/材料数据库专题/README.md)查结构、性质、谱学、反应与 AI 训练数据及 API |
| 开发科研 Agent | 阅读[后端工程专题](notes/后端工程/README.md)，运行带登录、文件上传、历史会话和后台任务的 [Agent Demo](examples/backend/agent-demo/README.md) |
| 搭建科研知识库 | 在[知识工程专题](notes/知识工程/README.md)学习 MinerU、RAG 和 Neo4j，并对照 Archeos、Alkemie 的源码实例 |
| 搭建自己的计算环境 | 在[算力硬件与集群搭建专题](notes/算力硬件与集群搭建专题/README.md)查 CPU/GPU、存储、网络选型及 Slurm 部署与运维 |
| 了解毕业去向 | 在[企业专题](notes/企业专题/README.md)和[高校与研究院专题](notes/高校与研究院专题/README.md)了解产品、研究方向、工具平台与岗位能力 |

## 参与贡献

欢迎补充笔记、修正错误或分享可复现的计算案例。可以通过 [Issue](https://github.com/wangchr1617/research-handbook/issues) 提出问题，或按[贡献指南](CONTRIBUTING.md)提交 Pull Request。初次使用 GitHub，可先读 [Git 入门](getting-started/git/Git入门.md)和 [Markdown 入门](getting-started/git/Markdown入门.md)。

克隆仓库到本地：

```bash
git clone https://github.com/wangchr1617/research-handbook.git
```

目录维护和笔记写作约定见 [AGENTS.md](AGENTS.md)。

## 致谢

感谢刘晗煜师兄启发我创建这本手册，也感谢分享笔记、复核计算案例、纠正错误和反馈问题的同学。手册标志沿用了 ALKEMIE 的蓝紫轨道配色。

[![Research Handbook 的 GitHub 贡献者头像](https://contrib.rocks/image?repo=wangchr1617/research-handbook)](https://github.com/wangchr1617/research-handbook/graphs/contributors)

[查看 GitHub 贡献者](https://github.com/wangchr1617/research-handbook/graphs/contributors)

## 许可

手册原创内容采用 [MIT 许可证](LICENSE)。引用的第三方资料遵循各自的许可。
