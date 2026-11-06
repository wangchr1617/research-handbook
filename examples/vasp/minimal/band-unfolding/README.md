# 硅完美超胞能带反折叠

操作与结果见[笔记](../../../../notes/VASP/电子结构与成键/VASP能带反折叠.md)。

准备授权 Si `POTCAR`，安装 `requirements.txt` 中依赖并加载 VASP；执行 `qsub job.pbs`。`run.py` 生成 k 点并运行四阶段对照，随后调用 easyunfold 计算谱权重与绘图。已有输出可执行 `python3 postprocess.py`，产物为 `unfolding-results.json`、`easyunfold.json` 和 `si-unfolded.png`。

`SUPERCELL_MATRIX` 对应超胞晶格相对于原胞的变换。本例仅适用于完美非自旋硅的价带对照，阈值与四条原胞价带的检查应随体系调整。
