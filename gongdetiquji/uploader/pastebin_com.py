import asyncio
import logging
import os

from aiohttp import ClientSession

from .base import UploaderBase

class PastebinDotComUploader(UploaderBase):

    '''
    Uploader that implements paste uploading to the well-known https://pastebin.com.
    '''

    def __init__(self, token='', **kwargs):
        self.http_client=ClientSession(base_url='https://pastebin.com')
        self.api_token=token

    async def upload(self, fname: str, content: bytes) -> str:
        # We have encountered cases where file content contains NUL character (embedded zero).
        # Thus we remove them before uploading, to avoid issue.
        content=content.translate({ 0: None })
        payload={
            'api_dev_key': self.api_token or os.environ['PASTEBIN_COM_TOKEN'],
            'api_option': 'paste', # Indicates that we are creating new paste
            'api_paste_name': fname,
            'api_paste_code': content,
            'api_paste_expire_date': 'N' # Never expires
        }
        async with self.http_client.post('/api/api_post.php', data=payload, raise_for_status=False) as resp:
            resp_body=(await resp.read()).decode('utf-8')
            if resp.ok:
               return resp_body
            else:
                logging.error(f'Uploading {fname} to https://pastebin.com encounters unexpected result! Server response: {resp_body}')
                raise Exception(f'https://pastebin.com did not return paste link in response')
    
    async def close(self):
        await self.http_client.close()