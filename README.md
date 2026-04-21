# fcmp

Compare two directory trees (or groups of directories) for parity. Built for
video proxy workflows, but works for any backup / mirror verification job.

- **Normal mode** — compare by filename (name + extension)
- **Proxy mode** — compare video files by basename, ignoring extension
- **Proxy-frames mode** — proxy mode plus frame-count verification via
  [mediainfo](https://mediaarea.net/en/MediaInfo), to catch incomplete or
  corrupted proxies

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
dependencies. The `fcmp` command is available via `uv run fcmp ...` or by
activating the venv.

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
