# MinerU 文档解析与质量检查

适用环境：本机 Linux、macOS 或 Windows 的独立 Python 环境；下列命令面向 MinerU 4.x。模型、推理引擎和硬件兼容性需按对应发行版核对。

一页吸附能数据即使识别出了所有数字，也可能因为列标题或脚注错位而给出错误答案。仓库的 [H/Al(111) 吸附能算例](../VASP/表面与反应/VASP吸附能计算.md) 中，满覆盖度的平均值约为 0.3150 eV/H，再加一个 H 的增量约为 0.3913 eV。如果只保留数字，后续检索就很难回答“第二个 H 的增量是多少”。下面借这份已有数据说明解析验收看什么。算例本身是 Markdown，无需用 MinerU 转换。

## 一、按 PDF 的文本层选解析方式

在自己选定的工具目录执行。下面的安装命令会下载依赖；使用模型解析时还可能下载权重。已有项目使用独立环境，避免把推理依赖装进 Web 后端。

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install 'mineru>=4.0,<5'
mineru version --json
mineru-kit parse paper.pdf -o paper.md --tier standard
```

Windows PowerShell 激活命令为 `.venv\Scripts\Activate.ps1`。`paper.pdf` 替换为有权处理的文件；记录实际版本、命令和输出位置。发行版准备与硬件要求以[官方快速入门](https://github.com/opendatalab/MinerU/blob/master/docs/en/quick_start/index.md)为准。

纯文本层 PDF 可先尝试下列路径，明确关闭扫描页 OCR 回退：

```bash
mineru-kit parse paper.pdf -o paper.md --tier flash --ocr-mode txt
```

扫描页应改用 OCR 并准备相应模型。4.x 的 `mineru parse` 使用文档库和缓存，默认分页行为与直接转换工具不同；完整文件转换用 `mineru-kit parse` 更容易明确输出范围。单文件 Markdown 的 `-o` 是文件路径，多输入时则应是目录。以上区别见同一份[官方说明](https://github.com/opendatalab/MinerU/blob/master/docs/en/quick_start/index.md)。

## 二、看数值有没有跟对列和脚注

成功退出后，打开原 PDF 与解析结果逐项比对：

| 内容 | 重点检查 | 错误影响 |
| --- | --- | --- |
| 双栏正文 | 段落顺序、标题归属、页眉混入 | 将无关句拼成论述 |
| 表格 | 行列、合并单元格、单位、脚注 | 数值绑定到错误材料或条件 |
| 公式 | 上下标、负号、希腊字母 | 改变表达式含义 |
| 图片与图注 | 图号、子图、图注对应 | 引用错误图证据 |
| 页码 | PDF 物理页与正文印刷页 | 引用无法回到原位置 |

先固定包含上述版式的抽查页，保存错误类型及修订记录。自动比较字符数量能发现空输出，无法证明表格结构正确。重要数值应回看原表，而不是仅检查解析 Markdown 是否流畅。

开工前可挑一页含表格和脚注的实际 PDF，人工抄下其中一个目标单元格及其标题、单位和参考态。解析后从对应输出回查这几项。按吸附能算例的口径，如果能看到满覆盖的平均值，却找不到增量公式和气相 H₂ 参考态，这份输出就还不能支撑增量问题。

## 三、把原文位置和条件交给检索

原始文档、解析产物和检索块分别保存。建议记录文档哈希、解析器版本、选项、结构块 ID、页码体系、表格或图号及解析时间。重新解析时生成新版本，再构建索引；旧回答引用应仍能找到原来的证据版本。

表格分块时，把标题、列名、单位和脚注与数据行一起组织；公式保留周边定义。段落切块可以适度重叠，但重复块需在检索合并时去重。固定字符数只是工程起点，是否切断证据要通过具体查询检验。

Archeos 的 [parsing.py](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/extension/mineru/parsing.py)优先保存物理页和块定位，结构缺失时回退到 Markdown。其切块参数属于该项目实现，可在[项目链路笔记](Archeos与Alkemie的知识链路.md)中继续阅读。

分块后再用同一个问题试搜，看命中的块是否带齐条件，以及引用能否回到原位置。这个问题可直接加入下游的固定评估集。 [RAG 的分层故障检查](RAG检索生成与评估.md#四用同一个问题定位故障)

## 四、接入服务后，失败了从哪一步重试

Web 应用中可拆成“上传 → 创建解析任务 → 轮询 → 下载产物 → 建索引”。分别记录解析失败、超时、空内容和索引失败，便于单独重试。重试要绑定任务代次，防止删除后返回的旧结果重新写入。

Archeos 的 [MinerUClient](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/extension/mineru/client.py)演示了异步任务接口的客户端封装；这是项目依赖的服务协议，接入其他版本时应核对运行服务的 OpenAPI。

资料上传外部服务前需确认访问权和允许的数据处理范围，本地解析则要确认实际推理后端与模型下载来源。
