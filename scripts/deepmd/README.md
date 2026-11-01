# DeePMD / DP-GEN

`dpgen_max_devi_f_distribution.py` 按表头收集 max_devi_f，保留来源路径；没有表头时用 `--column` 明确指定列。不推断温度，不将相同数据复制成不同温度样本。


## 文件

- [dp_descriptors.py](dp_descriptors.py)：dp_descriptors 数据处理工具。
- [dpgen_max_devi_f_distribution.py](dpgen_max_devi_f_distribution.py)：收集 DP-GEN 的最大原子力偏差。

涉及势函数、结构优化或大型科研软件的脚本，应先在小样本上核对环境和结果。
