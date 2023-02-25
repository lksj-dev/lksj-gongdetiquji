import asyncio
import logging
import os

from aiohttp import ClientSession

from .base import UploaderBase

class PasteGGUploader(UploaderBase):

    '''
    Uploader that implements paste uploading to any site that runs https://github.com/ascclemens/paste
    '''

    def __init__(self, token: str='', **kwargs):
        self.http_client=ClientSession(base_url=os.environ.get('PASTE_GG_URL', 'https://api.paste.gg'))
        self.api_token=token

    async def upload(self, fname: str, content: bytes) -> str:
        # We have encountered cases where file content contains NUL character (embedded zero).
        # Thus we remove them before uploading, to avoid issue.
        content=content.translate({ 0: None })
        payload={
            'name': fname,
            'description': '由功德提取机 Bot 自动转存',
            'visibility': 'unlisted',
            'files': [
                {
                    'name': fname,
                    'content': {
                        'format': 'text',
                        'value': content
                    }
                }
            ]
        }
        headers={ 'Authorization': self.api_token }
        if not self.api_token and 'PASTE_GG_TOKEN' in os.environ:
            headers['Authorization']='Key ' + os.environ['PASTE_GG_TOKEN']
        async with self.http_client.post('/v1/pastes', json=payload, headers=headers) as resp:
            if resp.ok:
                body=await resp.json()
                if body['status'] == 'success' and 'result' in body:
                    return 'https://paste.gg/' + body['result']['id'] # TODO Un-hardcode base url
                else:
                    logging.error(f'Uploading {fname} encounters unexpected result! Server response: {str(body)}')
                    raise Exception('paste.gg instance did not return paste link in response')
            else:
                raise Exception('paste.gg server is down!')

    async def close(self):
        await self.http_client.close()