# PyTorch 强化学习入门

**适用环境：已安装 PyTorch 的 Python 环境。**

强化学习让智能体根据状态选择动作，从环境奖励中学习策略。它与监督学习的区别在于动作会影响后续数据，奖励还可能延迟到达。

## 先认识 DQN 的目标

DQN 用网络估计各动作的价值。对非终止转移，常用目标为 $r+\gamma\max_a Q_{target}(s',a)$；任务终止的状态不再加入下一步价值。

下面用人工转移数据演示一次 DQN 参数更新。保存为 `dqn_step.py`，执行 `python dqn_step.py`：

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

这些是人工构造的转移，只演示张量维度与一次更新，不是完整训练器。完整 DQN 还需要环境交互、探索策略、经验回放、目标网络更新和独立评估。

环境因时间限制被截断，与任务真正终止的语义可能不同；是否继续 bootstrap 要按环境定义处理。不能简单把所有“本轮结束”都当成终止状态。

## 接着学什么

可以沿 [PyTorch 官方 DQN 教程](https://docs.pytorch.org/tutorials/intermediate/reinforcement_q_learning.html)安装 Gymnasium，运行完整的 CartPole 例子，再比较不同随机种子的回报曲线。先看状态、动作、奖励和终止条件，再增加模型复杂度。

材料搜索任务需要明确每次动作的计算成本、失败处理和奖励定义。训练回报上升不等于实际找到了稳定、可合成或更优的材料，最终仍需独立计算验证。
