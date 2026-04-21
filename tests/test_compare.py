from pathlib import Path

from fcmp.compare import ComparisonResult, FrameMismatch, compare
from fcmp.scanner import FileEntry


def entry(path: str, frames: int | None = None) -> FileEntry:
    p = Path(path)
    return FileEntry(path=p, filename=p.name, frame_count=frames)


def test_compare_empty_groups_returns_empty_result() -> None:
    result = compare({}, {})
    assert result == ComparisonResult(unique_a=[], unique_b=[], frame_mismatches=[])


def test_compare_finds_unique_in_each_group() -> None:
    a = {"x.mp4": entry("/a/x.mp4"), "y.mp4": entry("/a/y.mp4")}
    b = {"y.mp4": entry("/b/y.mp4"), "z.mp4": entry("/b/z.mp4")}
    result = compare(a, b)
    assert [p.name for p in result.unique_a] == ["x.mp4"]
    assert [p.name for p in result.unique_b] == ["z.mp4"]
    assert result.frame_mismatches == []


def test_compare_results_are_sorted_by_path() -> None:
    a = {"b": entry("/a/b"), "a": entry("/a/a"), "c": entry("/a/c")}
    result = compare(a, {})
    assert result.unique_a == [Path("/a/a"), Path("/a/b"), Path("/a/c")]


def test_compare_without_check_frames_never_reports_mismatches() -> None:
    a = {"k": entry("/a/k.mp4", frames=100)}
    b = {"k": entry("/b/k.mov", frames=200)}
    result = compare(a, b, check_frames=False)
    assert result.frame_mismatches == []


def test_compare_with_check_frames_detects_mismatch() -> None:
    a = {"k": entry("/a/k.mp4", frames=100)}
    b = {"k": entry("/b/k.mov", frames=90)}
    result = compare(a, b, check_frames=True)
    assert len(result.frame_mismatches) == 1
    mismatch = result.frame_mismatches[0]
    assert mismatch.basename == "k"
    assert mismatch.frames_a == 100
    assert mismatch.frames_b == 90
    assert mismatch.difference == 10


def test_compare_with_check_frames_no_mismatch_when_equal() -> None:
    a = {"k": entry("/a/k.mp4", frames=100)}
    b = {"k": entry("/b/k.mov", frames=100)}
    result = compare(a, b, check_frames=True)
    assert result.frame_mismatches == []


def test_compare_missing_frame_count_on_side_a() -> None:
    a = {"k": entry("/a/k.mp4", frames=None)}
    b = {"k": entry("/b/k.mov", frames=100)}
    result = compare(a, b, check_frames=True)
    m = result.frame_mismatches[0]
    assert m.frames_a is None
    assert isinstance(m.difference, str)
    assert "A" in m.difference or "a" in m.difference


def test_compare_missing_frame_count_on_side_b() -> None:
    a = {"k": entry("/a/k.mp4", frames=100)}
    b = {"k": entry("/b/k.mov", frames=None)}
    result = compare(a, b, check_frames=True)
    m = result.frame_mismatches[0]
    assert m.frames_b is None
    assert isinstance(m.difference, str)
    assert "B" in m.difference or "b" in m.difference


def test_frame_mismatch_holds_paths_and_filenames() -> None:
    a = {"k": entry("/a/k.mp4", frames=100)}
    b = {"k": entry("/b/k.mov", frames=90)}
    m = compare(a, b, check_frames=True).frame_mismatches[0]
    assert isinstance(m, FrameMismatch)
    assert m.path_a == Path("/a/k.mp4")
    assert m.path_b == Path("/b/k.mov")
    assert m.file_a == "k.mp4"
    assert m.file_b == "k.mov"
