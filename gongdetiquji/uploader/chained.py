from typing import Sequence

from .base import UploaderBase

class ChainedUploader(UploaderBase):

    '''
    A special uploader that combine different uploaders into one, and 
    will try them one by one.
    '''

    def __init__(self, children: Sequence[UploaderBase]):
        self.children=children

    async def upload(self, fname, content) -> str:
        for uploader in self.children:
            try:
                return (await uploader.upload(fname, content))
            except Exception as e:
                print(e)
                continue
        raise Exception('All uploaders have failed!')
    
    async def close(self):
        for uploader in self.children:
            await uploader.close()