# Git 分支协作与合并

**适用环境：Windows（Git Bash）、macOS、Linux。先完成 [Git 安装与账号配置](Git入门.md)。**

一个分支对应一项相对独立的工作，例如补充 GeTe 的计算说明。先在自己的分支修改，再通过 Pull Request（PR）请成员检查，比大家同时推送主分支容易保持清楚。

## 一、在本地练习分支

下面只在新建的练习目录中执行，不操作现有科研仓库：

```bash
mkdir git-branch-demo
cd git-branch-demo
git init -b main
git config user.name "Student"
git config user.email "student@example.com"
printf '# Calculation notes\n' > README.md
git add README.md
git commit -m "docs: add initial notes"
git switch -c docs/gete
printf '\nGeTe: check input units before calculation.\n' >> README.md
git diff
git add README.md
git commit -m "docs: add GeTe preparation"
git switch main
git merge --ff-only docs/gete
git log --oneline --graph --all
```

`switch -c` 创建并进入分支，`merge` 将指定分支的提交合入当前分支。这个例子中主分支没有其他改动，因此可以快进合并，最后日志应能看到两次提交。

`user.name` 和 `user.email` 在这里仅配置练习仓库，不是登录凭据。正式仓库填写自己的署名，不照抄示例身份。

## 二、多人协作的顺序

从仓库网页复制 HTTPS 或 SSH 地址，执行 `git clone 仓库地址`，进入克隆目录。先用 `git branch --show-current` 查看分支，主分支不一定叫 `main`。

```bash
git status --short
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c docs/gete-inputs
```

工作区有未提交修改时，先确认并保存自己的工作，不带着不明改动切换分支。`pull --ff-only` 在分支已经分叉时会停止，让你先弄清两边的提交。

完成修改后：

```bash
git diff --check
git diff
git add notes/gete.md
git diff --cached
git commit -m "docs: explain GeTe inputs"
git push -u origin docs/gete-inputs
```

`notes/gete.md` 是示例路径，替换成自己修改的文件。新文件不会出现在普通 `git diff` 中，要结合 `git status` 和文件内容检查。

在 GitHub / Gitee 打开 PR，说明解决什么问题、哪些步骤已验证。没有上游写权限时先 Fork，再从自己的仓库提交 PR；不要用强制推送解决权限或分支冲突。

## 三、遇到合并冲突时怎样继续

合并时 Git 如果显示冲突，用 `git status` 找到文件，打开后查看 `<<<<<<<`、`=======`、`>>>>>>>` 标记。读懂双方改动后保留正确内容，删除标记，重新检查文件。

```bash
git add 冲突文件.md
git commit
```

不确定双方意图时，先问修改者，不直接选择“全部保留我的”。如果本次合并还没完成、想回到合并前，可用 `git merge --abort`；操作前仍要保存合并期间自己新写的内容。

## 四、完成后整理

PR 合并后更新本地主分支，再确认自己的分支已合并：

```bash
git switch main
git pull --ff-only origin main
git branch --merged
git branch -d docs/gete-inputs
```

`-d` 会检查合并状态；平台若采用 squash merge，Git 可能无法按原提交关系判断，先核对最终内容，不为了清理而直接改用强制删除。

参考：[Git 官方入门](https://git-scm.com/docs/gittutorial)、[合并说明](https://git-scm.com/docs/git-merge)。
