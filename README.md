# fcmp

Check that every file in the source directory tree also exists in the
destination, by comparing filenames across the nested hierarchy.

Built for verifying transcode jobs: after producing proxies from source clips,
confirm no clip was dropped. In a long-running session, corrupted clips can be
skipped silently — this catches those gaps.

> **fcmp does not verify file contents.** Matching is filename-based; there are no
> checksums or hashes. `proxy-frames` mode adds a frame-count check via [mediainfo](https://mediaarea.net/en/MediaInfo)
> to flag truncated or corrupted proxies, which is still a metadata check, never
> byte-level. For true backup or mirror integrity, reach for `rsync -c`, `shasum`,
> or a dedicated dedupe/verification tool.

- **Normal mode** — match by filename (name + extension)
- **Proxy mode** — match video files by basename, ignoring extension
- **Proxy-frames mode** — proxy mode plus frame-count verification

Exports to JSON, TXT, CSV, or HTML (or any combination in a single run).

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for install / run
- `mediainfo` CLI (only for `proxy-frames` mode):

  ```sh
  # macOS
  brew install mediainfo

  # Linux
  sudo apt-get install mediainfo

  # Windows
  # https://mediaarea.net/en/MediaInfo/Download
  ```

## Install

```sh
git clone https://github.com/UserProjekt/File_Compare.git
cd File_Compare
uv sync
```

`uv sync` creates a virtualenv at `.venv/` and installs the package plus its
dependencies. The `fcmp` command is available via `uv run fcmp ...` or by activating
the venv.

## Usage

```
fcmp -a DIR [DIR ...] -b DIR [DIR ...]
     [-m {normal,proxy,proxy-frames}]
     [-f {json,txt,csv,html} ...]
     [-o OUTPUT_DIR] [-q]
```

### Options

| Flag | Description | Default |
| --- | --- | --- |
| `-a`, `--group-a` | One or more directories making up group A | required |
| `-b`, `--group-b` | One or more directories making up group B | required |
| `-m`, `--mode` | `normal`, `proxy`, or `proxy-frames` | `normal` |
| `-f`, `--format` | One or more of `json`, `txt`, `csv`, `html` | `html` |
| `-o`, `--output-dir` | Directory to write reports into | current dir |
| `-q`, `--quiet` | Suppress progress and summary output | off |
| `--version` | Print version and exit | — |

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `2` | Invalid arguments or missing prerequisite (e.g. mediainfo for `proxy-frames`) |

## Examples

```sh
# Simple: compare two directories, write an HTML report to the current dir.
uv run fcmp -a /src -b /backup

# Multiple formats in one run.
uv run fcmp -a /src -b /backup -f html json csv

# Multiple directories per group (supersedes the old "+" syntax).
uv run fcmp -a /part1 /part2 /part3 -b /mirror -o reports/

# Video proxy: match by basename, ignore extension.
uv run fcmp -a /Volumes/Originals -b /Volumes/Proxies -m proxy

# Full proxy verification: basename match + frame-count check.
uv run fcmp -a /Volumes/Originals -b /Volumes/Proxies -m proxy-frames -f html
```

## Real-World Scenarios

**Video Production Workflow:**
```sh
# Compare original footage with proxy files
python file_compare.py -m proxy -f html \
  /Volumes/Storage/Originals \
  /Volumes/EditDrive/Proxies

# Compare original footage with proxy files and export to HTML and JSON
python file_compare.py -m proxy -f html json \
  /Volumes/Storage/Originals \
  /Volumes/EditDrive/Proxies

# Advanced verification with frame count checking
python file_compare.py -m proxyadv -f html \
  /Volumes/Storage/Originals \
  /Volumes/EditDrive/Proxies
```

**Backup Verification:**
```sh
# Verify backup across multiple drives
python file_compare.py -f csv \
  "/Volumes/Backup1+/Volumes/Backup2" \
  /Volumes/Master
```

**Multi-Location Archive:**
```sh
# Compare files from multiple archive locations
python file_compare.py -f json \
  "/Archive/2024/Q1+/Archive/2024/Q2+/Archive/2024/Q3" \
  /CurrentProjects
```

**Quality Control for Proxy Encoding:**
```sh
# Verify all proxies are complete (not truncated)
python file_compare.py -m proxyadv -f html \
  /Production/Camera_Originals \
  /Production/Proxies
```

## Project layout

```
fcmp/
├── pyproject.toml
├── src/fcmp/
│   ├── __init__.py       # __version__
│   ├── __main__.py       # python -m fcmp
│   ├── cli.py            # argparse + rich output
│   ├── scanner.py        # directory walk, FileEntry
│   ├── compare.py        # ComparisonResult, FrameMismatch
│   ├── mediainfo.py      # mediainfo subprocess wrapper
│   ├── filters.py        # skip patterns + video extension set
│   └── exporters.py      # json/txt/csv/html renderers
└── tests/                # pytest suite
```

## Development

```sh
# Install dev deps (pytest + coverage).
uv sync --all-groups

# Run the full test suite.
uv run pytest

# Coverage.
uv run pytest --cov=fcmp --cov-report=term-missing
```
