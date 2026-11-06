# Git 文件管理与撤销

**适用环境：Windows（Git Bash）、macOS、Linux；Git 2.23 及以上支持 `restore`。**

撤销之前先区分三处位置：工作区是正在编辑的文件，暂存区是下次提交的内容，提交历史是已经保存的版本。想撤销哪一层，就针对哪一层操作。

## 一、先看状态与差异

```bash
git status --short
git diff
git diff --cached
git log --oneline -5
```

例如 ` M` 表示工作区修改尚未暂存，`M ` 表示已经暂存，`??` 表示未跟踪。一个文件也可能同时有暂存和未暂存修改。

## 二、只是放错了暂存区

```bash
git restore --staged notes.md
```

这会取消 `notes.md` 的暂存，工作区内容还在。修改后先检查：`git diff --cached` 应不再包含这次变化，`git diff` 仍能看到它。

## 三、想找回旧版内容，先另存

```bash
git show HEAD:notes.md > notes.previous.md
```

这将上一次提交里的文件另存，当前 `notes.md` 不变。查看更早的版本时，把 `HEAD` 替换为 `git log` 中确认过的提交号。先比较两份文件，再决定取哪些内容。

如果已经确认工作区里的修改完全不要了，才执行 `git restore -- notes.md`。它会用暂存区版本覆盖工作区，未保存到 Git 的内容可能无法找回。不要对整个科研目录随手运行批量恢复。

已提交并共享的普通提交需要撤销时，通常使用 `git revert 提交号` 生成反向提交，让历史保留；合并提交的撤销另有参数，先查帮助。`reset --hard` 会改分支位置并覆盖文件，不作为新生的默认撤销方式。

## 四、科研仓库哪些文件值得跟踪

以计算项目为例，优先保存输入、PBS 脚本、后处理脚本、较小的结果摘要和说明。大型轨迹、波函数、虚拟环境、临时日志和密钥不放进普通 Git 历史。

项目根目录的 `.gitignore` 示例：

```gitignore
.venv/
__pycache__/
*.pyc
.env
.DS_Store
outputs/
```

这是演示规则，按项目用途修改，不用 `*.dat`、`*.xyz` 这类过宽规则把需要共享的输入也隐藏掉。

```bash
git check-ignore -v outputs/demo.log
git ls-files .env
```

`.gitignore` 只影响未跟踪文件。若某文件已经跟踪，新增忽略规则不会把它从历史删除；确需停止跟踪时，先检查 `git diff` 和备份，再用 `git rm --cached 文件名`，本地文件仍保留。

凭据如果已经提交，仅添加忽略规则或删除最新版本不能撤销泄露，需要及时撤销凭据并由维护者处理历史。

## 五、记住这几个区别

| 需求 | 常用操作 |
| --- | --- |
| 查看当前目录的真实改动 | `status`、`diff` |
| 取消暂存但保留编辑 | `restore --staged` |
| 提取旧内容用于比较 | `show 提交号:路径` 并另存 |
| 撤销已共享的普通提交 | `revert` |
| 以后不跟踪生成文件 | `.gitignore`，必要时检查 `rm --cached` |

参考：[restore](https://git-scm.com/docs/git-restore)、[ignore 规则](https://git-scm.com/docs/gitignore)。
