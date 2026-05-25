"""Sentence segmentation for uploaded contracts, with light markdown handling."""

import re

import pysbd

# Strip the leading markdown markers on a line so pysbd doesn't fold a heading or
# list bullet into the next sentence. We keep the line's body intact.
_MD_LEAD = re.compile(r"^(?:#{1,6}|>{1,3}|[-*+]|\d+\.)\s+", re.MULTILINE)

_segmenter = pysbd.Segmenter(language="en", clean=False)


def segment(content: str) -> list[str]:
    """Split ``content`` into trimmed sentences.

    Markdown line prefixes (headings, blockquotes, list bullets) are stripped
    before segmentation so they don't get glued onto the next sentence; the
    sentence body itself is preserved verbatim.
    """
    stripped = _MD_LEAD.sub("", content)
    return [s.strip() for s in _segmenter.segment(stripped) if s.strip()]
