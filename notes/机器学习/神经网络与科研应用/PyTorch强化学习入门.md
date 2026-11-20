# PyTorch 强化学习入门

材料筛选常要决定下一次计算哪个候选。如果每个候选都能独立提交，已有结果只是帮助挑选下一批点，可以从[主动学习](../材料主动学习与自动实验.md)入手。如果动作会改变后续能采取的步骤，例如按顺序调整同一样品的工艺条件，而性能要到最后才测得，就要考虑一连串动作怎样共同影响结果。强化学习中的价值函数估计的是从当前状态采取某个动作后的累计回报。

## 一、从八条转移看一次 DQN 更新

DQN 适用于这个示例中的离散动作。对非终止转移，目标是即时奖励加上折扣后的下一步最大估计价值。对真正终止的转移，目标只剩即时奖励。

在已安装 PyTorch 的环境中把代码保存为 `dqn_step.py`，执行 `python dqn_step.py`。

```python
import copy
import torch
from torch import nn

torch.manual_seed(7)
q_net = nn.Sequential(nn.Linear(4, 32), nn.ReLU(), nn.Linear(32, 2))
target_net = copy.deepcopy(q_net).eval()
optimizer = torch.optim.Adam(q_net.parameters(), lr=1e-3)
states = torch.randn(8, 4)
next_states = torch.randn(8, 4)
actions = torch.randint(0, 2, (8, 1))
rewards = torch.randn(8)
terminated = torch.tensor([False] * 7 + [True])
selected_q = q_net(states).gather(1, actions).squeeze(1)
with torch.no_grad():
    next_q = target_net(next_states).max(dim=1).values
    expected_q = rewards + 0.99 * (~terminated).float() * next_q
loss = nn.SmoothL1Loss()(selected_q, expected_q)
optimizer.zero_grad(set_to_none=True)
loss.backward()
optimizer.step()
print("DQN update loss =", loss.item())
assert torch.isfinite(loss)
```

网络为每条状态输出两个动作分数，得到 `[8, 2]`。用 `gather` 取出实际选过的动作后，`squeeze(1)` 将预测变成 `[8]`，和八个目标逐项计算损失。最后一条样本是终止转移，所以即使目标网络给了很高的下一步分数，该样本的目标也等于它的即时奖励。

时间上限造成的截断要结合任务定义来理解。假如时间上限只是采集时划定的边界，任务原本还能继续，就仍可用截断处的下一状态估计未来回报。如果时间用尽本来就是任务结束条件，则不再估计终止后的收益。把两者混成一个终止标记，会改变网络学到的动作价值。

## 二、一次更新之后，怎样检验策略

示例使用人工转移，有限损失只能确认一次更新可以计算。完整 DQN 还需要与环境交互、探索动作、从经验池抽样并定期更新目标网络。可以沿 [PyTorch 官方 DQN 教程](https://docs.pytorch.org/tutorials/intermediate/reinforcement_q_learning.html)运行 CartPole，在独立回合中比较训练所得策略及简单基线，并报告不同随机种子下的回报差异。

转到材料问题时，先明确动作如何改变状态、失败会消耗多少预算，以及奖励对应哪个可测量的量。若用代理模型给奖励，策略可能偏向模型估计过高的区域。比较策略时可以固定计算或实验预算，记录有效结果数和达到目标所需的成本，再对高回报候选安排独立计算或测量。策略回报用于评价选择过程，材料性质和可合成性各有自己的验收依据。
