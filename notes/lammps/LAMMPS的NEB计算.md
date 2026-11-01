# LAMMPS NEB 计算

**适用环境：Linux（NEB 多副本计算）。**

## 命令

### fix neb

向不同副本点添加 nudging force 来寻找过渡态。通过弹簧力使不同点之间尽可能保持相同的距离。该命令产生的力会在 neb 的 minimization 中施加。

`fix ID group-ID neb Kspring keyword value`

- Kspring：弹簧系数（单位根据 parallel 的值确定）
- parallel：如何计算 nudging force，即 $F_{\|}$
  - neigh：通过前后相邻两个 replica 之间的距离计算，$F_{\|}=K \text { spring } \cdot\left(\left|R_{i+1}-R_i\right|-\left|R_i-R_{i-1}\right|\right)$，单位是 force/distance。(default)
  - ideal：根据目前位置(reaction coordinate)与理想位置之间的偏差来计算力
  - equal：在 climbing 之前（即下面的 NEB 第一步）用 ideal 方式计算，保证距离相等；climbing 时通过能量差来计算力。
- perp Kspring2：垂直于路径方向的 nudging force 弹簧常数，$F_{\perp}=K_{\text {spring } 2} \cdot F\left(R_{i-1}, R_i, R_{i+1}\right)\left(R_{i+1}+R_{i-1}-2 R_i\right)$。$F\left(R_{i-1}, R_i, R_{i+1}\right)$ 是与三点夹角有关的函数，当三点一线时为 0，当成锐角时为 1。default=0。
- end：设置作用在第一个和最后一个 replica 上的力，**默认这两个 replica 不受额外的力**。这个关键字可以使用两次，分别向 first 和 last 添加力
  - estyle：
    - first：向 first replica 施加力，*ETarget* is set to the initial energy of the replica
    - last：向 last replica 施加力，*ETarget* is set to the initial energy of the replica
    - last/efirst：向 last replica 施加力，并且设置其 target energy 为 first replica 的能量
    - last/efirst/middle：与 last/efirst 相同，加上防止 middle replica 的能量低于 first replica


### neb

`neb etol ftol N1 N2 Nevery file-style arg keywords values`

- etol：能量收敛条件，每个 replica 都要达到收敛标准，这里的能量计算不包括 replica 之间的 nudging forces 贡献
- ftol：力收敛条件，每个 replica 都要达到收敛标准，这里的力计算包括 replica 之间的 nudging forces 贡献
- N1：运行初始 NEB 的最大步长
- N2：运行 barrier-climbing NEB 的最大步长
- Nevery：在两个阶段中，每隔 Nevery 时间步，每个 replica 的势能及其沿反应路径的归一化距离(反应坐标 RD)将被输出到主日志 `log.lammps` 文件中。N1 和 N2 都必须为 Nevery 的倍数。
- file-style：
  - final：需要存在指定的文件，文件中指定 NEB atom 或 group 最终的坐标。NEB 计算时以这个作为 last replica，middle replica 的初始位置通过 first replica 和 last replica 插值得到。
  - each：为每个 replica 指定单独的坐标文件，文件名可以使用变量。除了 first replica 外都会读取对应的文件。**这种方法对扩散路径应该会控制的更好，但很麻烦。**
  - nono：不指定文件，但是需要通过 read_data，read_restart 或 read_dump 这些命令来读取结构作为 replica
- verbosity：设置输出主日志 `log.lammps` 的输出信息，不影响分区日志。每隔 Nevery 输出一次
  - terse：timestep, the maximum force of a replica, the maximum force per atom (in any replica), potential gradients in the initial, final, and climbing replicas, the forward and backward energy barriers, the total reaction coordinate (RDT).
  - default：除了 terse 中的还额外输出反应坐标和每个 replica 的势能
  - verbose：额外输出一些每个 replica 的信息，梯度之类的

```text
neb 0.1 0.0 1000 500 50 final coords.final
neb 0.0 0.001 1000 500 50 each coords.initial.$i				# each要用变量文件名
neb 0.0 0.001 1000 500 50 none verbose
```

NEB 计算时，时间步长设大一些会更快的收敛（正常的 10 倍）。

`fix neb` 和 `neb` 两个命令需要联用。

## 原理

NEB 计算分为两步，每一步都是一个 minimization 过程：

> 注意这时需要通过 `min_style` 指定 minimize 算法，用 quickmin 或 fire；不能用 cg/sd/hftn，因为这些算法在内部进行迭代，不能进行不同 replicas 之间的同步。

### 第一步

initial NEB

首先，n 个 replicas 朝着最小能量路径（minimum energy path，MEP）弛豫直到收敛，这时的能量收敛指的是所有 replicas 中的能量都达到收敛标准。

这个阶段先优化整体路径形状，不精确定位路径上的最高能量点（鞍点）。

### 第二步

在初始路径被优化之后，第二阶段是**climbing image NEB**，它精细化路径以更准确地定位鞍点，鞍点对应于 MEP 上的最高能态。

将能量最高的 replica 设置为鞍点，然后将作用在该 replica 上的力修改为驱动其到势垒顶部的力（这个力方向沿着切线斜向上，拉着该点爬升）。其他 replica 位置也会重新分布以保证间距相等。

每个 replica 的力通过下面的公式计算：
$$
F_i=-\nabla V+\left(\nabla V \cdot T^{\prime}\right) T^{\prime}+F_{\|}+F_{\perp}
$$
- $-\nabla V$：未进行 NEB 计算之前 N 个 replica 之间的相互作用力
- $\nabla V \cdot T^{\prime}$：消除平行于路径的梯度分量，因为沿着路径的力会使得点之间分布不均匀
- $F_{\|}$：在切线方向人为施加的 nudging force，为了保证不同 replicas 之间距离相等
- $F_{\perp}$：在垂直于切线方向施加的 nudging force，防止路径形成尖锐的扭折
- $T^{\prime}$：在第 i 个 replica 处的单位切向量

在 NEB 计算的第二阶段，将能量最高的 replica 的力修改为：
$$
F_i=-\nabla V+2\left(\nabla V \cdot T^{\prime}\right) T^{\prime}+F_{\perp}
$$
然后进行弛豫过程。

## 注意事项

1. 必须用 [atom_modify map](https://docs.lammps.org/atom_modify.html) 命令定义原子映射，因为对于 `atom_style atomic` 原子类型映射不是默认的。
2. The damped dynamics [minimizers](https://docs.lammps.org/min_style.html), such as *quickmin* and *fire*), adjust the position and velocity of the atoms via an Euler integration step. Thus you must define an appropriate [timestep](https://docs.lammps.org/timestep.html) to use with NEB. As mentioned above, NEB will often converge more quickly if you use a timestep about 10x larger than you would normally use for dynamics simulations.
3. 下方是输入的 replica 文件格式，原子 ID 顺序无所谓

```text
7
174  6.86775 9.49992 9.62069
175  9.46441 6.90709 9.62317
301  6.87004 6.90631 12.2171
304  8.44266 8.48312 11.1965
306  10.5121 8.48457 13.2624
331  8.44223 10.5435 13.2633
337  10.5124 10.5437 11.1959
```

4. 不要求 replica 文件中的原子与 fix NEB 命令定义的组中的 NEB 原子相对应，不是每个 NEB 原子都需要在输入文件中，并且非 NEB 原子也可以在文件中列出。
5. 如果输入脚本中的 `dump` 命令定义了一个包含*universe*或*uloop*样式 `variable` 的文件名，那么将为每个副本创建一个 dump 文件(每个转储命令)。

## Python 脚本

`neb_combine.py`：从各 replica 的 dump 文件中提取 NEB 原子，再与第一个 replica 的非 NEB 原子合并为一个 dump 文件。

`neb_final.py`：从各 replica 的 dump 文件中提取最后一帧，合并为一个 dump 文件。
