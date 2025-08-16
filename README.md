# elan-wrapper
通过本地 HTTPS 镜像离线安装 Lean4 工具链的辅助脚本

<details>
<summary>English README (click to expand)</summary>

# elan-wrapper
Helper scripts to install Lean4 toolchains via a local HTTPS mirror when networks are unreliable.

- Notice: Content is mostly GPT-generated and lightly edited. Not widely tested. Understand what scripts do before running them.
- How it works: Elan queries release.lean-lang.org for the releases JSON and downloads assets like lean-<ver>-linux.tar.zst. This project spins up a local HTTPS server that impersonates release.lean-lang.org so elan can install from local files.
- Applicability: Tested only on CachyOS. Should work on Linux distributions that use /etc/hosts for DNS and keep trust stores in /etc/ca-certificates/trust-source/anchors/ or /usr/local/share/ca-certificates/. On other distros and on Windows/macOS, lib/server.py may still work but you must adjust host and generate/install your own CA and server certs manually.
- Limitations: Nightly channel is fetched from GitHub, not release.lean-lang.org, so it’s currently unsupported. Origin override for elan toolchains is not supported. Only releases from leanprover/lean4 are considered.

## Prerequisites
- Linux
- Python 3.12 (tested on 3.12.11)
- uv (recommended) or a working Python environment
- Ability to edit /etc/hosts and install local CA certificates (may require sudo)

## Usage
1) Decide the Lean version you need. Manually download the toolchain archive (e.g., lean-4.22.0-linux.tar.zst or lean-4.22.0-linux.zip).
2) Visit release.lean-lang.org to find the corresponding release metadata, then update lib/config.py accordingly.
3) From the repo root:
```bash
sudo uv run main.py --run
```
during the script run, it will prompt you to use elan to download the toolchain. Download it as prompted.
Once the download is complete, type `done` to clean up and restore the system.

## Roadmap
- Move mirror workdir to /tmp
- Improve README with more detailed instructions
- Explicitly support only leanprover/lean4 releases
- Support nightly (mirroring GitHub) or dual servers
- Fetch JSON from release.lean-lang.org instead of generating via data_gen
- Better interactive guidance
- i18n
- Refactor

## Contributing
If this helps you install Lean4 more reliably, issues/PRs/tests/feedback are welcome. A star helps more users find and test it.

</details>

## 目录
- [注意](#注意)
- [简介](#简介)
- [工作原理](#工作原理)
- [适用性说明](#适用性说明)
- [限制](#限制)
- [前置条件](#前置条件)
- [用法](#用法)
- [TODO](#todo)
- [贡献](#贡献)

## 注意
本仓库的大部分内容由 GPT 生成并做了少量修改，尚未经过广泛测试。运行前请确保你清楚脚本将执行的操作。

## 简介
elan 是 Lean4 的工具链管理器，但在网络不稳定时往往无法正常工作。该工具通过在本地搭建一个 HTTPS 服务器，配合手动下载工具链，实现无需 elan toolchain link 也能用 elan 安装指定版本的 Lean4。

## 工作原理
- elan 首先请求 release.lean-lang.org，获取包含所有版本信息的 JSON；
- 随后根据该信息从 release.lean-lang.org 下载对应的资源文件（例如 lean-4.22.0-linux.tar.zst）；
- 本项目在本地启动一个 HTTPS 服务器并伪装为 release.lean-lang.org，从而让 elan 从本地文件完成安装。

示例：
```bash
elan toolchain install stable
```
当最新稳定版为 4.22.0 时，elan 将尝试访问：
https://release.lean-lang.org/lean4/v4.22.0/lean-4.22.0-linux.tar.zst

## 适用性说明
- 仅在 CachyOS 上测试过；
- 对于使用 /etc/hosts 管理域名解析，且信任证书目录位于 /etc/ca-certificates/trust-source/anchors/ 或 /usr/local/share/ca-certificates/ 的 Linux 发行版，理论上也可用；
- 对于其他发行版以及 Windows/macOS，lib/server.py 仍可能可用，但需要手动修改 host 并自行签发与安装 CA 和服务器证书。

## 限制
- 不支持 nightly 渠道（nightly 由 GitHub 发布，非 release.lean-lang.org）；
- 不支持使用 elan 指定 toolchain 的 origin；
- 目前仅考虑 leanprover/lean4 的 releases。

## 前置条件
- Linux 环境
- Python 3.12（在 3.12.11 上测试）
- 建议安装 uv；否则可直接用系统 Python
- 需要具备修改 /etc/hosts 与安装本地 CA 证书的权限（可能需要 sudo）

## 用法
1. 确定所需的 Lean 版本，手动下载相应工具链归档（如 lean-4.22.0-linux.tar.zst 或 lean-4.22.0-linux.zip）。
2. 访问 release.lean-lang.org，查找对应版本的发布信息，并据此修改 lib/config.py 中的配置。
3. 在项目根目录运行：
```bash
sudo uv run main.py --run
```
脚本运行时会要求用户使用elan进行下载，在此期间下载即可。
下载完成，输入done即可清理环境，还原系统。


## TODO
1. 将 mirror 的工作目录从当前目录迁移到 /tmp
2. 改进文档，提供更详细的用法说明
3. 明确声明仅支持 leanprover/lean4 的 releases
4. 支持 nightly（从 GitHub 获取）或通过双服务器实现
5. 直接请求 release.lean-lang.org 获取 JSON，而非使用 data_gen 生成
6. 提供更好的交互式引导
7. 可能的 i18n 支持
8. 代码重构

## 贡献
如果你也在安装 Lean4 时屡屡受网络困扰，欢迎贡献你的力量。即使没有编程背景，也可通过测试脚本、反馈问题、改进文档等方式参与。如果该脚本对你有用，欢迎点个 star，帮助项目被更多人看到、测试与改进。

