"""stream2py interface to video.

Read frames from a video file or a camera device as a ``stream2py`` source.

The package's entry point is :class:`videostream2py.video.VideoCapture`, a
:class:`stream2py.SourceReader` backed by OpenCV's ``cv2.VideoCapture``:

>>> from videostream2py.video import VideoCapture  # doctest: +SKIP
>>> with VideoCapture(video_input=0) as cap:  # doctest: +SKIP
...     timestamp, ret, frame = cap.read()
"""
