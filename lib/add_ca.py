from pathlib import Path
from lib.utils import run_command

CA_NAME = "local-root-ca"
CA_CERT_FILENAME = "rootCA.pem"
CA_KEY_FILENAME = "rootCA.key"


def ensure_root_ca(ca_workspace: Path):
    """Create a root CA (key + self-signed cert) if not exist."""
    ca_key = ca_workspace / CA_KEY_FILENAME
    ca_crt = ca_workspace / CA_CERT_FILENAME

    if ca_key.exists() and ca_crt.exists():
        print(f"根CA已存在: {ca_crt}")
        return ca_key, ca_crt

    print("Generating root CA...")
    run_command(f"openssl genrsa -out {ca_key} 4096")
    subj = "/C=CN/ST=Local/L=Local/O=Local Dev/OU=Local CA/CN=Local Root CA"
    run_command(
        "openssl req -x509 -new -nodes "
        f"-key {ca_key} -sha256 -days 3650 -out {ca_crt} -subj '{subj}'"
    )
    run_command(f"chmod 600 {ca_key}")
    run_command(f"chmod 644 {ca_crt}")
    print(f"成功创建根CA: {ca_crt}")
    return ca_key, ca_crt


def generate_server_certificate(
    server_root: Path, domain: str, ca_key: Path, ca_crt: Path
):
    """Generate server key + CSR + CA-signed certificate with SANs."""
    server_key = server_root / "server.key"
    server_csr = server_root / "server.csr"
    server_crt = server_root / "server.crt"
    ext_file = server_root / "server.ext"

    # Always (re)create to match current SAN/domain
    print("正在生成服务器密钥...")
    run_command(f"openssl genrsa -out {server_key} 2048")

    print("正在生成配置文件...")
    ext_content = f"""basicConstraints=CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = {domain}
DNS.2 = localhost
IP.1 = 127.0.0.1
"""
    ext_file.write_text(ext_content, encoding="utf-8")

    print("正在生成CSR...")
    subj = f"/C=CN/ST=Local/L=Local/O=Local Dev/OU=Server/CN={domain}"
    run_command(f"openssl req -new -key {server_key} -out {server_csr} -subj '{subj}'")

    print("正在使用根CA为服务器证书签名...")
    run_command(
        "openssl x509 -req "
        f"-in {server_csr} -CA {ca_crt} -CAkey {ca_key} -CAcreateserial "
        f"-out {server_crt} -days 825 -sha256 -extfile {ext_file}"
    )

    run_command(f"chmod 600 {server_key}")
    run_command(f"chmod 644 {server_crt}")

    print("服务器证书已生成:")
    run_command(f"openssl x509 -in {server_crt} -noout -subject -issuer")
    return server_crt


def add_root_ca_to_system_trust(ca_crt: Path):
    """Add the root CA cert (NOT the leaf) to the system trust store."""
    print("添加根CA至系统信任...")
    # Detect common paths
    debian_path = Path("/usr/local/share/ca-certificates")
    p11kit_path = Path("/etc/ca-certificates/trust-source/anchors")
    if debian_path.exists():
        target = debian_path / f"{CA_NAME}.crt"
        run_command(f"sudo cp {ca_crt} {target}")
        run_command("sudo update-ca-certificates")
    elif p11kit_path.exists():
        target = p11kit_path / ca_crt.name
        run_command(f"sudo cp {ca_crt} {target}")
        # Try both tools; one will succeed depending on distro
        run_command("sudo trust extract-compat", check=False)
        run_command("sudo update-ca-trust", check=False)
    else:
        print("由于您的系统使用未知的trust store机制，本脚本无法自动添加根CA")
        return
    print("根CA已添加")


def verify_certificate(server_crt: Path, domain: str):
    print("\n正在验证服务器证书...")
    run_command(f"openssl x509 -in {server_crt} -subject -issuer -noout")
    print("再次验证服务器证书:")
    run_command(f"openssl verify {server_crt}", check=False)
    print("\n必要时请在服务器启动后使用curl手动测试服务器证书:")
    print(f"curl -v https://{domain}/")


def ensure_hosts_entry(domain: str):
    """Ensure /etc/hosts has 127.0.0.1 domain entry."""
    hosts_path = Path("/etc/hosts")
    entry = f"127.0.0.1  {domain}"
    try:
        if hosts_path.exists():
            text = hosts_path.read_text(encoding="utf-8").splitlines()
            for line in text:
                line_stripped = line.strip()
                if line_stripped.startswith("#"):
                    continue
                if domain in line_stripped.split():
                    print(f"/etc/hosts 中已经存在{domain}")
                    return
    except PermissionError:
        pass
    print(f"添加{domain}至 /etc/hosts ...")
    # Use sudo append only if absent
    run_command(
        f"sudo sh -c \"grep -qw '{domain}' /etc/hosts || echo '{entry}' >> /etc/hosts\""
    )
    print("Host确认完毕.")


def add_ca():
    server_root = Path("/tmp/lean4_mirror")
    domain = "release.lean-lang.org"

    print("正在设置根CA与服务器证书:")
    print(f"  服务器根目录: {server_root}")
    print(f"  域名: {domain}\n")

    ca_key, ca_crt = ensure_root_ca(server_root)
    add_root_ca_to_system_trust(ca_crt)
    server_crt = generate_server_certificate(server_root, domain, ca_key, ca_crt)
    verify_certificate(server_crt, domain)
    ensure_hosts_entry(domain)
    print("\n根CA与服务器签名设置完毕")


if __name__ == "__main__":
    add_ca()
