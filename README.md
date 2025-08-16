# 注意
该仓库中的内容由gpt生成，还没准备好实际工作，实际上目前你可以通过手动使用lib文件夹下的文件来安装lean工具链。
该仓库将会在一周之内（也许）变得可以使用。

# 原理
elan是lean4的工具链管理器，但在网络不稳定时，往往无法正常工作。
本工具旨在不使用elan toolchain link的方式来让lean4用户能手动下载工具链并使用elan安装。
其原理如下：
elan在工作时会向release.lean-lang.org发起请求，主要是两个请求，首先是请求release.lean-lang.org，
这会返回一个json，其中记载了所有的release版本信息。
然后elan会根据这些信息访问release.lean-lang.org下的资源文件，
比如如果请求release.lean-lang.org发现最新的稳定版lean是4.22.0版，那么
```bash
elan toolchain install stable
```
就会请求release.lean-lang.org/lean4/v4.22.0/lean-4.22.0-linux.tar.zst
于是我们可以在本地建立一个https服务器，并修改/etc/hosts使release.lean-lang.org指向本地服务器，
就可以在本地下载lean工具链。

# 用法
pass

# TODO
1.阅览并修改main.py的内容
2.把mirror从当前目录移动到/tmp中工作
3.修改readme，提供更详细的用法说明
4.data_gen只有在stable的情况下正确，需修改
5.声明只支持来自leanprover/lean4的release
6.nightly版本不是从release.lean-lang.org而是从github中获取的，需要修改

# 贡献
```
```
