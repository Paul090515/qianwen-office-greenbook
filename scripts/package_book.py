#!/usr/bin/env python3
"""Package only the reader-facing files of a greenbook project."""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path, PureWindowsPath


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.project.resolve()
    require(root.is_dir(), f"项目目录不存在：{root}")
    manifest_path = root / "manifest.json"
    require(manifest_path.is_file(), f"缺少 manifest：{manifest_path}")
    version = json.loads(manifest_path.read_text(encoding="utf-8")).get("version", "")
    require(isinstance(version, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", version), "manifest.version 只能包含英文字母、数字、点、下划线和连字符，且须以字母或数字开头")
    package_name = f"千问办公绿皮书{version}_完整资料包"
    output = (args.output or root.parent / f"{package_name}.zip").expanduser().resolve()
    require(not output.exists(), f"输出文件已存在，为避免覆盖请指定新路径：{output}")
    md = root / "千问办公绿皮书.md"
    require(md.is_file(), f"缺少可编辑文稿：{md}")
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", md.read_text(encoding="utf-8"))
    files = [
        "index.html", "千问办公绿皮书.html", "千问办公绿皮书.md", "使用说明.md",
        "图片来源.md", "manifest.json", "sources.json", "README.md",
        "practice/活动报名练习.csv", "practice/核对答案.json",
        "practice/工具借还练习.csv", "practice/工具借还核对答案.json",
    ]
    cover = json.loads(manifest_path.read_text(encoding="utf-8")).get("coverIcon")
    files += images
    if cover:
        files.append(cover)
    files = list(dict.fromkeys(files))
    for name in files:
        relative = Path(name)
        require(not relative.is_absolute() and not PureWindowsPath(name).is_absolute(), f"打包路径必须是相对路径：{name}")
        require(".." not in relative.parts and ".." not in PureWindowsPath(name).parts, f"打包路径不能包含上级目录：{name}")
        source = (root / relative).resolve()
        try:
            source.relative_to(root)
        except ValueError:
            raise ValueError(f"打包路径越出项目目录（可能是符号链接）：{name}")
        require(source.is_file(), f"打包所需文件缺失：{name}")
    readme = (root / "README.md").read_text(encoding="utf-8")
    if "SKILL.md" in readme or re.search(r"(?im)^# .*skill\b", readme) or "技能说明" in readme:
        replacement = f"# 千问办公绿皮书 {version}\n\n阅读请打开 `index.html` 或 `千问办公绿皮书.html`；编辑请使用 `千问办公绿皮书.md`，并保留 `assets/` 配图。两组练习 CSV 与核对答案位于 `practice/`。本书案例和练习均为模拟内容。\n"
    else:
        replacement = None
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name + ".tmp")
    require(not temp.exists(), f"临时输出文件已存在：{temp}")
    expected = {}
    try:
        with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for name in files:
                data = (replacement.encode("utf-8") if name == "README.md" and replacement is not None
                        else (root / name).resolve().read_bytes())
                expected[f"{package_name}/{name}"] = data
                zf.writestr(f"{package_name}/{name}", data)
        with zipfile.ZipFile(temp, "r") as zf:
            require(zf.testzip() is None, "ZIP CRC 校验失败")
            require(set(zf.namelist()) == set(expected), "ZIP 条目清单与预期不一致")
            for name, data in expected.items():
                require(zf.read(name) == data, f"ZIP 条目字节校验失败：{name}")
        temp.replace(output)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    size = output.stat().st_size
    print(f"已打包 {len(expected)} 个文件，{size:,} 字节（{size / 1024 / 1024:.2f} MiB）：{output}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"打包失败：{exc}", file=sys.stderr)
        sys.exit(1)
