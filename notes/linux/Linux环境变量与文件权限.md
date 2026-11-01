# Linux 环境变量与文件权限

**适用环境：Linux（Bash）；macOS 的路径变量概念相同，交互配置通常使用 zsh。**

同一个命令在两台机器上表现不同，先看程序路径和环境，不先修改系统配置。

## 一、命令从哪里来

```bash
printf '%s\n' "$PATH"
command -v python
python --version
type module
```

`PATH` 是按顺序搜索的目录列表，用冒号分隔；前面的同名程序通常先被找到。Conda、Module 都可能改变它。使用绝对路径可以明确调用某一个程序，但其动态库仍要匹配。

练习一个仅影响当前终端的变量：

```bash
export DEMO_PROJECT=GeTe
printf '%s\n' "$DEMO_PROJECT"
bash -c 'printf "child sees %s\n" "$DEMO_PROJECT"'
unset DEMO_PROJECT
```

`export` 让子进程继承变量，子进程不能反过来改变父 shell。编辑 `.env` 文件本身不会让所有程序自动读取它，是否加载取决于应用。

## 二、临时与长期配置

```bash
OMP_NUM_THREADS=1 python analysis.py
```

上面只为这次命令设置变量，`analysis.py` 要换成自己的脚本。若希望某个设置长期生效，先确认机器和 shell，再编辑个人配置：Bash 交互 shell 常读 `~/.bashrc`，zsh 常读 `~/.zshrc`，登录 shell 的规则还不同。

`source 文件` 在当前 shell 执行配置；`bash 文件` 在子进程执行。PBS 作业、非交互 SSH 和图形应用不一定读取交互配置，作业脚本应显式加载需要的环境，见 [Module](../../getting-started/Module使用.md)。

## 三、读懂文件权限

```bash
ls -ld .
ls -l input.inp
```

以 `-rw-r-----` 为例，开头 `-` 表示普通文件；后三组分别对应所有者、组成员和其他用户的权限。`r` 读、`w` 写、`x` 执行；目录的 `x` 表示可进入和遍历。

给自己的脚本增加执行权限：

```bash
chmod u+x run.sh
```

配置文件只供自己读取时可以用 `chmod 600 私人配置文件`。这些都是示例文件名，先确认文件属于自己。不要通过 `chmod -R 777` 解决所有权限问题，共享目录的组和继承规则向管理员确认。

## 四、空间与配额

```bash
du -sh .
df -h .
```

`du` 看目录占用，`df` 看文件系统空间。文件系统还有空间也可能已超过个人配额或文件数量限制，配额查询按集群说明操作。

做计算时保留输入和必要重启文件，输出按用途整理；准备清理前先列出文件并确认是否用于续算。删除文件的权限主要取决于所在目录，也不要把“可写目录”理解为里面所有文件都属于自己。

参考：[Bash 环境说明](https://www.gnu.org/software/bash/manual/html_node/Environment.html)、本机 `man chmod`。
