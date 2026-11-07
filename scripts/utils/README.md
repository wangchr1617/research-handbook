# Shell 辅助工具

适用环境：macOS、Linux；使用 Bash 3.2 或更新版本。以下命令从仓库根目录执行，文件名和目录名中的空格须放在引号内。

## 按名称清理文件或目录

[remove_by_name.sh](remove_by_name.sh) 从指定目录递归匹配名称，支持多个模式，默认只预览：

```bash
bash scripts/utils/remove_by_name.sh --root calculations CHGCAR WAVECAR '*.tmp'
bash scripts/utils/remove_by_name.sh --delete --root calculations CHGCAR WAVECAR '*.tmp'
```

省略 `--root` 时搜索当前目录；模式按名称匹配，不能包含 `/`。`*.tmp` 等通配模式必须加引号，避免被调用者的 Shell 提前展开。匹配目录时会删除整个目录，子项不再单独列出；软链接只处理链接本身，不遍历其指向的目录。搜索根目录自身不会被删除，根目录 `/` 不接受。

旧版直接删除的调用现在改为预览；批量任务需要显式添加 `--delete`。脚本直接传递路径给 `rm`，支持空格、换行和特殊字符，不生成或执行 `name.sh`。无匹配时返回 0；查找失败时不会开始删除，删除失败时返回非零退出码并停止，已经完成的删除不能回滚。

## 链接文件到直接子目录

[link_to_subdirectories.sh](link_to_subdirectories.sh) 在当前目录的非隐藏直接子目录中，为每个源文件建立同名软链接：

```bash
# 在含 INCAR、KPOINTS 和 001/、002/ 等任务目录的位置执行。
bash /path/to/research-handbook/scripts/utils/link_to_subdirectories.sh --dry-run INCAR KPOINTS
bash /path/to/research-handbook/scripts/utils/link_to_subdirectories.sh INCAR KPOINTS
```

当前目录的源文件生成 `../INCAR` 这样的相对链接，整体移动父目录后仍可使用；其他路径的源文件生成绝对链接。源文件须是可访问的普通文件，同一批次不能提供两个同名文件。文件名以 `-` 开头时，在文件列表前加 `--`。

脚本先校验所有源文件和目标：已有指向同一文件的软链接会跳过，普通文件、目录、指向其他文件的链接和失效链接均报错，不覆盖。只遍历一级非隐藏子目录，不进入目录软链接。没有可用子目录时返回非零退出码。执行期间应保持源文件和任务目录稳定；已知冲突会在创建前发现，运行中发生的 I/O 错误则立即停止。

两个工具都支持 `--help`；退出码 0 为成功，2 为参数或预检错误，其他非零值为操作失败。
