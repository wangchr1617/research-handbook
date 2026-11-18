# CASTEP 声子与振动热力学

优化过的硅原胞在 Γ 点有三个接近零的平移模。若还想知道离开 Γ 后是否出现软模，就要在更多 q 点检查色散；若关心热容，则应改用规则网格积分。下面沿同一个 Si 原胞走这三步。

## 一、从 Γ 点检查扩展到声子色散

把优化后的 Si 原胞复制到声子目录。保留原有的电子 k 网格，另外在 `.cell` 加一个声子 q 点。前三列是倒格矢分数坐标，第四列是权重。

```text
%BLOCK PHONON_KPOINT_LIST
0.0 0.0 0.0 1.0
%ENDBLOCK PHONON_KPOINT_LIST
```

在 `.param` 中设置 `TASK : PHONON` 与 `PHONON_METHOD : DFPT`，核对当前版本对赝势和泛函的支持，再执行 `castep si`。检查 `si.phonon` 的单位和频率。两个原子的 Si 原胞在 Γ 点有 6 个模式，其中三个声学模趋于零。若用极性晶体练习，在 Γ 附近处理非解析长程修正，记录接近 Γ 的方向、Born 有效电荷和高频介电张量。

从 Γ 点单点切换到色散时，将 `.cell` 中的 `PHONON_KPOINT_LIST` 块换成 `PHONON_KPOINT_MP_GRID`，选用包含 Γ 的粗 q 网格。在 `.param` 中加 `PHONON_FINE_METHOD : INTERPOLATE`，再用 `.cell` 中的 `PHONON_FINE_KPOINT_PATH` 块定义插值路径。沿路径加点是在已有力常数上加密插值。若软模位置或频率对用于求力常数的粗网格敏感，应重新计算粗网格，再比较同一条插值路径。若用 `PHONON_METHOD : FINITEDISPLACEMENT`，检查超胞尺寸、位移量和受力噪声，比较低频支与异常软模。

Γ 附近的极小虚频先排查结构残余力、网格和声学和规则。若虚频在加密后仍存在，可沿对应本征矢扰动并弛豫，比较能量和对称性。

## 二、用规则 q 网格积分热容

从色散转向热容时，保留已收敛的粗网格设置，把细采样由路径切换为 `PHONON_FINE_KPOINT_MP_GRID` 指定的规则网格。加密这套积分网格，比较温度范围内的热容变化。若声子态密度按原胞的模式数归一化，积分应为 $3N$，本例为 6。读热容前再核对输出按原胞、原子还是化学式归一化。可沿用仓库[硅简谐热容案例](../VASP/振动与热力学/VASP热容计算.md)的读图检查，在同一归一化下比较低温趋势和高温 $6R$ 极限。对动力学稳定的结构，可得到零点能、振动自由能和定容热容。热膨胀需要比较多个体积下的自由能；热导率还需声子散射或其他输运模型。若有明显虚频，普通简谐自由能不适合直接用于相稳定性比较。

输入与后处理见 [CASTEP 声子教程](https://castep-docs.github.io/castep-docs/documentation/Phonons/Castep_Phonons/Running-phonon-calculations/)、[官方课程](https://castep-docs.github.io/workshop/workshop/05_phonon/)和[振动光谱说明](https://www.castep.org/features/capabilities/vibrational-spectroscopy)。
