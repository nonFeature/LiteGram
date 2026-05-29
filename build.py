import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

"""
I don't love using vars like: a b c
but it's really needed here
p - path
f - file
pd - priority dir
"""

# CONFIGURATION
DIST_DIR = Path("dist")
OUTPUT_FILENAME = "LegacyGram.plugin"
SRC_DIR = Path("LegacyGram")
HEADER_FILE = SRC_DIR / "header.py"

PRIORITY_FILES = ["header.py"]
PRIORITY_DIRS = ["data", "i18n", "utils"]
LAST_FILES = ["ui/settings.py", "main.py"]

COPYRIGHT_STRING = (
    "# Open Source LegacyGram plugin for https://exteragram.app\n"
    "# Plugin created by t.me/wepinek\n"
    "# Licensed under the MIT License\n"
    "# Repository: https://github.com/repinek/LegacyGram\n"
)

captured_imports = defaultdict(set)
captured_from_imports = defaultdict(set)


def parse_args():
    parser = argparse.ArgumentParser(description="LegacyGram Build Script")
    parser.add_argument("--no-bump", action="store_true", help="Compatibility flag; build no longer increments the version")
    return parser.parse_args()


def get_current_version() -> tuple[int, int, int] | None:
    content = HEADER_FILE.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if match:
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    return None


def increment_build_version(current_version: tuple[int, int, int]) -> str:
    major, minor, build_num = current_version
    new_version = (major, minor, build_num + 1)

    version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"

    # Update header.py
    content = HEADER_FILE.read_text(encoding="utf-8")
    content = re.sub(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{version_str}"',
        content,
    )
    HEADER_FILE.write_text(content, encoding="utf-8")

    return version_str


def run_linter():
    print("🔍 Running Ruff and ty...")

    subprocess.run(["ruff", "check", ".", "--fix"], capture_output=True)
    subprocess.run(["ruff", "format", "."], capture_output=True)

    result = subprocess.run(["ruff", "check", "."], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Ruff issues found:\n{result.stdout}")
        return False

    ty_result = subprocess.run(["ty", "check"], capture_output=True, text=True)

    if ty_result.returncode != 0:
        print(f"❌ Type issues found:\n{ty_result.stdout}")
        return False

    print("✅ Code is clean. Proceeding to build...")
    return True


def get_all_python_files(src: Path) -> list[Path]:
    return [p.relative_to(src) for p in src.rglob("*.py") if p.name != "__init__.py"]


def get_merge_order(all_files: list[Path]) -> list[Path]:
    order = []
    processed: set[Path] = set()

    # Priority Files
    for pf in PRIORITY_FILES:
        p = Path(pf)
        if p in all_files:
            order.append(p)
            processed.add(p)

    # Priority Directories
    for pd in PRIORITY_DIRS:
        dir_files = sorted([f for f in all_files if f.parts[0] == pd and f not in processed])
        order.extend(dir_files)
        processed.update(dir_files)

    # Everything else (except LAST_FILES)
    last_paths = {Path(f) for f in LAST_FILES}
    others = sorted([f for f in all_files if f not in processed and f not in last_paths])
    order.extend(others)
    processed.update(others)

    # Last Files
    for lf in LAST_FILES:
        p = Path(lf)
        if p in all_files:
            order.append(p)
            processed.add(p)

    return order


def parse_import_line(line: str):
    line = line.strip()

    from_match = re.match(r"^from ([\w.]+) import (.+)$", line)
    if from_match:
        module, names = from_match.groups()
        for name in names.split(","):
            captured_from_imports[module].add(name.strip())
        return

    import_match = re.match(r"^import ([\w.]+)$", line)
    if import_match:
        module = import_match.group(1)
        _ = captured_imports[module]


def normalize_import_block(import_lines: list[str]) -> str:
    block = " ".join(line.strip() for line in import_lines)
    block = re.sub(r"\s+", " ", block)
    block = block.replace("( ", "").replace("(", "").replace(" )", "").replace(")", "")
    return block.strip()


def generate_imports_block() -> str:
    lines = []

    for mod in sorted(captured_imports.keys()):
        lines.append(f"import {mod}")

    for mod in sorted(captured_from_imports.keys()):
        names = sorted(captured_from_imports[mod])
        lines.append(f"from {mod} import {', '.join(names)}")

    return "\n".join(lines) + "\n"


def process_file_content(file_path: Path) -> list[str]:
    """Removes imports, only comments lines, and docstrings"""
    with open(SRC_DIR / file_path, encoding="utf-8") as f:
        lines = f.readlines()

    processed_lines = []
    in_docstring = False
    docstring_char = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for docstring delimiters (both """ and ''')
        if not in_docstring:
            if stripped.startswith('"""'):
                docstring_char = '"""'
            elif stripped.startswith("'''"):
                docstring_char = "'''"
            else:
                docstring_char = None

        if docstring_char and docstring_char in stripped:
            count = stripped.count(docstring_char)
            if count == 1:
                in_docstring = not in_docstring
                i += 1
                continue
            elif count >= 2:
                if not in_docstring:
                    i += 1
                    continue
                else:
                    in_docstring = False
                    docstring_char = None
                    i += 1
                    continue

        # Skip if in docstrings
        if in_docstring:
            i += 1
            continue

        # Skip comment-only lines
        if stripped.startswith("#"):
            i += 1
            continue

        # Skip import lines (but parse them first)
        is_import = stripped.startswith(("import ", "from "))
        is_internal = stripped.startswith(("import LegacyGram", "from LegacyGram"))

        if is_import:
            import_lines = [line]
            open_parens = line.count("(") - line.count(")")
            while open_parens > 0 and i + 1 < len(lines):
                i += 1
                next_line = lines[i]
                import_lines.append(next_line)
                open_parens += next_line.count("(") - next_line.count(")")

            if not is_internal:
                parse_import_line(normalize_import_block(import_lines))
            i += 1
            continue

        processed_lines.append(line)
        i += 1

    file_code = "".join(processed_lines)
    cleaned_code = file_code.strip()
    cleaned_code = re.sub(r"\n{3,}", "\n\n", cleaned_code)

    return [cleaned_code + "\n"]


def build():
    parse_args()
    print(f"🚀 Starting build: {OUTPUT_FILENAME}...")

    if not SRC_DIR.exists():
        print(f"❌ Error: Source directory '{SRC_DIR}' not found!")
        sys.exit(1)

    if not HEADER_FILE.exists():
        print(f"❌ Error: Header file '{HEADER_FILE}' not found!")
        sys.exit(1)

    current_version = get_current_version()
    if not current_version:
        print("❌ Error: Can't find __version__ field in header!")
        sys.exit(1)

    new_version = f"{current_version[0]}.{current_version[1]}.{current_version[2]}"
    print(f"📌 Version: {new_version}")

    if not run_linter():
        sys.exit(1)

    all_files = get_all_python_files(SRC_DIR)
    merge_order = get_merge_order(all_files)

    body_content = []
    for file_path in merge_order:
        print(f"📦 Merging: {file_path}")
        body_content.append(f"\n# === {file_path} ===\n")
        body_content.extend(process_file_content(file_path))

    imports_block = generate_imports_block()
    full_code = COPYRIGHT_STRING + "\n" + imports_block + "".join(body_content)

    DIST_DIR.mkdir(exist_ok=True)
    out_path = DIST_DIR / OUTPUT_FILENAME
    out_path.write_text(full_code, encoding="utf-8")

    print(f"\n🎉 Build successful: {out_path}")


if __name__ == "__main__":
    build()
