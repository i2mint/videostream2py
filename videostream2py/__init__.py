"""stream2py interface to video.

Read frames from a video file or a camera device as a ``stream2py`` source.

The package's entry point is :class:`~videostream2py.video.VideoCapture`, a
:class:`stream2py.SourceReader` backed by OpenCV's ``cv2.VideoCapture``:

>>> from videostream2py import VideoCapture
>>> VideoCapture.__name__
'VideoCapture'
>>> with VideoCapture(video_input=0) as cap:  # doctest: +SKIP
...     timestamp, ret, frame = cap.read()

The re-export is lazy: importing this package does not import OpenCV. That
happens the first time a re-exported name is actually used.
"""

from importlib import import_module as _import_module

__all__ = ["VideoCapture"]

# Public name -> the submodule (relative to this package) that defines it.
# Resolution is deferred (PEP 562) because importing ``videostream2py.video``
# means importing ``cv2``, whose Linux wheels need ``libGL.so.1`` present at
# import time -- routinely absent on bare CI runners and headless containers.
# Keeping this lazy means merely importing the package never fails there.
_LAZY_EXPORTS = {"VideoCapture": ".video"}


def __getattr__(name: str):
    """Resolve a lazily re-exported name, importing its submodule on demand."""
    submodule = _LAZY_EXPORTS.get(name)
    if submodule is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(_import_module(submodule, __name__), name)
    globals()[name] = value  # cache it: __getattr__ is only consulted on a miss
    return value


def __dir__():
    """List this module's own names along with the lazily re-exported ones."""
    return sorted(set(globals()) | set(__all__))
