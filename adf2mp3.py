#!/usr/bin/env python3
"""adf2mp3 — Convert GTA Vice City .adf audio files to MP3.

See README.md for detailed usage and notes on the .adf format.
"""

import argparse
import sys
from pathlib import Path

XOR_KEY = 0x22
CHUNK_SIZE = 1 << 20
XOR_TABLE = bytes(b ^ XOR_KEY for b in range(256))
STATION_MIN_SIZE = 20 * 1024 * 1024

MP3_MAGIC = (b"ID3", b"\xff\xfb", b"\xff\xfa", b"\xff\xf3", b"\xff\xf2")

STATION_NAMES = {
    "WAVE": "Wave 103",
    "FLASH": "Flash FM",
    "VROCK": "V-Rock",
    "EMOTION": "Emotion 98.3",
    "KCHAT": "K-Chat",
    "ESPANT": "Radio Espantoso",
    "FEVER": "Fever 105",
    "VCPR": "VCPR",
    "WILD": "Wildstyle",
}


def looks_like_mp3(data: bytes) -> bool:
    """Check whether the leading bytes match an MP3 header."""
    return data.startswith(MP3_MAGIC)


def is_station(path: Path) -> bool:
    """Check whether a file is large enough to be a radio station."""
    try:
        return path.stat().st_size >= STATION_MIN_SIZE
    except OSError as exc:
        print(f"  ! {path}: {exc}", file=sys.stderr)
        return False


def convert(src: Path, dst: Path, force: bool = False) -> bool:
    """Convert one .adf to .mp3. Returns True on success."""
    if dst.exists() and not force:
        print(f"  ! {dst.name} already exists (use --force to overwrite)")
        return False

    tmp = dst.with_name(dst.name + ".part")
    try:
        with src.open("rb") as fin:
            head = fin.read(16)
            if not head:
                print(f"  ! {src.name} is empty")
                return False

            decoded_head = head.translate(XOR_TABLE)
            if not looks_like_mp3(decoded_head):
                if looks_like_mp3(head):
                    print(f"  ! {src.name} is already a plain MP3 — skipped")
                else:
                    print(f"  ! {src.name}: unexpected header after XOR — skipped")
                return False

            dst.parent.mkdir(parents=True, exist_ok=True)
            with tmp.open("wb") as fout:
                fout.write(decoded_head)
                while chunk := fin.read(CHUNK_SIZE):
                    fout.write(chunk.translate(XOR_TABLE))

        tmp.replace(dst)

    except OSError as exc:
        print(f"  ! {src.name}: {exc}", file=sys.stderr)
        tmp.unlink(missing_ok=True)
        return False
    except KeyboardInterrupt:
        tmp.unlink(missing_ok=True)
        raise

    size_mb = dst.stat().st_size / (1024 * 1024)
    label = STATION_NAMES.get(src.stem.upper(), "")
    suffix = f"  [{label}]" if label else ""
    print(f"  ✓ {src.name} → {dst.name}  ({size_mb:.1f} MB){suffix}")
    return True


def collect_sources(paths: list[str], stations_only: bool) -> list[Path]:
    """Expand the arguments into a list of .adf files."""
    sources: list[Path] = []
    for raw in paths:
        p = Path(raw).expanduser()
        if p.is_dir():
            sources.extend(sorted(p.glob("*.[aA][dD][fF]")))
        elif p.is_file():
            sources.append(p)
        else:
            print(f"  ! not found: {p}", file=sys.stderr)

    seen: set[Path] = set()
    unique: list[Path] = []
    for p in sources:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)

    if stations_only:
        unique = [p for p in unique if is_station(p)]

    return unique


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert GTA Vice City .adf files to MP3.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="The .adf files are MP3s XORed with 0x22.",
    )
    parser.add_argument("paths", nargs="+", metavar="FILE|DIR",
                        help="'.adf' files, or the game's Audio/ folder")
    parser.add_argument("-o", "--output", metavar="DIR",
                        help="output directory (default: next to the source)")
    parser.add_argument("-f", "--force", action="store_true",
                        help="overwrite existing files")
    parser.add_argument("--stations", action="store_true",
                        help="only process files >= 20 MB (radio stations)")
    args = parser.parse_args()

    sources = collect_sources(args.paths, args.stations)
    if not sources:
        print("No .adf files to process.", file=sys.stderr)
        return 1

    outdir = Path(args.output).expanduser() if args.output else None
    print(f"{len(sources)} file(s) to convert\n")

    ok = 0
    try:
        for src in sources:
            dst = (outdir or src.parent) / (src.stem + ".mp3")
            if convert(src, dst, force=args.force):
                ok += 1
    except KeyboardInterrupt:
        print(f"\nInterrupted after {ok}/{len(sources)} file(s).", file=sys.stderr)
        return 130

    print(f"\n{ok}/{len(sources)} converted.")
    if ok:
        print("Check with:  ffprobe <file>.mp3   or   mpv <file>.mp3")

    return 0 if ok == len(sources) else 1


if __name__ == "__main__":
    sys.exit(main())
