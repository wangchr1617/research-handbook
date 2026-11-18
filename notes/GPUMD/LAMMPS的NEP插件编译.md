# NEP-LAMMPS 编译

已有 LAMMPS 的结构、边界和后处理输入时，可以用 NEP_CPU 提供的 `pair_style nep` 接进原工作流。上游 LAMMPS 接口支持单隐藏层的 NEP 势及其 ZBL 变体，qNEP、偶极和极化率模型超出该接口的支持范围。选接口前先读模型文件头，再核对随所选提交发布的说明。 [NEP_CPU 接口说明](https://github.com/brucefan1983/NEP_CPU#lammps-interface)

## 一、按同一条构建路线接入 USER-NEP

先固定 LAMMPS 与 NEP_CPU 的版本或提交。按上游 CMake 路线，在两个源码目录的共同父目录执行以下复制步骤。若检出版本的目录结构不同，以该版本说明为准。

```bash
cp NEP_CPU/src/* NEP_CPU/interface/lammps/USER-NEP/
cp -R NEP_CPU/interface/lammps/USER-NEP lammps/src/
cp NEP_CPU/interface/lammps/USER-NEP.cmake lammps/cmake/Modules/Packages/
```

按上游构建说明，在 `lammps/cmake/CMakeLists.txt` 的 `STANDARD_PACKAGES` 与 `PKG_WITH_INCL` 列表中加入 `USER-NEP`，然后从共同父目录配置并构建。若选择传统 Make 路线，则按上游说明在 `lammps/src/` 中启用 `make yes-USER-NEP` 并使用对应的机器目标构建。 [NEP_CPU 构建说明](https://github.com/brucefan1983/NEP_CPU#build-1)

```bash
cmake -S lammps/cmake -B lammps/build -DCMAKE_BUILD_TYPE=Release -DPKG_USER-NEP=ON
cmake --build lammps/build --parallel 4
lammps/build/lmp -help
```

检查帮助输出的 pair style 列表中是否出现 `nep`。若没有，先确认调用的是刚编译的二进制，再查 CMake 是否识别并启用了 `USER-NEP`。

## 二、用同一个 GeTe 构型核对元素映射

仓库 [GeTe 示例](../../examples/gpumd/nep-phonons/)的 POSCAR 按 Ge、Te 列出元素，而势文件头的顺序是 Te、Ge。假如转换后的 LAMMPS 数据文件把 1 号类型指定为 Ge、2 号类型指定为 Te，读取结构后应按数据文件的类型顺序写映射。

```text
pair_style nep
pair_coeff * * nep_generation500000.txt Ge Te
run 0
```

完整输入还需在读结构前设置 `units metal` 和合适的 `atom_style`，把势文件放到输入指定的位置。先运行零步计算，按同一原子顺序和晶胞比较 LAMMPS 与 GPUMD 或 NEP_CPU 的势能及逐原子受力。如果差异超出预期，先查类型映射、单位、周期盒与坐标变换。单进程对照通过后，再增加 MPI 进程并比较结果和吞吐。
