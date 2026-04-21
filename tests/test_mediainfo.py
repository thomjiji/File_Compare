import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from fcmp import mediainfo


def _completed(stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def test_is_available_returns_true_on_success() -> None:
    with patch("subprocess.run", return_value=_completed("MediaInfo v23")):
        assert mediainfo.is_available() is True


def test_is_available_returns_false_when_binary_missing() -> None:
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert mediainfo.is_available() is False


def test_is_available_returns_false_on_timeout() -> None:
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="mediainfo", timeout=5),
    ):
        assert mediainfo.is_available() is False


def test_frame_count_parses_framecount_field() -> None:
    payload = json.dumps(
        {"media": {"track": [{"@type": "Video", "FrameCount": "12345"}]}}
    )
    with patch("subprocess.run", return_value=_completed(payload)):
        assert mediainfo.frame_count(Path("/fake/clip.mp4")) == 12345


def test_frame_count_falls_back_to_duration_times_framerate() -> None:
    payload = json.dumps(
        {
            "media": {
                "track": [
                    {"@type": "Video", "Duration": "10.0", "FrameRate": "24"}
                ]
            }
        }
    )
    with patch("subprocess.run", return_value=_completed(payload)):
        assert mediainfo.frame_count(Path("/fake/clip.mp4")) == 240


def test_frame_count_returns_none_when_no_video_track() -> None:
    payload = json.dumps({"media": {"track": [{"@type": "Audio"}]}})
    with patch("subprocess.run", return_value=_completed(payload)):
        assert mediainfo.frame_count(Path("/fake/audio.wav")) is None


def test_frame_count_returns_none_on_subprocess_error() -> None:
    with patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "mediainfo"),
    ):
        assert mediainfo.frame_count(Path("/fake/clip.mp4")) is None


def test_frame_count_returns_none_on_malformed_json() -> None:
    with patch("subprocess.run", return_value=_completed("not json")):
        assert mediainfo.frame_count(Path("/fake/clip.mp4")) is None


@pytest.mark.parametrize("bad", ["", "null"])
def test_frame_count_returns_none_on_empty_or_null_payload(bad: str) -> None:
    with patch("subprocess.run", return_value=_completed(bad)):
        assert mediainfo.frame_count(Path("/fake/clip.mp4")) is None
