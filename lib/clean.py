from pathlib import Path
from lib.utils import rm_dir_recursive, run_command

CA_NAME = "local-root-ca"
DOMAIN = "release.lean-lang.org"

DEBIAN_DIR = Path("/usr/local/share/ca-certificates")
P11KIT_DIR = Path("/etc/ca-certificates/trust-source/anchors")
HOSTS = Path("/etc/hosts")


def remove_trusted_ca():
    removed = False
    # Debian / Ubuntu style
    debian_file = DEBIAN_DIR / f"{CA_NAME}.crt"
    if debian_file.exists():
        print(f"删除 {debian_file}")
        run_command(f"sudo rm -f {debian_file}")
        print("更新系统证书存储...")
        run_command("sudo update-ca-certificates")
        removed = True

    # p11-kit style (we copied original rootCA.pem name)
    for fname in ("rootCA.pem", f"{CA_NAME}.crt", "rootCA.crt"):
        f = P11KIT_DIR / fname
        if f.exists():
            print(f"删除 {f}")
            run_command(f"sudo rm -f {f}")
            # Try both refresh commands (ignore failures)
            print("更新系统证书存储...")
            run_command("sudo trust extract-compat", check=False)
            run_command("sudo update-ca-trust", check=False)
            removed = True

    if not removed:
        print("未在系统trust store中找到根CA.")
    else:
        print("系统信任已还原")


def remove_hosts_entry():
    if not HOSTS.exists():
        print("/etc/hosts 不存在")
        return
    try:
        content = HOSTS.read_text(encoding="utf-8").splitlines()
    except PermissionError:
        print(
            "权限不足，请手动处理 /etc/hosts, 即删除添加的 release.lean-lang.org 的条目"
        )
        return

    new_lines = []
    drop_lines = []
    changed = False
    for line in content:
        if line.strip().startswith("#"):
            new_lines.append(line)
            continue
        tokens = line.split()
        if DOMAIN in tokens:
            # Drop entire line if domain present
            changed = True
            drop_lines.append(line)
            continue
        new_lines.append(line)

    if changed:
        tmp_path = Path("/tmp/hosts.cleaned")
        tmp_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print("正在还原/etc/hosts")
        run_command(f"sudo cp {tmp_path} /etc/hosts")
        run_command("rm /tmp/hosts.cleaned")
        print(f"从/etc/hosts 中移除了: {'\n'.join(drop_lines)}")
    else:
        print(f"未在/etc/hosts 中找到包含{DOMAIN}的条目")


def delete_mirror_data():
    print("正在删除服务器...")
    server_root = Path("mirror").absolute()
    rm_dir_recursive(server_root)


def clean():
    print("正在还原系统...")
    remove_trusted_ca()
    remove_hosts_entry()
    delete_mirror_data()
    print("系统已还原")


if __name__ == "__main__":
    clean()
