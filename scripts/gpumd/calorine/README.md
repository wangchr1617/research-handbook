# NEP 势计算

结构优化入口：`calorine_relax.py`，支持原子、晶胞与定体积模式。其他脚本处理不同性质，请按文件开头的参数说明配置。

## 文件

- [calorine_elastic.py](calorine_elastic.py)：使用 NEP 势计算弹性常数。
- [calorine_ev.py](calorine_ev.py)：使用 NEP 势计算能量体积曲线。
- [calorine_fc.py](calorine_fc.py)：使用 NEP 势生成力常数。
- [calorine_phon.py](calorine_phon.py)：使用 NEP 势计算声子性质。
- [calorine_raman.py](calorine_raman.py)：使用 NEP 势计算 Raman 相关量。
- [calorine_relax.py](calorine_relax.py)：使用 NEP 势优化结构，统一原子优化、晶胞优化与定体积模式。
- [calorine_thc.py](calorine_thc.py)：使用 NEP 势与 phono3py 计算晶格热导率。
