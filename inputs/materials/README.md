# 材料应用输入参数

**适用环境：macOS / Linux；JSON 为软件无关的案例参数。**

每个 JSON 对应一个可运行案例，`case` 必须与命令行案例名一致，`schema_version` 为 1。长度用 Å，能量参数用 eV，温度用 K，时间步用 fs；Langevin 摩擦系数在运行器中按 VASP 的 ps⁻¹ 单位设置。

| 参数 | 内容 |
| --- | --- |
| [metal.json](metal.json) | Al 初始晶格；EAM 势与扫描方式见运行器 |
| [inorganic.json](inorganic.json) | MgO 晶格、体积点、截断能与 k 网格 |
| [organic.json](organic.json) | 乙醇方法与构象初始二面角 |
| [semiconductor.json](semiconductor.json) | Si 晶格与自洽 k 网格 |
| [ferroelectric.json](ferroelectric.json) | BaTiO₃ 晶胞、极性路径与电子精度 |
| [magnetism.json](magnetism.json) | Fe 晶格与电子精度 |
| [thermoelectric.json](thermoelectric.json) | Si 电子输运的晶格与原始 k 网格 |
| [phase-change.json](phase-change.json) | GeTe 超胞、时间步、温度阶段与统计 cutoff |
| [battery.json](battery.json) | 石墨、LiC₆、Li 参考结构及精度 |
| [electrocatalysis.json](electrocatalysis.json) | Pt 模型、温度、电位与 H₂ 标准熵 |

完整输入由[运行器](../../scripts/materials/run_case.py)生成，在本地子任务目录中保留。复制参数文件并通过 `--config` 选择新设置，操作见[运行说明](../../notes/材料应用/本机运行与结果检查.md)。参数变更后使用新目录，避免将旧结果与新输入混合。

案例与结果见[材料案例](../../examples/materials/README.md)，材料问题入口见[材料应用](../../notes/材料应用/README.md)。
