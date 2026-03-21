import unicodedata
import re
import logging

log = logging.getLogger(__name__)


def unicde_eq(a, b):
    return unicodedata.normalize('NFC', a) == unicodedata.normalize('NFC', b)


def encode(title):
    return unicodedata.normalize('NFC', title)


def normalize(title):
    # Replace all non-word characters
    fixed_encoding = unicodedata.normalize('NFC', title)
    norm = re.sub(r"\W+", " ", fixed_encoding.lower()).strip()
    log.debug(f"{title} -> {norm=}")
    return norm
