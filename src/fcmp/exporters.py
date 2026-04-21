from __future__ import annotations

import csv
import html
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from fcmp.compare import ComparisonResult, FrameMismatch

Exporter = Callable[["Report", Path], None]


@dataclass(frozen=True, slots=True)
class Report:
    mode: str
    dirs_a: list[Path]
    dirs_b: list[Path]
    result: ComparisonResult
    generated_at: datetime = field(default_factory=datetime.now)


_MODE_LABELS = {
    "normal": "Normal (compare all files by filename)",
    "proxy": "Proxy (compare video files by basename)",
    "proxy-frames": "Proxy + frames (basename match plus frame-count verification)",
}


def _diff_sort_key(m: FrameMismatch) -> tuple[int, int | str]:
    """Sort numeric differences first (desc), then textual reasons."""
    if isinstance(m.difference, (int, float)):
        return (0, -int(m.difference))
    return (1, str(m.difference))


def _mismatch_to_dict(m: FrameMismatch) -> dict:
    d = asdict(m)
    d["path_a"] = str(m.path_a)
    d["path_b"] = str(m.path_b)
    return d


def export_json(report: Report, path: Path) -> None:
    payload = {
        "mode": report.mode,
        "generated_at": report.generated_at.isoformat(),
        "group_a": {"directories": [str(p) for p in report.dirs_a]},
        "group_b": {"directories": [str(p) for p in report.dirs_b]},
        "unique_in_a": [str(p) for p in report.result.unique_a],
        "unique_in_b": [str(p) for p in report.result.unique_b],
    }
    if report.mode == "proxy-frames":
        payload["frame_mismatches"] = [
            _mismatch_to_dict(m) for m in report.result.frame_mismatches
        ]
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def export_txt(report: Report, path: Path) -> None:
    lines: list[str] = []
    lines.append("File Comparison Report")
    lines.append(f"Mode: {report.mode}")
    lines.append(f"Generated: {report.generated_at.isoformat(timespec='seconds')}")
    lines.append("")

    def _emit_group(label: str, dirs: list[Path], uniques: list[Path]) -> None:
        lines.append(f"{label} ({len(uniques)} item(s))")
        lines.append("Directories:")
        for d in dirs:
            lines.append(f"  - {d}")
        lines.append("Unique items:")
        for p in uniques:
            lines.append(f"  {p}")
        lines.append("")

    _emit_group("Group A only", report.dirs_a, report.result.unique_a)
    _emit_group("Group B only", report.dirs_b, report.result.unique_b)

    if report.mode == "proxy-frames":
        lines.append("=" * 72)
        lines.append(
            f"Frame count mismatches ({len(report.result.frame_mismatches)} item(s))"
        )
        lines.append("=" * 72)
        for m in sorted(report.result.frame_mismatches, key=_diff_sort_key):
            lines.append(f"Basename: {m.basename}")
            lines.append(f"  Group A: {m.file_a} ({m.frames_a} frames)")
            lines.append(f"  Group B: {m.file_b} ({m.frames_b} frames)")
            lines.append(f"  Difference: {m.difference}")
            lines.append(f"  Path A: {m.path_a}")
            lines.append(f"  Path B: {m.path_b}")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def export_csv(report: Report, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Mode", report.mode])
        writer.writerow(
            ["Generated", report.generated_at.isoformat(timespec="seconds")]
        )
        writer.writerow([])
        writer.writerow(["Group A directories", *(str(p) for p in report.dirs_a)])
        writer.writerow(["Group B directories", *(str(p) for p in report.dirs_b)])
        writer.writerow([])
        writer.writerow(["Group", "Path"])
        for p in report.result.unique_a:
            writer.writerow(["A", str(p)])
        for p in report.result.unique_b:
            writer.writerow(["B", str(p)])

        if report.mode == "proxy-frames":
            writer.writerow([])
            writer.writerow(["Frame count mismatches"])
            writer.writerow(
                [
                    "Basename",
                    "File A",
                    "Frames A",
                    "File B",
                    "Frames B",
                    "Difference",
                    "Path A",
                    "Path B",
                ]
            )
            for m in sorted(report.result.frame_mismatches, key=_diff_sort_key):
                writer.writerow(
                    [
                        m.basename,
                        m.file_a,
                        m.frames_a,
                        m.file_b,
                        m.frames_b,
                        m.difference,
                        str(m.path_a),
                        str(m.path_b),
                    ]
                )


_HTML_STYLE = """
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    margin: 20px;
    line-height: 1.5;
    color: #333;
}
table { border-collapse: collapse; width: 100%; margin: 10px 0 40px; }
th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
th { background-color: #f2f2f2; font-weight: 600; }
.group-a { background-color: #ffeeee; }
.group-b { background-color: #eef4fb; }
.mismatch { background-color: #fff3cd; }
.path-header {
    background-color: #f8f9fa; padding: 20px; border-radius: 6px;
    margin: 30px 0; border: 1px solid #ddd;
}
.path-header h3 { margin: 0 0 10px 0; font-size: 1.2em; color: #333; }
.path-text {
    background-color: #fff; padding: 10px; border-radius: 4px;
    border: 1px solid #ddd; word-break: break-all; margin-bottom: 5px;
}
.section { margin-bottom: 40px; }
.mode-info {
    background-color: #e9ecef; padding: 10px 20px; border-radius: 4px;
    margin-bottom: 20px; border: 1px solid #dee2e6; display: inline-block;
}
.warning-box {
    background-color: #fff3cd; border: 1px solid #ffc107;
    border-radius: 6px; padding: 20px; margin: 30px 0;
}
.warning-box h3 { margin: 0 0 15px 0; color: #856404; }
.ok-box {
    background-color: #d4edda; border: 1px solid #c3e6cb;
    border-radius: 6px; padding: 20px; margin: 30px 0;
}
.ok-box h3 { margin: 0 0 15px 0; color: #155724; }
"""


def _fmt_num(value: int | float | str | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:,}"
    return str(value)


def _dirs_html(dirs: list[Path]) -> str:
    return "".join(f'<div class="path-text">{html.escape(str(d))}</div>' for d in dirs)


def _mismatches_html(mismatches: list[FrameMismatch]) -> str:
    if not mismatches:
        return """
<div class="section">
  <div class="ok-box">
    <h3>Frame counts all match</h3>
    <p>Every shared basename has matching frame counts.</p>
  </div>
</div>
"""
    rows = "".join(
        f"""
<tr class="mismatch">
  <td>{html.escape(m.basename)}</td>
  <td>{html.escape(m.file_a)}</td>
  <td>{_fmt_num(m.frames_a)}</td>
  <td>{html.escape(m.file_b)}</td>
  <td>{_fmt_num(m.frames_b)}</td>
  <td><strong>{_fmt_num(m.difference)}</strong></td>
</tr>"""
        for m in sorted(mismatches, key=_diff_sort_key)
    )
    return f"""
<div class="section">
  <div class="warning-box">
    <h3>Frame count mismatches ({len(mismatches)} item(s))</h3>
    <p>Shared basenames with differing frame counts — likely incomplete or corrupted proxies.</p>
  </div>
  <table>
    <tr>
      <th>Basename</th><th>File A</th><th>Frames A</th>
      <th>File B</th><th>Frames B</th><th>Difference</th>
    </tr>{rows}
  </table>
</div>
"""


def export_html(report: Report, path: Path) -> None:
    mode_label = _MODE_LABELS.get(report.mode, report.mode)

    mismatch_section = (
        _mismatches_html(report.result.frame_mismatches)
        if report.mode == "proxy-frames"
        else ""
    )

    rows_a = "".join(
        f'<tr class="group-a"><td>{html.escape(str(p))}</td></tr>'
        for p in report.result.unique_a
    )
    rows_b = "".join(
        f'<tr class="group-b"><td>{html.escape(str(p))}</td></tr>'
        for p in report.result.unique_b
    )

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>fcmp report</title>
  <style>{_HTML_STYLE}</style>
</head>
<body>
  <h2>File Comparison Report</h2>
  <div class="mode-info">
    <strong>Mode:</strong> {html.escape(mode_label)}<br>
    <strong>Generated:</strong> {report.generated_at.isoformat(timespec="seconds")}
  </div>
  {mismatch_section}
  <div class="section">
    <div class="path-header">
      <h3>Group A only ({len(report.result.unique_a)} item(s))</h3>
      {_dirs_html(report.dirs_a)}
    </div>
    <table><tr><th>Path</th></tr>{rows_a}</table>
  </div>
  <div class="section">
    <div class="path-header">
      <h3>Group B only ({len(report.result.unique_b)} item(s))</h3>
      {_dirs_html(report.dirs_b)}
    </div>
    <table><tr><th>Path</th></tr>{rows_b}</table>
  </div>
</body>
</html>"""

    with path.open("wb") as f:
        f.write(b"\xef\xbb\xbf")
        f.write(body.encode("utf-8"))


EXPORTERS: dict[str, Exporter] = {
    "json": export_json,
    "txt": export_txt,
    "csv": export_csv,
    "html": export_html,
}


def export(report: Report, path: Path, fmt: str) -> None:
    try:
        exporter = EXPORTERS[fmt]
    except KeyError as exc:
        raise ValueError(f"Unknown format: {fmt!r}. Choose from {sorted(EXPORTERS)}.") from exc
    exporter(report, path)
