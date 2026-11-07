#!/usr/bin/env bash
# 将文件链接到当前目录的直接子目录；Bash 3.2+。
set -euo pipefail

usage() {
  cat <<'HELP'
用法：bash link_to_subdirectories.sh [--dry-run] [--] 文件 ...
将每个文件以原文件名链接到当前目录下的非隐藏直接子目录。
本目录文件使用 ../文件名；其他目录的文件使用绝对路径。
示例：bash link_to_subdirectories.sh --dry-run INCAR KPOINTS
      bash link_to_subdirectories.sh INCAR KPOINTS
已有指向同一文件的链接会跳过；其他同名项（含失效链接）报错，不覆盖。
不进入指向目录的软链接。退出码：0 成功，1 创建失败，2 参数或冲突错误。
HELP
}

die() { printf '错误：%s\n' "$*" >&2; exit 2; }
preview=false
while (($#)); do
  case $1 in
    -h|--help) usage; exit 0 ;;
    --dry-run) preview=true; shift ;;
    --) shift; break ;;
    -*) die "未知选项：$1（以 - 开头的文件名请放在 -- 后）" ;;
    *) break ;;
  esac
done
(($#)) || die '至少提供一个文件；可用 --help 查看示例'
here=$(cd -P . && printf '%s/' "$PWD")
here=${here%/}
sources=()
names=()
targets=()
for file in "$@"; do
  [[ -f $file ]] || die "源文件不存在或不是普通文件：$file"
  name=${file##*/}
  parent=.
  if [[ $file == */* ]]; then parent=${file%/*}; fi
  [[ -n $parent ]] || parent=/
  source_path=$(cd -P -- "$parent" && printf '%s/' "$PWD")$name
  for previous in "${names[@]+${names[@]}}"; do
    [[ $name != "$previous" ]] || die "源文件同名：$name"
  done
  sources+=("$source_path")
  names+=("$name")
  if [[ ${source_path%/*} == "$here" ]]; then
    targets+=("../$name")
  else
    targets+=("$source_path")
  fi
done
shopt -s nullglob
directories=()
for directory in ./*/; do
  [[ ! -L ${directory%/} ]] || continue
  directories+=("${directory%/}")
done
((${#directories[@]})) || die '当前目录下没有可用的非隐藏直接子目录'

# 先检查整个批次，防止已知冲突导致只处理部分目录。
for directory in "${directories[@]}"; do
  for i in "${!sources[@]}"; do
    destination=$directory/${names[i]}
    if [[ -e $destination || -L $destination ]]; then
      [[ -L $destination && $destination -ef ${sources[i]} ]] || die "目标已存在：$destination"
    fi
  done
done
for directory in "${directories[@]}"; do
  for i in "${!sources[@]}"; do
    destination=$directory/${names[i]}
    if [[ -L $destination && $destination -ef ${sources[i]} ]]; then
      printf '已链接，跳过：%q\n' "$destination"
    elif $preview; then
      printf '将创建：%q -> %q\n' "$destination" "${targets[i]}"
    else
      # -n 防止检查之后目标变成目录软链接时，ln 写入其指向的目录。
      ln -sn -- "${targets[i]}" "$destination"
      printf '已创建：%q -> %q\n' "$destination" "${targets[i]}"
    fi
  done
done
