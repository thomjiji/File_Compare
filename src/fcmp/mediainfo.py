import json
import subprocess
from pathlib import Path

_BINARY = "mediainfo"
_TIMEOUT = 30


def is_available() -> bool:
    try:
        subprocess.run(
            [_BINARY, "--Version"],
            capture_output=True,
            check=True,
            timeout=5,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    return True


def _run_mediainfo(path: Path) -> str | None:
    try:
        result = subprocess.run(
            [_BINARY, "--Output=JSON", str(path)],
            capture_output=True,
            check=True,
            timeout=_TIMEOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    return result.stdout


def frame_count(path: Path) -> int | None:
    """Return the frame count for ``path``, or ``None`` if it can't be determined."""
    raw = _run_mediainfo(path)
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    for track in (data.get("media") or {}).get("track", []):
        if track.get("@type") != "Video":
            continue
        if (fc := track.get("FrameCount")) is not None:
            try:
                return int(fc)
            except (TypeError, ValueError):
                pass
        duration = track.get("Duration")
        frame_rate = track.get("FrameRate")
        if duration is not None and frame_rate is not None:
            try:
                return int(float(duration) * float(frame_rate))
            except (TypeError, ValueError):
                pass
        return None

    return None
