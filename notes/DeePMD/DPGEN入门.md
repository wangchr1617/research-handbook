# DPGEN 入门

**适用环境：Linux 集群。**

DPGEN 将势函数训练、构型探索和第一性原理标记组织成迭代流程。本文保留集群 3 上的安装和 GeTe 配置示例，重点区分“算什么”与“在哪里算”这两类设置。

## DPGEN 在集群 3 的安装

本例使用 DPGEN 0.10.6 离线安装包。上传到集群并赋予可执行权限后，运行 `./dpgen-0.10.6-Linux-x86_64.sh`，安装方式与 DeePMD-kit 类似。

安装完成后，使用命令 `conda activate dpgen` 加载环境。
如果找不到 `libffi.so.7`，`cd /home/changruiwang-ICME/Software/dpgen/lib` 目录，检查有没有 `libffi.so.7`。
如果没有，使用命令 `ln -s libffi.so.6 libffi.so.7` 创建一个链接即可。
注意，集群 3 由于 PBS 队列系统版本原因，需要 `vi dpgen/lib/python3.8/site-packages/dpdispatcher/pbs.py` 并修改下列变量为：

```python
pbs_script_header_dict['select_node_line'] = "#PBS -l nodes={number_node}:ppn={cpu_per_node}".format(number_node = resources.number_node, cpu_per_node = resources.cpu_per_node)
status_word = stdout.read().decode('utf-8').split('<job_state>')[-1].split('</job_state>')[0]
```

## DPGEN 的基本任务流程

常见任务有 `init_bulk`、`init_surf`、`run` 和 `test`。先用 `dpgen -h` 查看任务列表，再用 `dpgen run -h` 等命令查看具体用法。

例如，`nohup dpgen init_bulk param.json machine.json 1>log 2>err &` 在后台执行 `init_bulk`，`nohup dpgen run param.json machine.json 1>log 2>err &` 则启动 `run`。记录返回的进程号，并用 `ps -ux` 查看运行情况。

### 两个 JSON 文件分别管什么

`param.json` 定义执行什么计算，例如体系、训练设置和探索条件；`machine.json` 定义运行环境、程序路径和资源。本例从存放 `machine.json` 的主目录启动任务。

<div align="left">
<img alt="DPGEN 入门示例图" src="assets/dp-002.png" width="50%" />
</div>

以常用的 `run` 为例，每次迭代涉及训练、探索和标记，对应 `machine.json` 中的 `train`、`model_devi` 和 `fp`。三个部分分别配置各自的程序与计算环境，因此训练和第一性原理标记可以使用不同资源。示例如下：

```json
{
"api_version": "1.0",
   	"deepmd_version": "2.2.7",
   	"train" : [{
     	"command": "/home/changruiwang-ICME/Software/deepmd-gpu/bin/dp",
      	"machine": {
         	"batch_type": "PBS",
           	"local_root" : "./",
          	"remote_root": "/home/changruiwang-ICME/dpgen_work/dpgen_run",
         	"context_type": "LocalContext"
    	},
     	"resources": {
          	"number_node": 1,
           	"cpu_per_node": 32,
         	"gpu_per_node": 2,
         	"queue_name": "gpu",
           	"group_size": 1,
          	"custom_flags": [
             	"#PBS -N deepmd",
               	"#PBS -l walltime=144:00:00",
               	"#PBS -S /bin/bash",
               	"#PBS -V"
        	],
         	"source_list": [
           		"/home/changruiwang-ICME/script/dpgen_source/dpmd.sh"
        	],
       		"envs": {
               	"CUDA_VISIBLE_DEVICES": "0,1",
             	"OMP_NUM_THREADS": "16"
         	}
  		}
}],
 	"model_devi": [{
     	"command": "/home/changruiwang-ICME/Software/deepmd-gpu/bin/lmp",
    	"machine": {
         	"batch_type": "PBS",
        	"local_root" : "./",
          	"remote_root": "/home/changruiwang-ICME/dpgen_work/dpgen_run",
        	"context_type": "LocalContext"
     	},
      	"resources": {
       		"number_node": 1,
          	"cpu_per_node": 32,
           	"gpu_per_node": 2,
           	"queue_name": "gpu",
        	"group_size": 8,
          	"custom_flags": [
              	"#PBS -N lammps",
               	"#PBS -l walltime=144:00:00",
             	"#PBS -S /bin/bash",
             	"#PBS -V"
          	],
         	"source_list": [
           		"/home/changruiwang-ICME/script/dpgen_source/lmp.sh"
 			],
          	"envs": {
             	"CUDA_VISIBLE_DEVICES": "0,1",
            	"OMP_NUM_THREADS": "8",
             	"LAMMPS_PLUGIN_PATH": "/home/changruiwang-ICME/Software/deepmd-gpu/lib/deepmd_lmp"
        	}
  		}
}],
  	"fp": [{
     	"command": "mpirun -np 24 /opt/software/vasp/vasp6.4.0/bin/vasp_gam",
     	"machine": {
        	"batch_type": "PBS",
         	"local_root" : "./",
       		"remote_root": "/home/changruiwang-ICME/dpgen_work/dpgen_run",
        	"context_type": "LocalContext"
     	},
    	"resources": {
         	"number_node": 1,
           	"cpu_per_node": 24,
         	"gpu_per_node": 0,
        	"queue_name": "manycores",
        	"group_size": 8,
        	"custom_flags": [
               	"#PBS -N vasp",
            	"#PBS -l walltime=600:00:00",
               	"#PBS -S /bin/bash",
              	"#PBS -V"
        	],
        	"source_list": [
              	"/home/changruiwang-ICME/script/dpgen_source/vasp.sh"
         	]
    	}
}]
}
```

下面的 `param.json` 与之配套，定义 GeTe 数据、模型和探索任务：

```json
{
 	"type_map": ["Ge","Te"],
  	"mass_map": [72.64,127.6],
   	"init_data_prefix": "./",
   	"init_data_sys": ["train/Ge64Te64/"],
   	"sys_configs_prefix": "./",
   	"sys_configs": [
   		["init/perturb/*/POSCAR"],
     	["init/scale_0.96/*/POSCAR"],
      	["init/scale_1.04/*/POSCAR"]
 	],
  	"numb_models": 4,
  	"_training_init_frozen_model": [
     	["./init_model/000/frozen_model.pb"],
      	["./init_model/001/frozen_model.pb"],
      	["./init_model/002/frozen_model.pb"],
      	["./init_model/003/frozen_model.pb"]
  	],
  	"model_devi_activation_func": [
["tanh","tanh"],
["tanh","gelu"],
["gelu","tanh"],
["gelu","gelu"]
],
  	"default_training_param": {
      	"model": {
         	"type_map": ["Ge","Te"],
          	"descriptor": {
          		"type": "se_e2_a",
          		"sel": [100,100],
          		"rcut_smth": 2.0,
           		"rcut": 6.0,
           		"neuron": [25,50,100],
          		"resnet_dt": false,
          		"type_one_side": true,
         		"axis_neuron": 12,
           		"seed": 1
    		},
      		"fitting_net": {
          		"neuron": [240,240,240],
          		"resnet_dt": true,
          		"seed": 1
      		}
 		},
  		"learning_rate": {
     		"type": "exp",
     		"start_lr": 0.001,
      		"decay_steps": 4000
   		},
  		"loss": {
     		"start_pref_e": 0.02,
     		"limit_pref_e": 1,
       		"start_pref_f": 1000,
      		"limit_pref_f": 1,
      		"start_pref_v": 0.0,
       		"limit_pref_v": 0.0
  		},
  		"training": {
     		"stop_batch": 100000,
       		"disp_file": "lcurve.out",
      		"disp_freq": 2000,
       		"numb_test": 4,
      		"save_freq": 2000,
       		"save_ckpt": "model.ckpt",
      		"disp_training": true,
       		"time_training": true,
     		"profiling": false,
   			"profiling_file": "timeline.json"
  		}
},
"model_devi_engine": "lammps",
"model_devi_dt": 0.002,
"model_devi_skip": 0,
"model_devi_f_trust_lo": 0.05,
"model_devi_f_trust_hi": 0.15,
"model_devi_clean_traj": 1,
"model_devi_jobs": [
  		{"sys_idx": [0],"temps": [300, 450, 600, 750, 900],"press": [1.0, 100.0], "trj_freq":   5, "nsteps":   1000, "ensemble": "npt", "_idx":     "00" },
  		{"sys_idx": [1],"temps": [300, 450, 600, 750, 900],"press": [1.0, 100.0], "trj_freq":   5, "nsteps":   1000, "ensemble": "npt", "_idx":     "01" },
  		{"sys_idx": [2],"temps": [300, 450, 600, 750, 900],"press": [1.0, 100.0], "trj_freq":   5, "nsteps":   1000, "ensemble": "npt", "_idx":     "02" },
  		{"sys_idx": [0],"temps": [300, 450, 600, 750, 900],"press": [1.0, 100.0], "trj_freq":  50, "nsteps":  10000, "ensemble": "npt", "_idx":     "03" },
 		{"sys_idx": [1],"temps": [300, 450, 600, 750, 900],"press": [1.0, 100.0], "trj_freq":  50, "nsteps":  10000, "ensemble": "npt", "_idx":     "04" },
  		{"sys_idx": [2],"temps": [300, 450, 600, 750, 900],"press": [1.0, 100.0], "trj_freq":  50, "nsteps":  10000, "ensemble": "npt", "_idx":     "05" },
  		{"sys_idx": [0],"temps": [300, 450, 600, 750, 900],"press": [1.0, 100.0], "trj_freq": 500, "nsteps": 100000, "ensemble": "npt", "_idx":     "06" },
      	{"sys_idx": [1],"temps": [300, 450, 600, 750, 900],"press": [1.0, 100.0], "trj_freq": 500, "nsteps": 100000, "ensemble": "npt", "_idx":     "07" },
      	{"sys_idx": [2],"temps": [300, 450, 600, 750, 900],"press": [1.0, 100.0], "trj_freq": 500, "nsteps": 100000, "ensemble": "npt", "_idx":     "08" }
  	],
   	"fp_style": "vasp",
  	"fp_pp_path": "./",
   	"fp_pp_files": ["POTCAR_Ge","POTCAR_Te"],
  	"fp_incar": "./INCAR",
  	"fp_accurate_threshold": 0.999,
  	"fp_accurate_soft_threshold": 0.99,
   	"shuffle_poscar": false,
  	"fp_task_max": 50,
  	"fp_task_min": 3,
   	"ratio_failed": 0.05
}
```

### 使用自己的 LAMMPS 模板

在 `model_devi_jobs` 下设置 `template` 时，探索步骤使用指定的 `lmp/input.lammps` 模板：

```text
"model_devi_jobs":  [{
  	"sys_idx": [0],"traj_freq": 10,"_idx": "00",
      	"template":{"lmp": "lmp/input.lammps"},
       	"rev_mat":{
"lmp": {"V_NSTEPS": [20000], "V_TEMP": [300], "V_PRES": [1]},
          	"plm": {"V_TEMP":  [300], "V_STRIDE": [10]}
      	}}, …… ]
```

模板中的 `dump` 行需使用 `dump dpgen_dump`。在这一模式下，DPGEN 调用 `revise_lmp_input_dump` 写入 `trj_freq`，与在文件开头定义并引用 `DUMP_FREQ` 的方式不同。

### 迭代过程与恢复

`run` 主流程可进一步拆成图中的 9 步：

<div align="left">
<img alt="DPGEN 入门示例图" src="assets/dp-003.png" width="50%" />
</div>

假设最后一个迭代的候选构型数小于 `fp_task_min` 时，那该轮迭代实际上并没有进行新的 `00.train/`，而是软链接到前一轮迭代的 `00.train/`。
如果任务异常退出需要重启，删除 `record.dpgen` 最后一行并重新键入前述命令即可。

## 标记精度与模型偏差阈值

用 VASP 标记 DPGEN 构型时，同样需要测试 `ENCUT` 和 `KSPACING` 的收敛。
通过 MP 下载的晶体结构，可以先做晶胞微扰后再测试，目的是增大原子受力区分度。
收敛标准是以渐进收敛线（或最高精度值）为参考，取相对波动小于一定范围的参数。
一般而言，`ENCUT` 和 `KSPACING` 收敛测试的相对能量偏差小于 `1E-3 eV/atom`，
力和位力偏差小于 `1E-2 eV/Angstrom` 和 `1E-2 eV/atom` 即可。
此外，DPGEN 还需要通过测试来确定两个关键参数 `model_devi_f_trust_lo` 和 `model_devi_f_trust_hi` 的取值。
具体的做法是先做一轮 run 迭代，模拟中采样构型的模型力偏差可以在 `iter.00000*/01.model_devi/task*/model_devi.out` 查看。
使用 [collect_dpgen_deviations.py](../../scripts/deepmd/collect_dpgen_deviations.py) 收集 `model_devi.out` 的最大力偏差并输出 CSV。需要比较不同温度时，应依据来源目录和实际任务配置分组，不可将同一批数据重复标注为不同温度。分布图示例如下：

<div align="left">
<img alt="DPGEN 入门示例图" src="assets/dp-004.png" width="50%" />
</div>

图（a）中最大偏差力分布的峰值在 `0.15 eV/Angstrom` 左右。
一则说明该训练模型没有收敛，精度不够；二则说明力偏差判据下、上界取 `0.15` 和 `0.35` 是比较合适的。
另一种经验做法是，判据的下界略高于训练误差，而上界则在此基础上再增加 `0.1~0.3 eV/Angstrom` 左右。

## 训练集收集

迭代生成的数据分散在各轮目录中，可用 `dpgen collect` 汇总。先用 `dpgen collect -h` 查看说明，命令格式为 `dpgen collect JOB_DIR OUTPUT_DIR -p param.json`。其中 `JOB_DIR` 是包含 `iter.0000*` 的任务目录，`OUTPUT_DIR` 是收集后的目标目录。例如：

```bash
dpgen collect ./ ./collect -p param.json
```

上述命令会把当前文件夹下的数据收集到 `collect` 目录里。
`collect` 目录中，`init.*` 是初始训练集，`sys.*` 是 DPGEN 生成的训练集（按照 `param.json` 中的 `sys` 分类）。
最后，使用命令 `python deepmd_to_xyz.py collect/sys.000/` 即可将 DP 数据转成 `.xyz` 格式。
