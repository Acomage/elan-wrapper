from lib.config import CONFIG, DATA_PATH
from lib.utils import run_command
from lib.data_gen import data_gen, Release
from pathlib import Path


def mirror_gen():
    print("正在创建服务器...")
    server_root = Path("mirror").absolute()
    server_root.mkdir(parents=True, exist_ok=True)
    print("正在生成release数据...")
    release = Release.from_json(CONFIG)
    data_gen(server_root / "data.json", release)

    lean4_path = server_root / "lean4"
    lean4_path.mkdir(parents=True, exist_ok=True)
    release_path = lean4_path / f"v{release.version_str}"
    release_path.mkdir(parents=True, exist_ok=True)
    try:
        print(f"正在复制release文件到 {release_path} ...")
        run_command(f"cp {DATA_PATH} {release_path}")
    except FileNotFoundError:
        print(f"release文件：{DATA_PATH} 不存在")
        exit(1)
