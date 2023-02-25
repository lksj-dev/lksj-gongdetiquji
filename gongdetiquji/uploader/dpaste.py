import asyncio
import logging
import os

from aiohttp import ClientSession

from .base import UploaderBase

class DPatseUploader(UploaderBase):

    '''
    Uploader that implements paste uploading to any site that runs dpates
    (https://github.com/DarrenOfficial/dpaste)

    Known instances of dpaste includes the official instance https://dpaste.org, 
    as well as an instance maintained by Mozilla: https://pastebin.mozilla.org
    '''

    def __init__(self, **kwargs):
        self.http_client=ClientSession(base_url=os.environ.get('DPASTE_HOST', 'https://dpaste.org'))

    async def upload(self, fname: str, content: bytes) -> str:
        # We have encountered cases where file content contains NUL character (embedded zero).
        # Thus we remove them before uploading, to avoid issue.
        content=content.translate({ 0: None })
        payload={
            'format': 'url',
            'content': content,
            'lexer': '_text'
        }
        async with self.http_client.post('/api/', data=payload, raise_for_status=False) as resp:
            resp_body=(await resp.read()).decode('utf-8')
            if resp.ok:
                return resp_body
            else:
                logging.error(f'Uploading {fname} encounters unexpected result! Server response: {resp_body}')
                raise Exception(f'Remote dpaste instance did not return paste link in response')
    
    async def close(self):
        await self.http_client.close()