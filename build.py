import argparse
import ast
import base64
import hashlib
import os
import re
import subprocess
import sys
import urllib.request
import zipfile
import zlib
from collections import defaultdict
from pathlib import Path

if sys.platform == "win32":
    _reconf = getattr(sys.stdout, "reconfigure", None)
    if callable(_reconf):
        _reconf(encoding="utf-8", errors="replace")
    _reconf_err = getattr(sys.stderr, "reconfigure", None)
    if callable(_reconf_err):
        _reconf_err(encoding="utf-8", errors="replace")

"""
I don't love using vars like: a b c
but it's really needed here
p - path
f - file
pd - priority dir
"""

# CONFIGURATION
SCRIPT_DIR = Path(__file__).parent.resolve()
DIST_DIR = SCRIPT_DIR / "dist"
ROOT_DIST_DIR = SCRIPT_DIR.parent.parent
OUTPUT_FILENAME = "LiteGram.plugin"
SRC_DIR = SCRIPT_DIR / "LiteGram"
HEADER_FILE = SRC_DIR / "header.py"

PRIORITY_FILES = ["header.py"]
PRIORITY_DIRS = ["data", "i18n", "utils"]
LAST_FILES = ["ui/settings.py", "main.py"]

COPYRIGHT_STRING = (
    "# Open Source LiteGram plugin for https://exteragram.app\n"
    "# Plugin created by t.me/wepinek\n"
    "# Licensed under the MIT License\n"
    "# Repository: https://github.com/nonFeature/LegacyGram\n"
)

HEADER_WATERMARK = """
#          @@@@@@@@@@
#        @@@@@@@@@@@@
#       @@@@@
#       @@@@
# @@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@
#       @@@@
#       @@@@
#       @@@@
#       @@@@
#       @@@@
#       @@@@
# @@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@
"""

FOOTER_WATERMARK = """
#       @@@@
# @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@
"""

captured_imports = defaultdict(set)
captured_from_imports = defaultdict(set)


def parse_args():
    parser = argparse.ArgumentParser(description="LiteGram Build Script")
    parser.add_argument("--no-bump", action="store_true", help="Compatibility flag; build no longer increments the version")
    parser.add_argument("--no-minify", action="store_true", help="Disable minification entirely (keep comments, docstrings, and type hints)")
    parser.add_argument(
        "--minify-level",
        choices=["light", "medium", "max"],
        default="max",
        help=(
            "Minification level (default: max). "
            "light = remove comments/docstrings/annotations only (AST); "
            "medium = + whitespace compression, no variable renaming; "
            "max = + rename locals, hoist literals (smallest size)"
        ),
    )
    parser.add_argument("--no-lint", action="store_true", help="Disable linter check")
    parser.add_argument("--crlf", action="store_true", help="Use Windows CRLF line endings instead of Unix LF")
    return parser.parse_args()


def get_current_version() -> str | None:
    content = HEADER_FILE.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return None


def increment_version(version: str) -> str:
    match = re.search(r"(\d+)([^\d]*)$", version)
    if match:
        num = int(match.group(1))
        suffix = match.group(2)
        prefix = version[: match.start(1)]
        return f"{prefix}{num + 1}{suffix}"
    return version


def update_header_version(new_version: str) -> None:
    content = HEADER_FILE.read_text(encoding="utf-8")
    content = re.sub(
        r'__version__\s*=\s*"[^"]+"',
        f'__version__ = "{new_version}"',
        content,
    )
    HEADER_FILE.write_text(content, encoding="utf-8")


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
    block = re.sub(r"#.*", "", block)  # Strip inline comments
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
        is_internal = stripped.startswith(("import LiteGram", "from LiteGram"))

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


class ASTMinifier(ast.NodeTransformer):
    """AST transformer that removes docstrings and type annotations to reduce file size."""

    def visit_FunctionDef(self, node):
        node.returns = None
        for arg in node.args.posonlyargs:
            arg.annotation = None
        for arg in node.args.args:
            arg.annotation = None
        if node.args.vararg:
            node.args.vararg.annotation = None
        for arg in node.args.kwonlyargs:
            arg.annotation = None
        if node.args.kwarg:
            node.args.kwarg.annotation = None
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        node.returns = None
        for arg in node.args.posonlyargs:
            arg.annotation = None
        for arg in node.args.args:
            arg.annotation = None
        if node.args.vararg:
            node.args.vararg.annotation = None
        for arg in node.args.kwonlyargs:
            arg.annotation = None
        if node.args.kwarg:
            node.args.kwarg.annotation = None
        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node):
        self.generic_visit(node)
        if node.value is None:
            return None  # Remove variable declarations that have only type hints (e.g. x: int)
        new_node = ast.Assign(targets=[node.target], value=node.value)
        return ast.copy_location(new_node, node)

    def visit_Expr(self, node):
        # Remove docstring statements
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None
        self.generic_visit(node)
        return node

    def visit_Module(self, node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body.pop(0)
        return node

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body.pop(0)
        return node


def check_java():
    try:
        subprocess.run(["java", "-version"], check=True, capture_output=True)
        return "java"
    except Exception:
        pass

    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java_exe = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if java_exe.exists():
            return str(java_exe)

    return None


def get_tools_dir() -> Path:
    local_tools = SCRIPT_DIR / ".tools"
    if (local_tools / "android.jar").exists():
        return local_tools
    sibling_tools = SCRIPT_DIR.parent / "sync_powersaver_repo" / ".tools"
    if (sibling_tools / "android.jar").exists():
        return sibling_tools
    return local_tools


def ensure_xposed_stub_jar(tools_dir: Path) -> Path:
    xposed_jar = tools_dir / "xposed-api.jar"
    if xposed_jar.exists():
        return xposed_jar
    sibling_stub = SCRIPT_DIR.parent / "sync_powersaver_repo" / ".tools" / "xposed-api.jar"
    if sibling_stub.exists():
        import shutil

        shutil.copy2(sibling_stub, xposed_jar)
        return xposed_jar

    stub_dir = tools_dir / "xposed_stub_src" / "de" / "robv" / "android" / "xposed"
    stub_dir.mkdir(parents=True, exist_ok=True)
    (stub_dir / "XC_MethodHook.java").write_text(
        """package de.robv.android.xposed;
import java.lang.reflect.Member;
public abstract class XC_MethodHook {
    public static final int PRIORITY_DEFAULT = 50;
    public final int priority;
    public XC_MethodHook() { this(PRIORITY_DEFAULT); }
    public XC_MethodHook(int priority) { this.priority = priority; }
    protected void beforeHookedMethod(MethodHookParam param) throws Throwable {}
    protected void afterHookedMethod(MethodHookParam param) throws Throwable {}
    public static class MethodHookParam {
        public Member method;
        public Object thisObject;
        public Object[] args;
        private Object result;
        private Throwable throwable;
        public boolean returnEarly;
        public Object getResult() { return result; }
        public void setResult(Object result) { this.result = result; this.throwable = null; this.returnEarly = true; }
        public Throwable getThrowable() { return throwable; }
        public void setThrowable(Throwable throwable) { this.throwable = throwable; this.result = null; this.returnEarly = true; }
        public Object getResultOrThrowable() throws Throwable { if (throwable != null) throw throwable; return result; }
    }
    public static class Unhook {
        public Member getHookedMethod() { return null; }
        public XC_MethodHook getCallback() { return null; }
        public void unhook() {}
    }
}
""",
        encoding="utf-8",
    )
    (stub_dir / "XposedBridge.java").write_text(
        """package de.robv.android.xposed;
import java.lang.reflect.Member;
import java.util.Set;
public final class XposedBridge {
    public static XC_MethodHook.Unhook hookMethod(Member hookMethod, XC_MethodHook callback) { return null; }
    public static Set<XC_MethodHook.Unhook> hookAllMethods(Class<?> hookClass, String methodName, XC_MethodHook callback) { return null; }
    public static Set<XC_MethodHook.Unhook> hookAllConstructors(Class<?> hookClass, XC_MethodHook callback) { return null; }
    public static Object invokeOriginalMethod(Member method, Object thisObject, Object[] args) throws Throwable { return null; }
}
""",
        encoding="utf-8",
    )
    out_dir = tools_dir / "xposed_stub_out"
    out_dir.mkdir(exist_ok=True)
    subprocess.run(
        [
            "javac",
            "-source",
            "8",
            "-target",
            "8",
            str(stub_dir / "XC_MethodHook.java"),
            str(stub_dir / "XposedBridge.java"),
            "-d",
            str(out_dir),
        ],
        check=True,
    )
    subprocess.run(["jar", "cf", str(xposed_jar), "-C", str(out_dir), "."], check=True)
    return xposed_jar


def download_tools(tools_dir: Path):
    tools_dir.mkdir(exist_ok=True)

    kotlinc_dir = tools_dir / "kotlinc"
    if not kotlinc_dir.exists():
        print("Downloading Kotlin Compiler...")
        kt_zip = tools_dir / "kotlinc.zip"
        urllib.request.urlretrieve(
            "https://github.com/JetBrains/kotlin/releases/download/v1.9.22/kotlin-compiler-1.9.22.zip",
            kt_zip,
        )
        print("Extracting Kotlin Compiler...")
        with zipfile.ZipFile(kt_zip, "r") as zip_ref:
            zip_ref.extractall(tools_dir)
        kt_zip.unlink()

    d8_jar = tools_dir / "d8.jar"
    if not d8_jar.exists():
        print("Downloading D8 (R8) compiler...")
        urllib.request.urlretrieve(
            "https://dl.google.com/dl/android/maven2/com/android/tools/r8/8.2.33/r8-8.2.33.jar",
            d8_jar,
        )

    android_jar = tools_dir / "android.jar"
    if not android_jar.exists():
        print("Downloading android.jar (API 33)...")
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/Sable/android-platforms/master/android-33/android.jar",
            android_jar,
        )

    ensure_xposed_stub_jar(tools_dir)


def compile_kotlin_to_dex(minify: bool = False) -> bool:
    kt_files = sorted(set(SRC_DIR.rglob("*.kt")) | set((SCRIPT_DIR / "kotlin").glob("*.kt") if (SCRIPT_DIR / "kotlin").exists() else []))
    if not kt_files:
        return True

    build_dir = SCRIPT_DIR / "build"
    build_dir.mkdir(exist_ok=True)
    hash_file = build_dir / "kt_hash.txt"
    dex_file = SRC_DIR / "data" / "dex.py"

    hash_content = b"".join(f.read_bytes() for f in sorted(kt_files)) + str(minify).encode("utf-8") + b"zlib_v1"
    current_hash = hashlib.md5(hash_content).hexdigest()
    if hash_file.exists() and dex_file.exists():
        if hash_file.read_text(encoding="utf-8").strip() == current_hash:
            print("Kotlin files unchanged. Skipping compilation.")
            return True

    java_exe = check_java()
    if not java_exe:
        print("Java is required to compile Kotlin files. Please install Java and add it to PATH.")
        return False

    tools_dir = get_tools_dir()
    download_tools(tools_dir)

    kotlinc_home = tools_dir / "kotlinc"
    preloader_jar = kotlinc_home / "lib" / "kotlin-preloader.jar"
    compiler_jar = kotlinc_home / "lib" / "kotlin-compiler.jar"
    kt_stdlib_jar = kotlinc_home / "lib" / "kotlin-stdlib.jar"
    android_jar = tools_dir / "android.jar"
    d8_jar = tools_dir / "d8.jar"
    xposed_jar = tools_dir / "xposed-api.jar"

    if not xposed_jar.exists():
        print(f"Xposed stub jar missing at {xposed_jar}")
        return False

    print("Compiling Kotlin sources...")
    jar_path = build_dir / "classes.jar"
    kt_files_str = [str(p) for p in kt_files]
    sep = ";" if os.name == "nt" else ":"
    classpath = f"{android_jar}{sep}{xposed_jar}"

    cmd_kotlinc = [
        java_exe,
        "-cp",
        str(preloader_jar),
        "org.jetbrains.kotlin.preloading.Preloader",
        "-cp",
        str(compiler_jar),
        "org.jetbrains.kotlin.cli.jvm.K2JVMCompiler",
        *kt_files_str,
        "-d",
        str(jar_path),
        "-classpath",
        classpath,
        "-jvm-target",
        "1.8",
    ]
    if minify:
        cmd_kotlinc.extend(
            [
                "-Xno-param-assertions",
                "-Xno-call-assertions",
                "-Xno-receiver-assertions",
            ]
        )

    try:
        subprocess.run(cmd_kotlinc, check=True)
    except Exception as e:
        print(f"Failed to compile Kotlin: {e}")
        return False

    dex_out_dir = build_dir / "dex_out"
    dex_out_dir.mkdir(exist_ok=True)
    for existing in dex_out_dir.glob("*.dex"):
        try:
            existing.unlink()
        except Exception:
            pass

    if minify:
        print("⚡ Minifying and converting to DEX (R8 aggressive mode)...")
        r8_rules_file = build_dir / "r8_rules.pro"
        r8_rules_file.write_text(
            "-dontwarn **\n"
            "-repackageclasses ''\n"
            "-allowaccessmodification\n"
            "-overloadaggressively\n\n"
            "-assumenosideeffects class kotlin.jvm.internal.Intrinsics {\n"
            "    public static void checkNotNullParameter(java.lang.Object, java.lang.String);\n"
            "    public static void checkNotNullExpressionValue(java.lang.Object, java.lang.String);\n"
            "    public static void checkNotNull(java.lang.Object);\n"
            "    public static void checkNotNull(java.lang.Object, java.lang.String);\n"
            "    public static void checkExpressionValueIsNotNull(java.lang.Object, java.lang.String);\n"
            "    public static void checkParameterIsNotNull(java.lang.Object, java.lang.String);\n"
            "}\n\n"
            "-keep class non.feature.litegram.** {\n"
            "    *;\n"
            "}\n\n"
            "-keepclassmembers class * extends de.robv.android.xposed.XC_MethodHook {\n"
            "    protected void beforeHookedMethod(de.robv.android.xposed.XC_MethodHook$MethodHookParam);\n"
            "    protected void afterHookedMethod(de.robv.android.xposed.XC_MethodHook$MethodHookParam);\n"
            "}\n",
            encoding="utf-8",
        )

        stdlib_args = ["--lib", str(kt_stdlib_jar)] if kt_stdlib_jar.exists() else []
        cmd_dex = [
            java_exe,
            "-cp",
            str(d8_jar),
            "com.android.tools.r8.R8",
            str(jar_path),
            "--output",
            str(dex_out_dir),
            "--lib",
            str(android_jar),
            "--lib",
            str(xposed_jar),
            *stdlib_args,
            "--min-api",
            "26",
            "--pg-conf",
            str(r8_rules_file),
            "--release",
            "--no-data-resources",
        ]
    else:
        print("Converting to DEX (D8 debug mode)...")
        cmd_dex = [
            java_exe,
            "-cp",
            str(d8_jar),
            "com.android.tools.r8.D8",
            str(jar_path),
            "--output",
            str(dex_out_dir),
            "--lib",
            str(android_jar),
            "--lib",
            str(xposed_jar),
            "--min-api",
            "26",
        ]

    try:
        subprocess.run(cmd_dex, check=True)
    except Exception as e:
        print(f"Failed to run DEX converter: {e}")
        return False

    dex_path = dex_out_dir / "classes.dex"
    if not dex_path.exists():
        print("classes.dex not found!")
        return False

    try:
        import shutil

        shutil.copy2(dex_path, build_dir / "classes.dex")
    except Exception:
        pass

    with open(dex_path, "rb") as f:
        dex_bytes = f.read()
        dex_hash = hashlib.sha256(dex_bytes).hexdigest()
        compressed_dex = zlib.compress(dex_bytes, 9)
        dex_b64 = base64.b64encode(compressed_dex).decode("utf-8")

    dex_file.parent.mkdir(exist_ok=True)
    with open(dex_file, "w", encoding="utf-8") as f:
        f.write(f'DEX_B64 = "{dex_b64}"  # noqa: E501\n')
        f.write(f'DEX_HASH = "{dex_hash}"\n')

    hash_file.write_text(current_hash, encoding="utf-8")
    print(f"Injected DEX into {dex_file.name} (SHA-256: {dex_hash[:12]}..., raw: {len(dex_bytes) / 1024:.1f} KB, zlib: {len(compressed_dex) / 1024:.1f} KB).")
    return True


def build():
    args = parse_args()
    print(f"🚀 Starting build: {OUTPUT_FILENAME}...")

    if not compile_kotlin_to_dex(minify=not args.no_minify):
        sys.exit(1)

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

    print(f"📌 Version: {current_version}")

    if not args.no_lint:
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
    combined_code = imports_block + "".join(body_content)

    if args.no_minify:
        print("ℹ️ Minification is disabled via --no-minify")
        full_code = COPYRIGHT_STRING + "\n" + combined_code
    else:
        level = args.minify_level
        print(f"⚡ Minifying plugin (level: {level})...")

        if level == "light":
            # AST-only: strip docstrings, type annotations, pass statements
            try:
                tree = ast.parse(combined_code)
                minifier = ASTMinifier()
                minified_tree = minifier.visit(tree)
                minified_code = ast.unparse(minified_tree)
                full_code = COPYRIGHT_STRING + "\n" + minified_code
            except Exception as e:
                print(f"⚠️ Warning: AST minification failed ({e}). Falling back to unminified build.")
                full_code = COPYRIGHT_STRING + "\n" + combined_code
        else:
            # medium / max: use python-minifier
            rename_locals = level == "max"
            hoist_literals = level == "max"
            try:
                import python_minifier

                minified_code = python_minifier.minify(
                    combined_code,
                    rename_globals=False,
                    rename_locals=rename_locals,
                    hoist_literals=hoist_literals,
                    remove_annotations=True,
                    remove_pass=True,
                    remove_literal_statements=True,
                    combine_imports=True,
                )
                full_code = COPYRIGHT_STRING + "\n" + minified_code
            except Exception as e:
                print(f"⚠️ Warning: python-minifier failed ({e}). Falling back to AST minification.")
                try:
                    tree = ast.parse(combined_code)
                    minifier = ASTMinifier()
                    minified_tree = minifier.visit(tree)
                    minified_code = ast.unparse(minified_tree)
                    full_code = COPYRIGHT_STRING + "\n" + minified_code
                except Exception as e2:
                    print(f"⚠️ Warning: AST minification failed ({e2}). Falling back to unminified build.")
                    full_code = COPYRIGHT_STRING + "\n" + combined_code

    full_code = HEADER_WATERMARK + "\n" + full_code + "\n\n" + FOOTER_WATERMARK

    DIST_DIR.mkdir(exist_ok=True)
    out_path = DIST_DIR / OUTPUT_FILENAME

    newline = "\r\n" if args.crlf else "\n"
    out_path.write_text(full_code, encoding="utf-8", newline=newline)

    try:
        ROOT_DIST_DIR.mkdir(exist_ok=True)
        (ROOT_DIST_DIR / OUTPUT_FILENAME).write_text(full_code, encoding="utf-8", newline=newline)
    except Exception:
        pass

    # Calculate actual sizes
    orig_bytes = (HEADER_WATERMARK + "\n" + COPYRIGHT_STRING + "\n" + combined_code + "\n\n" + FOOTER_WATERMARK).replace("\n", newline).encode("utf-8")
    orig_size = len(orig_bytes)
    final_size = out_path.stat().st_size

    print(f"\n🎉 Build successful: {out_path}")

    saved_bytes = orig_size - final_size
    pct = (saved_bytes / orig_size) * 100 if orig_size > 0 else 0

    print(f"📉 Size on disk: {final_size / 1024:.1f} KB (originally {orig_size / 1024:.1f} KB, saved {saved_bytes / 1024:.1f} KB / {pct:.1f}%)")


if __name__ == "__main__":
    build()
