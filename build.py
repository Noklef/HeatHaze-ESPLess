from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parent
    source = root / "src"
    mesh_path = Path("Meshes/rwle/weather/heathaze/heathaze_torus.nif")
    varied_mesh = source / mesh_path.with_name("heathaze_torus_varied.nif")
    mesh = varied_mesh if varied_mesh.is_file() else source / mesh_path
    if not mesh.is_file():
        raise FileNotFoundError(f"Missing mesh: {mesh}")
    output = root / "dist" / "HeatHaze-ESPless.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            if relative.parts[0] == "Meshes":
                continue
            archive.write(path, relative)
        archive.write(mesh, mesh_path)
    print(f"Built {output} (mesh: {mesh.name})")


if __name__ == "__main__":
    main()
