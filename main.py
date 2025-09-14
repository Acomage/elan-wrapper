#!/usr/bin/env python3

from __future__ import annotations
import argparse
import os
import sys
import shutil
import subprocess
from pathlib import Path
from lib.mirror_gen import mirror_gen
from lib.add_ca import add_ca
from lib.clean import clean
from time import sleep

# Import project config
try:
    from lib.config import CONFIG, DATA_PATH  # type: ignore
except Exception as e:
    print(f"导入配置失败: {e}", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.resolve()
PYTHON = sys.executable


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


def orchestrate():
    ensure_config()
    check_prereqs()

    mirror_gen()
    add_ca()

    project_path = Path(".").absolute()
    server_proc = subprocess.Popen(
        ["sudo", "python", "-m", "lib.server", "--port", "443"],
        cwd=project_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    sleep(5)  # Give server time to start
    print("服务器已启动")

    while True:
        print("请再打开一个终端运行elan")
        done = input("一旦你下载完成，请输入done\n")
        if done.strip().lower() == "done":
            break

    print("正在停止服务器")
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
        print("服务器已停止")
    except subprocess.TimeoutExpired:
        print("服务器停止超时，强制终止")
        server_proc.kill()

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

    orchestrate()


if __name__ == "__main__":
    main()
