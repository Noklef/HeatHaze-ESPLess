#!/usr/bin/env python3
"""Randomize speed, rotation direction and phase in the original heathaze_torus.nif.

Uses only Python's standard library. Edits existing NIF fields without
re-exporting the mesh. This is intentionally specific to the original
Fallout: New Vegas Heat Haze NIF (48 independently animated spheres).

Usage: python scripts/heat_haze_variance.py [--seed 42]
"""

import argparse
import math
from pathlib import Path
import random
import struct


# Controller frequency ranges by sphere scale.
DEFAULT_RANGES = {"small": (0.55, 0.80), "medium": (0.35, 0.55), "large": (0.20, 0.35)}


def read_blocks(data):
    """Read block types, starts and sizes; we never rewrite the NIF structure."""
    header = b"Gamebryo File Format, Version 20.2.0.7\n"
    if not data.startswith(header):
        raise ValueError("Not the expected Fallout: New Vegas NIF format")
    pos = len(header)

    def take(fmt):
        nonlocal pos
        values = struct.unpack_from("<" + fmt, data, pos)
        pos += struct.calcsize("<" + fmt)
        return values[0] if len(values) == 1 else values

    if (take("I"), take("B"), take("I")) != (0x14020007, 1, 11):
        raise ValueError("Unexpected NIF version")
    count = take("I")
    if count != 558 or take("I") != 34:
        raise ValueError("Not the expected Heat Haze NIF layout")

    for _ in range(3):  # Bethesda header strings
        size = take("B")
        pos += size
    types = []
    for _ in range(take("H")):
        size = take("I")
        types.append(data[pos:pos + size].decode("ascii"))
        pos += size
    indices = take(f"{count}H")
    sizes = take(f"{count}I")
    string_count = take("I")
    take("I")  # Maximum string length
    for _ in range(string_count):
        size = take("I")
        pos += size
    groups = take("I")
    pos += 4 * groups
    blocks = []
    for type_id, size in zip(indices, sizes):
        if type_id >= len(types) or pos + size > len(data):
            raise ValueError("Invalid NIF block table")
        blocks.append((types[type_id], pos, size))
        pos += size
    if pos + 8 != len(data):
        raise ValueError("Unexpected NIF footer")
    return blocks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, help="Output path (default: *_varied.nif)")
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--reverse-percent", type=float, default=30)
    parser.add_argument("--no-phase", action="store_true", help="Keep original phase values")
    parser.add_argument("--phase-range", nargs=2, type=float, default=(0.0, 1.0),
                        metavar=("MIN", "MAX"), help="Phase range as fractions of one loop")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output")
    for group, (lo, hi) in DEFAULT_RANGES.items():
        parser.add_argument(f"--{group}", nargs=2, type=float, default=(lo, hi), metavar=("MIN", "MAX"))
    args = parser.parse_args()

    ranges = {name: getattr(args, name) for name in DEFAULT_RANGES}
    for name, (low, high) in ranges.items():
        if not (math.isfinite(low) and math.isfinite(high) and 0 < low < high <= 10):
            parser.error(f"Invalid --{name} range: require 0 < MIN < MAX <= 10")
    if not math.isfinite(args.reverse_percent) or not 0 <= args.reverse_percent <= 100:
        parser.error("--reverse-percent must be between 0 and 100")
    pmin, pmax = args.phase_range
    if not (math.isfinite(pmin) and math.isfinite(pmax) and 0 <= pmin <= pmax <= 1):
        parser.error("--phase-range requires 0 <= MIN <= MAX <= 1")

    source = Path(__file__).resolve().parent.parent / "src/Meshes/rwle/weather/heathaze/heathaze_torus.nif"
    target = (args.output or source.with_name(source.stem + "_varied.nif")).resolve()
    if source == target:
        parser.error("Output must differ from input")
    if target.exists() and not args.overwrite:
        parser.error("Output exists; use --overwrite to replace it")

    original = source.read_bytes()
    blocks = read_blocks(original)
    # Read a field within a block, checking its bounds.
    def get(index, fmt, offset):
        kind, start, size = blocks[index]
        if offset < 0 or offset + struct.calcsize("<" + fmt) > size:
            raise ValueError(f"Unexpected {kind} layout (block {index})")
        return struct.unpack_from("<" + fmt, original, start + offset)[0]

    def block_is(index, kind, size):
        return 0 <= index < len(blocks) and blocks[index][0] == kind and blocks[index][2] == size

    # Build node parent links so sphere size includes the 1x/2x/4x parent groups.
    parents, scales = {}, {}
    node_types = {"BSFadeNode", "NiNode", "NiBillboardNode"}
    for node, (kind, _, _) in enumerate(blocks):
        if kind not in node_types:
            continue
        offset = 8 + 4 * get(node, "I", 4)
        scales[node] = get(node, "f", offset + 56)
        for i in range(get(node, "I", offset + 68)):
            child = get(node, "i", offset + 72 + 4 * i)
            if 0 <= child < len(blocks) and blocks[child][0] in node_types:
                if child in parents:
                    raise ValueError("Shared child node in scene graph")
                parents[child] = node

    def world_scale(node):
        value, visited = 1.0, set()
        while node in scales:
            if node in visited:
                raise ValueError("Cycle in scene graph")
            visited.add(node)
            value *= scales[node]
            node = parents.get(node, -1)
        return round(value, 5)

    spheres = []
    for billboard, (kind, _, _) in enumerate(blocks):
        if kind != "NiBillboardNode":
            continue
        offset = 8 + 4 * get(billboard, "I", 4)  # Skip extra-data refs
        child_count = get(billboard, "I", offset + 68)
        if not 1 <= child_count <= 8:
            raise ValueError(f"Unexpected children on billboard {billboard}")
        children = [get(billboard, "i", offset + 72 + 4 * i) for i in range(child_count)]
        nodes = [child for child in children if 0 <= child < len(blocks) and blocks[child][0] == "NiNode"]
        if len(nodes) != 1:
            raise ValueError(f"Expected one animated child node on billboard {billboard}")
        node = nodes[0]
        scale = world_scale(node)
        offset = 8 + 4 * get(node, "I", 4)
        controller = get(node, "i", offset)
        if not block_is(controller, "NiTransformController", 30):
            raise ValueError(f"Unexpected controller on node {node}")
        if get(controller, "i", 22) != node or get(controller, "H", 4) != 0x48:
            raise ValueError(f"Controller {controller} doesn't match expected animation")
        if get(controller, "f", 6) != 1.0 or get(controller, "f", 10) != 0.0:
            raise ValueError("Use the original, unmodified NIF as input")
        interp = get(controller, "i", 26)
        if not block_is(interp, "NiTransformInterpolator", 36):
            raise ValueError(f"Unexpected interpolator on controller {controller}")
        animation = get(interp, "i", 32)
        if not block_is(animation, "NiTransformData", 116):
            raise ValueError(f"Unexpected animation on controller {controller}")
        if (get(animation, "I", 0), get(animation, "I", 4),
                get(animation, "I", 108), get(animation, "I", 112)) != (5, 1, 0, 0):
            raise ValueError(f"Unexpected rotation keys in animation {animation}")
        if not math.isclose(get(controller, "f", 18), 3.33333349, abs_tol=1e-4):
            raise ValueError(f"Unexpected animation duration in controller {controller}")
        spheres.append((controller, animation, scale))

    if (len(spheres) != 48 or len({c for c, _, _ in spheres}) != 48 or
            len({a for _, a, _ in spheres}) != 48 or
            sorted(round(s, 5) for _, _, s in spheres) != [1.5] * 24 + [3.0] * 16 + [6.0] * 8):
        raise ValueError("Expected 48 independent spheres across three size groups")
    curves = {original[blocks[a][1]:blocks[a][1] + 116] for _, a, _ in spheres}
    if len(curves) != 1:
        raise ValueError("Rotation curves differ; use the original NIF")

    spheres.sort()  # Stable output independent of block traversal order
    speed_rng = random.Random(args.seed)
    direction_rng = random.Random(f"direction:{args.seed}")
    phase_rng = random.Random(f"phase:{args.seed}")
    count_reverse = round(len(spheres) * args.reverse_percent / 100)
    reverse = set(direction_rng.sample([c for c, _, _ in spheres], count_reverse))
    changed = bytearray(original)

    for controller, animation, scale in spheres:
        group = {1.5: "small", 3.0: "medium", 6.0: "large"}[scale]
        low, high = ranges[group]
        cpos = blocks[controller][1]
        struct.pack_into("<f", changed, cpos + 6, round(speed_rng.uniform(low, high), 5))
        if not args.no_phase:
            duration = get(controller, "f", 18) - get(controller, "f", 14)
            struct.pack_into("<f", changed, cpos + 10,
                             round(phase_rng.uniform(pmin, pmax) * duration, 5))
        if controller in reverse:
            apos = blocks[animation][1]
            for key in range(5):
                for component in (2, 3, 4):  # Invert quaternion XYZ; keep W and key time
                    offset = apos + 8 + key * 20 + component * 4
                    bits = struct.unpack_from("<I", changed, offset)[0]
                    struct.pack_into("<I", changed, offset, bits ^ 0x80000000)

    # Binary patching must never alter NIF length or block structure.
    if len(changed) != len(original) or read_blocks(changed) != blocks:
        raise AssertionError("NIF structure changed unexpectedly")
    target.write_bytes(changed)
    print(f"Saved: {target} | 48 spheres | {count_reverse} reversed | seed {args.seed}")


if __name__ == "__main__":
    main()
