# CP2K 辅助工具

重启和 Multiwfn 转换默认生成新输入。`apply_cp2k_restart.py --in-place` 才修改原文件，并保留 `.bak` 备份。区块按完整路径匹配，多重 FORCE_EVAL 等歧义情形会报错，避免替换错误位置。

```bash
python scripts/cp2k/apply_cp2k_restart.py cp2k.restart cp2k.inp -o continued.inp
python scripts/cp2k/convert_cp2k_run_type.py cp2k.inp ot -o cp2k-ot.inp
```

## 文件

- [analyze_cp2k_output.py](analyze_cp2k_output.py)：该脚本解析 CP2K 输出文件，提取几何优化信息，并生成优化过程的能量、RMS 步长和 RMS 力的图表。
- [apply_cp2k_restart.py](apply_cp2k_restart.py)：将重启文件的结构写入 CP2K 输入。
- [cp2k_sections.py](cp2k_sections.py)：CP2K 区块读写辅助，供 apply_cp2k_restart.py 和 convert_cp2k_run_type.py 调用。
- [convert_cp2k_run_type.py](convert_cp2k_run_type.py)：用 Multiwfn 切换 CP2K SCF 或任务类型，默认写新文件。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
