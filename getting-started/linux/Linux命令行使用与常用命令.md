# Linux 命令行使用与常用命令

**适用环境：Linux（Bash）；macOS 终端中多数基础命令也适用，GNU / BSD 参数存在差异。**

先弄清“我在哪台机器、哪个目录、对哪些文件操作”，再执行命令。SSH 登录后看到的目录属于集群，不是本机。

## 开始前

先选一种可以练习的环境：

- 已有集群账号：按 [Mac SSH](../新生入门（Mac）.md#三连接集群与传文件)或 [Windows MobaXterm](../新生入门（Windows）.md)连接，命令在远端终端输入。
- Windows 暂无账号：按 [WSL 安装](../WSL与Docker安装使用（Windows）.md)准备本机 Ubuntu，无需先申请集群资源。
- Mac 暂无账号：按 `Cmd+空格` 搜索“终端”，可先练习目录、文件和文本命令；macOS 不是 Linux，参数差异见各节说明。

先在自己的练习目录操作，不需要管理员权限：

```bash
mkdir -p "$HOME/command-practice"
cd "$HOME/command-practice"
```

`$` 或 `%` 如果出现在终端提示符里，不属于命令本身；代码中的 `YOUR_USER`、`/path/to/...` 等是占位内容，先替换为自己的值。

## 一、目录与文件

```bash
hostname                 # 当前主机
pwd                      # 当前目录的绝对路径
ls -lah                  # 查看文件，包括隐藏文件
mkdir -p ~/projects/GeTe/scf
cd ~/projects/GeTe/scf
printf 'GeTe test\n' > note.txt
cp -i note.txt note.backup.txt
mv -i note.backup.txt note.old.txt
```

`~` 是当前用户主目录，`.` 是当前目录，`..` 是上一级目录。文件名含空格时加双引号；计算目录尽量使用简短英文、数字和连字符，减少软件兼容问题。

Linux 区分大小写，`POSCAR` 和 `poscar` 不是同一个文件。以 `.` 开头的文件默认隐藏，例如 `~/.bashrc`。

## 二、查看和搜索内容

```bash
cat note.txt
less program.out
head -n 20 program.out
tail -n 30 program.out
tail -f program.out
grep -n 'error' program.out
grep -in 'warning' program.out
find . -type f -name '*.pbs'
diff -u input.old input.new
```

`less` 按 `/关键词` 搜索、`n` 找下一个、`q` 退出；`tail -f` 按 `Ctrl+C` 退出，不会停止正在计算的程序。`grep -i` 忽略大小写，`-n` 显示行号。

装有 ripgrep 时，可用 `rg -n '关键词' .` 搜索内容、`rg --files` 列文件。`find` 的通配符要加引号，避免先被 shell 展开。

## 三、重定向、管道和退出状态

```bash
command > output.log 2> error.log
command >> output.log 2>&1
grep 'energy' program.out | tail -n 10
```

这里的 `command` 代表要执行的真实程序。`>` 覆盖文件，`>>` 追加内容；`2>` 保存标准错误。管道把前一个命令的标准输出交给后一个命令。

```bash
python analysis.py
status=$?
printf 'exit status = %s\n' "$status"
```

退出状态 `0` 通常代表命令成功，非零表示失败或特殊状态。要在紧接着的下一条命令保存 `$?`；管道的默认状态通常来自最后一个命令，写 Bash 脚本时可按需要启用 `set -o pipefail`。

## 四、编辑文本

```bash
vi input.inp
```

进入后按 `i` 编辑，按 `Esc` 返回普通模式；`:wq` 保存退出，`:q!` 放弃未保存修改，`/关键词` 搜索，`u` 撤销。习惯图形界面时，也可使用 VSCode Remote - SSH 编辑远端文件，保存前确认窗口左下角的远端主机名。

批量替换先输出到新文件检查，例如：

```bash
sed 's/dft_forces/forces/g' train.xyz > train.converted.xyz
```

这会替换每行所有匹配文本。macOS 的 `sed -i` 与 GNU `sed -i` 写法不同，跨平台笔记优先保留输出文件再比较。

## 五、权限、进程与空间

```bash
ls -l run.sh
chmod u+x run.sh
ps -u "$USER"
du -sh .
df -h .
```

`chmod u+x` 给文件所有者增加执行权限，不需要 `chmod 777`。磁盘还有空间也可能触及个人 quota，配额命令按集群说明查询。

本机普通进程确认 PID、所有者和命令后可用 `kill PID` 请求退出。集群作业通过 [PBS](../PBS作业管理系统使用.md)管理，用 `qdel` 取消；关闭 SSH、按 `Ctrl+C` 停止日志跟踪，都不会自动取消已提交的批处理作业。

## 六、压缩与传输

```bash
tar -czf inputs.tar.gz input.inp job.pbs
tar -tzf inputs.tar.gz
mkdir unpacked
tar -xzf inputs.tar.gz -C unpacked
```

先看压缩包内容，再解压到新目录，避免覆盖已有文件。Mac / Windows 与集群间传输使用 `scp` 或 SFTP，具体见[新生入门（Mac）](../新生入门（Mac）.md)和[新生入门（Windows）](../新生入门（Windows）.md)。

## 七、别名与删除

例如在当前 shell 定义：

```bash
alias ll='ls -alh'
```

希望长期生效时写入当前机器对应的 shell 配置文件，再重新打开终端。别名用于个人方便，提交到仓库的脚本尽量使用完整命令。

删除前先用 `pwd`、`ls` 或 `find` 展示将操作的对象。少量文件可用 `rm -i 文件名`；空目录可用 `rmdir 目录名`。`rm` 没有回收站，避免把带通配符的递归删除命令设成新手默认操作。

不记得参数时用 `man ls`、`man find` 或工具的 `--help`；手册按 `q` 退出。补充资料见 [Linux 命令参考](Linux命令参考.chm)。

## 八、几个顺手的小技巧

| 操作 | 用途 |
| --- | --- |
| `Tab` | 补全路径和命令，减少长文件名输错 |
| `Ctrl+R` | 反向搜索命令历史，输入关键词后先检查再执行 |
| `Ctrl+A` / `Ctrl+E` | 常见终端行编辑配置下移到行首 / 行尾 |
| `Ctrl+C` | 中止当前前台命令；不等于取消已经提交的 PBS 作业 |
| `Ctrl+D` | 在空输入行结束 shell，SSH 中通常意味着退出登录 |
| `cd -` | 回到上一次所在目录，适合两个计算目录间切换 |

历史记录中不要输入密码或 API Key；命令搜回来后尤其检查目录、通配符和作业 ID。

找日志时，可以先找文件再看内容：

```bash
find . -type f -name '*.out' -print
# 先确认路径，再查看某个日志的最后 50 行
# tail -n 50 ./具体目录/program.out
```

想留存命令输出，可用 `程序 2>&1 | tee run.log` 同时显示并保存日志；`tee` 默认覆盖文件，追加用 `tee -a`。管道的退出状态仍按第三节处理。
