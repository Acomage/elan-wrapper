import sys
import subprocess
from pathlib import Path


def run_command(cmd, check=True):
    """执行shell命令"""
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=True, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {cmd}")
        print(f"错误: {e.stderr}")
        if check:
            sys.exit(1)
        return None


def rm_dir_recursive(path: Path):
    """递归删除目录"""
    if path.exists():
        if path.is_dir():
            for item in path.iterdir():
                rm_dir_recursive(item)
            path.rmdir()
        else:
            path.unlink()
    else:
        print(f"路径 {path} 不存在，无法删除。")
