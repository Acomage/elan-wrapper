import json
from dataclasses import dataclass
import pathlib
from lib.config import CONFIG, DATA_PATH

resource_file_name = pathlib.Path(DATA_PATH).name


@dataclass
class Release:
    release_type: str
    version: str
    created_at: str

    @staticmethod
    def from_json(data: dict) -> "Release":
        return Release(
            release_type=data["channel"],
            version=data["version"],
            created_at=data["created_at"],
        )

    def to_json(self) -> dict:
        """
        this function generates a fake json
        """
        assets = []
        for arch in [
            "darwin",
            "darwin_aarch64",
            "linux",
            "linux_aarch64",
            "windows",
        ]:
            for ext in [".tar.zst", ".zip"]:
                name = self.name_map(arch, ext)
                url = f"https://release.lean-lang.org/{resource_file_name}"
                assets.append({"name": name, "browser_download_url": url})
        return {
            "name": self.father_name_map(),
            "created_at": self.created_at,
            "assets": assets,
        }

    def name_map(self, arch: str, ext: str) -> str:
        if self.release_type == "nightly":
            date = self.created_at.split("T")[0]
            return f"lean-{self.version}-nightly-{date}-{arch}{ext}"
        else:
            return f"lean-{self.version}-{arch}{ext}"

    def father_name_map(self) -> str:
        if self.release_type == "nightly":
            date = self.created_at.split("T")[0]
            return f"nightly-{date}"
        else:
            return f"v{self.version}"


def data_gen(path: pathlib.Path, release: Release):
    data = {"version": "1", "stable": [], "beta": [], "nightly": []}
    data[release.release_type].append(release.to_json())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def main():
    v4220 = Release.from_json(CONFIG)
    data_gen(pathlib.Path("data/test.json").absolute(), v4220)


if __name__ == "__main__":
    main()
