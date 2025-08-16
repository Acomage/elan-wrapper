import json
from dataclasses import dataclass
import pathlib
from config import CONFIG


@dataclass
class Release:
    release_type: str
    version_str: str
    time: str

    @staticmethod
    def from_json(data: dict) -> "Release":
        return Release(
            release_type=data["channel"],
            version_str=data["version"],
            time=data["time"],
        )

    def to_json(self) -> dict:
        if self.release_type == "stable":
            assets = []
            for arch in [
                "darwin",
                "darwin_aarch64",
                "linux",
                "linux_aarch64",
                "windows",
            ]:
                for ext in [".tar.zst", ".zip"]:
                    name = f"lean-{self.version_str}-{arch}{ext}"
                    url = f"https://release.lean-lang.org/lean4/v{self.version_str}/{name}"
                    assets.append({"name": name, "browser_download_url": url})
            return {
                "name": f"v{self.version_str}",
                "created_at": self.time,
                "assets": assets,
            }
        elif self.release_type == "beta":
            assets = [
                {
                    "name": "CMakeCache.txt",
                    "browser_download_url": f"https://release.lean-lang.org/lean4/v{self.version_str}/CMakeCache.txt",
                },
                {
                    "name": "cmake_install.cmake",
                    "browser_download_url": f"https://release.lean-lang.org/lean4/v{self.version_str}/cmake_install.cmake",
                },
                {
                    "name": "Makefile",
                    "browser_download_url": f"https://release.lean-lang.org/lean4/v{self.version_str}/Makefile",
                },
            ]
            for arch in [
                "darwin",
                "darwin_aarch64",
                "linux",
                "linux_aarch64",
                "windows",
            ]:
                for ext in [".tar.zst", ".zip"]:
                    name = f"lean-{self.version_str}-{arch}{ext}"
                    url = f"https://release.lean-lang.org/lean4/v{self.version_str}/{name}"
                    assets.append({"name": name, "browser_download_url": url})
            return {
                "name": f"v{self.version_str}",
                "created_at": self.time,
                "assets": assets,
            }
        else:
            date = self.time.split("T")[0]
            assets = [
                {
                    "name": "CMakeCache.txt",
                    "browser_download_url": f"https://github.com/leanprover/lean4-nightly/releases/download/nightly-{date}/CMakeCache.txt",
                },
                {
                    "name": "cmake_install.cmake",
                    "browser_download_url": f"https://github.com/leanprover/lean4-nightly/releases/download/nightly-{date}/cmake_install.cmake",
                },
                {
                    "name": "Makefile",
                    "browser_download_url": f"https://github.com/leanprover/lean4-nightly/releases/download/nightly-{date}/Makefile",
                },
            ]
            for arch in [
                "darwin",
                "darwin_aarch64",
                "linux",
                "linux_aarch64",
                "windows",
            ]:
                for ext in [".tar.zst", ".zip"]:
                    name = f"lean-{self.version_str}-nightly-{date}-{arch}{ext}"
                    url = f"https://github.com/leanprover/lean4-nightly/releases/download/nightly-{date}/{name}"
                    assets.append({"name": name, "browser_download_url": url})
            return {
                "name": f"nightly-{date}",
                "created_at": self.time,
                "assets": assets,
            }


def data_gen(path: pathlib.Path, release: Release):
    data = {"version": "1", "stable": [], "beta": [], "nightly": []}
    data[release.release_type].append(release)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, default=lambda r: r.to_json(), indent=4)


def main():
    v4220 = Release.from_json(CONFIG)
    data_gen(pathlib.Path("mirror/data.json").absolute(), v4220)


if __name__ == "__main__":
    main()
