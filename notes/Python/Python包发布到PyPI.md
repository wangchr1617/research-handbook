# Python 包发布到 PyPI

**适用环境：Windows（PowerShell）、macOS / Linux（终端）；Python 3.10 及以上。**

当几套分析脚本都要把总能量换算成每原子能量，可以把函数放进同一个小包，让每个项目明确安装哪个版本。本文沿用[脚本运行篇的 GeTe 换算函数](Python基础与脚本运行.md)，把它放进一个可安装的 wheel，再从空环境验证。组内共享可以先分发 wheel；需要让外部读者用包名安装时，再走 PyPI 发布流程。这个例子借鉴了 [altbc_analyzer](https://github.com/wangchr1617/altbc_analyzer) 的组织思路。

## 一、把 GeTe 换算函数放进可安装的包

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

## 二、写清安装名、导入名与运行依赖

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

安装时用的是 `[project].name` 中的发布名 `gete-analysis-demo`，代码里用的是 `src/` 下的导入名 `gete_analysis_demo`。如果换项目名，分别检查这两处和 README 示例是否一致。对外分发前补齐作者、来源和许可证；使用了他人代码时保留其许可要求。依赖写入 `[project]` 的 `dependencies`，不要把整个开发环境的 `pip freeze` 原样塞进运行依赖。

## 三、离开源码目录，用 wheel 跑同一个算例

在独立 Python 环境中，进入包含 `pyproject.toml` 的目录：

```bash
python -m pip install build twine
python -m build
python -m twine check dist/*
```

第一次构建会生成 `dist` 目录，其中应有源码归档 `.tar.gz` 与 wheel `.whl`。`twine check` 核对包元数据和说明格式；接下来还需安装 wheel，检查程序本身是否能用。

在另一个干净环境中安装自己生成的 wheel。下例文件名需与实际产物一致：

```bash
python -m pip install ./dist/gete_analysis_demo-0.1.0-py3-none-any.whl
python -c "import gete_analysis_demo as demo; print(demo.__file__); assert demo.energy_per_atom(-10.25, 2) == -5.125"
```

第一条命令从项目目录安装本次生成的 wheel。执行第二条前切换到项目外的目录，确认打印的路径来自测试环境的 `site-packages`，并且换算仍得到 −5.125 eV/atom。如果原仓库能运行、wheel 装好后却找不到模板或数据文件，直接解开 wheel 查看这些资源是否随包分发，再核对代码找资源的方式。

## 四、从测试索引装回指定版本，再发正式索引

先在 [TestPyPI](https://test.pypi.org/)注册账号，在账户设置中按平台要求配置验证和 API Token。正式 [PyPI](https://pypi.org/)需要独立账号凭据，测试站的 Token 不能直接用于正式站。

```bash
python -m twine upload --repository testpypi dist/*
```

按 Twine 提示或其支持的凭据存储方式认证，Token 用户名为 `__token__`。不把 Token 写进脚本或提交到 Git；长期自动发布可按平台文档配置 Trusted Publishing。

上传成功后，在另一个新环境里从测试索引装回本次版本。下面的包名和版本要换为自己实际上传的值。示例包没有运行依赖，可以跳过依赖解析。若实际项目有依赖，先从信任的正式索引单独装齐。参见 [PyPA 的 TestPyPI 指南](https://packaging.python.org/en/latest/guides/using-testpypi/)。

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps gete-analysis-demo==0.1.0
```

安装后在项目外重复上节的导入路径和数值断言。这样连同索引上的包名、版本和安装产物一起得到验证。

确认包名、版本、内容和许可后，才运行正式发布命令：

```bash
python -m twine upload dist/*
```

发布前检查 `dist` 里只有本次要发布的产物；同一版本通常不能靠覆盖上传修正，修改后使用新版本。不要把“上传成功”当成结束，还需在新环境安装正式包并运行最小示例。

参考：[PyPA 官方打包教程](https://packaging.python.org/en/latest/tutorials/packaging-projects/)。
