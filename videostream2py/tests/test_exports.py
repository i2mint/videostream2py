"""Tests for the package's top-level exports.

:mod:`videostream2py` re-exports :class:`~videostream2py.video.VideoCapture`
lazily (PEP 562). These tests pin both halves of that contract: the name
resolves from the package root, and it does not resolve eagerly.
"""

import subprocess
import sys

import pytest

import videostream2py
import videostream2py.video


def test_video_capture_is_importable_from_package_root():
    from videostream2py import VideoCapture

    assert VideoCapture is videostream2py.video.VideoCapture


def test_video_capture_is_listed_in_all_and_dir():
    assert "VideoCapture" in videostream2py.__all__
    assert "VideoCapture" in dir(videostream2py)


def test_unknown_attribute_still_raises_attribute_error():
    with pytest.raises(AttributeError, match="no_such_name"):
        videostream2py.no_such_name


def test_importing_the_package_does_not_import_cv2():
    """The re-export must stay lazy: ``import videostream2py`` skips OpenCV.

    opencv-python's Linux wheels need ``libGL.so.1`` at ``import cv2`` time, so
    an eager re-export would turn a working ``import videostream2py`` into a
    hard failure on bare runners and headless containers.
    """
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, videostream2py; "
            "print('cv2' in sys.modules, 'videostream2py.video' in sys.modules)",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert probe.stdout.strip() == "False False"
