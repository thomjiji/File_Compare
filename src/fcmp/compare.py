from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from fcmp.scanner import FileEntry


@dataclass(frozen=True, slots=True)
class FrameMismatch:
    basename: str
    file_a: str
    file_b: str
    frames_a: int | None
    frames_b: int | None
    difference: int | str
    path_a: Path
    path_b: Path


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    unique_a: list[Path]
    unique_b: list[Path]
    frame_mismatches: list[FrameMismatch] = field(default_factory=list)


def _diff_for(frames_a: int | None, frames_b: int | None) -> int | str:
    if frames_a is None and frames_b is None:
        return "Both frame counts missing"
    if frames_a is None:
        return "Group A frame count missing"
    if frames_b is None:
        return "Group B frame count missing"
    return abs(frames_a - frames_b)


def compare(
    files_a: dict[str, FileEntry],
    files_b: dict[str, FileEntry],
    *,
    check_frames: bool = False,
) -> ComparisonResult:
    keys_a = set(files_a)
    keys_b = set(files_b)

    unique_a = sorted(files_a[k].path for k in keys_a - keys_b)
    unique_b = sorted(files_b[k].path for k in keys_b - keys_a)

    mismatches: list[FrameMismatch] = []
    if check_frames:
        for key in keys_a & keys_b:
            a = files_a[key]
            b = files_b[key]
            if a.frame_count == b.frame_count:
                continue
            mismatches.append(
                FrameMismatch(
                    basename=key,
                    file_a=a.filename,
                    file_b=b.filename,
                    frames_a=a.frame_count,
                    frames_b=b.frame_count,
                    difference=_diff_for(a.frame_count, b.frame_count),
                    path_a=a.path,
                    path_b=b.path,
                )
            )
        mismatches.sort(key=lambda m: m.basename)

    return ComparisonResult(
        unique_a=unique_a, unique_b=unique_b, frame_mismatches=mismatches
    )
