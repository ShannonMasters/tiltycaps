#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from generate_stls import ROOT, display_path, quoted, run_openscad


ROWS = ("R1", "R2", "R3", "R4", "Thumb")
STEM_VARIANTS = (
    ("choc-stem", "choc_v1"),
    ("mx-stem", "mx"),
)
DETAIL_HOMING_SLUG = "r3-homing-3-dots"
DETAIL_HOMING_TYPE = "3 dots"

DEFAULT_TEMP_DIR = ROOT / "out" / "readme-mx-spacing-overview"
DEFAULT_OVERVIEW_IMAGE = ROOT / "docs" / "readme-mx-spacing-overview.png"
DEFAULT_DETAIL_IMAGE = ROOT / "docs" / "readme-mx-spacing-r3-detail.png"
BLENDER_HELPER = ROOT / "scripts" / "blender_readme_mx_spacing_overview.py"


def export_defs(row: str, stem_family: str) -> dict[str, str]:
    return {
        "$fa": "2",
        "$fs": "0.12",
        "render_mode": quoted("typing"),
        "low_profile": "true",
        "row": quoted(row),
        "outer_family": quoted("mx"),
        "stem_family": quoted(stem_family),
        "homing_type": quoted("None"),
    }


def export_typing_stls(openscad_bin: str, temp_dir: Path) -> dict[str, Path]:
    stl_root = temp_dir / "stls"
    variant_dirs: dict[str, Path] = {}

    for directory_name, stem_family in STEM_VARIANTS:
        variant_dir = stl_root / f"mx-spacing-{directory_name}"
        variant_dir.mkdir(parents=True, exist_ok=True)
        variant_dirs[directory_name] = variant_dir

        for row in ROWS:
            out_path = variant_dir / f"{row.lower()}.stl"
            run_openscad(openscad_bin, out_path, export_defs(row, stem_family))
            print(f"wrote {display_path(out_path)}")

        detail_out_path = variant_dir / f"{DETAIL_HOMING_SLUG}.stl"
        run_openscad(
            openscad_bin,
            detail_out_path,
            export_defs("R3", stem_family) | {"homing_type": quoted(DETAIL_HOMING_TYPE)},
        )
        print(f"wrote {display_path(detail_out_path)}")

    return variant_dirs


def run_blender(
    blender_bin: str,
    scene_name: str,
    choc_dir: Path,
    mx_dir: Path,
    output_image: Path,
    samples: int,
    resolution_x: int,
    resolution_y: int,
) -> None:
    cmd = [
        blender_bin,
        "-b",
        "-P",
        str(BLENDER_HELPER),
        "--",
        "--scene",
        scene_name,
        "--choc-dir",
        str(choc_dir),
        "--mx-dir",
        str(mx_dir),
        "--output",
        str(output_image),
        "--samples",
        str(samples),
        "--resolution-x",
        str(resolution_x),
        "--resolution-y",
        str(resolution_y),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise RuntimeError("Blender render failed")

    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the README overview render for MX-spacing keycaps with Choc and MX stems."
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=DEFAULT_TEMP_DIR,
        help="Temporary output directory used for the intermediate STL exports.",
    )
    parser.add_argument(
        "--overview-image",
        type=Path,
        default=DEFAULT_OVERVIEW_IMAGE,
        help="Final PNG path for the main lineup render.",
    )
    parser.add_argument(
        "--detail-image",
        type=Path,
        default=DEFAULT_DETAIL_IMAGE,
        help="Final PNG path for the R3 homing detail render.",
    )
    parser.add_argument(
        "--openscad-bin",
        default="openscad",
        help="OpenSCAD executable to use for the temporary STL exports.",
    )
    parser.add_argument(
        "--blender-bin",
        default="blender",
        help="Blender executable to use for the final render.",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=96,
        help="Cycles sample count used for the Blender render.",
    )
    parser.add_argument(
        "--resolution-x",
        type=int,
        default=1800,
        help="Horizontal render resolution in pixels.",
    )
    parser.add_argument(
        "--resolution-y",
        type=int,
        default=860,
        help="Vertical render resolution in pixels for the main lineup render.",
    )
    parser.add_argument(
        "--detail-resolution-x",
        type=int,
        default=1800,
        help="Horizontal render resolution in pixels for the detail render.",
    )
    parser.add_argument(
        "--detail-resolution-y",
        type=int,
        default=760,
        help="Vertical render resolution in pixels for the detail render.",
    )
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def main() -> int:
    args = parse_args()
    temp_dir = resolve_path(args.temp_dir)
    overview_image = resolve_path(args.overview_image)
    detail_image = resolve_path(args.detail_image)

    temp_dir.mkdir(parents=True, exist_ok=True)
    overview_image.parent.mkdir(parents=True, exist_ok=True)
    detail_image.parent.mkdir(parents=True, exist_ok=True)

    variant_dirs = export_typing_stls(args.openscad_bin, temp_dir)
    run_blender(
        blender_bin=args.blender_bin,
        scene_name="overview",
        choc_dir=variant_dirs["choc-stem"],
        mx_dir=variant_dirs["mx-stem"],
        output_image=overview_image,
        samples=args.samples,
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
    )
    run_blender(
        blender_bin=args.blender_bin,
        scene_name="detail",
        choc_dir=variant_dirs["choc-stem"],
        mx_dir=variant_dirs["mx-stem"],
        output_image=detail_image,
        samples=args.samples,
        resolution_x=args.detail_resolution_x,
        resolution_y=args.detail_resolution_y,
    )

    print(f"rendered {display_path(overview_image)}")
    print(f"rendered {display_path(detail_image)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
