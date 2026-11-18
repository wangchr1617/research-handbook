# NequIP 模型部署与跨接口单点

训练 checkpoint 保存训练状态。发布或迁移时按版本打包，生产时为目标接口编译。先用相同结构的单点核对两端能量和力，再进行结构优化或分子动力学。

## 一、在 ASE 留下一份单点基准

下面以带 AOTInductor 的现代接口为例。运行前已有兼容的 checkpoint 或模型包，且编译环境和目标机器的设备设置相容。将文件名替换为实际路径。若使用支持 Si 的模型，可以从仓库的[硅原胞](../../examples/vasp/minimal/equation-of-state/POSCAR)取结构，并保留一份略微缩放晶胞的构型。理想硅的力可能接近零，再加一份轻微移位的构型，更容易发现对接时的原子排序或单位错误。

```bash
nequip-compile model.ckpt model.nequip.pt2 \
  --device cpu --mode aotinductor --target ase
```

```python
from ase.io import read
from nequip.integrations.ase import NequIPCalculator

atoms = read("structure.extxyz")
atoms.calc = NequIPCalculator.from_compiled_model(
    compile_path="model.nequip.pt2",
    device="cpu",
)
print(atoms.get_potential_energy())
print(atoms.get_forces())
```

用训练时见过的构型和独立构型各测几帧。比较前对齐元素次序、晶胞、坐标精度、单位、力排序和计算精度。应力只在两端均能按同一约定输出时对照。

## 二、把同一构型送到 LAMMPS

按目标插件和模型架构选择编译目标。NequIP 与 Allegro 的 LAMMPS 集成分别核对该版本的 pair style、模型格式与进程支持。先用一个进程、同一个周期结构执行 `run 0`，导出原子 ID 和力，再按转换时保存的原子 ID 对齐 ASE。若总能量接近但力逐行对不上，先检查 ID、类型映射和坐标精度。LAMMPS 可能将晶胞转换成限制三斜表示，对照时需把力分量转回同一坐标基底。若两端预测彼此吻合、却同样偏离 DFT，就回到[模型评估](NequIP训练数据与误差评估.md)检查数据和适用范围。通过后做短程 NVE 与步长检查，最后再测并行规模。遗留 `nequip-deploy` 模型按对应旧版文档走完整套流程。

参考 [NequIP ASE 集成](https://nequip.readthedocs.io/en/latest/integrations/ase.html)与[训练、打包及编译工作流](https://nequip.readthedocs.io/en/latest/guide/getting-started/workflow.html)。

LAMMPS 的编译目标、模型格式和执行约束见 [pair_nequip_allegro 接口说明](https://github.com/mir-group/pair_nequip_allegro)。
