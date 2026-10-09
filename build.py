from pathlib import Path
import shutil


def main():
    root = Path(__file__).resolve().parent
    output = root / "dist" / "HeatHaze-ESPless"
    output.parent.mkdir(exist_ok=True)
    archive = shutil.make_archive(str(output), "zip", root_dir=root / "src")
    print(f"Built {archive}")


if __name__ == "__main__":
    main()
