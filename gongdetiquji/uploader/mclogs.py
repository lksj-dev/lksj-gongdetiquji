import asyncio
import logging
import os

from aiohttp import ClientSession

from .base import UploaderBase

class MCLogsUploader(UploaderBase):

    '''
    Uploader that implements paste uploading to any site that runs mclogs
    (https://github.com/aternosorg/mclogs).

    Known instances of dpaste includes the official instance https://mclo.gs 
    run by Aternos itself.
    '''

    def __init__(self, **kwargs):
        self.http_client=ClientSession(base_url=os.environ.get('MCLOGS_HOST', 'https://api.mclo.gs/'))

    async def upload(self, fname: str, content: bytes) -> str:
        # We have encountered cases where file content contains NUL character (embedded zero).
        # Thus we remove them before uploading, to avoid issue.
        content=content.translate({ 0: None })
        payload={ 'content': content }
        async with self.http_client.post('/1/log', data=payload, raise_for_status=False) as resp:
            resp_body=await resp.json()
            if resp.ok and resp_body['success']:
                return resp_body['url']
            else:
                logging.error(f'Uploading {fname} failed! Error message: {resp_body.get("error", "*no error message provided*")}')
                raise Exception(f'Remote mclogs instance did not return paste link in response')
    
    async def close(self):
        await self.http_client.close()