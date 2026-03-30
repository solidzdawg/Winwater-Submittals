#!/usr/bin/env python3
"""
Winwater Doc Browser & Cache
=============================
Scans both source document locations, displays a tree view, and caches
copies locally so docs are available offline and for the autonomous agent.

Source locations (edit config/paths.json):
  1. ~/Documents/submittal-task/   — project task folders
  2. Z:\\Vendor Parts\\             — company Z: drive vendor docs

Usage:
    python browse-docs.py --list
    python browse-docs.py --list --project "Double-RR"
    python browse-docs.py --list --manufacturer "Watts"
    python browse-docs.py --cache
    python browse-docs.py --cache --project "Double-RR"
    python browse-docs.py --cache --manufacturer "Watts"
    python browse-docs.py --cache --refresh
    python browse-docs.py --status
    python browse-docs.py --open "Watts/Cut Sheets/WATTS_LF25AUB_CutSheet.pdf"

Requirements:
    No extra dependencies — uses Python standard library only.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "paths.json"
CACHE_INDEX_FILE = BASE_DIR / ".doc-cache" / "cache-index.json"

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".png", ".jpg"}


# --------------------------------------------------------------------------- #
# Config                                                                       #
# --------------------------------------------------------------------------- #

def load_config() -> dict:
    defaults = {
        "submittal_task_dir": str(Path.home() / "Documents" / "submittal-task"),
        "z_drive_vendor_parts": "Z:\\Vendor Parts",
        "cache_dir": str(BASE_DIR / ".doc-cache"),
    }
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        for k, v in defaults.items():
            cfg.setdefault(k, v)
        # Expand ~ in paths
        for key in ("submittal_task_dir", "cache_dir"):
            cfg[key] = str(Path(cfg[key]).expanduser())
        return cfg
    return {k: str(Path(v).expanduser()) if "~" in v else v for k, v in defaults.items()}


# --------------------------------------------------------------------------- #
# Cache index                                                                  #
# --------------------------------------------------------------------------- #

def load_cache_index() -> dict:
    if CACHE_INDEX_FILE.exists():
        with open(CACHE_INDEX_FILE) as f:
            return json.load(f)
    return {"cached_files": {}}


def save_cache_index(index: dict):
    CACHE_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Scanning                                                                     #
# --------------------------------------------------------------------------- #

def scan_directory(root: Path, label: str, filter_subdir: str | None = None) -> list[dict]:
    """
    Recursively scan root for supported document files.
    Returns list of dicts with path, size, and mtime metadata.
    """
    docs = []
    if not root.exists():
        return docs
    search_root = (root / filter_subdir) if filter_subdir else root
    if not search_root.exists():
        return docs
    for path in sorted(search_root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                stat = path.stat()
                docs.append({
                    "source_label": label,
                    "source_path": str(path),
                    "relative_path": str(path.relative_to(root)),
                    "size_bytes": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                })
            except (OSError, PermissionError):
                continue
    return docs


# --------------------------------------------------------------------------- #
# Tree display                                                                 #
# --------------------------------------------------------------------------- #

def build_tree(docs: list[dict]) -> dict:
    """Build a nested dict tree from a flat list of doc dicts."""
    tree: dict = {}
    for doc in docs:
        parts = Path(doc["relative_path"]).parts
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = doc
    return tree


def print_tree(
    tree: dict,
    prefix: str = "",
    cache_index: dict | None = None,
    source_label: str = "",
):
    items = list(tree.items())
    for i, (name, value) in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "
        if isinstance(value, dict) and "source_path" not in value:
            print(f"{prefix}{connector}📁 {name}/")
            print_tree(value, prefix + extension, cache_index, source_label)
        else:
            size_kb = value["size_bytes"] / 1024
            cached = False
            if cache_index:
                rel = value["relative_path"]
                entry = cache_index["cached_files"].get(f"{source_label}/{rel}")
                if entry:
                    cached = True
            cache_icon = "💾" if cached else "  "
            print(f"{prefix}{connector}{cache_icon} {name}  ({size_kb:.0f} KB)")


# --------------------------------------------------------------------------- #
# Commands                                                                     #
# --------------------------------------------------------------------------- #

def cmd_list(config: dict, project: str | None, manufacturer: str | None):
    cache_index = load_cache_index()
    task_root = Path(config["submittal_task_dir"])
    zdrive_root = Path(config["z_drive_vendor_parts"])

    print(f"\n{'='*65}")
    print(f"  Winwater Document Browser")
    print(f"{'='*65}")

    # Location 1: submittal task folder
    print(f"\n📂 LOCATION 1 — Submittal Task Folder")
    print(f"   {task_root}")
    if not task_root.exists():
        print("   ⚠️  Path not found. Edit config/paths.json to set the correct path.")
    else:
        docs = scan_directory(task_root, "submittal_task", filter_subdir=project)
        if not docs:
            label = f"project: {project}" if project else "any project"
            print(f"   (no documents found for {label})")
        else:
            print_tree(build_tree(docs), "   ", cache_index, "submittal_task")
            print(f"\n   {len(docs)} document(s) found")

    # Location 2: Z: drive vendor parts
    print(f"\n📂 LOCATION 2 — Z: Drive Vendor Parts")
    print(f"   {zdrive_root}")
    if not zdrive_root.exists():
        print("   ⚠️  Z: drive not accessible. Connect to network or run --cache while connected.")
    else:
        docs = scan_directory(zdrive_root, "z_drive", filter_subdir=manufacturer)
        if not docs:
            label = f"manufacturer: {manufacturer}" if manufacturer else "any manufacturer"
            print(f"   (no documents found for {label})")
        else:
            print_tree(build_tree(docs), "   ", cache_index, "z_drive")
            print(f"\n   {len(docs)} document(s) found")

    print(f"\n  💾 = already cached locally    (no icon) = source only")
    print()


def cmd_cache(config: dict, project: str | None, manufacturer: str | None, refresh: bool):
    cache_dir = Path(config["cache_dir"])
    cache_index = load_cache_index()
    task_root = Path(config["submittal_task_dir"])
    zdrive_root = Path(config["z_drive_vendor_parts"])

    copied = skipped = errors = 0

    def cache_docs_from(root: Path, label: str, filter_subdir: str | None):
        nonlocal copied, skipped, errors
        docs = scan_directory(root, label, filter_subdir=filter_subdir)
        for doc in docs:
            rel = doc["relative_path"]
            cache_key = f"{label}/{rel}"
            dest = cache_dir / label / rel
            entry = cache_index["cached_files"].get(cache_key)

            if not refresh and dest.exists() and entry:
                skipped += 1
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(doc["source_path"], dest)
                digest = sha256_file(dest)
                cache_index["cached_files"][cache_key] = {
                    "source_label": label,
                    "source_path": doc["source_path"],
                    "cached_path": str(dest),
                    "cached_at": datetime.now(tz=timezone.utc).isoformat(),
                    "size_bytes": doc["size_bytes"],
                    "mtime": doc["mtime"],
                    "sha256": digest,
                }
                print(f"  ✅ Cached: {rel}")
                copied += 1
            except (OSError, PermissionError) as e:
                print(f"  ❌ Error: {rel} — {e}")
                errors += 1

    print(f"\n{'='*65}")
    print(f"  Winwater Doc Cache")
    print(f"  Cache dir: {cache_dir}")
    print(f"{'='*65}\n")

    print("Caching from submittal task folder...")
    if task_root.exists():
        cache_docs_from(task_root, "submittal_task", filter_subdir=project)
    else:
        print(f"  ⚠️  Submittal task folder not found: {task_root}")

    print("\nCaching from Z: drive vendor parts...")
    if zdrive_root.exists():
        cache_docs_from(zdrive_root, "z_drive", filter_subdir=manufacturer)
    else:
        print(f"  ⚠️  Z: drive not accessible: {zdrive_root}")

    save_cache_index(cache_index)

    print(f"\n{'='*65}")
    print(f"  Done: {copied} copied, {skipped} already cached, {errors} errors")
    print(f"  Index: {CACHE_INDEX_FILE}")
    print(f"{'='*65}\n")


def cmd_status(config: dict):
    cache_index = load_cache_index()
    entries = cache_index.get("cached_files", {})

    print(f"\n{'='*65}")
    print(f"  Winwater Doc Cache Status")
    print(f"{'='*65}\n")

    if not entries:
        print("  Cache is empty. Run --cache to populate it.\n")
        return

    by_source: dict[str, list] = {}
    for cache_key, meta in entries.items():
        label = meta.get("source_label", "unknown")
        by_source.setdefault(label, []).append((cache_key, meta))

    total_size = 0
    for label, files in sorted(by_source.items()):
        print(f"📂 {label}  ({len(files)} files)")
        for cache_key, meta in sorted(files):
            size_kb = meta.get("size_bytes", 0) / 1024
            cached_at = meta.get("cached_at", "")[:10]
            dest = Path(meta.get("cached_path", ""))
            exists_icon = "✅" if dest.exists() else "❌"
            rel = cache_key.split("/", 1)[-1]
            print(f"   {exists_icon} {rel}  ({size_kb:.0f} KB, cached {cached_at})")
            total_size += meta.get("size_bytes", 0)
        print()

    print(f"  Total: {len(entries)} files, {total_size / 1024 / 1024:.1f} MB")
    print(f"  Index: {CACHE_INDEX_FILE}\n")


def cmd_open(config: dict, doc_path: str):
    """Open a document — tries cached copy first, then source locations."""
    cache_index = load_cache_index()
    cache_dir = Path(config["cache_dir"])

    # Try cache index
    for cache_key, meta in cache_index["cached_files"].items():
        if doc_path in cache_key or cache_key.endswith(doc_path):
            cached_path = Path(meta["cached_path"])
            if cached_path.exists():
                print(f"  Opening cached copy: {cached_path}")
                _open_file(cached_path)
                return
            else:
                print("  ⚠️  Cached file missing — trying source...")

    # Try source locations directly
    for label, key in [("submittal_task", "submittal_task_dir"), ("z_drive", "z_drive_vendor_parts")]:
        root = Path(config[key])
        candidate = root / doc_path
        if candidate.exists():
            print(f"  Opening from source ({label}): {candidate}")
            _open_file(candidate)
            return

    print(f"  ❌ Document not found: {doc_path}")
    print("     Run --list to see available documents.")


def _open_file(path: Path):
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(str(path))
        elif system == "Darwin":
            subprocess.run(["open", str(path)], check=True)
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
    except Exception as e:
        print(f"  ❌ Could not open file: {e}")
        print(f"     File location: {path}")


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #

def main():
    config = load_config()

    parser = argparse.ArgumentParser(
        description="Browse and cache Winwater submittal source documents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python browse-docs.py --list
  python browse-docs.py --list --project "Double-RR"
  python browse-docs.py --list --manufacturer "Watts"
  python browse-docs.py --cache
  python browse-docs.py --cache --manufacturer "Watts" --refresh
  python browse-docs.py --status
  python browse-docs.py --open "Watts/Cut Sheets/WATTS_LF25AUB_CutSheet.pdf"
        """,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true",
                      help="List available documents from both source locations")
    mode.add_argument("--cache", action="store_true",
                      help="Copy documents from sources into local cache")
    mode.add_argument("--status", action="store_true",
                      help="Show cache contents and status")
    mode.add_argument("--open", metavar="DOC_PATH",
                      help="Open a document (tries cache first, then source)")

    parser.add_argument("--project", metavar="NAME",
                        help='Filter task folder by project name (e.g., "Double-RR")')
    parser.add_argument("--manufacturer", metavar="NAME",
                        help='Filter Z: drive by manufacturer name (e.g., "Watts")')
    parser.add_argument("--refresh", action="store_true",
                        help="Re-cache files even if already cached (use with --cache)")

    args = parser.parse_args()

    if args.list:
        cmd_list(config, args.project, args.manufacturer)
    elif args.cache:
        cmd_cache(config, args.project, args.manufacturer, args.refresh)
    elif args.status:
        cmd_status(config)
    elif args.open:
        cmd_open(config, args.open)


if __name__ == "__main__":
    main()
