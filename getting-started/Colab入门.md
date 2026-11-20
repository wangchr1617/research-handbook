# Colab 入门

Colab 适合在浏览器里试跑 Python 分析、检查数据或生成图。这里用仓库的一维紧束缚模型做第一次练习，默认 CPU 就够。若任务依赖授权求解器、受限数据或长时间独占资源，先按项目要求选择本机或集群环境。

## 一、先确认代码和文件在哪台机器上

登录 [Google Colab](https://colab.research.google.com/) 并新建 Notebook。先在第一格运行 `print("hello")`，看到输出后再运行下面的单元。Colab 的代码在云端运行时执行，浏览器里的 Notebook 和运行目录里的文件分别保存；重连或更换运行时后，需要重新获取输入和依赖，详见 [Colab 运行时说明](https://research.google.com/colaboratory/faq.html)。

## 二、从输入跑到可核对的结果

在新的运行时中运行下面的单元。从公共仓库取得算例后，先读 [案例说明](../examples/solid-state/tight-binding-band/README.md)，核对依赖和模型参数，再运行：

```python
!git clone --depth 1 https://github.com/wangchr1617/research-handbook.git /content/research-handbook
%cd /content/research-handbook/examples/solid-state/tight-binding-band
%pip install -r requirements.txt
!python run.py
```

输出应包含 0.8 eV 的区边界带隙和 3.2 eV 的全谱跨度。可以用 `data/input.json` 中的跃迁参数复核带隙，再打开 `result.png` 查看图像。若目录中已有旧图，先确认本次脚本正常结束，再读取新生成的 `results.json`。重新运行时可以复用已克隆的目录，直接从切换目录那一行继续；需要保存分析结果时，下载 Notebook 与结果图表，并记录所使用的仓库提交。

## 三、任务需要 GPU 时才更换运行时

从运行时菜单选择硬件加速器，更换后需要重新运行准备输入的单元。可执行 `!nvidia-smi` 检查 NVIDIA GPU 是否分配成功，随后还要确认所用计算库确实选择了该设备。若需要读取 Google Drive 中的文件，可以在 Notebook 中挂载 Drive，并按实际目录填写路径。运行时间、设备和可用额度以当前 Colab 环境为准，详见 [Colab 资源限制](https://research.google.com/colaboratory/faq.html#resource-limits)。
