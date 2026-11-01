# VASP 批处理

`prepare_jobs.py` 生成 ENCUT / 体积扫描任务、按结构分目录或调用 VASPKIT 生成 KPOINTS；不提交作业。
`summarize_outputs.py` 一次提取能量、每原子能量、体积、熵项和不可约 K 点，并区分输出存在、计算结束与离子收敛。

```bash
python scripts/vasp/prepare_jobs.py encut 300 400 500 --source . --output encut-test
python scripts/vasp/summarize_outputs.py calculations --recursive -o results.csv
python scripts/vasp/collect_structures.py calculations --output collected
```


## 文件

- [calculate_nose_hoover_mass.py](calculate_nose_hoover_mass.py)：根据给定的温度、频率等参数计算Nosé-Hoover链热浴质量（SMASS）。
- [collect_structures.py](collect_structures.py)：收集子目录的结构文件。
- [prepare_jobs.py](prepare_jobs.py)：准备 VASP 批量任务；只生成输入，不提交作业。
- [run_elastic.py](run_elastic.py)：批量运行各 cij/strain_* 的优化脚本，不提交集群任务。
- [summarize_outputs.py](summarize_outputs.py)：汇总子目录的 VASP 输出。
- [vasp_xdatcar_analysis.py](vasp_xdatcar_analysis.py)：该脚本用于处理VASP的XDATCAR输出文件，计算声子态密度（Phonon DOS）、速度自相关函数（VACF），。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
