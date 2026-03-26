#!/usr/bin/env python3

import struct
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "validation"
MAIN = ROOT / "tiltycaps.scad"
EXAMPLES = [
    ROOT / "examples" / "r3-standard.scad",
    ROOT / "examples" / "r1-row-variant.scad",
    ROOT / "examples" / "thumb-row-variant.scad",
    ROOT / "examples" / "mx-stem.scad",
    ROOT / "examples" / "print-pose.scad",
]


CASES = [
    {
        "name": "r1_native_choc",
        "defs": {
            "row": '"R1"',
            "stem_family": '"choc_v1"',
        },
    },
    {
        "name": "r2_native_choc",
        "defs": {
            "row": '"R2"',
            "stem_family": '"choc_v1"',
        },
    },
    {
        "name": "r3_native_choc",
        "defs": {
            "row": '"R3"',
            "stem_family": '"choc_v1"',
        },
    },
    {
        "name": "r4_native_choc",
        "defs": {
            "row": '"R4"',
            "stem_family": '"choc_v1"',
        },
    },
    {
        "name": "thumb_native_choc",
        "defs": {
            "row": '"Thumb"',
            "stem_family": '"choc_v1"',
        },
    },
    {
        "name": "r3_mx_swap",
        "defs": {
            "row": '"R3"',
            "stem_family": '"mx"',
        },
    },
    {
        "name": "r3_choc_spacing",
        "defs": {
            "row": '"R3"',
            "outer_family": '"choc"',
            "stem_family": '"choc_v1"',
        },
    },
    {
        "name": "r3_tall_choc",
        "defs": {
            "row": '"R3"',
            "stem_family": '"choc_v1"',
            "low_profile": "false",
        },
    },
    {
        "name": "r3_tall_mx",
        "defs": {
            "row": '"R3"',
            "stem_family": '"mx"',
            "low_profile": "false",
        },
    },
    {
        "name": "r1_mx_swap",
        "defs": {
            "row": '"R1"',
            "stem_family": '"mx"',
        },
    },
    {
        "name": "r4_mx_swap",
        "defs": {
            "row": '"R4"',
            "stem_family": '"mx"',
        },
    },
    {
        "name": "r2_extra_tilt",
        "defs": {
            "row": '"R2"',
            "stem_family": '"choc_v1"',
            "overall_tilt_deg": "3",
        },
    },
    {
        "name": "r2_print_pose",
        "defs": {
            "row": '"R2"',
            "stem_family": '"choc_v1"',
            "render_mode": '"print"',
        },
    },
    {
        "name": "r3_homing_dot",
        "defs": {
            "row": '"R3"',
            "stem_family": '"choc_v1"',
            "homing_type": '"Dot"',
        },
    },
    {
        "name": "r3_homing_circle_offset",
        "defs": {
            "row": '"R3"',
            "stem_family": '"choc_v1"',
            "homing_type": '"Circle"',
            "homing_offset_y_mm": "0.7",
            "homing_scale": "1.15",
        },
    },
    {
        "name": "r2_homing_line_mx",
        "defs": {
            "row": '"R2"',
            "stem_family": '"mx"',
            "homing_type": '"Line"',
            "homing_offset_y_mm": "-0.5",
        },
    },
]


def run_openscad(source: Path, out_path: Path, defs: dict[str, str] | None = None) -> None:
    cmd = ["openscad", "-o", str(out_path)]
    for key, value in (defs or {}).items():
        cmd.extend(["-D", f"{key}={value}"])
    cmd.append(str(source))
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"OpenSCAD failed for {out_path.name}")


def render_preview(source: Path, out_path: Path, defs: dict[str, str] | None = None) -> None:
    cmd = [
        "openscad",
        "-o",
        str(out_path),
        "--imgsize=1000,750",
        "--autocenter",
        "--viewall",
    ]
    for key, value in (defs or {}).items():
        cmd.extend(["-D", f"{key}={value}"])
    cmd.append(str(source))
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise RuntimeError(f"OpenSCAD preview failed for {out_path.name}")


def try_render_preview(source: Path, out_path: Path, defs: dict[str, str] | None = None) -> None:
    try:
        render_preview(source, out_path, defs)
    except RuntimeError as exc:
        print(f"WARNING: skipping preview export for {out_path.name}: {exc}")


def bounds_binary_stl(path: Path) -> tuple[float, float, float]:
    with path.open("rb") as fh:
        header = fh.read(80)
        count_bytes = fh.read(4)
        if len(count_bytes) != 4:
            raise RuntimeError(f"Invalid STL header in {path}")
        count = struct.unpack("<I", count_bytes)[0]
        mn = [float("inf")] * 3
        mx = [float("-inf")] * 3
        for _ in range(count):
            chunk = fh.read(50)
            if len(chunk) != 50:
                raise RuntimeError(f"Short STL triangle data in {path}")
            pts = struct.unpack("<12fH", chunk)[3:12]
            for i in range(0, 9, 3):
                x, y, z = pts[i : i + 3]
                mn[0] = min(mn[0], x)
                mn[1] = min(mn[1], y)
                mn[2] = min(mn[2], z)
                mx[0] = max(mx[0], x)
                mx[1] = max(mx[1], y)
                mx[2] = max(mx[2], z)
    return mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]


def bounds_ascii_stl(path: Path) -> tuple[float, float, float]:
    mn = [float("inf")] * 3
    mx = [float("-inf")] * 3
    vertex_count = 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line.startswith("vertex "):
                continue
            parts = line.split()
            if len(parts) != 4:
                raise RuntimeError(f"Malformed ASCII STL vertex line in {path}: {line}")
            x, y, z = (float(parts[1]), float(parts[2]), float(parts[3]))
            mn[0] = min(mn[0], x)
            mn[1] = min(mn[1], y)
            mn[2] = min(mn[2], z)
            mx[0] = max(mx[0], x)
            mx[1] = max(mx[1], y)
            mx[2] = max(mx[2], z)
            vertex_count += 1
    if vertex_count == 0:
        raise RuntimeError(f"No vertices found in ASCII STL {path}")
    return mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]


def triangles_ascii_stl(path: Path) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    triangles = []
    current: list[tuple[float, float, float]] = []
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line.startswith("vertex "):
                continue
            _, x, y, z = line.split()
            current.append((float(x), float(y), float(z)))
            if len(current) == 3:
                triangles.append((current[0], current[1], current[2]))
                current = []
    return triangles


def triangles_binary_stl(path: Path) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    triangles = []
    with path.open("rb") as fh:
        fh.read(80)
        count = struct.unpack("<I", fh.read(4))[0]
        for _ in range(count):
            chunk = fh.read(50)
            pts = struct.unpack("<12fH", chunk)[3:12]
            triangles.append(
                (
                    (pts[0], pts[1], pts[2]),
                    (pts[3], pts[4], pts[5]),
                    (pts[6], pts[7], pts[8]),
                )
            )
    return triangles


def triangles_stl(path: Path):
    with path.open("rb") as fh:
        head = fh.read(512)
    if head.startswith(b"solid") and b"facet" in head and b"vertex" in head:
        return triangles_ascii_stl(path)
    return triangles_binary_stl(path)


def bounds_stl(path: Path) -> tuple[float, float, float]:
    with path.open("rb") as fh:
        head = fh.read(512)

    if head.startswith(b"solid") and b"facet" in head and b"vertex" in head:
        return bounds_ascii_stl(path)

    return bounds_binary_stl(path)


def mesh_metrics(path: Path) -> dict[str, float | int]:
    triangles = triangles_stl(path)
    vertices = [v for tri in triangles for v in tri]
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    zs = [v[2] for v in vertices]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    sx = max_x - min_x
    sy = max_y - min_y
    sz = max_z - min_z
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2

    vert_to_tris: dict[tuple[float, float, float], list[int]] = defaultdict(list)
    for idx, tri in enumerate(triangles):
        for vertex in tri:
            vert_to_tris[(round(vertex[0], 5), round(vertex[1], 5), round(vertex[2], 5))].append(idx)

    adjacency = [set() for _ in triangles]
    for triangle_ids in vert_to_tris.values():
        for triangle_id in triangle_ids:
            adjacency[triangle_id].update(other for other in triangle_ids if other != triangle_id)

    seen: set[int] = set()
    component_count = 0
    for idx in range(len(triangles)):
        if idx in seen:
            continue
        component_count += 1
        queue = deque([idx])
        seen.add(idx)
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

    wall_vertices = {
        (round(v[0], 5), round(v[1], 5), round(v[2], 5))
        for v in vertices
        if min_z + sz * 0.22 <= v[2] <= min_z + sz * 0.82
        and (abs(v[0] - cx) >= sx * 0.36 or abs(v[1] - cy) >= sy * 0.32)
    }
    stem_vertices = {
        (round(v[0], 5), round(v[1], 5), round(v[2], 5))
        for v in vertices
        if min_z + sz * 0.08 <= v[2] <= min_z + sz * 0.72
        and abs(v[0] - cx) <= sx * 0.20
        and abs(v[1] - cy) <= sy * 0.20
    }
    stem_heights = [v[2] for v in vertices if (round(v[0], 5), round(v[1], 5), round(v[2], 5)) in stem_vertices]
    stem_span = max(stem_heights) - min(stem_heights) if stem_heights else 0.0

    return {
        "component_count": component_count,
        "wall_vertex_count": len(wall_vertices),
        "stem_vertex_count": len(stem_vertices),
        "stem_span": stem_span,
    }


def validate_export(path: Path, label: str, require_shell_checks: bool = True, require_stem_checks: bool = True) -> None:
    sx, sy, sz = bounds_stl(path)
    print(f"- {label}: {sx:.2f} x {sy:.2f} x {sz:.2f} mm")
    if sx < 10 or sy < 10 or sz < 2:
        raise RuntimeError(f"Suspiciously small bounds for {label}")

    metrics = mesh_metrics(path)
    if metrics["component_count"] != 1:
        raise RuntimeError(f"Disconnected STL components for {label}: {metrics['component_count']}")
    if require_shell_checks and metrics["wall_vertex_count"] < 24:
        raise RuntimeError(f"Missing side-wall geometry for {label}")
    if require_stem_checks and metrics["stem_vertex_count"] < 6:
        raise RuntimeError(f"Missing or collapsed stem geometry for {label}")


def stem_for_example(example: Path) -> str:
    return example.stem.replace("-", "_")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Validating main entrypoint and README examples...")

    main_out = OUT / "main_default.stl"
    run_openscad(MAIN, main_out)
    try_render_preview(MAIN, OUT / "main_default.png")
    validate_export(main_out, "tiltycaps.scad", require_shell_checks=False, require_stem_checks=False)

    for example in EXAMPLES:
        out_path = OUT / f"example_{stem_for_example(example)}.stl"
        run_openscad(example, out_path)
        try_render_preview(example, OUT / f"example_{stem_for_example(example)}.png")
        is_print_case = "print" in example.stem
        validate_export(
            out_path,
            example.relative_to(ROOT).as_posix(),
            require_shell_checks=not is_print_case,
            require_stem_checks=not is_print_case,
        )

    print("Validating representative tiltycaps risk matrix...")
    for case in CASES:
        out_path = OUT / f"{case['name']}.stl"
        run_openscad(MAIN, out_path, case["defs"])
        try_render_preview(MAIN, OUT / f"{case['name']}.png", case["defs"])
        is_print_case = "print" in case["name"]
        validate_export(
            out_path,
            case["name"],
            require_shell_checks=not is_print_case,
            require_stem_checks=not is_print_case,
        )
    print("Validation exports completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
