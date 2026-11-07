#!/usr/bin/env bash
# 按文件/目录的名称递归清理；Bash 3.2+，兼容 macOS 和 Linux。
set -euo pipefail

usage() {
  cat <<'HELP'
用法：bash remove_by_name.sh [--dry-run | --delete] [--root 目录] [--] 名称模式 ...
默认仅预览；--delete 才删除。模式匹配名称而非完整路径，通配符须加引号。
示例：bash remove_by_name.sh --root calculations CHGCAR WAVECAR '*.tmp'
      bash remove_by_name.sh --delete --root calculations CHGCAR WAVECAR
匹配目录时删除整个目录；不跟随软链接，不删除搜索根目录。
退出码：0 成功（含无匹配），1 操作失败，2 参数错误。
HELP
}

die() { printf '错误：%s\n' "$*" >&2; exit 2; }
mode=preview
selected_mode=''
root=.
while (($#)); do
  case $1 in
    -h|--help) usage; exit 0 ;;
    --dry-run|--delete)
      [[ -z $selected_mode || $selected_mode == "$1" ]] || die '不能同时指定 --dry-run 和 --delete'
      selected_mode=$1
      [[ $1 != --delete ]] || mode=delete
      shift ;;
    --root)
      (($# >= 2)) || die '--root 缺少目录'
      root=$2
      shift 2 ;;
    --) shift; break ;;
    -*) die "未知选项：$1（以 - 开头的名称请放在 -- 后）" ;;
    *) break ;;
  esac
done
(($#)) || die '至少提供一个名称模式；可用 --help 查看示例'
[[ -d $root ]] || die "搜索目录不存在：$root"
root=$(cd -P -- "$root" && printf '%s/' "$PWD")
root=${root%/}
[[ -n $root && $root != / ]] || die '搜索目录不能为 /'
expression=()
for pattern in "$@"; do
  [[ -n $pattern && $pattern != */* ]] || die "模式须为非空名称，不能包含 /：$pattern"
  if ((${#expression[@]})); then expression+=(-o); fi
  expression+=(-name "$pattern")
done

# 先完成查找；查找失败时不开始删除。NUL 分隔保留空格、换行等文件名。
matches=$(mktemp "${TMPDIR:-/tmp}/handbook-find.XXXXXXXX")
trap 'rm -f -- "$matches"' EXIT
find "$root" -mindepth 1 \( "${expression[@]}" \) -prune -print0 > "$matches"
count=0
while IFS= read -r -d '' entry; do
  if [[ $mode == delete ]]; then
    rm -rf -- "$entry"
    printf '已删除：%q\n' "$entry"
  else
    printf '将删除：%q\n' "$entry"
  fi
  count=$((count + 1))
done < "$matches"
printf '匹配 %d 项。\n' "$count"
if [[ $mode == preview ]]; then printf '当前仅预览；添加 --delete 执行删除。\n'; fi
