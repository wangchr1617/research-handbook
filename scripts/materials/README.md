# 材料应用计算与后处理

**适用环境：macOS / Linux；Python 环境需包含 ASE、NumPy 和 Matplotlib。**

- [run_local.sh](run_local.sh)：选择已有 Python 环境与本地程序路径，不安装依赖。
- [run_case.py](run_case.py)：按案例生成结构与程序输入、顺序运行、检查、提取数值和绘图。
- [plot_results.py](plot_results.py)：读取已提取的公开数值重绘，不启动计算程序。
- [analyze_phase.py](analyze_phase.py)：从完成的 GeTe 三阶段原始输出提取部分 RDF、分元素配位及去除质心漂移的 MSD。
- [test_materials.py](test_materials.py)：核对运行目录保护、续跑指纹、配置与真实输出分析。
- [record_startup.py](record_startup.py)：从 VASP 输出记录程序版本、迭代步数与文件摘要，保存在运行目录。
- [audit_materials.py](audit_materials.py)：检查计算数据、参数和文件摘要，发现缺失或不一致时返回非零状态。

```bash
bash scripts/materials/run_local.sh --help
bash scripts/materials/run_local.sh metal --output /tmp/al-example
bash scripts/materials/run_local.sh --plot inorganic examples/materials/inorganic/data --output /tmp/mgo.png
bash scripts/materials/run_local.sh --phase-structure _validation_runs/materials-user/phase-change
```

参数文件见[输入](../../inputs/materials/README.md)，逐例模型与命令见[案例](../../examples/materials/README.md)，数值定义和研究路线见[专题](../../notes/材料应用/README.md)。

`--resume` 复用已完成且输入/输出未变化的子任务。改变模型、参数或势文件后应选择新运行目录。`--publish` 只导出该例的提取数据、图和指纹；PAW 势及大输出留在本地运行位置。

GeTe 的受控短段续算使用 `--resume --continue-md`，详见[运行与结果检查](../../notes/材料应用/本机运行与结果检查.md)。运行摘要可从输出单独提取：

```bash
"$MATERIALS_PYTHON" scripts/materials/record_startup.py phase-change \
  --work _validation_runs/materials-user/phase-change
"$MATERIALS_PYTHON" scripts/materials/audit_materials.py --verify-local
```

这里的 `MATERIALS_PYTHON` 需先设为已有环境的解释器绝对路径。审计的本地摘要检查针对 `_validation_runs/materials/<case>`；仅检查数据文件时可省略 `--verify-local`。
