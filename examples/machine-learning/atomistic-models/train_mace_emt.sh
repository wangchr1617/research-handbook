#!/usr/bin/env bash
# 在已激活案例 Python 环境中运行：bash train_mace_emt.sh。
# 参考标签为 ASE EMT；先训练，再重新加载模型核对推理。
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
python make_emt_dataset.py
mace_run_train --name=Cu_EMT_fit --model=MACE \
  --train_file=results/cu_train.extxyz --valid_file=results/cu_valid.extxyz \
  --energy_key=REF_energy --forces_key=REF_forces --E0s=average \
  --r_max=4.0 --num_interactions=2 --hidden_irreps='8x0e + 8x1o' \
  --correlation=2 --batch_size=4 --max_num_epochs=100 \
  --energy_weight=10 --forces_weight=100 --lr=0.005 \
  --device=cpu --default_dtype=float64 \
  --model_dir=results/models --checkpoints_dir=results/checkpoints \
  --log_dir=results/logs --results_dir=results/metrics
python predict_trained.py
