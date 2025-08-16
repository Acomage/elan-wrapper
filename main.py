#!/usr/bin/env python3
"""
Simple orchestrator for the Lean mirror workflow.

Actions performed by --run (in order):
  1. Validate config & DATA_PATH
  2. Generate mirror (lib/mirror_gen.py)
  3. Generate & install local CA + server cert (lib/add_ca.py)
  4. Start HTTPS server (lib/server.py --port PORT) in background
  5. Install & select elan toolchain (elan toolchain install <channel>; elan default <channel>)
  6. Show lean --version
  7. Stop server
  8. Cleanup system trust + hosts entry (lib/clean.py)

Assumptions:
  - config.py provides CONFIG['channel'] and DATA_PATH path exists.
  - elan is installed and on PATH.
  - For port 443 you run this with sudo OR python has CAP_NET_BIND_SERVICE and
    add_ca.py will need sudo for trust store changes.

Use: uv run main.py --run
"""

from __future__ import annotations
import argparse
import os
import signal
import sys
import time
import shutil
import select
import subprocess
from pathlib import Path
from lib.mirror_gen import mirror_gen
from lib.add_ca import add_ca
from lib.config import ELAN_COMMAND
from lib.clean import clean

# Import project config
try:
    from lib.config import CONFIG, DATA_PATH  # type: ignore
except Exception as e:
    print(f"导入配置失败: {e}", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.resolve()
PYTHON = sys.executable


def run_cmd(
    cmd: list[str] | str, *, check: bool = True, capture: bool = False, env=None
):
    if isinstance(cmd, str):
        shell = True
        display = cmd
    else:
        shell = False
        display = " ".join(cmd)
    print(f"[RUN] {display}")
    try:
        if capture:
            out = subprocess.run(
                cmd,
                shell=shell,
                check=check,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
            )
            if out.stdout:
                print(out.stdout.rstrip())
            return out.stdout
        else:
            subprocess.run(cmd, shell=shell, check=check, env=env)
            return ""
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 命令执行失败 (exit {e.returncode}): {display}", file=sys.stderr)
        if e.stdout:
            print(e.stdout, file=sys.stderr)
        if check:
            sys.exit(e.returncode)
        return ""


def ensure_config():
    # Channel
    channel = CONFIG.get("channel")
    if not channel:
        print("未在config.py中设置channel", file=sys.stderr)
        sys.exit(1)
    # Data path
    data_path = Path(DATA_PATH)
    if not data_path.exists():
        print(f"工具链文件不存在: {data_path}", file=sys.stderr)
        sys.exit(1)


def start_server(port: int) -> subprocess.Popen:
    """Start HTTPS server in background."""
    server_path = ROOT / "lib" / "server.py"
    if not server_path.exists():
        print("server.py 不存在，你使用的仓库也许已破损", file=sys.stderr)
        sys.exit(1)
    cmd = [PYTHON, str(server_path), "--port", str(port)]
    print(f"[START SERVER] {' '.join(cmd)} (background)")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    # Wait for readiness (simple heuristic)
    start = time.time()
    ready = False
    while time.time() - start < 10:
        if proc.poll() is not None:
            print("[SERVER ERROR] server process exited early")
            if proc.stdout:
                print(proc.stdout.read())
            sys.exit(1)
        # Read any available lines non-blocking
        if proc.stdout:
            rlist, _, _ = select.select([proc.stdout], [], [], 0)
            if rlist:
                line = proc.stdout.readline()
                if line:
                    print(f"[SERVER] {line.rstrip()}")
                    if "Serving HTTPS" in line:
                        ready = True
                        break
        time.sleep(0.2)
    if not ready:
        print("Server did not confirm readiness within timeout; continuing anyway.")
    return proc


def stop_server(proc: subprocess.Popen):
    if proc.poll() is not None:
        return
    print("[STOP SERVER] Sending SIGINT")
    try:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("[STOP SERVER] Forcing kill")
            proc.kill()
    except Exception as e:
        print(f"[STOP SERVER] Error: {e}")
    if proc.stdout:
        remaining = proc.stdout.read()
        if remaining.strip():
            print("[SERVER OUTPUT REMAINING]")
            print(remaining)


def check_prereqs():
    # elan existence
    if not shutil.which("elan"):
        print("elan 不在PATH中. 可能未下载elan或未添加到环境变量中", file=sys.stderr)
        sys.exit(1)
    # Root / caps note
    if os.geteuid() != 0:
        print(
            "WARNING: 未使用root权限运行\n这可能导致无法启动服务器并暴露443端口\n尝试使用sudo运行"
        )


def orchestrate(port: int):
    ensure_config()
    check_prereqs()

    # 1 mirror generation
    # run_cmd([PYTHON, str(ROOT / "lib" / "mirror_gen.py")])
    mirror_gen()

    # 2 add CA + cert
    # run_cmd([PYTHON, str(ROOT / "lib" / "add_ca.py")])
    add_ca()

    # 3 start server
    server_proc = start_server(port)

    try:
        # 4 elan toolchain install / default
        run_cmd(ELAN_COMMAND)
        run_cmd(["elan", "show"])

    finally:
        # 6 stop server before cleanup
        stop_server(server_proc)

    # 7 cleanup (remove hosts + CA trust copies)
    # run_cmd([PYTHON, str(ROOT / "lib" / "clean.py")])
    clean()

    print("\n[DONE] Orchestration complete.")


def build_parser():
    p = argparse.ArgumentParser(
        prog="lean-mirror-wrapper",
        add_help=False,
        description="Wrapper tool. See README.md for detailed usage.",
    )
    p.add_argument(
        "--run",
        action="store_true",
        help="Run full workflow (mirror -> cert -> server -> elan -> clean)",
    )
    p.add_argument("--help", action="store_true", help="Show this help message")
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.help or (not args.run):
        print(
            "lean-mirror-wrapper\nA simple tool for generating a local Lean mirror, serving it via HTTPS,\ninstalling the configured toolchain with elan, and cleaning system modifications.\n\nyou \033[31mMUST\033[0m read README.md before using this tool.\n\nUsage:\n\tuv run main.py --run\n"
        )
        return

    orchestrate(443)


if __name__ == "__main__":
    main()
