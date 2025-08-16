from lib.config import CONFIG, DATA_PATH
from lib.utils import run_command
from lib.data_gen import data_gen, Release
from pathlib import Path

resource_file_name = Path(DATA_PATH).name


def mirror_gen():
    print("正在创建服务器...")
    server_root = Path("/tmp/lean4_mirror")
    server_root.mkdir(parents=True, exist_ok=True)
    print("正在生成release数据...")
    release = Release.from_json(CONFIG)
    data_gen(server_root / "data.json", release)
    resourse_path = server_root / resource_file_name
    try:
        print(f"正在复制release文件到 {resourse_path} ...")
        run_command(f"cp {DATA_PATH} {resourse_path}")
    except FileNotFoundError:
        print(f"release文件：{DATA_PATH} 不存在")
        exit(1)


if __name__ == "__main__":
    mirror_gen()
