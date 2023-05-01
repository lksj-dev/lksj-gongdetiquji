from typing import List, Sequence, Tuple

from .base import UploaderBase, UploadResult

class ChainedUploader(UploaderBase):

    '''
    A special uploader that combine different uploaders into one, and 
    will try them one by one.
    '''

    def __init__(self, children: Sequence[UploaderBase]):
        self.children=children

    async def upload(self, original_fname: str, files_to_upload: List[Tuple[str, str]]) -> UploadResult:
        for uploader in self.children:
            try:
                return (await uploader.upload(original_fname, files_to_upload))
            except Exception as e:
                print(e)
                continue
        raise Exception('All uploaders have failed!')
    
    async def close(self):
        for uploader in self.children:
            await uploader.close()