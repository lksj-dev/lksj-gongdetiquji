import logging

from .util import try_decode

def process_plain_text(fname: str, content: bytes):
    if fname.endswith('txt') or fname.endswith('log'):
        decoded=try_decode(content)
        if decoded:
            return ([ (fname, decoded) ], True)
        else:
            logging.warn(f"Cannot guess encoding for file '{fname}', uploading cannot continue.")
    return (None, True)