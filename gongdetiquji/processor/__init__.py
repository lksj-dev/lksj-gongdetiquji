from .plain import process_plain_text

processors=[
    process_plain_text
]

def get_files_to_upload(fname: str, content: bytes) -> list[tuple[str, str, bool]]:
    '''
    Gather a list of files (as list of name-to-content pairs) to upload.
    '''
    # Chain of responsibility: we stop at the first processor that accepts the input.
    for processor in processors:
        result=processor(fname, content)
        if result is not None:
            return result
    return []