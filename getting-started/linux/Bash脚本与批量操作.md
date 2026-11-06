# Bash 脚本与批量操作

**适用环境：Linux、macOS 的 Bash；Windows 在 WSL 或 Git Bash 执行。**

一串命令需要反复执行时，可以保存为脚本。先让脚本只列出准备处理的文件，确认范围后再执行实际操作。

## 一、从一个可运行脚本开始

先会使用 [Linux 命令行](Linux命令行使用与常用命令.md)，在自己的练习目录准备两个小文件：

```bash
mkdir -p shell-demo/run-a shell-demo/run-b
printf 'energy = -10.2\n' > shell-demo/run-a/program.out
printf 'energy = -10.4\n' > shell-demo/run-b/program.out
```

在 `shell-demo` 的上一级目录保存 `collect.sh`：

```bash
#!/bin/bash
set -euo pipefail

root=${1:-shell-demo}
if [[ ! -d "$root" ]]; then
    printf 'Not a directory: %s\n' "$root" >&2
    exit 1
fi

for directory in "$root"/*; do
    [[ -d "$directory" ]] || continue
    file="$directory/program.out"
    if [[ -f "$file" ]]; then
        printf '%s: ' "$directory"
        tail -n 1 "$file"
    fi
done
```

```bash
bash -n collect.sh
bash collect.sh shell-demo
```

应看到两个目录和各自最后一行。`bash -n` 检查语法，不执行脚本；它不能检查输入路径或计算结果是否正确。

## 二、变量和引号

`root=${1:-shell-demo}` 表示使用第一个位置参数，没有提供时用默认目录。`"$root"` 保证路径中有空格时仍作为一个参数传递。

单引号通常保留字面内容，双引号允许变量展开；路径和文件名变量尽量加双引号。`for file in $(ls ...)` 会按空白拆分文件名，不适合处理实际数据目录。

需要递归寻找文件时，在 Bash 中可以使用：

```bash
find shell-demo -type f -name '*.out' -print0 |
while IFS= read -r -d '' file; do
    printf 'Found: %s\n' "$file"
done
```

`-print0` 与 `read -d ''` 用空字符分隔路径，能处理文件名中的空格。这里仅展示文件，不删除或覆盖内容。

## 三、退出状态与日志

`set -u` 检查未定义变量，`pipefail` 让管道中的失败更容易被发现；`set -e` 在部分失败条件下退出，但有条件语句等例外，不能代替显式判断。

```bash
if bash collect.sh shell-demo > collect.log 2> collect.err; then
    printf 'Collection finished\n'
else
    printf 'Collection failed; read collect.err\n' >&2
fi
```

日志存在不代表处理成功，还要检查退出状态和预期记录数。需要并行运行大量计算时，通过 PBS 管理资源，不在登录节点给循环简单加上 `&` 就全部启动。

## 四、扩展到自己的计算

以 GeTe 多个体积目录为例，先固定目录结构和输出格式，再提取能量。目录名里有数字，不代表按字典排序就是物理顺序；汇总时保留目录名与原始单位，再做数值排序。

参考：[Bash 官方手册](https://www.gnu.org/software/bash/manual/bash.html)。
