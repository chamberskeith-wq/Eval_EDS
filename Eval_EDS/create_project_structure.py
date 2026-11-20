
from pathlib import Path

ROOT = Path(".")
OUTPUT = Path("project_structure.txt")

EXCLUDE = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    "build",
    "dist"
}

def write_tree(path, prefix="", lines=None):
    if lines is None:
        lines = []

    entries = sorted(
        [p for p in path.iterdir() if p.name not in EXCLUDE],
        key=lambda p: (p.is_file(), p.name.lower())
    )

    for index, entry in enumerate(entries):
        last = index == len(entries) - 1
        connector = "└── " if last else "├── "

        lines.append(prefix + connector + entry.name)

        if entry.is_dir():
            extension = "    " if last else "│   "
            write_tree(entry, prefix + extension, lines)

    return lines


lines = [ROOT.resolve().name]
lines.extend(write_tree(ROOT))

OUTPUT.write_text("\n".join(lines), encoding="utf-8")

print(f"Created {OUTPUT.resolve()}")
