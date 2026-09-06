"""stream2py interface to video.

Read frames from a video file or a camera device as a ``stream2py`` source.

The package's entry point is :class:`~videostream2py.video.VideoCapture`, a
:class:`stream2py.SourceReader` backed by OpenCV's ``cv2.VideoCapture``:

>>> from videostream2py import VideoCapture
>>> VideoCapture.__name__
'VideoCapture'
>>> with VideoCapture(video_input=0) as cap:  # doctest: +SKIP
...     timestamp, ret, frame = cap.read()

The re-export is lazy (PEP 562): a plain ``import videostream2py`` never imports
OpenCV. Anything that actually materialises an exported name does -- not only
``from videostream2py import VideoCapture`` but also ``import *``, ``hasattr``,
:func:`inspect.getmembers` and :func:`help`. So on a host where ``import cv2``
itself fails -- Linux without ``libGL.so.1`` -- importing this package still
works, while introspecting it raises that ``ImportError``.
"""

from importlib import import_module as _import_module

# Public name -> the submodule (relative to this package) that defines it.
# Resolution is deferred (PEP 562) because importing ``videostream2py.video``
# means importing ``cv2``, whose Linux wheels need ``libGL.so.1`` present at
# import time -- routinely absent on bare CI runners and headless containers.
# Keeping this lazy means merely importing the package never fails there.
_LAZY_EXPORTS = {"VideoCapture": ".video"}

# Derived, not repeated: a new export is one entry in _LAZY_EXPORTS and nothing
# else. Spelling __all__ out again would let the two drift apart silently.
__all__ = sorted(_LAZY_EXPORTS)


def __getattr__(name: str):
    """Resolve a lazily re-exported name, importing its submodule on demand."""
    submodule = _LAZY_EXPORTS.get(name)
    if submodule is None:
        # Same message shape CPython emits, so "Did you mean ...?" still works.
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(_import_module(submodule, __name__), name)
    globals()[name] = value  # cache it: __getattr__ is only consulted on a miss
    return value


def __dir__():
    """List this module's own names along with the lazily re-exported ones."""
    return sorted(set(globals()) | set(__all__))
