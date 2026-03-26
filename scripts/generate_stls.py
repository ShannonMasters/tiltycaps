#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "tiltycaps.scad"
DEFAULT_OUTPUT_DIR = ROOT / "stls"

ROWS = ("R1", "R2", "R3", "R4", "Thumb")
HOMING_VARIANTS = (
    ("dot", "Dot"),
    ("2-dots", "2 dots"),
    ("3-dots", "3 dots"),
    ("circle", "Circle"),
    ("line", "Line"),
)


@dataclass(frozen=True)
class ExportGroup:
    directory_name: str
    outer_family: str
    stem_family: str


EXPORT_GROUPS = (
    ExportGroup("choc-spacing-choc-stem", "choc", "choc_v1"),
    ExportGroup("choc-spacing-mx-stem", "choc", "mx"),
    ExportGroup("mx-spacing-choc-stem", "mx", "choc_v1"),
    ExportGroup("mx-spacing-mx-stem", "mx", "mx"),
)


def quoted(value: str) -> str:
    return f'"{value}"'


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_openscad(openscad_bin: str, out_path: Path, defs: dict[str, str]) -> None:
    cmd = [openscad_bin, "-o", str(out_path)]
    for key, value in defs.items():
        cmd.extend(["-D", f"{key}={value}"])
    cmd.append(str(MAIN))

    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"OpenSCAD failed for {display_path(out_path)}")


def export_defs(group: ExportGroup, row: str, homing_type: str = "None") -> dict[str, str]:
    return {
        "render_mode": quoted("print"),
        "low_profile": "true",
        "row": quoted(row),
        "outer_family": quoted(group.outer_family),
        "stem_family": quoted(group.stem_family),
        "homing_type": quoted(homing_type),
    }


def export_group(openscad_bin: str, output_dir: Path, group: ExportGroup) -> int:
    group_dir = output_dir / group.directory_name
    group_dir.mkdir(parents=True, exist_ok=True)

    export_count = 0
    for row in ROWS:
        out_path = group_dir / f"{row.lower()}.stl"
        run_openscad(openscad_bin, out_path, export_defs(group, row))
        print(f"wrote {display_path(out_path)}")
        export_count += 1

    for slug, homing_type in HOMING_VARIANTS:
        out_path = group_dir / f"r3-homing-{slug}.stl"
        run_openscad(openscad_bin, out_path, export_defs(group, "R3", homing_type))
        print(f"wrote {display_path(out_path)}")
        export_count += 1

    return export_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate print-mode STL batches for the supported spacing/stem combinations."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the generated STL tree will be written.",
    )
    parser.add_argument(
        "--openscad-bin",
        default="openscad",
        help="OpenSCAD executable to use for STL exports.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    total_exports = 0
    for group in EXPORT_GROUPS:
        total_exports += export_group(args.openscad_bin, output_dir, group)

    print(f"generated {total_exports} STL files in {display_path(output_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
