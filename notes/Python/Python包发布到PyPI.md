# Python 包发布到 PyPI

**适用环境：Windows（PowerShell）、macOS / Linux（终端）；Python 3.10 及以上。**

脚本被多个项目重复使用时，可以整理成包。以我此前的 [altbc_analyzer](https://github.com/wangchr1617/altbc_analyzer) 项目思路为例，这里用一个更小的演示包说明目录、构建、安装和发布流程。

先在本机把包构建、安装并测试好，再考虑上传。普通后处理脚本不必为了使用而发布到 PyPI。

## 一、准备项目目录

在新的练习目录中准备：

```text
gete-analysis-demo/
├── pyproject.toml
├── README.md
└── src/
    └── gete_analysis_demo/
        └── __init__.py
```

`src` 布局将源码与项目根目录分开。示例包名 `gete-analysis-demo` 只是占位，实际发布前换成自己有权使用且未被占用的名称。

`__init__.py` 写入：

```python
def energy_per_atom(energy_ev, atoms):
    """由总能量（eV）和原子数得到 eV/atom。"""
    if atoms <= 0:
        raise ValueError("atoms must be positive")
    return energy_ev / atoms
```

## 二、描述构建方式和元数据

`pyproject.toml` 示例：

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "gete-analysis-demo"
version = "0.1.0"
description = "A small energy normalization example"
readme = "README.md"
requires-python = ">=3.10"
authors = [{name = "YOUR_NAME"}]

[tool.setuptools.packages.find]
where = ["src"]
```

`README.md` 说明用途、输入输出、安装和最小示例，例如：

```markdown
# GeTe analysis demo

Convert total energy in eV to energy per atom.

Use `from gete_analysis_demo import energy_per_atom` after installation.
```

对外分发前补齐作者、来源和许可证；使用了他人代码时保留其许可要求。依赖写入 `[project]` 的 `dependencies`，不要把整个开发环境的 `pip freeze` 原样塞进运行依赖。

## 三、先本地构建与检查

在独立 Python 环境中，进入包含 `pyproject.toml` 的目录：

```bash
python -m pip install build twine
python -m build
python -m twine check dist/*
```

第一次构建时 `dist` 是新目录。应生成源码归档 `.tar.gz` 和 wheel `.whl`；`twine check` 检查包元数据与说明格式，不验证程序正确性。

在另一个干净环境中安装自己生成的 wheel。下例文件名需与实际产物一致：

```bash
python -m pip install ./dist/gete_analysis_demo-0.1.0-py3-none-any.whl
python -c "from gete_analysis_demo import energy_per_atom; assert energy_per_atom(-10, 2) == -5"
```

测试时离开源码目录再导入，避免误把当前目录中的源码当成安装成功。正式项目还应检查资源文件是否进入 wheel、依赖是否完整。

## 四、测试发布，再正式发布

先在 [TestPyPI](https://test.pypi.org/)注册账号，在账户设置中按平台要求配置验证和 API Token。正式 [PyPI](https://pypi.org/)需要独立账号凭据，测试站的 Token 不能直接用于正式站。

```bash
python -m twine upload --repository testpypi dist/*
```

按 Twine 提示或其支持的凭据存储方式认证，Token 用户名为 `__token__`。不把 Token 写进脚本或提交到 Git；长期自动发布可按平台文档配置 Trusted Publishing。

验证测试站安装时，TestPyPI 不一定具备所有运行依赖，应按项目说明单独准备。`--no-deps` 只适合依赖已确认安装齐全的情况。

确认包名、版本、内容和许可后，才运行正式发布命令：

```bash
python -m twine upload dist/*
```

发布前检查 `dist` 里只有本次要发布的产物；同一版本通常不能靠覆盖上传修正，修改后使用新版本。不要把“上传成功”当成结束，还需在新环境安装正式包并运行最小示例。

参考：[PyPA 官方打包教程](https://packaging.python.org/en/latest/tutorials/packaging-projects/)。
