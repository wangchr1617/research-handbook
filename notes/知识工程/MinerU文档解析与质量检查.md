# MinerU 文档解析与质量检查

适用环境：本机 Linux、macOS 或 Windows 的独立 Python 环境；下列命令面向 MinerU 4.x。模型、推理引擎和硬件兼容性需按对应发行版核对。

科研 PDF 可能含双栏正文、扫描页面、表格、公式和跨页标题。MinerU 将这些内容转成 Markdown 或结构化输出，供检索和阅读使用。解析质量决定后续检索能否拿到正确证据，尤其是表格数值与单位的对应关系。

## 先用一份文档跑通

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

## 怎样判断解析是否可用于科研

成功退出后，打开原 PDF 与解析结果逐项比对：

| 内容 | 重点检查 | 错误影响 |
| --- | --- | --- |
| 双栏正文 | 段落顺序、标题归属、页眉混入 | 将无关句拼成论述 |
| 表格 | 行列、合并单元格、单位、脚注 | 数值绑定到错误材料或条件 |
| 公式 | 上下标、负号、希腊字母 | 改变表达式含义 |
| 图片与图注 | 图号、子图、图注对应 | 引用错误图证据 |
| 页码 | PDF 物理页与正文印刷页 | 引用无法回到原位置 |

先固定包含上述版式的抽查页，保存错误类型及修订记录。自动比较字符数量能发现空输出，无法证明表格结构正确。重要数值应回看原表，而不是仅检查解析 Markdown 是否流畅。

## 给检索保留结构和定位

原始文档、解析产物和检索块分别保存。建议记录文档哈希、解析器版本、选项、结构块 ID、页码体系、表格或图号及解析时间。重新解析时生成新版本，再构建索引；旧回答引用应仍能找到原来的证据版本。

表格分块时，把标题、列名、单位和脚注与数据行一起组织；公式保留周边定义。段落切块可以适度重叠，但重复块需在检索合并时去重。固定字符数只是工程起点，是否切断证据要通过具体查询检验。

Archeos 的 [parsing.py](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/extension/mineru/parsing.py)优先保存物理页和块定位，结构缺失时回退到 Markdown。其切块参数属于该项目实现，可在[项目链路笔记](Archeos与Alkemie的知识链路.md)中继续阅读。

## 服务接入与失败处理

Web 应用中可拆成“上传 → 创建解析任务 → 轮询 → 下载产物 → 建索引”。分别记录解析失败、超时、空内容和索引失败，便于单独重试。重试要绑定任务代次，防止删除后返回的旧结果重新写入。

Archeos 的 [MinerUClient](https://github.com/hfood02/Archeos/blob/275ee9c5edcf4df6c773512d8576cb0010168fd4/backend/extension/mineru/client.py)演示了异步任务接口的客户端封装；这是项目依赖的服务协议，接入其他版本时应核对运行服务的 OpenAPI。

资料上传外部服务前需确认访问权和允许的数据处理范围，本地解析则要确认实际推理后端与模型下载来源。
