# adf2mp3

Extract the **GTA Vice City** radio stations as playable MP3 files.

The game's `Audio/` folder holds nine `.adf` files of roughly fifty megabytes
each. They are not a proprietary container: they are ordinary MP3 files with
every byte XORed against `0x22`. This script reapplies the XOR and writes a
valid `.mp3` — nothing is re-encoded and no quality is lost, the audio is copied
bit for bit.

One file, no dependencies, Python 3.9 or newer.

## Install

```bash
chmod +x adf2mp3.py
```

## Usage

```
adf2mp3.py [-h] [-o DIR] [-f] [--stations] FILE|DIR [FILE|DIR ...]
```

| Option | Effect |
|---|---|
| `FILE\|DIR` | One or more `.adf` files, or a directory to scan. Required, repeatable. |
| `-o`, `--output DIR` | Output directory, created if missing. By default each `.mp3` is written next to its source. |
| `-f`, `--force` | Overwrite existing `.mp3` files. Without it, a file that is already there is left untouched. |
| `--stations` | Only process files of at least 20 MB, meaning the radio stations. Skips ambient and mission audio. |
| `-h`, `--help` | Show help. |

## Examples

**A single file**, converted in place to `WAVE.mp3`:

```bash
./adf2mp3.py ~/GTA-VC/Audio/WAVE.adf
```

**The whole `Audio/` folder**, with output collected in `~/radio`:

```bash
./adf2mp3.py -o ~/radio ~/GTA-VC/Audio/
```

**The nine stations only**, ignoring everything else:

```bash
./adf2mp3.py --stations -o ~/radio ~/GTA-VC/Audio/
```

```
9 file(s) to convert

  ✓ EMOTION.adf → EMOTION.mp3  (54.1 MB)  [Emotion 98.3]
  ✓ ESPANT.adf → ESPANT.mp3  (56.4 MB)  [Radio Espantoso]
  ✓ FEVER.adf → FEVER.mp3  (57.9 MB)  [Fever 105]
  ✓ FLASH.adf → FLASH.mp3  (54.7 MB)  [Flash FM]
  ✓ KCHAT.adf → KCHAT.mp3  (47.6 MB)  [K-Chat]
  ✓ VCPR.adf → VCPR.mp3  (39.6 MB)  [VCPR]
  ✓ VROCK.adf → VROCK.mp3  (70.9 MB)  [V-Rock]
  ✓ WAVE.adf → WAVE.mp3  (60.5 MB)  [Wave 103]
  ✓ WILD.adf → WILD.mp3  (62.7 MB)  [Wildstyle]

9/9 converted.
Check with:  ffprobe <file>.mp3   or   mpv <file>.mp3
```

**Mixed sources**, files and directories in the same call:

```bash
./adf2mp3.py -o ~/radio ~/GTA-VC/Audio/ ~/backup/VROCK.adf
```

**Re-run a conversion**, overwriting whatever is already there:

```bash
./adf2mp3.py --force -o ~/radio ~/GTA-VC/Audio/
```

**In a script**, relying on the exit status:

```bash
if ./adf2mp3.py --stations -o ~/radio ~/GTA-VC/Audio/; then
    mpv --shuffle ~/radio/*.mp3
fi
```

## The stations

The script recognises the game's filenames and prints the real station name.
Durations and bitrates measured on a PC copy of Vice City:

| File | Station | Length | Bitrate |
|---|---|---:|---:|
| `WAVE.adf` | Wave 103 | 66 min | 128 kb/s |
| `FLASH.adf` | Flash FM | 59 min | 127 kb/s |
| `VROCK.adf` | V-Rock | 77 min | 128 kb/s |
| `EMOTION.adf` | Emotion 98.3 | 59 min | 127 kb/s |
| `KCHAT.adf` | K-Chat | 103 min | 64 kb/s |
| `ESPANT.adf` | Radio Espantoso | 61 min | 128 kb/s |
| `FEVER.adf` | Fever 105 | 63 min | 128 kb/s |
| `VCPR.adf` | VCPR | 86 min | 64 kb/s |
| `WILD.adf` | Wildstyle | 68 min | 127 kb/s |

The two talk stations, K-Chat and VCPR, are encoded at 64 kb/s, which is why
their files are smaller despite running longer.

An unrecognised file still converts normally, just without a label.

## Behaviour

**Validation before writing.** The first sixteen bytes are decoded and checked
against the known MP3 signatures (`ID3`, `FF FB`, `FF FA`, `FF F3`, `FF F2`). If
the result does not match, the file is skipped and nothing is written. An `.adf`
that has already been decoded is detected and reported as such rather than
XORed a second time.

**Atomic writes.** Conversion goes through a temporary `<name>.mp3.part`, which
is renamed to `.mp3` only once it is complete. On a disk error or a keyboard
interrupt the temporary file is removed and any pre-existing `.mp3` survives
untouched. No truncated file is ever left behind — which matters here, because a
cut-off MP3 keeps a valid header and plays without any obvious error.

**Source selection.** Directories are scanned non-recursively with
case-insensitive matching (`.adf`, `.ADF`, `.Adf`). Duplicates are removed after
path resolution. A file passed explicitly is accepted whatever its extension.

**Interruption.** `Ctrl-C` stops cleanly, reports how many files had been
processed, and exits with status 130.

## Exit status

| Code | Meaning |
|---:|---|
| `0` | Every file converted. |
| `1` | At least one failure, or no source found. |
| `130` | Interrupted with `Ctrl-C`. |

A partial success returns `1`: seven files out of nine is a failure from a
calling script's point of view.

## Checking the result

```bash
ffprobe ~/radio/VROCK.mp3      # length, bitrate, channels
mpv ~/radio/VROCK.mp3          # listen
```

## Performance

The XOR runs through `bytes.translate`, which applies a 256-byte table in a
single native pass instead of looping over bytes in Python — about 36 times
faster. The nine stations, a little over 500 MB, convert in under a second on an
NVMe SSD. Reads are done in one-megabyte blocks, so memory use stays flat
regardless of file size.

## Notes on the format

XOR is its own inverse, so the conversion works both ways: running the script on
a plain `.mp3` would produce the matching `.adf`. The header check prevents this
by default, since the result would not look like an MP3.

Other GTA games of the same era use variants of this format. The game also keeps
`.wav` files, plain `.mp3` files, and a several-hundred-megabyte `sfx.RAW` in
`Audio/`, none of which concern this script — `--stations` is the easiest way to
leave them out.

## Legal

This script contains no game data. It only decodes files you already own. The
recordings remain the property of their rights holders: personal use only, no
redistribution.
