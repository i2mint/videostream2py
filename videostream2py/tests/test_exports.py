"""Tests for the package's top-level exports.

:mod:`videostream2py` re-exports :class:`~videostream2py.video.VideoCapture`
lazily (PEP 562). These tests pin both halves of that contract: the name
resolves from the package root, and merely importing the package does *not*
resolve it -- which is what keeps ``import videostream2py`` working on a host
where ``import cv2`` would fail for want of ``libGL.so.1``.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import pytest

import videostream2py
import videostream2py.video

# The directory holding the ``videostream2py`` package that THIS session imported.
# Child interpreters are pinned to it so they can only be talking about the tree
# under test.
_TREE_UNDER_TEST = Path(videostream2py.__file__).resolve().parents[1]


def _run_in_fresh_interpreter(source: str) -> str:
    """Run ``source`` in a new interpreter that imports the tree under test.

    The child gets ``_TREE_UNDER_TEST`` prepended to ``PYTHONPATH``. Leaning on
    the inherited cwd instead would be a silent subject swap: under
    ``PYTHONSAFEPATH`` the cwd is not on ``sys.path`` at all for ``-c``, so the
    child would resolve ``videostream2py`` from whichever installed
    distribution happened to be around and report on that one instead.

    Returns:
        The child's stdout.
    """
    env = {**os.environ}
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(_TREE_UNDER_TEST), env.get("PYTHONPATH")])
    )
    child = subprocess.run(
        [sys.executable, "-c", source], capture_output=True, text=True, env=env
    )
    # Asserted rather than check=True: CalledProcessError.__str__ drops stderr,
    # which is precisely the traceback needed to see why the child failed.
    assert child.returncode == 0, child.stderr
    return child.stdout


class _FreshImport(NamedTuple):
    """What ``import videostream2py`` looks like in an otherwise untouched process."""

    package_file: Path
    cv2_imported: bool
    video_module_imported: bool
    public_names: tuple[str, ...]


# Asking for ``dir()`` in the same breath as the "did cv2 get imported?" question
# is safe: ``dir()`` consults the module's ``__dir__``, which resolves nothing.
_FRESH_IMPORT_SOURCE = """\
import json
import sys

import videostream2py

json.dump(
    {
        "package_file": videostream2py.__file__,
        "cv2_imported": "cv2" in sys.modules,
        "video_module_imported": "videostream2py.video" in sys.modules,
        "public_names": [n for n in dir(videostream2py) if not n.startswith("_")],
    },
    sys.stdout,
)
"""


@pytest.fixture(scope="module")
def fresh_import() -> _FreshImport:
    """Observe a pristine ``import videostream2py`` from outside this process.

    In-process assertions cannot see this: by the time any test runs, the
    package's own doctest and its sibling tests have already triggered
    ``__getattr__``, which caches the resolved name into ``globals()``.
    """
    observed = json.loads(_run_in_fresh_interpreter(_FRESH_IMPORT_SOURCE))
    return _FreshImport(
        package_file=Path(observed["package_file"]).resolve(),
        cv2_imported=observed["cv2_imported"],
        video_module_imported=observed["video_module_imported"],
        public_names=tuple(observed["public_names"]),
    )


def test_the_probe_looked_at_the_tree_under_test(fresh_import):
    """Guard the guard: a probe of some other installed copy would prove nothing."""
    assert fresh_import.package_file == Path(videostream2py.__file__).resolve()


def test_importing_the_package_does_not_import_cv2(fresh_import):
    """opencv-python's Linux wheels need ``libGL.so.1`` at ``import cv2`` time.

    An eager re-export would therefore turn a working ``import videostream2py``
    into a hard failure on bare runners and headless containers.
    """
    assert not fresh_import.cv2_imported
    assert not fresh_import.video_module_imported


def test_the_public_surface_is_exactly_the_lazy_exports(fresh_import):
    """``dir()`` must advertise the exports without the plumbing that serves them."""
    assert fresh_import.public_names == ("VideoCapture",)


def test_video_capture_is_importable_from_package_root():
    from videostream2py import VideoCapture

    assert VideoCapture is videostream2py.video.VideoCapture


def test_unknown_attribute_raises_attribute_error_naming_the_module():
    with pytest.raises(
        AttributeError,
        match=r"module 'videostream2py' has no attribute 'no_such_name'",
    ):
        videostream2py.no_such_name
