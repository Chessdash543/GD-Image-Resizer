#!/usr/bin/env python3
import os
import sys
import shutil
import time
import traceback
from PIL import Image

INPUT_DIR = "input"
OUTPUT_DIR = "output"

SUFFIXES = {
    "high": "-uhd",
    "medium": "-hd",
    "low": "",
}

SCALES = {
    "high": 1.0,
    "medium": 0.5,
    "low": 0.25,
}

VALID_COMMANDS = [
    "high_medium", "high_low",
    "medium_high", "medium_low",
    "low_high", "low_medium",
    "clean", "status",
]

EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff")

G = "\033[1;32m"
C = "\033[1;36m"
Y = "\033[1;33m"
R = "\033[1;31m"
B = "\033[1m"
N = "\033[0m"

def msg(title, text, color):
    print(f"  {color}{title}{N} {text}")


def action(text):
    print(f"  {G}->{N} {text}")


def header(text):
    print(f"  {C}::{N} {B}{text}{N}")


def warn(text):
    print(f"  {Y}!!{N} {text}")


def error(text):
    print(f"  {R}XX{N} {text}")

def logo():
    print("\n   ██████╗ ██████╗     ██╗███╗   ███╗ █████╗  ██████╗ ███████╗")
    print("  ██╔════╝ ██╔══██╗    ██║████╗ ████║██╔══██╗██╔════╝ ██╔════╝")
    print("  ██║  ███╗██║  ██║    ██║██╔████╔██║███████║██║  ███╗█████╗  ")
    print("  ██║   ██║██║  ██║    ██║██║╚██╔╝██║██╔══██║██║   ██║██╔══╝  ")
    print("  ╚██████╔╝██████╔╝    ██║██║ ╚═╝ ██║██║  ██║╚██████╔╝███████╗")
    print("   ╚═════╝ ╚═════╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝")
    print("                                                              ")
    print("  ██████╗ ███████╗███████╗██╗███████╗███████╗██████╗          ")
    print("  ██╔══██╗██╔════╝██╔════╝██║╚══███╔╝██╔════╝██╔══██╗         ")
    print("  ██████╔╝█████╗  ███████╗██║  ███╔╝ █████╗  ██████╔╝         ")
    print("  ██╔══██╗██╔══╝  ╚════██║██║ ███╔╝  ██╔══╝  ██╔══██╗         ")
    print("  ██║  ██║███████╗███████║██║███████╗███████╗██║  ██║         ")
    print("  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝         ")
    print(f"{B}    - A fast Image Resizer to Resize Images of the GD{N}")

def get_files_by_level(level, directory=INPUT_DIR):
    suffix = SUFFIXES[level]
    files = []
    os.makedirs(directory, exist_ok=True)
    header(f"Scanning {directory}/ for {level} files (suffix: '{suffix}')")
    for f in os.listdir(directory):
        if not f.lower().endswith(EXTENSIONS):
            continue
        name, _ = os.path.splitext(f)
        if level == "low":
            if name.endswith(SUFFIXES["high"]) or name.endswith(SUFFIXES["medium"]):
                continue
        else:
            if not name.endswith(suffix):
                continue
        files.append(f)
    action(f"Found {len(files)} file(s) for level '{level}'")
    return files


def change_suffix(filename, from_level, to_level, rename):
    name, ext = os.path.splitext(filename)
    if rename:
        from_suffix = SUFFIXES[from_level]
        to_suffix = SUFFIXES[to_level]
        if from_suffix and name.endswith(from_suffix):
            name = name[: -len(from_suffix)]
        name += to_suffix
    return name + ext


def resize_image(input_path, output_path, scale):
    basename = os.path.basename(input_path)
    action(f"Opening {basename} ...")
    t0 = time.time()
    img = Image.open(input_path)
    action(f"Opened ({img.width}x{img.height}, {time.time() - t0:.1f}s)")
    new_size = (int(img.width * scale), int(img.height * scale))
    action(f"Resizing to {new_size[0]}x{new_size[1]} (scale={scale:.2f}) ...")
    t0 = time.time()
    img_resized = img.resize(new_size, Image.LANCZOS)
    action(f"Resized ({time.time() - t0:.1f}s)")
    t0 = time.time()
    img_resized.save(output_path)
    action(f"Saved {os.path.basename(output_path)} ({time.time() - t0:.1f}s)")


def _print_dir_status(label, directory):
    if not os.path.isdir(directory) or not os.listdir(directory):
        header(f"{label}/ is empty")
        return
    print(f"  {label}/")
    for level in ["high", "medium", "low"]:
        files = get_files_by_level(level, directory)
        suffix = SUFFIXES[level] or "(none)"
        msg(f"[{level}]", f"suffix='{suffix}'  {len(files)} file(s)", B)
        for f in files:
            size = os.path.getsize(os.path.join(directory, f))
            action(f"{f}  ({size:,} bytes)")

    all_images = set()
    for f in os.listdir(directory):
        if f.lower().endswith(EXTENSIONS):
            all_images.add(f)
    others = [f for f in os.listdir(directory) if f not in all_images]
    if others:
        msg("[other]", f"non-image  {len(others)} file(s)", B)
        for f in others:
            size = os.path.getsize(os.path.join(directory, f))
            action(f"{f}  ({size:,} bytes)")

    total = sum(1 for f in os.listdir(directory))
    print(f"  {G}::{N} total: {total} file(s)")


def cmd_status():
    _print_dir_status("input", INPUT_DIR)
    _print_dir_status("output", OUTPUT_DIR)


def cmd_clean():
    header(f"Cleaning {OUTPUT_DIR}/ ...")
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    action(f"Cleaned {OUTPUT_DIR}/")


def get_all_images(directory=INPUT_DIR):
    files = []
    os.makedirs(directory, exist_ok=True)
    for f in os.listdir(directory):
        if f.lower().endswith(EXTENSIONS):
            files.append(f)
    return files


def cmd_resize(from_level, to_level, rename):
    t_start = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    scale = SCALES[to_level] / SCALES[from_level]

    if rename:
        header(f"Converting {from_level} -> {to_level}  (scale={scale:.2f})")
        files = get_files_by_level(from_level)
        if not files:
            warn(f"No {from_level} files found in {INPUT_DIR}/")
            return
    else:
        header(f"Resizing ALL images -> {to_level}  (scale={scale:.2f})")
        files = get_all_images()
        if not files:
            warn(f"No images found in {INPUT_DIR}/")
            return

    for f in files:
        try:
            input_path = os.path.join(INPUT_DIR, f)
            output_name = change_suffix(f, from_level, to_level, rename)
            output_path = os.path.join(OUTPUT_DIR, output_name)
            action(f"Processing: {f} -> {output_name}")
            resize_image(input_path, output_path, scale)
        except Exception:
            error(f"Failed on {f}")
            action(traceback.format_exc().strip())
    elapsed = time.time() - t_start
    msg(G + "::", f"Done! {len(files)} image(s) resized in {elapsed:.1f}s", N)


def print_help():
    print("  Commands:")
    for cmd in VALID_COMMANDS:
        print(f"    {G}->{N} {cmd}")
    print(f"    {G}->{N} help")
    print(f"    {G}->{N} exit")
    print()
    print("  Options (add to command):")
    print(f"    {G}->{N} --rename    Filter by source level suffix AND rename to target suffix")
    print(f"                (without --rename processes ALL images, keeps filenames)")
    print()
    print("  Suffix mapping:")
    for level, suffix in SUFFIXES.items():
        print(f"    {B}{level:8}{N} -> {suffix or '(none)'}")
    print()
    print("  Scale mapping:")
    for level, s in SCALES.items():
        print(f"    {B}{level:8}{N} -> {s}x")
    print()
    print(f"  {C}::{N} Tip: type a command and press Enter")


def execute(command, rename):
    if command == "clean":
        cmd_clean()
    elif command == "status":
        cmd_status()
    elif command in VALID_COMMANDS:
        from_level, to_level = command.split("_")
        cmd_resize(from_level, to_level, rename)
    else:
        warn(f"Unknown command: {command}")


def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if len(sys.argv) >= 2:
        command = sys.argv[1]
        rename = "--rename" in sys.argv
        execute(command, rename)
        return

    logo()
    print()
    while True:
        try:
            raw = input(f"  {C}> {N} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0]
        rename = "--rename" in parts
        if cmd == "exit":
            break
        elif cmd == "help":
            print_help()
        else:
            execute(cmd, rename)
        print()


if __name__ == "__main__":
    main()
