# QE 声子谱计算

**适用环境：Linux（Quantum ESPRESSO）。**

想判断硅的低频异常来自结构、数值误差还是简谐不稳定，可以先查 Γ 点，再算规则 q 网格并插值得到色散。每个阶段保留自己的输出，才能沿异常频率回查动力学矩阵和电子基态。

## 一、先优化 Si 结构

声子频率对结构和数值精度敏感。先充分优化结构，再进行后续计算，有助于减少由残余受力和数值误差引起的虚频。

```text
&CONTROL
 calculation = 'vc-relax'
 verbosity = 'high'
 nstep = 100
 tstress = .true.
 tprnfor = .true.
 outdir = './outdir'
 prefix = 'Si'
 etot_conv_thr = 1.0d-7
 forc_conv_thr = 1.0d-5
 disk_io = 'low'
 pseudo_dir = '/home/your-user/UPF/SSSP/'
/
&SYSTEM
 ibrav = 2
 celldm(1) = 10.410909236
 nat = 2
 ntyp = 1
 nbnd = 8
 ecutwfc = 50.0
 ecutrho = 200.0
 occupations = 'fixed'
/
&ELECTRONS
 electron_maxstep = 300
 scf_must_converge = .true.
 conv_thr = 1.0d-9
 mixing_mode = 'plain'
 mixing_beta = 0.8d0
 diagonalization = 'david'
/
&IONS
 ion_dynamics = 'bfgs'
 trust_radius_min = 1.0d-3
 trust_radius_ini = 0.5d0
/
&CELL
 cell_dynamics = 'bfgs'
 press = 0.0
 press_conv_thr = 0.1
 cell_dofree = 'all'
/
ATOMIC_SPECIES
 Si  28.0855  Si.pbe-n-rrkjus_psl.1.0.0.UPF
ATOMIC_POSITIONS (alat)
 Si 0.00 0.00 0.00
 Si 0.25 0.25 0.25
K_POINTS (automatic)
  12 12 12 0 0 0
```

运行 `pw.x < 1_vc_relax.inp > 1_vc_relax.out` 即可。

计算结束后，提取最终晶胞与坐标：

```text
awk '/Begin final coordinates/,/End final coordinates/{print $0}' output
```

其中 `output` 替换为本次运行的输出文件名 `1_vc_relax.out`。

## 二、自洽计算

用优化后的结构进行静态自洽计算，为声子任务准备电子态。将最终晶胞与坐标写入 `2_scf.inp`，把 `calculation = 'vc-relax'` 改为 `calculation = 'scf'`，再运行 `pw.x < 2_scf.inp > 2_scf.out`。静态输入可以移除 `&IONS` 和 `&CELL`。若直接复制末态的三个晶格向量，设置 `ibrav=0`、删除旧的 `celldm(1)`，并保留末态晶格与坐标卡片的单位。计算完成后确认电子收敛，并核对 `ph.x` 将读取同一 `outdir` 和 `prefix` 下的 `Si.save`。

## 三、声子计算

自洽完成后，用 `ph.x` 计算倒空间中的动力学矩阵。可以先计算单个 q 点，再扩展到规则 q 网格；这部分通常是流程中耗时较多的步骤。

### 单个 q 点的计算

```text
phonons of Si at Gamma
 &INPUTPH
  amass(1) = 28.0855
  outdir = './outdir'
  prefix = 'Si'
  tr2_ph = 1.0d-14
  fildyn = 'Si.dynG'
  epsil = .true.
 /
0.0 0.0 0.0
```

将该输入保存为 `ph_gamma.in`，执行 `ph.x -in ph_gamma.in > ph_gamma.out`，核对 Γ 点频率和各扰动的收敛。单点用于诊断。

### 声子色散计算

```text
phonons of Si q-grid
 &INPUTPH
  amass(1) = 28.0855
  outdir = './outdir'
  prefix = 'Si'
  tr2_ph = 1.0d-12
  fildyn = 'Si444.dyn'
  ldisp = .true.
  nq1 = 4
  nq2 = 4
  nq3 = 4
 /
```

将规则网格输入另存为 `ph_grid.in`，执行 `ph.x -in ph_grid.in > ph_grid.out`。确认网格的动力学矩阵文件齐全，再用 `q2r.x`。

## 四、后处理

规则 q 网格计算完成后，`q2r.x` 读取 `ph.x` 生成的 C(q)，通过傅里叶变换得到实空间原子间力常数 C(R)。随后由 `matdyn.x` 利用这些力常数计算所需路径上的声子频率。

输入 `q2r.inp` 如下，再运行 `q2r.x < 4_q2r.inp > 4_q2r.out` 即可。

```text
&INPUT
   fildyn = 'Si444.dyn'
   flfrc = 'Si444.fc'
   zasr = 'crystal'
 /
```

在输出文件 `4_q2r.out` 中需要有以下内容：

```text
fft-check success (sum of imaginary terms < 10^-12)
```

将以下内容保存为 `5_matdyn.inp`，运行 `matdyn.x < 5_matdyn.inp > 5_matdyn.out`，计算指定路径上的声子频率。

```text
&INPUT
  flfrc = 'Si444.fc'
  asr = 'crystal'
  flfrq = 'Si.freq'
  q_in_band_form = .true.
  q_in_cryst_coord = .false.
/
5
  0.00 0.00 0.00 30
  0.00 1.00 0.00 30
  0.50 1.00 0.00 30
  0.75 0.75 0.00 30
  0.00 0.00 0.00 1
```

这条 Γ—X—W—K—Γ 路径使用常规立方轴的笛卡尔坐标，单位为 $2\pi/a$。如果静态输入改用了显式晶格，应先按该任务实际的 `alat` 和坐标朝向换算路径，或改用分数倒易坐标。FFT 检查只能验证傅里叶变换本身；画图前还需查看 Γ 附近的声学支与虚频，并通过提高电子网格和 q 网格精度来判断异常的来源，相关参数见 [matdyn.x 输入手册](https://www.quantum-espresso.org/Doc/INPUT_MATDYN.html)。

最后，使用 `plotband.x` 来处理输出的声子频率文件。
将以下内容保存为 `6_plotband.inp` 文件，然后运行 `plotband.x < 6_plotband.inp > 6_plotband.out`，生成的 `freq.plot` 文件可以直接导入 Origin 做图。

```text
Si.freq
-100 600
freq.plot
freq.ps
0.0
50.0 0.0
```
