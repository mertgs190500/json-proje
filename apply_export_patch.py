
import sys, json, pathlib

def merge(a, b):
    # deep merge dict b into a
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict):
            merge(a[k], v)
        else:
            a[k] = v
    return a

def main():
    if len(sys.argv) < 3:
        print("Usage: python apply_export_patch.py <visible.v1.json> <visible.v2.json> [patch.json]")
        sys.exit(1)
    src = pathlib.Path(sys.argv[1])
    dst = pathlib.Path(sys.argv[2])
    patch_path = pathlib.Path(sys.argv[3]) if len(sys.argv) > 3 else pathlib.Path("export_rules_patch.json")

    with src.open("r", encoding="utf-8") as f:
        data = json.load(f)
    with patch_path.open("r", encoding="utf-8") as f:
        patch = json.load(f)

    merged = merge(data, patch)
    with dst.open("w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"Patched -> {dst}")

if __name__ == "__main__":
    main()
