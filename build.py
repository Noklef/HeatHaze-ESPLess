from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parent
    source = root / "src"
    output = root / "dist" / "HeatHaze-ESPless.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source))
    print(f"Built {output}")


if __name__ == "__main__":
    main()
