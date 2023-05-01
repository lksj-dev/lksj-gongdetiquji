import asyncio
import logging
import os
import typing

from aiohttp import ClientSession

from .base import UploaderBase, UploadResult

class PasteGGUploader(UploaderBase):

    '''
    Uploader that implements paste uploading to any site that runs https://github.com/ascclemens/paste
    '''

    def __init__(self, token: str='', **kwargs):
        self.http_client=ClientSession(base_url=os.environ.get('PASTE_GG_URL', 'https://api.paste.gg'))
        self.api_token=token

    async def upload(self, original_fname: str, files_to_upload: typing.List[typing.Tuple[str, str]]) -> UploadResult:
        # We have encountered cases where file content contains NUL character (embedded zero).
        # Thus we remove them before uploading, to avoid issue.
        content=content.translate({ 0: None })
        payload={
            'name': original_fname, 
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
                for fname, content in files_to_upload
            ]
        }
        headers={ 'Authorization': self.api_token }
        if not self.api_token and 'PASTE_GG_TOKEN' in os.environ:
            headers['Authorization']='Key ' + os.environ['PASTE_GG_TOKEN']
        async with self.http_client.post('/v1/pastes', json=payload, headers=headers) as resp:
            if resp.ok:
                body=await resp.json()
                if body['status'] == 'success' and 'result' in body:
                    # TODO Un-hardcode base url
                    paste_url='https://paste.gg/' + body['result']['id'] 
                    return UploadResult(True, { fname: paste_url for fname, _ in files_to_upload })
                else:
                    logging.error(f'Uploading {fname} encounters unexpected result! Server response: {str(body)}')
                    raise Exception('paste.gg instance did not return paste link in response')
            else:
                raise Exception('paste.gg server is down!')

    async def close(self):
        await self.http_client.close()