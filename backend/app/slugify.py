import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(label: str) -> str:
    """Lowercase, collapse runs of non-alphanumeric chars into underscores, trim.

    Used to derive the immutable machine ``value`` of a ClauseType from its
    human-readable display ``label``. ``"Service Level Agreement"`` becomes
    ``"service_level_agreement"``; ``"  Non-Compete!! "`` becomes
    ``"non_compete"``. Empty results bubble up as an empty string — the
    caller decides what to do with that.
    """
    return _NON_ALNUM.sub("_", label.lower()).strip("_")
