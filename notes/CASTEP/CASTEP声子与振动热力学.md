# CASTEP 声子与振动热力学

先优化结构并收敛力和应力，再计算振动。Γ 点给出长波极限下的模式，可以检查红外、Raman 或结构软模。声子色散、态密度和热容需要处理整个布里渊区。

## 从 Γ 点到色散

把优化后的 Si 原胞复制到声子目录。保留原有的电子 k 网格，另外在 `.cell` 加一个声子 q 点。前三列是倒格矢分数坐标，第四列是权重。

```text
%BLOCK PHONON_KPOINT_LIST
0.0 0.0 0.0 1.0
%ENDBLOCK PHONON_KPOINT_LIST
```

在 `.param` 中设置 `TASK : PHONON` 与 `PHONON_METHOD : DFPT`，核对当前版本对赝势和泛函的支持，再执行 `castep si`。检查 `si.phonon` 的单位和频率。两个原子的 Si 原胞在 Γ 点有 6 个模式，其中三个声学模趋于零。若用极性晶体练习，在 Γ 附近处理非解析长程修正，记录接近 Γ 的方向、Born 有效电荷和高频介电张量。

对色散，用 `PHONON_KPOINT_MP_GRID` 和包含 Γ 的粗 q 网格计算动力学矩阵，再用 `PHONON_FINE_KPOINT_PATH` 指定插值路径。路径点越多，曲线越平滑，力常数的精度仍需靠加密粗网格检验。若用 `PHONON_METHOD : FINITEDISPLACEMENT`，检查超胞尺寸、位移量和受力噪声，比较低频支与异常软模。

Γ 附近的极小虚频先排查结构残余力、网格和声学和规则。若虚频在加密后仍存在，可沿对应本征矢扰动并弛豫，比较能量和对称性。

## 从声子态密度到热容

用密 q 网格积分，按原胞归一化时，声子态密度积分应为 $3N$。对动力学稳定的结构，可得到零点能、振动自由能和定容热容。热膨胀需要比较多个体积下的自由能；热导率还需声子散射或其他输运模型。若有明显虚频，普通简谐自由能不适合直接用于相稳定性比较。

输入与后处理见 [CASTEP 声子教程](https://castep-docs.github.io/castep-docs/documentation/Phonons/Castep_Phonons/Running-phonon-calculations/)、[官方课程](https://castep-docs.github.io/workshop/workshop/05_phonon/)和[振动光谱说明](https://www.castep.org/features/capabilities/vibrational-spectroscopy)。
