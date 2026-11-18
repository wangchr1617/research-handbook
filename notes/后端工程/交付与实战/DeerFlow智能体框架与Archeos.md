# DeerFlow 智能体框架与 Archeos

一份 CSV 的 RMSE 用几行 Python 就能算。可如果同学上传的是几份预测结果，得先弄清哪份是参考、单位是否一致。算完也得说清楚用了哪份文件，以及结果在哪一次运行里生成。DeerFlow 管理模型和工具之间的往返，Archeos 把工具调用接到团队授权的科研服务上。下面仍用那份三行 CSV，看这个过程最后会留下什么。

## 一、什么情况下需要智能体框架

任务已经固定时，用脚本最省事。手册的 RMSE 小案例就是这样，输入列、计算公式、输出格式都固定，每次跑的步骤相同。需要模型从不同附件中选输入，发现单位不一致后向用户确认，或决定接着调用哪个工具时，才有必要让智能体组织过程。反复出现的数值计算仍可以封装成确定性的脚本或工具，供模型调用，也方便人工单独复核。 [手册的 RMSE 小案例](../../../examples/rmse/README.md)

## 二、DeerFlow 跑一轮，Archeos 接上哪几步

以“读附件并交付结果”为例。模型拿到问题、附件引用和可调用工具的说明，主智能体发出调用，DeerFlow 执行获准的工具，再把工具结果交给模型。任务还需要继续时，模型根据实际结果决定下一步。技能适合写下会反复使用的步骤，比如先检查单位和行数。真正读文件、运行 Python 和写出文件，走各自的工具接口和执行环境。 [主智能体入口](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/vendor/deer-flow/backend/packages/harness/deerflow/agents/lead_agent/agent.py)

检查点保存线程中的运行状态，后续一轮可以带上已有的消息和附件引用。SSE 把当前一轮的输出和事件传给页面。计算产物则随计算记录保存，刷新浏览器时，还得用对应的回执找到结果文件。 [Archeos 的对话运行](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/conversation-runtime.md)

在 Archeos 中，工作台代理先核对登录、团队成员和资源权限，再把请求送到团队的 DeerFlow 引擎。到了 Python 工具，计算适配器会把成员、线程和可读文件范围绑定到这次调用。读源码可顺着这两个入口走，先看请求是以什么身份进去的，再看计算能读到哪些文件。本文以 Archeos `e412ba0` 为准，锁定的 DeerFlow 基线为 `2.3.0-dev`。 [工作台代理](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/backend/archeos/engine/workbench.py) · [计算适配器](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/packages/scientific-compute/scientific_compute/adapters/deerflow.py) · [版本锁定清单](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/upstream.lock.json)

## 三、几种接入方式怎么选

| 要解决的问题 | 从哪里开始 |
| --- | --- |
| 固定流程要每天运行，或者要接进已有脚本 | 用确定性的 Python。需要隔离执行和数值回执时，可以用独立的 Scientific Compute CLI 或 SDK。 |
| 想验证模型怎么用工具、多步流程怎么跑 | 从 DeerFlow 的运行框架入手，先接一个可独立验证的工具，观察工具调用和返回结果。外部服务已有 MCP 接口时，可按实际权限接入。 |
| 课题组成员从工作台上传数据、调用计算、回看记录 | 走 Archeos。在团队范围配置模型、工具和分析环境。已有 Alkemie 项目里的建模和专业计算，沿用项目的执行与结果记录。 |

下面走工作台路线。可以在「设置 → 科研服务与计算环境」查看团队是否已配置 Python 分析环境。能看到配置后，还要确认当前成员可以使用工具并读取上传的文件。要单独验证执行器和验收逻辑，可以走 CLI 或 SDK。 [Scientific Compute 独立运行](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/packages/scientific-compute/README.md) · [Archeos 的计算接入说明](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/compute-runs.md)

## 四、拿同一份 CSV 验收两次

先在手册根目录运行 `python3 examples/rmse/run.py`，用本地脚本确认基准。那份 CSV 有三行，误差是 `+1`、`−1`、`+1`。完整输入得到 **3 个样本，RMSE 1.000000 eV/atom**。把同一份 CSV 上传到配置了 Python 分析的 Archeos，可以用这个请求。 [三行 CSV](../../../examples/rmse/data.csv)

> 附件的 `reference` 和 `prediction` 两列都以 `eV/atom` 为单位。用这两列计算 RMSE。请在计算请求中固定验收条件，样本数等于 3，RMSE 与 1 的绝对差不超过 `1e-6 eV/atom`，输出的单位字段为 `eV/atom`。保留原 CSV，交付带有 `samples`、`rmse` 和 `unit` 的 `values.json`，并给出该次计算回执。

为什么非得查样本数？删掉任意一行，剩下两行的平方误差仍然都是 1。下面这份文件完全可能由正常退出的脚本生成，只查 RMSE 就会漏过去。

```json
{"samples": 2, "rmse": 1.0, "unit": "eV/atom"}
```

把正确和漏读的两份 JSON 分别交给 Archeos `e412ba0` 的数值验收器，得到下面两条结果。 [数值验收契约](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/compute-runs.md#独立数值有效性检查) · [验收器源码](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/packages/scientific-compute/scientific_compute/numerical_checks.py)

```text
samples=3, passed: sample_count=passed, rmse=passed
samples=2, failed: sample_count=failed, rmse=passed
```

在工作台复核时，先用 `compute_run_python` 返回的 `run_id` 查 `compute_status`。回执里的 `execution.process_status` 回答脚本是否跑完，`numerical_validation.status` 回答结果是否满足条件。最后打开同一次运行交付的 `values.json`。两个状态分别看，才能识别上面这种正常退出却漏读一行的结果。 [Python 执行回执字段](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/packages/scientific-compute/scientific_compute/runtime.py)

<details>
<summary>展开本例用的验收配置</summary>

```json
{
  "outputs": ["values.json"],
  "scientific_checks": [
    {
      "name": "sample_count",
      "file": "values.json",
      "pointer": "/samples",
      "kind": "range",
      "min": 3,
      "max": 3
    },
    {
      "name": "rmse",
      "file": "values.json",
      "pointer": "/rmse",
      "kind": "close",
      "reference": 1,
      "atol": 0.000001,
      "unit": "eV/atom",
      "unit_pointer": "/unit"
    }
  ]
}
```

</details>

## 五、结果说“通过”以后，还有什么要查

**通过只覆盖事先声明的条件。** 这份 CSV 的列名本身没有单位，`eV/atom` 是用户在请求里提供的。验收器可以检查输出有没有写成这个单位，输入单位仍要回到数据来源查证。评估真实势函数时，参考集、划分和误差口径也要先说明，样本数对上只是其中一项。权限由运行环境检查，技能中的文字只描述操作步骤。 [数值检查的适用范围](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/compute-runs.md#独立数值有效性检查)

**页面断线先找原来那一轮。** 用 `thread_id` 找到会话，再用响应 `Location` 中的 GET 地址恢复原引擎流。要确认 Python 是否已经结束，继续查计算回执里的 `run_id`。对于已登记自动续接的长作业，作业完成后还可能启动新一轮来读取结果。这样，页面没继续出字时，可以先查连接和已有任务，再决定是否重试。 [Archeos 的运行和重连](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/conversation-runtime.md) · [计算执行和续接](https://github.com/hfood02/Archeos/blob/e412ba03df7138ab2cc04dda91a8d198743a596b/docs/compute-runs.md)

## 六、下一份分析从哪里开始

先留下一份有已知答案的小输入，和一份应该失败的输出。将来换模型、改工具或加新的分析列时，先用这一对样本检查实际产物。再接入真实科研数据，把参考来源、单位和误差条件随任务保存。这样同学接过结果时，能沿着计算回执复核自己的问题。
