import re

import pysbd

# Strip the leading markdown markers on a line so pysbd doesn't fold a heading or
# list bullet into the next sentence. We keep the line's body intact.
_MD_LEAD = re.compile(r"^(?:#{1,6}|>{1,3}|[-*+]|\d+\.)\s+", re.MULTILINE)

_segmenter = pysbd.Segmenter(language="en", clean=False)


def segment(content: str) -> list[str]:
    stripped = _MD_LEAD.sub("", content)
    return [s.strip() for s in _segmenter.segment(stripped) if s.strip()]
