#!/usr/bin/env bash
# 从仓库任意位置运行材料案例；只选择已有 Python 环境，不安装依赖。
# 用法：bash scripts/materials/run_local.sh metal --output /tmp/al-case
set -euo pipefail
project_root="$(cd "$(dirname "$0")/../.." && pwd)"
if [[ -n "${MATERIALS_PYTHON:-}" ]]; then
  candidate_python="$MATERIALS_PYTHON"
else
  candidate_python=""
  for entry in "$project_root/.venv/bin/python" "$project_root/_validation_runs/vasp-cp2k/venv/bin/python" "$(command -v python3 || true)"; do
    if [[ -x "$entry" ]] && "$entry" -c 'import ase,numpy,matplotlib' >/dev/null 2>&1; then
      candidate_python="$entry"
      break
    fi
  done
fi
if [[ -z "$candidate_python" || ! -x "$candidate_python" ]]; then
  echo '请用 MATERIALS_PYTHON 指定已有且含 ASE、NumPy、Matplotlib 的 Python 绝对路径。' >&2
  exit 2
fi
if ! "$candidate_python" -c 'import ase,numpy,matplotlib' >/dev/null 2>&1; then
  echo '指定的 Python 环境缺少 ASE、NumPy 或 Matplotlib；请使用已有科研环境。' >&2
  exit 2
fi
export PATH="$(dirname "$candidate_python"):$HOME/Software/bin:$PATH"
if [[ "${1:-}" == "--plot" ]]; then
  shift
  exec "$candidate_python" "$project_root/scripts/materials/plot_results.py" "$@"
fi
if [[ "${1:-}" == "--phase-structure" ]]; then
  shift
  exec "$candidate_python" "$project_root/scripts/materials/analyze_phase.py" "$@"
fi
exec "$candidate_python" "$project_root/scripts/materials/run_case.py" "$@"
