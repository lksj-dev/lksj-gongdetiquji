# TODO Configurable
encodings=[ 'gb18030', 'utf-8', 'big5', 'windows-1252', 'shift-jis' ]

def try_decode(raw: bytes) -> str:
    for codec in encodings:
        try:
            return str(raw, codec)
        except:
            continue
    return None