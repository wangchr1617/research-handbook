# DOVE 加速器配置与使用技巧

**适用环境：macOS / Windows（本机）；Linux（可选的远端代理）。**

先确认 DOVE 可以正常连接，再分别检查浏览器、终端、Docker 和集群程序的代理设置；各处配置可能不同。

## 一、注册、购买和安装

第一次使用先准备可接收邮件的邮箱，从下面的服务入口注册账号，再购买服务、安装客户端：

| 要做什么 | 入口 |
| --- | --- |
| 登录用户中心 | [DOVE 用户中心](https://www.doveapp.net/clientarea.php) |
| 注册账号 | [DOVE 注册页面](https://www.doveapp.net/register.php) |
| 查看套餐、购买和续费 | [购买服务](https://www.doveapp.net/pricing.php)，需先登录 |
| 下载 Windows / Mac 客户端 | [软件下载与帮助中心](https://www.doveapp.net/index.php?rp=/knowledgebase) |

1. 打开注册页，填写邮箱和密码，按网页提示完成验证，再登录用户中心。
2. 进入“购买服务”，比较有效期、流量和同时在线设备数，确认订单金额与续费规则后付款。套餐以登录后的页面为准，下载客户端本身不等于服务已经开通。
3. 打开软件下载页。Mac 先在苹果菜单 → 关于本机查看芯片，再选 Apple 或 Intel 版本；Windows 选择适合系统版本的安装包。
4. Mac 打开下载的安装包，按提示放入“应用程序”；Windows 运行安装程序并完成安装。首次打开后用刚注册的账号登录，等待加载服务与线路。
5. 选择一条线路连接，等客户端显示已连接，再用浏览器打开自己需要访问的网站，确认基本连接可用。

部分入口需要登录，页面也可能显示 DELink 名称。域名变更时，从客户端、用户中心或官方客服获取新入口，不使用搜索广告中的同名下载站。个人订阅链接不要贴进共享笔记。

### 查看代理端口

在客户端设置中查看本地代理的**协议、监听地址和端口**。下面假设 HTTP 代理为 `127.0.0.1:17897`，这只是示例，不是所有版本的默认端口；如果客户端只有 SOCKS5，按对应协议设置。

平时先使用规则分流，校园网和内网地址走直连；全局模式适合临时排查。系统代理通常供浏览器等应用读取，终端环境变量需要单独配置。TUN 模式会改变更广泛的路由，遇到校园 VPN 冲突时先检查规则和路由，不要同时反复切换多个网络工具。

## 二、Mac / Linux 终端使用 HTTP 代理

先用单条命令测试，成功后再设置当前 shell：

```bash
curl -I --connect-timeout 5 --max-time 15 \
  --proxy http://127.0.0.1:17897 https://example.com

export http_proxy=http://127.0.0.1:17897
export https_proxy="$http_proxy"
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$http_proxy"
export no_proxy=localhost,127.0.0.1,::1
export NO_PROXY="$no_proxy"
```

`HTTPS_PROXY` 指 HTTPS 目标请求使用的代理，HTTP 代理的值仍以 `http://` 开头。上述变量只影响当前 shell 启动的程序；从 Dock 打开的应用不一定继承它们。

以 Git 为例，临时执行 `git -c http.proxy=http://127.0.0.1:17897 ls-remote https://github.com/git/git.git HEAD`，就不必改全局 Git 配置。SSH 协议不直接读取 HTTP 代理变量。

用完后关闭当前 shell 的代理：

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
unset no_proxy NO_PROXY
```

如果这些变量原本已有配置，先记录原值，结束时恢复。不要把经常变化的代理地址无条件写入登录脚本。

## 三、Windows PowerShell 使用

下面在 Windows PowerShell 中执行：

```powershell
$env:HTTP_PROXY = 'http://127.0.0.1:17897'
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY = 'localhost,127.0.0.1,::1'
curl.exe -I --connect-timeout 5 --max-time 15 --proxy $env:HTTP_PROXY https://example.com

# 结束后移除本次设置；原本有值的变量应恢复原值
Remove-Item Env:HTTP_PROXY, Env:HTTPS_PROXY, Env:NO_PROXY
```

WSL 的代理地址取决于网络模式：镜像网络可尝试 localhost，NAT 网络通常需要宿主机地址及相应监听、防火墙设置。不要为了让 WSL 联网，直接把全部代理和 DNS 端口开放到所有网卡。

## 四、SOCKS5、浏览器和 Docker

如果客户端提供 SOCKS5，例如端口为 `17898`：

```bash
curl -I --connect-timeout 5 --max-time 15 \
  --proxy socks5h://127.0.0.1:17898 https://example.com
```

`socks5h` 让代理端解析目标域名。不要将这个端口当作 HTTP 代理端口。浏览器按需使用[代理扩展](SwitchyOmega代理配置.md)；插件是否可安装取决于浏览器版本，先检查扩展的维护状态。

Docker 拉取镜像使用 Docker Desktop 的代理设置，容器内部的代理又是另一层。容器中的 `127.0.0.1` 指容器自身，访问 Mac 宿主机可使用 `host.docker.internal`；是否能连接还取决于 DOVE 的监听地址与 Docker 网络，见 [Docker 笔记](Docker安装与使用（Mac）.md)。

## 五、通过 SSH 给远端临时使用

先保证校园 VPN 与 SSH 正常；SSH、PBS 提交和下载本身不需要这个代理。仅在远端需要访问外网且集群允许转发时，在 Mac / Windows OpenSSH 终端执行：

```bash
ssh -N -T -o ExitOnForwardFailure=yes \
  -R 127.0.0.1:27897:127.0.0.1:17897 lab-cluster
```

`lab-cluster` 是 SSH 别名，尚未配置时先按 [Mac SSH 教程](Codex连接科研集群（macOS）.md#配置-ssh)或 [Windows SSH 教程](Alkemie集群部署（Windows）.md#一准备-ssh-与源码)创建并验证登录。保持终端打开，另开终端登录集群，设置当前远端 shell：

```bash
export http_proxy=http://127.0.0.1:27897
export https_proxy="$http_proxy"
export HTTP_PROXY="$http_proxy"
export HTTPS_PROXY="$http_proxy"
curl -I --connect-timeout 5 --max-time 15 https://example.com
```

集群上的 `27897` 经 SSH 转到本机 DOVE 的 `17897`。远端端口只应监听回环地址，可用 `ss -ltn` 检查；端口冲突时换一个端口并同步修改变量，不终止别人的连接。远端服务端策略也可能禁止转发。

用完先在远端取消代理变量，再在隧道终端按 `Ctrl+C`。Mac 休眠、VPN 断开或 DOVE 退出都会使代理失效，已提交的独立 PBS 作业仍由调度器管理。不要让长时间计算依赖笔记本一直在线。

## 六、常见问题

| 现象 | 先检查什么 |
| --- | --- |
| 浏览器正常，终端失败 | 当前 shell 的代理协议和端口 |
| `Connection refused` | 客户端是否运行、是否正在监听这个端口 |
| 超时 | 线路、VPN 路由、代理服务是否可达 |
| 显示 `200 Connection established` 后仍报错 | 后续目标服务器响应和 TLS 错误，不能只看 CONNECT 成功 |
| 证书校验失败 | 系统时间、证书链和单位网络证书，不用关闭校验代替修复 |
| 关闭 DOVE 后工具都断网 | 残留环境变量、Git 全局代理、应用自己的代理设置 |

参数说明见 [curl 官方手册](https://curl.se/docs/manpage.html)和 [OpenSSH 转发说明](https://man.openbsd.org/ssh)。
